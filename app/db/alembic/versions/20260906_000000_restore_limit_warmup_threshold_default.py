"""restore the reset warm-up threshold as an active opt-in default

Revision ID: 20260906_000000_restore_limit_warmup_threshold_default
Revises: 20260908_020000_merge_overflow_transport_heads
Create Date: 2026-09-06
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.engine import Connection

revision = "20260906_000000_restore_limit_warmup_threshold_default"
down_revision = "20260908_020000_merge_overflow_transport_heads"
branch_labels = None
depends_on = None

_LEGACY_COLUMN_NAME = "limit_warmup_exhausted_threshold_percent"
_ACTIVE_COLUMN_NAME = "limit_warmup_reset_threshold_percent"
_OLD_DEFAULT = 99.0
_NEW_DEFAULT = 0.0
_PRISTINE_SETTINGS_VERSION = 1
_SYNC_TRIGGER_NAME = "trg_dashboard_settings_limit_warmup_threshold_legacy_sync"
_SYNC_FUNCTION_NAME = "sync_dashboard_settings_limit_warmup_threshold_legacy"


def _columns(connection: Connection, table_name: str) -> set[str]:
    inspector = sa.inspect(connection)
    if not inspector.has_table(table_name):
        return set()
    return {str(column["name"]) for column in inspector.get_columns(table_name) if column.get("name") is not None}


def _create_legacy_sync_trigger(connection: Connection) -> None:
    if connection.dialect.name == "sqlite":
        op.execute(
            sa.text(
                f"""
                CREATE TRIGGER {_SYNC_TRIGGER_NAME}
                AFTER UPDATE OF {_LEGACY_COLUMN_NAME} ON dashboard_settings
                FOR EACH ROW
                WHEN NEW.{_LEGACY_COLUMN_NAME} != OLD.{_LEGACY_COLUMN_NAME}
                 AND NEW.{_ACTIVE_COLUMN_NAME} = OLD.{_ACTIVE_COLUMN_NAME}
                BEGIN
                    UPDATE dashboard_settings
                    SET {_ACTIVE_COLUMN_NAME} = NEW.{_LEGACY_COLUMN_NAME}
                    WHERE id = NEW.id;
                END
                """
            )
        )
        return

    if connection.dialect.name == "postgresql":
        op.execute(
            sa.text(
                f"""
                CREATE FUNCTION {_SYNC_FUNCTION_NAME}()
                RETURNS trigger AS $$
                BEGIN
                    IF NEW.{_LEGACY_COLUMN_NAME} IS DISTINCT FROM OLD.{_LEGACY_COLUMN_NAME}
                       AND NEW.{_ACTIVE_COLUMN_NAME} IS NOT DISTINCT FROM OLD.{_ACTIVE_COLUMN_NAME} THEN
                        NEW.{_ACTIVE_COLUMN_NAME} := NEW.{_LEGACY_COLUMN_NAME};
                    END IF;
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql
                """
            )
        )
        op.execute(
            sa.text(
                f"""
                CREATE TRIGGER {_SYNC_TRIGGER_NAME}
                BEFORE UPDATE OF {_LEGACY_COLUMN_NAME} ON dashboard_settings
                FOR EACH ROW
                EXECUTE FUNCTION {_SYNC_FUNCTION_NAME}()
                """
            )
        )


def _drop_legacy_sync_trigger(connection: Connection) -> None:
    if connection.dialect.name == "sqlite":
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS {_SYNC_TRIGGER_NAME}"))
        return

    if connection.dialect.name == "postgresql":
        op.execute(sa.text(f"DROP TRIGGER IF EXISTS {_SYNC_TRIGGER_NAME} ON dashboard_settings"))
        op.execute(sa.text(f"DROP FUNCTION IF EXISTS {_SYNC_FUNCTION_NAME}()"))


def upgrade() -> None:
    bind = op.get_bind()
    columns = _columns(bind, "dashboard_settings")
    if _LEGACY_COLUMN_NAME not in columns or _ACTIVE_COLUMN_NAME in columns:
        return

    with op.batch_alter_table("dashboard_settings") as batch_op:
        batch_op.add_column(
            sa.Column(
                _ACTIVE_COLUMN_NAME,
                sa.Float(),
                nullable=False,
                server_default=sa.text(str(_NEW_DEFAULT)),
            )
        )

    op.execute(
        sa.text(
            "UPDATE dashboard_settings "
            "SET limit_warmup_reset_threshold_percent = "
            "CASE WHEN limit_warmup_exhausted_threshold_percent = :old_default "
            "AND version = :pristine_version "
            "AND created_at = updated_at "
            "THEN :new_default ELSE limit_warmup_exhausted_threshold_percent END"
        ).bindparams(
            new_default=_NEW_DEFAULT,
            old_default=_OLD_DEFAULT,
            pristine_version=_PRISTINE_SETTINGS_VERSION,
        )
    )
    _create_legacy_sync_trigger(bind)


def downgrade() -> None:
    bind = op.get_bind()
    columns = _columns(bind, "dashboard_settings")
    if _ACTIVE_COLUMN_NAME not in columns:
        return

    _drop_legacy_sync_trigger(bind)
    op.execute(
        sa.text(
            "UPDATE dashboard_settings "
            "SET limit_warmup_exhausted_threshold_percent = "
            "CASE WHEN limit_warmup_reset_threshold_percent = :new_default "
            "THEN :old_default ELSE limit_warmup_reset_threshold_percent END"
        ).bindparams(new_default=_NEW_DEFAULT, old_default=_OLD_DEFAULT)
    )

    with op.batch_alter_table("dashboard_settings") as batch_op:
        batch_op.drop_column(_ACTIVE_COLUMN_NAME)
