"""
run_experiments.py - equal-budget experiments for the revised HBALS study.

usage:  python src/run_experiments.py --group main|ablation|large [--runs 20]

Every (instance, algorithm) block is appended to results/csv/runs.csv and its
anytime curve (best-so-far at each 1% of the budget) is stored in
results/conv/<instance>__<algorithm>.npy.  Blocks already present are skipped,
so the script can be interrupted and resumed.
"""
import argparse, json, os, sys, time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from tsp_core import *

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RES = os.path.join(ROOT, "results")

BKS = {"eil51": 426, "berlin52": 7542, "st70": 675, "eil76": 538, "kroA100": 21282,
       "kroB100": 22141, "eil101": 629, "lin105": 14379, "ch130": 6110,
       "kroA150": 26524, "ch150": 6528, "rat195": 2323, "d198": 15780,
       "kroA200": 29368, "a280": 2579, "lin318": 42029,
       "kroC100": 20749, "pr107": 44303, "bier127": 118282, "kroB150": 26130}

CORE = ["eil51", "berlin52", "st70", "eil76", "kroA100", "kroB100", "eil101",
        "lin105", "ch130", "ch150", "rat195", "d198"]
ABL = ["st70", "kroA100", "ch130", "d198"]
LARGE = ["kroA200", "a280", "lin318"]
TUNE = ["kroC100", "pr107", "bier127", "kroB150"]   # never used for reporting

HB = lambda **kw: ("hbals", make_params(**kw))
ALGOS = {
    # final method: single-swap perturbation (the published code behaved this way)
    "HBALS": HB(adapt=2, ngh=1),
    "HBALS-orig-protocol": HB(adapt=0, thr=20, max_iter=300),   # as in the first manuscript
    # ablations
    "HBALS+adaptive": HB(adapt=1, cap=10),
    "HBALS-ngh3": HB(adapt=2, ngh=3),
    "HBALS-noNN": HB(adapt=2, ngh=1, nn_ratio=0.0),
    "HBALS-noRev": HB(adapt=2, ngh=1, p3=0.0),
    "HBALS-noSelLS": HB(adapt=2, ngh=1, p_sel=0.0),
    "HBALS-noEliteLS": HB(adapt=2, ngh=1, p_el=0.0),
    "HBALS-noScouts": HB(adapt=2, ngh=1, scouts=0),
    # baselines
    "BA": ("ba", None), "MS-2opt": ("ms", None), "ILS-2opt": ("ils", None),
    "GA-2opt": ("ga", None), "ACO-2opt": ("aco", None),
}
GROUPS = {
    "main": (CORE, ["HBALS", "HBALS-orig-protocol", "BA", "MS-2opt", "ILS-2opt", "GA-2opt", "ACO-2opt"]),
    "ablation": (ABL, ["HBALS+adaptive", "HBALS-ngh3", "HBALS-noNN", "HBALS-noRev",
                       "HBALS-noSelLS", "HBALS-noEliteLS", "HBALS-noScouts"]),
    "large": (LARGE, ["HBALS", "ILS-2opt", "GA-2opt", "ACO-2opt"]),
}


def budget_for(name, D):
    f = os.path.join(RES, "budgets.json")
    b = json.load(open(f)) if os.path.exists(f) else {}
    if name not in b:
        conv = np.zeros(100)
        P = make_params(adapt=0, thr=0, max_iter=300)       # published config, 300 iterations
        ev = [hbals(D, P, 0, 7000 + s, conv)[2] for s in range(3)]
        b[name] = int(round(np.mean(ev), -5))
        json.dump(b, open(f, "w"), indent=1)
    return b[name]


def run_one(kind, P, D, budget, seed, conv):
    if kind == "hbals":
        if P[P_THR] > 0:          # original protocol: iteration limit, no budget
            return hbals(D, P, 0, seed, conv)
        return hbals(D, P, budget, seed, conv)
    fn = {"ba": ba_plain, "ms": multistart_2opt, "ils": ils_2opt,
          "ga": ga_ls, "aco": aco_ls}[kind]
    return fn(D, budget, seed, conv)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group", required=True, choices=list(GROUPS))
    ap.add_argument("--runs", type=int, default=20)
    ap.add_argument("--instances", nargs="*")
    a = ap.parse_args()
    insts, algos = GROUPS[a.group]
    if a.instances:
        insts = a.instances
    os.makedirs(os.path.join(RES, "csv"), exist_ok=True)
    os.makedirs(os.path.join(RES, "conv"), exist_ok=True)
    out = os.path.join(RES, "csv", "runs.csv")
    done = set()
    if os.path.exists(out):
        d = pd.read_csv(out)
        done = set(zip(d.instance, d.algorithm))
    skipped = [(i, al) for i in insts for al in algos if (i, al) in done]
    if skipped:
        print(f"NOTE: {len(skipped)} (instance, method) blocks are already in results/csv/runs.csv and are SKIPPED. "
              "To recompute them, move or delete results/csv/runs.csv (run_all.py --fresh does this).", flush=True)
    for inst in insts:
        _, D = load_tsp(os.path.join(DATA, inst + ".tsp"))
        B = budget_for(inst, D)
        for al in algos:
            if (inst, al) in done:
                continue
            kind, P = ALGOS[al]
            rows, convs = [], []
            n_runs = min(a.runs, 10) if al == "BA" else a.runs
            t_block = time.time()
            for r in range(n_runs):
                seed = 1000 + r
                conv = np.zeros(100)
                t0 = time.time()
                c, t, ev, it = run_one(kind, P, D, B, seed, conv)
                dt = time.time() - t0
                check_tour(t, D, c)
                rows.append(dict(instance=inst, n=D.shape[0], algorithm=al, run=r, seed=seed,
                                 best=c, evals=int(ev), iters=int(it), time_s=dt,
                                 budget=B, bks=BKS[inst]))
                convs.append(conv)
            df = pd.DataFrame(rows)
            df.to_csv(out, mode="a", header=not os.path.exists(out), index=False)
            np.save(os.path.join(RES, "conv", f"{inst}__{al}.npy"), np.array(convs))
            print(f"{inst:9s} {al:20s} mean gap {(df.best.mean()-BKS[inst])/BKS[inst]*100:7.3f}%  "
                  f"best {df.best.min():.0f}  {time.time()-t_block:6.1f}s", flush=True)


if __name__ == "__main__":
    main()
