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
                "command": "mid",
                "aliases": ["mangaid"],
                "category": "anime",
                "description": {
                    "content": "Get detailed info of a manga using its ID.",
                    "usage": "<manga_id>",
                },
                "xp": 1,
            },
        )

    async def exec(self, M: Message, context: list[Any]) -> None:
        if not (int(context.get("text", ""))):
            await self.client.send_message(
                chat_id=M.chat_id,
                text="<blockquote>❌ <b>You must provide a valid manga ID.</b></blockquote>",
                reply_to_message_id=M.message_id,
                parse_mode="HTML",
            )
            return

        manga_id = int(context.get("text", ""))

        try:
            results = await self.client.utils.fetch(
                f"https://weeb-api.vercel.app/manga?search={manga_id}"
            )

            if not results:
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text="<blockquote>🤔 <b>No manga found for this ID.</b></blockquote>",
                    reply_to_message_id=M.message_id,
                    parse_mode="HTML",
                )
                return

            manga = results[0]
            title = manga["title"]

            text = (
                "<blockquote>"
                f"📚 <b>{title['english']} | {title['romaji']}</b>\n"
                f"├ <b>Japanese:</b> {title['native']}\n"
                f"├ <b>Type:</b> {manga['format']}\n"
                f"├ <b>Adult:</b> {'Yes' if manga['isAdult'] else 'No'}\n"
                f"├ <b>Status:</b> {manga['status']}\n"
                f"├ <b>Chapters:</b> {manga['chapters']}\n"
                f"├ <b>Volumes:</b> {manga['volumes']}\n"
                f"├ <b>First Aired:</b> {manga['startDate']}\n"
                f"├ <b>Last Aired:</b> {manga['endDate']}\n"
                f"├ <b>Genres:</b> {', '.join(manga['genres'])}\n"
                f"├ <b>Trailer:</b> https://youtu.be/{manga['trailer']['id'] if manga.get('trailer') else 'N/A'}\n"
                f"└ <b>Description:</b>\n{manga['description']}"
                "</blockquote>"
            )

            image = self.client.utils.fetch_buffer(manga["coverImage"])
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
                text="⚠️ <b>Failed to fetch manga details.</b>",
                reply_to_message_id=M.message_id,
                parse_mode="HTML",
            )
            tb = traceback.extract_tb(e.__traceback__)[-1]
            self.client.log.error(f"[ERROR] {context.cmd}: {tb.lineno} | {e}")
