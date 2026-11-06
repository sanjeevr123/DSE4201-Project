"""Rebuild every thesis table and figure from the saved result files, check the registered numbers, and build the PDF.

  .venv/bin/python scripts/build_all.py            # tables, figures, number check, PDF (needs tectonic)
  .venv/bin/python scripts/build_all.py --no-pdf   # skip the LaTeX build

Nothing here refits a model or touches the hold-out forecasts: the long computations (power studies, the exploration grid,
the hold-out run) are not repeated, and their saved outputs are read. The full recompute route is in the appendix of the thesis.
All steps are serial (n_jobs = 1); BLAS threads are fixed to 1 so the numbers do not depend on the machine's core count.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEPS = [("tables", ["scripts/thesis_tables.py"]),
         ("figure: forest plots", ["scripts/thesis_fig_forest.py"]),
         ("registered numbers", ["scripts/check_numbers.py"])]
CHAPTERS = sorted((ROOT / "thesis" / "tex" / "chapters").glob("ch*.tex"))


def run(cmd, env, cwd=ROOT):
    t0 = time.time()
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    return r, time.time() - t0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-pdf", action="store_true")
    args = ap.parse_args()
    env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1",
               MPLBACKEND="Agg")
    for name, cmd in STEPS:
        r, dt = run([sys.executable, *cmd], env)
        print(f"{'ok  ' if r.returncode == 0 else 'FAIL'} {name} ({dt:.1f} s)")
        if r.returncode:
            print(r.stdout[-2000:], r.stderr[-2000:])
            return 1
    if not args.no_pdf:
        r, dt = run(["sh", "thesis/tex/build.sh"], env)
        pdf = ROOT / "thesis" / "tex" / "build" / "main.pdf"
        bad = [l for l in (r.stdout + r.stderr).splitlines() if l.startswith("error") or "Undefined" in l]
        ok = r.returncode == 0 and pdf.exists() and not bad
        print(f"{'ok  ' if ok else 'FAIL'} PDF ({dt:.1f} s) {pdf.relative_to(ROOT)}")
        if not ok:
            print("\n".join(bad) or (r.stdout + r.stderr)[-2000:])
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
