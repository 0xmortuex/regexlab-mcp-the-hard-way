"""Find regexes that can backtrack catastrophically, then prove it by timing them.

Two stages, because each is weak alone:
  static  - cheap, reads the tree, but only suspects (it over-warns)
  probe   - slow, runs the pattern on nasty input, but only measures what it tried
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "01-syntax-tree"))
sys.path.insert(0, os.path.join(HERE, "..", "03-running-safely"))

import sandbox  # noqa: E402
import tree  # noqa: E402

PROBE = os.path.join(HERE, "probe_runner.py")
SIZES = list(range(6, 44, 2))


def unbounded(n: tree.Node) -> bool:
    return n.kind == "repeat" and n.hi is None


def descendants(n: tree.Node) -> list[tree.Node]:
    out = []
    for k in n.kids:
        out.append(k)
        out.extend(descendants(k))
    return out


def static_suspects(root: tree.Node) -> list[tree.Node]:
    r"""Unbounded repeats that contain another unbounded repeat: (a+)+, (\w+\s?)*, (.*)*"""
    return [n for n in descendants(root)
            if unbounded(n) and any(unbounded(d) for d in descendants(n))]


def sample(n: tree.Node) -> str:
    """A short string the node matches."""
    if n.kind == "lit":
        return n.text
    if n.kind == "esc":
        return {"d": "0", "w": "a", "s": " ", "D": "a", "W": "!", "S": "a"}[n.text]
    if n.kind == "any":
        return "a"
    if n.kind == "class":
        item = n.kids[0]
        return item.text[0] if item.kind == "range" else sample(item)
    if n.kind == "repeat":
        return sample(n.kids[0]) * n.lo  # the minimum: optional parts stay out, so they cannot
        #                                  keep the unit from being ambiguous
    return "".join(sample(k) for k in n.kids)  # alt/seq/group: first branch is good enough


@dataclass
class Verdict:
    suspects: list[str]
    level: str          # "exponential", "none"
    detail: str
    example: str = ""


def check(pattern: str, budget: float = 2.5) -> Verdict:
    root = tree.parse(pattern)
    suspects = static_suspects(root)
    if not suspects:
        return Verdict([], "none", "no nested unbounded repeat found; not probed")
    target = suspects[0]
    unit = sample(target.kids[0]) or "a"
    req = {"pattern": pattern, "prefix": "", "unit": unit, "suffix": "!", "sizes": SIZES}
    res = sandbox.run([sys.executable, "-I", PROBE], json.dumps(req), budget)
    points = [json.loads(line) for line in res.stdout.splitlines()]
    names = [pattern[s.start:s.end] for s in suspects]
    if res.timed_out:
        n = (points[-1]["n"] + 2) if points else SIZES[0]
        return Verdict(names, "exponential",
                       f"killed after {budget}s at n~{n}; last completed point: "
                       f"{points[-1] if points else 'none'}", f"{unit!r} * {n} + '!'")
    worst = max(p["ms"] for p in points)
    return Verdict(names, "none", f"suspected, but the probe did not slow down "
                   f"(slowest {worst:.1f} ms up to n={SIZES[-1]})")
