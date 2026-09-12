"""Panda Tool Blender add-on entry point."""

bl_info = {
    "name": "Panda Tool",
    "author": "Gonsaku",
    "version": (0, 3, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Panda Tool",
    "description": "Small workflow utilities for animation and rigging",
    "category": "Rigging",
}

_REGISTERED_CLASSES = ()


def register():
    import bpy
    from .operators import CLASSES as operator_classes
    from .operators.remove_unused_vertex_groups import register_properties
    from .ui import CLASSES as ui_classes

    global _REGISTERED_CLASSES
    _REGISTERED_CLASSES = (*operator_classes, *ui_classes)
    for cls in _REGISTERED_CLASSES:
        bpy.utils.register_class(cls)
    register_properties()


def unregister():
    import bpy
    from .operators.remove_unused_vertex_groups import unregister_properties

    global _REGISTERED_CLASSES
    unregister_properties()
    for cls in reversed(_REGISTERED_CLASSES):
        bpy.utils.unregister_class(cls)
    _REGISTERED_CLASSES = ()
