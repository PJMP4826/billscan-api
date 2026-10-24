"""add_billing_preferences_to_receipt_billing_details

Revision ID: c3a7f1d94b28
Revises: 2d944ffc2411
Create Date: 2026-10-24

Persiste la elección fiscal del cliente al solicitar la factura de un ticket.
Antes, el uso de CFDI y el régimen se tomaban por defecto de ``fiscal_info``;
ahora el cliente los envía en la request, por lo que se guardan junto al
detalle de facturación para poder auditarlos y reintentar con los mismos
valores.

- ``uso_cfdi VARCHAR(10)``: código SAT de uso de CFDI (ej. ``G03``).
- ``regimen_code VARCHAR(10)``: código SAT de régimen fiscal (ej. ``612``).

Ambas columnas son NULLABLE: si el cliente no envía los valores se conserva el
comportamiento anterior (fallback a ``fiscal_info``).
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3a7f1d94b28"
down_revision: Union[str, Sequence[str], None] = "2d944ffc2411"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE receipt_billing_details
        ADD COLUMN IF NOT EXISTS uso_cfdi VARCHAR(10);
    """)
    op.execute("""
        ALTER TABLE receipt_billing_details
        ADD COLUMN IF NOT EXISTS regimen_code VARCHAR(10);
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE receipt_billing_details DROP COLUMN IF EXISTS uso_cfdi;")
    op.execute(
        "ALTER TABLE receipt_billing_details DROP COLUMN IF EXISTS regimen_code;"
    )
