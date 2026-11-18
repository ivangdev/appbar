"""payment cancellation audit

Revision ID: af641611f644
Revises: 5b75bd615613
Create Date: 2026-11-17 23:33:32.803136

Anular un pago deja de borrar la fila: se marca `cancelled_at`/`cancelled_by`
para conservar el historial de caja (quien anulo y cuando).
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "af641611f644"
down_revision: Union[str, Sequence[str], None] = "5b75bd615613"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "payments",
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "payments",
        sa.Column("cancelled_by", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_payments_cancelled_by_users",
        "payments",
        "users",
        ["cancelled_by"],
        ["id"],
    )
    op.create_index("ix_payments_cancelled_at", "payments", ["cancelled_at"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_payments_cancelled_at", table_name="payments")
    op.drop_constraint("fk_payments_cancelled_by_users", "payments", type_="foreignkey")
    op.drop_column("payments", "cancelled_by")
    op.drop_column("payments", "cancelled_at")
