# Basic Bee Algorithm for TSP
# Standard implementation without local search for fair comparison

import argparse
import random
import time
import numpy as np
import pandas as pd
import tsplib95
import matplotlib.pyplot as plt
import multiprocessing
import os
from tqdm import tqdm
from dataclasses import dataclass
from typing import List, Tuple, Dict

@dataclass
class TSPResult:
    best_tour: List[int]
    best_cost: float
    convergence: List[float]
    run_time: float
    seed: int

class TSPInstance:
    def __init__(self, tsp_path: str):
        self.path = tsp_path
        self.problem = tsplib95.load(tsp_path)
        self.nodes = list(self.problem.get_nodes())
        self.n = len(self.nodes)
        self.coords = np.array([self.problem.node_coords[n] for n in self.nodes], dtype=float)
        self._dist_matrix = None
        self.name = os.path.splitext(os.path.basename(tsp_path))[0]
    
    @property
    def dist_matrix(self) -> np.ndarray:
        if self._dist_matrix is None:
            diff = self.coords.reshape((self.n, 1, 2)) - self.coords.reshape((1, self.n, 2))
            self._dist_matrix = np.sqrt((diff ** 2).sum(axis=2))
            self._dist_matrix = np.rint(self._dist_matrix).astype(float)
        return self._dist_matrix

class BasicBA:
    """Standard Bee Algorithm without local search"""
    
    @staticmethod
    def tour_length(tour: List[int], dist: np.ndarray) -> float:
        t = np.asarray(tour, dtype=int)
        return float(np.sum(dist[t, np.roll(t, -1)]))
    
    @staticmethod
    def random_tour(n: int) -> List[int]:
        t = list(range(n))
        random.shuffle(t)
        return t
    
    @staticmethod
    def nearest_neighbor_tour(dist: np.ndarray, start: int = 0) -> List[int]:
        n = dist.shape[0]
        unvisited = set(range(n))
        unvisited.remove(start)
        tour = [start]
        
        while unvisited:
            current = tour[-1]
            nearest = min(unvisited, key=lambda node: dist[current, node])
            tour.append(nearest)
            unvisited.remove(nearest)
        return tour
    
    def initialize_population(self, dist: np.ndarray, n: int, nn_ratio: float) -> Tuple[List[List[int]], List[float]]:
        n_nodes = dist.shape[0]
        num_nn = max(1, int(nn_ratio * n))
        population = []
        
        for start in range(min(num_nn, n_nodes)):
            population.append(self.nearest_neighbor_tour(dist, start))
        
        while len(population) < n:
            population.append(self.random_tour(n_nodes))
        
        costs = [self.tour_length(tour, dist) for tour in population]
        return population, costs
    
    def search_site(self, base_tour: List[int], dist: np.ndarray, 
                num_bees: int, ngh: int) -> Tuple[List[int], float]:
        """Basic search without local search - only random perturbations"""
        best_tour = base_tour[:]
        best_cost = self.tour_length(best_tour, dist)
        n_nodes = len(base_tour)
        
        for _ in range(num_bees):
            candidate = base_tour[:]
            
            # Simple random swaps
            for _ in range(ngh):
                i, j = random.sample(range(n_nodes), 2)
                candidate[i], candidate[j] = candidate[j], candidate[i]
            
            candidate_cost = self.tour_length(candidate, dist)
            
            if candidate_cost < best_cost:
                best_tour, best_cost = candidate, candidate_cost
                
        return best_tour, best_cost
    
    def solve(self, dist: np.ndarray, params: Dict, max_iter: int = 500, seed: int = None) -> TSPResult:
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
            
        n_nodes = dist.shape[0]
        n, m, e = params['n'], params['m'], params['e']
        nep, nsp, ngh = params['nep'], params['nsp'], params['ngh']
        nn_ratio = params.get('nn_ratio', 0.3)
        
        # Initialize population
        population, costs = self.initialize_population(dist, n, nn_ratio)
        best_idx = np.argmin(costs)
        best_tour, best_cost = population[best_idx][:], costs[best_idx]
        convergence = [best_cost]
        
        start_time = time.time()
        
        for iteration in range(max_iter):
            # Sort by quality
            sorted_indices = np.argsort(costs)
            elite_indices = sorted_indices[:e]
            selected_indices = sorted_indices[:m]
            
            new_population = []
            new_costs = []
            
            # Elite sites
            for idx in elite_indices:
                improved_tour, improved_cost = self.search_site(
                    population[idx], dist, nep, ngh)
                new_population.append(improved_tour)
                new_costs.append(improved_cost)
            
            # Selected sites
            for idx in selected_indices[e:m]:
                improved_tour, improved_cost = self.search_site(
                    population[idx], dist, nsp, ngh)
                new_population.append(improved_tour)
                new_costs.append(improved_cost)
            
            # Scout bees
            while len(new_population) < n:
                scout_tour = self.random_tour(n_nodes)
                scout_cost = self.tour_length(scout_tour, dist)
                new_population.append(scout_tour)
                new_costs.append(scout_cost)
            
            population, costs = new_population, new_costs
            
            # Update global best
            current_best_idx = np.argmin(costs)
            current_best_cost = costs[current_best_idx]
            
            if current_best_cost < best_cost:
                best_tour, best_cost = population[current_best_idx][:], current_best_cost
            
            convergence.append(best_cost)
        
        run_time = time.time() - start_time
        
        return TSPResult(
            best_tour=best_tour,
            best_cost=best_cost,
            convergence=convergence,
            run_time=run_time,
            seed=seed
        )

# BA Parameters (same as HBALS fast preset for fair comparison)
BA_PARAMS = {
    'n': 20,
    'm': 12,
    'e': 3,
    'nep': 8,
    'nsp': 4,
    'ngh': 3,
    'nn_ratio': 0.5
}

class ExperimentRunner:
    @staticmethod
    def run_single_experiment(args: Tuple) -> Dict:
        tsp_path, max_iter, seed = args
        instance = TSPInstance(tsp_path)
        solver = BasicBA()
        result = solver.solve(instance.dist_matrix, BA_PARAMS, max_iter, seed)
        
        return {
            'best_cost': result.best_cost,
            'run_time': result.run_time,
            'convergence': result.convergence,
            'seed': seed
        }
    
    @staticmethod
    def run_parallel_experiments(tsp_path: str, runs: int = 20, max_iter: int = 300, 
                            procs: int = None) -> Dict:
        if procs is None:
            procs = max(1, multiprocessing.cpu_count() - 1)
            
        seeds = [int(time.time() * 1000) % (2**32) + i for i in range(runs)]
        args_list = [(tsp_path, max_iter, seed) for seed in seeds]
        
        results = []
        with multiprocessing.Pool(processes=procs) as pool:
            for result in tqdm(pool.imap_unordered(ExperimentRunner.run_single_experiment, args_list),
                            total=runs, desc="BasicBA"):
                results.append(result)
        
        best_costs = [r['best_cost'] for r in results]
        run_times = [r['run_time'] for r in results]
        convergences = [r['convergence'] for r in results]
        
        instance = TSPInstance(tsp_path)
        
        return {
            'instance': tsp_path,
            'instance_name': instance.name,
            'best': float(np.min(best_costs)),
            'mean': float(np.mean(best_costs)),
            'std': float(np.std(best_costs)),
            'avg_time': float(np.mean(run_times)),
            'all_costs': best_costs,
            'all_times': run_times,
            'convergences': convergences
        }

class ResultAnalyzer:
    """Handles result analysis and visualization for BA"""
    
    @staticmethod
    def average_convergence(convergences: List[List[float]]) -> np.ndarray:
        """Compute average convergence curve across runs"""
        max_len = max(len(c) for c in convergences)
        padded = [c + [c[-1]] * (max_len - len(c)) if len(c) < max_len else c 
                for c in convergences]
        return np.mean(padded, axis=0)
    
    @staticmethod
    def plot_convergence(results: Dict, output_path: str):
        """Plot convergence curves with dataset name in title"""
        plt.figure(figsize=(10, 6))
        
        avg_conv = ResultAnalyzer.average_convergence(results['convergences'])
        plt.plot(avg_conv, 'r-', linewidth=2, label='Basic BA (Average)')
        
        # Add min/max envelope
        min_conv = np.min(results['convergences'], axis=0)
        max_conv = np.max(results['convergences'], axis=0)
        plt.fill_between(range(len(avg_conv)), min_conv, max_conv, alpha=0.2, label='Min-Max Range')
        
        plt.xlabel('Iteration', fontsize=12)
        plt.ylabel('Tour Cost', fontsize=12)
        
        # Enhanced title with dataset name
        title = (f"Basic BA Convergence - {results['instance_name'].upper()} "
                f"({len(results['convergences'])} runs)")
        plt.title(title, fontsize=14, pad=20)
        
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

def main():
    parser = argparse.ArgumentParser(description="Basic Bee Algorithm for TSP")
    parser.add_argument('--tsp-file', required=True, help='Path to TSPLIB instance file')
    parser.add_argument('--runs', type=int, default=20, help='Number of independent runs')
    parser.add_argument('--max-iter', type=int, default=300, help='Maximum iterations per run')
    parser.add_argument('--procs', type=int, help='Number of parallel processes')
    parser.add_argument('--out-csv', help='Output CSV file')
    parser.add_argument('--out-plot', help='Output plot file')
    
    args = parser.parse_args()
    
    instance = TSPInstance(args.tsp_file)
    
    if args.out_csv is None:
        args.out_csv = f"ba_{instance.name}_results.csv"
    if args.out_plot is None:
        args.out_plot = f"ba_convergence_{instance.name}.png"
    
    print("=" * 60)
    print("Basic Bee Algorithm for TSP")
    print("=" * 60)
    print(f"Instance: {instance.name.upper()} ({instance.n} nodes)")
    print(f"Runs: {args.runs}, Iterations: {args.max_iter}")
    print(f"Output CSV: {args.out_csv}")
    print(f"Output Plot: {args.out_plot}")
    print(f"Parameters: {BA_PARAMS}")
    print("-" * 60)
    
    start_time = time.time()
    results = ExperimentRunner.run_parallel_experiments(
        args.tsp_file, args.runs, args.max_iter, args.procs
    )
    total_time = time.time() - start_time
    
    print("\nRESULTS SUMMARY")
    print("=" * 60)
    print(f"Instance: {results['instance_name'].upper()}")
    print(f"Best cost: {results['best']:.2f}")
    print(f"Mean cost: {results['mean']:.2f} ± {results['std']:.2f}")
    print(f"Average time per run: {results['avg_time']:.2f}s")
    print(f"Total experiment time: {total_time:.2f}s")
    print("-" * 60)
    
    # Save results to CSV
    df = pd.DataFrame([{
        'algorithm': 'BasicBA',
        'instance': results['instance'],
        'instance_name': results['instance_name'],
        'n_nodes': instance.n,
        'best': results['best'],
        'mean': results['mean'],
        'std': results['std'],
        'avg_time_s': results['avg_time'],
        'runs': args.runs,
        'max_iter': args.max_iter
    }])
    df.to_csv(args.out_csv, index=False)
    print(f"Results saved to: {args.out_csv}")
    
    # Generate convergence plot
    ResultAnalyzer.plot_convergence(results, args.out_plot)
    print(f"Convergence plot saved to: {args.out_plot}")

if __name__ == "__main__":
    main()