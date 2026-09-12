"""Panda Tool Blender add-on entry point."""

bl_info = {
    "name": "Panda Tool",
    "author": "Gonsaku",
    "version": (0, 2, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Panda Tool",
    "description": "Small workflow utilities for animation and rigging",
    "category": "Rigging",
}

_REGISTERED_CLASSES = ()


def register():
    import bpy
    from .operators import CLASSES as operator_classes
    from .ui import CLASSES as ui_classes

    global _REGISTERED_CLASSES
    _REGISTERED_CLASSES = (*operator_classes, *ui_classes)
    for cls in _REGISTERED_CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    import bpy

    global _REGISTERED_CLASSES
    for cls in reversed(_REGISTERED_CLASSES):
        bpy.utils.unregister_class(cls)
    _REGISTERED_CLASSES = ()
