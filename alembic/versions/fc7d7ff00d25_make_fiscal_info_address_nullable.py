"""make fiscal_info.address nullable

Revision ID: fc7d7ff00d25
Revises: 20f1477488de
Create Date: 2026-07-01 05:34:50.235272

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "fc7d7ff00d25"
down_revision: Union[str, Sequence[str], None] = "20f1477488de"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE fiscal_info
        ALTER COLUMN address DROP NOT NULL;
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE fiscal_info
        ALTER COLUMN address SET NOT NULL;
    """)
