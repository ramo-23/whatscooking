import uuid
from typing import Optional

from pydantic import BaseModel


class RecipeSearchResult(BaseModel):
    spoonacular_id: int
    title: str
    image_url: Optional[str] = None
    used_ingredient_count: int
    missed_ingredient_count: int
    missed_ingredients: list[str] = []


class RecipeIngredientOut(BaseModel):
    ingredient_name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None

    class Config:
        from_attributes = True


class RecipeOut(BaseModel):
    id: uuid.UUID
    spoonacular_id: int
    title: str
    image_url: Optional[str] = None
    instructions: Optional[str] = None
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    servings: Optional[int] = None
    ingredients: list[RecipeIngredientOut] = []

    class Config:
        from_attributes = True