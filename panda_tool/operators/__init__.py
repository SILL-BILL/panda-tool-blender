"""Operators provided by Panda Tool."""

from .apply_modifier import CLASSES as apply_modifier_classes
from .create_anchor import PANDA_OT_create_anchor
from .delete_unregistered_bones import CLASSES as bone_cleanup_classes
from .disconnect_bones import PANDA_OT_disconnect_bones
from .remove_unused_vertex_groups import CLASSES as vertex_group_classes


CLASSES = (
    *apply_modifier_classes,
    *vertex_group_classes,
    *bone_cleanup_classes,
    PANDA_OT_create_anchor,
    PANDA_OT_disconnect_bones,
)
