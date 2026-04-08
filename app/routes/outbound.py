from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas import OutboundSend, OutboundResult
from ..token_utils import get_current_user
from ..models import User, Domain, Mailbox, Thread
from ..config import settings
from ..mail_service import mail_service

router = APIRouter()


@router.post("/send", response_model=OutboundResult)
def send_email(payload: OutboundSend, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Validate sender mailbox belongs to a registered domain owned by the user
    from_domain = payload.from_mailbox.split("@")[-1].lower()
    domain = db.query(Domain).filter(Domain.name == from_domain, Domain.owner_id == current_user.id).first()
    if not domain:
        raise HTTPException(status_code=403, detail="You do not own this domain")

    mailbox = db.query(Mailbox).filter(Mailbox.full_address == payload.from_mailbox.lower(), Mailbox.domain_id == domain.id).first()
    if not mailbox:
        # auto-create outbound mailbox for convenience
        mailbox = mail_service.ensure_mailbox(db, domain, payload.from_mailbox)

    # Determine thread
    if payload.thread_id:
        thread = db.query(Thread).filter(Thread.id == payload.thread_id, Thread.mailbox_id == mailbox.id).first()
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found for this mailbox")
    else:
        thread = Thread(mailbox_id=mailbox.id, subject=payload.subject or "", counterpart=str(payload.to).lower())
        db.add(thread)
        db.commit()
        db.refresh(thread)

    # Compose and send
    from_addr = mailbox.full_address
    reply_to = None
    if settings.DELEGATED_EMAIL:
        reply_to = mailbox.full_address
        from_addr = settings.DELEGATED_EMAIL

    em = mail_service._compose_email(
        from_addr=from_addr,
        to_addr=str(payload.to).lower(),
        subject=payload.subject or thread.subject or "",
        text=payload.text,
        html=payload.html,
        reply_to=reply_to,
    )
    mail_service._smtp_send(em)

    # Persist outbound message
    msg = mail_service.store_outbound(
        db=db,
        thread=thread,
        from_addr=from_addr,
        to_addr=str(payload.to).lower(),
        subject=em.get("Subject"),
        text=payload.text,
        html=payload.html,
    )

    return OutboundResult(status="sent", message_id=msg.id, thread_id=thread.id)
