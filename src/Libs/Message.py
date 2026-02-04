from __future__ import annotations

from typing import Union, Optional, List, Dict, Any, TYPE_CHECKING, Tuple
from telegram import (
    CallbackQuery,
    Message as PTBMessage,
    ChatMemberUpdated,
)
from telegram.constants import ChatType, ChatMemberStatus
from Helpers.JsonObject import JsonObject

if TYPE_CHECKING:
    from telegram import Chat, User, ChatMember
    from Libs import SuperClient


class Message:
    _media_types: List[str] = [
        "voice",
        "animation",
        "audio",
        "photo",
        "video",
        "document",
        "video_note",
        "sticker",
    ]

    def __init__(
        self,
        client: SuperClient,
        data: Union[PTBMessage, CallbackQuery, ChatMemberUpdated],
    ) -> None:
        self._client: SuperClient = client
        self.is_callback: bool = isinstance(data, CallbackQuery)
        self.is_event: bool = isinstance(data, PTBMessage) and (
            getattr(data, "new_chat_members", None)
            or getattr(data, "left_chat_member", None)
        )

        self._m: Optional[PTBMessage] = (
            data.message
            if self.is_callback
            else (data if isinstance(data, PTBMessage) else None)
        )

        self.chat: Optional[Chat]
        self.chat_id: int
        self.chat_type: str
        self.chat_title: Optional[str]
        self.chat_permissions: Optional[Dict[str, bool]] = None

        if self._m:
            self.chat = self._m.chat
            self.chat_id = self.chat.id
            self.chat_type = self.chat.type
            self.chat_title = (
                self.chat.title if self.chat.type != ChatType.PRIVATE else None
            )
        else:
            self.chat = None
            self.chat_id = 0
            self.chat_type = ""
            self.chat_title = None

        if isinstance(data, ChatMemberUpdated):
            self.sender_raw: Optional[User] = data.from_user
        elif self.is_callback:
            self.sender_raw = data.from_user
        else:
            self.sender_raw = getattr(self._m, "from_user", None)

        self.message_id: Optional[int] = getattr(self._m, "message_id", None)

        if self.is_callback:
            self.message: str = data.data or ""
        else:
            self.message = (
                getattr(self._m, "caption", None) or getattr(self._m, "text", "") or ""
            )

        self.reply_to_message: Optional[PTBMessage] = getattr(
            self._m, "reply_to_message", None
        )

        self.event_type: Optional[str] = None
        self.event_user: Optional[JsonObject] = None
        self.action_by: Optional[JsonObject] = None

        if self.is_event:
            self._greeting()

        self.sender: Optional[JsonObject] = None
        self.reply_to_user: Optional[JsonObject] = None
        self.msg_type: Optional[str] = None
        self.file_id: Optional[str] = None
        self.user_status: Optional[str] = None
        self.urls: List[str] | str = []
        self.numbers: List[int] = []
        self.mentioned: List[JsonObject] = []
        self.user_roles: Dict[int, str] = {}

    def _greeting(self) -> None:
        m: Optional[PTBMessage] = self._m
        if not m:
            return

        if getattr(m, "new_chat_members", None):
            user: User = m.new_chat_members[0]
            self.event_type = "join"
            self.event_user = JsonObject(
                {
                    "user_id": user.id,
                    "user_name": user.username,
                    "user_full_name": user.full_name,
                }
            )
            if m.from_user and m.from_user.id != user.id:
                self.action_by = JsonObject(
                    {
                        "user_id": m.from_user.id,
                        "user_name": m.from_user.username,
                        "user_full_name": m.from_user.full_name,
                    }
                )

        elif getattr(m, "left_chat_member", None):
            user: User = m.left_chat_member
            self.event_type = (
                "kick" if (m.from_user and m.from_user.id != user.id) else "leave"
            )
            self.event_user = JsonObject(
                {
                    "user_id": user.id,
                    "user_name": user.username,
                    "user_full_name": user.full_name,
                }
            )
            if self.event_type == "kick":
                self.action_by = JsonObject(
                    {
                        "user_id": m.from_user.id,
                        "user_name": m.from_user.username,
                        "user_full_name": m.from_user.full_name,
                    }
                )

    async def _get_user_permissions(
        self,
        user_id: int,
    ) -> Tuple[ChatMemberStatus, Optional[Dict[str, bool]]]:
        member: ChatMember = await self._client.get_chat_member(
            self.chat_id,
            user_id,
        )
        permissions: Optional[Dict[str, bool]] = {
            "can_change_info": getattr(member, "can_change_info", True),
            "can_delete_messages": getattr(member, "can_delete_messages", True),
            "can_invite_users": getattr(member, "can_invite_users", True),
            "can_pin_messages": getattr(member, "can_pin_messages", True),
            "can_promote_members": getattr(member, "can_promote_members", True),
            "can_restrict_members": getattr(member, "can_restrict_members", True),
        }
        return member.status, permissions

    async def _get_mentioned_users(self, text: str) -> List[JsonObject]:
        mentioned: List[JsonObject] = []

        for word in text.split():
            if not word.startswith("@"):
                continue
            try:
                user: User = await self._client.get_users(word)
                full_name: str = (
                    f"{user.first_name or ''} {user.last_name or ''}".strip()
                )

                role, perms = await self._get_user_permissions(user.id)

                mentioned.append(
                    JsonObject(
                        {
                            "user_id": user.id,
                            "user_name": user.username,
                            "user_full_name": full_name,
                            "user_role": role,
                            "permissions": perms,
                        }
                    )
                )
            except Exception as e:
                self._client.log.error(
                    f"[ERROR][_get_mentioned_users] Could not resolve {word}: {e}"
                )

        return mentioned

    def _extract_media(self) -> None:
        def _get_file_id(media: Any) -> Optional[str]:
            if isinstance(media, (list, tuple)) and media:
                return media[-1].file_id
            return getattr(media, "file_id", None)

        for src in (self.reply_to_message, self._m):
            if not src:
                continue
            for mtype in self._media_types:
                media: Any = getattr(src, mtype, None)
                if not media:
                    continue
                file_id: Optional[str] = _get_file_id(media)
                if file_id:
                    self.msg_type = mtype
                    self.file_id = file_id
                    return

    async def build(self) -> Message:
        if self.is_event:
            return self

        self._extract_media()
        self.urls = self._client.utils.get_urls(self.message)

        if self.sender_raw:
            role, perms = await self._get_user_permissions(self.sender_raw.id)
            self.sender = JsonObject(
                {
                    "user_id": self.sender_raw.id,
                    "user_name": self.sender_raw.username,
                    "user_full_name": self.sender_raw.full_name,
                    "user_role": role,
                    "permissions": perms,
                }
            )

        if self.reply_to_message and getattr(self.reply_to_message, "from_user", None):
            reply_user: User = self.reply_to_message.from_user
            if reply_user.id != (self.sender_raw.id if self.sender_raw else 0):
                role, perms = await self._get_user_permissions(reply_user.id)
                self.reply_to_user = JsonObject(
                    {
                        "user_id": reply_user.id,
                        "user_name": reply_user.username,
                        "user_full_name": reply_user.full_name,
                        "user_role": role,
                        "permissions": perms,
                    }
                )

        self.mentioned = await self._get_mentioned_users(self.message)
        if self.reply_to_user:
            self.mentioned.append(self.reply_to_user)

        return self
