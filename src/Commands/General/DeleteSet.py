from __future__ import annotations

from typing import Any, TYPE_CHECKING

from Libs import BaseCommand
from telegram.error import BadRequest

if TYPE_CHECKING:
    from Libs import SuperClient, Message
    from Handler import CommandHandler


class Command(BaseCommand):
    def __init__(self, client: SuperClient, handler: CommandHandler) -> None:
        super().__init__(
            client,
            handler,
            {
                "command": "deleteset",
                "aliases": ["delset"],
                "category": "general",
                "description": {
                    "content": "Delete a sticker set created by this bot.",
                    "usage": "<reply to a sticker>",
                },
            },
        )

    async def exec(self, M: Message, context: dict[str, Any]) -> None:
        reply = M.reply_to_message

        if not reply or not reply.sticker:
            await self.client.send_message(
                chat_id=M.chat_id,
                text="❌ Reply to a sticker from the pack you want to delete.",
                reply_to_message_id=M.message_id,
            )
            return

        sticker = reply.sticker
        pack_name: str | None = sticker.set_name

        if not pack_name:
            await self.client.send_message(
                chat_id=M.chat_id,
                text="❌ This sticker does not belong to a sticker set.",
                reply_to_message_id=M.message_id,
            )
            return

        bot_username: str = self.client.bot.username.lower()

        if not pack_name.endswith(f"_by_{bot_username}"):
            await self.client.send_message(
                chat_id=M.chat_id,
                text="❌ I can only delete sticker sets created by me.",
                reply_to_message_id=M.message_id,
            )
            return

        try:
            await self.client.bot.delete_sticker_set(name=pack_name)
        except BadRequest as e:
            await self.client.send_message(
                chat_id=M.chat_id,
                text="❌ Failed to delete sticker set.",
                reply_to_message_id=M.message_id,
            )
            self.client.log.error(f"[DeleteSet] {e}")
            return
        self.client.db.delete_sticker_set()
        await self.client.send_message(
            chat_id=M.chat_id,
            text=f"✅ Sticker set deleted successfully",
            reply_to_message_id=M.message_id,
            parse_mode="HTML",
        )
