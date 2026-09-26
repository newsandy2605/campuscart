"""add lost found claim message

Revision ID: d7b7e1c6d1f7
Revises: c21d0baf4f8c
"""
from alembic import op
import sqlalchemy as sa

revision = "d7b7e1c6d1f7"
down_revision = "c21d0baf4f8c"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("lost_found_items", sa.Column("claim_message", sa.Text(), nullable=False, server_default=""))

def downgrade():
    op.drop_column("lost_found_items", "claim_message")
