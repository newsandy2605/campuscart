"""Add campus verification review fields and lost-found claimant tracking."""
from alembic import op
import sqlalchemy as sa

revision = "c21d0baf4f8c"
down_revision = "b7d1f67cc9a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("swap_offer_id", sa.Integer(), nullable=True))
    op.create_unique_constraint("uq_transaction_swap_offer", "transactions", ["swap_offer_id"])
    op.create_index("ix_transactions_swap_offer_id", "transactions", ["swap_offer_id"])
    op.create_foreign_key("fk_transactions_swap_offer_id_swap_offers", "transactions", "swap_offers", ["swap_offer_id"], ["id"], ondelete="SET NULL")
    op.add_column("lost_found_items", sa.Column("claimant_id", sa.Integer(), nullable=True))
    op.add_column("lost_found_items", sa.Column("claimed_at", sa.DateTime(), nullable=True))
    op.add_column("lost_found_items", sa.Column("resolved_at", sa.DateTime(), nullable=True))
    op.create_index("ix_lost_found_items_claimant_id", "lost_found_items", ["claimant_id"])
    op.create_foreign_key(
        "fk_lost_found_items_claimant_id_users",
        "lost_found_items",
        "users",
        ["claimant_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_transactions_swap_offer_id_swap_offers", "transactions", type_="foreignkey")
    op.drop_index("ix_transactions_swap_offer_id", table_name="transactions")
    op.drop_constraint("uq_transaction_swap_offer", "transactions", type_="unique")
    op.drop_column("transactions", "swap_offer_id")
    op.drop_constraint("fk_lost_found_items_claimant_id_users", "lost_found_items", type_="foreignkey")
    op.drop_index("ix_lost_found_items_claimant_id", table_name="lost_found_items")
    op.drop_column("lost_found_items", "resolved_at")
    op.drop_column("lost_found_items", "claimed_at")
    op.drop_column("lost_found_items", "claimant_id")
