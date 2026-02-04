from __future__ import annotations
from pymodm import MongoModel, fields
from datetime import datetime
from zoneinfo import ZoneInfo

# ⚙️ Command Model
class Command(MongoModel):
    cmd_name: str = fields.CharField(required=True)
    enable: bool = fields.BooleanField(required=True, default=True)
    reason: str = fields.CharField(required=False, blank=True, default=None)
    sticker_sets: list[str] = fields.ListField(fields.CharField(),required=False,blank=True,default=list,)
    created_at: datetime = fields.DateTimeField(required=True, default=lambda: datetime.now().timestamp())

