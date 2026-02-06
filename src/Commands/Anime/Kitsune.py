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
                "command": "kitsune",
                "aliases": ["foxgirl"],
                "category": "anime",
                "description": {
                    "content": "Send a cute kitsune image.",
                },
                "xp": 1,
            },
        )

    async def exec(self, M: Message, context: list[Any]) -> None:
        try:
            res = await self.client.utils.fetch("https://nekos.best/api/v2/kitsune")
            results = res.get("results", [])

            if not results:
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text="<blockquote>❌ <b>No kitsune found right now.</b></blockquote>",
                    reply_to_message_id=M.message_id,
                    parse_mode="HTML",
                )
                return

            kitsune = results[0]
            image = self.client.utils.fetch_buffer(kitsune["url"])

            text = (
                "<blockquote>"
                "🦊 <b>Kitsune</b>\n"
                f"├ <b>Artist:</b> {kitsune.get('artist_name', 'Unknown')}\n"
                f"├ <b>Source:</b> {kitsune.get('source_url', 'N/A')}\n"
                f"├ <b>Artist Profile:</b> {kitsune.get('artist_href', 'N/A')}\n"
                f"└ <b>Image:</b> {kitsune.get('url')}"
                "</blockquote>"
            )

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
                text="⚠️ <b>Failed to fetch kitsune image.</b>",
                reply_to_message_id=M.message_id,
                parse_mode="HTML",
            )
            tb = traceback.extract_tb(e.__traceback__)[-1]
            self.client.log.error(f"[ERROR] {context.cmd}: {tb.lineno} | {e}")