"""Module 05: the same pattern, two engines, and the places they disagree."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import differences  # noqa: E402
import engines  # noqa: E402


def main() -> None:
    py = lambda p, s, f="": engines.run("python", p, [s], f)[0]  # noqa: E731
    js = lambda p, s, f="": engines.run("javascript", p, [s], f)[0]  # noqa: E731

    # agreement first: ordinary patterns behave the same, spans included
    assert py(r"\d+", "a12b345") == js(r"\d+", "a12b345") == [(1, 3, "12"), (4, 7, "345")]
    # spans are code points in both, even after an emoji
    assert py("a", "\U0001F600a") == js("a", "\U0001F600a") == [(1, 2, "a")]

    # 1. $ and a trailing newline
    assert py("^abc$", "abc\n") == [(0, 3, "abc")]
    assert js("^abc$", "abc\n") == []

    # 2. \d and \w are Unicode in Python, ASCII in JavaScript
    assert py(r"\d+", "٣٤") == [(0, 2, "٣٤")]
    assert js(r"\d+", "٣٤") == []
    assert py(r"\w+", "café") == [(0, 4, "café")]
    assert js(r"\w+", "café") == [(0, 3, "caf")]

    # 3. named-group syntax: each engine rejects the other's
    for engine, bad in (("python", "(?<y>a)"), ("javascript", "(?P<y>a)")):
        try:
            engines.run(engine, bad, ["a"])
        except engines.EngineError as e:
            print("rejected:", e)
        else:
            raise AssertionError(f"{engine} should reject {bad}")

    # 4. lookbehind width
    assert js("(?<=a+)b", "aab") == [(2, 3, "b")]
    try:
        py("(?<=a+)b", "aab")
    except engines.EngineError as e:
        assert "fixed-width" in str(e)

    # 5. a backreference to a group that did not participate
    assert py(r"(a)?\1", "b") == []
    assert js(r"(a)?\1", "b") == [(0, 0, ""), (1, 1, "")]

    # 6. Turkish dotless i: JavaScript /i never maps U+0130 / U+0131 onto ASCII i
    assert [t for _, _, t in js("i", "İ ı I i", "i")] == ["I", "i"]
    assert "ı" in [t for _, _, t in py("i", "İ ı I i", "i")]

    # the table: every probe in one place
    table = differences.compare(r"^\d+$", "123")
    for label, row in table.items():
        print(f"{label:22} agree={row['agree']}  python={row['python']}  javascript={row['javascript']}")
    assert table["your subject"]["agree"]
    assert not table["trailing newline"]["agree"]
    assert not table["Arabic-Indic digits"]["agree"]
    print("\nmodule 05 ok")


if __name__ == "__main__":
    main()
