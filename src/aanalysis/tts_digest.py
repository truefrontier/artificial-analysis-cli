"""TTS model analysis and digest generation."""

from typing import Any, Optional


def normalize_tts_model(model: dict[str, Any]) -> dict[str, Any]:
    """Normalize TTS model data to consistent schema.
    
    Handles model_creator object extraction and field variations.
    """
    normalized = model.copy()
    
    # Extract creator name from object if needed
    if "model_creator" in normalized and isinstance(normalized["model_creator"], dict):
        normalized["model_creator_name"] = normalized["model_creator"].get("name", "")
    else:
        normalized["model_creator_name"] = normalized.get("model_creator", "")
    
    # Normalize CI field names (ci95 vs ci_95)
    if "ci_95" in normalized and "ci95" not in normalized:
        normalized["ci95"] = normalized["ci_95"]
    
    return normalized


def get_elo(model: dict[str, Any]) -> Optional[float]:
    """Extract Elo rating from TTS model."""
    return model.get("elo")


def get_ci95(model: dict[str, Any]) -> Optional[float]:
    """Extract 95% confidence interval from TTS model."""
    return model.get("ci95") or model.get("ci_95")


def get_rank(model: dict[str, Any]) -> Optional[int]:
    """Extract rank from TTS model."""
    return model.get("rank")


def get_price_per_1m_chars(model: dict[str, Any]) -> Optional[float]:
    """Extract price per 1M characters from TTS model (Pro tier)."""
    return model.get("price_per_1m_characters")


def get_chars_per_second(model: dict[str, Any]) -> Optional[float]:
    """Extract characters per second speed from TTS model (Pro tier)."""
    return model.get("chars_per_second")


def filter_tts_models(
    models: list[dict[str, Any]],
    creator: Optional[str] = None,
    min_elo: Optional[float] = None
) -> list[dict[str, Any]]:
    """Filter TTS models by criteria."""
    filtered = []
    
    for model in models:
        # Normalize first
        model = normalize_tts_model(model)
        
        # Creator filter
        if creator:
            model_creator_name = model.get("model_creator_name", "")
            if creator.lower() not in model_creator_name.lower():
                continue
        
        # Elo filter
        if min_elo is not None:
            elo = get_elo(model)
            if elo is None or elo < min_elo:
                continue
        
        filtered.append(model)
    
    return filtered


def rank_by_elo(models: list[dict[str, Any]], limit: Optional[int] = None) -> list[dict[str, Any]]:
    """Rank TTS models by Elo rating (smartest)."""
    ranked = sorted(
        [m for m in models if get_elo(m) is not None],
        key=lambda m: get_elo(m),
        reverse=True
    )
    return ranked[:limit] if limit else ranked


def rank_by_smart_fast_tts(models: list[dict[str, Any]], limit: Optional[int] = None) -> list[dict[str, Any]]:
    """Rank TTS models by quality vs speed composite.
    
    Uses z-score normalization when both Elo and speed are available.
    Requires Elo ≥ median of scored models.
    Falls back to best Elo among models with speed data if too few.
    """
    import math
    
    # Get models with both metrics
    scored = []
    for model in models:
        elo = get_elo(model)
        speed = get_chars_per_second(model)
        if elo is not None and speed is not None and speed > 0:
            scored.append({
                "model": model,
                "elo": elo,
                "log_speed": math.log(speed),
                "speed": speed
            })
    
    if not scored:
        # Graceful degradation: return models with speed, ranked by Elo
        with_speed = [m for m in models if get_chars_per_second(m) is not None]
        if with_speed:
            return rank_by_elo(with_speed, limit=limit)
        return []
    
    # If too few models for meaningful z-score, just rank by Elo
    if len(scored) < 3:
        ranked = sorted(scored, key=lambda x: x["elo"], reverse=True)
        return [s["model"] for s in ranked[:limit]] if limit else [s["model"] for s in ranked]
    
    # Calculate median Elo
    elos = sorted([s["elo"] for s in scored])
    median_elo = elos[len(elos) // 2]
    
    # Filter to models with Elo ≥ median
    scored = [s for s in scored if s["elo"] >= median_elo]
    
    if not scored:
        return []
    
    # Calculate z-scores
    elo_mean = sum(s["elo"] for s in scored) / len(scored)
    elo_std = (sum((s["elo"] - elo_mean) ** 2 for s in scored) / len(scored)) ** 0.5
    
    log_speed_mean = sum(s["log_speed"] for s in scored) / len(scored)
    log_speed_std = (sum((s["log_speed"] - log_speed_mean) ** 2 for s in scored) / len(scored)) ** 0.5
    
    # Avoid division by zero
    if elo_std == 0:
        elo_std = 1
    if log_speed_std == 0:
        log_speed_std = 1
    
    # Calculate composite scores
    for s in scored:
        z_elo = (s["elo"] - elo_mean) / elo_std
        z_log_speed = (s["log_speed"] - log_speed_mean) / log_speed_std
        s["score"] = z_elo + z_log_speed
    
    # Sort by score
    scored.sort(key=lambda x: x["score"], reverse=True)
    
    # Extract models and add metadata
    ranked = []
    for s in scored:
        model = s["model"]
        model["_smart_fast_score"] = s["score"]
        model["_elo"] = s["elo"]
        model["_speed"] = s["speed"]
        ranked.append(model)
    
    return ranked[:limit] if limit else ranked


def rank_by_smart_cheap_tts(models: list[dict[str, Any]], limit: Optional[int] = None) -> list[dict[str, Any]]:
    """Rank TTS models by cost efficiency (quality per dollar).
    
    Uses elo / price_per_1m_chars when available.
    Requires Elo ≥ median of scored models.
    """
    # Calculate efficiency scores
    scored = []
    for model in models:
        elo = get_elo(model)
        price = get_price_per_1m_chars(model)
        
        if elo is not None and price is not None and price > 0:
            efficiency = elo / price
            scored.append({
                "model": model,
                "elo": elo,
                "efficiency": efficiency,
                "price": price
            })
    
    if not scored:
        # Graceful degradation: note in model metadata
        return []
    
    # Calculate median Elo
    elos = sorted([s["elo"] for s in scored])
    median_elo = elos[len(elos) // 2]
    
    # Filter to models with Elo ≥ median
    scored = [s for s in scored if s["elo"] >= median_elo]
    
    if not scored:
        return []
    
    # Sort by efficiency (descending)
    scored.sort(key=lambda x: x["efficiency"], reverse=True)
    
    # Extract models and add metadata
    ranked = []
    for s in scored:
        model = s["model"]
        model["_cost_efficiency"] = s["efficiency"]
        model["_price"] = s["price"]
        ranked.append(model)
    
    return ranked[:limit] if limit else ranked
