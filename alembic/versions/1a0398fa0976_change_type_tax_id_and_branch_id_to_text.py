"""change_type_tax_id_and_branch_id_to_text

Revision ID: 1a0398fa0976
Revises: 888738deecc7
Create Date: 2026-07-02 15:48:28.259752

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1a0398fa0976"
down_revision: Union[str, Sequence[str], None] = "888738deecc7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Cambiamos los tipos a TEXT para
    op.execute("""
        ALTER TABLE merchants 
            ALTER COLUMN tax_id TYPE TEXT,
            ALTER COLUMN branch_id TYPE TEXT;
    """)


def downgrade() -> None:
    # En caso de revertir, regresamos al VARCHAR(50) original
    op.execute("""
        ALTER TABLE merchants 
            ALTER COLUMN tax_id TYPE VARCHAR(50),
            ALTER COLUMN branch_id TYPE VARCHAR(50);
    """)
