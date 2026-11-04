"""
Wording check (docs/THESIS_PLAN.md 2.B.1, 2.A.3). Fails on phrases that overstate what a comparison isolates or that
read a non-significant result as evidence of no effect.

  .venv/bin/python scripts/check_wording.py FILE [FILE ...]

Text is checked one paragraph at a time. CONDITIONAL phrases pass only when their paragraph also matches the stated
requirement. A paragraph containing the marker `wording-ok` is skipped and counted in the report, for example when the
text quotes a banned phrase in order to define the rule. Exit code 1 if anything is found.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

BANNED = [
    r"no effect", r"no correlation channel", r"correlation does not matter", r"does not help", r"no gain",
    r"no improvement", r"adds nothing", r"ruled out", r"rules out", r"well[- ]powered", r"confirms the absence",
    r"evidence that regimes do not", r"the null result shows", r"honest null",
    # plan 2.A.3 and errors E1-E15
    r"attribute[sd]? (the|an) improvement to a single ingredient", r"nested .?ladder", r"nested models",
    r"controlled ablation", r"isolates volatility", r"volatility evolve within a regime",
    r"differ only in how volatility", r"mean treatment does not explain", r"automatic lag selection",
    r"without rebalancing", r"no rebalancing", r"never used for forecasting", r"only filtered probabilities",
    r"about half of what", r"8\.800%", r"1992-2009 fund sample", r"too conservative",
]
INTERVAL = r"(\bCI\b|confidence interval|95% interval|\[[-+−]?\d|minimum detectable)"
CONDITIONAL = [
    (r"indistinguishable", INTERVAL, "needs an interval"),
    (r"no detectable", INTERVAL, "needs an interval or MDE"),
    (r"5% level", r"(one-sided|two-sided|tail)", "must say which 5%"),
]


def paragraphs(text: str):
    start = 1
    for block in re.split(r"(\n\s*\n)", text):
        if block.strip():
            yield start, block
        start += block.count("\n")


def check(text: str):
    hits, skipped = [], 0
    for line, para in paragraphs(text):
        if "wording-ok" in para:
            skipped += 1
            continue
        for pat in BANNED:
            for m in re.finditer(pat, para, flags=re.I):
                hits.append((line, m.group(0), "banned"))
        for pat, need, why in CONDITIONAL:
            if re.search(pat, para, flags=re.I) and not re.search(need, para, flags=re.I):
                hits.append((line, pat, why))
    return hits, skipped


def main(paths) -> int:
    bad = 0
    for p in paths:
        hits, skipped = check(Path(p).read_text())
        bad += len(hits)
        print(f"{p}: {len(hits)} hit(s), {skipped} paragraph(s) marked wording-ok")
        for line, phrase, why in hits:
            print(f"  near line {line}: '{phrase}' ({why})")
    return 1 if bad else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1:]))
