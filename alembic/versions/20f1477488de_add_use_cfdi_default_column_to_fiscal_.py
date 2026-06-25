"""add use_cfdi_default column to fiscal_info table

Revision ID: 20f1477488de
Revises: 6ebe7d9818f3
Create Date: 2026-06-25 05:27:37.071359

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20f1477488de"
down_revision: Union[str, Sequence[str], None] = "6ebe7d9818f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agrega la columna receipt_id con la restricción UNIQUE
    op.execute("""
        ALTER TABLE fiscal_info 
        ADD COLUMN use_cfdi_default VARCHAR(50) NOT NULL DEFAULT 'G03';
    """)


def downgrade() -> None:
    # Elimina la columna en caso de hacer un rollback
    op.execute("""
        ALTER TABLE fiscal_info 
        DROP COLUMN IF EXISTS use_cfdi_default;
    """)
