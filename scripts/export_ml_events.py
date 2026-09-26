"""Export interaction_events to JSONL for offline recommendation evaluation."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import InteractionEvent


def main() -> None:
    out = Path(os.getenv("ML_EVENTS_OUT", "ml_data/interaction_events.jsonl"))
    out.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(settings.database_url)
    with Session(engine) as db, out.open("w", encoding="utf-8") as f:
        for event in db.scalars(select(InteractionEvent).order_by(InteractionEvent.created_at)).yield_per(1000):
            row = {
                "user_id": event.user_id,
                "campus_id": event.campus_id,
                "listing_id": event.listing_id,
                "event_type": event.event_type,
                "category": event.category,
                "query": event.query,
                "created_at": event.created_at.isoformat() if event.created_at else None,
            }
            f.write(json.dumps(row) + "\n")
    print(out)


if __name__ == "__main__":
    main()
