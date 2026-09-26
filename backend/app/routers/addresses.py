
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session
from app.db import get_db
from app.deps import current_user
from app.models import Address, User
from app.schemas import AddressIn

router = APIRouter(prefix="/api/addresses", tags=["addresses"])

def out(a: Address):
    return {"id": a.id, "label": a.label, "line1": a.line1, "line2": a.line2, "locality": a.locality, "city": a.city,
            "state": a.state, "pincode": a.pincode, "landmark": a.landmark, "is_default": a.is_default}

@router.get("")
def list_addresses(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [out(a) for a in db.scalars(select(Address).where(Address.user_id == user.id).order_by(Address.is_default.desc(), Address.created_at.desc())).all()]

@router.post("")
def add_address(data: AddressIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    if data.is_default:
        db.query(Address).filter(Address.user_id == user.id).update({Address.is_default: False})
    address = Address(user_id=user.id, **data.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return out(address)

@router.patch("/{address_id}")
def edit_address(address_id: int, data: AddressIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    address = db.get(Address, address_id)
    if not address or address.user_id != user.id:
        raise HTTPException(404, "Address not found")
    if data.is_default:
        db.query(Address).filter(Address.user_id == user.id).update({Address.is_default: False})
    for k, v in data.model_dump().items():
        setattr(address, k, v)
    db.commit()
    return out(address)

@router.delete("/{address_id}")
def delete_address(address_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    address = db.get(Address, address_id)
    if not address or address.user_id != user.id:
        raise HTTPException(404, "Address not found")
    db.delete(address)
    db.commit()
    return {"ok": True}
