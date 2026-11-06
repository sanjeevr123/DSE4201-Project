"""Clone the repository at HEAD into a temporary directory, run scripts/build_all.py there, and compare every generated
table (bytes), figure (decoded pixels) and the PDF text with the working copy. Usage:
  .venv/bin/python scripts/verify_clean_clone.py
The clone contains only committed files, so it shows whether the build depends on anything untracked. Exit 1 on any difference.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]


def pix(p):
    return hashlib.sha256(np.asarray(Image.open(p).convert("RGBA")).tobytes()).hexdigest()


def pdf_text(p):
    return "\n".join(pg.extract_text() for pg in PdfReader(p).pages)


def main() -> int:
    dirty = subprocess.run(["git", "status", "--porcelain", "--", "src", "scripts", "thesis", "output/explore", "output/confirm/holdout",
                            "data", "tests"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if dirty:
        print("working copy has uncommitted changes; commit first:\n" + dirty)
        return 1
    with tempfile.TemporaryDirectory(prefix="thesis_clone_") as tmp:
        clone = Path(tmp) / "repo"
        subprocess.run(["git", "clone", "-q", str(ROOT), str(clone)], check=True)
        r = subprocess.run([sys.executable, "scripts/build_all.py"], cwd=clone, capture_output=True, text=True)
        print(r.stdout, r.stderr[-1500:])
        if r.returncode:
            return 1
        problems = []
        for f in sorted((ROOT / "thesis/tex/generated").glob("*.tex")):
            g = clone / "thesis/tex/generated" / f.name
            if not g.exists() or g.read_bytes() != f.read_bytes():
                problems.append(f"table differs: {f.name}")
        for f in sorted((ROOT / "output/figures").glob("forest_comparisons_*.png")):
            g = clone / "output/figures" / f.name
            if not g.exists() or pix(g) != pix(f):
                problems.append(f"figure differs: {f.name}")
        a, b = pdf_text(ROOT / "thesis/tex/build/main.pdf"), pdf_text(clone / "thesis/tex/build/main.pdf")
        if a != b:
            problems.append("PDF text differs")
        n_tab = len(list((ROOT / "thesis/tex/generated").glob("*.tex")))
        print(f"compared {n_tab} tables, 3 figures, PDF text ({len(b.split())} words)")
        print("MATCH" if not problems else "\n".join(problems))
        return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
