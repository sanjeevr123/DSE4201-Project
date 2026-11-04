"""Quality gates for the thesis sources: citations both ways, [UNVERIFIED] and [PENDING] counts, unresolved
cross-references (from the last build log), word counts, and an originality check against a reference PDF
(no run of N or more consecutive words shared). Usage: .venv/bin/python scripts/check_thesis_gates.py [--ref PDF] [--n 8]"""
from __future__ import annotations
import re, sys, argparse
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; TEX = ROOT / "thesis" / "tex"

def words(t): return re.findall(r"[a-z0-9']+", t.lower())

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--ref"); ap.add_argument("--n", type=int, default=8)
    a = ap.parse_args(); bad = 0
    files = sorted((TEX / "chapters").glob("*.tex")) + sorted((TEX / "front").glob("*.tex")) + sorted((TEX / "generated").glob("*.tex"))
    src = "\n".join(f.read_text() for f in files)
    cited = set()
    for m in re.finditer(r"\\cite[a-z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}", src):
        cited |= {k.strip() for k in m.group(1).split(",")}
    bib = (TEX / "references.bib").read_text()
    keys = set(re.findall(r"@\w+\{([^,]+),", bib))
    print("cited but not in bib:", sorted(cited - keys)); print("in bib but not cited:", sorted(keys - cited))
    bad += len(cited - keys)
    print("[UNVERIFIED] marks:", src.count("\\unverified") + src.count("UNVERIFIED") + bib.count("UNVERIFIED"),
          "| [PENDING] marks:", src.count("\\pending{"), "| TO WRITE:", src.count("\\todo{"))
    log = (TEX / "build" / "main.log")
    if log.exists():
        und = set(re.findall(r"Reference `([^']+)'", log.read_text(errors="ignore")))
        print("undefined references:", sorted(und)); bad += len(und)
    labels = set(re.findall(r"\\label\{([^}]+)\}", src)); refs = set(re.findall(r"\\ref\{([^}]+)\}", src))
    print("refs without label:", sorted(refs - labels)); print("labels never referenced:", sorted(labels - refs)); bad += len(refs - labels)
    tot = 0
    for f in sorted((TEX / "chapters").glob("ch*.tex")):
        t = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?", " ", f.read_text()); n = len(words(t)); tot += n; print(f"  {f.name}: ~{n} words")
    print("  total chapters (incl. placeholders): ~", tot)
    if a.ref and Path(a.ref).exists():
        import pypdf
        rw = words(" ".join((p.extract_text() or "") for p in pypdf.PdfReader(a.ref).pages))
        grams = {tuple(rw[i:i + a.n]) for i in range(len(rw) - a.n + 1)}
        hits = 0
        for f in files:
            w = words(re.sub(r"\\[a-zA-Z]+\*?", " ", f.read_text()))
            for i in range(len(w) - a.n + 1):
                if tuple(w[i:i + a.n]) in grams: hits += 1; print("OVERLAP", f.name, " ".join(w[i:i + a.n]))
        print(f"originality: {hits} shared runs of {a.n}+ words with the reference"); bad += hits
    return 1 if bad else 0
if __name__ == "__main__": sys.exit(main())
