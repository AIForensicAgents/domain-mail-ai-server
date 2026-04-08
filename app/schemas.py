from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# Auth
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True


# Domains
class DomainCreate(BaseModel):
    name: str


class DomainOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# Inbound Email Payload
class InboundEmail(BaseModel):
    domain: str
    recipient: EmailStr
    sender: EmailStr
    subject: Optional[str] = None
    text: Optional[str] = None
    html: Optional[str] = None
    message_id: Optional[str] = None
    in_reply_to: Optional[str] = None
    references: Optional[List[str]] = None


class InboundResult(BaseModel):
    status: str
    thread_id: int
    reply_message_id: Optional[int] = None


# Outbound
class OutboundSend(BaseModel):
    from_mailbox: EmailStr
    to: EmailStr
    subject: Optional[str] = None
    text: Optional[str] = None
    html: Optional[str] = None
    thread_id: Optional[int] = None


class OutboundResult(BaseModel):
    status: str
    message_id: int
    thread_id: int
