# HBALS: Hybrid Bees Algorithm with Adaptive Local Search for the Traveling Salesman Problem

A hybrid metaheuristic that combines the **Bees Algorithm (BA)** with adaptive neighborhood control and **2-opt / lightweight 3-opt-style local search** to solve the **Traveling Salesman Problem (TSP)**.

The project investigates whether adaptive neighborhood control and local-search refinement can improve the solution quality and convergence of the Bees Algorithm while preserving the exploration capability of a population-based metaheuristic.

> 🎓 **Bachelor's Final Project**, Computer Project course, Islamic Azad University, Ardabil (2026)

---

## 🔬 Research Question

Can adaptive neighborhood control and local-search refinement improve the solution quality and convergence behavior of the Bees Algorithm for the Traveling Salesman Problem while maintaining sufficient population diversity?

---

## 💡 Motivation

The TSP is a classic NP-hard combinatorial optimization problem. Exact methods become impractical as the number of cities grows, so metaheuristics are widely used to obtain high-quality tours within practical computational budgets.

The standard Bees Algorithm can converge slowly or stall in local optima. HBALS addresses this by intensifying the search around elite and selected sites with local search, while scout bees keep the population exploring new regions.

---

## 🧠 Method

1. **Population initialization**: a mixture of Nearest-Neighbor and random tours (`nn_ratio = 0.5`) balances initial quality and diversity.
2. **Adaptive neighborhood adjustment**: the neighborhood size (number of random-swap perturbations) is shrunk by `α = 0.9` while progress is recent, and grown by `β = 1.05` after 3 or more consecutive non-improving iterations (upper bound `N/2`, lower bound 1).
3. **Evaluation and ranking**: tours are ranked by total length.
4. **Elite-site search**: the best `e = 3` tours each generate `nep = 8` candidates, which are perturbed, then refined with 2-opt (probability 0.7) and, occasionally, lightweight 3-opt-style refinement (probability 0.1).
5. **Selected-site search**: the remaining sites among the top `m = 12` each generate `nsp = 4` candidates with lighter perturbation and 2-opt (probability 0.3).
6. **Scout bees**: new random tours refill the population to `n_b = 20`.
7. **Global-best update and termination**: stop after 300 iterations, or after 20 consecutive non-improving iterations.

The full pseudocode and parameter rationale are in the [project report](docs/).

---

## 📊 Experimental Evaluation

HBALS was evaluated on six TSPLIB instances (up to 195 cities). Each algorithm used:

- **20 independent runs**
- **300 maximum iterations**
- HBALS `fast` preset, no automated parameter tuning
- Windows 11, Intel Core i3 (12th gen), 16 GB RAM, Python 3.12.7

### HBALS results

BKS = best-known solution. Mean Gap = (Mean − BKS) / BKS × 100.

| Dataset    | Cities | BKS   | Best  | Mean     | Std. Dev. | Mean Gap (%) | Time (s) |
| ---------- | ------ | ----- | ----- | -------- | --------- | ------------ | -------- |
| `eil51`    | 51     | 426   | 426   | 427.85   | 1.68      | 0.43         | 4.62     |
| `berlin52` | 52     | 7542  | 7542  | 7543.00  | 2.00      | 0.01         | 5.31     |
| `st70`     | 70     | 675   | 675   | 679.40   | 2.82      | 0.65         | 11.91    |
| `kroA100`  | 100    | 21282 | 21296 | 21388.60 | 79.06     | 0.50         | 39.17    |
| `ch150`    | 150    | 6528  | 6570  | 6627.95  | 40.13     | 1.53         | 83.68    |
| `rat195`   | 195    | 2323  | 2349  | 2375.30  | 14.16     | 2.25         | 161.51   |

HBALS reached the BKS on `eil51`, `berlin52`, and `st70`, with mean gaps between 0.01% and 2.25% across all six instances.

### Comparison with baselines

Implemented baselines: **BA**, **ACO** (Ant System), **GA**, and **PSO**. Values are **Best (Mean)** over 20 runs.

| Dataset    | HBALS               | ACO                 | PSO                 | BA                  | GA                    |
| ---------- | ------------------- | ------------------- | ------------------- | ------------------- | --------------------- |
| `eil51`    | **426** (427.85)    | 438 (452.75)        | 489 (505.65)        | 503 (543.70)        | 674 (770.65)          |
| `berlin52` | **7542** (7543.00)  | 7548 (7684.45)      | 8801 (8970.65)      | 9592 (9838.55)      | 12368 (14009.00)      |
| `st70`     | **675** (679.40)    | 698 (731.60)        | 765 (810.90)        | 978 (1084.05)       | 1570 (1711.20)        |
| `kroA100`  | **21296** (21388.60)| 23240 (23611.40)    | 25816 (26117.15)    | 44975 (48562.60)    | 71781 (79111.40)      |
| `ch150`    | **6570** (6627.95)  | 6758 (6964.35)      | 7309 (7309.00)      | 16817 (18193.60)    | 27083 (29230.70)      |
| `rat195`   | **2349** (2375.30)  | 2466 (2552.95)      | 2742 (2751.20)      | 7344 (7843.50)      | 11063 (12062.65)      |

- HBALS obtained the lowest best-tour length on all six instances.
- Relative to the implemented BA baseline, HBALS reduced the best-tour length by **15.3% to 68.0%** (arithmetic mean **41.5%**).
- Baselines were run with the parameter settings implemented in this repository, with the same number of runs and iteration budget. They were **not** tuned to identical internal parameters, so the comparison evaluates the implemented configurations.

### Statistical analysis

A **Friedman test** on mean tour lengths across the six instances showed a significant difference among the five algorithms (χ² = 24.0, p < 0.001). Mean ranks: HBALS 1.00, ACO 2.00, PSO 3.00, BA 4.00, GA 5.00.

Post-hoc **Nemenyi** comparisons against HBALS:

| Comparison      | p-value | Significant at 0.05 |
| --------------- | ------- | ------------------- |
| HBALS vs BA     | 0.009   | Yes                 |
| HBALS vs GA     | 0.0001  | Yes                 |
| HBALS vs ACO    | 0.809   | **No**              |
| HBALS vs PSO    | 0.183   | **No**              |

HBALS ranked first on every instance, but with only six instances the differences from **ACO and PSO are not statistically significant**. These results are evidence about the tested configurations, not a universal conclusion about the underlying methods.

### Runtime

| Dataset    | HBALS  | BA   | GA   | PSO  | ACO    |
| ---------- | ------ | ---- | ---- | ---- | ------ |
| `eil51`    | 4.62   | 1.77 | 0.34 | 0.29 | 20.66  |
| `berlin52` | 5.31   | 1.70 | 0.33 | 0.34 | 21.97  |
| `st70`     | 11.91  | 1.81 | 0.47 | 0.35 | 45.94  |
| `kroA100`  | 39.17  | 1.92 | 0.67 | 0.50 | 123.28 |
| `ch150`    | 83.68  | 2.52 | 1.23 | 0.68 | 363.54 |
| `rat195`   | 161.51 | 2.59 | 1.95 | 0.93 | 767.89 |

Average time per run, in seconds. HBALS is slower than BA, GA, and PSO because of perturbation and local-search overhead, and generally faster than ACO.

### Comparison with published Bees-Algorithm methods

Mean gap from BKS (%). Published results come from different implementations, parameters, hardware, and stopping criteria, so treat this comparison cautiously.

| Dataset    | HBALS | Sahin (2023) | Suluova & Pham (2024) |
| ---------- | ----- | ------------ | --------------------- |
| `eil51`    | 0.43  | not reported | 2.58                  |
| `berlin52` | 0.01  | 0.03         | 5.14                  |
| `st70`     | 0.65  | 0.31         | 3.11                  |
| `kroA100`  | 0.50  | 0.02         | 3.46                  |
| `ch150`    | 1.53  | 0.37         | 6.13                  |
| `rat195`   | 2.25  | 0.73         | not reported          |

HBALS is competitive but does **not** consistently outperform all published methods: the reported Sahin (2023) results are closer to the BKS on `st70`, `kroA100`, `ch150`, and `rat195`.

---

## 📈 Convergence

Convergence plots (mean best-so-far over 20 runs, with min–max range) are available for all six instances in [`results/plots/`](results/plots), and for the baselines in [`results/baselines/plots/`](results/baselines/plots).

On the tested instances HBALS typically improves rapidly in early iterations and then approaches a stable solution region. This is an observation on these instances only; no universal convergence-rate advantage is claimed.

---

## ⚙️ Compared Algorithms

- **HBALS**: Hybrid Bees Algorithm with adaptive neighborhood control and local search.
- **BA**: Basic Bees Algorithm with random initialization, fixed neighborhood (`ngh = 3`), and single-swap neighbors; no HBALS-specific components.
- **ACO**: Ant Colony Optimization (Ant System).
- **GA**: Genetic Algorithm with ordered crossover and permutation-based mutation.
- **PSO**: Particle Swarm Optimization adapted for permutation-based TSP solutions.

---

## 🧪 Reproducibility

All six benchmark instances are included in [`data/`](data), so the experiments can be reproduced without downloading external datasets.

### Installation

```bash
pip install -r requirements.txt
```

### Run HBALS

```bash
python src/hbals.py \
    --tsp-file data/eil51.tsp \
    --preset fast \
    --runs 20 \
    --max-iter 300
```

### Run the baselines

```bash
python src/baselines/ba.py  --tsp-file data/eil51.tsp --runs 20 --max-iter 300
python src/baselines/aco.py --tsp-file data/eil51.tsp --runs 20 --max-iter 300
python src/baselines/ga.py  --tsp-file data/eil51.tsp --runs 20 --max-iter 300
python src/baselines/pso.py --tsp-file data/eil51.tsp --runs 20 --max-iter 300
```

---

## 📁 Repository Structure

```
HBALS-TSP/
├── src/
│   ├── hbals.py
│   └── baselines/
│       ├── ba.py
│       ├── aco.py
│       ├── ga.py
│       └── pso.py
│
├── data/
│   ├── eil51.tsp
│   ├── berlin52.tsp
│   ├── st70.tsp
│   ├── kroA100.tsp
│   ├── ch150.tsp
│   └── rat195.tsp
│
├── results/
│   ├── csv/
│   ├── plots/
│   └── baselines/
│       ├── csv/
│       └── plots/
│
├── docs/
│   └── HBALS_paper.docx
│
├── CITATION.cff
├── LICENSE
├── requirements.txt
└── README.md
```

---

## ⚠️ Limitations

- **No ablation study.** The complete hybrid configuration was evaluated, so the individual contributions of Nearest-Neighbor initialization, adaptive neighborhood control, 2-opt, and lightweight 3-opt-style refinement cannot be isolated.
- The implemented **3-opt operator is a lightweight randomized segment-reversal search**, not a full 3-opt neighborhood.
- Performance is sensitive to parameter settings; automated parameter optimization was not performed.
- Experiments cover instances up to **195 cities** only; behavior on substantially larger instances is untested.
- Only six instances were used for statistical testing, and differences from ACO and PSO are not statistically significant.
- Runtime grows with instance size and local-search effort.

---

## 🚀 Future Work

- Ablation experiments for each HBALS component
- Adaptive parameter self-tuning
- More extensive TSPLIB benchmarking, including larger instances
- Full 3-opt neighborhood exploration
- Parallel or GPU-accelerated local search
- Hybridization with stronger local-search methods such as Lin-Kernighan

---

## 📄 Project Report

The written report is available in [`docs/`](docs). It covers background, related work, algorithm design, methodology, experimental evaluation, comparison with recent methods, and discussion.

---

## 🎓 Academic Information

**Project:** HBALS: Hybrid Bees Algorithm with Adaptive Local Search  
**Degree:** B.Sc. in Computer Engineering  
**Course:** Computer Project  
**University:** Islamic Azad University, Ardabil  
**Year:** 2026  
**Course supervisor:** Dr. Masoud Bakravi

---

## 📚 Citation

If you use this implementation or build upon this project, please cite:

> Khadiv, Erfan. (2026). *HBALS: Hybrid Bees Algorithm with Adaptive Local Search for the Traveling Salesman Problem*. GitHub. <https://github.com/ErfanKhadiv/HBALS-TSP>

Citation metadata is also provided in [`CITATION.cff`](CITATION.cff).

---

## 📜 License

This project is licensed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
