"""Bootstrap the current CampusCart schema.

This baseline is intentionally idempotent so an existing development database created
by earlier CampusCart versions can be adopted by Alembic without destructive changes.
Future schema changes should use normal Alembic op.* migrations.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "926e207bfe9f"
down_revision: Union[str, Sequence[str], None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.db import Base
    import app.models  # noqa: F401
    import app.campus_models  # noqa: F401

    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    # Baseline migrations are non-destructive by design. Use explicit migrations
    # for any future table/column removal.
    pass
