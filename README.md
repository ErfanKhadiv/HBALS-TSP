# HBALS: Hybrid Bees Algorithm with Adaptive Local Search for the Traveling Salesman Problem

A hybrid metaheuristic that combines the **Bees Algorithm (BA)** with adaptive **2-opt/3-opt local search** to solve the Traveling Salesman Problem (TSP).

The project investigates whether adaptive local search can improve solution quality and convergence while preserving the exploration capability of a population-based metaheuristic.

> 🎓 **Academic Project**
> Bachelor's final project for the **Computer Project** course at Islamic Azad University, Ardabil (2026), supervised by **Dr. Masoud Bakravi**.

---

## 🔬 Research Question

Can adaptive local search improve the Bees Algorithm for the TSP by refining promising solutions while maintaining sufficient population diversity for exploration?

---

## 💡 Approach

HBALS combines the global exploration of the Bees Algorithm with targeted local improvement:

1. **Population initialization**
   A mixture of Nearest-Neighbor and random tours is used to balance initial solution quality and diversity.

2. **Population evaluation**
   Candidate tours are evaluated and ranked according to their total length.

3. **Elite-site search**
   Intensive 2-opt local search, with occasional 3-opt moves, is applied to the best candidate solutions.

4. **Selected-site search**
   Lighter local search is applied to additional promising solutions.

5. **Scout bees**
   New candidate tours are introduced to maintain exploration and reduce premature convergence.

6. **Adaptive neighborhood**
   The search radius is adjusted according to improvement or stagnation.

7. **Termination**
   The process continues until the maximum number of iterations is reached or the search stagnates for a specified number of generations.

---

## 📊 Experimental Evaluation

HBALS was evaluated on six standard **TSPLIB** benchmark instances.

Each experiment used:

* **20 independent runs**
* **300 iterations**
* `fast` configuration
* Best, mean, standard deviation, and execution time recorded

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

Across the six tested benchmark instances, HBALS obtained the lowest tour length among the implemented baselines in the recorded experiments. The complete comparison results are available in [`results/csv/`](results/csv/).

---

## 📈 Convergence

Convergence curves are provided for HBALS and all baseline algorithms.

See [`results/plots/`](results/plots/) for the complete set of generated plots.

---

## 🧠 Algorithm Components

### Bees Algorithm

The population-based search is organized around:

* Elite sites
* Selected sites
* Recruited bees
* Scout bees

### Local Search

HBALS incorporates:

* **2-opt** for systematic route improvement
* A lightweight **3-opt-inspired segment reversal operation**
* Adaptive neighborhood control

The local-search intensity is concentrated around promising solutions rather than applied uniformly to the entire population.

---

## 🧪 Reproducibility

All six benchmark instances used in the experiments are included in the repository, so the experiments can be reproduced without downloading external datasets.

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
├── requirements.txt
├── LICENSE
└── README.md
```

---

## ⚠️ Limitations

* The implemented 3-opt operation is a lightweight randomized segment-reversal search rather than a full 3-opt neighborhood.
* Performance is sensitive to parameter settings; automated parameter optimization was not performed.
* Experiments were conducted on instances up to 195 cities.
* Scalability to substantially larger instances has not been evaluated.

---

## 🚀 Future Work

Potential extensions include:

* Automated parameter self-tuning
* Parallel or GPU-accelerated local search
* More extensive TSPLIB benchmarking
* Full 3-opt neighborhood exploration
* Hybridization with Lin-Kernighan search
* Evaluation on larger TSP instances

---

## 📄 Project Documentation

The original project paper is available in [`docs/`](docs/).

The repository also contains the complete experimental results and generated plots.

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

For the associated academic report, see [`docs/`](docs/).

---

## 📜 License

This project is licensed under the MIT License. See [`LICENSE`](LICENSE) for details.
