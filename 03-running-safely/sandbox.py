"""Run a command with a hard timeout and kill its whole process tree."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass


@dataclass
class Result:
    stdout: str
    stderr: str
    timed_out: bool
    elapsed: float


def kill_tree(proc: subprocess.Popen[bytes]) -> None:
    if sys.platform == "win32":
        # /T kills the children too. No shell: taskkill is a normal executable.
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                       capture_output=True, check=False)
    else:
        # The child was started with start_new_session=True, so its pid is also the
        # id of its process group; killing the group kills the grandchildren.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    proc.wait(timeout=10)


def run(argv: list[str], stdin_text: str, timeout: float) -> Result:
    """Run argv (a list: never a shell string), feeding it stdin_text."""
    t0 = time.perf_counter()
    if sys.platform == "win32":
        proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, creationflags=0x08000000)
    else:
        proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, start_new_session=True)
    timed_out = False
    try:
        out, err = proc.communicate(stdin_text.encode("utf-8"), timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        kill_tree(proc)
        out, err = proc.communicate()  # whatever the child managed to print before dying
    return Result(out.decode("utf-8", "replace"), err.decode("utf-8", "replace"),
                  timed_out, time.perf_counter() - t0)
