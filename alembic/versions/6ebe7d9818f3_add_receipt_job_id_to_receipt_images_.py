"""add receipt_job_id to receipt_images, relax receipt_id to nullable

Revision ID: 6ebe7d9818f3
Revises: a1ec0512d09e
Create Date: 2026-06-17 06:14:57.328384

NOTA: receipt_id se vuelve NULLABLE porque las imágenes ahora se insertan
al momento de crear el job (receipt_job_id NOT NULL), antes de que exista
un receipt. receipt_id se rellena (backfill) cuando la extracción
completa con éxito.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6ebe7d9818f3"
down_revision: Union[str, Sequence[str], None] = "a1ec0512d09e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE receipt_images
        ALTER COLUMN receipt_id DROP NOT NULL;
    """)

    op.execute("""
        ALTER TABLE receipt_images
        ADD COLUMN receipt_job_id BIGINT NOT NULL
            REFERENCES receipt_jobs_details(id) ON DELETE CASCADE;
    """)

    op.execute("""
        CREATE INDEX idx_receipt_images_receipt_job_id
        ON receipt_images(receipt_job_id);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_receipt_images_receipt_job_id;")
    op.execute("ALTER TABLE receipt_images DROP COLUMN IF EXISTS receipt_job_id;")
    # op.execute("""
    #     ALTER TABLE receipt_images
    #     ALTER COLUMN receipt_id SET NULL;
    # """)
