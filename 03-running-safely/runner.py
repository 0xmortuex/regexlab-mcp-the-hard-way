"""The child process: reads one JSON request on stdin, prints one JSON line per case.

The pattern is passed to re.compile as DATA. Nothing from the request is ever
evaluated as code. Each line is flushed so that, if we are killed in the middle of
case 3, the parent still has the results of cases 1 and 2.
"""

import json
import re
import sys

req = json.loads(sys.stdin.read())
flag_map = {"i": re.I, "m": re.M, "s": re.S}
flags = 0
for f in req["flags"]:
    flags |= flag_map[f]
try:
    pat = re.compile(req["pattern"], flags)
except re.error as e:
    print(json.dumps({"error": f"compile: {e}"}), flush=True)
    sys.exit(0)

for i, subject in enumerate(req["subjects"]):
    matches = [{"start": m.start(), "end": m.end(), "text": m.group(0), "groups": list(m.groups())}
               for m in pat.finditer(subject)]
    print(json.dumps({"case": i, "matches": matches}), flush=True)
print(json.dumps({"done": True}), flush=True)
