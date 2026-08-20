from datetime import date, datetime
import re
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models import MealLog, PantryItem, Recipe, UserProfile
from app.schemas.suggestion import MacroBudget, SuggestionRequest, SuggestionResponse
from app.models.user import User
from app.services.ai_suggestion import select_suggestions
from app.services.matching_engine import rank_recipes_by_pantry_match
from app.services.recipe_cache import get_or_fetch_recipe
from app.services.spoonacular_client import search_recipes_by_ingredients, search_recipes_by_query

router = APIRouter(prefix="/suggestions", tags=["suggestions"])


def _recipe_url(title: str, spoonacular_id: int) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"https://spoonacular.com/recipes/{slug}-{spoonacular_id}"


def _remaining_budget(db: Session, user_id: Any, profile: UserProfile) -> MacroBudget:
    today = date.today()
    start_of_day = datetime(today.year, today.month, today.day)
    end_of_day = datetime(today.year, today.month, today.day, 23, 59, 59, 999999)
    meals = db.query(MealLog).filter(
        MealLog.user_id == user_id,
        MealLog.logged_at >= start_of_day,
        MealLog.logged_at <= end_of_day,
    ).all()

    logged_calories = sum(float(meal.calories or 0.0) for meal in meals)
    logged_protein = sum(float(meal.protein_g or 0.0) for meal in meals)
    logged_carbs = sum(float(meal.carbs_g or 0.0) for meal in meals)
    logged_fat = sum(float(meal.fat_g or 0.0) for meal in meals)

    return MacroBudget(
        calories=max(0.0, float(profile.target_calories or 0.0) - logged_calories),
        protein_g=max(0.0, float(profile.target_protein_g or 0.0) - logged_protein),
        carbs_g=max(0.0, float(profile.target_carbs_g or 0.0) - logged_carbs),
        fat_g=max(0.0, float(profile.target_fat_g or 0.0) - logged_fat),
    )


def _candidate_payload(ranked: dict[str, Any], recipe: Recipe) -> dict[str, Any]:
    return {
        "recipe_id": ranked["recipe_id"],
        "spoonacular_id": ranked["spoonacular_id"],
        "title": ranked["title"],
        "recipe_url": _recipe_url(ranked["title"], ranked["spoonacular_id"]),
        "image_url": str(recipe.image_url) if recipe.image_url else None,
        "coverage_pct": ranked["coverage_pct"],
        "missing_ingredients": ranked["missing_ingredients"],
        "calories": float(recipe.calories) if recipe.calories is not None else None,
        "protein_g": float(recipe.protein_g) if recipe.protein_g is not None else None,
        "carbs_g": float(recipe.carbs_g) if recipe.carbs_g is not None else None,
        "fat_g": float(recipe.fat_g) if recipe.fat_g is not None else None,
    }


def _rank_candidates(
    recipes: list[Recipe], pantry_names: set[str], use_pantry: bool
) -> list[dict[str, Any]]:
    if use_pantry and pantry_names:
        return rank_recipes_by_pantry_match(recipes, pantry_names)
    return [
        {
            "recipe_id": recipe.id,
            "spoonacular_id": recipe.spoonacular_id,
            "title": recipe.title,
            "coverage_pct": 0.0,
            "missing_ingredients": [],
        }
        for recipe in recipes
    ]


def _response_message(source: str, count: int) -> str:
    if count == 0:
        return "I couldn't find a matching recipe for that request. Try adding more detail or ingredients."
    if source == "pantry":
        return f"I found {count} recipe{'s' if count != 1 else ''} that fit your pantry and goals."
    if source == "search":
        return f"I found {count} recipe{'s' if count != 1 else ''} matching your request."
    return f"I found {count} recipe{'s' if count != 1 else ''} using your request and pantry."


@router.post("", response_model=SuggestionResponse)
def suggest_meals(
    payload: SuggestionRequest = SuggestionRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return grounded AI selections from pantry or natural-language candidates."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found - please set your goals first",
        )

    pantry_items = db.query(PantryItem).filter(PantryItem.user_id == current_user.id).all()
    pantry_names = {item.ingredient_name for item in pantry_items}
    budget = _remaining_budget(db, current_user.id, profile)
    if payload.source == "pantry" and not pantry_items:
        return SuggestionResponse(
            message="Your pantry is empty, so I couldn't make a pantry-based suggestion yet.",
            source=payload.source,
            remaining_budget=budget,
            suggestions=[],
        )
    try:
        search_results: list[dict[str, Any]] = []
        if payload.source in {"pantry", "hybrid"} and pantry_names:
            search_results.extend(
                search_recipes_by_ingredients(list(pantry_names), number=payload.candidate_count)
            )
        if payload.source in {"search", "hybrid"} and payload.request:
            search_results.extend(
                search_recipes_by_query(payload.request, number=payload.candidate_count)
            )

        unique_results = {result["id"]: result for result in search_results}
        cached_recipes = [get_or_fetch_recipe(db, spoonacular_id) for spoonacular_id in unique_results]
        ranked = _rank_candidates(cached_recipes, pantry_names, payload.source != "search")
        if not ranked:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No recipes were found for the selected suggestion source",
            )
        recipes_by_id = {recipe.id: recipe for recipe in cached_recipes}
        candidates = [
            _candidate_payload(match, recipes_by_id[match["recipe_id"]])
            for match in ranked
        ]
        selected = select_suggestions(
            candidates, budget, payload.number, payload.request, payload.source
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return SuggestionResponse(
        message=_response_message(payload.source, len(selected)),
        source=payload.source,
        remaining_budget=budget,
        suggestions=selected,
    )
