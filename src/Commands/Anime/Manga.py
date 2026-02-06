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
                "command": "manga",
                "aliases": ["mang", "manhwa"],
                "category": "anime",
                "description": {
                    "content": "Search for manga details.",
                    "usage": "<manga_name>",
                },
                "xp": 1,
            },
        )

    async def exec(self, M: Message, context: list[Any]) -> None:
        query = context.get("text", "")
        if not query:
            await self.client.send_message(
                chat_id=M.chat_id,
                text="<blockquote>❌ <b>You forgot to provide a manga name.</b></blockquote>",
                reply_to_message_id=M.message_id,
                parse_mode="HTML",
            )
            return

        try:
            mangas = await self.client.utils.fetch(
                f"https://weeb-api.vercel.app/manga?search={query}"
            )

            if not mangas:
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text=(
                        "<blockquote>"
                        "🤔 <b>No results found.</b>\n"
                        "├ Try a different name"
                        "</blockquote>"
                    ),
                    reply_to_message_id=M.message_id,
                    parse_mode="HTML",
                )
                return

            text = (
                "<blockquote>"
                f"📚 <b>Manga Search Results</b>\n"
                f"├ <b>Query:</b> {query}\n"
                "</blockquote>\n"
            )

            for i, manga in enumerate(mangas):
                symbol = "🔞" if manga.get("isAdult") else "🌀"
                text += (
                    "<blockquote>"
                    f"#{i + 1}\n"
                    f"├ <b>English:</b> {manga['title']['english']}\n"
                    f"├ <b>Romaji:</b> {manga['title']['romaji']}\n"
                    f"├ <b>Status:</b> {manga['status']}\n"
                    f"├ <b>Adult:</b> {manga['isAdult']} {symbol}\n"
                    f"└ <b>More:</b> {self.client.config.prefix}mid {manga['id']}"
                    "</blockquote>\n"
                )

            await self.client.send_message(
                chat_id=M.chat_id,
                text=text.strip(),
                reply_to_message_id=M.message_id,
                parse_mode="HTML",
            )

        except Exception as e:
            await self.client.send_message(
                chat_id=M.chat_id,
                text="⚠️ <b>Failed to fetch manga information.</b>",
                reply_to_message_id=M.message_id,
                parse_mode="HTML",
            )
            tb = traceback.extract_tb(e.__traceback__)[-1]
            self.client.log.error(f"[ERROR] {context.cmd}: {tb.lineno} | {e}")
