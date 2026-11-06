"""Run one pattern in both engines on targeted inputs, and say where they disagree."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import engines  # noqa: E402

ARABIC_INDIC = {ord(str(d)): chr(0x660 + d) for d in range(10)}

# Variants of the user's subject that expose the classic differences.
PROBES = {
    "trailing newline": lambda s: s + "\n",
    "Arabic-Indic digits": lambda s: s.translate(ARABIC_INDIC),
    "non-ASCII word": lambda s: s + " café",
    "emoji": lambda s: s + " \U0001F600",
}


def compare(pattern: str, subject: str, flags: str = "") -> dict[str, dict[str, object]]:
    """label -> {"python": matches or error, "javascript": ..., "agree": bool}"""
    labelled = {"your subject": subject} | {k: fn(subject) for k, fn in PROBES.items()}
    subjects = list(labelled.values())
    results: dict[str, dict[str, object]] = {label: {} for label in labelled}
    per_engine: dict[str, list | str] = {}
    for engine in ("python", "javascript"):
        try:
            per_engine[engine] = engines.run(engine, pattern, subjects, flags)
        except engines.EngineError as e:
            per_engine[engine] = str(e)
    for i, label in enumerate(labelled):
        row = results[label]
        for engine, res in per_engine.items():
            row[engine] = res if isinstance(res, str) else res[i]
        row["agree"] = row["python"] == row["javascript"]
    return results
