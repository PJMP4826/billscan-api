"""create receipt_jobs_details table

Revision ID: a1ec0512d09e
Revises: d9f1e59840b1
Create Date: 2026-06-17 06:05:47.672282

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1ec0512d09e"
down_revision: Union[str, Sequence[str], None] = "d9f1e59840b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE receipt_jobs_details (
            id BIGSERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            job_name VARCHAR(255) NOT NULL,
            status TEXT NOT NULL
                CONSTRAINT chk_receipt_jobs_status
                CHECK (status IN ('RECEIVED', 'EXTRACTING', 'COMPLETED', 'FAILED'))
                DEFAULT 'RECEIVED',
            error_message TEXT,
            receipt_id BIGINT REFERENCES receipts(id) ON DELETE SET NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
        );
    """)

    op.execute("""
        CREATE INDEX idx_receipt_jobs_user_id ON receipt_jobs_details(user_id);
    """)

    op.execute("""
        CREATE INDEX idx_receipt_jobs_status ON receipt_jobs_details(status);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_receipt_jobs_status;")
    op.execute("DROP INDEX IF EXISTS idx_receipt_jobs_user_id;")
    op.execute("DROP TABLE IF EXISTS receipt_jobs_details CASCADE;")
