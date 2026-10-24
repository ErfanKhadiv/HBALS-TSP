"""
quick_test.py - run HBALS (and optionally the baselines) on ONE instance.

Examples
  python src/quick_test.py --instance eil51
  python src/quick_test.py --instance kroA100 --algos HBALS ILS-2opt GA-2opt --runs 5
  python src/quick_test.py --instance path/to/myinstance.tsp --bks 12345 --runs 3
  python src/quick_test.py --instance eil51 --budget 20000000      # smaller budget (faster)

Only TSPLIB files with EDGE_WEIGHT_TYPE: EUC_2D are supported.
Prints the best tour length, mean, standard deviation and gap to the best-known
length (if known) for every algorithm, and the best tour of the first algorithm.
"""
import argparse, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from tsp_core import load_tsp, check_tour
from run_experiments import ALGOS, BKS, DATA, budget_for, run_one


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", required=True, help="instance name in data/ (e.g. eil51) or path to a .tsp file")
    ap.add_argument("--algos", nargs="*", default=["HBALS"], help="names from run_experiments.ALGOS")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--budget", type=int, default=0, help="evaluation budget (default: the budget used in the paper)")
    ap.add_argument("--bks", type=float, default=0, help="best-known length (for the gap); default: value from the paper's table")
    a = ap.parse_args()

    path = a.instance if a.instance.endswith(".tsp") else os.path.join(DATA, a.instance + ".tsp")
    name, D = load_tsp(path)
    key = os.path.splitext(os.path.basename(path))[0]
    bks = a.bks or BKS.get(key, 0)
    B = a.budget or budget_for(key, D)
    print(f"instance {name}: N = {D.shape[0]}, budget = {B/1e6:.1f} M evaluations, best-known = {bks or 'unknown'}")
    first_tour = None
    for al in a.algos:
        kind, P = ALGOS[al]
        res, t0 = [], time.time()
        for r in range(a.runs):
            conv = np.zeros(100)
            c, t, ev, it = run_one(kind, P, D, B, 1000 + r, conv)
            check_tour(t, D, c)
            res.append(c)
            if al == a.algos[0] and (first_tour is None or c < first_tour[2]):
                first_tour = (al, t.copy(), c)
        res = np.array(res)
        s = f"{al:20s} best {res.min():.0f}  mean {res.mean():.1f}  std {res.std(ddof=1) if len(res) > 1 else 0:.1f}"
        if bks:
            s += f"  mean gap {(res.mean() - bks) / bks * 100:.3f}%"
        print(s + f"   ({time.time() - t0:.1f}s for {a.runs} runs)")
    al, t, c = first_tour
    print(f"\nbest tour found by {al} (length {c:.0f}), city indices starting at 0:")
    print(" ".join(map(str, t.tolist())))


if __name__ == "__main__":
    main()
