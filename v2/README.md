# HBALS-TSP v2: equal-budget evaluation, ablation and statistics

Code, data and results for the paper *"HBALS: A Hybrid Bees Algorithm with 2-opt Local Search for the Travelling Salesman Problem, Evaluated by Ablation and Equal-Budget Comparison"*.

**Preprint (all versions):** [10.5281/zenodo.23450861](https://doi.org/10.5281/zenodo.23450861) · **Project overview and main results:** [root README](../README.md) · **How to run:** [`HOW_TO_RUN.md`](HOW_TO_RUN.md)

This folder supersedes the v1 study in the repository root (see "Corrections to v1" in the root README).

## What is in this folder

| Path | Purpose |
| --- | --- |
| `src/tsp_core.py` | Numba implementations of HBALS (all ablation variants) and the baselines: ILS-2opt, GA-2opt, ACO-2opt, multi-start 2-opt, plain BA |
| `src/run_experiments.py` | Resumable experiment runner (`--group main\|ablation\|large`); seeds 1000 + run index |
| `src/quick_test.py` | Run HBALS and the baselines on one instance (also your own EUC_2D `.tsp` file) |
| `src/analyze.py`, `src/make_paper_data.py` | Statistics (Friedman, Wilcoxon, Mann-Whitney, Holm), tables, figures |
| `src/validate_port.py`, `src/collect_env.py`, `src/compare_with_reference.py` | Check of the Numba port against the first implementation, environment report, comparison with the reference run |
| `run_all.py` | Run the whole study (`--verify`, `--fresh`, `--resume`) |
| `data/` | 21 TSPLIB files (EUC_2D): 15 reported, 4 used only for parameter tuning (kroC100, pr107, bier127, kroB150), 2 not used |
| `results/` | Per-run results (`csv/runs.csv`), anytime curves (`conv/`), tables, figures, budgets, environment (Windows 11 run) |
| `results_reference/` | Independent re-run in a Linux container; identical tour lengths, evaluation counts and iteration counts |

## Experimental design in brief

- **Methods:** HBALS, ILS-2opt, GA-2opt, ACO-2opt, multi-start 2-opt, plain BA.
- **Instances:** 12 main (51-198 cities, 20 runs), 3 larger (200-318 cities, 10 runs), 4 for the ablation (20 runs per variant).
- **Same 2-opt operator** in every method that uses local search, and **the same budget of move evaluations** for every method on an instance.
- **Budget unit:** one move evaluation (2-opt or segment-reversal delta = 1, swap delta = 4, full tour length = N, ant construction = N^2/2, order crossover = N).
  Per-instance budget = evaluations used by 300 HBALS iterations (`results/budgets.json`).
- **Statistics:** Friedman test with Nemenyi critical difference, Wilcoxon signed-rank on instance means with Holm correction, per-instance Mann-Whitney U with effect size (A12).

## Main results

See the [root README](../README.md#results-at-a-glance). Short version: HBALS has the best average rank (1.25 of 6) on the 12 main instances,
is not significantly different from ILS-2opt overall, and ILS-2opt is better from about 195 cities upward.

Figures are in [`results/figures/`](results/figures/), tables in [`results/tables/`](results/tables/).

## Quick start

```bash
pip install -r requirements.txt
python src/quick_test.py --instance eil51
python run_all.py --verify
```

## Citation

Please cite the preprint: Khadiv, E. (2026). *HBALS: A Hybrid Bees Algorithm with 2-opt Local Search for the Travelling Salesman Problem, Evaluated by Ablation and Equal-Budget Comparison.* Zenodo. <https://doi.org/10.5281/zenodo.23450861>
