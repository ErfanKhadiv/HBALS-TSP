"""
compare_with_reference.py - compares YOUR results/csv/runs.csv with the reference results shipped in results_reference/.
For every (instance, method) block present in both it reports how many runs are identical (same seed -> same tour length
is expected when the library versions behave identically) and, if not identical, a Mann-Whitney test of your runs against
the reference runs. Output: results/comparison_with_reference.txt
"""
import os, sys
import numpy as np, pandas as pd
from scipy import stats
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = pd.read_csv(os.path.join(ROOT, "results", "csv", "runs.csv"))
b = pd.read_csv(os.path.join(ROOT, "results_reference", "csv", "runs.csv"))
lines, n_blocks, n_same_blocks, bad = [], 0, 0, []
for (inst, al), x in a.groupby(["instance", "algorithm"]):
    y = b[(b.instance == inst) & (b.algorithm == al)]
    if y.empty:
        continue
    y = y[y.run.isin(x.run)]
    j = x.merge(y, on="run", suffixes=("_you", "_ref"))
    same = int((j.best_you == j.best_ref).sum())
    gap_you = (x.best.mean() - x.bks.iloc[0]) / x.bks.iloc[0] * 100
    gap_ref = (y.best.mean() - y.bks.iloc[0]) / y.bks.iloc[0] * 100
    p = 1.0 if same == len(j) else stats.mannwhitneyu(x.best, y.best, alternative="two-sided").pvalue
    n_blocks += 1
    n_same_blocks += int(same == len(j))
    flag = "" if p >= 0.01 else "  <-- differs"
    if p < 0.01:
        bad.append((inst, al))
    lines.append(f"{inst:9s} {al:20s} identical runs {same:2d}/{len(j):2d}  mean gap you {gap_you:7.3f}%  ref {gap_ref:7.3f}%  p={p:.3f}{flag}")
lines.append("")
lines.append(f"{n_blocks} blocks compared; {n_same_blocks} identical run-by-run; {len(bad)} with a significant difference (p<0.01): {bad}")
txt = "\n".join(lines)
print(txt)
open(os.path.join(ROOT, "results", "comparison_with_reference.txt"), "w").write(txt + "\n")
