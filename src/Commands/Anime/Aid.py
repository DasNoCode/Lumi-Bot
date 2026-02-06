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
                "command": "aid",
                "aliases": ["animeid"],
                "category": "anime",
                "description": {
                    "content": "Get detailed info of anime by ID.",
                    "usage": "<anime_id>",
                },
                "xp": 1,
            },
        )

    async def exec(self, M: Message, context: list[Any]) -> None:
        if not int(context.get("text", "")):
            await self.client.send_message(
                chat_id=M.chat_id,
                text="<blockquote>❌ <b>You must provide a valid anime ID.</b></blockquote>",
                reply_to_message_id=M.message_id,
                parse_mode="HTML",
            )
            return

        anime_id: str = int(context.get("text", ""))

        try:
            data = self.client.utils.fetch(
                f"https://weeb-api.vercel.app/anime?search={anime_id}"
            )

            if not data:
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text="<blockquote>🤔 <b>No anime found for this ID.</b></blockquote>",
                    reply_to_message_id=M.message_id,
                    parse_mode="HTML",
                )
                return

            anime = data[0]
            title = anime["title"]

            text = (
                "<blockquote>"
                f"🎬 <b>{title['english']} | {title['romaji']}</b>\n"
                f"├ <b>Japanese:</b> {title['native']}\n"
                f"├ <b>Type:</b> {anime['format']}\n"
                f"├ <b>Adult:</b> {'Yes' if anime['isAdult'] else 'No'}\n"
                f"├ <b>Status:</b> {anime['status']}\n"
                f"├ <b>Episodes:</b> {anime['episodes']}\n"
                f"├ <b>Duration:</b> {anime['duration']} min\n"
                f"├ <b>First Aired:</b> {anime['startDate']}\n"
                f"├ <b>Last Aired:</b> {anime['endDate']}\n"
                f"├ <b>Genres:</b> {', '.join(anime['genres'])}\n"
                f"├ <b>Studios:</b> {anime['studios']}\n"
                f"├ <b>Trailer:</b> https://youtu.be/{anime.get('trailer', {}).get('id', 'N/A')}\n\n"
                f"📖 <b>Description</b>\n{anime['description']}"
                "</blockquote>"
            )

            image = self.client.utils.fetch_buffer(anime["imageUrl"])
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
                text="⚠️ <b>Failed to fetch anime data.</b>",
                reply_to_message_id=M.message_id,
                parse_mode="HTML",
            )
            tb = traceback.extract_tb(e.__traceback__)[-1]
            self.client.log.error(f"[ERROR] {context.cmd}: {tb.lineno} | {e}")
            
