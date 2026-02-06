from __future__ import annotations

import os
import traceback
from typing import Any, TYPE_CHECKING

from telegram.error import NetworkError
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
                "command": "setchatpfp",
                "aliases": ["setpfp", "setgpic"],
                "category": "chat",
                "description": {
                    "content": "Set a new chat profile photo (reply to an image or send it with caption).",
                    "usage": "<reply to a photo or send with caption>",
                },
                "OnlyChat": True,
                "OnlyAdmin": True,
                "admin_permissions": ["can_change_info"],
            },
        )

    async def exec(self, M: Message, context: dict[str, Any]) -> None:
        try:
            photo_file_id: str | None = None

            if M.msg_type == "photo" and M.file_id:
                photo_file_id = M.file_id
            elif (
                M.reply_to_message
                and M.reply_to_message.photo
                and M.reply_to_message.photo[0].file_id
            ):
                photo_file_id = M.reply_to_message.photo[0].file_id

            if not photo_file_id:
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text="❗ Please reply to a photo or send one with the command.",
                    reply_to_message_id=M.message_id,
                )
                return

            loading = await self.client.send_message(
                chat_id=M.chat_id,
                text="👨‍💻",
                reply_to_message_id=M.message_id,
            )

            path: str | None = None
            try:
                path = await self.client.download_media(photo_file_id)

                with open(path, "rb") as img:
                    await self.client.bot.set_chat_photo(
                        chat_id=M.chat_id,
                        photo=img,
                    )

                await self.client.bot.delete_message(
                    chat_id=M.chat_id,
                    message_id=loading.message_id,
                )

                await self.client.send_message(
                    chat_id=M.chat_id,
                    text="✅ Group profile picture updated successfully!",
                    reply_to_message_id=M.message_id,
                )

            finally:
                if path and os.path.exists(path):
                    os.remove(path)

        except NetworkError as e:
            tb = traceback.extract_tb(e.__traceback__)[-1]
            self.client.log.error(f"[ERROR] {context.cmd}: {tb.lineno} | {e}")

            await self.client.send_message(
                chat_id=M.chat_id,
                text="⚠️ Telegram network issue. Please try again.",
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
