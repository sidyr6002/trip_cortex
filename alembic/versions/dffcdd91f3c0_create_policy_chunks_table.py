"""create_policy_chunks_table

Revision ID: dffcdd91f3c0
Revises: 
Create Date: 2026-02-26 08:47:10.460570

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dffcdd91f3c0'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    
    # Create policy_chunks table
    op.execute("""
        CREATE TABLE policy_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            policy_id UUID NOT NULL,
            content_type VARCHAR(20) NOT NULL,
            content_text TEXT,
            source_page INTEGER,
            section_title VARCHAR(255),
            reading_order INTEGER,
            bda_entity_id VARCHAR(255),
            bda_entity_subtype VARCHAR(50),
            embedding vector(1024) NOT NULL,
            metadata JSONB,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    
    # Create HNSW index for vector similarity search
    op.execute("""
        CREATE INDEX idx_policy_chunks_embedding
        ON policy_chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)
    
    # Create B-tree index on policy_id
    op.execute("""
        CREATE INDEX idx_policy_chunks_policy_id
        ON policy_chunks (policy_id)
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.execute("DROP INDEX IF EXISTS idx_policy_chunks_policy_id")
    op.execute("DROP INDEX IF EXISTS idx_policy_chunks_embedding")
    
    # Drop table
    op.execute("DROP TABLE IF EXISTS policy_chunks")
    
    # Drop extension
    op.execute("DROP EXTENSION IF EXISTS vector")
