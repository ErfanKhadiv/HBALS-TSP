# HBALS-TSP v2: equal-budget evaluation, ablation and statistics

Code, data and results for the manuscript "HBALS: A Hybrid Bees Algorithm with 2-opt Local Search for the Travelling Salesman
Problem, Evaluated by Ablation and Equal-Budget Comparison". See `HOW_TO_RUN.md` for installation and testing.

* `src/tsp_core.py` - Numba implementations of HBALS (all variants) and the baselines (ILS, GA, ACO, multi-start 2-opt, plain BA)
* `src/run_experiments.py` - resumable experiment runner (`--group main|ablation|large`); seeds 1000 + run index
* `src/quick_test.py` - run HBALS/baselines on one instance (also your own EUC_2D `.tsp` file)
* `src/analyze.py`, `src/make_paper_data.py` - statistics, tables, figures
* `src/validate_port.py`, `src/collect_env.py`, `src/compare_with_reference.py` - validation, environment report, comparison
* `run_all.py` - run the whole study (`--verify`, `--fresh`, `--resume`)
* `data/` TSPLIB instances; `results/` per-run results (Windows 11 run), anytime curves, tables, figures;
  `results_reference/csv/runs.csv` independent run in a Linux container (identical tour lengths, evaluation counts and iteration counts)

Budget unit: one move evaluation (2-opt or segment-reversal delta = 1, swap delta = 4, full tour length = N, ant construction = N^2/2,
order crossover = N). Per-instance budget = evaluations used by 300 HBALS iterations (`results/budgets.json`).
