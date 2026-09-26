
from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import current_user
from app.models import Campus, InteractionEvent, Listing, User
from app.services.demand import price_insight
from app.schemas import ListingCreateIn

router = APIRouter(prefix="/api/listing-tools", tags=["listing-tools"])

@router.post("/copilot")
def copilot(data: dict, user: User = Depends(current_user), db: Session = Depends(get_db)):
    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()
    category = str(data.get("category", "")).strip()
    condition = str(data.get("condition", "")).strip().lower() or "good"
    text = f"{title} {description}".lower()

    suggestions = {
        "books": ["book", "textbook", "notes", "manual", "novel"],
        "electronics": ["phone", "laptop", "monitor", "calculator", "earbud", "keyboard", "mouse"],
        "hostel essentials": ["chair", "table", "lamp", "mattress", "storage", "extension"],
        "clothing": ["coat", "jacket", "shirt", "jeans", "hoodie"],
        "sports": ["football", "basketball", "bat", "racket", "sports"],
    }
    detected_category = category
    if not detected_category:
        for name, words in suggestions.items():
            if any(word in text for word in words):
                detected_category = name.title()
                break
    detected_category = detected_category or "Other"
    suggested_title = title
    if not suggested_title:
        suggested_title = {
            "Books": "Student Textbook",
            "Electronics": "Used Electronics",
            "Academic Supplies": "Academic Supply",
            "Hostel Essentials": "Hostel Essential",
            "Clothing": "Student Clothing",
            "Sports": "Sports Equipment",
        }.get(detected_category, "Campus Listing")
    suggested_title = suggested_title[:180]
    notes = []
    if "working" in text or "works" in text:
        notes.append("working condition mentioned")
    if "negot" in text:
        notes.append("price negotiable")
    if "new" in condition:
        notes.append("new-condition listing")
    return {
        "suggested_title": suggested_title,
        "category": detected_category,
        "condition": condition,
        "detected_attributes": notes,
        "description_cleanup": description.strip(),
        "assistant_note": "Review and edit these suggestions before publishing.",
    }

@router.get("/semester")
def semester(campus_slug: str, db: Session = Depends(get_db)):
    campus = db.scalar(select(Campus).where(Campus.slug == campus_slug))
    if not campus:
        return {"error": "Campus not found"}
    return {
        "campus_slug": campus.slug,
        "current_semester": campus.current_semester,
        "semester_start": campus.semester_start,
        "semester_end": campus.semester_end,
        "guidance": "CampusCart uses semester context in recommendations and demand insights.",
    }

@router.post("/track")
def track(event_type: str, campus_slug: str = "", listing_id: int | None = None, category: str = "",
          query: str = "", user: User | None = Depends(current_user), db: Session = Depends(get_db)):
    campus = db.scalar(select(Campus).where(Campus.slug == campus_slug)) if campus_slug else None
    db.add(InteractionEvent(
        user_id=user.id if user else None,
        campus_id=campus.id if campus else None,
        listing_id=listing_id,
        event_type=event_type,
        category=category,
        query=query,
    ))
    db.commit()
    return {"recorded": True}
