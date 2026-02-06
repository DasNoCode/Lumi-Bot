from __future__ import annotations

import subprocess
from pathlib import Path
import traceback
from typing import Any, TYPE_CHECKING

from Libs import BaseCommand

if TYPE_CHECKING:
    from Libs import SuperClient, Message
    from Handler import CommandHandler


class Command(BaseCommand):
    def __init__(self, client: SuperClient, handler: CommandHandler) -> None:
        super().__init__(
            client,
            handler,
            {
                "command": "hi",
                "category": "general",
                "description": {"content": "Convert MP4 to WebM"},
            },
        )

    async def exec(self, M: Message, context: list[Any]) -> None:
        image_url = "https://nekos.best/api/v2/waifu/2a115c8c-9bb7-4e53-bc31-c36afa9db494.png"
        text = f'<a href="{image_url}">&#8204;</a>Here is your requested waifu!'
    
        await self.client.send_message(
            chat_id=M.chat_id,
            text=text,
            parse_mode="HTML",
            reply_to_message_id=M.message_id 
        )

        
        
