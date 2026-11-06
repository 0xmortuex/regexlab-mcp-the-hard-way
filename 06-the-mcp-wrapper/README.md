# Module 06: The MCP Wrapper

## The Concept

MCP is JSON-RPC over a pipe. The client launches your server as a subprocess, writes requests
to its stdin and reads responses from its stdout. Everything the model knows about your
server comes from three things: the **tool names**, the **descriptions** (your docstrings),
and the **text you return**.

`server.py` exposes modules 02 to 05 as three tools:

| Tool | Backed by |
|------|-----------|
| `test_regex` | module 05 (both engines, side by side) |
| `explain_regex` | modules 01 and 02 |
| `check_backtracking` | module 04 (which uses module 03's sandbox) |

## Design choices that matter

**Few tools, rich descriptions.** The docstring says *when* to use the tool ("use this before
telling the user a regex works"), what the arguments mean, and what a result contains. The
description is the model's only manual.

**Errors the model can act on.** With `mcp>=2`, the client only sees the message of a
`ToolError`; any other exception turns into a generic "Error executing tool". So `tool()`
wraps expected failures (a bad pattern, an engine problem) into `ToolError` with a useful text:

```
invalid pattern: missing ), unterminated subpattern at position 0
```

A genuine bug is deliberately left alone, so it stays visible as a bug.

**An engine failing is a result, not an error.** In `test_regex`, if the pattern does not
compile in JavaScript, the tool still returns Python's matches and a line saying
`javascript: ERROR ...`. That is the useful answer: "this pattern is only valid in Python".

**stdout belongs to the protocol.** A stray `print()` in a stdio server corrupts the JSON-RPC
stream. Log to stderr.

## Run it

```bash
python 06-the-mcp-wrapper/main.py
```

`main.py` is a real MCP client: it launches `server.py` over stdio, performs the handshake,
lists the tools, calls each, and checks that an error message survives the trip.

To use the server with Claude Code:

```bash
claude mcp add regexlab-tutorial -- python /full/path/to/06-the-mcp-wrapper/server.py
```

## Try breaking it

1. Add `print("hello")` at the top of `test_regex` and rerun. What does the client report?
2. Change `ToolError(...)` to a bare `raise` in the wrapper. What does `explain_regex "(oops"`
   return to the client now?
3. Rewrite the `check_backtracking` docstring to `"""Check."""`. Would you know when to call it?

-> [Next: Module 07](../07-testing-it-for-real/README.md)
