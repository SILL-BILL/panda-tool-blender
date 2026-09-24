"""Panda Tool Blender add-on entry point."""

bl_info = {
    "name": "Panda Tool",
    "author": "Gonsaku",
    "version": (0, 6, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Panda Tool",
    "description": "Small workflow utilities for animation and rigging",
    "category": "Rigging",
}

_REGISTERED_OPERATOR_CLASSES = ()
_REGISTERED_UI_CLASSES = ()


def register():
    import bpy
    from .operators import CLASSES as operator_classes
    from .operators.apply_modifier import (
        register_properties as register_apply_modifier_properties,
    )
    from .operators.delete_unregistered_bones import (
        register_properties as register_bone_cleanup_properties,
    )
    from .operators.remove_unused_vertex_groups import register_properties
    from .ui import CLASSES as ui_classes

    global _REGISTERED_OPERATOR_CLASSES, _REGISTERED_UI_CLASSES
    _REGISTERED_OPERATOR_CLASSES = tuple(operator_classes)
    _REGISTERED_UI_CLASSES = tuple(ui_classes)

    # PropertyGroup classes must be registered before properties which use
    # them, and all RNA properties must exist before Blender can draw panels.
    for cls in _REGISTERED_OPERATOR_CLASSES:
        bpy.utils.register_class(cls)
    register_apply_modifier_properties()
    register_properties()
    register_bone_cleanup_properties()
    for cls in _REGISTERED_UI_CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    import bpy
    from .operators.apply_modifier import (
        unregister_properties as unregister_apply_modifier_properties,
    )
    from .operators.delete_unregistered_bones import (
        unregister_properties as unregister_bone_cleanup_properties,
    )
    from .operators.remove_unused_vertex_groups import unregister_properties

    global _REGISTERED_OPERATOR_CLASSES, _REGISTERED_UI_CLASSES
    for cls in reversed(_REGISTERED_UI_CLASSES):
        bpy.utils.unregister_class(cls)
    unregister_bone_cleanup_properties()
    unregister_properties()
    unregister_apply_modifier_properties()
    for cls in reversed(_REGISTERED_OPERATOR_CLASSES):
        bpy.utils.unregister_class(cls)
    _REGISTERED_UI_CLASSES = ()
    _REGISTERED_OPERATOR_CLASSES = ()
