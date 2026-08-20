import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MealLog(Base):
    __tablename__ = "meal_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    recipe_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("recipes.id"), nullable=True)
    meal_name: Mapped[str | None] = mapped_column(String, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    calories: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    protein_g: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    carbs_g: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    fat_g: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)