"""Add pickup instructions to listings."""
from alembic import op
import sqlalchemy as sa

revision = "b7d1f67cc9a"
down_revision = "aa92c4d30b88"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("listings", sa.Column("pickup_instructions", sa.String(length=500), nullable=False, server_default=""))

def downgrade() -> None:
    op.drop_column("listings", "pickup_instructions")
