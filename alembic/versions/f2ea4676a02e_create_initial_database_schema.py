"""create initial database schema

Revision ID: f2ea4676a02e
Revises:
Create Date: 2026-06-14 03:06:08.377528

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa # type: ignore

# revision identifiers, used by Alembic.
revision: str = "f2ea4676a02e"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE users (
            id VARCHAR(255) PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)

    op.execute("""
        CREATE TABLE fiscal_info (
            id BIGSERIAL PRIMARY KEY NOT NULL,
            user_id VARCHAR(255) NOT NULL,
            rfc VARCHAR(255) NOT NULL,
            razon_social VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            cp VARCHAR(255) NOT NULL,
            address TEXT NOT NULL,
            CONSTRAINT fiscal_info_user_id_foreign FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """)

    op.execute("""
        CREATE TABLE regimenes (
            id BIGSERIAL PRIMARY KEY NOT NULL,
            fiscal_info BIGINT NOT NULL,
            regimen_code VARCHAR(255) NOT NULL,
            regimen_description VARCHAR(255) NOT NULL,
            fecha_alta DATE NOT NULL,
            CONSTRAINT regimenes_fiscal_info_foreign FOREIGN KEY(fiscal_info) REFERENCES fiscal_info(id)
        );
    """)

    op.execute("""
        CREATE TABLE merchants (
            id BIGSERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            tax_id VARCHAR(50),
            address TEXT,
            branch_id VARCHAR(50),
            phone VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unq_merchant_branch UNIQUE (tax_id, branch_id)
        );
    """)

    op.execute("""
        CREATE TABLE payment_methods (
            code VARCHAR(10) PRIMARY KEY,
            description VARCHAR(100) NOT NULL
        );
    """)

    op.execute("""
        CREATE TABLE receipts (
            id BIGSERIAL PRIMARY KEY,
            user_id VARCHAR(255) REFERENCES users(id) ON DELETE CASCADE, -- podra ser null por ahora (MVP)
            merchant_id BIGINT REFERENCES merchants(id) ON DELETE SET NULL,
            payment_method_code VARCHAR(10) REFERENCES payment_methods(code) ON DELETE SET NULL,
            transaction_date DATE,
            transaction_time TIME,
            ticket_number VARCHAR(100),
            pos_id VARCHAR(50),
            cashier VARCHAR(100),
            subtotal NUMERIC(15, 2),
            total_discount NUMERIC(15, 2) DEFAULT 0.00,
            total NUMERIC(15, 2) NOT NULL,
            amount_paid NUMERIC(15, 2) NOT NULL,
            "change" NUMERIC(15, 2),
            card_last_four VARCHAR(10),
            authorization_code VARCHAR(100),
            context_notes TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)

    op.execute("""
        CREATE TABLE receipt_payments (
            id BIGSERIAL PRIMARY KEY,
            receipt_id BIGINT NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
            payment_method_code VARCHAR(10) NOT NULL REFERENCES payment_methods(code),
            amount NUMERIC(15, 2) NOT NULL,
            card_last_four VARCHAR(10),
            authorization_code VARCHAR(100),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)

    op.execute("""
        CREATE TABLE receipt_billing_details (
            receipt_id BIGINT PRIMARY KEY REFERENCES receipts(id) ON DELETE CASCADE,
            is_billable BOOLEAN DEFAULT FALSE,
            has_qr_code BOOLEAN DEFAULT FALSE,
            billing_url TEXT,
            barcode TEXT,
            billing_code TEXT,
            expiration_date DATE,
            billing_data JSONB,
            extra_metadata JSONB,
            facturagpt_session_id VARCHAR(100),
            billing_status VARCHAR(50) DEFAULT 'NOT_REQUESTED',
            billing_error_code VARCHAR(100),
            billing_error_message TEXT,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)

    op.execute("""
        CREATE TABLE billing_files (
            id BIGSERIAL PRIMARY KEY,
            receipt_id BIGINT NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
            file_type VARCHAR(10),
            file_key VARCHAR(255) NOT NULL,
            file_url TEXT NOT NULL,
            mime_type VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)

    op.execute("""
        CREATE TABLE receipt_items (
            id BIGSERIAL PRIMARY KEY,
            receipt_id BIGINT NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
            quantity FLOAT NOT NULL,
            description VARCHAR(500) NOT NULL,
            sku VARCHAR(100),
            unit_price NUMERIC(15, 2),
            total_price NUMERIC(15, 2) NOT NULL,
            discount NUMERIC(15, 2) DEFAULT 0.00,
            item_metadata JSONB
        );
    """)

    op.execute("""
        CREATE TABLE receipt_taxes (
            id BIGSERIAL PRIMARY KEY,
            receipt_id BIGINT NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
            tax_name VARCHAR(50) NOT NULL,
            tax_rate NUMERIC(5, 2),
            amount NUMERIC(15, 2) NOT NULL
        );
    """)

    op.execute("""
        CREATE TABLE receipt_images (
            id BIGSERIAL PRIMARY KEY,
            receipt_id BIGINT NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
            file_key VARCHAR(255) NOT NULL,
            file_url TEXT NOT NULL,
            mime_type VARCHAR(50) DEFAULT 'image/jpeg',
            page_number INT DEFAULT 1,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)

    op.execute("""
        CREATE TABLE facturagpt_webhooks (
            idempotency_key VARCHAR(255) PRIMARY KEY,
            event_type VARCHAR(50) NOT NULL,
            session_id VARCHAR(100) NOT NULL,
            payload JSONB NOT NULL,
            processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)

    op.execute("""
        CREATE TABLE billing_attempts (
            id BIGSERIAL PRIMARY KEY,
            receipt_id BIGINT NOT NULL REFERENCES receipts(id) ON DELETE CASCADE,
            session_id VARCHAR(100),
            status VARCHAR(50) NOT NULL,
            attempted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            error_code VARCHAR(100),
            error_message TEXT,
            response_payload JSONB
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS billing_attempts CASCADE;")
    op.execute("DROP TABLE IF EXISTS receipt_images CASCADE;")
    op.execute("DROP TABLE IF EXISTS receipt_taxes CASCADE;")
    op.execute("DROP TABLE IF EXISTS receipt_items CASCADE;")
    op.execute("DROP TABLE IF EXISTS billing_files CASCADE;")
    op.execute("DROP TABLE IF EXISTS receipt_billing_details CASCADE;")
    op.execute("DROP TABLE IF EXISTS receipt_payments CASCADE;")
    op.execute("DROP TABLE IF EXISTS receipts CASCADE;")
    op.execute("DROP TABLE IF EXISTS facturagpt_webhooks CASCADE;")
    op.execute("DROP TABLE IF EXISTS merchants CASCADE;")
    op.execute("DROP TABLE IF EXISTS regimenes CASCADE;")
    op.execute("DROP TABLE IF EXISTS fiscal_info CASCADE;")
    op.execute("DROP TABLE IF EXISTS payment_methods CASCADE;")
    op.execute("DROP TABLE IF EXISTS users CASCADE;")
