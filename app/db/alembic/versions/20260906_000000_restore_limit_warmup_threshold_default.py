"""restore the reset warm-up threshold as an active opt-in default

Revision ID: 20260906_000000_restore_limit_warmup_threshold_default
Revises: 20260830_000000_add_quota_warmup_claim_expiry
Create Date: 2026-09-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

revision = "20260906_000000_restore_limit_warmup_threshold_default"
down_revision = "20260830_000000_add_quota_warmup_claim_expiry"
branch_labels = None
depends_on = None

_COLUMN_NAME = "limit_warmup_exhausted_threshold_percent"
_OLD_DEFAULT = 99.0
_NEW_DEFAULT = 0.0


def _columns(connection: Connection, table_name: str) -> set[str]:
    inspector = sa.inspect(connection)
    if not inspector.has_table(table_name):
        return set()
    return {str(column["name"]) for column in inspector.get_columns(table_name) if column.get("name") is not None}


def upgrade() -> None:
    bind = op.get_bind()
    columns = _columns(bind, "dashboard_settings")
    if _COLUMN_NAME not in columns:
        return

    op.execute(
        sa.text(
            "UPDATE dashboard_settings "
            "SET limit_warmup_exhausted_threshold_percent = :new_default "
            "WHERE limit_warmup_exhausted_threshold_percent = :old_default"
        ).bindparams(new_default=_NEW_DEFAULT, old_default=_OLD_DEFAULT)
    )
    with op.batch_alter_table("dashboard_settings") as batch_op:
        batch_op.alter_column(
            _COLUMN_NAME,
            existing_type=sa.Float(),
            server_default=sa.text(str(_NEW_DEFAULT)),
        )


def downgrade() -> None:
    bind = op.get_bind()
    columns = _columns(bind, "dashboard_settings")
    if _COLUMN_NAME not in columns:
        return

    with op.batch_alter_table("dashboard_settings") as batch_op:
        batch_op.alter_column(
            _COLUMN_NAME,
            existing_type=sa.Float(),
            server_default=sa.text(str(_OLD_DEFAULT)),
        )
