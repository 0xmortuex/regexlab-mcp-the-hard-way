# Module 02: Explaining

## The Concept

Explaining a regex is a tree walk. For each node, produce one line: the slice of source it
covers (that is what the spans from module 01 are for) and a sentence about what it does.
Groups open a line, recurse into their body at a deeper indent, then close with a line of
their own, which is also where a quantifier on the group (`)+`) gets described.

```
  (?P<user>  start of capture group 1, named "user"
    [\w.-]+  any one of a word character, ".", "-", one or more times (greedy: ...)
  )          end of group
```

## Words matter

The explanations carry the details that cause bugs, not just the syntax:

- a quantifier is described as **greedy** or **lazy**, because `.*` vs `.*?` is the most
  common source of a regex matching too much
- `\d` is described as "any Unicode decimal digit" for Python, because that is why validating
  a phone number with it lets Arabic-Indic digits through (module 05 proves this)

## Never explain what you did not parse

The `unsupported` nodes from module 01 become lines that start with `NOT EXPLAINED:` and quote
the construct. The last assertion in `main.py` checks that the number of output lines equals
the number of tokens, so nothing is skipped silently.

This is the same rule the real server follows. If a model is shown a confident explanation of
a construct the tool did not understand, it will repeat it to a user as fact.

## Run it

```bash
python 02-explaining/main.py
```

## Try breaking it

1. Change `lit()` to print characters raw. What happens to a pattern containing `\n` or a tab?
2. Delete the `unsupported` branch of `describe_leaf`. Which assertion fails, and is that the
   failure you want (an exception) or the one you would get in production (a silent wrong answer)?
3. The explainer knows nothing about flags. Python's `(?i)` and the `m` flag change what `^`
   means. Where would you thread a `flags` argument through, and which descriptions change?

-> [Next: Module 03](../03-running-safely/README.md)
