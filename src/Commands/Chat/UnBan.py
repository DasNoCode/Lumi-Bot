from __future__ import annotations
import sys
import traceback
from typing import Any, TYPE_CHECKING
from Libs import BaseCommand

if TYPE_CHECKING:
    from telegram import User
    from Libs import SuperClient, Message
    from Handler import CommandHandler


class Command(BaseCommand):
    def __init__(self, client: SuperClient, handler: CommandHandler) -> None:
        super().__init__(
            client,
            handler,
            {
                "command": "unban",
                "category": "chat",
                "description": {
                    "content": "unBan one or more users from the chat.",
                    "usage": "<@mention> or <reply>",
                },
                "OnlyChat": True,
                "OnlyAdmin": True,
                "admin_permissions": ["can_restrict_members"]
            },
        )

    async def exec(self, M: Message, context: list[Any]) -> None:
        try:
            users: list[User] = []

            if M.reply_to_user:
                users.append(M.reply_to_user)
            elif M.mentioned:
                users.extend(M.mentioned)

            if not users:
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text="❗ Please mention at least one user or reply to their message to unban them.",
                    reply_to_message_id=M.message_id,
                )
                return

            for user in users:
                member = await self.client.bot.get_chat_member(M.chat_id, user.user_id)
                if member.status == "creator":
                    return

                if user.user_id == M.bot_userid:
                    return

                await self.client.bot.unban_chat_member(
                    chat_id=M.chat_id,
                    user_id=user.user_id,
                )

                await self.client.send_message(
                    chat_id=M.chat_id,
                    text=f"✅ User with ID {user.user_id} has been unbanned.",
                )

        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)[-1]
            self.client.log.error(f"[ERROR] {context.cmd}: {tb.lineno} | {e}")
            
            await self.client.send_message(
                chat_id=M.chat_id,
                text="❌ Failed to unban user(s).",
                reply_to_message_id=M.message_id,
            )

