# Module 05: Engine Differences

## The Concept

"It works" is meaningless until you say *where*. The same pattern text can match different
things, or fail to compile, depending on the engine. This is the largest single source of
subtly wrong regexes written by models, because a model blends everything it has seen.

Here we run one pattern in **Python's `re`** and **JavaScript's RegExp** (through `node`) and
compare. The JavaScript side is a tiny fixed `runner.js` with the same shape as module 03's
Python runner: JSON on stdin, one JSON line per case on stdout, the pattern only ever handed to
`new RegExp` as data, and it runs through the same `sandbox.run`.

## Comparable results

Two details make the output of both engines comparable:

- **Spans.** JavaScript indexes UTF-16 units, so an emoji counts as two. Python counts code
  points. `runner.js` converts so that `[1:2]` means the same thing in both. Without that, every
  result after an emoji disagrees for a boring reason.
- **Group syntax.** The two engines spell named groups differently, so a pattern may be valid in
  one and a compile error in the other. A compile error is a *result*, not a crash.

## The differences the tests pin down

| Pattern | Subject | Python `re` | JavaScript |
|---------|---------|-------------|------------|
| `^abc$` | `abc\n` | matches (`$` also matches before a final newline) | no match |
| `\d+` | Arabic-Indic digits | matches | no match (`\d` is `[0-9]`) |
| `\w+` | `café` | `café` | `caf` |
| `(?<=a+)b` | `aab` | error: needs fixed width | matches |
| `(a)?\1` | `b` | no match (unset group fails) | empty matches (unset group is empty) |
| `i` with flag `i` | `İ ı I i` | also matches `İ` and `ı` | only `I` and `i` |
| `(?<y>a)` / `(?P<y>a)` | `a` | second form only | first form only |

`differences.compare` runs your subject and a few automatic variants (a trailing newline,
digits swapped to Arabic-Indic, a non-ASCII word, an emoji) in both engines at once and reports
which variants disagree. It is differential testing: you do not need to know the answer, only
that two engines should agree and do not.

## Run it

```bash
python 05-engine-differences/main.py
```

Requires `node` on your PATH. Every row of the table above is an `assert` in `main.py`, so if
a future Python or Node changes one of these behaviours, this module tells you.

## Try breaking it

1. Add the `u` flag to the JavaScript run of `\w+` on `café`. Does it become Unicode-aware?
   (No: `u` changes escapes and astral handling, not `\w`.)
2. Run `k` with flag `i` against the Kelvin sign `K` in both engines, then with `iu`.
3. Add a "variable lookbehind" probe to `differences.PROBES`. Why does a probe that appends
   text not help here, and what would?

-> [Next: Module 06](../06-the-mcp-wrapper/README.md)
