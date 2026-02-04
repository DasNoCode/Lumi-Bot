from __future__ import annotations

import subprocess
from pathlib import Path
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
       self.client.db.add_sticker_sets("dajgsgdsas")
        
        
