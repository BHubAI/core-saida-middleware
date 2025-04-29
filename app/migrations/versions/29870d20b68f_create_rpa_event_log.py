"""create RPA event log

Revision ID: 29870d20b68f
Revises: cc7c84d4c31b
Create Date: 2025-04-25 22:49:08.544770

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "29870d20b68f"
down_revision = "cc7c84d4c31b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE rpa_event_log_id_seq START WITH 1 INCREMENT BY 1")
    op.create_table(
        "rpa_event_log",
        sa.Column("id", sa.Integer, primary_key=True, server_default=sa.text("nextval('rpa_event_log_id_seq')")),
        sa.Column("process_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("event_data", sa.JSON, nullable=True),
        sa.Column("event_source", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("rpa_event_log")
    op.execute("DROP SEQUENCE rpa_event_log_id_seq")
