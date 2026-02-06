from __future__ import annotations

import traceback
from typing import Any, TYPE_CHECKING

from Libs import BaseCommand
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
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
                    "content": "Delete a sticker set created by you using this bot.",
                    "usage": "<reply to sticker> or <no args>",
                },
            },
        )

    async def exec(self, M: Message, context: dict[str, Any]) -> None:
        flags: dict[str, str] = context.get("flags", {})
        user_sets = self.client.db.get_user_sticker_sets(
            user_id=M.sender.user_id,
            )

        if M.is_callback:
            pack_name: str | None = flags.get("set")
            if not pack_name:
                return

            reply_to = (
                M.reply_to_message.message_id if M.reply_to_message else M.message_id
            )

            try:
                await self.client.bot.delete_message(
                    chat_id=M.chat_id,
                    message_id=M.message_id,
                )
            except Exception:
                pass

            try:
                await self.client.bot.delete_sticker_set(name=pack_name)
                self.client.db.delete_sticker_set(pack_name)
            except BadRequest as e:
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text="❌ Failed to delete sticker set.",
                    reply_to_message_id=reply_to,
                )
                tb = traceback.extract_tb(e.__traceback__)[-1]
                self._client.log.error(f"[ERROR] {context.cmd}: {tb.lineno} | {e}")
                return

            await self.client.send_message(
                chat_id=M.chat_id,
                text="✅ Sticker set deleted successfully.",
                reply_to_message_id=reply_to,
            )
            return

        reply = M.reply_to_message
        if reply and reply.sticker:
            pack_title: str | None = reply.sticker.set_name

            if not pack_title:
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text="❌ This sticker does not belong to a sticker set.",
                    reply_to_message_id=M.message_id,
                )
                return
            
            pack_name: str | None = next(
                (
                    sticker["pack_name"]
                    for sticker in user_sets
                    if sticker.get("pack_title") == pack_title
                ),
                None,
            )
            if not pack_name:
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text="❌ Sticker packs isn't created by this bot, cannot be deleted.",
                    reply_to_message_id=M.message_id,
                )
                return

            try:
                await self.client.bot.delete_sticker_set(name=pack_name)
                self.client.db.delete_sticker_set(pack_name)
            except BadRequest as e:
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text="❌ Failed to delete sticker set.",
                    reply_to_message_id=M.message_id,
                )
                tb = traceback.extract_tb(e.__traceback__)[-1]
                self.client.log.error(f"[ERROR] {context.cmd}: {tb.lineno} | {e}")
                return

            await self.client.send_message(
                chat_id=M.chat_id,
                text="✅ Sticker set deleted successfully.",
                reply_to_message_id=M.message_id,
            )
            return

        if not user_sets:
            await self.client.send_message(
                chat_id=M.chat_id,
                text="ℹ️ You don’t have any sticker sets yet.",
                reply_to_message_id=M.message_id,
            )
            return

        buttons: list[list[InlineKeyboardButton]] = []
        row: list[InlineKeyboardButton] = []

        for s in user_sets:
            row.append(
                InlineKeyboardButton(
                    text=s["pack_title"],
                    callback_data=f"cmd:deleteset set:{s['pack_name']}",
                )
            )
            if len(row) == 2:
                buttons.append(row)
                row = []

        if row:
            buttons.append(row)

        await self.client.send_message(
            chat_id=M.chat_id,
            text="🗑 Choose a sticker set to delete:",
            reply_markup=InlineKeyboardMarkup(buttons),
            reply_to_message_id=M.message_id,
        )
