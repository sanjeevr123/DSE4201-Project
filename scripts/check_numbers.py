"""Check that every number registered in thesis/numbers.yaml (a) is recomputed from its result file to the stated
text and (b) occurs in the named chapter file. Usage: .venv/bin/python scripts/check_numbers.py
Entry kinds: csv (filter rows, take a column, optional abs/scale/div, format), json (dotted path), count_headline
(D-vs-B headline tests in backtest_dm_table.csv), doc (a string must occur in a document).
Registered numbers only: unregistered numbers in prose are caught by the Phase 9 trace, not here."""
from __future__ import annotations
import json, sys
from pathlib import Path
import pandas as pd, yaml

ROOT = Path(__file__).resolve().parents[1]
TEX = ROOT / "thesis" / "tex" / "chapters"


def value(e):
    f = ROOT / e["file"]
    k = e["kind"]
    if k == "csv":
        df = pd.read_csv(f)
        for c, v in e["where"].items():
            df = df[df[c] == v]
        assert len(df) == 1, f"{e['id']}: {len(df)} rows"
        x = float(df[e["column"]].iloc[0])
    elif k == "json":
        x = json.loads(f.read_text())
        for p in e["path"].split("."):
            x = x[p]
        x = float(x)
    elif k == "count_headline":
        df = pd.read_csv(f)
        h = df[df.p_holm_headline.notna()]
        x = {"n": len(h), "raw": int((h.p < 0.05).sum()), "fav_d": int(((h.p < 0.05) & (h.mean_diff < 0)).sum()),
             "fav_b": int(((h.p < 0.05) & (h.mean_diff > 0)).sum()), "min_holm": float(h.p_holm_headline.min()),
             "share": float((h.p < 0.05).mean())}[e["column"]]
    else:
        raise ValueError(k)
    if e.get("abs"): x = abs(x)
    if "div" in e: x = x / e["div"]
    if "scale" in e: x = x * e["scale"]
    return format(x, e["fmt"])


def main() -> int:
    ents = yaml.safe_load((ROOT / "thesis" / "numbers.yaml").read_text())
    bad = 0
    for e in ents:
        try:
            if e["kind"] == "doc":
                ok_val = e["text"] in (ROOT / e["file"]).read_text()
                got = e["text"]
            else:
                got = value(e)
                ok_val = got == e["text"]
        except Exception as ex:  # noqa
            print("ERROR", e["id"], ex); bad += 1; continue
        ok_txt = e["text"] in (TEX / e["chapter"]).read_text()
        if not (ok_val and ok_txt):
            bad += 1
            print(f"FAIL {e['id']}: file gives {got!r}, registered {e['text']!r}, in chapter: {ok_txt}")
    print(f"{len(ents)} numbers checked, {bad} problems")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
