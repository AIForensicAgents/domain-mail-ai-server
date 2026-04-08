from sqlalchemy.orm import Session
from typing import List, Dict
from .models import Thread, Message, MessageDirection


def build_chat_history_for_thread(db: Session, thread: Thread, system_prompt: str, max_tokens: int) -> List[Dict]:
    # Convert the last N messages to chat format
    # role=user for inbound (external), role=assistant for outbound (our replies)
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    # Fetch messages sorted by created_at ascending (relationship already ordered)
    for m in thread.messages[-200:]:  # Hard cap to avoid over-fetch
        if m.direction == MessageDirection.inbound:
            role = "user"
        else:
            role = "assistant"
        body = m.body_text or ""
        messages.append({"role": role, "content": body})
    return messages
