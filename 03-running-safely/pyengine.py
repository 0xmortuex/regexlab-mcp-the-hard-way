"""Python's re, run safely: the parent side of runner.py."""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field

import sandbox

RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runner.py")


@dataclass
class Outcome:
    error: str | None = None
    timed_out: bool = False
    cases: list[list[dict]] = field(default_factory=list)  # type: ignore[type-arg]
    elapsed: float = 0.0


def run(pattern: str, subjects: list[str], flags: str = "", timeout: float = 5.0) -> Outcome:
    if len(subjects) > 100 or sum(map(len, subjects)) > 200_000:
        raise ValueError("too many cases or too much text")
    req = json.dumps({"pattern": pattern, "flags": flags, "subjects": subjects})
    # -I: isolated mode, so the child ignores PYTHON* env vars and the cwd on sys.path
    res = sandbox.run([sys.executable, "-I", RUNNER], req, timeout)
    out = Outcome(timed_out=res.timed_out, elapsed=res.elapsed)
    for line in res.stdout.splitlines():
        ev = json.loads(line)
        if "error" in ev:
            out.error = ev["error"]
        elif "case" in ev:
            out.cases.append(ev["matches"])
    if not res.timed_out and out.error is None and len(out.cases) != len(subjects):
        raise RuntimeError(f"runner died: {res.stderr[-300:]}")
    return out
