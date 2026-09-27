"""
HISTORICAL / SUPERSEDED: kept only as an audit trail. WP2's aggregation
now lives in src/wp2_simulation.py (aggregate_scenario). Do not import
from or edit this file for current work.
"""
import json, sys
import numpy as np
from collections import defaultdict

def summarize(path):
    res = json.load(open(path))
    by = defaultdict(list)
    for r in res:
        by[r["scen"]].append(r)
    out = {}
    for s, rs in by.items():
        n = len(rs)
        def rej(pair, one_sided=True):
            t = np.array([r["dm"][pair][0] for r in rs])
            return float(np.mean(t < -1.645)) if one_sided else float(np.mean(np.abs(t) > 1.96))
        def worse(pair):
            t = np.array([r["dm"][pair][0] for r in rs])
            return float(np.mean(t > 1.645))
        def dmean(a, b):
            d = np.array([r["loss"][a] - r["loss"][b] for r in rs])
            return float(d.mean()), float(d.std(ddof=1) / np.sqrt(n))
        models = list(rs[0]["loss"].keys())
        real = [m for m in models if not m.startswith("Oracle")]
        best = defaultdict(int)
        for r in rs:
            best[min(real, key=lambda m: r["loss"][m])] += 1
        out[s] = dict(
            n=n,
            regime_acc=float(np.mean([r["regime_acc"] for r in rs])),
            stress_share=float(np.mean([r["stress_share"] for r in rs])),
            power_DB=rej("D-B"), wrong_DB=worse("D-B"),
            power_oracle_DB=rej("Oracle_D-Oracle_B"),
            power_CA=rej("C-A"), power_BA=rej("B-A"),
            D_beats_GARCH=rej("D-GARCHt"), B_beats_GARCH=rej("B-GARCHt"),
            GARCH_beats_D=worse("D-GARCHt"), GARCH_beats_B=worse("B-GARCHt"),
            D_beats_EWMA=rej("D-EWMA"), D_beats_HS=rej("D-HS"),
            dloss_DB=dmean("D", "B"), dloss_BA=dmean("B", "A"),
            dloss_oracle=dmean("Oracle_D", "Oracle_B"),
            hit={m: float(np.mean([r["hit"][m] for r in rs])) for m in models},
            kupiec_rej={m: float(np.mean([r["kupiec_p"][m] < 0.05 for r in rs])) for m in models},
            loss={m: float(np.mean([r["loss"][m] for r in rs])) for m in models},
            best=dict(best),
        )
    return out

if __name__ == "__main__":
    for p in sys.argv[1:]:
        print("=====", p)
        print(json.dumps(summarize(p), indent=1))
