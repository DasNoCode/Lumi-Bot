from __future__ import annotations
import traceback
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
                "command": "character",
                "aliases": ["char", "csearch"],
                "category": "anime",
                "description": {
                    "content": "Search for anime character details.",
                    "usage": "<character_name>",
                },
                "xp": 1,
            },
        )

    async def exec(self, M: Message, context: list[Any]) -> None:
        query = context.get("text", "")

        if not query:
            await self.client.send_message(
                chat_id=M.chat_id,
                text="<blockquote>❌ <b>Please provide a character name.</b></blockquote>",
                reply_to_message_id=M.message_id,
                parse_mode="HTML",
            )
            return

        try:
            characters = self.client.utils.fetch(
                f"https://weeb-api.vercel.app/character?search={query}"
            )

            if not characters:
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text=(
                        "<blockquote>"
                        "🤔 <b>No characters found.</b>\n"
                        "Try searching with a different name."
                        "</blockquote>"
                    ),
                    reply_to_message_id=M.message_id,
                    parse_mode="HTML",
                )
                return

            text = (
                "<blockquote>"
                f"👤 <b>Character Search Results</b>\n"
                f"├ <b>Query:</b> {query}\n\n"
            )

            for i, char in enumerate(characters, start=1):
                gender = char.get("gender", "Unknown")
                symbol = "🚺" if gender == "Female" else "🚹" if gender == "Male" else "🚻"

                text += (
                    f"#{i}\n"
                    f"├ <b>Full Name:</b> {char['name']['full']}\n"
                    f"├ <b>Native Name:</b> {char['name']['native']}\n"
                    f"├ <b>Gender:</b> {gender} {symbol}\n"
                    f"├ <b>More Info:</b> {self.client.prefix}cid {char['id']}\n\n"
                )

            text += "</blockquote>"

            await self.client.send_message(
                chat_id=M.chat_id,
                text=text.strip(),
                reply_to_message_id=M.message_id,
                parse_mode="HTML",
            )

        except Exception as e:
            await self.client.send_message(
                chat_id=M.chat_id,
                text="⚠️ <b>Failed to fetch character data.</b>",
                reply_to_message_id=M.message_id,
                parse_mode="HTML",
            )
            tb = traceback.extract_tb(e.__traceback__)[-1]
            self.client.log.error(f"[ERROR] {context.cmd}: {tb.lineno} | {e}")
            
