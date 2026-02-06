from __future__ import annotations
import asyncio
import traceback
from datetime import datetime
import os
import importlib.util
from typing import List, Dict, Any, TYPE_CHECKING
import telegram
import random
from Helpers import JsonObject, get_rank

if TYPE_CHECKING:
    from Libs import SuperClient, Message, BaseCommand
    from Models import Command, User


class CommandHandler:
    def __init__(self, client: SuperClient) -> None:

        self._client: SuperClient = client
        self._commands: Dict[str, BaseCommand] = {}

    #--- 🔍 Argument Parser ---
    def _parse_args(self, raw: str) -> Dict[str, Any]:
        parts: List[str] = raw.split(" ")
        cmd: str = ""
        if parts:
            first: str = parts[0]
        
            if first.startswith(self._client.config.prefix):
                cmd = parts.pop(0)[len(self._client.config.prefix):].lower()
            elif first.startswith("cmd:"):
                cmd = parts.pop(0)[4:].lower()
        text: str = " ".join(parts)
        flags: Dict[str, str] = {}
    
        i: int = 0
        while i < len(parts):
            part: str = parts[i]
    
            if ":" in part and not part.startswith(":"):
                key, value = part.split(":", 1)
                i += 1
    
                while i < len(parts) and ":" not in parts[i]:
                    value += f" {parts[i]}"
                    i += 1
    
                flags[key] = value
            else:
                i += 1
    
        return {
            "cmd": cmd,
            "text": text,
            "flags": flags,
            "raw": raw,
        }
        
    # --- Command Loader ---
    def load_commands(self, folder_path: str) -> None:
        self._client.log.info("Loading commands...")
        all_files: list[str] = self._client.utils.readdir_recursive(folder_path)
    
        for file_path in all_files:
            if not file_path.endswith(".py") or os.path.basename(file_path).startswith("_"):
                continue
    
            try:
                module_name: str = os.path.splitext(os.path.basename(file_path))[0]
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if not spec or not spec.loader:
                    continue
    
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
    
                CommandClass = getattr(module, "Command", None)
                if CommandClass is None:
                    continue 
    
                instance: BaseCommand = CommandClass(self._client, self)
                self._commands[instance.config.command] = instance
    
                category: str = instance.config.get("category", "Uncategorized")
                self._client.log.info(
                    f"✅ Loaded: {instance.config.command} from {category}"
                )
    
            except Exception as e:
                self._client.log.error(f"[ERROR] Failed to load {file_path}: {e}")
    
        self._client.log.info(f"✅ Successfully loaded {len(self._commands)} commands.")


    # --- Main Handler ---
    async def handler(self, M: Message) -> None:
        is_command: bool
        raw = M.message
        if getattr(M, "is_callback", False):
            is_command = True
        else:
            is_command = raw.startswith(self._client.config.prefix)
        context: JsonObject = JsonObject(self._parse_args(raw))
        msg_type: str = "CMD" if is_command else "MSG"
        chat_name: str = M.chat_title if M.chat_type == "supergroup" else "private"
        timestamp: int = datetime.now().date()
        get_user = lambda uid: self._client.db.get_user_by_user_id(
            uid or M.sender.user_id
        )

        sender: User = get_user(M.sender.user_id)

        # --- AFK Check ---
        if sender.afk["status"]:
            if M.message[1:] == "afk":
                return
        
            now_ts: int = int(datetime.now().second)
            afk_duration: int = (int(now_ts - sender.afk["duration"]))
            user_name: str = (
                M.sender.user_name
                or M.sender.user_full_name
                or "User"
            )
        
            text: str = (
                f"@{user_name} "
                f"{random.choice(['re-active', 'returned', 'came back', 're-appeared'])} "
                f"after {self._client.utils.format_duration(afk_duration)}!"
            )
        
            msgs: list[int] = sender.afk.get("mentioned_msgs", [])
            if msgs:
                chat_id = str(M.chat_id).replace("-100", "", 1)
                text += "\n\nTagged messages:\n"
                text += "\n".join(
                    f"{i}. https://t.me/c/{chat_id}/{msg}"
                    for i, msg in enumerate(msgs, 1)
                )
        
            await self._client.send_message(
                chat_id=M.chat_id,
                text=text,
                reply_to_message_id=M.message_id,
            )
            # --- Disable AFK ---
            self._client.db.update_user_afk(M.sender.user_id, False, None, [])

        # --- Command or Message Logging ---
        if is_command:
            self._client.log.info(
                f"[{msg_type}] {self._client.config.prefix}{context.cmd} from "
                f"@{getattr(M.sender, 'user_name', 'user_full_name')} in {chat_name} at {timestamp}"
            )
        else:
            return self._client.log.info(
                f"[{msg_type}] from {M.sender.user_name} in {chat_name} at {timestamp}"
            )
             
        # --- Empty Command ---
        if M.message == self._client.config.prefix:
            return await self._client.send_message(
                chat_id=M.chat_id,
                text=f"Please enter a command starting with {self._client.config.prefix}.",
                reply_to_message_id=M.message_id,
            )

        # --- Command Resolver ---
        cmd: BaseCommand | None = self._commands.get(context.cmd.lower()) or next(
            (
                c
                for c in self._commands.values()
                if context.cmd.lower() in getattr(c.config, "aliases", [])
            ),
            None,
        )

        if not cmd:
            return await self._client.send_message(
                chat_id=M.chat_id,
                text=f"❌ Unknown command! Use {self._client.config.prefix}help to see all available commands.",
                reply_to_message_id=M.message_id,
            )

        # --- Ban Check ---
        if sender.ban["status"]:
            banned_at = sender.ban.get("since", None)
            banned_at_str = (
                banned_at.strftime("%Y-%m-%d %H:%M:%S (%z)") if banned_at else "Unknown"
            )
            return await self._client.send_message(
                chat_id=M.chat_id,
                text=(
                    "<blockquote>"
                    "🚫 <b>Oops! You're banned from using this bot.</b>\n\n"
                    f"📝 <b>Reason:</b> {sender.ban['reason']}\n"
                    f"🕒 <b>Banned at:</b> {banned_at_str}\n\n"
                    "Contact admin if this is a mistake."
                    "</blockquote>"
                ),
                reply_to_message_id=M.message_id,
                parse_mode=telegram.constants.ParseMode.HTML,
            )

        # --- Command Enabled Check ---
        command_info: dict[str, Any] = self._client.db.get_cmd_info(cmd.config.command)
        
        if not command_info.get("enabled", True):
            reason: str | None = command_info.get("reason")
        
            return await self._client.send_message(
                chat_id=M.chat_id,
                text=(
                    f"<blockquote>"
                    f"Command <b>{cmd.config.command}</b> is currently disabled.\n\n"
                    f"└📝 Reason: {reason or 'No reason provided.'}"
                    f"</blockquote>"
                ),
                parse_mode=telegram.constants.ParseMode.HTML,
            )

        # --- Chat/Private Command Validation ---
        if getattr(cmd.config, "OnlyChat", False) and M.chat_type == "private":
            return await self._client.send_message(
                chat_id=M.chat_id,
                text="👥 Chat-only command. Try this in a chat.",
                reply_to_message_id=M.message_id,
            )

        if getattr(cmd.config, "OnlyChat", True) == "chat":
            return await self._client.send_message(
                chat_id=M.chat_id,
                text="💬 Please use this command in private chat only.",
                reply_to_message_id=M.message_id,
            )

        # --- Developer-only Command ---
        if (
            getattr(cmd.config, "DevOnly", False)
            and M.Info.Sender.User not in self._client.config.mods
        ):
            return await self._client.send_message(
                chat_id=M.chat_id,
                text="⚠️ Oops! This command is only for developers.",
                reply_to_message_id=M.message_id,
            )

        # --- Admin Command Validation ---
        required_perms: List[str] = getattr(cmd.config, "admin_permissions", [])
        
        if getattr(cmd.config, "OnlyAdmin", False):
            for perm in required_perms:
                bot_perm: bool = await self._client.get_chat_member(M.chat_id, self._client.bot_user_id)
                if not getattr(bot_perm, perm, True):
                    return await self._client.send_message(
                        chat_id=M.chat_id,
                        text=f"🤖 Bot must have '{perm}' permission to execute this command.",
                        reply_to_message_id=M.message_id,
                    )
                    
        if M.sender.user_role == "admin":
            for perm in required_perms:
                has_perm: bool = M.sender.permissions.get(perm)
                if not has_perm:
                    return await self._client.send_message(
                        chat_id=M.chat_id,
                        text=f"❌ You must have '{perm}' permission to run this command.",
                        reply_to_message_id=M.message_id,
                    )

        # --- Execute Command ---
        await cmd.exec(M, context)

        # --- Mention AFK Users ---
        users: list[User] = []
        
        if M.reply_to_user:
            users.append(M.reply_to_user)
        elif M.mentioned:
            users.extend(M.mentioned)
        
        for mentioned_user in users:
            mentioned_data: User = get_user(mentioned_user.user_id)
            afk_info: dict[str, Any] = mentioned_data.afk
        
            if not afk_info.get("status"):
                continue
        
            afk_reason: str | None = afk_info.get("reason")
        
            self._client.db.update_user_afk_message_id(
                mentioned_user.user_id,
                M.message_id,
            )
            await self._client.send_message(
                chat_id=M.chat_id,
                text=(
                    f"@{mentioned_user.user_name or mentioned_user.user_full_name} "
                    "is currently AFK. 💤"
                    + (f"\nReason: {afk_reason}" if afk_reason else "")
                ),
                reply_to_message_id=M.message_id,
            )
            return

        # --- XP & Rank System ---
        if getattr(cmd.config, "xp", None):
            self._client.db.add_xp(M.sender.user_id, cmd.config.xp)
            xp: int = sender.xp + cmd.config.xp
            old_level: Dict[str, Any] = get_rank(sender.xp)
            new_level: Dict[str, Any] = get_rank(xp)
            if old_level["level"] != new_level["level"]:
                rank_cmd: BaseCommand = self._commands.get("rank")
                if rank_cmd:
                    await rank_cmd.exec(M, self._parse_args(f" caption:@{M.sender.user_name or M.sender.user_full_name} you levelled up 🎉!\n{old_level['level']} -> {new_level['level']}"))
                
    