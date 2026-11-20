"""create_invoice_quota_usages

Revision ID: 7f3c2b91d4a8
Revises: c3a7f1d94b28
Create Date: 2026-11-20

Registra el consumo del límite de facturas por RFC. El RFC nunca se guarda en
claro: se usa un fingerprint determinístico (HMAC-SHA256) como llave lógica,
de modo que dos cuentas con el mismo RFC comparten la misma cuota.

- ``status``: ``RESERVED`` (factura en curso), ``CONSUMED`` (factura timbrada)
  o ``RELEASED`` (falló y devolvió el cupo).
- ``receipt_id`` es UNIQUE para que la reserva sea idempotente por ticket.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7f3c2b91d4a8"
down_revision: Union[str, Sequence[str], None] = "c3a7f1d94b28"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS invoice_quota_usages (
            id BIGSERIAL PRIMARY KEY,
            rfc_hash VARCHAR(64) NOT NULL,
            receipt_id BIGINT NOT NULL UNIQUE
                REFERENCES receipts(id) ON DELETE CASCADE,
            status VARCHAR(20) NOT NULL DEFAULT 'RESERVED'
                CHECK (status IN ('RESERVED', 'CONSUMED', 'RELEASED')),
            created_at TIMESTAMP WITH TIME ZONE
                DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_invoice_quota_usages_rfc_hash
        ON invoice_quota_usages(rfc_hash);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_invoice_quota_usages_rfc_hash;")
    op.execute("DROP TABLE IF EXISTS invoice_quota_usages CASCADE;")
