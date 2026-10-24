# How to run and test HBALS v2

`results_reference/` holds an independent reference run (produced in an AI assistant's code-execution environment on Linux).
`results/` holds the author's own full run (Windows 11). The two are identical run by run.

When you run the code yourself, your results are written to `results/`. The runner skips every (instance, method) block that is already present in
`results/csv/runs.csv`, so do not copy the reference `runs.csv` into `results/` if you want to reproduce the results from scratch.

## 1. Install (Python 3.10+)
```bash
cd v2
pip install -r requirements.txt        # numpy scipy pandas matplotlib numba
```
The first run takes ~15-30 s extra (Numba compiles the code once).

## 2. Quick tests
```bash
python src/quick_test.py --instance eil51
python src/quick_test.py --instance kroA100 --algos HBALS ILS-2opt GA-2opt --runs 5
python src/quick_test.py --instance path/to/my.tsp --bks 12345 --runs 5     # your own EUC_2D TSPLIB file
python src/quick_test.py --instance eil51 --budget 5000000                    # smaller budget = faster
```

## 3. Independent verification (about 15-40 min)
```bash
python run_all.py --verify
```
Runs 4 small instances x 7 methods x 20 runs on your machine and compares every run with `results_reference/`
(output: `results/comparison_with_reference.txt`). Identical tour lengths run by run are expected when seeds and library behaviour
match; otherwise the script reports whether the differences are statistically significant.

## 4. Full study (several hours, resumable)
```bash
python run_all.py --fresh        # moves any old results/ to results_backup_<time>/ and recomputes everything
python run_all.py --resume       # continue after an interruption
```
Keep 20 runs per method (do not edit `--runs`) so your numbers are comparable with the paper.

## 5. Output files
Everything is written to `results/`:

| File or folder | Content |
| --- | --- |
| `csv/runs.csv` | One row per run (instance, method, seed, best length, evaluations, iterations, time) |
| `conv/` | Anytime curves (best-so-far versus evaluations) |
| `tables/` | Summary, Friedman, Wilcoxon, Mann-Whitney, ablation and protocol tables |
| `figures/` | Box plots, anytime curves, ablation and protocol-effect plots |
| `budgets.json`, `paper_data.json` | Per-instance budgets and the numbers used in the paper |
| `environment.txt` | Python and library versions, operating system, CPU |
| `validation_log.txt` | Check of the Numba port against the first implementation |
| `comparison_with_reference.txt` | Run-by-run comparison with `results_reference/` |
