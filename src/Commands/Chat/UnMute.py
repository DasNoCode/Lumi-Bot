from __future__ import annotations

import sys
import traceback
from typing import Any, TYPE_CHECKING

from Libs import BaseCommand
from telegram import ChatPermissions

if TYPE_CHECKING:
    from Libs import SuperClient, Message
    from Handler import CommandHandler


class Command(BaseCommand):
    def __init__(self, client: SuperClient, handler: CommandHandler) -> None:
        super().__init__(
            client,
            handler,
            {
                "command": "unmute",
                "category": "chat",
                "description": {
                    "content": "Unmute one or more users in the chat.",
                    "usage": "<@mention> or <reply>",
                },
                "OnlyChat": True,
                "OnlyAdmin": True,
                "admin_permissions": ["can_restrict_members"],
            },
        )

    async def exec(self, M: Message, context: dict[str, Any]) -> None:
        try:
           users = []
   
           if M.reply_to_user:
               users.append(M.reply_to_user)
           elif M.mentioned:
               users.extend(M.mentioned)
   
           if not users:
               await self.client.send_message(
                   chat_id=M.chat_id,
                   text="❗ Reply to a user or mention at least one user to unmute.",
                   reply_to_message_id=M.message_id,
               )
               return
   
           for user in users:
               member = await self.client.bot.get_chat_member(
                   chat_id=M.chat_id,
                   user_id=user.user_id,
               )
   
               already_unmuted = (
                   member.can_send_messages is not False
               )
   
               if already_unmuted:
                   await self.client.send_message(
                       chat_id=M.chat_id,
                       text=f"⚠️ {user.user_full_name or user.user_name} is not muted.",
                   )
                   continue
   
               await self.client.bot.restrict_chat_member(
                   chat_id=M.chat_id,
                   user_id=user.user_id,
                   permissions=ChatPermissions.all_permissions(),
               )
   
               await self.client.send_message(
                   chat_id=M.chat_id,
                   text=f"🔊 {user.user_full_name or user.user_name} has been unmuted.",
               )
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)[-1]
            self.client.log.error(f"[ERROR] {context.cmd}: {tb.lineno} | {e}")
        
            await self.client.send_message(
                chat_id=M.chat_id,
                text="❌ Something went wrong. Please try again later.",
                reply_to_message_id=M.message_id,
            )
