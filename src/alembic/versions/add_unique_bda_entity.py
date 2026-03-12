"""add_unique_bda_entity_constraint

Revision ID: add_unique_bda_entity
Revises: add_embedded_status
Create Date: 2026-03-12 18:22:00.000000

"""

from typing import Sequence, Union

from alembic import op

revision: str = "add_unique_bda_entity"
down_revision: Union[str, Sequence[str], None] = "add_embedded_status"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_policy_chunks_policy_bda_entity",
        "policy_chunks",
        ["policy_id", "bda_entity_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_policy_chunks_policy_bda_entity", "policy_chunks", type_="unique")
