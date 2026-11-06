# Module 04: Backtracking

## The Concept

A backtracking engine tries a choice, and if the rest of the pattern fails it goes back and
tries the next choice. With `(a+)+$` on `aaaa...a!` there are exponentially many ways to split
the `a`s between the inner and outer repeat, and the engine tries all of them before it gives
up. Each extra `a` doubles the time. That is ReDoS: a regular expression denial of service.

## Two stages, because each alone is weak

| Stage | Reads | Strength | Weakness |
|-------|-------|----------|----------|
| **Static** | the tree from module 01 | instant, no input needed | only suspects; it over-warns |
| **Probe** | runs the pattern on nasty input | measures real behaviour | only knows what it tried |

**Static** (`static_suspects`): an unbounded repeat that contains another unbounded repeat:
`(a+)+`, `(\w+\s?)*`, `(.*)*`. This is a deliberately simple rule. It flags
`^(\d+,)+$` too, which is safe: the comma forces each iteration to end somewhere, so there is
only one way to split the input. The real server refines the rule with character-set overlap;
here the lesson is that **a static finding is a suspicion, not a verdict**.

**Probe** (`check`): build an input from the suspect repeat. `sample()` writes a short string
that the repeated part matches (`"a"` for `(a+)+`), repeat it `n` times, append a character
that makes the overall match fail (`!`), and time `pattern.search` for growing `n` in a child
process. If the child is still running at the budget it is killed (module 03) and the pattern is
reported as exponential with its slow input: `'a' * 26 + '!'`.

## A bug worth remembering

The first version of `sample()` wrote at least one copy of every optional part, so for
`(\w+\s?)*` the unit became `"a "` (a letter and a space). With a separator in every unit there
is only one way to split the input and the probe found nothing: a **false negative from a probe
that did not match the pattern's ambiguity**. Optional parts must stay out (the minimum
count). `main.py` asserts that this pattern is caught.

## Run it

```bash
python 04-backtracking/main.py
```

It checks three known-bad patterns (each takes about 2.5 seconds, the budget), one with no
suspicious shape, and `^(\d+,)+$`, which the static stage flags and the probe clears.

## Try breaking it

1. Change the suffix from `"!"` to `""`. Why does `(a+)+$` stop being slow? (The match
   succeeds, so nothing is backtracked.)
2. Add a second kind of danger: `.*.*=.*` is polynomial, not exponential. What would you
   probe, and how would you tell n^2 from 2^n using the timing points?
3. Python 3.11 added possessive quantifiers (`a++`) and atomic groups. Teach `static_suspects`
   to skip a repeat that is possessive.

-> [Next: Module 05](../05-engine-differences/README.md)
