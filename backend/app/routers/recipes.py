from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.pantry import PantryItem
from app.schemas.recipe import RecipeSearchResult, RecipeOut, RecipeMatchResult
from app.services.spoonacular_client import search_recipes_by_ingredients
from app.services.recipe_cache import get_or_fetch_recipe
from app.services.matching_engine import rank_recipes_by_pantry_match

router = APIRouter(prefix="/recipes", tags=["recipes"])

@router.get("/search", response_model=list[RecipeSearchResult])
def search_recipes(
    ingredients: str = Query(..., description="Comma-separated ingredient names"),
    current_user: User = Depends(get_current_user)
):
    ingredient_list = [i.strip() for i in ingredients.split(",") if i.strip()]
    raw_results = search_recipes_by_ingredients(ingredient_list)

    return [
        RecipeSearchResult(
            spoonacular_id=r["id"],
            title=r["title"],
            image_url=r.get("image"),
            used_ingredient_count=r.get("usedIngredientCount", 0),
            missed_ingredient_count=r.get("missedIngredientCount", 0),
            missed_ingredients=[m["name"] for m in r.get("missedIngredients", [])],
        )
        for r in raw_results
    ]

@router.get("/match", response_model=list[RecipeMatchResult])
def match_recipes(
    number: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pantry_items = db.query(PantryItem).filter(PantryItem.user_id == current_user.id).all()
    if not pantry_items:
        return []

    pantry_ingreditent_names = {item.ingredient_name for item in pantry_items}

    candidates = search_recipes_by_ingredients(list(pantry_ingreditent_names), number=number)

    cached_recipes = [get_or_fetch_recipe(db, c["id"]) for c in candidates]

    ranked = rank_recipes_by_pantry_match(cached_recipes, pantry_ingreditent_names)

    return ranked

@router.get("/{spoonacular_id}", response_model=RecipeOut)
def get_recipe(
    spoonacular_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_or_fetch_recipe(db, spoonacular_id)