from __future__ import annotations

from typing import Any


def estimate_llm_cost(
    *,
    pricing_config: dict[str, Any],
    provider: str,
    model: str,
    usage_normalized: dict[str, int | None],
) -> dict[str, Any]:
    prompt_tokens = usage_normalized.get("prompt_tokens") or 0
    completion_tokens = usage_normalized.get("completion_tokens") or 0

    provider_pricing = pricing_config.get("llm", {}).get(provider, {})
    model_pricing = provider_pricing.get("models", {}).get(model, {})

    input_rate = float(model_pricing.get("input") or 0.0)
    output_rate = float(model_pricing.get("output") or 0.0)

    llm_cost = (
        (prompt_tokens * input_rate) + (completion_tokens * output_rate)
    ) / 1_000_000

    return {
        "llm_cost_usd": round(llm_cost, 8),
        "total_cost_usd": round(llm_cost, 8),
        "currency": pricing_config.get("currency", "USD"),
        "pricing_version": pricing_config.get("updated_at", "unknown"),
    }
