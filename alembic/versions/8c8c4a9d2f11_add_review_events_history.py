from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8c8c4a9d2f11'
down_revision: Union[str, Sequence[str], None] = '6f1f259aed3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'review_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('card_id', sa.UUID(), nullable=False),
        sa.Column('quality', sa.Integer(), nullable=False),
        sa.Column('was_correct', sa.Boolean(), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['card_id'], ['cards.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_review_events_user_id'), 'review_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_review_events_card_id'), 'review_events', ['card_id'], unique=False)
    op.create_index(op.f('ix_review_events_reviewed_at'), 'review_events', ['reviewed_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_review_events_reviewed_at'), table_name='review_events')
    op.drop_index(op.f('ix_review_events_card_id'), table_name='review_events')
    op.drop_index(op.f('ix_review_events_user_id'), table_name='review_events')
    op.drop_table('review_events')
