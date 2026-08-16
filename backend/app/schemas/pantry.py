import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field

class PantryItemBase(BaseModel):
    ingredient_name: str = Field(..., min_length=1)
    quantity: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1)
    expiry_date: Optional[date] = None

class PantryItemCreate(PantryItemBase):
    pass

class PantryItemUpdate(BaseModel):
    ingredient_name: Optional[str] = Field(None, min_length=1)
    quantity: Optional[float] = Field(None, gt=0)
    unit: Optional[str] = Field(None, min_length=1)
    expiry_date: Optional[date] = None

class PantryItemOut(PantryItemBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True