"""Child process: time pattern.search on a growing input, printing each timing at once."""

import json
import re
import sys
import time

req = json.loads(sys.stdin.read())
pat = re.compile(req["pattern"])
for n in req["sizes"]:
    subject = req["prefix"] + req["unit"] * n + req["suffix"]
    t0 = time.perf_counter()
    pat.search(subject)
    ms = (time.perf_counter() - t0) * 1000
    print(json.dumps({"n": n, "ms": ms}), flush=True)
