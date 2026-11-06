# Module 03: Running Safely

## The Concept

The tester is the dangerous part. A regex engine can spend hours on a short input
(`(a+)+$` against 30 `a`s and a `!`), and Python's `re` is C code that never checks for
interruption: you cannot cancel it from a thread, with a signal handler, or with
`asyncio.timeout`. The only reliable way to stop it is to run it **in another process** and
kill that process.

```
  your server                      child process
  ───────────                      ─────────────
  sandbox.run(argv, stdin, 5s) ──► python -I runner.py  (reads JSON on stdin)
        │                              │ re.compile(pattern)   <- pattern is DATA
        │ ◄── one JSON line per case ──┤ finditer(...)
        │ timeout? kill the TREE
```

## Five rules the code follows

1. **A list, never a shell string.** `subprocess.Popen([...])` with no `shell=True`. The
   pattern never touches a command line; it goes in as JSON on stdin.
2. **The pattern is data.** `runner.py` calls `re.compile(req["pattern"])`. There is no
   `eval`, no `exec`, no string formatting into code.
3. **A hard timeout, then kill the whole tree.** On POSIX the child is started with
   `start_new_session=True`, so its pid is a process-group id and `os.killpg` takes out
   grandchildren as well. On Windows `taskkill /F /T` does the same. (The full server also uses
   a Job Object there.)
4. **Flush every result line.** `runner.py` prints and flushes after each case. If case 2
   hangs, case 1's answer is already in the pipe and `communicate()` returns it after the kill.
   The user learns *which* input hung.
5. **Cap the inputs.** Number of cases and total text are limited before anything runs.

## The proof

A claim like "we kill the process tree" is exactly the kind of thing that is quietly false.
`main.py` therefore starts a parent that spawns a grandchild, prints both pids, and sleeps.
After the 2-second timeout it checks, by pid, that **both are dead**. A zombie counts as dead
(on Linux a killed child that nobody has reaped still has a `/proc` entry in state `Z`).

## Run it

```bash
python 03-running-safely/main.py
```

## Try breaking it

1. Remove `start_new_session=True` on Linux or macOS and replace the group kill with
   `proc.kill()`. Does the grandchild survive? That is the bug the proof test catches.
2. Delete the `flush=True` in `runner.py`. What does the "kept case 1" assertion see now?
3. Add `import os; os.system(req["pattern"])` to the runner and read it back: it works. Why is
   that exactly what rule 2 forbids, and what would the tests need to look like to catch it?

-> [Next: Module 04](../04-backtracking/README.md)
