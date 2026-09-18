"""Delete bones absent from a target mesh while preserving surviving rest transforms."""

import bpy
from bpy.props import BoolProperty, CollectionProperty, PointerProperty, StringProperty


def _find_armature(mesh_obj):
    """Return the armature associated with a mesh through parenting or a modifier."""
    if mesh_obj is None or mesh_obj.type != "MESH":
        return None
    return mesh_obj.find_armature()


def _unregistered_bone_names(mesh_obj, armature_obj):
    """Return armature bone names absent from the mesh's vertex groups."""
    registered_names = {group.name for group in mesh_obj.vertex_groups}
    return [
        bone.name
        for bone in armature_obj.data.bones
        if bone.name not in registered_names
    ]


def _refresh_scan_results(mesh_obj, armature_obj, previous_selection=None):
    """Refresh cached candidates while retaining explicit checkbox choices."""
    previous_selection = previous_selection or {}
    mesh_obj.panda_unregistered_bones.clear()

    for bone_name in _unregistered_bone_names(mesh_obj, armature_obj):
        bone = armature_obj.data.bones[bone_name]
        item = mesh_obj.panda_unregistered_bones.add()
        item.bone_name = bone_name
        item.is_deform = bone.use_deform
        item.remove = previous_selection.get(bone_name, bone.use_deform)

    mesh_obj.panda_bone_cleanup_armature = armature_obj
    mesh_obj.panda_bone_cleanup_scan_complete = True


def _nearest_surviving_parent(parent_name, parent_names, delete_names):
    """Walk upward through deleted bones to find the closest surviving parent."""
    while parent_name in delete_names:
        parent_name = parent_names.get(parent_name)
    return parent_name


def _delete_bones_keep_rest_transform(context, armature_obj, delete_names):
    """Delete edit bones and preserve every surviving bone's rest-space shape."""
    view_layer = context.view_layer
    original_active = view_layer.objects.active
    original_selected = list(context.selected_objects)

    try:
        bpy.ops.object.select_all(action="DESELECT")
        armature_obj.select_set(True)
        view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode="EDIT")

        edit_bones = armature_obj.data.edit_bones
        delete_names = {name for name in delete_names if edit_bones.get(name)}
        parent_names = {
            bone.name: bone.parent.name if bone.parent else None
            for bone in edit_bones
        }
        active_name = edit_bones.active.name if edit_bones.active else None

        survivors = {}
        for bone in edit_bones:
            if bone.name in delete_names:
                continue
            survivors[bone.name] = {
                "parent": parent_names[bone.name],
                "head": bone.head.copy(),
                "tail": bone.tail.copy(),
                "roll": bone.roll,
                "use_connect": bone.use_connect,
                "select": bone.select,
                "select_head": bone.select_head,
                "select_tail": bone.select_tail,
            }

        for bone_name in list(delete_names):
            bone = edit_bones.get(bone_name)
            if bone is not None:
                edit_bones.remove(bone)

        for bone_name, snapshot in survivors.items():
            bone = edit_bones.get(bone_name)
            if bone is None:
                continue

            original_parent = snapshot["parent"]
            parent_name = _nearest_surviving_parent(
                original_parent,
                parent_names,
                delete_names,
            )
            bone.use_connect = False
            bone.parent = edit_bones.get(parent_name) if parent_name else None
            bone.head = snapshot["head"]
            bone.tail = snapshot["tail"]
            bone.roll = snapshot["roll"]

            # Connected can remain enabled only when the original parent was
            # not removed. Reparented children are disconnected so Blender
            # cannot snap their heads and change the preserved transform.
            if snapshot["use_connect"] and parent_name == original_parent:
                bone.use_connect = True

            bone.select = snapshot["select"]
            bone.select_head = snapshot["select_head"]
            bone.select_tail = snapshot["select_tail"]

        if active_name and active_name not in delete_names:
            edit_bones.active = edit_bones.get(active_name)

        bpy.ops.object.mode_set(mode="OBJECT")
    finally:
        if armature_obj.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        for obj in original_selected:
            if obj.name in view_layer.objects:
                obj.select_set(True)
        if original_active and original_active.name in view_layer.objects:
            view_layer.objects.active = original_active


class PANDA_PG_unregistered_bone(bpy.types.PropertyGroup):
    """One bone absent from the target mesh's vertex groups."""

    bone_name: StringProperty(name="Bone", options={"SKIP_SAVE"})
    remove: BoolProperty(
        name="Remove",
        description="Delete this bone",
        default=True,
        options={"SKIP_SAVE"},
    )
    is_deform: BoolProperty(default=True, options={"SKIP_SAVE"})


class PANDA_OT_scan_unregistered_bones(bpy.types.Operator):
    """Find armature bones absent from the active mesh's vertex groups"""

    bl_idname = "panda_tool.scan_unregistered_bones"
    bl_label = "Scan Unregistered Bones"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "MESH" and obj.mode == "OBJECT"

    def execute(self, context):
        mesh_obj = context.active_object
        if mesh_obj is None or mesh_obj.type != "MESH" or mesh_obj.mode != "OBJECT":
            self.report({"INFO"}, "Select a Mesh Object in Object Mode.")
            return {"CANCELLED"}

        # Recover RNA properties if an in-place extension update let the
        # previous version unregister them after this version was loaded.
        register_properties()
        armature_obj = _find_armature(mesh_obj)
        if armature_obj is None:
            self.report({"WARNING"}, "The active Mesh has no associated Armature.")
            return {"CANCELLED"}

        _refresh_scan_results(mesh_obj, armature_obj)
        count = len(mesh_obj.panda_unregistered_bones)
        if count:
            status = f"{count} unregistered bone{'s' if count != 1 else ''} found."
        else:
            status = "No unregistered bones found."
        mesh_obj.panda_bone_cleanup_status = status
        self.report({"INFO"}, status)
        return {"FINISHED"}


class PANDA_OT_set_unregistered_bone_selection(bpy.types.Operator):
    """Check or uncheck all visible unregistered-bone candidates"""

    bl_idname = "panda_tool.set_unregistered_bone_selection"
    bl_label = "Set Bone Cleanup Selection"

    select: BoolProperty(default=True, options={"SKIP_SAVE"})

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        candidates = getattr(obj, "panda_unregistered_bones", ()) if obj else ()
        return (
            obj is not None
            and obj.type == "MESH"
            and obj.mode == "OBJECT"
            and getattr(obj, "panda_bone_cleanup_scan_complete", False)
            and len(candidates) > 0
        )

    def execute(self, context):
        for item in context.active_object.panda_unregistered_bones:
            item.remove = self.select
        return {"FINISHED"}


class PANDA_OT_delete_unregistered_bones(bpy.types.Operator):
    """Delete checked bones after confirming they remain unregistered"""

    bl_idname = "panda_tool.delete_unregistered_bones"
    bl_label = "Delete Checked Bones"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        candidates = getattr(obj, "panda_unregistered_bones", ()) if obj else ()
        return (
            obj is not None
            and obj.type == "MESH"
            and obj.mode == "OBJECT"
            and getattr(obj, "panda_bone_cleanup_scan_complete", False)
            and any(item.remove for item in candidates)
        )

    def execute(self, context):
        mesh_obj = context.active_object
        if mesh_obj is None or mesh_obj.type != "MESH" or mesh_obj.mode != "OBJECT":
            self.report({"ERROR"}, "Select a Mesh Object in Object Mode.")
            return {"CANCELLED"}
        if not getattr(mesh_obj, "panda_bone_cleanup_scan_complete", False):
            self.report({"INFO"}, "Scan unregistered bones first.")
            return {"CANCELLED"}

        armature_obj = _find_armature(mesh_obj)
        if armature_obj is None:
            self.report({"WARNING"}, "The active Mesh has no associated Armature.")
            return {"CANCELLED"}
        if armature_obj != mesh_obj.panda_bone_cleanup_armature:
            self.report({"WARNING"}, "The associated Armature changed. Scan again.")
            return {"CANCELLED"}

        previous_selection = {
            item.bone_name: item.remove
            for item in mesh_obj.panda_unregistered_bones
        }
        selected_names = {
            item.bone_name
            for item in mesh_obj.panda_unregistered_bones
            if item.remove
        }
        still_unregistered = set(_unregistered_bone_names(mesh_obj, armature_obj))
        removable_names = selected_names & still_unregistered
        if not removable_names:
            _refresh_scan_results(mesh_obj, armature_obj, previous_selection)
            mesh_obj.panda_bone_cleanup_status = "No checked bones were deleted."
            self.report({"INFO"}, mesh_obj.panda_bone_cleanup_status)
            return {"CANCELLED"}

        _delete_bones_keep_rest_transform(context, armature_obj, removable_names)
        _refresh_scan_results(mesh_obj, armature_obj, previous_selection)

        count = len(removable_names)
        status = f"Deleted {count} bone{'s' if count != 1 else ''}."
        mesh_obj.panda_bone_cleanup_status = status
        self.report({"INFO"}, status)
        return {"FINISHED"}


CLASSES = (
    PANDA_PG_unregistered_bone,
    PANDA_OT_scan_unregistered_bones,
    PANDA_OT_set_unregistered_bone_selection,
    PANDA_OT_delete_unregistered_bones,
)


def register_properties():
    if not hasattr(bpy.types.Object, "panda_unregistered_bones"):
        bpy.types.Object.panda_unregistered_bones = CollectionProperty(
            type=PANDA_PG_unregistered_bone,
            options={"SKIP_SAVE"},
        )
    if not hasattr(bpy.types.Object, "panda_bone_cleanup_scan_complete"):
        bpy.types.Object.panda_bone_cleanup_scan_complete = BoolProperty(
            default=False,
            options={"SKIP_SAVE"},
        )
    if not hasattr(bpy.types.Object, "panda_bone_cleanup_armature"):
        bpy.types.Object.panda_bone_cleanup_armature = PointerProperty(
            type=bpy.types.Object,
            options={"SKIP_SAVE"},
        )
    if not hasattr(bpy.types.Object, "panda_bone_cleanup_status"):
        bpy.types.Object.panda_bone_cleanup_status = StringProperty(
            default="",
            options={"SKIP_SAVE"},
        )


def unregister_properties():
    for property_name in (
        "panda_bone_cleanup_status",
        "panda_bone_cleanup_armature",
        "panda_bone_cleanup_scan_complete",
        "panda_unregistered_bones",
    ):
        if hasattr(bpy.types.Object, property_name):
            delattr(bpy.types.Object, property_name)
