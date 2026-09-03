import os
import sys
import json
import time
import csv
import numpy as np

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from optimization.search_space import SearchSpace
from optimization.constraints import ConstraintHandler
from optimization.fitness import FitnessEvaluator, FitnessWeights
from optimization.evaluation import RetrievalEvaluator, DEFAULT_BENCHMARK_DOCUMENT
from optimization.baseline import BaselineOptimizer
from optimization.ga import GeneticAlgorithmOptimizer
from optimization.pso import ParticleSwarmOptimizer
from optimization.gwo import GreyWolfOptimizer
from optimization.nsga2 import NSGA2Optimizer
from optimization.hybrid_ga_pso import HybridGAPSOOptimizer
from optimization.experiment_runner import ExperimentRunner
from optimization.sensitivity import SensitivityAnalyzer
from optimization.ablation import AblationStudyRunner

print("==========================================================")
print("STARTING FULL EXPERIMENTAL CAMPAIGN FOR M.TECH RESEARCH PAPER")
print("==========================================================")

# 1. Initialize evaluation system
weights = FitnessWeights(w_retrieval=0.35, w_semantic=0.25, w_coverage=0.15, w_latency=0.15, w_tokens=0.10)
weights.normalize()
space = SearchSpace()
constraints = ConstraintHandler(space)
evaluator = RetrievalEvaluator(document_text=DEFAULT_BENCHMARK_DOCUMENT)
fitness = FitnessEvaluator(weights)

experiment_results = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    "dataset": {
        "name": "Academic Deep Learning Benchmark Corpus",
        "total_characters": len(DEFAULT_BENCHMARK_DOCUMENT),
        "total_words": len(DEFAULT_BENCHMARK_DOCUMENT.split()),
        "benchmark_queries_count": len(evaluator.queries),
        "benchmark_queries": evaluator.queries
    },
    "fitness_weights": weights.to_dict(),
    "algorithms": {}
}

# 2. Experiment 1: Baseline
print("\n--- 1. Running Baseline Evaluation ---")
baseline_opt = BaselineOptimizer(space, constraints, evaluator, fitness, random_seed=42)
res_baseline = baseline_opt.optimize()
experiment_results["algorithms"]["baseline"] = res_baseline.to_dict()
print(f"Baseline -> Fitness: {res_baseline.best_fitness:.4f}, Quality: {res_baseline.metrics['retrieval_quality']:.4f}, Latency: {res_baseline.metrics['latency_ms']}ms, Tokens: {res_baseline.metrics['estimated_tokens']}")

# 3. Experiment 2: Genetic Algorithm
print("\n--- 2. Running Genetic Algorithm (GA) ---")
ga_opt = GeneticAlgorithmOptimizer(space, constraints, evaluator, fitness, random_seed=42)
res_ga = ga_opt.optimize(population_size=12, iterations=8, crossover_prob=0.85, mutation_prob=0.20, elite_size=2)
experiment_results["algorithms"]["ga"] = res_ga.to_dict()
print(f"GA -> Fitness: {res_ga.best_fitness:.4f}, Quality: {res_ga.metrics['retrieval_quality']:.4f}, Latency: {res_ga.metrics['latency_ms']}ms, Tokens: {res_ga.metrics['estimated_tokens']}")

# 4. Experiment 3: Particle Swarm Optimization (PSO)
print("\n--- 3. Running Particle Swarm Optimization (PSO) ---")
pso_opt = ParticleSwarmOptimizer(space, constraints, evaluator, fitness, random_seed=42)
res_pso = pso_opt.optimize(population_size=12, iterations=8, inertia_weight_max=0.90, inertia_weight_min=0.40, cognitive_coeff=1.70, social_coeff=1.70)
experiment_results["algorithms"]["pso"] = res_pso.to_dict()
print(f"PSO -> Fitness: {res_pso.best_fitness:.4f}, Quality: {res_pso.metrics['retrieval_quality']:.4f}, Latency: {res_pso.metrics['latency_ms']}ms, Tokens: {res_pso.metrics['estimated_tokens']}")

# 5. Experiment 4: Grey Wolf Optimizer (GWO)
print("\n--- 4. Running Grey Wolf Optimizer (GWO) ---")
gwo_opt = GreyWolfOptimizer(space, constraints, evaluator, fitness, random_seed=42)
res_gwo = gwo_opt.optimize(population_size=12, iterations=8)
experiment_results["algorithms"]["gwo"] = res_gwo.to_dict()
print(f"GWO -> Fitness: {res_gwo.best_fitness:.4f}, Quality: {res_gwo.metrics['retrieval_quality']:.4f}, Latency: {res_gwo.metrics['latency_ms']}ms, Tokens: {res_gwo.metrics['estimated_tokens']}")

# 6. Experiment 5: NSGA-II Multi-Objective
print("\n--- 5. Running NSGA-II Multi-Objective Optimization ---")
nsga_opt = NSGA2Optimizer(space, constraints, evaluator, fitness, random_seed=42)
res_nsga = nsga_opt.optimize(population_size=16, iterations=8, crossover_prob=0.85, mutation_prob=0.20)
experiment_results["algorithms"]["nsga2"] = res_nsga.to_dict()
print(f"NSGA-II -> Pareto Front size: {len(res_nsga.pareto_front)}, Best Quality: {res_nsga.best_fitness:.4f}, Latency: {res_nsga.metrics['latency_ms']}ms")

# 7. Experiment 6: Hybrid GA + PSO
print("\n--- 6. Running Hybrid GA + PSO ---")
hybrid_opt = HybridGAPSOOptimizer(space, constraints, evaluator, fitness, random_seed=42)
res_hybrid = hybrid_opt.optimize(population_size=12, iterations=8, ga_ratio=0.50, crossover_prob=0.85, mutation_prob=0.20)
experiment_results["algorithms"]["hybrid"] = res_hybrid.to_dict()
print(f"Hybrid -> Fitness: {res_hybrid.best_fitness:.4f}, Quality: {res_hybrid.metrics['retrieval_quality']:.4f}, Latency: {res_hybrid.metrics['latency_ms']}ms, Tokens: {res_hybrid.metrics['estimated_tokens']}")

# 8. Experiment 7: Parameter Sensitivity Sweeps
print("\n--- 7. Running Parameter Sensitivity Sweeps ---")
analyzer = SensitivityAnalyzer(evaluator, fitness)
sensitivity_res = analyzer.run_full_sensitivity()
experiment_results["sensitivity"] = sensitivity_res
print("Sensitivity sweeps completed (Top-K, Chunk Size, Similarity Cutoff).")

# 9. Experiment 8: 5-Stage Ablation Study
print("\n--- 8. Running 5-Stage Ablation Study ---")
ablation_runner = AblationStudyRunner(evaluator, fitness, iterations=6, population_size=10, random_seed=42)
ablation_res = ablation_runner.run_ablation()
experiment_results["ablation"] = ablation_res
for st in ablation_res:
    print(f"Ablation Stage {st['stage']}: {st['name']} -> Fitness: {st['fitness']:.4f}, Quality: {st['quality']:.4f}")

# 10. Experiment 9: Multi-Run Statistical Analysis (N=5 independent runs per algorithm)
print("\n--- 9. Running Multi-Run Statistical Analysis (5 Independent Runs per Algorithm) ---")
seeds = [42, 59, 76, 93, 110]
runner = ExperimentRunner(evaluator=evaluator, weights=weights)

statistical_experiments = {}
for algo_name in ["ga", "pso", "gwo", "hybrid"]:
    print(f"Executing 5 runs for {algo_name.upper()}...")
    stat_res = runner.run_multi_statistical(
        algorithm_name=algo_name,
        num_runs=5,
        population_size=12,
        iterations=8,
        base_seed=42
    )
    statistical_experiments[algo_name] = stat_res
    print(f"{algo_name.upper()} Stats -> Fitness: Mean={stat_res['fitness']['mean']} (std={stat_res['fitness']['std']}), Quality: Mean={stat_res['retrieval_quality']['mean']}")

experiment_results["statistical_analysis"] = statistical_experiments

# Save master experiment results to JSON
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "paper_experiment_results.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(experiment_results, f, indent=2)

print(f"\n==========================================================")
print(f"ALL EXPERIMENTS COMPLETED SUCCESSFULLY! Results saved to: {out_path}")
print(f"==========================================================")
