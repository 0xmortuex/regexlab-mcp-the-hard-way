"""Module 01: parse a few patterns, print the trees, and check them."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tree  # noqa: E402


def kinds(pattern: str) -> list[str]:
    root = tree.parse(pattern)
    out: list[str] = []

    def walk(n: tree.Node) -> None:
        out.append(n.kind)
        for k in n.kids:
            walk(k)

    walk(root)
    return out


def main() -> None:
    pattern = r"^(?P<year>\d{4})-(\d\d)$"
    root = tree.parse(pattern)
    print(tree.dump(root, pattern))

    # shape: ^ , a named group, '-', a plain group, $
    seq = root.kids[0]
    assert [n.kind for n in seq.kids] == ["anchor", "group", "lit", "group", "anchor"]
    named, plain = seq.kids[1], seq.kids[3]
    assert (named.group_kind, named.name, named.index) == ("named", "year", 1)
    assert (plain.group_kind, plain.index) == ("capture", 2)
    # every node knows which slice of the source it came from
    assert pattern[named.start:named.end] == r"(?P<year>\d{4})"
    rep = named.kids[0].kids[0].kids[0]
    assert rep.kind == "repeat" and (rep.lo, rep.hi) == (4, 4)

    # quantifiers and laziness
    lazy = tree.parse("a+?").kids[0].kids[0]
    assert (lazy.lo, lazy.hi, lazy.lazy) == (1, None, True)
    assert tree.parse("a{2,}").kids[0].kids[0].hi is None
    assert "repeat" in kinds("(a|b)*")

    # character classes
    cls = tree.parse("[^a-c_]").kids[0].kids[0]
    assert cls.negated and [i.kind for i in cls.kids] == ["range", "lit"]

    # honest about what it does not model
    assert "unsupported" in kinds(r"(?<=a)b")   # lookbehind
    assert "unsupported" in kinds(r"(a)\1")     # backreference

    # errors carry a position
    for bad, msg, pos in [("(abc", "missing )", 0), ("a)", "unbalanced", 1),
                          ("*a", "nothing to repeat", 0), ("[abc", "unterminated", 0),
                          ("a{3,1}", "min repeat", 1)]:
        try:
            tree.parse(bad)
        except tree.ParseError as e:
            assert msg in e.message and e.pos == pos, (bad, e)
        else:
            raise AssertionError(f"{bad!r} should not parse")
    print("\nmodule 01 ok")


if __name__ == "__main__":
    main()
