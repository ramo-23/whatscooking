import uuid
from datetime import datetime

from sqlalchemy import Column, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class MealLog(Base):
    __tablename__ = "meal_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    recipe_id = Column(UUID(as_uuid=True), ForeignKey("recipes.id"), nullable=True)
    logged_at = Column(DateTime, default=datetime.utcnow)
    calories = Column(Numeric, nullable=True)
    protein_g = Column(Numeric, nullable=True)
    carbs_g = Column(Numeric, nullable=True)
    fat_g = Column(Numeric, nullable=True)