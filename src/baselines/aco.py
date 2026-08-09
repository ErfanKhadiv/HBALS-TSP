# Ant Colony Optimization for TSP
# Standard implementation with Ant System

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

class AntColonyOptimization:
    """Standard Ant Colony Optimization for TSP"""
    
    @staticmethod
    def tour_length(tour: List[int], dist: np.ndarray) -> float:
        t = np.asarray(tour, dtype=int)
        return float(np.sum(dist[t, np.roll(t, -1)]))
    
    def construct_solution(self, dist: np.ndarray, pheromone: np.ndarray, 
                        alpha: float, beta: float) -> List[int]:
        n = dist.shape[0]
        start_city = random.randint(0, n-1)
        tour = [start_city]
        unvisited = set(range(n)) - {start_city}
        
        while unvisited:
            current_city = tour[-1]
            
            # Calculate probabilities for next city
            probabilities = []
            for next_city in unvisited:
                if dist[current_city, next_city] > 0:
                    tau = pheromone[current_city, next_city] ** alpha
                    eta = (1.0 / dist[current_city, next_city]) ** beta
                    probabilities.append(tau * eta)
                else:
                    probabilities.append(0)
            
            # Select next city
            if sum(probabilities) > 0:
                probabilities = [p / sum(probabilities) for p in probabilities]
                next_city = random.choices(list(unvisited), weights=probabilities)[0]
            else:
                next_city = random.choice(list(unvisited))
            
            tour.append(next_city)
            unvisited.remove(next_city)
        
        return tour
    
    def update_pheromone(self, pheromone: np.ndarray, tours: List[List[int]], 
                        costs: List[float], rho: float, Q: float) -> np.ndarray:
        # Evaporation
        pheromone *= (1.0 - rho)
        
        # Add new pheromone
        for tour, cost in zip(tours, costs):
            pheromone_deposit = Q / cost
            for i in range(len(tour)):
                j = (i + 1) % len(tour)
                pheromone[tour[i], tour[j]] += pheromone_deposit
                pheromone[tour[j], tour[i]] += pheromone_deposit
        
        return pheromone
    
    def solve(self, dist: np.ndarray, params: Dict, max_iter: int = 500, seed: int = None) -> TSPResult:
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
            
        n = dist.shape[0]
        n_ants = params['n_ants']
        alpha = params['alpha']
        beta = params['beta']
        rho = params['rho']
        Q = params['Q']
        initial_pheromone = params['initial_pheromone']
        
        # Initialize pheromone matrix
        pheromone = np.ones((n, n)) * initial_pheromone
        
        best_tour = None
        best_cost = float('inf')
        convergence = []
        
        start_time = time.time()
        
        for iteration in range(max_iter):
            tours = []
            costs = []
            
            # Construct solutions
            for _ in range(n_ants):
                tour = self.construct_solution(dist, pheromone, alpha, beta)
                cost = self.tour_length(tour, dist)
                tours.append(tour)
                costs.append(cost)
                
                if cost < best_cost:
                    best_tour, best_cost = tour, cost
            
            # Update pheromone
            pheromone = self.update_pheromone(pheromone, tours, costs, rho, Q)
            
            convergence.append(best_cost)
        
        run_time = time.time() - start_time
        
        return TSPResult(
            best_tour=best_tour,
            best_cost=best_cost,
            convergence=convergence,
            run_time=run_time,
            seed=seed
        )

# ACO Parameters (standard values from literature)
ACO_PARAMS = {
    'n_ants': 20,
    'alpha': 1.0,    # Pheromone importance
    'beta': 2.0,     # Distance importance  
    'rho': 0.5,      # Evaporation rate
    'Q': 100.0,      # Pheromone constant
    'initial_pheromone': 0.1
}

class ExperimentRunner:
    @staticmethod
    def run_single_experiment(args: Tuple) -> Dict:
        tsp_path, max_iter, seed = args
        instance = TSPInstance(tsp_path)
        solver = AntColonyOptimization()
        result = solver.solve(instance.dist_matrix, ACO_PARAMS, max_iter, seed)
        
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
                            total=runs, desc="AntColony"):
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
    """Handles result analysis and visualization for ACO"""
    
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
        plt.plot(avg_conv, 'orange', linewidth=2, label='Ant Colony (Average)')
        
        # Add min/max envelope
        min_conv = np.min(results['convergences'], axis=0)
        max_conv = np.max(results['convergences'], axis=0)
        plt.fill_between(range(len(avg_conv)), min_conv, max_conv, alpha=0.2, label='Min-Max Range')
        
        plt.xlabel('Iteration', fontsize=12)
        plt.ylabel('Tour Cost', fontsize=12)
        
        # Enhanced title with dataset name
        title = (f"Ant Colony Optimization Convergence - {results['instance_name'].upper()} "
                f"({len(results['convergences'])} runs)")
        plt.title(title, fontsize=14, pad=20)
        
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

def main():
    parser = argparse.ArgumentParser(description="Ant Colony Optimization for TSP")
    parser.add_argument('--tsp-file', required=True, help='Path to TSPLIB instance file')
    parser.add_argument('--runs', type=int, default=20, help='Number of independent runs')
    parser.add_argument('--max-iter', type=int, default=300, help='Maximum iterations per run')
    parser.add_argument('--procs', type=int, help='Number of parallel processes')
    parser.add_argument('--out-csv', help='Output CSV file')
    parser.add_argument('--out-plot', help='Output plot file')
    
    args = parser.parse_args()
    
    instance = TSPInstance(args.tsp_file)
    
    if args.out_csv is None:
        args.out_csv = f"aco_{instance.name}_results.csv"
    if args.out_plot is None:
        args.out_plot = f"aco_convergence_{instance.name}.png"
    
    print("=" * 60)
    print("Ant Colony Optimization for TSP")
    print("=" * 60)
    print(f"Instance: {instance.name.upper()} ({instance.n} nodes)")
    print(f"Runs: {args.runs}, Iterations: {args.max_iter}")
    print(f"Output CSV: {args.out_csv}")
    print(f"Output Plot: {args.out_plot}")
    print(f"Parameters: {ACO_PARAMS}")
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
        'algorithm': 'AntColony',
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