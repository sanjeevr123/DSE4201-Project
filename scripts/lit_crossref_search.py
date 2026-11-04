"""
Literature verification, stage 0: for each query, list the top Crossref candidates (the Crossref REST API, a registry of publisher
metadata) so that a human can choose the right record. Nothing here is a verification by itself.
  .venv/bin/python scripts/lit_crossref_search.py QUERIES.txt     (one query per line: KEY | free-text query)
Writes the raw responses to notes/literature/cache/ (not committed) and prints a compact candidate list.
"""
import json, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "notes" / "literature" / "cache"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "thesis-citation-check/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main(path):
    CACHE.mkdir(parents=True, exist_ok=True)
    for line in Path(path).read_text().splitlines():
        if "|" not in line:
            continue
        key, q = [x.strip() for x in line.split("|", 1)]
        url = "https://api.crossref.org/works?" + urllib.parse.urlencode(
            {"query.bibliographic": q, "rows": 3, "select": "DOI,title,author,container-title,issued,volume,issue,page,type,score"})
        try:
            d = get(url)
        except Exception as e:
            print(f"## {key}: ERROR {e}")
            continue
        (CACHE / f"search_{key}.json").write_text(json.dumps(d))
        print(f"## {key}  <- {q[:70]}")
        for it in d["message"]["items"]:
            au = ", ".join((a.get("family") or a.get("name", "?")) for a in it.get("author", [])[:4])
            yr = it.get("issued", {}).get("date-parts", [[None]])[0][0]
            print(f"   {it['DOI']} | {au} | {yr} | {(it.get('title') or ['?'])[0][:80]} | {(it.get('container-title') or ['-'])[0][:40]} {it.get('volume','')}({it.get('issue','')}) {it.get('page','')} | {it['type']} | score {it.get('score',0):.0f}")
        time.sleep(0.4)


if __name__ == "__main__":
    main(sys.argv[1])
