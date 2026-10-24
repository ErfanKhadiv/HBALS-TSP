"""
analyze.py - statistics, tables and figures for the revised HBALS study.
Reads results/csv/runs.csv and writes results/tables/*.csv, results/figures/*.png
"""
import os, sys, itertools, json
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(__file__))
from run_experiments import CORE, ABL, LARGE, BKS, ROOT, RES

TAB = os.path.join(RES, "tables")
FIG = os.path.join(RES, "figures")
os.makedirs(TAB, exist_ok=True)
os.makedirs(FIG, exist_ok=True)

d = pd.read_csv(os.path.join(RES, "csv", "runs.csv"))
# plain BA is reported with its first 10 runs on every instance (two small instances were run 20 times)
d = d[(d.algorithm != "BA") | (d.run < 10)].copy()
d["gap"] = (d.best - d.bks) / d.bks * 100.0


def holm(p):
    p = np.asarray(p, float)
    o = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    run = 0.0
    for r, i in enumerate(o):
        run = max(run, (m - r) * p[i])
        adj[i] = min(1.0, run)
    return adj


def a12(x, y):
    """Vargha-Delaney A12 = P(x < y) + 0.5 P(x == y) for minimisation
    (probability that a run of x is better than a run of y)."""
    x = np.asarray(x); y = np.asarray(y)
    gt = (x[:, None] < y[None, :]).sum()
    eq = (x[:, None] == y[None, :]).sum()
    return (gt + 0.5 * eq) / (len(x) * len(y))


def summary(sub):
    g = sub.groupby(["instance", "algorithm"])
    s = g.agg(n=("n", "first"), runs=("run", "count"), best=("best", "min"),
              mean=("best", "mean"), std=("best", "std"), median=("best", "median"),
              worst=("best", "max"), gap_mean=("gap", "mean"), time=("time_s", "mean"),
              evals=("evals", "mean"), iters=("iters", "mean"), budget=("budget", "first"),
              bks=("bks", "first")).reset_index()
    s["gap_best"] = (s.best - s.bks) / s.bks * 100
    s["hits_bks"] = g.apply(lambda x: int((x.best <= x.bks).sum()), include_groups=False).values
    return s


S = summary(d)
S.to_csv(os.path.join(TAB, "summary_all.csv"), index=False)

# ------------------------------------------------------------------ main comparison
main_algos = ["HBALS", "ILS-2opt", "GA-2opt", "ACO-2opt", "MS-2opt", "BA"]
core_done = [i for i in CORE if all(((S.instance == i) & (S.algorithm == a)).any() for a in main_algos)]
M = S[S.instance.isin(core_done) & S.algorithm.isin(main_algos)]
piv = M.pivot(index="instance", columns="algorithm", values="gap_mean").loc[core_done, main_algos]
piv.to_csv(os.path.join(TAB, "main_gap_mean.csv"))
ranks = piv.rank(axis=1, method="average")
avg_rank = ranks.mean()
k, N = len(main_algos), len(core_done)
fried = stats.friedmanchisquare(*[piv[a].values for a in main_algos]) if N >= 3 else None
q = stats.studentized_range.ppf(0.95, k, np.inf) / np.sqrt(2)
CD = q * np.sqrt(k * (k + 1) / (6.0 * N))
# Wilcoxon signed-rank across instances, HBALS vs each (Holm)
wl, wp = [], []
for a in main_algos[1:]:
    diff = piv["HBALS"] - piv[a]
    try:
        w = stats.wilcoxon(piv["HBALS"], piv[a], alternative="two-sided")
        wp.append(w.pvalue)
    except Exception:
        wp.append(np.nan)
    wl.append(a)
wp_h = holm(np.nan_to_num(wp, nan=1.0))
wdf = pd.DataFrame(dict(comparator=wl, p_raw=wp, p_holm=wp_h))
wdf["hbals_better_on"] = [int((piv["HBALS"] < piv[a]).sum()) for a in wl]
wdf["tied_on"] = [int((piv["HBALS"] == piv[a]).sum()) for a in wl]
wdf["comparator_better_on"] = [int((piv["HBALS"] > piv[a]).sum()) for a in wl]
wdf.to_csv(os.path.join(TAB, "main_wilcoxon_instances.csv"), index=False)
pd.DataFrame(dict(algorithm=main_algos, avg_rank=avg_rank.values)).assign(
    CD=CD, friedman_chi2=(fried.statistic if fried else np.nan),
    friedman_p=(fried.pvalue if fried else np.nan), n_instances=N).to_csv(
    os.path.join(TAB, "main_friedman.csv"), index=False)

# per-instance Mann-Whitney (run level), Holm across the 5 comparators, A12
rows = []
for inst in core_done:
    hb = d[(d.instance == inst) & (d.algorithm == "HBALS")].best.values
    ps, tmp = [], []
    for a in main_algos[1:]:
        x = d[(d.instance == inst) & (d.algorithm == a)].best.values
        if len(hb) == len(x) and np.all(hb == x):
            p = 1.0
        else:
            p = stats.mannwhitneyu(hb, x, alternative="two-sided").pvalue
        ps.append(p)
        tmp.append((a, a12(hb, x)))
    ph = holm(ps)
    for (a, A), p, pa in zip(tmp, ps, ph):
        rows.append(dict(instance=inst, comparator=a, p_raw=p, p_holm=pa, A12_hbals_better=A))
mw = pd.DataFrame(rows)
mw.to_csv(os.path.join(TAB, "main_mannwhitney_runs.csv"), index=False)

# ------------------------------------------------------------------ protocol effect
prot = S[S.algorithm.isin(["HBALS", "HBALS-orig-protocol"]) & S.instance.isin(CORE)]
pp = prot.pivot(index="instance", columns="algorithm", values="gap_mean")
pit = prot.pivot(index="instance", columns="algorithm", values="iters")
pp.to_csv(os.path.join(TAB, "protocol_gap.csv"))
pit.to_csv(os.path.join(TAB, "protocol_iters.csv"))

# ------------------------------------------------------------------ ablation
abl_algos = ["HBALS", "HBALS+adaptive", "HBALS-ngh3", "HBALS-noNN", "HBALS-noRev",
             "HBALS-noSelLS", "HBALS-noEliteLS", "HBALS-noScouts"]
abl_done = [i for i in ABL if all(((S.instance == i) & (S.algorithm == a)).any() for a in abl_algos)]
if abl_done:
    A = S[S.instance.isin(abl_done) & S.algorithm.isin(abl_algos)]
    ap = A.pivot(index="instance", columns="algorithm", values="gap_mean").loc[abl_done, abl_algos]
    ap.to_csv(os.path.join(TAB, "ablation_gap_mean.csv"))
    rows = []
    for a in abl_algos[1:]:
        ps, As, nb, nw = [], [], 0, 0
        for inst in abl_done:
            hb = d[(d.instance == inst) & (d.algorithm == "HBALS")].best.values
            x = d[(d.instance == inst) & (d.algorithm == a)].best.values
            p = 1.0 if (len(hb) == len(x) and np.all(hb == x)) else stats.mannwhitneyu(hb, x, alternative="two-sided").pvalue
            ps.append(p)
            As.append(a12(hb, x))
        ph = holm(ps)
        sig_worse = sum((pp_ < 0.05 and aa > 0.5) for pp_, aa in zip(ph, As))   # HBALS better
        sig_better = sum((pp_ < 0.05 and aa < 0.5) for pp_, aa in zip(ph, As))  # variant better
        rows.append(dict(variant=a, mean_gap=ap[a].mean(), delta_vs_HBALS=ap[a].mean() - ap["HBALS"].mean(),
                         instances_HBALS_sig_better=sig_worse, instances_variant_sig_better=sig_better,
                         wilcoxon_p_instances=(stats.wilcoxon(ap["HBALS"], ap[a]).pvalue
                                               if not np.allclose(ap["HBALS"], ap[a]) else 1.0)))
    ar = pd.DataFrame(rows)
    ar.loc[len(ar)] = dict(variant="HBALS", mean_gap=ap["HBALS"].mean(), delta_vs_HBALS=0.0)
    ar.to_csv(os.path.join(TAB, "ablation_summary.csv"), index=False)

# ------------------------------------------------------------------ large instances
L = S[S.instance.isin(LARGE)]
L.to_csv(os.path.join(TAB, "large_summary.csv"), index=False)

# ------------------------------------------------------------------ figures
colors = {"HBALS": "#1f4e79", "ILS-2opt": "#c55a11", "GA-2opt": "#548235", "ACO-2opt": "#7f6000",
          "MS-2opt": "#7030a0", "BA": "#7f7f7f", "HBALS-orig-protocol": "#2e75b6"}

# convergence (anytime) curves
show = [i for i in ["eil101", "kroA100", "ch150", "d198"] if i in core_done]
if show:
    fig, axes = plt.subplots(2, 2, figsize=(9, 6.2), squeeze=False)
    for ax, inst in zip(axes.ravel(), show):
        for a in ["HBALS", "ILS-2opt", "GA-2opt", "ACO-2opt", "MS-2opt"]:
            f = os.path.join(RES, "conv", f"{inst}__{a}.npy")
            if not os.path.exists(f):
                continue
            c = np.load(f)
            g = (c - BKS[inst]) / BKS[inst] * 100
            x = np.arange(1, 101)
            ax.plot(x, g.mean(0), label=a, color=colors[a], lw=1.8)
            ax.fill_between(x, g.min(0), g.max(0), color=colors[a], alpha=0.10)
        ax.set_yscale("log"); ax.set_title(inst); ax.set_xlabel("budget used (%)")
        ax.grid(alpha=0.3)
    for ax in axes[:, 0]:
        ax.set_ylabel("mean gap to BKS (%)")
    axes[0][0].legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG, "anytime_curves.png"), dpi=200)
    plt.close()

# box plots of final gaps
box = [i for i in ["kroA100", "ch150", "d198"] if i in core_done]
if box:
    fig, axes = plt.subplots(1, len(box), figsize=(10.5, 3.8), squeeze=False)
    for ax, inst in zip(axes[0], box):
        data = [d[(d.instance == inst) & (d.algorithm == a)].gap.values for a in main_algos[:5]]
        bp = ax.boxplot(data, tick_labels=[a.replace("-2opt", "") for a in main_algos[:5]], patch_artist=True)
        for patch, a in zip(bp["boxes"], main_algos[:5]):
            patch.set_facecolor(colors[a]); patch.set_alpha(0.6)
        ax.set_title(inst); ax.grid(alpha=0.3, axis="y")
        ax.tick_params(axis="x", labelsize=9)
    axes[0][0].set_ylabel("final gap to BKS (%)")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG, "boxplots.png"), dpi=200)
    plt.close()

# ablation bars
if abl_done:
    fig, ax = plt.subplots(figsize=(7, 3.4))
    vals = ap.mean().loc[abl_algos]
    names = [a.replace("HBALS-", "−").replace("HBALS+adaptive", "+adaptive\n(corrected)") if a != "HBALS" else "HBALS\n(full)" for a in abl_algos]
    cols = ["#1f4e79"] + ["#9dc3e6"] * (len(abl_algos) - 1)
    ax.bar(range(len(vals)), vals.values, color=cols)
    ax.set_xticks(range(len(vals))); ax.set_xticklabels(names, fontsize=7)
    ax.set_ylabel("mean gap to BKS (%%)\n(avg over %d instances)" % len(abl_done))
    ax.grid(alpha=0.3, axis="y")
    for i, v in enumerate(vals.values):
        ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=7)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG, "ablation.png"), dpi=200)
    plt.close()

# protocol effect figure
if len(pp) > 0 and "HBALS-orig-protocol" in pp.columns:
    fig, ax = plt.subplots(figsize=(7, 3.2))
    x = np.arange(len(pp))
    ax.bar(x - 0.2, pp["HBALS-orig-protocol"], 0.4, label="early stop after 20 stagnant iterations", color="#9dc3e6")
    ax.bar(x + 0.2, pp["HBALS"], 0.4, label="full budget (no early stop)", color="#1f4e79")
    ax.set_xticks(x); ax.set_xticklabels(pp.index, fontsize=7, rotation=30)
    ax.set_ylabel("mean gap to BKS (%)"); ax.legend(fontsize=7); ax.grid(alpha=0.3, axis="y")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG, "protocol_effect.png"), dpi=200)
    plt.close()

print("instances with all main algos:", core_done)
print(piv.round(3).to_string())
print("avg ranks:\n", avg_rank.round(2).to_string(), "\nCD =", round(CD, 3), "friedman", fried)
print(wdf.to_string())
if abl_done:
    print(ap.round(3).to_string())
    print(ar.round(4).to_string())
