from datetime import date, time, timedelta
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models import Campus, CampusMember, Listing, PickupLocation, SellerProfile, Transaction, User
from app.security import hash_password
from app.services.transactions import cancel_transaction, confirm_handoff, schedule_pickup


def make_transaction(db):
    campus = Campus(name="Test Campus", slug="test-campus", city="Pune", state="Maharashtra", pincode="411001", email_domain="")
    buyer = User(name="Buyer", email="buyer@test.local", password_hash=hash_password("StrongPass123!"))
    seller_user = User(name="Seller", email="seller@test.local", password_hash=hash_password("StrongPass123!"))
    seller = SellerProfile(user=seller_user, display_name="Seller")
    db.add_all([campus, buyer, seller_user, seller])
    db.flush()
    db.add(CampusMember(campus_id=campus.id, user_id=buyer.id, student_id_hash="x", verified=True))
    db.add(CampusMember(campus_id=campus.id, user_id=seller_user.id, student_id_hash="y", verified=True))
    location = PickupLocation(campus_id=campus.id, name="Library", address="PTU Library", landmark="Main entrance")
    db.add(location)
    listing = Listing(campus_id=campus.id, seller_id=seller.id, title="Math Book", category="Books", price=Decimal("450"))
    db.add(listing)
    db.flush()
    tx = Transaction(listing_id=listing.id, buyer_id=buyer.id, seller_id=seller_user.id, agreed_price=Decimal("450"), status="paid")
    db.add(tx)
    db.flush()
    return tx, buyer, seller_user, location


def test_handoff_code_is_stable_across_reschedules(db):
    tx, buyer, seller, location = make_transaction(db)
    future = date.today() + timedelta(days=2)
    code = schedule_pickup(db, tx, buyer.id, location.id, None, future, time(17, 30))
    assert len(code) == 4
    first_hash = tx.handoff_code_hash
    new_code = schedule_pickup(db, tx, buyer.id, location.id, None, future + timedelta(days=1), time(18, 0))
    assert new_code == code
    assert tx.handoff_code_hash == first_hash


def test_handoff_cannot_happen_before_scheduled_date(db):
    tx, buyer, seller, location = make_transaction(db)
    schedule_pickup(db, tx, buyer.id, location.id, None, date.today() + timedelta(days=2), time(17, 30))
    with pytest.raises(HTTPException) as exc:
        confirm_handoff(db, tx, seller.id, "0000")
    assert exc.value.status_code == 409


def test_paid_transaction_requires_refund_before_cancel(db):
    tx, buyer, seller, location = make_transaction(db)
    with pytest.raises(HTTPException) as exc:
        cancel_transaction(db, tx, buyer.id)
    assert exc.value.status_code == 409
    assert "refund" in str(exc.value.detail).lower()
