from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import enum


class MessageDirection(str, enum.Enum):
    inbound = "in"
    outbound = "out"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    domains = relationship("Domain", back_populates="owner")


class Domain(Base):
    __tablename__ = "domains"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="domains")
    mailboxes = relationship("Mailbox", back_populates="domain")


class Mailbox(Base):
    __tablename__ = "mailboxes"

    id = Column(Integer, primary_key=True, index=True)
    local_part = Column(String(255), nullable=False)
    full_address = Column(String(512), unique=True, index=True, nullable=False)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    domain = relationship("Domain", back_populates="mailboxes")
    threads = relationship("Thread", back_populates="mailbox")


class Thread(Base):
    __tablename__ = "threads"

    id = Column(Integer, primary_key=True, index=True)
    mailbox_id = Column(Integer, ForeignKey("mailboxes.id"), nullable=False)
    subject = Column(String(512), nullable=True)
    counterpart = Column(String(512), nullable=True)  # primary external participant (e.g., sender)
    references_header = Column(Text, nullable=True)   # raw References/In-Reply-To aggregation
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    mailbox = relationship("Mailbox", back_populates="threads")
    messages = relationship("Message", back_populates="thread", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("threads.id"), nullable=False, index=True)

    direction = Column(Enum(MessageDirection), nullable=False)

    from_addr = Column(String(512), nullable=False)
    to_addr = Column(String(1024), nullable=False)
    subject = Column(String(512), nullable=True)

    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)

    raw_headers = Column(Text, nullable=True)
    message_id = Column(String(255), nullable=True, index=True)
    in_reply_to = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    thread = relationship("Thread", back_populates="messages")


Index("idx_thread_created", Message.thread_id, Message.created_at)
