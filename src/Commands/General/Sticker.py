from __future__ import annotations

from pathlib import Path
from typing import Any, TYPE_CHECKING, Dict, List

from Libs import BaseCommand
from telegram import InputSticker, InlineKeyboardButton, InlineKeyboardMarkup
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
                "command": "sticker",
                "aliases": ["createset", "newpack", "sset"],
                "category": "general",
                "description": {
                    "content": "Create or add to a sticker set from replied media.",
                    "usage": "<reply> emoji:✨ title:My Pack",
                },
            },
        )

    async def exec(self, M: Message, context: dict[str, Any]) -> None:
        flags: dict[str, str] = context.get("flags", {})
        text: str = context.get("text", "").strip()

        emoji: str = flags.get("emoji") or (text.split()[0] if text else "✨")
        title: str | None = flags.get("title")

        if title and len(title) > 64:
            await self.client.send_message(
                chat_id=M.chat_id,
                text="❌ Title must be 64 characters or less.",
                reply_to_message_id=M.message_id,
            )
            return

        store_key = (M.chat_id, M.sender.user_id)
        user_sets: List[Dict[str, Any]] = self.client.db.get_user_sticker_sets(M.sender.user_id)

        if M.is_callback:
            try:
                await self.client.bot.delete_message(
                    chat_id=M.chat_id,
                    message_id=M.message_id,
                )
            except Exception:
                pass

            store = self.client.interaction_store.get(store_key)
            if not store:
                return

            file_id: str = store["file_id"]
            is_video: bool = store["is_video"]
            emoji = store["emoji"]
            title = store["title"]
            origin_msg_id: int = store["origin_msg_id"]

            selected_set: str | None = flags.get("set")
            force_new: bool = flags.get("new") == "true"

        else:
            reply = M.reply_to_message
            if not reply or not (reply.photo or reply.video or reply.animation):
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text="❌ Reply to a photo, GIF, or video.",
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

            is_video: bool = bool(reply.video or reply.animation)
            origin_msg_id: int = M.message_id

            self.client.interaction_store[store_key] = {
                "file_id": file_id,
                "is_video": is_video,
                "emoji": emoji,
                "title": title,
                "origin_msg_id": origin_msg_id,
            }

            if user_sets:
                buttons: list[list[InlineKeyboardButton]] = []
                row: list[InlineKeyboardButton] = []

                for s in user_sets:
                    row.append(
                        InlineKeyboardButton(
                            text=s["pack_title"],
                            callback_data=f"cmd:sticker set:{s['pack_name']}",
                        )
                    )
                    if len(row) == 2:
                        buttons.append(row)
                        row = []

                if row:
                    buttons.append(row)

                buttons.append(
                    [
                        InlineKeyboardButton(
                            text="➕ New Sticker Set",
                            callback_data="cmd:sticker new:true",
                        )
                    ]
                )

                await self.client.send_message(
                    chat_id=M.chat_id,
                    text="🗂 Choose a sticker set:",
                    reply_markup=InlineKeyboardMarkup(buttons),
                    reply_to_message_id=origin_msg_id,
                )
                return

            selected_set = None
            force_new = True

        loading = await self.client.send_message(
            chat_id=M.chat_id,
            text="🔮",
            reply_to_message_id=origin_msg_id,
        )

        input_path: Path | None = None
        output_path: Path | None = None

        try:
            input_path = Path(await self.client.download_media(file_id))

            if input_path.stat().st_size > 256 * 1024:
                await self.client.send_message(
                    chat_id=M.chat_id,
                    text="❌ File must be under 256 KB.",
                    reply_to_message_id=origin_msg_id,
                )
                return

            pack_type: str = "video" if is_video else "static"
            pack_id: str = self.client.utils.random_text()
            bot_username: str = self.client.bot.username.lower()

            if force_new or not selected_set:
                pack_name = (
                    f"pack_{pack_id}_{M.sender.user_id}_{pack_type}_by_{bot_username}"
                )
                pack_title = (title or f"{M.sender.user_full_name}'s Stickers") + (
                    f" ({n})"
                    if (
                        n := sum(
                            1
                            for s in user_sets
                            if s["pack_title"].startswith(
                                title or f"{M.sender.user_full_name}'s Stickers"
                            )
                        )
                    )
                    else ""
                )
            else:
                pack_name = selected_set
                pack_title = None

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
                await self.client.bot.add_sticker_to_set(
                    user_id=M.sender.user_id,
                    name=pack_name,
                    sticker=sticker,
                )
            except BadRequest:
                await self.client.bot.create_new_sticker_set(
                    user_id=M.sender.user_id,
                    name=pack_name,
                    title=pack_title,
                    stickers=[sticker],
                    sticker_type="regular",
                )

            self.client.db.add_sticker_sets(
                pack_name=pack_name,
                pack_title=pack_title,
                format=pack_type,
                creator_user_id=M.sender.user_id,
            )

            sticker_set = await self.client.bot.get_sticker_set(pack_name)

            await self.client.bot.delete_message(
                chat_id=M.chat_id,
                message_id=loading.message_id,
            )

            await self.client.bot.send_sticker(
                chat_id=M.chat_id,
                sticker=sticker_set.stickers[-1].file_id,
                reply_to_message_id=origin_msg_id,
            )

        finally:
            try:
                if input_path:
                    input_path.unlink(missing_ok=True)
                if output_path:
                    output_path.unlink(missing_ok=True)
            except Exception:
                pass
