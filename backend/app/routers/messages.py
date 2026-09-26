from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import current_user, require_verified_member
from app.models import Campus, Conversation, Listing, Message, User
from app.schemas import ConversationCreateIn, MessageCreateIn
from app.services.notifications import create_notification
from app.services.rate_limit import check_message_rate

router = APIRouter(prefix="/api/messages", tags=["messages"])


def is_participant(c: Conversation, user_id: int):
    return user_id in {c.buyer_id, c.seller_id}


def conv_out(c: Conversation, db: Session):
    listing = db.get(Listing, c.listing_id)
    buyer = db.get(User, c.buyer_id)
    seller = db.get(User, c.seller_id)
    return {
        "id": c.id,
        "listing_id": c.listing_id,
        "buyer_id": c.buyer_id,
        "seller_id": c.seller_id,
        "buyer_name": buyer.name if buyer else None,
        "seller_name": seller.name if seller else None,
        "listing_title": listing.title if listing else None,
        "transaction_id": c.transaction_id,
        "blocked": c.blocked,
        "last_message_at": c.last_message_at,
        "created_at": c.created_at,
    }


def msg_out(m: Message):
    return {
        "id": m.id,
        "conversation_id": m.conversation_id,
        "sender_id": m.sender_id,
        "body": m.body,
        "read_at": m.read_at,
        "created_at": m.created_at,
    }


@router.post("/conversations")
def create_conversation(data: ConversationCreateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    listing = db.get(Listing, data.listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    campus = db.get(Campus, listing.campus_id)
    if not campus:
        raise HTTPException(404, "Campus not found")
    require_verified_member(campus.slug, user, db)
    seller_id = listing.seller.user_id
    if user.id == seller_id:
        raise HTTPException(400, "You cannot message yourself")

    conversation = db.scalar(
        select(Conversation).where(
            Conversation.listing_id == listing.id,
            Conversation.buyer_id == user.id,
            Conversation.seller_id == seller_id,
        )
    )
    if not conversation:
        conversation = Conversation(
            listing_id=listing.id,
            buyer_id=user.id,
            seller_id=seller_id,
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
    return conv_out(conversation, db)


@router.get("/conversations")
def list_conversations(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Conversation)
        .where(or_(Conversation.buyer_id == user.id, Conversation.seller_id == user.id))
        .order_by(desc(Conversation.last_message_at), desc(Conversation.created_at))
    ).all()
    return [conv_out(row, db) for row in rows]


@router.get("/conversations/{conversation_id}")
def conversation_detail(conversation_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if not conversation or not is_participant(conversation, user.id):
        raise HTTPException(404, "Conversation not found")

    messages = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
    ).all()

    db.query(Message).filter(
        Message.conversation_id == conversation.id,
        Message.sender_id != user.id,
        Message.read_at.is_(None),
    ).update({Message.read_at: datetime.utcnow()}, synchronize_session=False)
    db.commit()
    return {"conversation": conv_out(conversation, db), "messages": [msg_out(m) for m in messages]}


@router.post("/conversations/{conversation_id}/messages")
def send_message(conversation_id: int, data: MessageCreateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    try:
        check_message_rate(user.id)
    except ValueError as exc:
        raise HTTPException(429, str(exc)) from exc

    conversation = db.get(Conversation, conversation_id)
    if not conversation or not is_participant(conversation, user.id):
        raise HTTPException(404, "Conversation not found")
    if conversation.blocked:
        raise HTTPException(403, "Conversation is blocked")

    body = data.body.strip()
    if not body:
        raise HTTPException(400, "Message cannot be empty")

    message = Message(conversation_id=conversation.id, sender_id=user.id, body=body)
    db.add(message)
    conversation.last_message_at = datetime.utcnow()
    receiver_id = conversation.seller_id if user.id == conversation.buyer_id else conversation.buyer_id
    create_notification(
        db,
        receiver_id,
        "message",
        "New message",
        body[:160],
        f"/messages?conversation={conversation.id}",
    )
    db.commit()
    db.refresh(message)
    return msg_out(message)


@router.post("/conversations/{conversation_id}/block")
def block_conversation(conversation_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    conversation = db.get(Conversation, conversation_id)
    if not conversation or not is_participant(conversation, user.id):
        raise HTTPException(404, "Conversation not found")
    conversation.blocked = True
    db.commit()
    return {"blocked": True}
