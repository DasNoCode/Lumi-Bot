from datetime import datetime
from typing import Optional, Any, Dict, List

from pymodm import connect
from pymodm.errors import DoesNotExist
from telegram import ChatPermissions

from Models import User, Chat, Bot
from Helpers import JsonObject


class Database:
    def __init__(self, url: str):
        connect(url)

    @staticmethod
    def now() -> float:
        return datetime.now().second

    def _update_or_create_user(self, user_id: int, updates: Dict[str, Any]) -> None:
        try:
            user = User.objects.raw({"user_id": str(user_id)}).first()
            for key, value in updates.items():
                setattr(user, key, value)
            user.save()
        except DoesNotExist:
            updates["user_id"] = str(user_id)
            User(**updates).save()

    def get_user_by_user_id(self, user_id: int) -> User:
        try:
            return User.objects.raw({"user_id": str(user_id)}).first()
        except DoesNotExist:
            self._update_or_create_user(user_id, {})
            return User.objects.raw({"user_id": str(user_id)}).first()

    def _update_or_create_group(self, chat_id: int, updates: Dict[str, Any]) -> None:
        try:
            chat = Chat.objects.raw({"chat_id": str(chat_id)}).first()
            for key, value in updates.items():
                setattr(chat, key, value)
            chat.save()
        except DoesNotExist:
            updates["chat_id"] = str(chat_id)
            Chat(**updates).save()

    def get_group_by_chat_id(self, chat_id: int) -> Any:
        try:
            return Chat.objects.raw({"chat_id": str(chat_id)}).first()
        except DoesNotExist:
            self._update_or_create_group(chat_id, {})
            return JsonObject({"chat_id": str(chat_id), "mod": False, "events": False})

    def _get_bot(self) -> Bot:
        try:
            return Bot.objects.first()
        except DoesNotExist:
            bot = Bot()
            bot.save()
            return bot


    def enable_command(
        self,
        command_name: str,
        enabled: bool,
        reason: Optional[str] = None,
    ) -> None:
        bot = self._get_bot()

        for cmd in bot.commands:
            if cmd.get("command") == command_name:
                cmd["enabled"] = enabled
                cmd["reason"] = reason
                bot.save()
                return

        bot.commands.append(
            {
                "command": command_name,
                "enabled": enabled,
                "reason": reason,
            }
        )
        bot.save()

    def get_cmd_info(self, command_name: str) -> Dict[str, Any]:
        bot = self._get_bot()

        for cmd in bot.commands:
            if cmd.get("command") == command_name:
                return cmd

        default = {
            "command": command_name,
            "enabled": True,
            "reason": None,
        }
        bot.commands.append(default)
        bot.save()
        return default

    def add_sticker_sets(
        self,
        pack_name: str,
        pack_title: str,
        format: str,
        creator_user_id: int,
    ) -> bool:
        bot = self._get_bot()

        for sticker in bot.sticker_sets:
            if sticker.get("pack_name") == pack_name:
                return False

        bot.sticker_sets.append(
            {
                "pack_name": pack_name,
                "pack_title": pack_title,
                "format": format,
                "creator_user_id": creator_user_id,
            }
        )
        bot.save()
        return True

    def delete_sticker_set(self, pack_name: str) -> bool:
        bot = self._get_bot()

        for sticker in bot.sticker_sets:
            if sticker.get("pack_name") == pack_name:
                bot.sticker_sets.remove(sticker)
                bot.save()
                return True

        return False

    def get_user_sticker_sets(self, user_id: int) -> List[Dict[str, Any]]:
        bot = self._get_bot()
        print(bot)
        print(bot.sticker_sets)
        return [
            sticker
            for sticker in bot.sticker_sets
            if sticker.get("creator_user_id") == user_id
        ]

    def get_all_sticker_sets(self) -> List[Dict[str, Any]]:
        bot = self._get_bot()
        return bot.sticker_sets

    def greetings(self, chat_id: int, events_status: bool) -> None:
        self._update_or_create_group(chat_id, {"events": events_status})
        
    def set_group_mod(self, chat_id: int, mod_status: bool) -> None:
        self._update_or_create_group(chat_id, {"mod": mod_status})

    def chat_perms(
        self,
        chat_id: int,
        perms: ChatPermissions,
    ) -> None:
        permissions: Dict[str, bool] = {
            "can_send_messages": perms.can_send_messages,
            "can_send_photos": perms.can_send_photos,
            "can_send_videos": perms.can_send_videos,
            "can_send_audios": perms.can_send_audios,
            "can_send_documents": perms.can_send_documents,
            "can_send_voice_notes": perms.can_send_voice_notes,
            "can_send_video_notes": perms.can_send_video_notes,
            "can_send_polls": perms.can_send_polls,
            "can_send_other_messages": perms.can_send_other_messages,
            "can_add_web_page_previews": perms.can_add_web_page_previews,
            "can_invite_users": perms.can_invite_users,
            "can_pin_messages": perms.can_pin_messages,
            "can_change_info": perms.can_change_info,
            "can_manage_topics": perms.can_manage_topics,
        }
    
        chat = self.get_group_by_chat_id(chat_id)
        current = getattr(chat, "permissions", {}) or {}
        current.update(permissions)
    
        self._update_or_create_group(chat_id, {"permissions": current})

    def update_user_ban(self, user_id: int, status: bool, reason: str | None = None) -> None:
        ban_data = {
            "status": status,
            "reason": reason,
            "since": self.now() if status else None,
        }
        self._update_or_create_user(user_id, {"ban": ban_data})

    def update_user_afk(
        self,
        user_id: int,
        status: bool,
        reason: str | None = None,
        mentioned_msgs: list[int] | None = None,
    ) -> None:
        afk_data = {
            "status": status,
            "reason": reason,
            "duration": self.now() if status else None,
            "mentioned_msgs": mentioned_msgs or [],
        }
        self._update_or_create_user(user_id, {"afk": afk_data})
    
    
    def update_user_afk_message_id(self, user_id: int, message_id: int) -> None:
        try:
            user_data: User = self.get_user_by_user_id(user_id)
            afk_data = user_data.afk
            afk_data.setdefault("mentioned_msgs", []).append(message_id)
            self._update_or_create_user(user_id, {"afk": afk_data})
        except Exception as e:
            print(e)
    
    def add_xp(self, user_id: int, xp: int) -> None:
        try:
            user = User.objects.raw({"user_id": str(user_id)}).first()
            user.xp += xp
            user.save()
        except DoesNotExist:
            self._update_or_create_user(user_id, {"xp": xp})



