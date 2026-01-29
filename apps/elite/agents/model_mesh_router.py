"""
The Model Mesh Router: Dynamic Multi-Dimensional Model Selection

This implements intelligent model routing based on:
- Cost efficiency (tokens/dollar)
- Latency (response time)
- Quality (capability match, benchmarks)
- Privacy (data residency, on-premise)

Design Principles:
- Multi-Dimensional Scoring: Weighted combination of factors
- Adaptive: Can learn from outcomes (future)
- Fallback: Graceful degradation on failures
- Transparent: Scoring is auditable
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class ModelInfo:
    """
    Metadata about an available model.
    
    This catalog drives routing decisions.
    """
    name: str                          # e.g., "gpt-4-turbo", "claude-3-opus"
    provider: str                      # e.g., "openai", "anthropic", "azure"
    
    # Cost factors
    cost_per_1k_input_tokens: float    # USD per 1K input tokens
    cost_per_1k_output_tokens: float   # USD per 1K output tokens
    
    # Performance factors
    avg_latency_ms: float              # Average response latency
    max_tokens: int                    # Context window size
    
    # Quality factors
    capability_tags: List[str]         # e.g., ["coding", "reasoning", "multimodal"]
    benchmark_scores: Dict[str, float] # e.g., {"mmlu": 0.89, "humaneval": 0.85}
    
    # Privacy factors
    on_premise: bool                   # Can run locally/air-gapped
    data_residency: str                # e.g., "us", "eu", "china", "global"
    privacy_rating: float              # 0.0 (public cloud) to 1.0 (local-only)
    
    # Availability
    available: bool = True             # Currently available
    rate_limit_rpm: Optional[int] = None  # Requests per minute


@dataclass
class TaskMetadata:
    """
    Metadata about a task used for routing.
    
    Extracted from SwarmTask for routing decisions.
    """
    agent_type: str                    # Specialist type
    task_type: str                     # More specific categorization
    estimated_input_tokens: int
    estimated_output_tokens: int
    priority: str                      # "low", "medium", "high", "critical"
    privacy_requirement: str           # "public", "confidential", "restricted"
    latency_sensitivity: str           # "batch", "interactive", "realtime"


class ModelMeshRouter:
    """
    The Model Mesh Router: Intelligent Model Selection
    
    Core Algorithm:
    1. Filter models by hard constraints (availability, capability)
    2. Score remaining models on multiple dimensions
    3. Select highest-scoring model
    4. Fallback if score below threshold
    
    Scoring Dimensions:
    - Cost: Lower is better (normalized)
    - Latency: Lower is better (normalized)
    - Quality: Higher is better (embedding similarity + benchmarks)
    - Privacy: Higher is better (based on requirements)
    
    Future Enhancements:
    - Learn from outcomes (fine-tune weights)
    - Auto-discover new models
    - Agentic negotiation for complex decisions
    """

    def __init__(
        self,
        model_catalog: List[ModelInfo],
        default_weights: Optional[Dict[str, float]] = None,
        min_score_threshold: float = 0.5
    ):
        """
        Initialize the router with a model catalog.
        
        Args:
            model_catalog: List of available models
            default_weights: Default scoring weights
            min_score_threshold: Minimum score to accept (else trigger fallback)
        """
        self.catalog = model_catalog
        self.min_score_threshold = min_score_threshold
        
        # Default weights: cost, latency, quality, privacy
        self.default_weights = default_weights or {
            "cost": 0.3,
            "latency": 0.3,
            "quality": 0.3,
            "privacy": 0.1
        }
        
        # Precompute normalization ranges for scoring
        self._compute_normalization_ranges()
    
    def select_model(self, task: Any) -> str:
        """
        Select the optimal model for a task.
        
        This is the main entry point called by the scheduler.
        
        Args:
            task: SwarmTask (must have agent_type and payload)
            
        Returns:
            The name of the selected model
        """
        # Extract task metadata
        metadata = self._extract_task_metadata(task)
        
        # Get adaptive weights based on task requirements
        weights = self._get_adaptive_weights(metadata)
        
        # Filter models by hard constraints
        candidates = self._filter_candidates(metadata)
        
        if not candidates:
            # No models meet constraints - return fallback
            return self._get_fallback_model()
        
        # Score each candidate
        scored_models = []
        for model in candidates:
            score = self._score_model(model, metadata, weights)
            scored_models.append((model, score))
        
        # Sort by score (descending)
        scored_models.sort(key=lambda x: x[1], reverse=True)
        
        best_model, best_score = scored_models[0]
        
        # Check if score meets threshold
        if best_score < self.min_score_threshold:
            # Score too low - may trigger agentic negotiation (future)
            # For now, return best available or fallback
            if best_score > 0:
                return best_model.name
            else:
                return self._get_fallback_model()
        
        return best_model.name
    
    def _extract_task_metadata(self, task: Any) -> TaskMetadata:
        """
        Extract routing metadata from a SwarmTask.
        
        Args:
            task: SwarmTask object
            
        Returns:
            TaskMetadata for routing
        """
        payload = task.payload if isinstance(task.payload, dict) else {}
        
        # Estimate token counts (rough heuristic)
        input_text = str(payload.get("instruction", "") + payload.get("query", ""))
        estimated_input = max(100, len(input_text) // 4)  # ~4 chars per token
        estimated_output = payload.get("max_tokens", 1000)
        
        return TaskMetadata(
            agent_type=task.agent_type,
            task_type=payload.get("task_type", task.agent_type),
            estimated_input_tokens=estimated_input,
            estimated_output_tokens=estimated_output,
            priority=payload.get("priority", "medium"),
            privacy_requirement=payload.get("privacy", "public"),
            latency_sensitivity=payload.get("latency", "interactive")
        )
    
    def _get_adaptive_weights(self, metadata: TaskMetadata) -> Dict[str, float]:
        """
        Adjust scoring weights based on task requirements.
        
        Examples:
        - High privacy requirement: boost privacy weight
        - Critical priority: boost latency weight
        - Batch processing: boost cost weight
        
        Args:
            metadata: Task metadata
            
        Returns:
            Adjusted weights dict
        """
        weights = self.default_weights.copy()
        
        # Privacy boost
        if metadata.privacy_requirement in ["confidential", "restricted"]:
            weights["privacy"] = 0.4
            weights["cost"] = 0.2
            weights["latency"] = 0.2
            weights["quality"] = 0.2
        
        # Latency boost
        if metadata.latency_sensitivity == "realtime":
            weights["latency"] = 0.5
            weights["cost"] = 0.1
            weights["quality"] = 0.3
            weights["privacy"] = 0.1
        
        # Cost boost
        if metadata.priority == "low" or metadata.latency_sensitivity == "batch":
            weights["cost"] = 0.5
            weights["latency"] = 0.1
            weights["quality"] = 0.3
            weights["privacy"] = 0.1
        
        # Normalize to sum to 1.0
        total = sum(weights.values())
        return {k: v / total for k, v in weights.items()}
    
    def _filter_candidates(self, metadata: TaskMetadata) -> List[ModelInfo]:
        """
        Filter models by hard constraints.
        
        Constraints:
        - Model must be available
        - Must have required capabilities
        - Must meet privacy requirements
        - Must have sufficient context window
        
        Args:
            metadata: Task metadata
            
        Returns:
            List of candidate models
        """
        candidates = []
        
        for model in self.catalog:
            # Must be available
            if not model.available:
                continue
            
            # Must have capability for this agent type
            if metadata.agent_type not in model.capability_tags:
                continue
            
            # Privacy constraint
            if metadata.privacy_requirement == "restricted" and not model.on_premise:
                continue
            
            # Context window constraint
            total_tokens = metadata.estimated_input_tokens + metadata.estimated_output_tokens
            if model.max_tokens < total_tokens:
                continue
            
            candidates.append(model)
        
        return candidates
    
    def _score_model(
        self,
        model: ModelInfo,
        metadata: TaskMetadata,
        weights: Dict[str, float]
    ) -> float:
        """
        Compute multi-dimensional score for a model.
        
        Each dimension is normalized to [0, 1] where higher is better.
        
        Args:
            model: The model to score
            metadata: Task metadata
            weights: Scoring weights
            
        Returns:
            Overall score (0.0 to 1.0)
        """
        # 1. Cost score (lower cost = higher score)
        cost = self._estimate_cost(model, metadata)
        cost_score = 1.0 - self._normalize(
            cost,
            self.norm_ranges["cost"]["min"],
            self.norm_ranges["cost"]["max"]
        )
        
        # 2. Latency score (lower latency = higher score)
        latency_score = 1.0 - self._normalize(
            model.avg_latency_ms,
            self.norm_ranges["latency"]["min"],
            self.norm_ranges["latency"]["max"]
        )
        
        # 3. Quality score (higher quality = higher score)
        quality_score = self._compute_quality_score(model, metadata)
        
        # 4. Privacy score
        privacy_score = model.privacy_rating
        
        # Weighted combination
        total_score = (
            weights["cost"] * cost_score +
            weights["latency"] * latency_score +
            weights["quality"] * quality_score +
            weights["privacy"] * privacy_score
        )
        
        return max(0.0, min(1.0, total_score))  # Clamp to [0, 1]
    
    def _estimate_cost(self, model: ModelInfo, metadata: TaskMetadata) -> float:
        """
        Estimate total cost for this task on this model.
        
        Args:
            model: The model
            metadata: Task metadata
            
        Returns:
            Estimated cost in USD
        """
        input_cost = (metadata.estimated_input_tokens / 1000) * model.cost_per_1k_input_tokens
        output_cost = (metadata.estimated_output_tokens / 1000) * model.cost_per_1k_output_tokens
        return input_cost + output_cost
    
    def _compute_quality_score(self, model: ModelInfo, metadata: TaskMetadata) -> float:
        """
        Compute quality score based on benchmarks and capabilities.
        
        Future: Use embedding similarity between task and model capabilities.
        
        Args:
            model: The model
            metadata: Task metadata
            
        Returns:
            Quality score (0.0 to 1.0)
        """
        # Simple heuristic: average relevant benchmark scores
        relevant_benchmarks = []
        
        if metadata.agent_type == "coder":
            relevant_benchmarks = ["humaneval", "mbpp"]
        elif metadata.agent_type == "researcher":
            relevant_benchmarks = ["mmlu", "drop"]
        elif metadata.agent_type == "critic":
            relevant_benchmarks = ["mmlu", "truthfulqa"]
        else:
            relevant_benchmarks = ["mmlu"]  # General fallback
        
        scores = [
            model.benchmark_scores.get(bench, 0.5)
            for bench in relevant_benchmarks
        ]
        
        if scores:
            return sum(scores) / len(scores)
        else:
            return 0.5  # Default to median
    
    def _normalize(self, value: float, min_val: float, max_val: float) -> float:
        """
        Normalize a value to [0, 1] range.
        
        Args:
            value: The value to normalize
            min_val: Minimum value in range
            max_val: Maximum value in range
            
        Returns:
            Normalized value (0.0 to 1.0)
        """
        if max_val == min_val:
            return 0.5
        
        normalized = (value - min_val) / (max_val - min_val)
        return max(0.0, min(1.0, normalized))
    
    def _compute_normalization_ranges(self) -> None:
        """
        Precompute min/max ranges for normalization.
        
        This is called once during initialization.
        """
        if not self.catalog:
            self.norm_ranges = {
                "cost": {"min": 0.0, "max": 1.0},
                "latency": {"min": 0.0, "max": 1000.0}
            }
            return
        
        # Compute cost range (estimate for median task)
        median_task_tokens = 2000  # 1K input + 1K output
        costs = []
        for model in self.catalog:
            cost = (1 * model.cost_per_1k_input_tokens + 1 * model.cost_per_1k_output_tokens)
            costs.append(cost)
        
        # Compute latency range
        latencies = [m.avg_latency_ms for m in self.catalog]
        
        self.norm_ranges = {
            "cost": {"min": min(costs), "max": max(costs)},
            "latency": {"min": min(latencies), "max": max(latencies)}
        }
    
    def _get_fallback_model(self) -> str:
        """
        Get fallback model when routing fails.
        
        Returns:
            Name of fallback model
        """
        # Find cheapest available model
        available = [m for m in self.catalog if m.available]
        if available:
            cheapest = min(
                available,
                key=lambda m: m.cost_per_1k_input_tokens + m.cost_per_1k_output_tokens
            )
            return cheapest.name
        
        return "default-model"  # Ultimate fallback


# --- Example Model Catalog ---

def create_example_catalog() -> List[ModelInfo]:
    """
    Create an example model catalog for demonstration.
    
    Returns:
        List of ModelInfo objects
    """
    return [
        ModelInfo(
            name="gpt-4-turbo",
            provider="openai",
            cost_per_1k_input_tokens=0.01,
            cost_per_1k_output_tokens=0.03,
            avg_latency_ms=2000,
            max_tokens=128000,
            capability_tags=["coder", "researcher", "critic", "planner"],
            benchmark_scores={"mmlu": 0.86, "humaneval": 0.67},
            on_premise=False,
            data_residency="us",
            privacy_rating=0.3,
            available=True,
            rate_limit_rpm=500
        ),
        ModelInfo(
            name="claude-3-opus",
            provider="anthropic",
            cost_per_1k_input_tokens=0.015,
            cost_per_1k_output_tokens=0.075,
            avg_latency_ms=3000,
            max_tokens=200000,
            capability_tags=["coder", "researcher", "critic", "planner"],
            benchmark_scores={"mmlu": 0.89, "humaneval": 0.84},
            on_premise=False,
            data_residency="us",
            privacy_rating=0.3,
            available=True,
            rate_limit_rpm=400
        ),
        ModelInfo(
            name="gemini-pro-1.5",
            provider="google",
            cost_per_1k_input_tokens=0.0025,
            cost_per_1k_output_tokens=0.0075,
            avg_latency_ms=1500,
            max_tokens=1000000,
            capability_tags=["researcher", "critic", "planner"],
            benchmark_scores={"mmlu": 0.81, "drop": 0.82},
            on_premise=False,
            data_residency="global",
            privacy_rating=0.2,
            available=True,
            rate_limit_rpm=1000
        ),
        ModelInfo(
            name="llama-3-70b-local",
            provider="meta",
            cost_per_1k_input_tokens=0.0,  # Free if self-hosted
            cost_per_1k_output_tokens=0.0,
            avg_latency_ms=5000,
            max_tokens=8192,
            capability_tags=["coder", "researcher"],
            benchmark_scores={"mmlu": 0.79, "humaneval": 0.62},
            on_premise=True,
            data_residency="local",
            privacy_rating=1.0,
            available=True,
            rate_limit_rpm=None
        ),
    ]


# --- Usage Example ---

if __name__ == "__main__":
    from collections import namedtuple
    
    # Create router with example catalog
    catalog = create_example_catalog()
    router = ModelMeshRouter(catalog)
    
    # Create mock task
    MockTask = namedtuple('MockTask', ['agent_type', 'payload'])
    
    # Test 1: Cost-sensitive research task
    task1 = MockTask(
        agent_type='researcher',
        payload={
            "query": "What is quantum computing?",
            "priority": "low",
            "latency": "batch"
        }
    )
    
    selected = router.select_model(task1)
    print(f"Cost-sensitive research task: {selected}")
    
    # Test 2: High-privacy coding task
    task2 = MockTask(
        agent_type='coder',
        payload={
            "instruction": "Implement encryption algorithm",
            "privacy": "restricted",
            "requires_llm": True
        }
    )
    
    selected = router.select_model(task2)
    print(f"High-privacy coding task: {selected}")
    
    # Test 3: Realtime critical task
    task3 = MockTask(
        agent_type='critic',
        payload={
            "artifact": "security code",
            "priority": "critical",
            "latency": "realtime"
        }
    )
    
    selected = router.select_model(task3)
    print(f"Realtime critical task: {selected}")
