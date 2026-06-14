"""add receipt_uuid to receipts table

Revision ID: d9f1e59840b1
Revises: 9b692df66236
Create Date: 2026-06-14 04:36:41.083796

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa # type: ignore

# revision identifiers, used by Alembic.
revision: str = "d9f1e59840b1"
down_revision: Union[str, Sequence[str], None] = "9b692df66236"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agrega la columna receipt_id con la restricción UNIQUE
    op.execute("""
        ALTER TABLE receipts 
        ADD COLUMN receipt_uuid VARCHAR(36) UNIQUE NOT NULL;
    """)


def downgrade() -> None:
    # Elimina la columna en caso de hacer un rollback
    op.execute("""
        ALTER TABLE receipts 
        DROP COLUMN IF EXISTS receipt_uuid;
    """)
