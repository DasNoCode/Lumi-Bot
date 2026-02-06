from __future__ import annotations
import traceback
from typing import Any, TYPE_CHECKING
from Libs import BaseCommand

if TYPE_CHECKING:
    from Libs import SuperClient, Message
    from Handler import CommandHandler


class Command(BaseCommand):
    def __init__(self, client: SuperClient, handler: CommandHandler) -> None:
        super().__init__(
            client,
            handler,
            {
                "command": "afk",
                "category": "chat",
                "description": {
                    "content": (
                        "Set yourself as AFK (Away From Keyboard). "
                        "Mentions will auto-reply that you're unavailable "
                        "and notify you when you're mentioned."
                    ),
                },
                "OnlyChat": True
            },
        )

    async def exec(self, M: Message, context: list[Any]) -> None:
        try:
            reason: str = " ".join(context.get("args", [])).strip() if context else None
            self.client.db.update_user_afk(M.sender.user_id, True, reason)

            afk_text: str = (
                f"@{M.sender.user_name or M.sender.user_full_name}, you're now AFK 💤"
                + (f"\nReason: {reason}" if reason else "")
            )

            await self.client.send_message(
                chat_id=M.chat_id,
                text=afk_text,
                reply_to_message_id=M.message_id,
            )

        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)[-1]
            self.client.log.error(f"[ERROR] {context.cmd}: {tb.lineno} | {e}")
            
            await self.client.send_message(
                chat_id=M.chat_id,
                text="❌ Something went wrong. Please try again later.",
                reply_to_message_id=M.message_id,
            )

