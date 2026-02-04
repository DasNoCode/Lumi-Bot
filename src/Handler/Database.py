from datetime import datetime
from typing import Optional, Any, Dict, List, Union

from pymodm import connect
from pymodm.errors import DoesNotExist

from Models import User, Chat, Command
from Helpers import JsonObject


# 🧠 Database Manager
class Database:
    def __init__(self, url: str):
        connect(url)

    @staticmethod
    def now() -> datetime:
        return datetime.now().timestamp()

    # --- Create or update a user ---
    def _update_or_create_user(self, user_id: int, updates: dict) -> None:
        try:
            user = User.objects.raw({"user_id": str(user_id)}).first()
            for key, value in updates.items():
                setattr(user, key, value)
            user.save()
        except DoesNotExist:
            updates["user_id"] = str(user_id)
            updates["created_at"] = self.now()
            User(**updates).save()

    # --- Create or update a group ---
    def _update_or_create_group(self, chat_id: int, updates: dict) -> None:
        try:
            chat = Chat.objects.raw({"chat_id": str(chat_id)}).first()
            for key, value in updates.items():
                setattr(chat, key, value)
            chat.save()
        except DoesNotExist:
            updates["chat_id"] = str(chat_id)
            Chat(**updates).save()

    # --- Update user ban data ---
    def update_user_ban(self, user_id: int, status: bool, reason: str = None) -> None:
        ban_data = {
            "status": status,
            "reason": reason,
            "since": self.now() if status else None,
        }
        self._update_or_create_user(user_id, {"ban": ban_data})

    # --- Update AFK data ---
    def update_user_afk(
        self,
        user_id: int,
        status: bool,
        reason: str = None,
        mentioned_msgs: Optional[List[int]] = None,
    ) -> None:
        afk_data = {
            "status": status,
            "reason": reason,
            "duration": self.now() if status else None,
            "mentioned_msgs": mentioned_msgs or [],
        }
        self._update_or_create_user(user_id, {"afk": afk_data})

    # --- Append a message ID to the user's AFK msg list ---
    def update_user_afk_message_id(self, user_id: int, message_id: int) -> None:
        try:
            user_data: User = self.get_user_by_user_id(user_id)
            afk_data = user_data.afk
            afk_data.setdefault("mentioned_msgs", []).append(message_id)
            self._update_or_create_user(user_id, {"afk": afk_data})
        except Exception as e:
            print(e)

    # --- update user XP (creat new user if new) ---
    def add_xp(self, user_id: int, xp: int) -> None:
        try:
            user = User.objects.raw({"user_id": str(user_id)}).first()
            user.xp += xp
            user.save()
        except DoesNotExist:
            self._update_or_create_user(user_id, {"xp": xp})

    def get_user_by_user_id(self, user_id):
        try:
            return User.objects.raw({"user_id": str(user_id)}).first()
        except DoesNotExist:
            self._update_or_create_user(user_id, {})
            return User.objects.raw({"user_id": str(user_id)}).first()

    # --- get the group by chat ID ---
    def get_group_by_chat_id(self, chat_id: int) -> Any:
        try:
            return Chat.objects.raw({"chat_id": str(chat_id)}).first()
        except DoesNotExist:
            self._update_or_create_group(chat_id, {})
            return JsonObject({"chat_id": str(chat_id), "mod": False, "events": False})

    # --- group greeting events ---
    def greetings(self, chat_id: int, events_status: bool) -> None:
        self._update_or_create_group(chat_id, {"events": events_status})

    # --- group moderator mode ---
    def set_group_mod(self, chat_id: int, mod_status: bool) -> None:
        self._update_or_create_group(chat_id, {"mod": mod_status})

    # --- enable / disable bot command ---
    def enable_command(self, cmd_name: str, enable: bool, reason: str | None = None) -> None:
        try:
            command = Command.objects.raw({"cmd_name": cmd_name}).first()
            command.enable = enable
            command.reason = reason
            command.save()
        except DoesNotExist:
            Command(
                cmd_name=cmd_name,
                enable=enable,
                reason=reason
            ).save()

    
    # --- cmd info ---
    def get_cmd_info(self, cmd_name: str) -> Union[Command, JsonObject]:
        try:
            return Command.objects.raw({"cmd_name": cmd_name}).first()
        except DoesNotExist:
            Command(
                cmd_name=cmd_name,
                enable=True,
                reason=None
            ).save()
            return JsonObject(
                {
                    "cmd_name": cmd_name,
                    "enable": True,
                    "reason": None
                }
            )

    def add_sticker_sets(
        self,
        sticker_sets_name: str,
    ) -> list[str]:
        command: Command = Command.objects.first()
        if sticker_sets_name not in command.sticker_sets:
            command.sticker_sets.append(sticker_sets_name)
    
        command.save()
        return command.sticker_sets

                
    def delete_sticker_set(
        self,
        sticker_set_name: str,
    ) -> bool:
        try:
            command: Command = Command.objects.first()
    
            if sticker_set_name not in command.sticker_sets:
                return False
    
            command.sticker_sets.remove(sticker_set_name)
            command.save()
            return True
    
        except DoesNotExist:
            return False
            
    # --- get all users data ---
    def get_all_users_data(self, field: Optional[str] = None) -> List[Dict[str, Any]]:
        query = User.objects.all()
        results: List[Dict[str, Any]] = []

        for user in query:
            if field:
                user_dict = {
                    "user_id": getattr(user, "user_id", None),
                    field: getattr(user, field, 0),
                }
            else:
                user_dict = user.to_son().to_dict()
            results.append(user_dict)

        return results
