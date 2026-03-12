"""add_embedded_status_to_policies

Revision ID: add_embedded_status
Revises: 2f59c70e0b61
Create Date: 2026-03-12 16:40:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "add_embedded_status"
down_revision: Union[str, Sequence[str], None] = "2f59c70e0b61"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("chk_policies_status", "policies", type_="check")
    op.create_check_constraint(
        "chk_policies_status",
        "policies",
        "status IN ('pending', 'processing', 'embedded', 'ready', 'failed')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("chk_policies_status", "policies", type_="check")
    op.create_check_constraint(
        "chk_policies_status",
        "policies",
        "status IN ('pending', 'processing', 'ready', 'failed')",
    )
