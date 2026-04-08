from typing import List, Dict
from .config import settings
import tiktoken

try:
    from openai import OpenAI
except Exception:  # pragma: no cover - optional import guard
    OpenAI = None


class AIReplyService:
    def __init__(self):
        self.model = settings.OPENAI_MODEL
        self.api_key = settings.OPENAI_API_KEY
        self.org_id = settings.ORG_ID
        self.max_out_tokens = settings.MAX_COMPLETION_TOKENS

        # Fallback tokenizer (cl100k_base is common for GPT-3.5/4 families)
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.encoding = None

    def _count_tokens(self, messages: List[Dict]) -> int:
        if not self.encoding:
            # Approximate if tokenizer unavailable
            text = " ".join([m.get("content", "") for m in messages])
            return max(1, len(text) // 4)
        text = " ".join([m.get("content", "") for m in messages])
        return len(self.encoding.encode(text))

    def _trim_to_window(self, messages: List[Dict], max_tokens: int) -> List[Dict]:
        # Keep from the end until within the window, always preserve the first system message if present
        if not messages:
            return messages
        system_msgs = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]

        trimmed = []
        total = self._count_tokens(system_msgs)

        # add from the end of non_system
        for m in reversed(non_system):
            t = self._count_tokens([m])
            if total + t > max_tokens:
                break
            trimmed.insert(0, m)
            total += t
        # Prepend system at front
        return (system_msgs[:1] if system_msgs else []) + trimmed

    def generate_reply(self, chat_messages: List[Dict]) -> str:
        # Trim to 10k (or configured) tokens
        clipped = self._trim_to_window(chat_messages, settings.MAX_TOKENS_WINDOW)

        if not self.api_key or OpenAI is None:
            # Safe fallback if OpenAI is not configured; useful for dev/testing
            return "Thanks for reaching out! This is an automated acknowledgment. We'll follow up shortly."

        client = OpenAI(api_key=self.api_key, organization=self.org_id) if self.org_id else OpenAI(api_key=self.api_key)

        # Use Chat Completions API semantics
        try:
            resp = client.chat.completions.create(
                model=self.model,
                messages=clipped,
                max_tokens=self.max_out_tokens,
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            # Fallback behavior on API error
            return "Thank you for your email. We are experiencing high load; a human will follow up soon."
