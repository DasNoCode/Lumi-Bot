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
                "command": "cid",
                "aliases": ["charid", "characterid"],
                "category": "anime",
                "description": {
                    "content": "Get anime character info by ID.",
                    "usage": "<character_id>",
                },
                "xp": 1,
            },
        )

    async def exec(self, M: Message, context: list[Any]) -> None:
        query = context.get("text", "")

        if not query or not query.isdigit():
            await self.client.send_message(
                chat_id=M.chat_id,
                text="<blockquote>❌ <b>Please provide a valid character ID.</b></blockquote>",
                reply_to_message_id=M.message_id,
                parse_mode="HTML",
            )
            return

        try:
            result = self.client.utils.fetch(
                f"https://weeb-api.vercel.app/character?search={query}"
            )

            if not result:
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text=(
                        "<blockquote>"
                        "🤔 <b>No character found.</b>\n"
                        "Try checking the ID and try again."
                        "</blockquote>"
                    ),
                    reply_to_message_id=M.message_id,
                    parse_mode="HTML",
                )
                return

            character = result[0]
            gender = character.get("gender", "Unknown")
            symbol = "🚺" if gender == "Female" else "🚹" if gender == "Male" else "🚻"

            text = (
                "<blockquote>"
                "👤 <b>Character Information</b>\n"
                f"├ <b>Name:</b> {character['name']['full']}\n"
                f"├ <b>Native:</b> {character['name']['native']}\n"
                f"├ <b>ID:</b> <code>{character['id']}</code>\n"
                f"├ <b>Age:</b> {character.get('age', 'Unknown')}\n"
                f"├ <b>Gender:</b> {gender} {symbol}\n"
                f"├ <b>AniList:</b> {character.get('siteUrl', 'N/A')}\n\n"
                f"├ <b>Description:</b>\n"
                f"{character.get('description', 'No description available.')}"
                "</blockquote>"
            )

            image = self.client.utils.fetch_buffer(character["imageUrl"])
            await self.client.send_photo(
                chat_id=M.chat_id,
                photo=image,
                caption=text,
                reply_to_message_id=M.message_id,
                parse_mode="HTML",
            )

        except Exception as e:
            await self.client.send_message(
                chat_id=M.chat_id,
                text="⚠️ <b>Failed to fetch character information.</b>",
                reply_to_message_id=M.message_id,
                parse_mode="HTML",
            )
            tb = traceback.extract_tb(e.__traceback__)[-1]
            self.client.log.error(f"[ERROR] {context.cmd}: {tb.lineno} | {e}")
            
