# regexlab-mcp - The Hard Way

Build an MCP server that lets an AI agent test, explain and stress-test regular expressions
by **running them in real engines**. You write the parser, the sandbox, the ReDoS probe and
the MCP wrapper yourself, in plain Python, and every module ends in a check that actually
runs.

At the end you will have built a minimal version of
[regexlab-mcp](https://github.com/0xmortuex/regexlab-mcp), and you will understand the three
things that make a regex tool trustworthy: **a real syntax tree instead of string tricks**,
**a sandbox that can kill a runaway match**, and **honesty about what you did not check**.

## Why This Exists

Language models write regexes that look right and are subtly wrong: a `$` that accepts a
trailing newline, a `\d` that matches Arabic digits, `(a+)+$` that freezes a server, a Python
named group pasted into JavaScript. A model cannot tell by reading, but a machine can tell by
running. The interesting engineering is not "call `re.findall`". It is:

- parsing the pattern yourself, so you can explain it and reason about it
- running untrusted patterns without letting one hang the process forever
- measuring catastrophic backtracking instead of guessing at it
- comparing engines that disagree on the same pattern
- returning errors an agent can act on

## Prerequisites

- Python 3.10+ and basic regex knowledge
- [Node.js](https://nodejs.org) (module 05 runs patterns in JavaScript too)
- `pip install -r requirements.txt` (just `mcp` and `anyio`; everything else is the standard library)

## Modules

| # | Module | What You'll Build |
|---|--------|-------------------|
| 01 | [Syntax Tree](01-syntax-tree/) | A parser from pattern text to a tree where every node knows its source span, with precise errors |
| 02 | [Explaining](02-explaining/) | A token-by-token plain-English explainer that says "not explained" instead of guessing |
| 03 | [Running Safely](03-running-safely/) | A child-process sandbox with a hard timeout and a process-tree kill, plus the proof that it works |
| 04 | [Backtracking](04-backtracking/) | A static ReDoS scan and an empirical timing probe, and why you need both |
| 05 | [Engine Differences](05-engine-differences/) | Python and JavaScript side by side: `$`, `\d`, lookbehind, named groups, Turkish i |
| 06 | [The MCP Wrapper](06-the-mcp-wrapper/) | Three tools over stdio, descriptions a model can use, and errors that reach it |
| 07 | [Testing It For Real](07-testing-it-for-real/) | A test suite that uses real engines and real processes, with the kill proof |

Each module has a `README.md` (the why), runnable code, and a `main.py` that checks its own
results with `assert`. Modules build on each other by importing the earlier module's files.

## Verify

```bash
pip install -r requirements.txt
python verify.py          # runs every module's main.py; non-zero exit on any failure
python verify.py 03 05    # just these modules
```

CI runs this on Ubuntu and Windows.

## What the real server adds

This tutorial is deliberately small. [regexlab-mcp](https://github.com/0xmortuex/regexlab-mcp)
adds the optional third-party `regex` engine, a much fuller parser (lookbehind, atomic groups,
possessive quantifiers, inline flags, verbose mode), a Windows Job Object memory cap, polynomial
ReDoS detection, pattern conversion between Python and JavaScript, substitution previews, and
test generation that verifies its own examples.

## License

MIT
