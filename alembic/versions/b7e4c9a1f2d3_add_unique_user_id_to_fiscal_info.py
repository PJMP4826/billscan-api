"""add_unique_user_id_to_fiscal_info

Revision ID: b7e4c9a1f2d3
Revises: 7f3c2b91d4a8
Create Date: 2026-11-21

Garantiza una sola fila de ``fiscal_info`` por usuario. Con este constraint el
registro pasa a ser un upsert (``ON CONFLICT (user_id) DO UPDATE``) y deja de
crear filas nuevas en cada POST.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b7e4c9a1f2d3"
down_revision: Union[str, Sequence[str], None] = "7f3c2b91d4a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE fiscal_info
        ADD CONSTRAINT fiscal_info_user_id_unique UNIQUE (user_id);
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE fiscal_info
        DROP CONSTRAINT IF EXISTS fiscal_info_user_id_unique;
    """)
