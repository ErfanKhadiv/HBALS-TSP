# HBALS: Hybrid Bee algorithm with Adaptive Local Search for Traveling Salesman Problem
# Publication-ready implementation with scientific optimizations

import argparse
import math
import random
import time
import numpy as np
import pandas as pd
import tsplib95
import matplotlib.pyplot as plt
import multiprocessing
import os
from tqdm import tqdm
from functools import partial
from dataclasses import dataclass
from typing import List, Tuple, Dict

@dataclass
class TSPResult:
    """Container for TSP algorithm results"""
    best_tour: List[int]
    best_cost: float
    convergence: List[float]
    run_time: float
    seed: int

class TSPInstance:
    """Efficient TSP instance handler with cached distance matrix"""
    
    def __init__(self, tsp_path: str):
        self.path = tsp_path
        self.problem = tsplib95.load(tsp_path)
        self.nodes = list(self.problem.get_nodes())
        self.n = len(self.nodes)
        self.coords = np.array([self.problem.node_coords[n] for n in self.nodes], dtype=float)
        self._dist_matrix = None
        # Extract instance name from path
        self.name = os.path.splitext(os.path.basename(tsp_path))[0]
    
    @property
    def dist_matrix(self) -> np.ndarray:
        """Lazy-loaded distance matrix with caching"""
        if self._dist_matrix is None:
            diff = self.coords.reshape((self.n, 1, 2)) - self.coords.reshape((1, self.n, 2))
            self._dist_matrix = np.sqrt((diff ** 2).sum(axis=2))
            self._dist_matrix = np.rint(self._dist_matrix).astype(float)
        return self._dist_matrix

class TSPSolver:
    """Base class with common TSP utilities"""
    
    @staticmethod
    def tour_length(tour: List[int], dist: np.ndarray) -> float:
        """Fast tour length calculation using numpy"""
        t = np.asarray(tour, dtype=int)
        return float(np.sum(dist[t, np.roll(t, -1)]))
    
    @staticmethod
    def random_tour(n: int) -> List[int]:
        """Generate random permutation tour"""
        t = list(range(n))
        random.shuffle(t)
        return t
    
    @staticmethod
    def nearest_neighbor_tour(dist: np.ndarray, start: int = 0) -> List[int]:
        """Construct greedy nearest neighbor tour"""
        n = dist.shape[0]
        unvisited = set(range(n))
        unvisited.remove(start)
        tour = [start]
        
        while unvisited:
            current = tour[-1]
            # Find nearest unvisited node
            nearest = min(unvisited, key=lambda node: dist[current, node])
            tour.append(nearest)
            unvisited.remove(nearest)
        
        return tour

class LocalSearch:
    """Optimized local search operations for TSP"""
    
    @staticmethod
    def two_opt_swap(tour: List[int], i: int, j: int) -> List[int]:
        """Perform 2-opt swap between indices i and j"""
        return tour[:i] + tour[i:j+1][::-1] + tour[j+1:]
    
    @staticmethod
    def two_opt_fast(tour: List[int], dist: np.ndarray, max_iterations: int = 50) -> Tuple[List[int], float]:
        """Optimized 2-opt with delta evaluation"""
        n = len(tour)
        current_tour = tour[:]
        current_len = TSPSolver.tour_length(current_tour, dist)
        improved = True
        iterations = 0
        
        while improved and iterations < max_iterations:
            improved = False
            iterations += 1
            
            for i in range(1, n - 2):
                for j in range(i + 1, n):
                    if j - i == 1: continue  # Skip adjacent edges
                    
                    # Delta evaluation - much faster than full tour length
                    a, b, c, d = current_tour[i-1], current_tour[i], current_tour[j], current_tour[(j+1) % n]
                    delta = dist[a, c] + dist[b, d] - dist[a, b] - dist[c, d]
                    
                    if delta < -1e-9:
                        current_tour = LocalSearch.two_opt_swap(current_tour, i, j)
                        current_len += delta
                        improved = True
                        break
                if improved:
                    break
                    
        return current_tour, current_len
    
    @staticmethod
    def three_opt_light(tour: List[int], dist: np.ndarray, max_tries: int = 8) -> List[int]:
        """Lightweight 3-opt with random segment reversal"""
        n = len(tour)
        best_tour = tour[:]
        best_len = TSPSolver.tour_length(best_tour, dist)
        
        for _ in range(max_tries):
            # Randomly select three distinct indices
            i, j, k = sorted(random.sample(range(1, n), 3))
            
            # Try reversing segment between i and j
            candidate = tour[:i] + tour[i:j][::-1] + tour[j:]
            candidate_len = TSPSolver.tour_length(candidate, dist)
            
            if candidate_len < best_len:
                best_tour, best_len = candidate, candidate_len
                
        return best_tour

class HBALS(TSPSolver):
    """
    Hybrid Bee algorithm with Adaptive Local Search
    Enhanced version with adaptive neighborhood and sophisticated local search
    """
    
    def __init__(self, params: Dict):
        self.params = params
        
    def initialize_population(self, dist: np.ndarray) -> Tuple[List[List[int]], List[float]]:
        """Initialize population with mixed NN and random tours"""
        n_nodes = dist.shape[0]
        n = self.params['n']
        nn_ratio = self.params.get('nn_ratio', 0.5)
        
        num_nn = max(1, int(nn_ratio * n))
        population = []
        
        # Nearest Neighbor tours from different starting points
        for start in range(min(num_nn, n_nodes)):
            population.append(self.nearest_neighbor_tour(dist, start))
        
        # Random tours to fill population
        while len(population) < n:
            population.append(self.random_tour(n_nodes))
        
        costs = [self.tour_length(tour, dist) for tour in population]
        return population, costs
    
    def search_elite_site(self, base_tour: List[int], dist: np.ndarray, 
                    nep: int, ngh: int) -> Tuple[List[int], float]:
        """Intensive search around elite site"""
        best_tour = base_tour[:]
        best_cost = self.tour_length(best_tour, dist)
        n_nodes = len(base_tour)
        
        for _ in range(nep):
            candidate = base_tour[:]
            
            # Apply multiple random swaps
            for _ in range(ngh):
                i, j = random.sample(range(n_nodes), 2)
                candidate[i], candidate[j] = candidate[j], candidate[i]
            
            # Aggressive local search
            if random.random() < 0.7:
                candidate, candidate_cost = LocalSearch.two_opt_fast(candidate, dist, 20)
            else:
                candidate_cost = self.tour_length(candidate, dist)
                
            # Occasional 3-opt refinement
            if random.random() < 0.1:
                candidate = LocalSearch.three_opt_light(candidate, dist, 3)
                candidate_cost = self.tour_length(candidate, dist)
            
            if candidate_cost < best_cost:
                best_tour, best_cost = candidate, candidate_cost
                
        return best_tour, best_cost
    
    def search_selected_site(self, base_tour: List[int], dist: np.ndarray,
                        nsp: int, ngh: int) -> Tuple[List[int], float]:
        """Moderate search around selected site"""
        best_tour = base_tour[:]
        best_cost = self.tour_length(best_tour, dist)
        n_nodes = len(base_tour)
        
        for _ in range(nsp):
            candidate = base_tour[:]
            
            # Fewer swaps for selected sites
            for _ in range(max(1, ngh // 2)):
                i, j = random.sample(range(n_nodes), 2)
                candidate[i], candidate[j] = candidate[j], candidate[i]
            
            # Light local search
            if random.random() < 0.3:
                candidate, candidate_cost = LocalSearch.two_opt_fast(candidate, dist, 10)
            else:
                candidate_cost = self.tour_length(candidate, dist)
            
            if candidate_cost < best_cost:
                best_tour, best_cost = candidate, candidate_cost
                
        return best_tour, best_cost
    
    def solve(self, dist: np.ndarray, max_iter: int = 500, seed: int = None) -> TSPResult:
        """Main HBALS algorithm with adaptive neighborhood and local search"""
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
            
        n_nodes = dist.shape[0]
        params = self.params
        
        # Extract parameters
        n, m, e = params['n'], params['m'], params['e']
        nep, nsp = params['nep'], params['nsp']
        alpha, beta = params['alpha'], params['beta']
        no_improve_threshold = params.get('no_improve_threshold', 25)
        
        # Initialize
        population, costs = self.initialize_population(dist)
        best_idx = np.argmin(costs)
        best_tour, best_cost = population[best_idx][:], costs[best_idx]
        convergence = [best_cost]
        no_improve_count = 0
        base_ngh = params['ngh']
        current_ngh = base_ngh
        
        start_time = time.time()
        
        # Main optimization loop
        for iteration in range(max_iter):
            # Adaptive neighborhood adjustment
            if no_improve_count >= 3:
                current_ngh = min(int(current_ngh * beta), n_nodes // 2)
            else:
                current_ngh = max(int(current_ngh * alpha), 1)
            
            # Sort population by quality
            sorted_indices = np.argsort(costs)
            elite_indices = sorted_indices[:e]
            selected_indices = sorted_indices[:m]
            
            new_population = []
            new_costs = []
            
            # Elite site exploitation
            for idx in elite_indices:
                improved_tour, improved_cost = self.search_elite_site(
                    population[idx], dist, nep, current_ngh)
                new_population.append(improved_tour)
                new_costs.append(improved_cost)
            
            # Selected site exploration
            for idx in selected_indices[e:m]:
                improved_tour, improved_cost = self.search_selected_site(
                    population[idx], dist, nsp, current_ngh)
                new_population.append(improved_tour)
                new_costs.append(improved_cost)
            
            # Scout bees - random exploration
            while len(new_population) < n:
                scout_tour = self.random_tour(n_nodes)
                scout_cost = self.tour_length(scout_tour, dist)
                new_population.append(scout_tour)
                new_costs.append(scout_cost)
            
            # Update population
            population, costs = new_population, new_costs
            
            # Update global best
            current_best_idx = np.argmin(costs)
            current_best_cost = costs[current_best_idx]
            
            if current_best_cost < best_cost:
                best_tour, best_cost = population[current_best_idx][:], current_best_cost
                no_improve_count = 0
            else:
                no_improve_count += 1
            
            convergence.append(best_cost)
            
            # Early stopping
            if no_improve_count >= no_improve_threshold:
                break
        
        # Ensure convergence history has exactly max_iter points
        if len(convergence) < max_iter:
            convergence.extend([best_cost] * (max_iter - len(convergence)))
        else:
            convergence = convergence[:max_iter]
            
        run_time = time.time() - start_time
        
        return TSPResult(
            best_tour=best_tour,
            best_cost=best_cost,
            convergence=convergence,
            run_time=run_time,
            seed=seed
        )

# -------------------------
# Scientific Presets (Optimized)
# -------------------------
PRESETS = {
    'fast': {
        'n': 20, 'm': 12, 'e': 3,
        'nep': 8, 'nsp': 4, 'ngh': 3,
        'alpha': 0.9, 'beta': 1.05,
        'nn_ratio': 0.5,
        'no_improve_threshold': 20
    },
    'balanced': {
        'n': 30, 'm': 15, 'e': 4,
        'nep': 20, 'nsp': 10, 'ngh': 4,
        'alpha': 0.92, 'beta': 1.08,
        'nn_ratio': 0.4,
        'no_improve_threshold': 30
    },
    'thorough': {
        'n': 50, 'm': 20, 'e': 5,
        'nep': 80, 'nsp': 35, 'ngh': 6,  # Reduced from original
        'alpha': 0.85, 'beta': 1.09,     # More aggressive
        'nn_ratio': 0.35,
        'no_improve_threshold': 40
    }
}

# -------------------------
# Parallel Experiment Runner
# -------------------------
class ExperimentRunner:
    """Handles parallel execution of multiple algorithm runs"""
    
    @staticmethod
    def run_single_experiment(args: Tuple) -> Dict:
        """Single experiment run for parallel processing"""
        tsp_path, preset_name, max_iter, seed = args
        instance = TSPInstance(tsp_path)
        solver = HBALS(PRESETS[preset_name])
        result = solver.solve(instance.dist_matrix, max_iter, seed)
        
        return {
            'best_cost': result.best_cost,
            'run_time': result.run_time,
            'convergence': result.convergence,
            'seed': seed
        }
    
    @staticmethod
    def run_parallel_experiments(tsp_path: str, preset: str = 'balanced',
                            runs: int = 10, max_iter: int = 500, 
                            procs: int = None) -> Dict:
        """Run multiple experiments in parallel"""
        if procs is None:
            procs = max(1, multiprocessing.cpu_count() - 1)
            
        # Generate unique seeds
        seeds = [int(time.time() * 1000) % (2**32) + i for i in range(runs)]
        args_list = [(tsp_path, preset, max_iter, seed) for seed in seeds]
        
        results = []
        with multiprocessing.Pool(processes=procs) as pool:
            for result in tqdm(pool.imap_unordered(ExperimentRunner.run_single_experiment, args_list),
                            total=runs, desc=f"HBALS-{preset}"):
                results.append(result)
        
        # Aggregate results
        best_costs = [r['best_cost'] for r in results]
        run_times = [r['run_time'] for r in results]
        convergences = [r['convergence'] for r in results]
        
        instance = TSPInstance(tsp_path)
        
        return {
            'instance': tsp_path,
            'instance_name': instance.name,
            'preset': preset,
            'best': float(np.min(best_costs)),
            'mean': float(np.mean(best_costs)),
            'std': float(np.std(best_costs)),
            'avg_time': float(np.mean(run_times)),
            'all_costs': best_costs,
            'all_times': run_times,
            'convergences': convergences
        }

# -------------------------
# Analysis and Visualization
# -------------------------
class ResultAnalyzer:
    """Handles result analysis and visualization"""
    
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
        plt.plot(avg_conv, 'b-', linewidth=2, label='HBALS (Average)')
        
        # Add min/max envelope
        min_conv = np.min(results['convergences'], axis=0)
        max_conv = np.max(results['convergences'], axis=0)
        plt.fill_between(range(len(avg_conv)), min_conv, max_conv, alpha=0.2, label='Min-Max Range')
        
        plt.xlabel('Iteration', fontsize=12)
        plt.ylabel('Tour Cost', fontsize=12)
        
        # Enhanced title with dataset name
        title = (f"HBALS Convergence - {results['instance_name'].upper()} "
                f"({results['preset']} preset, {len(results['convergences'])} runs)")
        plt.title(title, fontsize=14, pad=20)
        
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

# -------------------------
# Main CLI Interface
# -------------------------
def main():
    parser = argparse.ArgumentParser(
        description="HBALS: Hybrid Bee Algorithm with Local Search for TSP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Example usage:
            python HBALS.py --tsp-file instances/eil51.tsp --preset fast --runs 10 --max-iter 200
            python HBALS.py --tsp-file instances/berlin52.tsp --preset balanced --runs 20
        """
    )
    
    parser.add_argument('--tsp-file', required=True, help='Path to TSPLIB instance file')
    parser.add_argument('--preset', choices=list(PRESETS.keys()), default='balanced',
                    help='Parameter preset (fast, balanced, thorough)')
    parser.add_argument('--runs', type=int, default=10, help='Number of independent runs')
    parser.add_argument('--max-iter', type=int, default=500, help='Maximum iterations per run')
    parser.add_argument('--procs', type=int, help='Number of parallel processes (default: CPU_count-1)')
    parser.add_argument('--out-csv', help='Output CSV file for results (auto-generated if not provided)')
    parser.add_argument('--out-plot', help='Output plot file (auto-generated if not provided)')
    
    args = parser.parse_args()
    
    # Auto-generate output filenames based on instance name
    instance = TSPInstance(args.tsp_file)
    
    if args.out_csv is None:
        args.out_csv = f"hbals_{instance.name}_results.csv"
    
    if args.out_plot is None:
        args.out_plot = f"hbals_convergence_{instance.name}.png"
    
    print("=" * 60)
    print("HBALS: Hybrid Bee Algorithm with Local Search")
    print("=" * 60)
    print(f"Instance: {instance.name.upper()} ({instance.n} nodes)")
    print(f"Preset: {args.preset}")
    print(f"Runs: {args.runs}, Iterations: {args.max_iter}")
    print(f"Output CSV: {args.out_csv}")
    print(f"Output Plot: {args.out_plot}")
    print(f"Parameters: {PRESETS[args.preset]}")
    print("-" * 60)
    
    # Run experiments
    start_time = time.time()
    results = ExperimentRunner.run_parallel_experiments(
        args.tsp_file, args.preset, args.runs, args.max_iter, args.procs
    )
    total_time = time.time() - start_time
    
    # Display results
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    print(f"Instance: {results['instance_name'].upper()}")
    print(f"Best cost: {results['best']:.2f}")
    print(f"Mean cost: {results['mean']:.2f} ± {results['std']:.2f}")
    print(f"Average time per run: {results['avg_time']:.2f}s")
    print(f"Total experiment time: {total_time:.2f}s")
    print("-" * 60)
    
    # Save results to CSV
    df = pd.DataFrame([{
        'algorithm': 'HBALS',
        'instance': results['instance'],
        'instance_name': results['instance_name'],
        'preset': results['preset'],
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