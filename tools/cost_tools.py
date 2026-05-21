"""Cost analysis tool. Pricing data is cached inline — no network call at import time."""
from __future__ import annotations

# Pricing approximate as of 2025-Q2. Verify at https://cloud.google.com/vertex-ai/pricing
# before using in customer-facing estimates.
_LLM_PRICING: dict[str, dict] = {
    "gemini-2.0-flash": {
        "input_per_1m_tokens": 0.075,
        "output_per_1m_tokens": 0.30,
        "notes": "Best cost/perf for high-volume call center inference",
    },
    "gemini-2.0-pro": {
        "input_per_1m_tokens": 1.25,
        "output_per_1m_tokens": 5.00,
        "notes": "Use for complex reasoning tasks only",
    },
    "gemini-1.5-flash": {
        "input_per_1m_tokens": 0.075,
        "output_per_1m_tokens": 0.30,
        "notes": "Legacy — prefer 2.0-flash for new deployments",
    },
}

_INFRA_ESTIMATES: dict[str, dict] = {
    "vertex_ai_search": {
        "monthly_fixed": 300,
        "per_query": 0.001,
        "notes": "Vertex AI Search data store + serving",
    },
    "cloud_run": {
        "monthly_estimate_small": 50,
        "monthly_estimate_medium": 400,
        "notes": "Agent serving layer — scales to zero",
    },
    "vector_store_managed": {
        "monthly_per_million_vectors": 65,
        "notes": "Vertex AI Vector Search alternative to Vertex AI Search",
    },
}


def get_cost_analysis(
    monthly_calls: int = 50_000,
    avg_tokens_per_call: int = 2000,
    model_tier: str = "mixed",
) -> str:
    """Estimate monthly GenAI costs for a call center deployment.

    Args:
        monthly_calls: Estimated number of AI-assisted calls per month.
        avg_tokens_per_call: Average total tokens (input + output) per call interaction.
        model_tier: One of 'flash', 'pro', or 'mixed' (80% flash, 20% pro).

    Returns:
        Formatted cost breakdown and recommendations.
    """
    total_tokens_m = (monthly_calls * avg_tokens_per_call) / 1_000_000

    if model_tier == "flash":
        pricing = _LLM_PRICING["gemini-2.0-flash"]
        llm_cost = total_tokens_m * (pricing["input_per_1m_tokens"] + pricing["output_per_1m_tokens"]) / 2
    elif model_tier == "pro":
        pricing = _LLM_PRICING["gemini-2.0-pro"]
        llm_cost = total_tokens_m * (pricing["input_per_1m_tokens"] + pricing["output_per_1m_tokens"]) / 2
    else:  # mixed
        flash = _LLM_PRICING["gemini-2.0-flash"]
        pro = _LLM_PRICING["gemini-2.0-pro"]
        flash_cost = total_tokens_m * 0.8 * (flash["input_per_1m_tokens"] + flash["output_per_1m_tokens"]) / 2
        pro_cost = total_tokens_m * 0.2 * (pro["input_per_1m_tokens"] + pro["output_per_1m_tokens"]) / 2
        llm_cost = flash_cost + pro_cost

    infra_cost = (
        _INFRA_ESTIMATES["vertex_ai_search"]["monthly_fixed"]
        + (monthly_calls * _INFRA_ESTIMATES["vertex_ai_search"]["per_query"])
        + _INFRA_ESTIMATES["cloud_run"]["monthly_estimate_medium"]
    )
    total = llm_cost + infra_cost

    return f"""COST ESTIMATE (monthly, {monthly_calls:,} calls, {model_tier} tier)
─────────────────────────────────────────
LLM inference:      ${llm_cost:>8,.2f}
Infrastructure:     ${infra_cost:>8,.2f}
  - Vertex AI Search: ${_INFRA_ESTIMATES['vertex_ai_search']['monthly_fixed']:.0f}/mo + ${_INFRA_ESTIMATES['vertex_ai_search']['per_query']}/query
  - Cloud Run serving: ~${_INFRA_ESTIMATES['cloud_run']['monthly_estimate_medium']}/mo
─────────────────────────────────────────
TOTAL ESTIMATE:     ${total:>8,.2f}/mo
Per-call cost:      ${total / monthly_calls:.4f}

COST OPTIMIZATION LEVERS:
1. Route simple intent classification to gemini-2.0-flash (lowest cost)
2. Route complex escalation reasoning to gemini-2.0-pro (10-20% of calls)
3. Cache top-200 FAQ responses — eliminates ~40% of RAG queries
4. Batch post-call summarization during off-peak hours
5. Use streaming to reduce perceived latency without extra cost

NOTE: Prices approximate as of 2025-Q2. Verify at cloud.google.com/vertex-ai/pricing.
"""
