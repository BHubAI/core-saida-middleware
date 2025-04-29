"""create process_event_log

Revision ID: cc7c84d4c31b
Revises: 15f318d0b537
Create Date: 2025-04-09 01:08:51.825121

"""

import sqlalchemy as sa
import sqlmodel
from alembic import op


# revision identifiers, used by Alembic.
revision = "cc7c84d4c31b"
down_revision = "15f318d0b537"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE process_event_log_id_seq START WITH 1 INCREMENT BY 1")
    op.create_table(
        "process_event_log",
        sa.Column("id", sa.Integer, primary_key=True, server_default=sa.text("nextval('process_event_log_id_seq')")),
        sa.Column("process_id", sa.String(length=255), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("event_data", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("process_event_log")
    op.execute("DROP SEQUENCE process_event_log_id_seq")
