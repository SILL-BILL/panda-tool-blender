"""Operators provided by Panda Tool."""

from .create_anchor import PANDA_OT_create_anchor
from .disconnect_bones import PANDA_OT_disconnect_bones


CLASSES = (
    PANDA_OT_create_anchor,
    PANDA_OT_disconnect_bones,
)
