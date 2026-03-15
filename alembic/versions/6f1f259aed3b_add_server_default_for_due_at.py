"""add server default for due_at

Revision ID: 6f1f259aed3b
Revises: bd084dd3193e
Create Date: 2026-03-15 15:40:11.349638

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6f1f259aed3b'
down_revision: Union[str, Sequence[str], None] = 'bd084dd3193e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "card_progress",
        "due_at",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
        server_default=sa.text("now()"),
    )
    op.execute("UPDATE card_progress SET due_at = now() WHERE due_at IS NULL")


def downgrade() -> None:
    op.alter_column(
        "card_progress",
        "due_at",
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=True,
        server_default=None,
    )
