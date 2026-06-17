"""seed sat codes in payment_methods table

Revision ID: 9b692df66236
Revises: f2ea4676a02e
Create Date: 2026-06-14 03:44:18.032313

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa  # type: ignore

# revision identifiers, used by Alembic.
revision: str = "9b692df66236"
down_revision: Union[str, Sequence[str], None] = "f2ea4676a02e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
            INSERT INTO payment_methods (code, description) VALUES
            ('01', 'Efectivo'),
            ('02', 'Cheque nominativo'),
            ('03', 'Transferencia electrónica de fondos'),
            ('04', 'Tarjeta de crédito'),
            ('05', 'Monedero electrónico'),
            ('06', 'Dinero electrónico'),
            ('08', 'Vales de despensa'),
            ('12', 'Dación en pago'),
            ('13', 'Pago por subrogación'),
            ('14', 'Pago por consignación'),
            ('15', 'Condonación'),
            ('17', 'Compensación'),
            ('23', 'Novación'),
            ('24', 'Confusión'),
            ('25', 'Remisión de deuda'),
            ('26', 'Prescripción o caducidad'),
            ('27', 'A satisfacción del acreedor'),
            ('28', 'Tarjeta de débito'),
            ('29', 'Tarjeta de servicios'),
            ('30', 'Aplicación de anticipos'),
            ('99', 'Por definir')
            ON CONFLICT (code) DO NOTHING;
        """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM receipt_payments 
        WHERE payment_method_code IN (
            '01', '02', '03', '04', '05', '06', '08', '12', '13', '14', 
            '15', '17', '23', '24', '25', '26', '27', '28', '29', '30', '99'
        );
    """)
    op.execute("""
        DELETE FROM payment_methods 
        WHERE code IN (
            '01', '02', '03', '04', '05', '06', '08', '12', '13', '14', 
            '15', '17', '23', '24', '25', '26', '27', '28', '29', '30', '99'
        );
    """)
