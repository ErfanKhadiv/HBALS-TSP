"""Collects the numbers used in the manuscript into results/paper_data.json."""
import json, os, sys, platform
import numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, os.path.dirname(__file__))
from run_experiments import CORE, ABL, LARGE, BKS, RES
from analyze import holm, a12
d = pd.read_csv(os.path.join(RES, "csv", "runs.csv"))
d = d[(d.algorithm != "BA") | (d.run < 10)].copy()
d["gap"] = (d.best - d.bks) / d.bks * 100
out = {}
algos = ["HBALS", "ILS-2opt", "GA-2opt", "ACO-2opt", "MS-2opt", "BA"]
rows = []
for inst in CORE:
    r = {"instance": inst, "n": int(d[d.instance == inst].n.iloc[0]), "bks": BKS[inst],
         "budget_M": d[d.instance == inst].budget.iloc[0] / 1e6}
    for a in algos:
        x = d[(d.instance == inst) & (d.algorithm == a)]
        r[a] = [x.gap.mean(), x.gap.std(), int((x.best <= x.bks).sum()), len(x), float(x.best.min())]
    h = d[(d.instance == inst) & (d.algorithm == "HBALS")].best.values
    il = d[(d.instance == inst) & (d.algorithm == "ILS-2opt")].best.values
    p = 1.0 if np.all(h == il) else stats.mannwhitneyu(h, il, alternative="two-sided").pvalue
    r["p_ils"] = p
    r["A12_ils"] = a12(h, il)
    rows.append(r)
ps = holm([r["p_ils"] for r in rows])
for r, ph in zip(rows, ps):
    r["p_ils_holm12"] = ph
out["main"] = rows
out["friedman"] = pd.read_csv(os.path.join(RES, "tables", "main_friedman.csv")).to_dict("records")
out["wilcoxon"] = pd.read_csv(os.path.join(RES, "tables", "main_wilcoxon_instances.csv")).to_dict("records")
# protocol
prot = []
for inst in CORE:
    a = d[(d.instance == inst) & (d.algorithm == "HBALS-orig-protocol")]
    b = d[(d.instance == inst) & (d.algorithm == "HBALS")]
    prot.append(dict(instance=inst, gap_orig=a.gap.mean(), it_orig=a.iters.mean(), gap_full=b.gap.mean(), it_full=b.iters.mean()))
out["protocol"] = prot
# ablation
variants = ["HBALS", "HBALS+adaptive", "HBALS-ngh3", "HBALS-noNN", "HBALS-noRev", "HBALS-noSelLS", "HBALS-noEliteLS", "HBALS-noScouts"]
ab = []
for inst in ABL:
    r = {"instance": inst}
    hb = d[(d.instance == inst) & (d.algorithm == "HBALS")].best.values
    for v in variants:
        x = d[(d.instance == inst) & (d.algorithm == v)]
        r[v] = [x.gap.mean(), x.gap.std()]
    ps = []
    for v in variants[1:]:
        x = d[(d.instance == inst) & (d.algorithm == v)].best.values
        ps.append(1.0 if np.all(hb == x) else stats.mannwhitneyu(hb, x, alternative="two-sided").pvalue)
    ph = holm(ps)
    r["p_holm"] = dict(zip(variants[1:], ph))
    r["A12"] = {v: a12(hb, d[(d.instance == inst) & (d.algorithm == v)].best.values) for v in variants[1:]}
    ab.append(r)
out["ablation"] = ab
# large
lg = []
for inst in LARGE:
    r = {"instance": inst, "n": int(d[d.instance == inst].n.iloc[0]), "bks": BKS[inst],
         "budget_M": d[d.instance == inst].budget.iloc[0] / 1e6}
    for a in ["HBALS", "ILS-2opt", "GA-2opt", "ACO-2opt"]:
        x = d[(d.instance == inst) & (d.algorithm == a)]
        r[a] = [x.gap.mean(), x.gap.std(), float(x.best.min()), len(x)]
    h = d[(d.instance == inst) & (d.algorithm == "HBALS")].best.values
    il = d[(d.instance == inst) & (d.algorithm == "ILS-2opt")].best.values
    r["p_ils"] = stats.mannwhitneyu(h, il, alternative="two-sided").pvalue
    lg.append(r)
out["large"] = lg
out["env"] = dict(python=platform.python_version(), numpy=np.__version__)
import numba; out["env"]["numba"] = numba.__version__
out["timing"] = d[d.algorithm.isin(["HBALS", "ILS-2opt"])].groupby(["instance", "algorithm"]).time_s.mean().unstack().to_dict()
json.dump(out, open(os.path.join(RES, "paper_data.json"), "w"), indent=1, default=float)
print("ok")
