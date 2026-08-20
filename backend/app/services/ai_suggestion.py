import json
from typing import Any
from uuid import UUID

from groq import Groq

from app.core.config import settings
from app.schemas.suggestion import (
    LLMSelectionResponse,
    MacroBudget,
)


SYSTEM_PROMPT = """You select meals from a fixed candidate list.
You must only select recipe_id values that appear in the candidates.
Do not invent recipes, ingredients, nutrition values, or IDs.
Use the user's request as a preference, not as permission to invent a recipe.
Treat macro_fit as authoritative. Prefer candidates where macro_fit is true.
If no candidate fits, choose the least over-budget candidate and say so clearly.
Never claim a recipe fits a macro whose remaining budget it exceeds.
Return JSON only in this exact shape:
{"selections": [{"recipe_id": "UUID", "reason": "brief explanation"}]}
"""


def _build_prompt(
    candidates: list[dict[str, Any]],
    budget: MacroBudget,
    number: int,
    user_request: str | None,
) -> str:
    prompt_candidates = []
    for candidate in candidates:
        overages = {
            "calories": max(0.0, (candidate["calories"] or 0.0) - budget.calories),
            "protein_g": max(0.0, (candidate["protein_g"] or 0.0) - budget.protein_g),
            "carbs_g": max(0.0, (candidate["carbs_g"] or 0.0) - budget.carbs_g),
            "fat_g": max(0.0, (candidate["fat_g"] or 0.0) - budget.fat_g),
        }
        prompt_candidate = candidate.copy()
        prompt_candidate["macro_fit"] = not any(overages.values())
        prompt_candidate["macro_overages"] = overages
        prompt_candidates.append(prompt_candidate)

    return json.dumps(
        {
            "remaining_budget": budget.model_dump(),
            "user_request": user_request,
            "max_selections": number,
            "candidates": prompt_candidates,
        },
        default=str,
    )


def _correct_macro_reason(
    candidate: dict[str, Any], budget: MacroBudget, source: str
) -> None:
    overages = {
        "calories": max(0.0, (candidate["calories"] or 0.0) - budget.calories),
        "protein": max(0.0, (candidate["protein_g"] or 0.0) - budget.protein_g),
        "carbohydrates": max(0.0, (candidate["carbs_g"] or 0.0) - budget.carbs_g),
        "fat": max(0.0, (candidate["fat_g"] or 0.0) - budget.fat_g),
    }
    exceeded = [name for name, amount in overages.items() if amount > 0]
    candidate["macro_fit"] = not exceeded
    if exceeded:
        selection_context = {
            "pantry": "Best available pantry match",
            "search": "Best available recipe for the request",
            "hybrid": "Best available pantry-aware match",
        }[source]
        candidate["reason"] = (
            f"{selection_context}, but it is over your "
            f"{', '.join(exceeded)} limit. {candidate['reason']}"
        )
        candidate["macro_note"] = (
            f"Over your {', '.join(exceeded)} limit; this was the closest available match."
        )
    else:
        candidate["macro_note"] = "Fits within your remaining macro budget."


def select_suggestions(
    candidates: list[dict[str, Any]],
    budget: MacroBudget,
    number: int,
    user_request: str | None = None,
    source: str = "pantry",
) -> list[dict[str, Any]]:
    """Ask Groq to rank only recipes already supplied by the matching engine."""
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")
    if not candidates:
        return []

    client = Groq(api_key=settings.groq_api_key)
    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_prompt(candidates, budget, number, user_request)},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "meal_selections",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "selections": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": number,
                            "items": {
                                "type": "object",
                                "properties": {
                                    "recipe_id": {"type": "string"},
                                    "reason": {"type": "string"},
                                },
                                "required": ["recipe_id", "reason"],
                                "additionalProperties": False,
                            },
                        }
                    },
                    "required": ["selections"],
                    "additionalProperties": False,
                },
            },
        },
        temperature=0,
    )

    content = completion.choices[0].message.content
    if not content:
        raise RuntimeError("Groq returned an empty suggestion response")

    parsed = LLMSelectionResponse.model_validate_json(content)
    candidate_by_id = {candidate["recipe_id"]: candidate for candidate in candidates}
    selected: list[dict[str, Any]] = []
    seen: set[UUID] = set()

    for selection in parsed.selections:
        if selection.recipe_id in seen or selection.recipe_id not in candidate_by_id:
            continue
        candidate = candidate_by_id[selection.recipe_id].copy()
        candidate["reason"] = selection.reason
        selected.append(candidate)
        seen.add(selection.recipe_id)
        if len(selected) == number:
            break

    if not selected:
        fallback = candidates[0].copy()
        fallback["reason"] = "Best available candidate selected because the AI returned no valid candidate."
        _correct_macro_reason(fallback, budget, source)
        return [fallback]

    for candidate in selected:
        _correct_macro_reason(candidate, budget, source)

    return selected
