"""init

Revision ID: 0001_init
Revises: None
Create Date: 2026-03-08 00:00:00
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "link",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("target_url", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("clicks", sa.Integer(), nullable=False),
        sa.Column("is_blocked", sa.Boolean(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("max_clicks", sa.Integer(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_link_code"), "link", ["code"], unique=True)
    op.create_index(op.f("ix_link_deleted_at"), "link", ["deleted_at"], unique=False)

    op.create_table(
        "clickevent",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("link_id", sa.Integer(), nullable=False),
        sa.Column("clicked_at", sa.DateTime(), nullable=False),
        sa.Column("ip", sa.String(), nullable=True),
        sa.Column("user_agent", sa.String(), nullable=True),
        sa.Column("referrer", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["link_id"], ["link.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clickevent_clicked_at"), "clickevent", ["clicked_at"], unique=False)
    op.create_index(op.f("ix_clickevent_link_id"), "clickevent", ["link_id"], unique=False)

    op.create_table(
        "apikey",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_apikey_key"), "apikey", ["key"], unique=True)


def downgrade():
    op.drop_index(op.f("ix_apikey_key"), table_name="apikey")
    op.drop_table("apikey")

    op.drop_index(op.f("ix_clickevent_link_id"), table_name="clickevent")
    op.drop_index(op.f("ix_clickevent_clicked_at"), table_name="clickevent")
    op.drop_table("clickevent")

    op.drop_index(op.f("ix_link_deleted_at"), table_name="link")
    op.drop_index(op.f("ix_link_code"), table_name="link")
    op.drop_table("link")