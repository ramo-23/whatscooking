import httpx

from app.core.config import settings

BASE_URL = "https://api.spoonacular.com"

def search_recipes_by_ingredients(ingrediets: list[str], number: int = 10) -> list[dict]:
    response = httpx.get(
        f"{BASE_URL}/recipes/findByIngredients",
        params={
            "ingredients": ",".join(ingrediets),
            "number": number,
            "ranking": 1,
            "ignorePantry": True,
            "apiKey": settings.spoonacular_api_key
        },
    )
    if response.status_code != 200:
        raise RuntimeError(f"Spoonacular search failed: {response.status_code} {response.text}")
    return response.json()

def fetch_recipe_details(spoonacular_id: int) -> dict: 
    response = httpx.get(
        f"{BASE_URL}/recipes/{spoonacular_id}/information",
        params= {
            "includeNutrition": True,
            "apiKey": settings.spoonacular_api_key
        },
    )
    if response.status_code != 200:
        raise RuntimeError(f"Spoonacular recipe fetch failed: {response.status_code} {response.text}")
    return response.json()

def _extract_nutrient(nutrients: list[dict], name: str) -> float | None:
    for n in nutrients:
        if n.get("name") == name:
            return n.get("amount")
    return None

def parse_recipe_details(data: dict) -> dict:
    """Here I will flatten the raw response from the API into the fields that my model needs"""
    nutrients = data.get("nutrition", {}).get("nutrients", [])
    return{
        "spoonacular_id": data["id"],
        "title": data.get("title"),
        "image_url": data.get("image"),
        "instructions": data.get("instructions"),
        "calories": _extract_nutrient(nutrients, "Calories"),
        "protein_g": _extract_nutrient(nutrients, "Protein"),
        "carbs_g": _extract_nutrient(nutrients, "Carbohydrates"),
        "fat_g": _extract_nutrient(nutrients, "Fat"),
        "servings": data.get("servings"),
        "ingredients": [
            {
                "ingredient_name": ing.get("name"),
                "quantity": ing.get("amount"),
                "unit": ing.get("unit"),
            }
            for ing in data.get("extendedIngredients", [])
        ],
    }