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
                "command": "anime",
                "aliases": ["ani"],
                "category": "anime",
                "description": {
                    "content": "Search for anime details.",
                    "usage": "<anime_name>",
                },
                "xp": 1,
            },
        )

    async def exec(self, M: Message, context: list[Any]) -> None:
        query = context.get("text", "")

        if not query:
            await self.client.send_message(
                chat_id=M.chat_id,
                text="<blockquote>❌ <b>Please provide an anime name.</b></blockquote>",
                reply_to_message_id=M.message_id,
                parse_mode="HTML",
            )
            return

        try:
            animes = self.client.utils.fetch(
                f"https://weeb-api.vercel.app/anime?search={query}"
            )

            if not animes:
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text=(
                        "<blockquote>"
                        "🤔 <b>No results found.</b>\n"
                        "Try searching with a different name."
                        "</blockquote>"
                    ),
                    reply_to_message_id=M.message_id,
                    parse_mode="HTML",
                )
                return

            text = (
                "<blockquote>"
                f"🎬 <b>Anime Search Results</b>\n"
                f"├ <b>Query:</b> {query}\n\n"
            )

            for i, anime in enumerate(animes, start=1):
                text += (
                    f"#{i}\n"
                    f"├ <b>English:</b> {anime['title']['english']}\n"
                    f"├ <b>Romaji:</b> {anime['title']['romaji']}\n"
                    f"├ <b>Type:</b> {anime['format']}\n"
                    f"├ <b>Status:</b> {anime['status']}\n"
                    f"├ <b>More Info:</b> {self.client.prefix}aid {anime['id']}\n\n"
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
                text="⚠️ <b>Failed to fetch anime data.</b>",
                reply_to_message_id=M.message_id,
                parse_mode="HTML",
            )
            tb = traceback.extract_tb(e.__traceback__)[-1]
            self.client.log.error(f"[ERROR] {context.cmd}: {tb.lineno} | {e}")
            
