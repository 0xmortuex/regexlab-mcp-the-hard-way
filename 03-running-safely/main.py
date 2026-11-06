"""Module 03: run patterns in a child process; prove a hang is killed, tree and all."""

import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pyengine  # noqa: E402
import sandbox  # noqa: E402


def pid_alive(pid: int) -> bool:
    if sys.platform == "win32":
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True,
                           text=True)
        return str(pid) in r.stdout
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    try:
        with open(f"/proc/{pid}/stat") as f:
            return f.read().rsplit(")", 1)[1].split()[0] != "Z"  # a zombie is dead
    except FileNotFoundError:
        return True


def wait_dead(pid: int) -> bool:
    for _ in range(100):
        if not pid_alive(pid):
            return True
        time.sleep(0.1)
    return False


TREE = """
import json, os, subprocess, sys, time
g = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
print(json.dumps({"child": os.getpid(), "grandchild": g.pid}), flush=True)
time.sleep(120)
"""


def main() -> None:
    # 1. normal use: exact matches
    out = pyengine.run(r"(\d+)-(\d+)", ["10-20 and 3-4", "nope"])
    assert out.error is None and not out.timed_out
    assert [(m["start"], m["end"], m["groups"]) for m in out.cases[0]] == \
        [(0, 5, ["10", "20"]), (10, 13, ["3", "4"])]
    assert out.cases[1] == []
    print("matches:", out.cases[0])

    # 2. a bad pattern is reported, not raised
    assert pyengine.run("(oops", ["x"]).error.startswith("compile:")

    # 3. a catastrophic pattern is cut off at the timeout
    t0 = time.perf_counter()
    hung = pyengine.run(r"(a+)+$", ["fine aaa", "a" * 60 + "!", "never reached"], timeout=1.5)
    wall = time.perf_counter() - t0
    assert hung.timed_out and wall < 15
    assert len(hung.cases) == 1, "case 1 finished before the hang and must be kept"
    print(f"hang killed after {wall:.1f}s; kept case 1: {hung.cases[0]}")

    # 4. the kill proof: the whole tree dies, not just the direct child
    res = sandbox.run([sys.executable, "-c", TREE], "", timeout=2.0)
    assert res.timed_out
    pids = json.loads(res.stdout.splitlines()[0])
    assert wait_dead(pids["child"]), "child survived"
    assert wait_dead(pids["grandchild"]), "grandchild survived"
    print("child and grandchild are both dead:", pids)

    # 5. pattern text is data: shell metacharacters do nothing
    pyengine.run("a; touch /tmp/pwned & echo $(id) > pwned.txt", ["x"])
    assert not os.path.exists("pwned.txt")
    print("\nmodule 03 ok")


if __name__ == "__main__":
    main()
