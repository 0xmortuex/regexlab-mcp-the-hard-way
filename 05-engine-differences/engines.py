"""Two engines behind one function: run(engine, pattern, subjects) -> list of match lists."""

from __future__ import annotations

import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "03-running-safely"))

import pyengine  # noqa: E402
import sandbox  # noqa: E402

RUNNER_JS = os.path.join(HERE, "runner.js")


class EngineError(Exception):
    pass


def node_path() -> str:
    node = shutil.which("node")
    if node is None:
        raise EngineError("node is not installed; the JavaScript engine needs it")
    return node


def run(engine: str, pattern: str, subjects: list[str], flags: str = "",
        timeout: float = 5.0) -> list[list[tuple[int, int, str]]]:
    """Per case, a list of (start, end, text). Raises EngineError on a compile error or hang."""
    if engine == "python":
        out = pyengine.run(pattern, subjects, flags, timeout)
        if out.error:
            raise EngineError(f"python: {out.error}")
        if out.timed_out:
            raise EngineError("python: timed out (catastrophic backtracking?)")
        return [[(m["start"], m["end"], m["text"]) for m in case] for case in out.cases]
    if engine == "javascript":
        req = json.dumps({"pattern": pattern, "flags": flags, "subjects": subjects})
        res = sandbox.run([node_path(), RUNNER_JS], req, timeout)
        if res.timed_out:
            raise EngineError("javascript: timed out (catastrophic backtracking?)")
        cases = []
        for line in res.stdout.splitlines():
            ev = json.loads(line)
            if "error" in ev:
                raise EngineError(f"javascript: {ev['error']}")
            if "case" in ev:
                cases.append([(m["start"], m["end"], m["text"]) for m in ev["matches"]])
        return cases
    raise ValueError(f"unknown engine {engine!r}")
