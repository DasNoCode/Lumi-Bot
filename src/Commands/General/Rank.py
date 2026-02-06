from __future__ import annotations

import os
import sys
import traceback
from typing import Any, TYPE_CHECKING

import telegram

from Libs import BaseCommand
from Helpers import get_rank

if TYPE_CHECKING:
    from telegram import User, Message
    from Libs import SuperClient
    from Handler import CommandHandler


class Command(BaseCommand):
    def __init__(self, client: SuperClient, handler: CommandHandler) -> None:
        super().__init__(
            client,
            handler,
            {
                "command": "rank",
                "category": "general",
                "description": {
                    "content": "Show the rank of a user based on XP.",
                }
            },
        )

    async def exec(self, M: Message, context: dict[str, Any]) -> None:
        try:
            users: list[User] = []
            
            context: str = context.get("flags", {})
            
            caption = context.get("caption")
            
            if M.reply_to_user:
                users.append(M.reply_to_user)
            elif M.mentioned:
                users.extend(M.mentioned)
            else:
                users.append(M.sender)

            for user in users:
                db_user = self.client.db.get_user_by_user_id(user.user_id)
                xp: int = db_user.xp

                user_name: str = (
                    user.user_name
                    or user.user_full_name
                    or "User"
                )

                rank_data: dict[str, Any] = get_rank(xp)

                level: int = rank_data["level"]
                rank_name: str = rank_data["rank_name"]
                rank_emoji: str = rank_data["rank_emoji"]
                next_rank_name: str = rank_data["next_rank_name"]
                next_rank_emoji: str = rank_data["next_rank_emoji"]
                next_rank_xp: int = rank_data["next_rank_xp"]
                current_xp: int = rank_data["xp"]
                level_xp_target: int = rank_data["level_xp_target"]

                previous_level_xp: int = (
                    5 * ((level - 1) ** 2) + 50
                    if level > 1
                    else 0
                )
                photo_id: str = await self.client.get_profile_id(user.user_id)
                photo: str | None = await self.client.download_media(
                    photo_id
                )
                avatar_url: str = self.client.utils.img_to_url(photo)
                os.remove(photo)
                
                card_buffer = self.client.utils.fetch_buffer(
                    self.client.utils.rank_card(
                        user_name,
                        avatar_url,
                        level,
                        current_xp,
                        level_xp_target,
                        previous_level_xp,
                    )
                )
                await self.client.send_photo(
                    chat_id=M.chat_id,
                    photo=card_buffer,
                    caption=(
                        "<blockquote>"
                        f"├Rank name: {rank_name} {rank_emoji}\n"
                        f"├Next rank: {next_rank_name} {next_rank_emoji}\n"
                        f"└XP needed: {next_rank_xp - current_xp}"
                        "</blockquote>"
                        f"\n{caption if caption else ''}"
                    ),
                    reply_to_message_id=M.message_id,
                    parse_mode=telegram.constants.ParseMode.HTML,
                )

        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)[-1]
            self.client.log.error(f"[ERROR] {context.cmd}: {tb.lineno} | {e}")
