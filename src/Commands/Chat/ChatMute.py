from __future__ import annotations
import traceback
from telegram import ChatPermissions
from Libs import BaseCommand
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from Libs import SuperClient, Message
    from Handler import CommandHandler


class Command(BaseCommand):
    def __init__(self, client: SuperClient, handler: CommandHandler) -> None:
        super().__init__(
            client,
            handler,
            {
                "command": "lockchat",
                "aliases": ["muteall", "adminonly"],
                "category": "chat",
                "description": {
                    "content": "Toggle announcement mode (only admins can send messages).",
                    "usage": "<on/off>",
                },
                "OnlyChat": True,
                "OnlyAdmin": True,
                "admin_permissions": ["can_change_info"]
            },
        )

    async def exec(self, M: Message, context: dict[str, Any]) -> None:
        args: list[str] = context.get("args", [])

        if not args:
            await self.client.send_message(
                chat_id=M.chat_id,
                text=f"⚠️ Please specify on or off.\nExample: {self.client.prefix}lockchat on",
                reply_to_message_id=M.message_id,
            )
            return

        option: str = args[0].strip().lower()

        if option == "on":
            is_announce = True
        elif option == "off":
            is_announce = False
        else:
            await self.client.send_message(
                chat_id=M.chat_id,
                text="❌ Invalid option. Use *on* or *off* only.",
                reply_to_message_id=M.message_id,
                parse_mode="Markdown",
            )
            return

        try:
            permissions = ChatPermissions(
                can_send_messages=not is_announce,
                can_send_audios=not is_announce,
                can_send_documents=not is_announce,
                can_send_photos=not is_announce,
                can_send_video_notes=not is_announce,
                can_send_videos=not is_announce,
                can_send_voice_notes=not is_announce,
                can_send_polls=not is_announce,
                can_send_other_messages=not is_announce,
                can_add_web_page_previews=not is_announce,
                can_change_info=False,
                can_invite_users=True,
                can_pin_messages=False,
            )

            await self.client.bot.set_chat_permissions(
                chat_id=M.chat_id,
                permissions=permissions,
            )

            await self.client.send_message(
                chat_id=M.chat_id,
                text=f"📢 Chat announcement mode is now {'enabled' if is_announce else 'disabled'}.",
                reply_to_message_id=M.message_id,
                parse_mode="Markdown",
            )

        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)[-1]
            self.client.log.error(f"[ERROR] {context.cmd}: {tb.lineno} | {e}")
            
            await self.client.send_message(
                chat_id=M.chat_id,
                text="❌ Something went wrong. Please try again later.",
                reply_to_message_id=M.message_id,
            )
