# Genetic Algorithm for TSP
# Standard implementation with OX crossover and swap mutation

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

class GeneticAlgorithm:
    """Standard Genetic Algorithm for TSP"""
    
    @staticmethod
    def tour_length(tour: List[int], dist: np.ndarray) -> float:
        t = np.asarray(tour, dtype=int)
        return float(np.sum(dist[t, np.roll(t, -1)]))
    
    @staticmethod
    def random_tour(n: int) -> List[int]:
        t = list(range(n))
        random.shuffle(t)
        return t
    
    def initialize_population(self, n: int, pop_size: int) -> List[List[int]]:
        return [self.random_tour(n) for _ in range(pop_size)]
    
    def ordered_crossover(self, parent1: List[int], parent2: List[int]) -> List[int]:
        """OX crossover for TSP"""
        n = len(parent1)
        start, end = sorted(random.sample(range(n), 2))
        
        child = [-1] * n
        child[start:end+1] = parent1[start:end+1]
        
        current_pos = (end + 1) % n
        parent2_pos = (end + 1) % n
        
        while -1 in child:
            gene = parent2[parent2_pos]
            if gene not in child:
                child[current_pos] = gene
                current_pos = (current_pos + 1) % n
            parent2_pos = (parent2_pos + 1) % n
            
        return child
    
    def swap_mutation(self, tour: List[int], mutation_rate: float) -> List[int]:
        """Swap mutation"""
        if random.random() < mutation_rate:
            i, j = random.sample(range(len(tour)), 2)
            tour[i], tour[j] = tour[j], tour[i]
        return tour
    
    def tournament_selection(self, population: List[List[int]], costs: List[float], 
                        tournament_size: int) -> List[int]:
        """Tournament selection"""
        contestants = random.sample(range(len(population)), tournament_size)
        best_idx = min(contestants, key=lambda i: costs[i])
        return population[best_idx][:]
    
    def solve(self, dist: np.ndarray, params: Dict, max_iter: int = 500, seed: int = None) -> TSPResult:
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
            
        n_nodes = dist.shape[0]
        pop_size = params['pop_size']
        mutation_rate = params['mutation_rate']
        crossover_rate = params['crossover_rate']
        tournament_size = params['tournament_size']
        elitism_count = params['elitism_count']
        
        # Initialize population
        population = self.initialize_population(n_nodes, pop_size)
        costs = [self.tour_length(tour, dist) for tour in population]
        best_idx = np.argmin(costs)
        best_tour, best_cost = population[best_idx][:], costs[best_idx]
        convergence = [best_cost]
        
        start_time = time.time()
        
        for generation in range(max_iter):
            new_population = []
            
            # Elitism: keep best individuals
            elite_indices = np.argsort(costs)[:elitism_count]
            for idx in elite_indices:
                new_population.append(population[idx][:])
            
            # Fill rest of population
            while len(new_population) < pop_size:
                if random.random() < crossover_rate:
                    parent1 = self.tournament_selection(population, costs, tournament_size)
                    parent2 = self.tournament_selection(population, costs, tournament_size)
                    child = self.ordered_crossover(parent1, parent2)
                    child = self.swap_mutation(child, mutation_rate)
                else:
                    child = self.tournament_selection(population, costs, tournament_size)
                    child = self.swap_mutation(child, mutation_rate)
                new_population.append(child)
            
            population = new_population
            costs = [self.tour_length(tour, dist) for tour in population]
            
            # Update best
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

# GA Parameters (comparable computational effort)
GA_PARAMS = {
    'pop_size': 20,
    'mutation_rate': 0.1,
    'crossover_rate': 0.8,
    'tournament_size': 3,
    'elitism_count': 2
}

class ExperimentRunner:
    @staticmethod
    def run_single_experiment(args: Tuple) -> Dict:
        tsp_path, max_iter, seed = args
        instance = TSPInstance(tsp_path)
        solver = GeneticAlgorithm()
        result = solver.solve(instance.dist_matrix, GA_PARAMS, max_iter, seed)
        
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
                            total=runs, desc="GeneticAlgorithm"):
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
    """Handles result analysis and visualization for GA"""
    
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
        plt.plot(avg_conv, 'g-', linewidth=2, label='Genetic Algorithm (Average)')
        
        # Add min/max envelope
        min_conv = np.min(results['convergences'], axis=0)
        max_conv = np.max(results['convergences'], axis=0)
        plt.fill_between(range(len(avg_conv)), min_conv, max_conv, alpha=0.2, label='Min-Max Range')
        
        plt.xlabel('Generation', fontsize=12)
        plt.ylabel('Tour Cost', fontsize=12)
        
        # Enhanced title with dataset name
        title = (f"Genetic Algorithm Convergence - {results['instance_name'].upper()} "
                f"({len(results['convergences'])} runs)")
        plt.title(title, fontsize=14, pad=20)
        
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

def main():
    parser = argparse.ArgumentParser(description="Genetic Algorithm for TSP")
    parser.add_argument('--tsp-file', required=True, help='Path to TSPLIB instance file')
    parser.add_argument('--runs', type=int, default=20, help='Number of independent runs')
    parser.add_argument('--max-iter', type=int, default=300, help='Maximum iterations per run')
    parser.add_argument('--procs', type=int, help='Number of parallel processes')
    parser.add_argument('--out-csv', help='Output CSV file')
    parser.add_argument('--out-plot', help='Output plot file')
    
    args = parser.parse_args()
    
    instance = TSPInstance(args.tsp_file)
    
    if args.out_csv is None:
        args.out_csv = f"ga_{instance.name}_results.csv"
    if args.out_plot is None:
        args.out_plot = f"ga_convergence_{instance.name}.png"
    
    print("=" * 60)
    print("Genetic Algorithm for TSP")
    print("=" * 60)
    print(f"Instance: {instance.name.upper()} ({instance.n} nodes)")
    print(f"Runs: {args.runs}, Generations: {args.max_iter}")
    print(f"Output CSV: {args.out_csv}")
    print(f"Output Plot: {args.out_plot}")
    print(f"Parameters: {GA_PARAMS}")
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
        'algorithm': 'GeneticAlgorithm',
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