"""
Monte Carlo pilot: can the design detect the correlation channel?
Data-generating process: 2-state Markov-switching multivariate Student-t
(df=6) for three assets resembling US equities, 7-10y Treasuries and gold.
Parameters are ASSUMED stylised values, not estimates.
"""
import sys, json, time
import numpy as np
from multiprocessing import Pool
from pilot_core import walk_forward, score

VOL_CALM = np.array([0.0075, 0.0030, 0.0090])
VOL_STRESS = np.array([0.0200, 0.0050, 0.0160])
P = np.array([[0.99, 0.01], [0.03, 0.97]])
DF = 6
W = np.ones(3) / 3

def corr(a, b, c):  # (eq-bond, eq-gold, bond-gold)
    return np.array([[1, a, b], [a, 1, c], [b, c, 1]])

CALM = corr(-0.30, 0.05, 0.30)
SCENARIOS = {
    "S0_vol_only":          corr(-0.30, 0.05, 0.30),
    "S1_moderate_breakdown": corr(0.00, 0.20, 0.30),
    "S2_strong_breakdown":  corr(0.40, 0.40, 0.30),
    "S3_flight_to_quality": corr(-0.55, -0.10, 0.40),
}

def cov(v, C):
    return np.outer(v, v) * C

def simulate(stress_corr, T, rng):
    S = np.empty(T, dtype=int)
    S[0] = 0
    for t in range(1, T):
        S[t] = rng.random() < P[S[t - 1], 1]
    covs = [cov(VOL_CALM, CALM), cov(VOL_STRESS, stress_corr)]
    L = [np.linalg.cholesky(c) for c in covs]
    z = rng.standard_normal((T, 3))
    g = rng.chisquare(DF, T) / DF
    z = z / np.sqrt(g)[:, None] * np.sqrt((DF - 2) / DF)  # unit-variance t
    R = np.empty((T, 3))
    for k in range(2):
        m = S == k
        R[m] = z[m] @ L[k].T
    # oracle predictive probs P(S_{t}|S_{t-1}) known
    pred = np.vstack([[1.0, 0.0], P[S[:-1]]])
    true_covs = {"B": [cov(VOL_CALM, CALM), cov(VOL_STRESS, CALM)],
                 "D": covs}
    # Oracle_B keeps the calm correlation in both states (vol-only truth)
    return R, S, pred, true_covs

def one_rep(args):
    scen, rep, alpha = args
    rng = np.random.default_rng(10_000 * list(SCENARIOS).index(scen) + rep)
    T = 1260 + 2520
    R, S, pred, tc = simulate(SCENARIOS[scen], T, rng)
    res = walk_forward(R, W, start=1260, window=1260, alpha=alpha,
                       true_pred=pred, true_covs=tc, seed=rep)
    sc = score(res, alpha, pairs=(("D", "B"), ("C", "A"), ("B", "A"),
                                  ("D", "A"), ("B", "GARCHt"), ("D", "GARCHt"),
                                  ("Oracle_D", "Oracle_B"), ("B", "EWMA"),
                                  ("D", "EWMA"), ("D", "HS")))
    # regime detection accuracy in the test period (predictive prob vs truth)
    s_true = S[res["idx"]]
    acc = np.mean((res["stress_prob"] > 0.5) == s_true)
    return dict(scen=scen, rep=rep, alpha=alpha,
                loss=sc["loss"], hit=sc["hit"], kupiec_p=sc["kupiec_p"],
                dm={k: list(v) for k, v in sc["dm"].items()},
                regime_acc=acc, stress_share=float(s_true.mean()))

if __name__ == "__main__":
    reps = int(sys.argv[1]); alpha = float(sys.argv[2]); out = sys.argv[3]
    jobs = [(s, r, alpha) for s in SCENARIOS for r in range(reps)]
    t0 = time.time()
    with Pool(2) as pool:
        results = pool.map(one_rep, jobs, chunksize=1)
    json.dump(results, open(out, "w"))
    print(f"done {len(results)} in {time.time()-t0:.0f}s")
