from __future__ import annotations

from typing import Any, TYPE_CHECKING
from telegram import ChatPermissions

from Helpers import JsonObject
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
                "command": "unlock",
                "category": "chat",
                "description": {
                    "content": "Unlock the chat (mute everyone).",
                    "usage": "<@mention> or <reply> [time:<minutes>]",
                },
                "OnlyChat": True,
                "OnlyAdmin": True,
                "admin_permissions": ["can_restrict_members", "can_change_info"],
            },
        )
    async def exec(self, M: Message, context: dict[str, Any]) -> None:
        perms = self.client.db.get_group_by_chat_id(M.chat_id)
        await self.client.bot.set_chat_permissions(
            chat_id=M.chat_id,
            permissions=ChatPermissions(perms.permissions)
        )
        await self.client.send_message(
            chat_id=M.chat_id,
            text="🔓 Chat unlocked.",
            reply_to_message_id=M.message_id,
        )


        
        



