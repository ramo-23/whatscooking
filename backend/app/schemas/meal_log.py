from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


class MealLogCreate(BaseModel):
    recipe_id: Optional[UUID] = None
    meal_name: Optional[str] = None
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    
    @property
    def is_manual(self) -> bool:
        return self.recipe_id is None


class MealLogOut(BaseModel):
    id: UUID
    user_id: UUID
    recipe_id: Optional[UUID]
    meal_name: Optional[str] = None
    logged_at: datetime
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    
    class Config:
        from_attributes = True


class DailySummary(BaseModel):
    date: str
    total_calories: int
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    target_calories: int
    target_protein_g: float
    target_carbs_g: float
    target_fat_g: float
    remaining_calories: int
    remaining_protein_g: float
    remaining_carbs_g: float
    remaining_fat_g: float
    meals: list[MealLogOut]