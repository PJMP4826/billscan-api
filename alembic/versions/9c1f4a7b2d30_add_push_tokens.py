"""add_push_tokens

Revision ID: 9c1f4a7b2d30
Revises: b7e4c9a1f2d3
Create Date: 2026-11-26

Persiste los tokens de notificación de Expo por dispositivo. ``token`` es
UNIQUE global para que un mismo dispositivo pueda cambiar de usuario (gana el
último login) y para que el registro sea idempotente vía ``ON CONFLICT``.
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9c1f4a7b2d30"
down_revision: Union[str, Sequence[str], None] = "b7e4c9a1f2d3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE push_tokens (
            id BIGSERIAL PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            token VARCHAR(255) NOT NULL,
            platform VARCHAR(16) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE
                DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE
                DEFAULT CURRENT_TIMESTAMP NOT NULL,
            CONSTRAINT push_tokens_user_id_foreign
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            CONSTRAINT push_tokens_token_unique UNIQUE (token),
            CONSTRAINT push_tokens_platform_check
                CHECK (platform IN ('android', 'ios'))
        );
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_push_tokens_user_id
        ON push_tokens(user_id);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_push_tokens_user_id;")
    op.execute("DROP TABLE IF EXISTS push_tokens CASCADE;")
