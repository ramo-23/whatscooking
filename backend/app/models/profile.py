import uuid

from sqlalchemy import Column, String, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    weight_kg = Column(Numeric, nullable=True)
    goal = Column(String, nullable=True)  # 'bulk' | 'cut' | 'maintain'
    activity_level = Column(String, nullable=True)  # 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active'
    target_calories = Column(Numeric, nullable=True)
    target_protein_g = Column(Numeric, nullable=True)
    target_carbs_g = Column(Numeric, nullable=True)
    target_fat_g = Column(Numeric, nullable=True)