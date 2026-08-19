from typing import Optional, Literal
from pydantic import BaseModel, Field

class ProfileUpsert(BaseModel):
    weight_kg: float = Field(..., gt=0)
    height_cm: float = Field(..., gt=0)
    age: int = Field(..., gt=0, lt=120)
    sex: Literal["male", "female"]
    goal: Literal["bulk", "cut", "maintain"]
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"]

class ProfileOut(BaseModel):
    weight_kg: float
    height_cm: float
    age: int
    sex: str
    goal: str
    activity_level: str
    target_calories: float
    target_protein_g: float
    target_carbs_g: float
    target_fat_g: float

    class Config:
        from_attributes = True