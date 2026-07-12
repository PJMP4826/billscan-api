"""modify_idempotency_key_and_add_unique_index_to_webhooks

Revision ID: ec96e3bcbc61
Revises: 1a0398fa0976
Create Date: 2026-07-12 00:51:28.732099

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ec96e3bcbc61"
down_revision: Union[str, Sequence[str], None] = "1a0398fa0976"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Primer comando
    op.execute("""
        ALTER TABLE facturagpt_webhooks 
        ADD CONSTRAINT uq_facturagpt_webhooks_idempotency_key UNIQUE (idempotency_key);
    """)

    op.execute("""
        CREATE INDEX ix_facturagpt_webhooks_idempotency_key 
        ON facturagpt_webhooks (idempotency_key);
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_facturagpt_webhooks_idempotency_key;")
    op.execute(
        "ALTER TABLE facturagpt_webhooks DROP CONSTRAINT IF EXISTS uq_facturagpt_webhooks_idempotency_key;"
    )
