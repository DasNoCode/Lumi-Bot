from __future__ import annotations
from typing import Any, TYPE_CHECKING, List

from Libs import BaseCommand
from telegram import InputSticker, LinkPreviewOptions
from telegram.constants import StickerFormat
from telegram.error import BadRequest

if TYPE_CHECKING:
    from Libs import SuperClient, Message
    from Handler import CommandHandler


class Command(BaseCommand):
    def __init__(self, client: SuperClient, handler: CommandHandler) -> None:
        super().__init__(
            client,
            handler,
            {
                "command": "stealpack",
                "aliases": ["clonepack"],
                "category": "general",
                "description": {
                    "content": "Clone a sticker pack by replying to a sticker.",
                    "usage": "<reply to a sticker>",
                },
            },
        )

    async def exec(self, M: Message, context: dict[str, Any]) -> None:
        reply = M.reply_to_message
        if not reply or not reply.sticker:
            await self.client.send_message(
                chat_id=M.chat_id,
                text="❌ Reply to a sticker to clone its pack.",
                reply_to_message_id=M.message_id,
            )
            return

        loading = await self.client.send_message(
            chat_id=M.chat_id,
            text="🪄",
            reply_to_message_id=M.message_id,
        )

        try:
            sticker = reply.sticker
            original_set = await self.client.bot.get_sticker_set(sticker.set_name)

            first_stk = original_set.stickers[0]
            is_video = first_stk.is_video
            is_animated = first_stk.is_animated

            if is_video:
                stk_format = StickerFormat.VIDEO
                pack_type = "video"
            elif is_animated:
                stk_format = StickerFormat.ANIMATED
                pack_type = "animated"
            else:
                stk_format = StickerFormat.STATIC
                pack_type = "static"

            bot_username = self.client.bot.username.lower()
            new_pack_name = f"u{M.sender.user_id}_{pack_type}_by_{bot_username}".lower()
            new_pack_title = f"{M.sender.user_full_name}'s Cloned Stickers"

            stickers: List[InputSticker] = [
                InputSticker(
                    sticker=s.file_id, 
                    emoji_list=[s.emoji] if s.emoji else ["✨"],
                    format=stk_format
                ) for s in original_set.stickers
            ]

            max_limit = 50 if (is_video or is_animated) else 120
            stickers = stickers[:max_limit]

            await self.client.bot.create_new_sticker_set(
                user_id=M.sender.user_id,
                name=new_pack_name,
                title=new_pack_title,
                stickers=stickers,
                sticker_type="regular",
            )

            await self.client.bot.delete_message(M.chat_id, loading.message_id)
            await self.client.send_message(
                chat_id=M.chat_id,
                text=(
                    "✅ Sticker pack cloned successfully!\n"
                    f"👉 <a href=\"https://t.me/addstickers/{new_pack_name}\">Sticker Pack</a>"
                ),
                parse_mode="HTML",
                link_preview_options=LinkPreviewOptions(is_disabled=True),
                reply_to_message_id=M.message_id,
            )

        except BadRequest as e:
            await self.client.send_message(
                chat_id=M.chat_id,
                text="❌ Failed to clone sticker pack. Telegram rejected the request.",
                reply_to_message_id=M.message_id,
            )
            self.client.log.error(f"[StealPack][BadRequest] {e}")
        
        except Exception as e:
            await self.client.send_message(
                chat_id=M.chat_id,
                text="❌ Failed to clone sticker pack due to an unexpected error.",
                reply_to_message_id=M.message_id,
            )
            self.client.log.error(f"[StealPack][Error] {e}")