"""Operators provided by Panda Tool."""

from .create_anchor import PANDA_OT_create_anchor
from .disconnect_bones import PANDA_OT_disconnect_bones
from .remove_unused_vertex_groups import CLASSES as vertex_group_classes


CLASSES = (
    *vertex_group_classes,
    PANDA_OT_create_anchor,
    PANDA_OT_disconnect_bones,
)
