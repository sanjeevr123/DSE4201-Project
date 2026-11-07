"""Generate the LaTeX tables of Chapters 5 and 6 from saved result files (no manual numbers).

Reads exploration, simulation and confirm/ files. Until 2026-11-05 only files that stop at 2019-12-31 or are simulations; the
hold-out tables (tab_holdout_*.tex) read output/confirm/holdout/ and exist only after the single scored run. Writes
thesis/tex/generated/*.tex. Every table reports: richer-minus-baseline mean loss difference (negative favours the
richer model), HAC standard error, two-sided 95% interval d +/- 1.96 SE, t, a labelled two-sided p-value, n, and the
minimum detectable difference MDE = 2.8016 SE (two-sided 5% test, 80% power).

Usage: .venv/bin/python scripts/thesis_tables.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "thesis" / "tex" / "generated"
LAD = ROOT / "output" / "explore" / "ladder"
Z = 1.96
SAMPLES = {"U1_pilot": "SPY/IEF/GLD", "U3_credit": "SPY/IEF/HYG", "U8_sectors": "Sectors",
           "U10_riskassets": "Risk assets", "L1_longhist": "Funds 1992--2019"}


def f4(x): return f"{x:.4f}".replace("-", "$-$")
def f3(x): return f"{x:.3f}".replace("-", "$-$")
def f2(x): return f"{x:.2f}".replace("-", "$-$")
def pct(x): return f"{100 * x:.1f}\\%"


def pfmt(p):
    return "$<$0.001" if p < 0.001 else f"{p:.3f}"


def ci(d, se): return f"[{f4(d - Z * se)}, {f4(d + Z * se)}]"


def write(name, text):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(text)


def ladder_rows(df, step):
    sub = df[(df.alpha == 0.05) & (df.period == "full") & (df.mean_set == "pooled") & (df.chain == "N")
             & (df.step == step)].set_index("universe")
    return [(SAMPLES[u], sub.loc[u]) for u in SAMPLES]


def ladder_panel(df, step, title, holm=False):
    rows = []
    for name, r in ladder_rows(df, step):
        extra = ""
        if holm:
            ph = r.p_holm_primary
            extra = " & " + (("\\textbf{" + f4(ph) + "}" if ph < 0.05 else f4(ph)) if pd.notna(ph) else "--")
        rows.append(f"{name} & {int(r.n):,} & {f4(r.mean_diff)} & {f4(r.se)} & {ci(r.mean_diff, r.se)} & {f2(r.t)} & "
                    f"{pfmt(r.p)} & {f4(r.mde80)}{extra} \\\\")
    cols = 8 + (1 if holm else 0)
    return f"\\multicolumn{{{cols}}}{{l}}{{\\textbf{{{title}}}}}\\\\\n" + "\n".join(rows) + "\n"


def ladder_table(df, name, caption, label, panels, note, holm_step=None):
    holm = holm_step is not None
    head = ("Sample & $n$ & $\\bar d$ & SE & 95\\% interval & $t$ & $p$ (2-sided) & MDE" + (" & Holm $p$" if holm else ""))
    cs = "lrrrcrrr" + ("r" if holm else "")
    body = ""
    for step, title in panels:
        body += ladder_panel(df, step, title, holm=(holm and step == holm_step)) if True else ""
        body += "\\midrule\n"
    body = body.rsplit("\\midrule\n", 1)[0]
    if holm:  # panels without a Holm column still need the cell
        pass
    size = "\\scriptsize" if holm else "\\footnotesize"
    txt = (f"\\begin{{table}}[t]\n\\centering\\setstretch{{1}}{size}\\setlength{{\\tabcolsep}}{{5pt}}\n\\caption{{\\uc{{{caption}}}}}\\label{{{label}}}\n"
           f"\\begin{{tabular}}{{{cs}}}\n\\toprule\n{head} \\\\\n\\midrule\n{body}\\bottomrule\n\\end{{tabular}}\n"
           f"\\tabnote{{{note}}}\n\\end{{table}}\n")
    write(name, txt)


def main():
    df = pd.read_csv(LAD / "ladder_dm_table.csv")
    note_common = ("Mean FZ0 difference $\\bar d$ of the richer model minus the baseline over the forecast days, "
                   "tail level $\\alpha=5\\%$, Gaussian chain, pooled mean; negative favours the richer model. SE: "
                   "Bartlett-kernel HAC standard error. The interval is $\\bar d\\pm1.96\\,\\mathrm{SE}$. The "
                   "$p$-value is two-sided. MDE $=2.8016\\,\\mathrm{SE}$ is the smallest true difference a two-sided "
                   "5\\% test detects with 80\\% power. Source: \\texttt{output/explore/ladder/ladder\\_dm\\_table.csv}. "
                   "Forecast days 2010--2019 (ETFs; credit and risk-asset samples start in 2012), 1992--2019 (funds).")
    ladder_table(df, "tab_ladder_vol.tex", "Regime-specific volatility against a pooled normal (B versus A)",
                 "tab:ladder-vol", [("regime_vol", "B versus A")], note_common)
    ladder_table(df, "tab_ladder_margin.tex", "GARCH margins against static regime covariance",
                 "tab:ladder-margin",
                 [("margin_pooledcorr", "CCC versus B (non-nested)"), ("margin_effect", "RSC versus D (non-nested; pre-declared family)")],
                 "As Table~\\ref{tab:ladder-vol}. Holm $p$: the pre-declared family is RSC versus D in the four ETF samples, "
                 "Holm-adjusted over the four; the fund sample is not in the family. Bold: the one adjusted $p$-value below 0.05.", holm_step="margin_effect")
    ladder_table(df, "tab_ladder_corr.tex", "Correlation steps",
                 "tab:ladder-corr",
                 [("static_corr", "D versus B (nested in the correlation matrix; size unreliable under GARCH margins)"),
                  ("corr_with_margins", "RSC versus CCC (nested in the correlation matrix)"),
                  ("regime_vs_smooth", "DCC versus RSC (non-nested)")], "As Table~\\ref{tab:ladder-vol}.")

    # real-data primary pair on development data --------------------------------------------------------------
    rt = pd.read_csv(ROOT / "output" / "explore" / "routes" / "routes_dm_table.csv")
    rt = rt[(rt.provider == "HMM_SPY2") & (rt["first"] == "RSC_P_N") & (rt["second"] == "CCC_S_N")]
    label = {"full_2010_2019": "2010--2019", "dev_2010_2015": "2010--2015", "pseudo_2016_2019": "2016--2019"}
    per = list(rt.period.unique())
    rows = []
    for a in (0.05, 0.025):
        for p in per:
            r = rt[(rt.alpha == a) & (rt.period == p)].iloc[0]
            se = r.mde80 / 2.8
            rows.append(f"{pct(a)} & {label.get(p, p)} & {int(r.n):,} & {f4(r.mean_diff)} & {f4(se)} & {ci(r.mean_diff, se)} & "
                        f"{f2(r.t)} & {pfmt(r.p)} & {f4(r.mde80)} \\\\")
    write("tab_real_pair.tex",
          "\\begin{table}[t]\n\\centering\\setstretch{1}\\footnotesize\\setlength{\\tabcolsep}{5pt}\n\\caption{\\uc{Single-pair correlation switching against constant correlation, "
          "development data (RSC\\_P versus CCC)}}\\label{tab:real-pair}\n\\begin{tabular}{llrrrcrrr}\n\\toprule\n"
          "$\\alpha$ & Forecast days & $n$ & $\\bar d$ & SE & 95\\% interval & $t$ & $p$ (2-sided) & MDE \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n"
          "\\tabnote{RSC\\_P minus CCC, Gaussian chain, pooled mean; negative favours switching the SPY--IEF correlation. "
          "SE is MDE$/2.8$ (the table stores MDE rounded to $2.8\\,\\mathrm{SE}$); the interval is $\\bar d\\pm1.96\\,\\mathrm{SE}$. "
          "These are development data: the specification was chosen after seeing them, so they are not validation. "
          "Source: \\texttt{output/explore/routes/routes\\_dm\\_table.csv}, provider HMM\\_SPY2.}\n\\end{table}\n")

    # power ---------------------------------------------------------------------------------------------------
    p15 = pd.read_csv(LAD / "power_1508_summary.csv")
    p25 = pd.read_csv(LAD / "power_2520_twosided.csv")
    names = {"S0_vol_only": "S0 (no correlation change)", "S1_moderate_breakdown": "S1 (moderate)",
             "S2_strong_breakdown": "S2 (strong)", "S3_flight_to_quality": "S3 (flight to quality)"}

    def prow(src, sc, step, lab):
        r = src[(src.scenario == sc) & (src.alpha == 0.05) & (src.step == step)].iloc[0]
        return (f"{lab} & {pct(r.one_sided)} [{pct(r.one_sided_lo)}, {pct(r.one_sided_hi)}] & {pct(r.two_sided)} & "
                f"{pct(r.upper_196)} & {f4(r.mean_diff)} & {f4(r.mean_se_d)} \\\\")

    rows = ["\\multicolumn{6}{l}{\\textbf{Primary test: RSC\\_P versus CCC, 1,508 test days, 500 replications}}\\\\"]
    rows += [prow(p15, s, "pair_with_margins", n) for s, n in names.items()]
    rows += ["\\midrule", "\\multicolumn{6}{l}{\\textbf{Same test, 2,520 test days (earlier study, 200 replications)}}\\\\"]
    rows += [prow(p25, s, "pair_with_margins", n) for s, n in names.items()]
    rows += ["\\midrule", "\\multicolumn{6}{l}{\\textbf{RSC versus CCC (all pairs switch), 1,508 test days}}\\\\"]
    rows += [prow(p15, s, "corr_with_margins", n) for s, n in names.items()]
    rows += ["\\midrule", "\\multicolumn{6}{l}{\\textbf{Static D versus B, 1,508 test days (size under GARCH margins)}}\\\\"]
    rows += [prow(p15, "S0_vol_only", "static_corr", names["S0_vol_only"])]
    write("tab_power1508.tex",
          "\\begin{table}[t]\n\\centering\\setstretch{1}\\footnotesize\\setlength{\\tabcolsep}{5pt}\n\\caption{\\uc{Simulated size and power of the difference tests (500 replications per scenario at 1,508 days; 200 at 2,520 days)}}\\label{tab:power1508}\n"
          "\\begin{tabular}{lcccrr}\n\\toprule\nScenario & One-sided rejection [95\\% CI] & Two-sided & Upper tail & Mean $\\bar d$ & Mean SE \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n"
          "\\tabnote{Tail level $\\alpha=5\\%$, Gaussian chain, simulated data from the stylised GARCH regime-switching process "
          "(Section~\\ref{sec:power-design}); S0 is the null and its row is the test size. One-sided: reject when $t<-1.6449$ "
          "(the pre-declared rule). Two-sided: $|t|>1.96$. Upper tail: $t>+1.96$, the rate at which the richer model is declared "
          "significantly worse. The interval is a 95\\% binomial interval on the replications. Mean $\\bar d$ and mean SE are averages "
          "over replications. Sources: \\texttt{power\\_1508\\_summary.csv}, \\texttt{power\\_2520\\_twosided.csv}.}\n\\end{table}\n")

    # calibration (development data) ---------------------------------------------------------------------------
    lt = pd.read_csv(LAD / "ladder_loss_table.csv")
    lt = lt[(lt.alpha == 0.05) & (lt.period == "full") & (lt.mean_set == "pooled") & (lt.chain == "N")]
    rungs = [r for r in ["A", "B", "D", "CCC", "RSC", "RSC_P", "DCC"] if r in set(lt.rung)]
    rows = []
    for u, nm in SAMPLES.items():
        hs = []
        for r in rungs:
            x = lt[(lt.universe == u) & (lt.rung == r)]
            hs.append(pct(x.hit.iloc[0]) if len(x) else "--")
        rows.append(f"{nm} & " + " & ".join(hs) + " \\\\")
    write("tab_hits.tex",
          "\\begin{table}[t]\n\\centering\\setstretch{1}\\footnotesize\\setlength{\\tabcolsep}{5pt}\n\\caption{\\uc{Share of days on which the return fell below the forecast VaR (nominal 5\\%), development data}}\\label{tab:hits}\n"
          f"\\begin{{tabular}}{{l{'r' * len(rungs)}}}\n\\toprule\nSample & " + " & ".join(r.replace("_", "\\_") for r in rungs) + " \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n"
          "\\tabnote{Gaussian chain, pooled mean, forecast days as in Table~\\ref{tab:ladder-vol}. A hit is a day with $y_t\\le\\mathrm{VaR}_t$. "
          "Source: \\texttt{output/explore/ladder/ladder\\_loss\\_table.csv}.}\n\\end{table}\n")

    # SESOI derivation -----------------------------------------------------------------------------------------
    s = json.loads((ROOT / "output" / "confirm" / "sesoi.json").read_text())["penalty_by_scale_factor"]
    cs = ["c=0.95", "c=0.97", "c=1.03", "c=1.05"]
    rows = []
    for k, lab in (("normal_alpha0.05", "Normal, $\\alpha=5\\%$"), ("t6_alpha0.05", "Student-$t$(6), $\\alpha=5\\%$"),
                   ("normal_alpha0.025", "Normal, $\\alpha=2.5\\%$")):
        rows.append(f"{lab} & " + " & ".join(f4(s[k][c]) for c in cs) + " \\\\")
    write("tab_sesoi.tex",
          "\\begin{table}[t]\n\\centering\\setstretch{1}\\footnotesize\\setlength{\\tabcolsep}{5pt}\n\\caption{\\uc{Expected FZ0 penalty of scaling both VaR and ES by a constant factor}}\\label{tab:sesoi}\n"
          "\\begin{tabular}{lrrrr}\n\\toprule\nTrue distribution & $c=0.95$ & $c=0.97$ & $c=1.03$ & $c=1.05$ \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n"
          "\\tabnote{Analytic expected loss at scale factor $c$ minus the expected loss at $c=1$, for a unit-variance true distribution; "
          "no market data are used. Source: \\texttt{output/confirm/sesoi.json}.}\n\\end{table}\n")

    # eras ------------------------------------------------------------------------------------------------------
    lh = json.loads((ROOT / "output" / "explore" / "longhistory_summary.json").read_text())["share_days_pos"]
    rows = [f"{k.replace('-', '--')} & {pct(v)} \\\\" for k, v in lh.items()]
    write("tab_eras.tex",
          "\\begin{table}[t]\n\\centering\\setstretch{1}\\footnotesize\\setlength{\\tabcolsep}{5pt}\n\\caption{\\uc{Share of days with a positive 252-day stock--bond correlation, by era}}\\label{tab:eras}\n"
          "\\begin{tabular}{lr}\n\\toprule\nEra & Share of days \\\\\n\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n"
          "\\tabnote{Mutual-fund proxies for stocks and long Treasuries (VFINX, VUSTX), not ETFs. Source: "
          "\\texttt{output/explore/longhistory\\_summary.json}.}\n\\end{table}\n")
    holdout_tables()
    print("wrote", sorted(p.name for p in OUT.glob("*.tex")))


def holdout_tables():
    """Tables of Chapter 7 from the single scored hold-out run (output/confirm/holdout/)."""
    H = ROOT / "output" / "confirm" / "holdout"
    if not (H / "primary.json").exists():
        return
    pj = json.loads((H / "primary.json").read_text())
    p15 = pd.read_csv(LAD / "power_1508_summary.csv")
    pw = {sc: p15[(p15.scenario == sc) & (p15.alpha == 0.05) & (p15.step == "pair_with_margins")].iloc[0].one_sided
          for sc in ("S1_moderate_breakdown", "S2_strong_breakdown")}
    d, se = pj["mean_diff"], pj["se"]
    rows = [("Forecast days $n$", f"{pj['n']:,}"), ("Mean difference $\\bar d$ (RSC\\_P minus CCC)", f4(d)),
            ("HAC standard error (7 lags)", f4(se)), ("$t$ statistic", f2(pj["t"])),
            ("One-sided $p$-value (pre-declared test)", f"{pj['p_one_sided']:.3f}"),
            ("Two-sided $p$-value", f"{pj['p_two_sided']:.3f}"),
            ("95\\% interval, two-sided", f"[{f4(pj['ci_lo'])}, {f4(pj['ci_hi'])}]"),
            ("One-sided 95\\% lower bound $\\bar d-1.6449\\,\\mathrm{SE}$", f4(pj["lower_bound_one_sided"])),
            ("Smallest effect of interest (SESOI)", f4(-pj["sesoi"])),
            ("MDE, one-sided 5\\% test, 80\\% power", f4(pj["mde_one_sided"])),
            ("MDE, two-sided 5\\% test, 80\\% power", f4(pj["mde_two_sided"])),
            ("Simulated power, moderate shift S1 / strong shift S2", f"{pct(pw['S1_moderate_breakdown'])} / {pct(pw['S2_strong_breakdown'])}"),
            ("Outcome", pj["outcome"])]
    body = "\n".join(f"{a} & {b} \\\\" for a, b in rows)
    write("tab_holdout_primary.tex",
          "\\begin{table}[t]\n\\centering\\setstretch{1}\\footnotesize\\setlength{\\tabcolsep}{5pt}\n\\caption{\\uc{The pre-specified hold-out test: switching SPY--IEF correlation against constant correlation}}\\label{tab:holdout-primary}\n"
          "\\begin{tabular}{lr}\n\\toprule\nQuantity & Value \\\\\n\\midrule\n" + body + "\n\\bottomrule\n\\end{tabular}\n"
          "\\tabnote{Forecast days 2 January 2020 to 31 December 2025, tail level $\\alpha=5\\%$, Gaussian chain, pooled mean. Negative $\\bar d$ favours "
          "switching the SPY--IEF correlation. The interval is $\\bar d\\pm1.96\\,\\mathrm{SE}$. Power is the simulated one-sided rejection rate at 1,508 days "
          "(Table~\\ref{tab:power1508}), not a property of this estimate. Source: \\texttt{output/confirm/holdout/primary.json}.}\n\\end{table}\n")

    # secondary comparisons ------------------------------------------------------------------------------------
    lad = pd.read_csv(H / "secondary_ladder.csv")
    names = {"B vs A": "B versus A", "D vs B": "D versus B", "CCC vs B": "CCC versus B", "RSC vs D": "RSC versus D",
             "RSC vs CCC": "RSC versus CCC", "DCC vs RSC": "DCC versus RSC"}

    def drow(lab, r):
        return (f"{lab} & {int(r.n):,} & {f4(r.mean_diff)} & {f4(r.se)} & [{f4(r.ci_lo)}, {f4(r.ci_hi)}] & {f2(r.t)} & "
                f"{pfmt(r.p_two_sided)} & {f4(r.mde_two_sided)} \\\\")
    rows = ["\\multicolumn{8}{l}{\\textbf{Ladder steps (all pairs switch where stated)}}\\\\"]
    rows += [drow(names[r.step], r) for r in lad.itertuples()]
    ac = pd.read_csv(H / "secondary_alpha_and_t_chain.csv")
    rows += ["\\midrule", "\\multicolumn{8}{l}{\\textbf{Primary pair at other settings}}\\\\"]
    rows += [drow(r.analysis.replace("alpha", "$\\alpha$").replace("%", "\\%").replace("Student-t", "Student-$t$"), r) for r in ac.itertuples()]
    fy = pd.read_csv(H / "secondary_focus_year.csv").iloc[0]
    rows += ["\\midrule", "\\multicolumn{8}{l}{\\textbf{Calendar year 2022 (interval only, not a test)}}\\\\",
             f"RSC\\_P versus CCC, 2022 & {int(fy.n):,} & {f4(fy.mean_diff)} & {f4(fy.se)} & [{f4(fy.ci_lo)}, {f4(fy.ci_hi)}] & -- & -- & -- \\\\"]
    write("tab_holdout_secondary.tex",
          "\\begin{table}[t]\n\\centering\\setstretch{1}\\scriptsize\\setlength{\\tabcolsep}{5pt}\n\\caption{\\uc{Secondary comparisons on the hold-out (unadjusted; not confirmatory)}}\\label{tab:holdout-secondary}\n"
          "\\begin{tabular}{lrrrcrrr}\n\\toprule\nComparison & $n$ & $\\bar d$ & SE & 95\\% interval & $t$ & $p$ (2-sided) & MDE \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n"
          "\\tabnote{Mean FZ0 difference of the richer model minus the baseline; negative favours the richer model. Panel 1 is the ladder of "
          "Chapter~\\ref{ch:method} on the hold-out, with tail level 5\\%, Gaussian chain, pooled mean. The interval is $\\bar d\\pm1.96\\,\\mathrm{SE}$ and the MDE is "
          "$2.8016\\,\\mathrm{SE}$ (two-sided 5\\%, 80\\% power). None of these $p$-values is adjusted and none is cited as confirmation. "
          "Source: \\texttt{output/confirm/holdout/secondary\\_ladder.csv}, \\texttt{secondary\\_alpha\\_and\\_t\\_chain.csv}, \\texttt{secondary\\_focus\\_year.csv}.}\n\\end{table}\n")

    # calibration ----------------------------------------------------------------------------------------------
    cal = pd.read_csv(H / "calibration.csv")
    arm = {"RSC_P_N": "RSC\\_P", "CCC_S_N": "CCC", "RSC_P_t": "RSC\\_P", "CCC_S_t": "CCC"}
    rows = ["\\multicolumn{10}{l}{\\textbf{Gaussian chain (the primary forecasts)}}\\\\"]
    for a in (0.05, 0.025):
        for r in cal[cal.alpha == a].itertuples():
            rows.append(f"{pct(a)} & {arm[r.arm]} & {int(r.hits)} & {pct(r.hit_rate)} & {pfmt(r.kupiec_p)} & {pfmt(r.independence_p)} & "
                        f"{pfmt(r.cc_p)} & {f3(r.z2)} & {pfmt(r.z2_p_underestimated)} & {f2(r.mean_es_exceedance_ratio)} \\\\")
    ph_all = json.loads((ROOT / "output" / "confirm" / "posthoc.json").read_text())
    tc = ph_all["t_chain_calib"]
    by = ph_all["breach_by_year"]
    yrs = sorted(by["days"])
    def cell(y, x):
        t = pct(x)
        return "\\textbf{" + t + "}" if y == "2022" else t
    brows = [f"Forecast days & " + " & ".join(("\\textbf{" + str(by['days'][y]) + "}" if y == "2022" else str(by['days'][y])) for y in yrs) + " \\\\", "\\midrule"]
    for k, lab in (("CCC_S_N", "CCC (constant correlation)"), ("RSC_P_N", "RSC\\_P (switching SPY--IEF correlation)"), ("EWMA", "RiskMetrics EWMA (POST HOC baseline)")):
        brows.append(f"{lab} & " + " & ".join(cell(y, by[k][y]) for y in yrs) + " \\\\")
    write("tab_holdout_breach_year.tex",
          "\\begin{table}[t]\n\\centering\\setstretch{1}\\footnotesize\\setlength{\\tabcolsep}{4pt}\n\\caption{\\uc{Share of hold-out days on which the 5\\% VaR was breached, by calendar year}}\\label{tab:breach-year}\n"
          "\\begin{tabular}{l" + "r" * len(yrs) + "}\n\\toprule\n & " + " & ".join(("\\textbf{" + y + "}" if y == "2022" else y) for y in yrs) + " \\\\\n\\midrule\n"
          + "\n".join(brows) + "\n\\bottomrule\n\\end{tabular}\n"
          "\\tabnote{Nominal rate 5\\%; Gaussian chain for CCC and RSC\\_P. 2022, the year in which the stock--bond correlation turned positive, is in bold. POST HOC and descriptive: chosen after the result was known; no test. Source: \\texttt{output/confirm/posthoc.json} (\\texttt{scripts/thesis\\_posthoc.py}).}\n\\end{table}\n")
    rows += ["\\midrule", "\\multicolumn{10}{l}{\\textbf{Student-$t$ chain (POST HOC, descriptive)}}\\\\"]
    for a in (0.05, 0.025):
        for k in ("RSC_P_t", "CCC_S_t"):
            r = tc[f"{k}_a{int(a * 1000)}"]
            rows.append(f"{pct(a)} & {arm[k]} & {r['hits']} & {pct(r['hit_rate'])} & {pfmt(r['kupiec_p'])} & {pfmt(r['independence_p'])} & "
                        f"{pfmt(r['cc_p'])} & -- & -- & {f2(r['es_ratio'])} \\\\")
    write("tab_holdout_calib.tex",
          "\\begin{table}[t]\n\\centering\\setstretch{1}\\scriptsize\\setlength{\\tabcolsep}{8pt}\n\\caption{\\uc{Coverage and expected-shortfall calibration of the two primary models on the hold-out}}\\label{tab:holdout-calib}\n"
          "\\begin{tabular}{llrrrrrrrr}\n\\toprule\n$\\alpha$ & Model & Hits & Hit rate & Kupiec $p$ & Indep. $p$ & Cond. cov. $p$ & $Z_2$ & $Z_2$ $p$ & ES ratio \\\\\n\\midrule\n"
          + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n"
          "\\tabnote{1,508 forecast days; 75.4 hits expected at 5\\% and 37.7 at 2.5\\%. A hit is a day with $y_t\\le\\mathrm{VaR}_t$. Kupiec: unconditional coverage; Indep.: Christoffersen independence; "
          "Cond. cov.: their sum. $Z_2$ is positive when risk is underestimated (my sign, opposite to Acerbi and Szekely); its $p$-value is the simulated "
          "share of $Z_2$ values at or above the observed one, and it is not simulated for the Student-$t$ chain. ES ratio: mean of $y_t/\\mathrm{ES}_t$ over hit days, above one when exceedances are larger than the "
          "forecast shortfall. Descriptive, not part of the decision. Sources: \\texttt{output/confirm/holdout/calibration.csv}; Student-$t$ rows \\texttt{output/confirm/posthoc.json} (\\texttt{scripts/thesis\\_posthoc.py}).}\n\\end{table}\n")


if __name__ == "__main__":
    main()
