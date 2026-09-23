"""Model analysis and digest generation."""

from typing import Any, Optional


# Open-weight model heuristics
OPEN_WEIGHT_FAMILIES = {
    "llama",
    "qwen",
    "deepseek",
    "mistral",
    "gemma",
    "phi",
    "gpt-oss",
    "glm",
    "yi",
    "command-r",
    "mixtral",
    "codellama",
    "openchat",
    "vicuna",
    "falcon",
    "mpt",
    "stablelm",
    "solar",
}

OPEN_WEIGHT_CREATORS = {
    "meta",
    "alibaba",
    "deepseek",
    "mistral ai",
    "google",
    "microsoft",
    "tsinghua",
    "01.ai",
    "databricks",
    "stability ai",
    "eleutherai",
    "together",
}


def normalize_model(model: dict[str, Any]) -> dict[str, Any]:
    """Normalize model data to consistent schema.
    
    Handles different field naming conventions in the API.
    """
    normalized = model.copy()
    
    # Normalize pricing fields
    if "pricing" in normalized:
        pricing = normalized["pricing"]
        # Handle both price_1m_input and price_1m_input_tokens
        if "price_1m_input_tokens" in pricing and "price_1m_input" not in pricing:
            pricing["price_1m_input"] = pricing["price_1m_input_tokens"]
        if "price_1m_output_tokens" in pricing and "price_1m_output" not in pricing:
            pricing["price_1m_output"] = pricing["price_1m_output_tokens"]
    
    # Normalize performance fields
    if "performance" in normalized:
        perf = normalized["performance"]
        # Ensure we have short field names
        if "median_output_tokens_per_second" not in perf and "output_tokens_per_second" in perf:
            perf["median_output_tokens_per_second"] = perf["output_tokens_per_second"]
        if "median_time_to_first_token_seconds" not in perf and "time_to_first_token_seconds" in perf:
            perf["median_time_to_first_token_seconds"] = perf["time_to_first_token_seconds"]
    
    return normalized


def is_open_weight(model: dict[str, Any]) -> bool:
    """Guess if model is open-weight based on name and creator.
    
    Free tier typically lacks explicit licensing fields.
    """
    name = model.get("name", "").lower()
    creator = model.get("model_creator", "").lower()
    
    # Check family patterns
    for family in OPEN_WEIGHT_FAMILIES:
        if family in name:
            return True
    
    # Check creator
    for creator_pattern in OPEN_WEIGHT_CREATORS:
        if creator_pattern in creator:
            # But exclude obvious proprietary patterns
            if any(prop in name for prop in ["gpt-4", "claude", "gemini-pro", "palm"]):
                continue
            return True
    
    return False


def get_intelligence_index(model: dict[str, Any]) -> Optional[float]:
    """Extract intelligence index from model."""
    evals = model.get("evaluations", {})
    return evals.get("artificial_analysis_intelligence_index")


def get_coding_index(model: dict[str, Any]) -> Optional[float]:
    """Extract coding index from model."""
    evals = model.get("evaluations", {})
    return evals.get("artificial_analysis_coding_index")


def get_agentic_index(model: dict[str, Any]) -> Optional[float]:
    """Extract agentic index from model."""
    evals = model.get("evaluations", {})
    return evals.get("artificial_analysis_agentic_index")


def get_cost_per_intel_task(model: dict[str, Any]) -> Optional[float]:
    """Extract cost per intelligence task."""
    cost = model.get("artificial_analysis_intelligence_index_cost", {})
    per_task = cost.get("cost_per_task", {})
    return per_task.get("total_cost")


def get_tokens_per_second(model: dict[str, Any]) -> Optional[float]:
    """Extract median output tokens per second."""
    perf = model.get("performance", {})
    return perf.get("median_output_tokens_per_second")


def get_time_to_first_token(model: dict[str, Any]) -> Optional[float]:
    """Extract median time to first token in seconds."""
    perf = model.get("performance", {})
    return perf.get("median_time_to_first_token_seconds")


def get_input_price(model: dict[str, Any]) -> Optional[float]:
    """Extract price per 1M input tokens in USD."""
    pricing = model.get("pricing", {})
    return pricing.get("price_1m_input") or pricing.get("price_1m_input_tokens")


def get_output_price(model: dict[str, Any]) -> Optional[float]:
    """Extract price per 1M output tokens in USD."""
    pricing = model.get("pricing", {})
    return pricing.get("price_1m_output") or pricing.get("price_1m_output_tokens")


def compute_smart_score(model: dict[str, Any]) -> Optional[float]:
    """Compute composite intelligence + speed score.
    
    Normalizes intelligence (0-100) and tokens/sec, then takes geometric mean.
    """
    intel = get_intelligence_index(model)
    tok_s = get_tokens_per_second(model)
    
    if intel is None or tok_s is None:
        return None
    
    # Normalize speed to 0-100 scale (assume max ~200 tok/s)
    speed_norm = min(tok_s / 2.0, 100.0)
    
    # Geometric mean
    return (intel * speed_norm) ** 0.5


def is_pareto_optimal(
    models: list[dict[str, Any]],
    x_key: str,
    y_key: str,
    x_higher_better: bool = True,
    y_higher_better: bool = True
) -> list[bool]:
    """Mark Pareto frontier for two metrics.
    
    Args:
        models: List of models
        x_key: Key for x-axis metric
        y_key: Key for y-axis metric
        x_higher_better: True if higher x is better
        y_higher_better: True if higher y is better
        
    Returns:
        List of bools indicating Pareto optimality
    """
    n = len(models)
    pareto = [True] * n
    
    for i in range(n):
        if pareto[i]:
            for j in range(n):
                if i == j or not pareto[j]:
                    continue
                
                # Check if j dominates i
                x_i = models[i].get(x_key)
                x_j = models[j].get(x_key)
                y_i = models[i].get(y_key)
                y_j = models[j].get(y_key)
                
                if x_i is None or x_j is None or y_i is None or y_j is None:
                    continue
                
                # j dominates i if j is >= i on both metrics (with proper direction)
                x_dom = (x_j >= x_i) if x_higher_better else (x_j <= x_i)
                y_dom = (y_j >= y_i) if y_higher_better else (y_j <= y_i)
                x_better = (x_j > x_i) if x_higher_better else (x_j < x_i)
                y_better = (y_j > y_i) if y_higher_better else (y_j < y_i)
                
                if x_dom and y_dom and (x_better or y_better):
                    pareto[i] = False
                    break
    
    return pareto


def filter_models(
    models: list[dict[str, Any]],
    creator: Optional[str] = None,
    min_intelligence: Optional[float] = None,
    open_only: bool = False
) -> list[dict[str, Any]]:
    """Filter models by criteria."""
    filtered = []
    
    for model in models:
        # Normalize first
        model = normalize_model(model)
        
        # Creator filter
        if creator:
            model_creator = model.get("model_creator", "")
            if creator.lower() not in model_creator.lower():
                continue
        
        # Intelligence filter
        if min_intelligence is not None:
            intel = get_intelligence_index(model)
            if intel is None or intel < min_intelligence:
                continue
        
        # Open-weight filter
        if open_only and not is_open_weight(model):
            continue
        
        filtered.append(model)
    
    return filtered


def rank_by_intelligence(models: list[dict[str, Any]], limit: Optional[int] = None) -> list[dict[str, Any]]:
    """Rank models by intelligence index."""
    ranked = sorted(
        [m for m in models if get_intelligence_index(m) is not None],
        key=lambda m: get_intelligence_index(m),
        reverse=True
    )
    return ranked[:limit] if limit else ranked


def rank_by_smart_fast(models: list[dict[str, Any]], limit: Optional[int] = None) -> list[dict[str, Any]]:
    """Rank models by composite intelligence + speed score."""
    # Compute scores
    scored = []
    for model in models:
        score = compute_smart_score(model)
        if score is not None:
            scored.append((model, score))
    
    # Sort by score
    scored.sort(key=lambda x: x[1], reverse=True)
    ranked = [m for m, _ in scored]
    
    # Mark Pareto frontier
    if ranked:
        pareto = is_pareto_optimal(
            ranked,
            "intelligence_index",
            "tokens_per_second",
            x_higher_better=True,
            y_higher_better=True
        )
        for i, model in enumerate(ranked):
            model["_pareto_intel_speed"] = pareto[i]
    
    return ranked[:limit] if limit else ranked


def rank_by_smart_cheap(models: list[dict[str, Any]], limit: Optional[int] = None) -> list[dict[str, Any]]:
    """Rank models by cost efficiency (prefer low cost per intelligence task)."""
    # Prefer cost_per_intel_task if available
    with_cost = []
    for model in models:
        cost = get_cost_per_intel_task(model)
        intel = get_intelligence_index(model)
        
        if cost is not None and intel is not None:
            with_cost.append((model, cost))
        elif intel is not None:
            # Fallback: use blended $/MTok if cost_per_task missing
            in_price = get_input_price(model)
            out_price = get_output_price(model)
            if in_price is not None and out_price is not None:
                # Use simple average as proxy
                blended = (in_price + out_price) / 2.0
                # Normalize by intelligence (lower is better)
                if intel > 0:
                    efficiency = blended / intel
                    with_cost.append((model, efficiency))
    
    # Sort by cost (ascending)
    with_cost.sort(key=lambda x: x[1])
    ranked = [m for m, _ in with_cost]
    
    return ranked[:limit] if limit else ranked


def rank_by_coding(models: list[dict[str, Any]], limit: Optional[int] = None) -> list[dict[str, Any]]:
    """Rank models by coding capability."""
    # Prefer coding_index when present
    with_coding = []
    for model in models:
        coding = get_coding_index(model)
        if coding is not None:
            with_coding.append((model, coding))
        else:
            # Fallback: use intelligence for coding-ish names
            name = model.get("name", "").lower()
            if any(kw in name for kw in ["code", "coder", "codestral", "deepseek"]):
                intel = get_intelligence_index(model)
                if intel is not None:
                    with_coding.append((model, intel))
    
    # Sort by score (descending)
    with_coding.sort(key=lambda x: x[1], reverse=True)
    ranked = [m for m, _ in with_coding]
    
    return ranked[:limit] if limit else ranked


def get_open_digest(models: list[dict[str, Any]], limit: Optional[int] = None) -> dict[str, Any]:
    """Generate open-weight digest with comparison to proprietary."""
    # Mark all models
    for model in models:
        model["_open_guess"] = is_open_weight(model)
    
    # Get top open models
    open_models = [m for m in models if m["_open_guess"]]
    open_ranked = rank_by_intelligence(open_models, limit=limit)
    
    # Get top proprietary for comparison
    proprietary = [m for m in models if not m["_open_guess"]]
    proprietary_ranked = rank_by_intelligence(proprietary, limit=5)
    
    # Calculate gap
    top_open_intel = get_intelligence_index(open_ranked[0]) if open_ranked else None
    top_prop_intel = get_intelligence_index(proprietary_ranked[0]) if proprietary_ranked else None
    gap = None
    if top_open_intel is not None and top_prop_intel is not None:
        gap = top_prop_intel - top_open_intel
    
    return {
        "open_models": open_ranked,
        "proprietary_comparison": proprietary_ranked,
        "intelligence_gap": gap
    }


def pick_recommendation(models: list[dict[str, Any]], category: str) -> dict[str, Any]:
    """Pick one clear recommendation with runners-up.
    
    Args:
        models: List of models
        category: "local", "cheap-api", "frontier", or "coding-agent"
        
    Returns:
        Dict with recommendation and runners_up
    """
    if category == "local":
        # Prefer open-weight, good intelligence, can run on consumer hardware
        candidates = [m for m in models if is_open_weight(m)]
        ranked = rank_by_intelligence(candidates, limit=5)
    
    elif category == "cheap-api":
        # Lowest cost per intelligence
        ranked = rank_by_smart_cheap(models, limit=5)
    
    elif category == "frontier":
        # Highest intelligence
        ranked = rank_by_intelligence(models, limit=5)
    
    elif category == "coding-agent":
        # Best for coding tasks
        ranked = rank_by_coding(models, limit=5)
    
    else:
        raise ValueError(f"Unknown category: {category}")
    
    return {
        "category": category,
        "recommendation": ranked[0] if ranked else None,
        "runners_up": ranked[1:5] if len(ranked) > 1 else []
    }
