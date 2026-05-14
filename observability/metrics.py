import json
import time
from datetime import datetime
from pathlib import Path

METRICS_PATH = Path(__file__).parent.parent / "data" / "metrics.jsonl"

def log_metric(agent: str, action: str, duration_seconds: float, 
               input_tokens: int, output_tokens: int, 
               confidence: float = None, success: bool = True, error: str = None):
    """Log a single agent metric entry."""
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "agent": agent,
        "action": action,
        "duration_seconds": round(duration_seconds, 3),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "estimated_cost_usd": round((input_tokens * 0.000003) + (output_tokens * 0.000015), 6),
        "confidence": confidence,
        "success": success,
        "error": error
    }
    with open(METRICS_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry

def get_all_metrics() -> list[dict]:
    """Read all metric entries."""
    if not METRICS_PATH.exists():
        return []
    entries = []
    with open(METRICS_PATH) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries

def get_summary() -> dict:
    """Compute summary statistics across all runs."""
    metrics = get_all_metrics()
    if not metrics:
        return {}

    total_cost = sum(m["estimated_cost_usd"] for m in metrics)
    total_tokens = sum(m["total_tokens"] for m in metrics)
    avg_latency = sum(m["duration_seconds"] for m in metrics) / len(metrics)
    success_rate = sum(1 for m in metrics if m["success"]) / len(metrics) * 100
    
    by_agent = {}
    for m in metrics:
        agent = m["agent"]
        if agent not in by_agent:
            by_agent[agent] = {"calls": 0, "total_duration": 0, "total_tokens": 0, "total_cost": 0, "confidences": []}
        by_agent[agent]["calls"] += 1
        by_agent[agent]["total_duration"] += m["duration_seconds"]
        by_agent[agent]["total_tokens"] += m["total_tokens"]
        by_agent[agent]["total_cost"] += m["estimated_cost_usd"]
        if m["confidence"] is not None:
            by_agent[agent]["confidences"].append(m["confidence"])

    for agent in by_agent:
        d = by_agent[agent]
        d["avg_latency"] = round(d["total_duration"] / d["calls"], 3)
        d["avg_confidence"] = round(sum(d["confidences"]) / len(d["confidences"]), 1) if d["confidences"] else None
        d["total_cost"] = round(d["total_cost"], 6)

    return {
        "total_runs": len(metrics),
        "total_cost_usd": round(total_cost, 6),
        "total_tokens": total_tokens,
        "avg_latency_seconds": round(avg_latency, 3),
        "success_rate_pct": round(success_rate, 1),
        "by_agent": by_agent,
        "recent": metrics[-10:]
    }