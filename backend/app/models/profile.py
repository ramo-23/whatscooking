import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False, index=True)
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sex: Mapped[str | None] = mapped_column(String, nullable=True)
    goal: Mapped[str | None] = mapped_column(String, nullable=True)  # 'bulk' | 'cut' | 'maintain'
    activity_level: Mapped[str | None] = mapped_column(String, nullable=True)  # 'sedentary' | 'light' | 'moderate' | 'active' | 'very_active'
    target_calories: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    target_protein_g: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    target_carbs_g: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    target_fat_g: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)