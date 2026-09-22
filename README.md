# HBALS: Hybrid Bees Algorithm with Adaptive Local Search for the Traveling Salesman Problem

A hybrid metaheuristic that combines the **Bees Algorithm (BA)** with adaptive **2-opt / 3-opt local search** to solve the **Traveling Salesman Problem (TSP)**.

The project investigates whether adaptive local search can improve solution quality and convergence while preserving the exploration capability of a population-based metaheuristic.

> 🎓 **Bachelor's Final Project**
> Computer Project course, Islamic Azad University, Ardabil — 2026
> **Supervisor:** Dr. Masoud Bakravi

---

## 🔬 Research Question

Can adaptive local search improve the solution quality and convergence behavior of the Bees Algorithm for the Traveling Salesman Problem while maintaining sufficient population diversity?

---

## 💡 Motivation

The Traveling Salesman Problem is a classic combinatorial optimization problem for which exact methods become increasingly difficult to apply as the problem size grows.

Population-based metaheuristics provide a practical alternative, but the standard Bees Algorithm can experience slow convergence or become trapped in local optima.

HBALS addresses this by applying local search **adaptively to promising regions of the population**, combining global exploration with targeted local improvement.

---

## 🧠 Method

HBALS combines the Bees Algorithm with adaptive local search through the following process:

1. **Population initialization**
   Generate an initial population using a mixture of Nearest-Neighbor and random tours to balance initial solution quality and diversity.

2. **Evaluation and ranking**
   Evaluate candidate tours according to their total route length and rank the population.

3. **Elite-site search**
   Apply intensive 2-opt local search, with occasional 3-opt moves, to the best candidate solutions.

4. **Selected-site search**
   Apply lighter local search to additional promising solutions.

5. **Scout bees**
   Introduce new candidate tours to preserve exploration and reduce premature convergence.

6. **Adaptive neighborhood**
   Adjust the search neighborhood according to improvement or stagnation.

7. **Termination**
   Continue until the maximum number of iterations is reached or the search stagnates for a specified number of generations.

---

## 📊 Experimental Evaluation

HBALS was evaluated on six standard TSPLIB benchmark instances.

Each experiment used:

* **20 independent runs**
* **300 iterations**
* `fast` preset
* Best solution
* Mean solution quality
* Standard deviation
* Execution time

### HBALS Results

| Dataset    | Cities |  Best |     Mean | Std. Dev. | Time (s) |
| ---------- | -----: | ----: | -------: | --------: | -------: |
| `eil51`    |     51 |   426 |   427.85 |      1.68 |     4.62 |
| `berlin52` |     52 |  7542 |  7543.00 |      2.00 |     5.31 |
| `st70`     |     70 |   675 |   679.40 |      2.82 |    11.91 |
| `kroA100`  |    100 | 21296 | 21388.60 |     79.06 |    39.17 |
| `ch150`    |    150 |  6570 |  6627.95 |     40.13 |    83.68 |
| `rat195`   |    195 |  2349 |  2375.30 |     14.16 |   161.51 |

### Baseline Comparison

The implementation includes four baseline algorithms:

* **Bees Algorithm (BA)**
* **Ant Colony Optimization (ACO)**
* **Genetic Algorithm (GA)**
* **Particle Swarm Optimization (PSO)**

In the experiments conducted for this project, **HBALS obtained the lowest tour length among the implemented baselines on all six tested instances**.

The complete comparison results are available in [`results/`](results/).

---

## 📈 Convergence

The repository includes convergence plots for HBALS and all baseline algorithms.

The experiments show that HBALS reaches near-final solution quality relatively early in the optimization process on the tested instances.

See [`results/plots/`](results/plots/) for the generated convergence curves.

---

## ⚙️ Compared Algorithms

### HBALS

Hybrid Bees Algorithm with adaptive local search.

### BA

Basic Bees Algorithm without the HBALS local-search component.

### ACO

Ant Colony Optimization using an Ant System approach.

### GA

Genetic Algorithm using ordered crossover and permutation-based mutation.

### PSO

Particle Swarm Optimization adapted for permutation-based TSP solutions.

These baseline implementations provide a direct comparison against different population-based and swarm-inspired optimization approaches.

---

## 🧪 Reproducibility

All six benchmark instances used in the experiments are included in the repository, so the reported experiments can be reproduced without downloading external datasets.

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

### Run the Baselines

```bash
python src/baselines/ba.py \
    --tsp-file data/eil51.tsp \
    --runs 20 \
    --max-iter 300

python src/baselines/aco.py \
    --tsp-file data/eil51.tsp \
    --runs 20 \
    --max-iter 300

python src/baselines/ga.py \
    --tsp-file data/eil51.tsp \
    --runs 20 \
    --max-iter 300

python src/baselines/pso.py \
    --tsp-file data/eil51.tsp \
    --runs 20 \
    --max-iter 300
```

---

## 📁 Repository Structure

```text
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

* The implemented **3-opt operator is a lightweight randomized segment-reversal search**, rather than a full 3-opt neighborhood.
* Performance is sensitive to parameter settings, and automated parameter optimization was not performed.
* The experiments cover instances up to **195 cities**; behavior on substantially larger instances has not been evaluated.
* Runtime increases as local-search effort and problem size increase.

These limitations are documented explicitly to distinguish the current implementation from possible future extensions.

---

## 🚀 Future Work

Possible directions for extending the project include:

* Adaptive parameter self-tuning
* More extensive TSPLIB benchmarking
* Full 3-opt neighborhood exploration
* Parallel or GPU-accelerated local search
* Hybridization with stronger local-search methods such as Lin-Kernighan

---

## 📄 Project Report

The written report accompanying this Bachelor's final project is available in [`docs/`](docs/).

It contains the project background, algorithm design, related work, methodology, experimental evaluation, and discussion.

---

## 🎓 Academic Information

**Project:** HBALS — Hybrid Bees Algorithm with Adaptive Local Search  
**Degree:** B.Sc. in Computer Engineering  
**Course:** Computer Project  
**University:** Islamic Azad University, Ardabil  
**Year:** 2026  
**Supervisor:** Dr. Masoud Bakravi  

---

## 📚 Citation

If you use this implementation or build upon this project, please cite:

> Khadiv, Erfan. (2026). *HBALS: Hybrid Bees Algorithm with Adaptive Local Search for the Traveling Salesman Problem*. GitHub.
> https://github.com/ErfanKhadiv/HBALS-TSP

Citation metadata is also provided in [`CITATION.cff`](CITATION.cff).

---

## 📜 License

This project is licensed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
