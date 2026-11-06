# Module 01: Syntax Tree

## The Concept

You could build a regex tool on top of `re.compile` alone: compile, run, print. That gets you
a tester. It does not get you an explainer, a ReDoS detector or a converter, because the
compiled object hides the structure. `re` does not tell you which part of the pattern is a
group, where a quantifier applies, or whether two repeats overlap.

So the first thing we build is a parser. Regex syntax is small and recursive:

```
alt     := seq ( '|' seq )*
seq     := quantified*
quantified := atom ( '*' | '+' | '?' | '{n,m}' ) '?'?
atom    := literal | escape | '.' | anchor | '[' class ']' | '(' alt ')'
```

`tree.py` is a recursive-descent parser for that grammar: one method per rule, a cursor `i`
that only moves forward. The result is a tree of `Node` objects.

## Spans: the detail that pays for itself

Every node stores `start` and `end`, the slice of the pattern it came from. That looks like
bookkeeping now. Later it is how the explainer prints the exact source next to each
description, how the ReDoS report quotes the offending group, and how a converter can rewrite
one token without touching the rest of the pattern.

## Errors are part of the product

An agent reads your error and fixes its pattern. `missing ), unterminated subpattern at
position 0` is actionable; `error` is not. Each failure raises `ParseError` with a message
and a position, mirroring what Python's `re` says for the same mistakes.

## Saying "I don't know"

Real engines support far more than we model: lookbehind, backreferences, atomic groups,
inline flags. The parser does not try to be clever. When it meets `(?<=...)` or `\1` it
returns an `unsupported` node that covers the exact source span, and later modules label it
`NOT EXPLAINED`. A tool that confidently explains something it did not parse is worse than no
tool.

## Run it

```bash
python 01-syntax-tree/main.py
```

`main.py` prints the tree for `^(?P<year>\d{4})-(\d\d)$` and asserts its shape, its spans,
the quantifier bounds and the exact position of five kinds of syntax error.

## Try breaking it

1. Add `{n}` support inside character classes by mistake (treat `[a{2}]` as a repeat). What
   does the test for classes tell you?
2. Parse `a**`. Python says "multiple repeat". What does this parser do, and what should it do?
3. Add lookbehind support: parse `(?<=` and `(?<!` into a `group` node. What else in module 02
   has to learn about the new group kind?

-> [Next: Module 02](../02-explaining/README.md)
