"""Turn the syntax tree from module 01 into plain English, one line per token."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "01-syntax-tree"))

import tree  # noqa: E402

ESC = {
    "d": "a digit (Python: any Unicode decimal digit)",
    "D": "anything that is not a digit",
    "w": "a word character (letter, digit or underscore)",
    "W": "anything that is not a word character",
    "s": "whitespace",
    "S": "anything that is not whitespace",
}


def lit(ch: str) -> str:
    names = {"\n": "a newline", "\t": "a tab", "\r": "a carriage return", " ": "a space"}
    return names.get(ch, f'the character "{ch}"')


def quantifier(n: tree.Node) -> str:
    lo, hi = n.lo, n.hi
    if (lo, hi) == (0, None):
        base = "zero or more times"
    elif (lo, hi) == (1, None):
        base = "one or more times"
    elif (lo, hi) == (0, 1):
        base = "optionally"
    elif hi is None:
        base = f"{lo} or more times"
    elif lo == hi:
        base = f"exactly {lo} times"
    else:
        base = f"between {lo} and {hi} times"
    return base + (" (lazy: as few as possible)" if n.lazy else " (greedy: as many as possible)")


def describe_leaf(n: tree.Node) -> str:
    if n.kind == "lit":
        return lit(n.text)
    if n.kind == "esc":
        return ESC[n.text]
    if n.kind == "any":
        return "any character except a newline"
    if n.kind == "anchor":
        return {"^": "the start of the text", "$": "the end of the text",
                "\\b": "a word boundary", "\\B": "not a word boundary"}[n.text]
    if n.kind == "class":
        parts = []
        for item in n.kids:
            if item.kind == "range":
                parts.append(f'"{item.text[0]}" to "{item.text[1]}"')
            elif item.kind == "esc":
                parts.append(ESC[item.text].split(" (")[0])
            else:
                parts.append(f'"{item.text}"')
        return ("any character EXCEPT " if n.negated else "any one of ") + ", ".join(parts)
    if n.kind == "unsupported":
        return f"NOT EXPLAINED: {n.text} is valid regex syntax this explainer does not model"
    raise AssertionError(n.kind)


def group_open(n: tree.Node) -> str:
    return {
        "capture": f"start of capture group {n.index}",
        "named": f'start of capture group {n.index}, named "{n.name}"',
        "noncap": "start of a non-capturing group",
        "lookahead": "start of a lookahead: what follows must match (nothing is consumed)",
        "neg_lookahead": "start of a negative lookahead: what follows must NOT match",
    }[n.group_kind]


def explain_node(n: tree.Node, pattern: str, depth: int, out: list[tuple[int, str, str]]) -> None:
    if n.kind == "alt":
        for i, branch in enumerate(n.kids):
            if i:
                out.append((depth, "|", "OR - try the next alternative"))
            explain_node(branch, pattern, depth, out)
    elif n.kind == "seq":
        for item in n.kids:
            explain_node(item, pattern, depth, out)
    elif n.kind == "group":
        out.append((depth, pattern[n.start:n.start + _header_len(n, pattern)], group_open(n)))
        explain_node(n.kids[0], pattern, depth + 1, out)
        out.append((depth, ")", "end of group"))
    elif n.kind == "repeat":
        child = n.kids[0]
        if child.kind == "group":
            out.append((depth, pattern[child.start:child.start + _header_len(child, pattern)],
                        group_open(child)))
            explain_node(child.kids[0], pattern, depth + 1, out)
            out.append((depth, ")" + n.text, "end of group, repeated " + quantifier(n)))
        else:
            out.append((depth, pattern[n.start:n.end], f"{describe_leaf(child)}, {quantifier(n)}"))
    else:
        out.append((depth, pattern[n.start:n.end], describe_leaf(n)))


def _header_len(g: tree.Node, pattern: str) -> int:
    """Length of the opening token: '(', '(?:', '(?P<name>' ..."""
    body = g.kids[0]
    return body.start - g.start


def explain(pattern: str) -> str:
    root = tree.parse(pattern)
    rows: list[tuple[int, str, str]] = []
    explain_node(root, pattern, 0, rows)
    width = max(len("  " * d + s) for d, s, _ in rows) if rows else 0
    lines = [f"  {('  ' * d + s).ljust(width)}  {desc}" for d, s, desc in rows]
    return "\n".join(lines)
