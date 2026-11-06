"""Run every module's main.py, the way CI does.

Each main.py checks its own results with assert (or a unittest run), so a chapter
whose code drifts out of sync with what its README claims fails here.

Usage: python verify.py            # all modules
       python verify.py 03 05      # just these
"""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    if shutil.which("node") is None:
        print("node is required (module 05 runs patterns in JavaScript): install Node.js first")
        return 2
    wanted = sys.argv[1:]
    modules = sorted(glob.glob(os.path.join(ROOT, "[0-9][0-9]-*", "main.py")))
    if wanted:
        modules = [m for m in modules if os.path.basename(os.path.dirname(m))[:2] in wanted]
    if not modules:
        print("no modules matched")
        return 2
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    failed = []
    for path in modules:
        name = os.path.basename(os.path.dirname(path))
        t0 = time.time()
        proc = subprocess.run([sys.executable, path], cwd=ROOT, env=env, text=True,
                              encoding="utf-8", errors="replace", capture_output=True,
                              timeout=300)
        ok = proc.returncode == 0
        print(f"{'PASS' if ok else 'FAIL'}  {name}  ({time.time() - t0:.1f}s)")
        if not ok:
            failed.append(name)
            print(proc.stdout[-2000:])
            print(proc.stderr[-2000:])
    print()
    print(f"{len(modules) - len(failed)}/{len(modules)} modules passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
