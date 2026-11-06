"""The MCP server: modules 01-05 behind three tools."""

from __future__ import annotations

import functools
import os
import sys
from collections.abc import Callable
from typing import Any

HERE = os.path.dirname(os.path.abspath(__file__))
for d in ("01-syntax-tree", "02-explaining", "03-running-safely", "04-backtracking",
          "05-engine-differences"):
    sys.path.insert(0, os.path.join(HERE, "..", d))

import backtrack  # noqa: E402
import engines  # noqa: E402
import explain as explainer  # noqa: E402
import tree  # noqa: E402
from mcp.server.mcpserver import MCPServer  # noqa: E402
from mcp.server.mcpserver.exceptions import ToolError  # noqa: E402

mcp = MCPServer(
    "regexlab-tutorial",
    instructions="Runs regexes in real engines. Verify a regex with test_regex before claiming it works.",
)


def tool(fn: Callable[..., Any]) -> Callable[..., Any]:
    """Register fn as a tool. The client only ever sees a ToolError's message, so expected
    failures (a bad pattern, a missing engine) are converted into one with a useful text;
    a genuine bug stays a bug."""

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return fn(*args, **kwargs)
        except tree.ParseError as e:
            raise ToolError(f"invalid pattern: {e}") from e
        except (engines.EngineError, ValueError) as e:
            raise ToolError(str(e)) from e

    mcp.tool()(wrapper)
    return wrapper


@tool
def test_regex(pattern: str, subject: str | list[str], flags: str = "") -> str:
    """Run a regex in Python re and JavaScript RegExp and report every match.

    Use this before telling the user a regex works. Spans are [start:end) in code points.
    subject: one text or a list of cases. flags: any of i, m, s.
    """
    subjects = [subject] if isinstance(subject, str) else subject
    lines = [f"Pattern: {pattern}"]
    results = {}
    for engine in ("python", "javascript"):
        try:
            results[engine] = engines.run(engine, pattern, subjects, flags)
        except engines.EngineError as e:
            if "node is not installed" in str(e):
                lines.append(f"{engine}: skipped - {e}")
                continue
            lines.append(f"{engine}: ERROR {e}")
    for i, s in enumerate(subjects):
        lines.append(f"case {i + 1}: {s!r}")
        for engine, res in results.items():
            ms = res[i]
            lines.append(f"  {engine}: " + ("no match" if not ms else
                         "; ".join(f"[{a}:{b}] {t!r}" for a, b, t in ms)))
        if len(results) == 2 and results["python"][i] != results["javascript"][i]:
            lines.append("  => ENGINES DIFFER")
    return "\n".join(lines)


@tool
def explain_regex(pattern: str) -> str:
    """Explain a regex token by token in plain English (Python semantics).
    Constructs the explainer does not model are marked NOT EXPLAINED."""
    return explainer.explain(pattern)


@tool
def check_backtracking(pattern: str) -> str:
    """Check a regex for catastrophic backtracking: static scan, then a timed probe that is
    killed after 2.5 seconds. Reports an example slow input when it finds one."""
    v = backtrack.check(pattern)
    out = f"{v.level.upper()}: {v.detail}"
    if v.example:
        out += f"\nslow input: {v.example}"
    return out


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
