from __future__ import annotations
from typing import Dict
from pymodm import MongoModel, fields


# 👥 Chat (Group) Model
class Chat(MongoModel):
    chat_id: int = fields.CharField(required=True)
    xp: int = fields.IntegerField(required=True, min_value=0, default=0)
    captcha: bool = fields.BooleanField(required=True, default=False)
    events: bool = fields.BooleanField(required=True, default=False)
    mod: bool = fields.BooleanField(required=True, default=False)
    permissions: Dict[str, bool] = fields.DictField(
        required=False,
        blank=True,
        default=dict,
    )


