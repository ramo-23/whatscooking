from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.recipe import RecipeSearchResult, RecipeOut
from app.services.spoonacular_client import search_recipes_by_ingredients
from app.services.recipe_cache import get_or_fetch_recipe

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

@router.get("/{spoonacular_id}", response_model=RecipeOut)
def get_recipe(
    spoonacular_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_or_fetch_recipe(db, spoonacular_id)