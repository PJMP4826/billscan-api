"""remove_file_url_from_receipt_images

Revision ID: e57776a3dcdf
Revises: ec96e3bcbc61
Create Date: 2026-08-24 04:58:12.396346

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e57776a3dcdf'
down_revision: Union[str, Sequence[str], None] = 'ec96e3bcbc61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # We check if the column exists before dropping to avoid "column does not exist" errors
    op.execute("""
        ALTER TABLE receipt_images 
        DROP COLUMN IF EXISTS file_url;
    """)

def downgrade() -> None:
    # To go back, you MUST allow NULLs or provide a default, 
    # otherwise, old records will block the downgrade.
    op.add_column('receipt_images', sa.Column('file_url', sa.Text(), nullable=True))
