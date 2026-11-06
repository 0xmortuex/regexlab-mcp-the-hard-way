"""Module 02: explain patterns token by token, and refuse to guess."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import explain  # noqa: E402


def main() -> None:
    pattern = r"^(?P<user>[\w.-]+)@(?:[a-z]+\.)+[a-z]{2,}$"
    text = explain.explain(pattern)
    print(text)

    assert 'start of capture group 1, named "user"' in text
    assert 'any one of a word character, ".", "-"' in text
    assert "start of a non-capturing group" in text
    assert "end of group, repeated one or more times (greedy" in text
    assert "2 or more times" in text
    assert "the start of the text" in text and "the end of the text" in text

    # lazy and a negated class
    t2 = explain.explain(r'"[^"]*?"')
    print("\n" + t2)
    assert "any character EXCEPT" in t2 and "lazy" in t2

    # lookahead
    assert "negative lookahead" in explain.explain(r"foo(?!bar)")

    # unsupported syntax is labelled, not guessed
    t3 = explain.explain(r"(?<=\$)\d+")
    print("\n" + t3)
    assert "NOT EXPLAINED" in t3 and r"(?<=\$)" in t3

    # the line count matches the token count: nothing silently skipped
    assert len(explain.explain("abc").splitlines()) == 3
    print("\nmodule 02 ok")


if __name__ == "__main__":
    main()
