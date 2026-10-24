# How to run and test HBALS v2

`results_reference/` holds the reference results (AI assistant, Linux container). `results/` holds the author's own full re-run (Windows 11); they are identical run by run.
`results/` is where YOUR runs go. The runner skips every (instance, method) block already present in
`results/csv/runs.csv`, so never copy the reference runs.csv into `results/` if you want to reproduce the results yourself.

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

## 3. Independent verification (about 15-40 min)  <- do this first
```bash
python run_all.py --verify
```
Runs 4 small instances x 7 methods x 20 runs on your machine and compares every run with `results_reference/`
(`results/comparison_with_reference.txt`). Identical tour lengths run-by-run are expected when seeds and library behaviour
match; otherwise the script reports whether the differences are statistically significant.

## 4. Full study (several hours, resumable)
```bash
python run_all.py --fresh        # moves any old results/ to results_backup_<time>/ and recomputes everything
python run_all.py --resume       # continue after an interruption
```
Keep 20 runs per method (do not edit --runs) so your numbers are comparable with the manuscript.

## 5. What to send back
Zip the folder `results/` (runs.csv, conv/, tables/, figures/, environment.txt, validation_log.txt,
comparison_with_reference.txt, analysis_log.txt, paper_data.json).
