from __future__ import annotations

import sys
import traceback
from typing import Any, TYPE_CHECKING

from Libs import BaseCommand
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

if TYPE_CHECKING:
    from Libs import SuperClient, Message
    from Handler import CommandHandler


class Command(BaseCommand):
    def __init__(self, client: SuperClient, handler: CommandHandler) -> None:
        super().__init__(
            client,
            handler,
            {
                "command": "settings",
                "category": "chat",
                "description": {
                    "content": "Enable or disable greetings and captcha.",
                    "usage": "",
                },
                "OnlyChat": True,
                "OnlyAdmin": True,
                "admin_permissions": ["can_change_info"],
            },
        )

    async def exec(self, M: Message, context: dict[str, Any]) -> None:
        try:
           flags = context.get("flags", {})
           chat_data = self.client.db.get_group_by_chat_id(M.chat_id)
           greetings_on: bool = bool(getattr(chat_data, "events", False))
           captcha_on: bool = bool(getattr(chat_data, "captcha", False))
   
           action = flags.get("toggle")
   
           if M.is_callback and action:
               if action == "greetings":
                   greetings_on = not greetings_on
                   self.client.db.greetings(M.chat_id, greetings_on)
   
               elif action == "captcha":
                   if not captcha_on:
                       me = await self.client.bot.get_chat_member(
                           M.chat_id, self.client.bot.id
                       )
                       if not getattr(me, "can_restrict_members", False):
                           await self.client.send_message(
                               chat_id=M.chat_id,
                               text="❌ I need <b>can_restrict_members</b> permission to enable captcha.",
                               parse_mode="HTML",
                           )
                           return
   
                   captcha_on = not captcha_on
                   self.client.db._update_or_create_group(
                       M.chat_id,
                       {"captcha": captcha_on},
                   )
   
           keyboard = InlineKeyboardMarkup(
               [
                   [
                       InlineKeyboardButton(
                           text=f"Greetings {'Enabled ✅' if greetings_on else 'Disabled ❌'}",
                           callback_data="cmd:settings toggle:greetings",
                       )
                   ],
                   [
                       InlineKeyboardButton(
                           text=f"Captcha {'Enabled ✅' if captcha_on else 'Disabled ❌'}",
                           callback_data="cmd:settings toggle:captcha",
                       )
                   ],
               ]
           )
   
           text = (
               "<blockquote><b>⚙️Chat Settings</b>\n"
               f"├<b>Greetings:</b> {'Enabled' if greetings_on else 'Disabled'}\n"
               f"└<b>Captcha:</b> {'Enabled' if captcha_on else 'Disabled'}</blockquote>"
           )
   
           if M.is_callback:
               await self.client.bot.edit_message_text(
                   chat_id=M.chat_id,
                   message_id=M.message_id,
                   text=text,
                   reply_markup=keyboard,
                   parse_mode="HTML",
               )
           else:
               await self.client.send_message(
                   chat_id=M.chat_id,
                   text=text,
                   reply_markup=keyboard,
                   parse_mode="HTML",
               )
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)[-1]
            self.client.log.error(f"[ERROR] {context.cmd}: {tb.lineno} | {e}")
            
            await self.client.send_message(
                chat_id=M.chat_id,
                text="❌ Something went wrong. Please try again later.",
                reply_to_message_id=M.message_id,
            )
