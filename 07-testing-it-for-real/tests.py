"""The test suite for the tutorial server: real processes, real engines, exact expectations."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
for d in ("01-syntax-tree", "02-explaining", "03-running-safely", "04-backtracking",
          "05-engine-differences"):
    sys.path.insert(0, os.path.join(ROOT, d))

import backtrack  # noqa: E402
import engines  # noqa: E402
import explain  # noqa: E402
import pyengine  # noqa: E402
import sandbox  # noqa: E402
import tree  # noqa: E402

HAS_NODE = shutil.which("node") is not None
needs_node = unittest.skipUnless(HAS_NODE, "node is not installed")

HANG_TREE = """
import json, os, subprocess, sys, time
g = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
print(json.dumps({"child": os.getpid(), "grandchild": g.pid}), flush=True)
time.sleep(120)
"""


def pid_alive(pid: int) -> bool:
    if sys.platform == "win32":
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True,
                           text=True)
        return str(pid) in r.stdout
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    try:
        with open(f"/proc/{pid}/stat") as f:
            return f.read().rsplit(")", 1)[1].split()[0] != "Z"
    except FileNotFoundError:
        return True


class ParserTests(unittest.TestCase):
    def test_every_error_has_a_position(self):
        for bad, pos in [("(a", 0), ("a)", 1), ("+a", 0), ("[a", 0)]:
            with self.assertRaises(tree.ParseError) as cm:
                tree.parse(bad)
            self.assertEqual(cm.exception.pos, pos, bad)

    def test_unsupported_is_marked_not_guessed(self):
        self.assertIn("NOT EXPLAINED", explain.explain(r"(?<=a)b"))


class SandboxTests(unittest.TestCase):
    def test_kill_proof_whole_tree_dies(self):
        res = sandbox.run([sys.executable, "-c", HANG_TREE], "", timeout=2.0)
        self.assertTrue(res.timed_out)
        pids = json.loads(res.stdout.splitlines()[0])
        for name in ("child", "grandchild"):
            for _ in range(100):
                if not pid_alive(pids[name]):
                    break
                time.sleep(0.1)
            self.assertFalse(pid_alive(pids[name]), f"{name} survived the kill")

    def test_hang_is_bounded_and_keeps_finished_cases(self):
        t0 = time.perf_counter()
        out = pyengine.run(r"(a+)+$", ["aaa", "a" * 60 + "!"], timeout=1.5)
        self.assertTrue(out.timed_out)
        self.assertLess(time.perf_counter() - t0, 20)
        self.assertEqual(len(out.cases), 1)


class BacktrackTests(unittest.TestCase):
    def test_known_redos_patterns_are_confirmed_within_the_budget(self):
        for pattern in (r"(a+)+$", r"^(\w+\s?)*$", r"(.*)*x"):
            t0 = time.perf_counter()
            self.assertEqual(backtrack.check(pattern).level, "exponential", pattern)
            self.assertLess(time.perf_counter() - t0, 20)

    def test_safe_patterns_are_not_flagged(self):
        for pattern in (r"^\d+-\d+$", r"^(\d+,)+$", r"^[a-z]+@[a-z]+\.com$"):
            self.assertEqual(backtrack.check(pattern).level, "none", pattern)


@needs_node
class EngineFactTests(unittest.TestCase):
    def spans(self, engine, pattern, subject, flags=""):
        return engines.run(engine, pattern, [subject], flags)[0]

    def test_dollar_and_trailing_newline(self):
        self.assertEqual(self.spans("python", "^abc$", "abc\n"), [(0, 3, "abc")])
        self.assertEqual(self.spans("javascript", "^abc$", "abc\n"), [])

    def test_unicode_digits(self):
        arabic = "٣٤"
        self.assertEqual(self.spans("python", r"\d+", arabic), [(0, 2, arabic)])
        self.assertEqual(self.spans("javascript", r"\d+", arabic), [])

    def test_astral_spans_are_code_points(self):
        for engine in ("python", "javascript"):
            self.assertEqual(self.spans(engine, "a", "\U0001F600a"), [(1, 2, "a")], engine)

    def test_turkish_dotless_i(self):
        js = [t for _, _, t in self.spans("javascript", "i", "İ ı I i", "i")]
        self.assertEqual(js, ["I", "i"])
        py = [t for _, _, t in self.spans("python", "i", "İ ı I i", "i")]
        self.assertIn("ı", py)

    def test_named_group_syntax_is_dialect_specific(self):
        with self.assertRaises(engines.EngineError):
            engines.run("python", "(?<y>a)", ["a"])
        with self.assertRaises(engines.EngineError):
            engines.run("javascript", "(?P<y>a)", ["a"])


class StdioTests(unittest.IsolatedAsyncioTestCase):
    async def test_the_real_server_over_stdio(self):
        from mcp import ClientSession
        from mcp.client.stdio import StdioServerParameters, stdio_client

        server = os.path.join(ROOT, "06-the-mcp-wrapper", "server.py")
        params = StdioServerParameters(command=sys.executable, args=[server])
        async with stdio_client(params) as (r, w), ClientSession(r, w) as s:
            await s.initialize()
            names = {t.name for t in (await s.list_tools()).tools}
            self.assertEqual(names, {"test_regex", "explain_regex", "check_backtracking"})
            res = await s.call_tool("test_regex", {"pattern": r"\d+", "subject": "a12"})
            self.assertIn("[1:3] '12'", res.content[0].text)
            res = await s.call_tool("explain_regex", {"pattern": "(x"})
            self.assertTrue(res.is_error)
            self.assertIn("missing )", res.content[0].text)


if __name__ == "__main__":
    unittest.main()
