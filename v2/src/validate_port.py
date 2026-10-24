"""Checks that the Numba port reproduces the first manuscript's HBALS results
(first-version configuration: integer-truncated neighbourhood, early stop after
20 stagnant iterations, at most 300 iterations, 20 runs)."""
import os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from tsp_core import *
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = []
paper = {"eil51": 427.85, "berlin52": 7543.0, "st70": 679.4, "kroA100": 21388.6, "ch150": 6627.95, "rat195": 2375.3}
for nm, pm in paper.items():
    _, D = load_tsp(os.path.join(ROOT, "data", nm + ".tsp"))
    conv = np.zeros(100)
    P = make_params(adapt=0, thr=20, max_iter=300)
    res, its = [], []
    for s in range(20):
        c, t, ev, it = hbals(D, P, 0, 100 + s, conv)
        res.append(c); its.append(it)
    line = f"{nm:9s} port mean {np.mean(res):9.2f}  first-manuscript mean {pm:9.2f}  avg iterations {np.mean(its):5.1f}"
    print(line, flush=True)
    LOG.append(line)
os.makedirs(os.path.join(ROOT, "results"), exist_ok=True)
open(os.path.join(ROOT, "results", "validation_log.txt"), "w").write("\n".join(LOG) + "\n")
