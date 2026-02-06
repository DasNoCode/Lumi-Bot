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
                "command": "husbu",
                "aliases": ["husbando"],
                "category": "anime",
                "description": {
                    "content": "Send a husbando image.",
                },
                "xp": 1,
            },
        )

    async def exec(self, M: Message, context: list[Any]) -> None:
        try:
            res = await self.client.utils.fetch("https://nekos.best/api/v2/husbando")
            results = res.get("results", [])
            
            if not results:
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text="<blockquote>❌ <b>No husbando found right now.</b></blockquote>",
                    reply_to_message_id=M.message_id,
                    parse_mode="HTML",
                )
                return

            image = self.client.utils.fetch_buffer(results[0].get('url'))

            text = (
                "<blockquote>"
                "🧔 <b>Husbando</b>\n"
                f"├ <b>Source:</b> {results[0].get('source_url') or 'N/A'}\n"
                f"├ <b>Artist Profile:</b> {results[0].get('artist_href') or 'N/A'}\n"
                f"└ <b>Image:</b> {results[0].get('url') or 'N/A'}"
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
                text="⚠️ <b>Failed to fetch husbando image.</b>",
                reply_to_message_id=M.message_id,
                parse_mode="HTML",
            )
            tb = traceback.extract_tb(e.__traceback__)[-1]
            self.client.log.error(f"[ERROR] {context.cmd}: {tb.lineno} | {e}")




            