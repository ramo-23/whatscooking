import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ingredients = relationship("RecipeIngredient", cascade="all, delete-orphan")
    spoonacular_id = Column(Integer, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    instructions = Column(String, nullable=True)
    calories = Column(Numeric, nullable=True)
    protein_g = Column(Numeric, nullable=True)
    carbs_g = Column(Numeric, nullable=True)
    fat_g = Column(Numeric, nullable=True)
    servings = Column(Integer, nullable=True)
    cached_at = Column(DateTime, default=datetime.utcnow)


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=False, index=True)
    ingredient_name = Column(String, nullable=False, index=True)
    quantity = Column(Numeric, nullable=True)
    unit = Column(String, nullable=True)