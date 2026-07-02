"""remove_unique_constraint_from_merchants

Revision ID: 888738deecc7
Revises: fc7d7ff00d25
Create Date: 2026-07-02 15:26:44.497277

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "888738deecc7"
down_revision: Union[str, Sequence[str], None] = "fc7d7ff00d25"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Eliminamos el constraint único compuesto
    op.execute("""
        ALTER TABLE merchants 
        DROP CONSTRAINT unq_merchant_branch;
    """)


def downgrade() -> None:
    # Volvemos a crear el constraint en caso de revertir
    op.execute("""
        ALTER TABLE merchants 
        ADD CONSTRAINT unq_merchant_branch UNIQUE (tax_id, branch_id);
    """)
