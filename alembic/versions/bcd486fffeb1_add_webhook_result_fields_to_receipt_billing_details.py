"""add_webhook_result_fields_to_receipt_billing_details

Revision ID: bcd486fffeb1
Revises: ad576528aa27
Create Date: 2026-09-06

Persiste el resultado del CFDI reportado por el webhook `factura.completed`
de FacturaGPT en `receipt_billing_details`:

- `cfdi_summary JSONB`: resumen fiscal crudo del CFDI generado
  (folio fiscal, RFC emisor/receptor, montos, moneda, fecha timbrado).
- `completed_at TIMESTAMP WITH TIME ZONE`: cuándo FacturaGPT reportó el
  timbrado completado.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "bcd486fffeb1"
down_revision: Union[str, Sequence[str], None] = "ad576528aa27"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE receipt_billing_details
        ADD COLUMN IF NOT EXISTS cfdi_summary JSONB;
    """)
    op.execute("""
        ALTER TABLE receipt_billing_details
        ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP WITH TIME ZONE;
    """)


def downgrade() -> None:
    op.execute(
        "ALTER TABLE receipt_billing_details DROP COLUMN IF EXISTS cfdi_summary;"
    )
    op.execute(
        "ALTER TABLE receipt_billing_details DROP COLUMN IF EXISTS completed_at;"
    )
