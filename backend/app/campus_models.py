from __future__ import annotations
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class CampusDomain(Base):
    __tablename__ = "campus_domains"
    __table_args__ = (UniqueConstraint("campus_id", "domain", name="uq_campus_domain"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campus_id: Mapped[int] = mapped_column(
        ForeignKey("campuses.id", ondelete="CASCADE"), index=True
    )
    domain: Mapped[str] = mapped_column(String(120), index=True)
    active: Mapped[bool] = mapped_column(default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

