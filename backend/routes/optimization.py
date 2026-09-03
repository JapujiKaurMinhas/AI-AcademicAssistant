import os
import json
import csv
import io
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlmodel import Session, select

from database.db import get_session
from models.experiment import OptimizationExperiment
from models.processed_document import ProcessedDocument
from services.document_service import extract_text_from_pdf
from optimization.search_space import SearchSpace
from optimization.fitness import FitnessWeights
from optimization.evaluation import RetrievalEvaluator, DEFAULT_BENCHMARK_DOCUMENT
from optimization.experiment_runner import ExperimentRunner, ALGORITHM_MAP
from optimization.sensitivity import SensitivityAnalyzer
from optimization.ablation import AblationStudyRunner
from optimization.active_config import get_active_config, set_active_config, reset_to_default, RetrievalConfig

router = APIRouter(prefix="/api/optimization", tags=["Optimization"])

# Request / Response Schemas
class OptimizationRunRequest(BaseModel):
    algorithm: str = "ga"                       # "baseline", "ga", "pso", "gwo", "nsga2", "hybrid"
    population_size: int = 12
    iterations: int = 8
    random_seed: int = 42
    dataset_name: Optional[str] = "Benchmark Document"
    document_filename: Optional[str] = None
    custom_bounds: Optional[Dict[str, Any]] = None
    weights: Optional[Dict[str, float]] = None
    algo_params: Optional[Dict[str, Any]] = None # e.g. crossover_prob, inertia_weight, etc.

class MultiRunRequest(BaseModel):
    algorithm: str = "ga"
    num_runs: int = 3
    population_size: int = 10
    iterations: int = 6
    random_seed: int = 42
    document_filename: Optional[str] = None
    weights: Optional[Dict[str, float]] = None

class SensitivityRequest(BaseModel):
    document_filename: Optional[str] = None

class AblationRequest(BaseModel):
    document_filename: Optional[str] = None
    population_size: int = 10
    iterations: int = 6
    random_seed: int = 42

class SetActiveConfigRequest(BaseModel):
    chunk_size: int
    chunk_overlap: int
    top_k: int
    similarity_threshold: float
    context_token_budget: int
    mode: str = "optimized"
    algorithm_source: Optional[str] = "Optimized Experiment"


class Tuple_Text_DocName:
    def __init__(self, text: str, name: str):
        self.text = text
        self.name = name

def load_text_for_eval(filename: Optional[str], session: Session) -> Tuple_Text_DocName:
    if filename:
        # Look in DB first
        doc = session.exec(select(ProcessedDocument).where(ProcessedDocument.filename == filename)).first()
        if doc and doc.extracted_text and len(doc.extracted_text.strip()) > 50:
            return Tuple_Text_DocName(doc.extracted_text, filename)
        
        # Look in uploads folder
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
        path = os.path.join(upload_dir, filename)
        if os.path.exists(path):
            with open(path, "rb") as f:
                content = f.read()
            text = extract_text_from_pdf(content)
            if text and not text.startswith("Error"):
                return Tuple_Text_DocName(text, filename)

    # Check if there are any uploaded documents in DB
    first_doc = session.exec(select(ProcessedDocument)).first()
    if first_doc and first_doc.extracted_text and len(first_doc.extracted_text.strip()) > 50:
        return Tuple_Text_DocName(first_doc.extracted_text, first_doc.filename)

    # Fallback to rich academic benchmark document
    return Tuple_Text_DocName(DEFAULT_BENCHMARK_DOCUMENT, "Standard Academic Benchmark Paper")


@router.get("/search-space")
def get_search_space():
    """Returns the decision variables, bounds, defaults, and physical constraints."""
    space = SearchSpace()
    return {
        "decision_variables": space.get_specification(),
        "dimension": space.dimension,
        "constraints": [
            {"id": "C1", "rule": "chunk_overlap < chunk_size", "description": "Overlap must be strictly smaller than chunk size."},
            {"id": "C2", "rule": "chunk_overlap <= 0.5 * chunk_size", "description": "Overlap capped at 50% to prevent excessive redundancy."},
            {"id": "C3", "rule": "top_k >= 1", "description": "Must retrieve at least one passage."},
            {"id": "C4", "rule": "500 <= context_token_budget <= 6000", "description": "Context budget must remain within LLM context safety bounds."},
            {"id": "C5", "rule": "estimated_tokens <= context_token_budget", "description": "Total context injected into prompt cannot exceed budget."}
        ],
        "objective_function": {
            "single_objective": "Fitness(X) = w1*Relevance + w2*SemanticSim + w3*Coverage - w4*NormLatency - w5*NormTokens - Penalty",
            "multi_objective": ["Maximize Quality (Relevance + Semantic + Coverage)", "Minimize Latency (ms)", "Minimize Token Consumption"],
            "default_weights": FitnessWeights().to_dict()
        }
    }

@router.get("/algorithms")
def get_algorithms():
    """Lists all available metaheuristic optimization algorithms with metadata."""
    return {
        "algorithms": [
            {
                "id": "baseline",
                "name": "Baseline (Manual Default)",
                "family": "Deterministic / Empirical Control",
                "description": "Standard unoptimized retrieval parameters used by the default AI Academic Assistant.",
                "exploration_vs_exploitation": "None (Static point evaluation)",
                "tunable_params": []
            },
            {
                "id": "ga",
                "name": "Genetic Algorithm (GA)",
                "family": "Evolutionary",
                "description": "Mimics natural selection with chromosome crossover, Gaussian mutation, elitism, and diversity-adaptive mutation rates.",
                "exploration_vs_exploitation": "Crossover and mutation explore; tournament selection and elitism exploit.",
                "tunable_params": ["crossover_prob", "mutation_prob", "elite_size", "adaptive_mutation"]
            },
            {
                "id": "pso",
                "name": "Particle Swarm Optimization (PSO)",
                "family": "Swarm Intelligence",
                "description": "Simulates flocking behavior where particles fly through search space guided by personal best and global swarm best with decaying inertia.",
                "exploration_vs_exploitation": "High inertia explores broad regions; cognitive/social velocity pulls towards best.",
                "tunable_params": ["inertia_weight_max", "inertia_weight_min", "cognitive_coeff", "social_coeff", "adaptive_inertia"]
            },
            {
                "id": "gwo",
                "name": "Grey Wolf Optimizer (GWO)",
                "family": "Bio-Inspired Swarm",
                "description": "Simulates grey wolf hunting hierarchy (Alpha, Beta, Delta, Omega) with encircling mechanisms and linearly decaying parameter a.",
                "exploration_vs_exploitation": "|A| > 1 diverges pack for exploration; |A| < 1 converges for prey exploitation.",
                "tunable_params": []
            },
            {
                "id": "nsga2",
                "name": "NSGA-II (Multi-Objective)",
                "family": "Pareto Evolutionary",
                "description": "Finds a trade-off Pareto Front across Quality, Latency, and Tokens using fast non-dominated sorting and crowding distance.",
                "exploration_vs_exploitation": "Crowding distance promotes spread across front; non-dominated rank drives convergence.",
                "tunable_params": ["crossover_prob", "mutation_prob"]
            },
            {
                "id": "hybrid",
                "name": "Hybrid GA + PSO",
                "family": "Hybrid Metaheuristic",
                "description": "Combines GA's broad global search capabilities in Phase 1 with PSO's fast local exploitation and refinement in Phase 2.",
                "exploration_vs_exploitation": "Phase 1: GA exploration -> Transition -> Phase 2: PSO exploitation.",
                "tunable_params": ["ga_ratio", "crossover_prob", "mutation_prob", "cognitive_coeff", "social_coeff"]
            }
        ]
    }

@router.post("/run")
def run_optimization(req: OptimizationRunRequest, session: Session = Depends(get_session)):
    """Runs a single metaheuristic optimization experiment and saves the record to the database."""
    doc_info = load_text_for_eval(req.document_filename, session)
    
    weights = FitnessWeights(**(req.weights or {}))
    weights.normalize()
    evaluator = RetrievalEvaluator(document_text=doc_info.text)
    
    runner = ExperimentRunner(
        evaluator=evaluator,
        weights=weights,
        custom_bounds=req.custom_bounds
    )

    algo_kwargs = req.algo_params or {}
    
    result = runner.run_single(
        algorithm_name=req.algorithm,
        population_size=req.population_size,
        iterations=req.iterations,
        random_seed=req.random_seed,
        **algo_kwargs
    )

    # Save to SQLite Database
    experiment = OptimizationExperiment(
        algorithm=result.algorithm,
        dataset_name=doc_info.name,
        population_size=req.population_size,
        iterations=req.iterations,
        random_seed=req.random_seed,
        best_fitness=result.best_fitness,
        runtime_seconds=result.runtime_seconds,
        parameters_json=json.dumps(result.best_parameters),
        metrics_json=json.dumps(result.metrics),
        bounds_json=json.dumps(req.custom_bounds or {}),
        weights_json=json.dumps(weights.to_dict()),
        convergence_history_json=json.dumps(result.convergence_history),
        diversity_history_json=json.dumps(result.diversity_history),
        pareto_front_json=json.dumps(result.pareto_front) if result.pareto_front else None,
        notes=f"Premature convergence flag: {result.premature_convergence_detected}"
    )
    session.add(experiment)
    session.commit()
    session.refresh(experiment)

    res_dict = result.to_dict()
    res_dict["experiment_id"] = experiment.id
    res_dict["dataset_name"] = doc_info.name
    return res_dict

@router.post("/statistical")
def run_statistical_experiment(req: MultiRunRequest, session: Session = Depends(get_session)):
    """Executes multiple stochastic runs with distinct random seeds and calculates statistics."""
    doc_info = load_text_for_eval(req.document_filename, session)
    weights = FitnessWeights(**(req.weights or {}))
    weights.normalize()
    evaluator = RetrievalEvaluator(document_text=doc_info.text)

    runner = ExperimentRunner(evaluator=evaluator, weights=weights)
    stats = runner.run_multi_statistical(
        algorithm_name=req.algorithm,
        num_runs=req.num_runs,
        population_size=req.population_size,
        iterations=req.iterations,
        base_seed=req.random_seed
    )

    # Save best run to database with statistical summary
    best_run = stats["best_run"]
    experiment = OptimizationExperiment(
        algorithm=f"{stats['algorithm']} ({req.num_runs} Runs)",
        dataset_name=doc_info.name,
        population_size=req.population_size,
        iterations=req.iterations,
        random_seed=req.random_seed,
        best_fitness=best_run["best_fitness"],
        runtime_seconds=stats["runtime_seconds"]["total"],
        parameters_json=json.dumps(best_run["best_parameters"]),
        metrics_json=json.dumps(best_run["metrics"]),
        bounds_json=json.dumps({}),
        weights_json=json.dumps(weights.to_dict()),
        convergence_history_json=json.dumps(best_run["convergence_history"]),
        diversity_history_json=json.dumps(best_run["diversity_history"]),
        statistical_summary_json=json.dumps(stats),
        notes=f"Multi-run statistical evaluation across {req.num_runs} seeds."
    )
    session.add(experiment)
    session.commit()
    session.refresh(experiment)

    stats["experiment_id"] = experiment.id
    stats["dataset_name"] = doc_info.name
    return stats

@router.post("/compare")
def compare_all_algorithms(
    population_size: int = Query(12),
    iterations: int = Query(8),
    random_seed: int = Query(42),
    document_filename: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    """Executes a comparative benchmark across Baseline, GA, PSO, GWO, NSGA-II, and Hybrid."""
    doc_info = load_text_for_eval(document_filename, session)
    evaluator = RetrievalEvaluator(document_text=doc_info.text)
    runner = ExperimentRunner(evaluator=evaluator)
    
    comparison = runner.run_algorithm_comparison(
        population_size=population_size,
        iterations=iterations,
        random_seed=random_seed
    )
    return {
        "dataset_name": doc_info.name,
        "population_size": population_size,
        "iterations": iterations,
        "random_seed": random_seed,
        "results": comparison
    }

@router.post("/sensitivity")
def run_sensitivity(req: SensitivityRequest, session: Session = Depends(get_session)):
    """Executes empirical sensitivity analysis sweeps."""
    doc_info = load_text_for_eval(req.document_filename, session)
    evaluator = RetrievalEvaluator(document_text=doc_info.text)
    fitness = FitnessEvaluator()
    analyzer = SensitivityAnalyzer(evaluator, fitness)
    results = analyzer.run_full_sensitivity()
    results["dataset_name"] = doc_info.name
    return results

@router.post("/ablation")
def run_ablation(req: AblationRequest, session: Session = Depends(get_session)):
    """Executes a 5-stage ablation study."""
    doc_info = load_text_for_eval(req.document_filename, session)
    evaluator = RetrievalEvaluator(document_text=doc_info.text)
    fitness = FitnessEvaluator()
    ablation_runner = AblationStudyRunner(
        evaluator=evaluator,
        fitness_evaluator=fitness,
        iterations=req.iterations,
        population_size=req.population_size,
        random_seed=req.random_seed
    )
    stages = ablation_runner.run_ablation()
    return {
        "dataset_name": doc_info.name,
        "stages": stages
    }

@router.get("/active-config")
def get_current_retrieval_config():
    """Returns the current active retrieval configuration used by AI Academic Assistant QA."""
    cfg = get_active_config()
    return cfg.to_dict()

@router.post("/active-config")
def update_active_retrieval_config(req: SetActiveConfigRequest):
    """Updates the active retrieval parameters used across document retrieval and QA."""
    cfg = set_active_config(
        chunk_size=req.chunk_size,
        chunk_overlap=req.chunk_overlap,
        top_k=req.top_k,
        similarity_threshold=req.similarity_threshold,
        context_token_budget=req.context_token_budget,
        mode=req.mode,
        algorithm_source=req.algorithm_source or "Optimized Experiment"
    )
    return {
        "status": "success",
        "message": f"Active retrieval parameters updated to mode '{req.mode}' via {req.algorithm_source}.",
        "active_config": cfg.to_dict()
    }

@router.post("/active-config/reset")
def reset_retrieval_config():
    """Resets the active retrieval parameters back to manual default."""
    cfg = reset_to_default()
    return {
        "status": "success",
        "message": "Retrieval configuration reset to default.",
        "active_config": cfg.to_dict()
    }

@router.get("/experiments")
def list_experiments(session: Session = Depends(get_session)):
    """Lists all historical optimization experiments."""
    experiments = session.exec(select(OptimizationExperiment).order_by(OptimizationExperiment.created_at.desc())).all()
    results = []
    for exp in experiments:
        results.append({
            "id": exp.id,
            "created_at": exp.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "algorithm": exp.algorithm,
            "dataset_name": exp.dataset_name,
            "population_size": exp.population_size,
            "iterations": exp.iterations,
            "random_seed": exp.random_seed,
            "best_fitness": exp.best_fitness,
            "runtime_seconds": exp.runtime_seconds,
            "parameters": json.loads(exp.parameters_json),
            "metrics": json.loads(exp.metrics_json),
            "has_pareto": exp.pareto_front_json is not None,
            "has_stats": exp.statistical_summary_json is not None
        })
    return {"experiments": results}

@router.get("/experiments/{exp_id}")
def get_experiment_details(exp_id: int, session: Session = Depends(get_session)):
    """Retrieves full details, convergence curves, and Pareto fronts for a specific experiment."""
    exp = session.get(OptimizationExperiment, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")

    return {
        "id": exp.id,
        "created_at": exp.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "algorithm": exp.algorithm,
        "dataset_name": exp.dataset_name,
        "population_size": exp.population_size,
        "iterations": exp.iterations,
        "random_seed": exp.random_seed,
        "best_fitness": exp.best_fitness,
        "runtime_seconds": exp.runtime_seconds,
        "parameters": json.loads(exp.parameters_json),
        "metrics": json.loads(exp.metrics_json),
        "bounds": json.loads(exp.bounds_json) if exp.bounds_json else {},
        "weights": json.loads(exp.weights_json) if exp.weights_json else {},
        "convergence_history": json.loads(exp.convergence_history_json) if exp.convergence_history_json else [],
        "diversity_history": json.loads(exp.diversity_history_json) if exp.diversity_history_json else [],
        "pareto_front": json.loads(exp.pareto_front_json) if exp.pareto_front_json else None,
        "statistical_summary": json.loads(exp.statistical_summary_json) if exp.statistical_summary_json else None,
        "notes": exp.notes
    }

@router.delete("/experiments/{exp_id}")
def delete_experiment(exp_id: int, session: Session = Depends(get_session)):
    """Deletes an experiment record from the database."""
    exp = session.get(OptimizationExperiment, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")
    session.delete(exp)
    session.commit()
    return {"message": f"Experiment {exp_id} deleted successfully."}

@router.get("/export/{exp_id}")
def export_experiment(exp_id: int, format: str = Query("json"), session: Session = Depends(get_session)):
    """Exports experiment results as JSON or CSV format."""
    exp = session.get(OptimizationExperiment, exp_id)
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")

    exp_data = {
        "id": exp.id,
        "algorithm": exp.algorithm,
        "dataset": exp.dataset_name,
        "created_at": exp.created_at.isoformat(),
        "runtime_seconds": exp.runtime_seconds,
        "best_fitness": exp.best_fitness,
        "parameters": json.loads(exp.parameters_json),
        "metrics": json.loads(exp.metrics_json),
        "convergence_history": json.loads(exp.convergence_history_json) if exp.convergence_history_json else []
    }

    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Experiment ID", "Algorithm", "Dataset", "Best Fitness", "Runtime (s)", "Chunk Size", "Chunk Overlap", "Top K", "Threshold", "Token Budget", "Retrieval Quality", "Latency (ms)", "Tokens"])
        
        p = exp_data["parameters"]
        m = exp_data["metrics"]
        writer.writerow([
            exp.id,
            exp.algorithm,
            exp.dataset_name,
            exp.best_fitness,
            exp.runtime_seconds,
            p.get("chunk_size"),
            p.get("chunk_overlap"),
            p.get("top_k"),
            p.get("similarity_threshold"),
            p.get("context_token_budget"),
            m.get("retrieval_quality"),
            m.get("latency_ms"),
            m.get("estimated_tokens")
        ])
        
        # Add convergence history table in CSV
        writer.writerow([])
        writer.writerow(["Iteration", "Best Fitness", "Mean Fitness", "Diversity", "Exploration Rate", "Elapsed ms"])
        for pt in exp_data["convergence_history"]:
            writer.writerow([
                pt.get("iteration"),
                pt.get("best_fitness"),
                pt.get("mean_fitness"),
                pt.get("diversity"),
                pt.get("exploration_rate"),
                pt.get("elapsed_time_ms")
            ])

        response = Response(content=output.getvalue(), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename=experiment_{exp_id}_{exp.algorithm.replace(' ', '_')}.csv"
        return response

    # Default: JSON format
    response = Response(content=json.dumps(exp_data, indent=2), media_type="application/json")
    response.headers["Content-Disposition"] = f"attachment; filename=experiment_{exp_id}_{exp.algorithm.replace(' ', '_')}.json"
    return response
