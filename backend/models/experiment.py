from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class OptimizationExperiment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    algorithm: str
    dataset_name: str
    population_size: int
    iterations: int
    random_seed: int
    best_fitness: float
    runtime_seconds: float
    
    # Serialized JSON strings
    parameters_json: str          # Dict of best parameters
    metrics_json: str             # Dict of evaluated metrics
    bounds_json: str              # Parameter search bounds
    weights_json: str             # Objective weights
    convergence_history_json: str # List of generation points
    diversity_history_json: str   # List of diversity points
    pareto_front_json: Optional[str] = None # List of Pareto front solutions (for NSGA-II)
    statistical_summary_json: Optional[str] = None # Summary if multi-run
    notes: Optional[str] = None
