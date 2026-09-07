"""add_received_processed_fields_to_facturagpt_webhooks

Revision ID: ad576528aa27
Revises: e57776a3dcdf
Create Date: 2026-09-06

Soporta el flujo idempotente de procesamiento de webhooks de FacturaGPT
(tabla `facturagpt_webhooks`):

- `received_at`: momento en que el evento se recibió y almacenó (store-before-process).
- `processed_at` pasa a ser NULLABLE sin DEFAULT: NULL == "recibido pero aún no
  procesado correctamente" (pendiente o falló). El worker lo setea al terminar.
- `last_error`: último error del worker (auditoría / reconciliación).
- `receipt_id`: trazabilidad directa al receipt resuelto (ON DELETE SET NULL,
  el webhook es auditoría y no debe bloquear borrados).
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ad576528aa27"
down_revision: Union[str, Sequence[str], None] = "e57776a3dcdf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # facturagpt_webhooks: recibido != procesado
    # ------------------------------------------------------------------
    op.execute("""
        ALTER TABLE facturagpt_webhooks
        ADD COLUMN IF NOT EXISTS received_at TIMESTAMP WITH TIME ZONE
            DEFAULT CURRENT_TIMESTAMP NOT NULL;
    """)

    # processed_at: lo setea el worker cuando TERMINA de procesar.
    op.execute("""
        ALTER TABLE facturagpt_webhooks
        ALTER COLUMN processed_at DROP DEFAULT;
    """)
    op.execute("""
        ALTER TABLE facturagpt_webhooks
        ALTER COLUMN processed_at DROP NOT NULL;
    """)

    op.execute("""
        ALTER TABLE facturagpt_webhooks
        ADD COLUMN IF NOT EXISTS last_error TEXT;
    """)

    op.execute("""
        ALTER TABLE facturagpt_webhooks
        ADD COLUMN IF NOT EXISTS receipt_id BIGINT REFERENCES receipts(id)
            ON DELETE SET NULL;
    """)


def downgrade() -> None:
    # Antes de restaurar NOT NULL, los pendientes se consideran procesados.
    op.execute("""
        UPDATE facturagpt_webhooks
        SET processed_at = received_at
        WHERE processed_at IS NULL;
    """)
    op.execute("""
        ALTER TABLE facturagpt_webhooks
        ALTER COLUMN processed_at SET DEFAULT CURRENT_TIMESTAMP;
    """)
    op.execute("""
        ALTER TABLE facturagpt_webhooks
        ALTER COLUMN processed_at SET NOT NULL;
    """)

    op.execute("ALTER TABLE facturagpt_webhooks DROP COLUMN IF EXISTS received_at;")
    op.execute("ALTER TABLE facturagpt_webhooks DROP COLUMN IF EXISTS last_error;")
    op.execute("ALTER TABLE facturagpt_webhooks DROP COLUMN IF EXISTS receipt_id;")
