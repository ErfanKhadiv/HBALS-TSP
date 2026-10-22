# HBALS: Hybrid Bees Algorithm with Adaptive Local Search for the Traveling Salesman Problem

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Problem](https://img.shields.io/badge/Problem-Traveling%20Salesman-orange)
![Benchmark](https://img.shields.io/badge/Benchmark-TSPLIB%20(6%20instances)-informational)
![Project](https://img.shields.io/badge/Bachelor's%20Final%20Project-2026-A51C30)
[![Preprint DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23450862.svg)](https://doi.org/10.5281/zenodo.23450862)
![License](https://img.shields.io/badge/License-MIT-green)

HBALS is a hybrid metaheuristic that combines the **Bees Algorithm (BA)** with adaptive **2-opt / 3-opt local search** to solve the **Traveling Salesman Problem (TSP)**. The project asks whether adaptive local search can improve solution quality and convergence while keeping the exploration ability of a population-based method. It was my Bachelor's final project (*Computer Project* course, Islamic Azad University, Ardabil, 2026), supervised by Dr. Masoud Bakravi. This repository contains the HBALS implementation, four baseline algorithms (BA, ACO, GA, PSO), the six TSPLIB instances used in the experiments, the generated results and plots, and the written project report. A preprint of the paper is available on Zenodo: [10.5281/zenodo.23450862](https://doi.org/10.5281/zenodo.23450862).

## Contents

- [Research question](#research-question)
- [Motivation](#motivation)
- [Method](#method)
- [Experimental evaluation](#experimental-evaluation)
- [Convergence](#convergence)
- [Compared algorithms](#compared-algorithms)
- [Concepts and skills covered](#concepts-and-skills-covered)
- [Repository structure](#repository-structure)
- [Setup and running](#setup-and-running)
- [Limitations](#limitations)
- [Future work](#future-work)
- [Project report and preprint](#project-report-and-preprint)
- [Academic information](#academic-information)
- [Citation](#citation)
- [License](#license)

## Research question

Can adaptive local search improve the solution quality and convergence behavior of the Bees Algorithm for the Traveling Salesman Problem while maintaining sufficient population diversity?

## Motivation

The TSP is a classic combinatorial optimization problem, and exact methods become harder to apply as the number of cities grows. Population-based metaheuristics are a practical alternative, but the standard Bees Algorithm can converge slowly or get trapped in local optima. HBALS applies local search **adaptively to the promising regions of the population**, combining global exploration with targeted local improvement.

## Method

| Step | Stage | What it does |
| --- | --- | --- |
| 1 | Population initialization | Builds the initial population from a mixture of Nearest-Neighbor and random tours, balancing starting quality and diversity |
| 2 | Evaluation and ranking | Scores each tour by total route length and ranks the population |
| 3 | Elite-site search | Applies intensive 2-opt local search, with occasional 3-opt moves, to the best candidate solutions |
| 4 | Selected-site search | Applies lighter local search to additional promising solutions |
| 5 | Scout bees | Introduces new candidate tours to preserve exploration and reduce premature convergence |
| 6 | Adaptive neighborhood | Adjusts the search neighborhood according to improvement or stagnation |
| 7 | Termination | Stops at the maximum number of iterations, or when the search stagnates for a set number of generations |

## Experimental evaluation

HBALS was evaluated on six standard TSPLIB benchmark instances. Each experiment used 20 independent runs of 300 iterations with the `fast` preset, and recorded the best solution, mean solution quality, standard deviation and execution time.

### HBALS results

| Dataset | Cities | Best | Mean | Std. dev. | Time (s) |
| --- | --- | --- | --- | --- | --- |
| `eil51` | 51 | 426 | 427.85 | 1.68 | 4.62 |
| `berlin52` | 52 | 7542 | 7543.00 | 2.00 | 5.31 |
| `st70` | 70 | 675 | 679.40 | 2.82 | 11.91 |
| `kroA100` | 100 | 21296 | 21388.60 | 79.06 | 39.17 |
| `ch150` | 150 | 6570 | 6627.95 | 40.13 | 83.68 |
| `rat195` | 195 | 2349 | 2375.30 | 14.16 | 161.51 |

### Baseline comparison

Four baseline algorithms are implemented: the Bees Algorithm (BA), Ant Colony Optimization (ACO), a Genetic Algorithm (GA) and Particle Swarm Optimization (PSO). In the experiments conducted for this project, **HBALS obtained the lowest tour length among the implemented baselines on all six tested instances**. The full comparison is in [`results/`](results).

## Convergence

The repository includes convergence plots for HBALS and all baselines in [`results/plots/`](results/plots). On the tested instances, HBALS reaches near-final solution quality relatively early in the optimization.

## Compared algorithms

| Algorithm | Description |
| --- | --- |
| **HBALS** | Hybrid Bees Algorithm with adaptive local search |
| **BA** | Basic Bees Algorithm without the HBALS local-search component |
| **ACO** | Ant Colony Optimization using an Ant System approach |
| **GA** | Genetic Algorithm with ordered crossover and permutation-based mutation |
| **PSO** | Particle Swarm Optimization adapted for permutation-based TSP solutions |

The baselines give a direct comparison against different population-based and swarm-inspired approaches.

## Concepts and skills covered

- **Combinatorial optimization:** the Traveling Salesman Problem, tour construction, Nearest-Neighbor heuristic
- **Local search:** 2-opt and (randomized) 3-opt moves, adaptive neighborhoods
- **Metaheuristics:** Bees Algorithm, Ant Colony Optimization, Genetic Algorithm, Particle Swarm Optimization
- **Experimental method:** TSPLIB benchmarks, repeated independent runs, best / mean / standard deviation / runtime reporting, convergence analysis
- **Research practice:** reproducible experiments, documented limitations, project report, citation metadata
- **Tools:** Python

## Repository structure

```
HBALS-TSP/
├── src/
│   ├── hbals.py            # HBALS
│   └── baselines/
│       ├── ba.py
│       ├── aco.py
│       ├── ga.py
│       └── pso.py
├── data/                   # the six TSPLIB instances
│   ├── eil51.tsp
│   ├── berlin52.tsp
│   ├── st70.tsp
│   ├── kroA100.tsp
│   ├── ch150.tsp
│   └── rat195.tsp
├── results/
│   ├── csv/                # HBALS results
│   ├── plots/              # HBALS convergence curves
│   └── baselines/
│       ├── csv/
│       └── plots/
├── docs/
│   └── HBALS_paper.docx    # project report
├── CITATION.cff
├── LICENSE
├── requirements.txt
└── README.md
```

## Setup and running

All six benchmark instances are included, so the reported experiments can be reproduced without downloading any external dataset.

```
pip install -r requirements.txt
```

Run HBALS:

```
python src/hbals.py \
    --tsp-file data/eil51.tsp \
    --preset fast \
    --runs 20 \
    --max-iter 300
```

Run the baselines (the same arguments apply to each):

```
python src/baselines/ba.py  --tsp-file data/eil51.tsp --runs 20 --max-iter 300
python src/baselines/aco.py --tsp-file data/eil51.tsp --runs 20 --max-iter 300
python src/baselines/ga.py  --tsp-file data/eil51.tsp --runs 20 --max-iter 300
python src/baselines/pso.py --tsp-file data/eil51.tsp --runs 20 --max-iter 300
```

Replace `eil51.tsp` with any other file in `data/` to run a different instance.

## Limitations

- The implemented **3-opt operator is a lightweight randomized segment-reversal search**, not a full 3-opt neighborhood.
- Performance is sensitive to parameter settings, and automated parameter optimization was not performed.
- The experiments cover instances up to **195 cities**; behavior on substantially larger instances has not been evaluated.
- Runtime grows with local-search effort and problem size.

These limitations are stated explicitly to distinguish the current implementation from possible future extensions.

## Future work

- Adaptive parameter self-tuning
- More extensive TSPLIB benchmarking
- Full 3-opt neighborhood exploration
- Parallel or GPU-accelerated local search
- Hybridization with stronger local-search methods such as Lin-Kernighan

## Project report and preprint

The written report for this Bachelor's final project is in [`docs/`](docs). It covers the project background, algorithm design, related work, methodology, experimental evaluation and discussion.

The paper is also available as a preprint on Zenodo: **[https://doi.org/10.5281/zenodo.23450862](https://doi.org/10.5281/zenodo.23450862)**.

## Academic information

| | |
| --- | --- |
| **Project** | HBALS: Hybrid Bees Algorithm with Adaptive Local Search |
| **Degree** | B.Sc. in Computer Engineering |
| **Course** | Computer Architecture Project |
| **University** | Islamic Azad University, Ardabil |
| **Year** | 2026 |
| **Supervisor** | Dr. Masoud Bakravi |

## Citation

If you use this implementation or build on this project, please cite:

> Khadiv, Erfan. (2026). *HBALS: Hybrid Bees Algorithm with Adaptive Local Search for the Traveling Salesman Problem*. GitHub. <https://github.com/ErfanKhadiv/HBALS-TSP>

The preprint can be cited by its DOI: <https://doi.org/10.5281/zenodo.23450862>.

Citation metadata is also provided in [`CITATION.cff`](CITATION.cff).

## License

Released under the MIT license; see [LICENSE](LICENSE).
