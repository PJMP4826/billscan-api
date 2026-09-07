"""remove_file_url_and_add_unique_file_type_to_billing_files

Revision ID: 2d944ffc2411
Revises: bcd486fffeb1
Create Date: 2026-09-06

Ajustes en `billing_files` para el flujo de webhooks de FacturaGPT:

- Se ELIMINA `file_url`: los archivos se referencian únicamente por su
  `file_key` en el storage (nada en el código inserta o lee `file_url`).
- Índice único parcial `(receipt_id, file_type)` para garantizar a nivel BD
  que solo exista un XML y un PDF por receipt: el worker de webhooks
  pre-chequea, pero esto cierra la carrera de dos entregas duplicadas
  concurrentes del webhook (idempotencia).
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2d944ffc2411"
down_revision: Union[str, Sequence[str], None] = "bcd486fffeb1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ningún código inserta ni lee file_url (solo file_key). Antes de dropear,
    # si existieran duplicados (receipt_id, file_type) el índice fallaría;
    # por eso se crea con IF NOT EXISTS y se asume datos limpios.
    op.execute("ALTER TABLE billing_files DROP COLUMN IF EXISTS file_url;")

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_billing_files_receipt_file_type
        ON billing_files (receipt_id, file_type)
        WHERE file_type IS NOT NULL;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_billing_files_receipt_file_type;")

    # Se restaura file_url como NULLABLE: la columna original era NOT NULL,
    # pero las filas creadas después del drop no tienen valor que rellenar.
    op.execute("""
        ALTER TABLE billing_files
        ADD COLUMN IF NOT EXISTS file_url TEXT;
    """)
