"""store meal names and use an integer profile age

Revision ID: 8e2c4f1a7b90
Revises: 55b31bfb2043
Create Date: 2026-08-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8e2c4f1a7b90"
down_revision: Union[str, Sequence[str], None] = "55b31bfb2043"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("meal_log", sa.Column("meal_name", sa.String(), nullable=True))
    op.alter_column(
        "user_profiles",
        "age",
        existing_type=sa.Numeric(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="age::integer",
    )


def downgrade() -> None:
    op.alter_column(
        "user_profiles",
        "age",
        existing_type=sa.Integer(),
        type_=sa.Numeric(),
        existing_nullable=True,
        postgresql_using="age::numeric",
    )
    op.drop_column("meal_log", "meal_name")
