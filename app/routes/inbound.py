from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import InboundEmail, InboundResult
from ..config import settings
from ..domain_service import get_domain_by_name
from ..mail_service import mail_service

router = APIRouter()


@router.post("/email", response_model=InboundResult)
def inbound_email(payload: InboundEmail, db: Session = Depends(get_db), x_webhook_token: str = Header(default="")):
    # Authenticate inbound webhook
    if x_webhook_token != settings.INBOUND_API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid webhook token")

    domain = get_domain_by_name(db, payload.domain)
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not registered")

    # Ensure mailbox exists (dynamic create on first inbound)
    mailbox = mail_service.ensure_mailbox(db, domain, payload.recipient)

    # Build reference headers
    refs = []
    if payload.references:
        refs.extend(payload.references)
    if payload.in_reply_to:
        refs.append(payload.in_reply_to)
    references_header = " ".join(refs) if refs else None

    # Find or create a thread
    thread = mail_service._find_or_create_thread(db, mailbox, payload.subject or "", payload.sender, references_header)

    # Store inbound message
    inbound_msg = mail_service.store_inbound(
        db=db,
        thread=thread,
        sender=payload.sender,
        recipient=payload.recipient,
        subject=payload.subject,
        text=payload.text,
        html=payload.html,
        message_id=payload.message_id,
        in_reply_to=payload.in_reply_to,
        raw_headers=references_header,
    )

    # Update thread subject and references if empty
    if not thread.subject and payload.subject:
        thread.subject = payload.subject
    if references_header and (not thread.references_header or references_header not in thread.references_header):
        thread.references_header = ((thread.references_header or "") + " " + references_header).strip()
    db.add(thread)
    db.commit()

    # Generate and send auto-reply
    outbound_msg = mail_service.auto_reply(
        db=db,
        thread=thread,
        mailbox_addr=mailbox.full_address,
        sender=payload.sender,
        last_inbound_message=inbound_msg,
    )

    return InboundResult(status="ok", thread_id=thread.id, reply_message_id=outbound_msg.id)
