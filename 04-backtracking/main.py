"""Module 04: static suspicion, then an empirical probe that is killed at the budget."""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import backtrack  # noqa: E402
import tree  # noqa: E402


def main() -> None:
    # static stage alone
    root = tree.parse(r"(a+)+$")
    assert len(backtrack.static_suspects(root)) == 1
    assert backtrack.static_suspects(tree.parse(r"^\d+-\d+$")) == []

    for pattern, expect in [
        (r"(a+)+$", "exponential"),
        (r"^(\w+\s?)*$", "exponential"),
        (r"(.*)*x", "exponential"),
        (r"^\d+-\d+$", "none"),        # nothing suspicious: not even probed
        (r"^(\d+,)+$", "none"),        # suspicious shape, but the probe clears it
    ]:
        t0 = time.perf_counter()
        v = backtrack.check(pattern)
        wall = time.perf_counter() - t0
        print(f"{pattern!r:18} -> {v.level:11} ({wall:.1f}s)  {v.detail}"
              + (f"  slow input: {v.example}" if v.example else ""))
        assert v.level == expect, (pattern, v)
        assert wall < 20, "the probe must never run past its budget"

    # `^(\d+,)+$` is the lesson: the static stage over-warns, the probe is the judge
    cleared = backtrack.check(r"^(\d+,)+$")
    assert cleared.suspects and cleared.level == "none"
    print("\nmodule 04 ok")


if __name__ == "__main__":
    main()
