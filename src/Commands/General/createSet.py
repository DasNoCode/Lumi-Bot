from __future__ import annotations

from pathlib import Path
from typing import Any, TYPE_CHECKING

from Libs import BaseCommand
from telegram import InputSticker
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
                "command": "createset",
                "aliases": ["sticker", "newpack", "sset"],
                "category": "general",
                "description": {
                    "content": "Creates a sticker set and converts the replied photo / GIF / video into a sticker.",
                    "usage": "<reply to photo | gif | video> [emoji]",
                },
            }
        )


    async def exec(self, M: Message, context: dict[str, Any]) -> None:
        loading = None
        input_path: Path | None = None
        output_path: Path | None = None

        try:
            reply = M.reply_to_message
            if not reply or not (reply.photo or reply.video or reply.animation):
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text="❌ Please reply to a photo, GIF, or video to create a sticker.",
                    reply_to_message_id=M.message_id,
                )
                return

            file_id: str = (
                reply.animation.file_id
                if reply.animation
                else reply.video.file_id
                if reply.video
                else reply.photo[-1].file_id
            )

            loading = await self.client.send_message(
                chat_id=M.chat_id,
                text="🔮",
                reply_to_message_id=M.message_id,
            )

            text: str = context.get("text", "").strip()
            emoji: str = text.split()[0] if text else "✨"

            input_path = Path(await self.client.download_media(file_id))

            if input_path.stat().st_size > 256 * 1024:
                raise ValueError("FILE_TOO_LARGE")

            is_video: bool = bool(reply.video or reply.animation)

            pack_type: str = "video" if is_video else "static"
            bot_username: str = self.client.bot.username.lower()

            pack_name: str = f"pack_{M.sender.user_id}_{pack_type}_by_{bot_username}"
            pack_title: str = f"{M.sender.user_full_name}'s {pack_type.title()} Stickers"

            output_path = (
                input_path.with_suffix(".webm")
                if is_video
                else input_path.with_suffix(".webp")
            )

            if is_video:
                self.client.utils.video_to_webm(input_path, output_path)
            else:
                self.client.utils.image_to_webp(input_path, output_path)

            sticker = InputSticker(
                sticker=output_path.open("rb"),
                emoji_list=[emoji],
                format=StickerFormat.VIDEO if is_video else StickerFormat.STATIC,
            )

            try:
                await self.client.bot.get_sticker_set(pack_name)
                pack_exists = True
            except BadRequest:
                pack_exists = False

            if not pack_exists:
                await self.client.bot.create_new_sticker_set(
                    user_id=M.sender.user_id,
                    name=pack_name,
                    title=pack_title,
                    stickers=[sticker],
                    sticker_type="regular",
                )
            else:
                await self.client.bot.add_sticker_to_set(
                    user_id=M.sender.user_id,
                    name=pack_name,
                    sticker=sticker,
                )
            self.client.db.add_sticker_sets(pack_name)
            
            await self.client.bot.delete_message(
                chat_id=M.chat_id,
                message_id=loading.message_id,
            )
            
            sticker_set = await self.client.bot.get_sticker_set(pack_name)
            last_sticker = sticker_set.stickers[-1]

            await self.client.bot.send_sticker(
                chat_id=M.chat_id,
                sticker=last_sticker.file_id,
                reply_to_message_id=M.message_id,
            )

        except ValueError as e:
            if str(e) == "FILE_TOO_LARGE":
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text="❌ File is too large. Sticker must be under 256 KB.",
                    reply_to_message_id=M.message_id
                )
            else:
                raise

        except BadRequest as e:
            await self.client.send_message(
                chat_id=M.chat_id,
                text="❌ Telegram rejected this media. Try a different file.",
                reply_to_message_id=M.message_id,
            )
            self.client.log.error(f"[Sticker][BadRequest] {e}")

        except Exception as e:
            await self.client.send_message(
                chat_id=M.chat_id,
                text="❌ Failed to create sticker due to an unexpected error.",
                reply_to_message_id=M.message_id,
            )
            self.client.log.error(f"[Sticker][Error] {e}")

        finally:
            try:
                if input_path:
                    input_path.unlink(missing_ok=True)
                if output_path:
                    output_path.unlink(missing_ok=True)
            except Exception:
                pass
