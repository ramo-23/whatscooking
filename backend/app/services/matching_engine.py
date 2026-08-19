from app.models.recipe import Recipe
from app.utils.normalize import tokenize_ingredient


def _is_match(pantry_tokens: set[str], recipe_tokens: set[str]) -> bool:
    """True if the two ingredient token sets share at least one meaningful word."""
    return bool(pantry_tokens & recipe_tokens)


def score_recipe_against_pantry(recipe: Recipe, pantry_ingredient_names: set[str]) -> dict:
    recipe_ingredients = recipe.ingredients

    if not recipe_ingredients:
        return {
            "recipe_id": recipe.id,
            "spoonacular_id": recipe.spoonacular_id,
            "title": recipe.title,
            "coverage_pct": 0.0,
            "missing_ingredients": [],
        }

    pantry_token_sets = [tokenize_ingredient(p) for p in pantry_ingredient_names]

    missing = []
    matched_count = 0

    for ing in recipe_ingredients:
        recipe_tokens = tokenize_ingredient(ing.ingredient_name)
        if any(_is_match(p_tokens, recipe_tokens) for p_tokens in pantry_token_sets):
            matched_count += 1
        else:
            missing.append(ing.ingredient_name)

    coverage_pct = round((matched_count / len(recipe_ingredients)) * 100, 1)

    return {
        "recipe_id": recipe.id,
        "spoonacular_id": recipe.spoonacular_id,
        "title": recipe.title,
        "coverage_pct": coverage_pct,
        "missing_ingredients": missing,
    }


def rank_recipes_by_pantry_match(recipes: list[Recipe], pantry_ingredient_names: set[str]) -> list[dict]:
    scored = [score_recipe_against_pantry(r, pantry_ingredient_names) for r in recipes]
    return sorted(scored, key=lambda r: r["coverage_pct"], reverse=True)