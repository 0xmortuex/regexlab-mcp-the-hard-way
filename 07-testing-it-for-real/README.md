# Module 07: Testing It For Real

## The Concept

A regex tool is easy to test badly. If your tests mock the engine, they prove your mock works.
Everything this server promises is about real behaviour: what `re` does, what V8 does, that a
hung process really dies. So the tests use the real things, with exact expected values.

`tests.py` (standard-library `unittest`, no extra dependencies) contains:

| Group | What it proves |
|-------|----------------|
| `ParserTests` | every syntax error carries a position; unsupported syntax is marked, not guessed |
| `SandboxTests` | **the kill proof**: a grandchild process is dead after the timeout; a hang is bounded and keeps the cases that finished |
| `BacktrackTests` | known ReDoS patterns are confirmed *inside the time budget* (the test must not hang CI); safe patterns are not flagged |
| `EngineFactTests` | exact spans per engine for `$`, `\d`, astral characters, the Turkish dotless i, and dialect-specific group syntax |
| `StdioTests` | the real server is launched over stdio, its tools listed and called, and an error message crosses the wire |

## Lessons baked into the tests

- **Assert the engine's behaviour, not your belief about it.** The Turkish-i test only asserts
  what is stable: JavaScript never maps `İ`/`ı` onto ASCII `i`, and Python does map
  `ı`. Details that differ between Python versions are not pinned.
- **Tests that exercise a timeout need an upper bound on wall-clock time**, or a regression
  turns into a hung CI job instead of a failing test.
- **Skip, don't fail, when an optional engine is missing.** The tutorial requires `node`, so
  `@needs_node` is a no-op in CI, but the real server's suite uses the same pattern so that
  `node`-free machines still run everything else.
- **Don't depend on unrelated machine state.** The liveness check treats a Linux zombie as
  dead, and uses `tasklist` on Windows instead of signalling the pid.

## Run it

```bash
python 07-testing-it-for-real/main.py
```

or the whole tutorial the way CI does it:

```bash
python verify.py
```

## Try breaking it

1. In `sandbox.kill_tree`, kill only `proc` (`proc.kill()`) on every platform. Which test
   fails, and does the failure message point at the cause?
2. Raise the budget in `backtrack.check` to 60 seconds. Which tests would now be slow, and what
   bound would you put on them?
3. Add a test for a pattern you wrote yesterday. Run it in both engines before you decide what
   the expected value is.

## Where to go from here

You have built a small version of the real thing. [regexlab-mcp](https://github.com/0xmortuex/regexlab-mcp)
is the same architecture with a fuller parser, polynomial ReDoS detection, a third engine,
pattern conversion, substitution previews and verified test generation.
