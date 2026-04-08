from sqlalchemy.orm import Session
from fastapi import HTTPException
from email.utils import formataddr, make_msgid
from email.message import EmailMessage
import smtplib
import ssl
from datetime import datetime
from .models import Domain, Mailbox, Thread, Message, MessageDirection
from .config import settings
from .ai_service import AIReplyService
from .history_service import build_chat_history_for_thread


class MailService:
    def __init__(self):
        self.ai = AIReplyService()

    def ensure_mailbox(self, db: Session, domain: Domain, recipient: str) -> Mailbox:
        local_part = recipient.split("@")[0].lower()
        full_address = f"{local_part}@{domain.name}"
        m = db.query(Mailbox).filter(Mailbox.full_address == full_address).first()
        if m:
            return m
        m = Mailbox(local_part=local_part, full_address=full_address, domain_id=domain.id)
        db.add(m)
        db.commit()
        db.refresh(m)
        return m

    def _find_or_create_thread(self, db: Session, mailbox: Mailbox, subject: str | None, sender: str, references: str | None) -> Thread:
        # Heuristic: find latest thread for mailbox + counterpart + similar subject
        q = db.query(Thread).filter(
            Thread.mailbox_id == mailbox.id,
            Thread.counterpart == sender
        ).order_by(Thread.updated_at.desc())
        t = None
        for cand in q.limit(5):
            # Very lightweight subject check
            if (not subject) or (not cand.subject) or (subject.strip().lower() in cand.subject.strip().lower()) or (cand.subject.strip().lower() in subject.strip().lower()):
                t = cand
                break
        if not t:
            t = Thread(mailbox_id=mailbox.id, subject=subject or "", counterpart=sender, references_header=references or "")
            db.add(t)
            db.commit()
            db.refresh(t)
        return t

    def store_inbound(self, db: Session, thread: Thread, sender: str, recipient: str, subject: str | None, text: str | None, html: str | None, message_id: str | None, in_reply_to: str | None, raw_headers: str | None = None) -> Message:
        msg = Message(
            thread_id=thread.id,
            direction=MessageDirection.inbound,
            from_addr=sender,
            to_addr=recipient,
            subject=subject or "",
            body_text=text or "",
            body_html=html or "",
            raw_headers=raw_headers or "",
            message_id=message_id or "",
            in_reply_to=in_reply_to or "",
        )
        db.add(msg)
        thread.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(msg)
        return msg

    def _compose_email(self, from_addr: str, to_addr: str, subject: str | None, text: str | None, html: str | None, reply_to: str | None = None, in_reply_to: str | None = None, references: str | None = None) -> EmailMessage:
        em = EmailMessage()
        em["Subject"] = subject or ""
        em["From"] = from_addr
        em["To"] = to_addr
        if reply_to:
            em["Reply-To"] = reply_to
        # threading headers
        if in_reply_to:
            em["In-Reply-To"] = in_reply_to
        if references:
            em["References"] = references
        em["Message-ID"] = make_msgid()

        # Set body (prefer multipart if html provided)
        if html and text:
            em.set_content(text)
            em.add_alternative(html, subtype="html")
        elif html:
            em.add_alternative(html, subtype="html")
            # also include text fallback
            em.set_content(text or "")
        else:
            em.set_content(text or "")
        return em

    def _smtp_send(self, em: EmailMessage):
        host = settings.SMTP_HOST
        port = settings.SMTP_PORT
        username = settings.SMTP_USERNAME
        password = settings.SMTP_PASSWORD
        use_ssl = settings.SMTP_USE_SSL
        use_tls = settings.SMTP_USE_TLS

        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context) as server:
                if username and password:
                    server.login(username, password)
                server.send_message(em)
        else:
            with smtplib.SMTP(host, port) as server:
                server.ehlo()
                if use_tls:
                    server.starttls(context=ssl.create_default_context())
                if username and password:
                    server.login(username, password)
                server.send_message(em)

    def store_outbound(self, db: Session, thread: Thread, from_addr: str, to_addr: str, subject: str | None, text: str | None, html: str | None, in_reply_to: str | None = None) -> Message:
        msg = Message(
            thread_id=thread.id,
            direction=MessageDirection.outbound,
            from_addr=from_addr,
            to_addr=to_addr,
            subject=subject or "",
            body_text=text or "",
            body_html=html or "",
            in_reply_to=in_reply_to or "",
        )
        db.add(msg)
        thread.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(msg)
        return msg

    def auto_reply(self, db: Session, thread: Thread, mailbox_addr: str, sender: str, last_inbound_message: Message) -> Message:
        # Build chat history up to token window
        chat_messages = build_chat_history_for_thread(db, thread, settings.SYSTEM_PROMPT, settings.MAX_TOKENS_WINDOW)
        # Ask AI for reply
        ai_text = self.ai.generate_reply(chat_messages)

        # Determine from/reply-to logic with delegation
        from_addr = mailbox_addr
        reply_to = None
        if settings.DELEGATED_EMAIL:
            # Send with delegated identity and set Reply-To for the real mailbox
            reply_to = mailbox_addr
            from_addr = settings.DELEGATED_EMAIL

        # Compose and send email
        em = self._compose_email(
            from_addr=from_addr,
            to_addr=sender,
            subject=f"Re: {thread.subject}" if thread.subject else "Re:",
            text=ai_text,
            html=None,
            reply_to=reply_to,
            in_reply_to=last_inbound_message.message_id or None,
            references=thread.references_header or None,
        )
        self._smtp_send(em)

        # Store outbound record
        outbound_msg = self.store_outbound(
            db=db,
            thread=thread,
            from_addr=from_addr,
            to_addr=sender,
            subject=em.get("Subject"),
            text=ai_text,
            html=None,
            in_reply_to=last_inbound_message.message_id or None,
        )
        return outbound_msg


mail_service = MailService()
