'use strict';
// Child process for the JavaScript engine: one JSON request on stdin, one JSON line per case.
// The pattern goes to `new RegExp` as DATA and is never evaluated as code.
const fs = require('fs');
const req = JSON.parse(fs.readFileSync(0, 'utf8'));

function out(o) { fs.writeSync(1, JSON.stringify(o) + '\n'); }

// JavaScript counts UTF-16 units, Python counts code points: convert so spans compare equal.
function cp(s, i) { return Array.from(s.slice(0, i)).length; }

let re;
try {
  re = new RegExp(req.pattern, 'dg' + req.flags);
} catch (e) {
  out({ error: 'compile: ' + e.message });
  process.exit(0);
}
req.subjects.forEach((s, i) => {
  const matches = [];
  for (const m of s.matchAll(re)) {
    matches.push({
      start: cp(s, m.index), end: cp(s, m.index + m[0].length), text: m[0],
      groups: m.slice(1).map((g) => (g === undefined ? null : g)),
    });
  }
  out({ case: i, matches });
});
out({ done: true });
