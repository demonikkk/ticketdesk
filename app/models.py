from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


def now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(100), nullable=False)
    role = Column(String(20), default="user", nullable=False)


class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True)
    title = Column(String(120), nullable=False)
    description = Column(Text, default="")
    priority = Column(String(10), default="Medium", nullable=False)
    status = Column(String(20), default="Open", nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=now)
    creator = relationship("User")
    attachments = relationship("Attachment", back_populates="ticket", cascade="all, delete-orphan")


class Attachment(Base):
    __tablename__ = "attachments"
    id = Column(Integer, primary_key=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    s3_key = Column(String(512), nullable=False)
    content_type = Column(String(100))
    uploaded_at = Column(DateTime, default=now)
    ticket = relationship("Ticket", back_populates="attachments")
