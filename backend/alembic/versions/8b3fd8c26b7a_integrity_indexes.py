"""Add integrity constraints and high-value composite indexes."""
from alembic import op

revision = "8b3fd8c26b7a"
down_revision = "926e207bfe9f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_campus_domain", "campus_domains", ["campus_id", "domain"])
    op.create_unique_constraint("uq_payment_provider_order", "payments", ["provider_order_id"])
    op.create_unique_constraint("uq_payment_provider_payment", "payments", ["provider_payment_id"])
    op.create_check_constraint("ck_offer_amount_nonnegative", "offers", "amount >= 0")
    op.create_check_constraint("ck_transaction_price_nonnegative", "transactions", "agreed_price >= 0")
    op.create_check_constraint("ck_review_rating", "reviews", "rating >= 1 AND rating <= 5")
    op.create_index("ix_offers_listing_status", "offers", ["listing_id", "status"])
    op.create_index("ix_transactions_buyer_status", "transactions", ["buyer_id", "status"])
    op.create_index("ix_transactions_seller_status", "transactions", ["seller_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_transactions_seller_status", table_name="transactions")
    op.drop_index("ix_transactions_buyer_status", table_name="transactions")
    op.drop_index("ix_offers_listing_status", table_name="offers")
    op.drop_constraint("ck_review_rating", "reviews", type_="check")
    op.drop_constraint("ck_transaction_price_nonnegative", "transactions", type_="check")
    op.drop_constraint("ck_offer_amount_nonnegative", "offers", type_="check")
    op.drop_constraint("uq_payment_provider_payment", "payments", type_="unique")
    op.drop_constraint("uq_payment_provider_order", "payments", type_="unique")
    op.drop_constraint("uq_campus_domain", "campus_domains", type_="unique")
