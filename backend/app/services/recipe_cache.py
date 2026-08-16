from datetime import datetime

from sqlalchemy.orm import Session

from app.models.recipe import Recipe, RecipeIngredient
from app.services.spoonacular_client import fetch_recipe_details, parse_recipe_details

def get_or_fetch_recipe(db: Session, spoonacular_id: int) -> Recipe:
    recipe = db.query(Recipe).filter(Recipe.spoonacular_id == spoonacular_id).first()

    if recipe:
        return recipe

    raw = fetch_recipe_details(spoonacular_id)
    parsed = parse_recipe_details(raw)

    recipe = Recipe(
        spoonacular_id=parsed["spoonacular_id"],
        title=parsed["title"],
        image_url=parsed["image_url"],
        instructions=parsed["instructions"],
        calories=parsed["calories"],
        protein_g=parsed["protein_g"],
        carbs_g=parsed["carbs_g"],
        fat_g=parsed["fat_g"],
        servings=parsed["servings"],
    )
    db.add(recipe)
    db.flush()

    for ing in parsed["ingredients"]:
        db.add(RecipeIngredient(recipe_id=recipe.id, **ing))

    db.commit()
    db.refresh(recipe)
    return recipe