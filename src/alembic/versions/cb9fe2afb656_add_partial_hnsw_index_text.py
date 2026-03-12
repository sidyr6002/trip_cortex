"""add_partial_hnsw_index_text

Revision ID: cb9fe2afb656
Revises: add_unique_bda_entity
Create Date: 2026-03-12 19:12:02.471862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cb9fe2afb656'
down_revision: Union[str, Sequence[str], None] = 'add_unique_bda_entity'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE INDEX idx_policy_chunks_embedding_text
        ON policy_chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        WHERE content_type = 'text'
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_policy_chunks_embedding_text")
