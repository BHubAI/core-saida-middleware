"""create obrigacoeshistorico

Revision ID: 4465531d1a31
Revises: 29870d20b68f
Create Date: 2025-06-10 23:06:05.968478

"""
import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '4465531d1a31'
down_revision = '29870d20b68f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE historico_obrigacoes_id_seq START WITH 1 INCREMENT BY 1")
    op.create_table(
        "historico_obrigacoes",
        sa.Column("id", sa.Integer, primary_key=True, server_default=sa.text("nextval('historico_obrigacoes_id_seq')")),
        sa.Column("cnpj", sa.String(length=55), nullable=False),
        sa.Column("competencia", sa.DateTime(timezone=True), nullable=False),
        sa.Column("tipo_obrigacao", sa.String(length=255), nullable=False),
        sa.Column("valor", sa.Float, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("historico_obrigacoes")
    op.execute("DROP SEQUENCE historico_obrigacoes_id_seq")
