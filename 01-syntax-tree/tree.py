"""A minimal regex parser: pattern text in, syntax tree out.

Supports: literals, escapes (\\d \\w \\s \\b and escaped punctuation), `.`, anchors,
character classes with ranges, groups (capturing, non-capturing, named, lookahead),
alternation, and the quantifiers * + ? {n} {n,} {n,m} with a lazy `?` suffix.
Anything else raises ParseError or becomes an `unsupported` node. It never guesses.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class ParseError(ValueError):
    def __init__(self, message: str, pos: int) -> None:
        super().__init__(f"{message} at position {pos}")
        self.message = message
        self.pos = pos


@dataclass
class Node:
    kind: str  # lit any anchor esc class group alt seq repeat unsupported
    start: int
    end: int
    text: str = ""          # lit: the char; esc: the letter; anchor: ^ or $ or b; class items
    kids: list[Node] = field(default_factory=list)
    lo: int = 0             # repeat bounds (hi None = unbounded)
    hi: int | None = None
    lazy: bool = False
    negated: bool = False
    group_kind: str = ""    # capture, noncap, named, lookahead, neg_lookahead
    name: str = ""
    index: int = 0


class Parser:
    def __init__(self, pattern: str) -> None:
        self.p = pattern
        self.i = 0
        self.groups = 0

    def peek(self) -> str:
        return self.p[self.i] if self.i < len(self.p) else ""

    def parse(self) -> Node:
        node = self.alt()
        if self.i < len(self.p):
            raise ParseError("unbalanced parenthesis", self.i)
        return node

    def alt(self) -> Node:
        start = self.i
        branches = [self.seq()]
        while self.peek() == "|":
            self.i += 1
            branches.append(self.seq())
        return Node("alt", start, self.i, kids=branches)

    def seq(self) -> Node:
        start = self.i
        items: list[Node] = []
        while self.i < len(self.p) and self.peek() not in "|)":
            items.append(self.quantified())
        return Node("seq", start, self.i, kids=items)

    def quantified(self) -> Node:
        atom = self.atom()
        c = self.peek()
        lo = hi = None
        qstart = self.i
        if c == "*":
            lo, hi = 0, None
            self.i += 1
        elif c == "+":
            lo, hi = 1, None
            self.i += 1
        elif c == "?":
            lo, hi = 0, 1
            self.i += 1
        elif c == "{":
            close = self.p.find("}", self.i)
            body = self.p[self.i + 1:close] if close != -1 else ""
            parts = body.split(",")
            if close != -1 and parts[0].isdigit() and len(parts) <= 2 and \
                    all(x.isdigit() or x == "" for x in parts[1:]):
                lo = int(parts[0])
                hi = lo if len(parts) == 1 else (int(parts[1]) if parts[1] else None)
                self.i = close + 1
                if hi is not None and lo > hi:
                    raise ParseError("min repeat greater than max repeat", qstart)
        if lo is None:
            return atom
        if atom.kind == "anchor":
            raise ParseError("nothing to repeat", qstart)
        lazy = False
        if self.peek() == "?":
            lazy = True
            self.i += 1
        return Node("repeat", atom.start, self.i, kids=[atom], lo=lo, hi=hi, lazy=lazy,
                    text=self.p[qstart:self.i])

    def atom(self) -> Node:
        s = self.i
        c = self.peek()
        if c == "(":
            return self.group()
        if c == "[":
            return self.char_class()
        if c == "\\":
            return self.escape()
        if c in "*+?":
            raise ParseError("nothing to repeat", s)
        self.i += 1
        if c == ".":
            return Node("any", s, self.i)
        if c in "^$":
            return Node("anchor", s, self.i, text=c)
        return Node("lit", s, self.i, text=c)

    def escape(self) -> Node:
        s = self.i
        self.i += 1
        if self.i >= len(self.p):
            raise ParseError("bad escape at end of pattern", s)
        c = self.p[self.i]
        self.i += 1
        if c in "dDwWsS":
            return Node("esc", s, self.i, text=c)
        if c in "bB":
            return Node("anchor", s, self.i, text="\\" + c)
        if c in "ntr":
            return Node("lit", s, self.i, text={"n": "\n", "t": "\t", "r": "\r"}[c])
        if c.isalnum():
            # \1 backreferences, \p{..}, \k<..>, ... exist in real engines; we say so.
            return Node("unsupported", s, self.i, text=f"\\{c}")
        return Node("lit", s, self.i, text=c)  # escaped punctuation: \. \* \\ ...

    def char_class(self) -> Node:
        s = self.i
        self.i += 1
        negated = self.peek() == "^"
        if negated:
            self.i += 1
        items: list[Node] = []
        first = True
        while True:
            if self.i >= len(self.p):
                raise ParseError("unterminated character set", s)
            c = self.p[self.i]
            if c == "]" and not first:
                self.i += 1
                break
            first = False
            lo = self.class_atom()
            if self.peek() == "-" and self.i + 1 < len(self.p) and self.p[self.i + 1] != "]":
                self.i += 1
                hi = self.class_atom()
                if lo.kind != "lit" or hi.kind != "lit" or hi.text < lo.text:
                    raise ParseError("bad character range", lo.start)
                items.append(Node("range", lo.start, hi.end, text=lo.text + hi.text))
            else:
                items.append(lo)
        return Node("class", s, self.i, kids=items, negated=negated)

    def class_atom(self) -> Node:
        if self.peek() == "\\":
            node = self.escape()
            if node.kind == "anchor":  # \b inside a class means backspace
                return Node("lit", node.start, node.end, text="\b")
            return node
        s = self.i
        self.i += 1
        return Node("lit", s, self.i, text=self.p[s])

    def group(self) -> Node:
        s = self.i
        self.i += 1
        kind, name, index = "capture", "", 0
        if self.peek() == "?":
            rest = self.p[self.i:]
            if rest.startswith("?:"):
                kind = "noncap"
                self.i += 2
            elif rest.startswith("?="):
                kind = "lookahead"
                self.i += 2
            elif rest.startswith("?!"):
                kind = "neg_lookahead"
                self.i += 2
            elif rest.startswith("?P<"):
                close = self.p.find(">", self.i)
                if close == -1:
                    raise ParseError("missing > in group name", s)
                kind, name = "named", self.p[self.i + 3:close]
                self.i = close + 1
            else:
                # lookbehind, atomic, conditionals, inline flags...: real, but not modelled here
                end = self.skip_group(s)
                self.i = end
                return Node("unsupported", s, end, text=self.p[s:end])
        if kind in ("capture", "named"):
            self.groups += 1
            index = self.groups
        body = self.alt()
        if self.peek() != ")":
            raise ParseError("missing ), unterminated subpattern", s)
        self.i += 1
        return Node("group", s, self.i, kids=[body], group_kind=kind, name=name, index=index)

    def skip_group(self, s: int) -> int:
        depth = 0
        j = s
        while j < len(self.p):
            if self.p[j] == "\\":
                j += 2
                continue
            if self.p[j] == "(":
                depth += 1
            elif self.p[j] == ")":
                depth -= 1
                if depth == 0:
                    return j + 1
            j += 1
        raise ParseError("missing ), unterminated subpattern", s)


def parse(pattern: str) -> Node:
    return Parser(pattern).parse()


def dump(node: Node, pattern: str, depth: int = 0) -> str:
    """Indented text view of the tree, with the source slice each node covers."""
    label = node.kind
    if node.kind == "repeat":
        label += f" {node.lo}..{'inf' if node.hi is None else node.hi}{' lazy' if node.lazy else ''}"
    elif node.kind == "group":
        label += f" {node.group_kind}" + (f" #{node.index}" if node.index else "") + \
            (f" '{node.name}'" if node.name else "")
    elif node.kind == "class" and node.negated:
        label += " negated"
    elif node.text and node.kind != "repeat":
        label += f" {node.text!r}"
    lines = ["  " * depth + f"{label:<28} {pattern[node.start:node.end]!r}"]
    for k in node.kids:
        lines.append(dump(k, pattern, depth + 1))
    return "\n".join(lines)
