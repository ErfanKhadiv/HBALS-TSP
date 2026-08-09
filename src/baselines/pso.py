# Particle Swarm Optimization for TSP - FIXED VERSION
# Same parameters as other algorithms: 20 runs, 300 iterations

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

class ParticleSwarmOptimization:
    """Fixed PSO for TSP - No infinite loops, same parameters"""
    
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
    
    def safe_order_crossover(self, parent1: List[int], parent2: List[int]) -> List[int]:
        """Safe OX crossover that cannot hang"""
        n = len(parent1)
        if n <= 1:
            return parent1[:]
            
        start, end = sorted(random.sample(range(n), 2))
        child = [-1] * n
        
        # Copy segment from parent1
        child[start:end+1] = parent1[start:end+1]
        
        # Fill remaining positions from parent2 - SAFE VERSION
        used_positions = set(child[start:end+1])
        current_pos = (end + 1) % n
        
        for i in range(n):
            if child[i] == -1:
                # Find next available gene from parent2
                for j in range(n):
                    gene = parent2[(current_pos + j) % n]
                    if gene not in used_positions:
                        child[i] = gene
                        used_positions.add(gene)
                        current_pos = (current_pos + j + 1) % n
                        break
                # If still not filled, fill with any remaining
                if child[i] == -1:
                    for gene in parent2:
                        if gene not in used_positions:
                            child[i] = gene
                            used_positions.add(gene)
                            break
        
        return child
    
    def swap_mutation(self, tour: List[int], mutation_rate: float) -> List[int]:
        """Safe swap mutation"""
        if len(tour) <= 1 or random.random() > mutation_rate:
            return tour[:]
        i, j = random.sample(range(len(tour)), 2)
        new_tour = tour[:]
        new_tour[i], new_tour[j] = new_tour[j], new_tour[i]
        return new_tour
    
    def initialize_population(self, dist: np.ndarray, pop_size: int, nn_ratio: float) -> List[List[int]]:
        """Initialize population with mixed strategies"""
        n_nodes = dist.shape[0]
        num_nn = max(1, int(nn_ratio * pop_size))
        population = []
        
        # Nearest Neighbor tours
        for start in range(min(num_nn, n_nodes)):
            population.append(self.nearest_neighbor_tour(dist, start))
        
        # Random tours
        while len(population) < pop_size:
            population.append(self.random_tour(n_nodes))
        
        return population
    
    def solve(self, dist: np.ndarray, params: Dict, max_iter: int = 500, seed: int = None) -> TSPResult:
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
            
        n_nodes = dist.shape[0]
        pop_size = params['pop_size']
        w = params['inertia_weight']
        c1 = params['cognitive_weight']
        c2 = params['social_weight']
        mutation_rate = params['mutation_rate']
        nn_ratio = params.get('nn_ratio', 0.3)
        
        # Initialize population
        population = self.initialize_population(dist, pop_size, nn_ratio)
        costs = [self.tour_length(tour, dist) for tour in population]
        
        # Initialize personal bests
        personal_best = [tour[:] for tour in population]
        personal_best_costs = costs[:]
        
        # Initialize global best
        best_idx = np.argmin(costs)
        global_best = population[best_idx][:]
        global_best_cost = costs[best_idx]
        
        convergence = [global_best_cost]
        start_time = time.time()
        
        # Main optimization loop - SAFE VERSION
        for iteration in range(max_iter):
            new_population = []
            new_costs = []
            
            for i in range(pop_size):
                current_tour = population[i]
                current_cost = costs[i]
                
                # Start with current tour
                candidate = current_tour[:]
                
                # PSO updates - SAFE VERSION
                rand_val = random.random()
                
                if rand_val < c1:
                    # Move toward personal best
                    candidate = self.safe_order_crossover(current_tour, personal_best[i])
                elif rand_val < c1 + c2:
                    # Move toward global best  
                    candidate = self.safe_order_crossover(current_tour, global_best)
                # Else: keep current tour (exploration)
                
                # Apply mutation
                candidate = self.swap_mutation(candidate, mutation_rate)
                
                # Apply inertia (keep some characteristics from current tour)
                if random.random() < w:
                    # Keep a random segment from current tour
                    if n_nodes > 1:
                        segment_size = random.randint(1, n_nodes // 3)
                        start_pos = random.randint(0, n_nodes - segment_size)
                        if start_pos + segment_size <= n_nodes:
                            # Preserve this segment in candidate
                            segment = current_tour[start_pos:start_pos+segment_size]
                            # Create new candidate that includes this segment
                            remaining = [x for x in candidate if x not in segment]
                            candidate = remaining[:start_pos] + segment + remaining[start_pos:]
                
                candidate_cost = self.tour_length(candidate, dist)
                
                # Update personal best
                if candidate_cost < personal_best_costs[i]:
                    personal_best[i] = candidate[:]
                    personal_best_costs[i] = candidate_cost
                
                new_population.append(candidate)
                new_costs.append(candidate_cost)
            
            # Update population
            population = new_population
            costs = new_costs
            
            # Update global best
            current_best_idx = np.argmin(costs)
            current_best_cost = costs[current_best_idx]
            
            if current_best_cost < global_best_cost:
                global_best = population[current_best_idx][:]
                global_best_cost = current_best_cost
            
            convergence.append(global_best_cost)
        
        run_time = time.time() - start_time
        
        return TSPResult(
            best_tour=global_best,
            best_cost=global_best_cost,
            convergence=convergence,
            run_time=run_time,
            seed=seed
        )

# PSO Parameters (SAME AS ORIGINAL - only algorithm is fixed)
PSO_PARAMS = {
    'pop_size': 20,
    'inertia_weight': 0.7,
    'cognitive_weight': 0.8,
    'social_weight': 0.9,
    'mutation_rate': 0.1,
    'nn_ratio': 0.3
}

class ExperimentRunner:
    @staticmethod
    def run_single_experiment(args: Tuple) -> Dict:
        tsp_path, max_iter, seed = args
        instance = TSPInstance(tsp_path)
        solver = ParticleSwarmOptimization()
        result = solver.solve(instance.dist_matrix, PSO_PARAMS, max_iter, seed)
        
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
                            total=runs, desc="PSO"):
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
    """Handles result analysis and visualization for PSO"""
    
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
        plt.plot(avg_conv, 'purple', linewidth=2, label='PSO (Average)')
        
        # Add min/max envelope
        min_conv = np.min(results['convergences'], axis=0)
        max_conv = np.max(results['convergences'], axis=0)
        plt.fill_between(range(len(avg_conv)), min_conv, max_conv, alpha=0.2, label='Min-Max Range')
        
        plt.xlabel('Iteration', fontsize=12)
        plt.ylabel('Tour Cost', fontsize=12)
        
        # Enhanced title with dataset name
        title = (f"Particle Swarm Optimization Convergence - {results['instance_name'].upper()} "
                f"({len(results['convergences'])} runs)")
        plt.title(title, fontsize=14, pad=20)
        
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()

def main():
    parser = argparse.ArgumentParser(description="Particle Swarm Optimization for TSP")
    parser.add_argument('--tsp-file', required=True, help='Path to TSPLIB instance file')
    parser.add_argument('--runs', type=int, default=20, help='Number of independent runs')
    parser.add_argument('--max-iter', type=int, default=300, help='Maximum iterations per run')
    parser.add_argument('--procs', type=int, help='Number of parallel processes')
    parser.add_argument('--out-csv', help='Output CSV file')
    parser.add_argument('--out-plot', help='Output plot file')
    
    args = parser.parse_args()
    
    instance = TSPInstance(args.tsp_file)
    
    if args.out_csv is None:
        args.out_csv = f"pso_{instance.name}_results.csv"
    if args.out_plot is None:
        args.out_plot = f"pso_convergence_{instance.name}.png"
    
    print("=" * 60)
    print("Particle Swarm Optimization for TSP - FIXED VERSION")
    print("=" * 60)
    print(f"Instance: {instance.name.upper()} ({instance.n} nodes)")
    print(f"Runs: {args.runs}, Iterations: {args.max_iter}")
    print(f"Output CSV: {args.out_csv}")
    print(f"Output Plot: {args.out_plot}")
    print(f"Parameters: {PSO_PARAMS}")
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
        'algorithm': 'PSO',
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