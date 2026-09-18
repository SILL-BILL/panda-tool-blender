"""Safely scan for and remove empty vertex groups from one mesh object."""

import bpy
from bpy.props import BoolProperty, CollectionProperty, StringProperty


def _unused_group_names(obj):
    """Return groups which have no vertex assignment with a positive weight."""
    unused_indices = {group.index for group in obj.vertex_groups}

    for vertex in obj.data.vertices:
        for assignment in vertex.groups:
            if assignment.weight > 0.0:
                unused_indices.discard(assignment.group)
        if not unused_indices:
            break

    return [
        group.name for group in obj.vertex_groups if group.index in unused_indices
    ]


def _refresh_scan_results(obj, previous_selection=None):
    """Replace cached results while optionally preserving checkbox choices."""
    previous_selection = previous_selection or {}
    obj.panda_unused_vertex_groups.clear()

    for group_name in _unused_group_names(obj):
        item = obj.panda_unused_vertex_groups.add()
        item.group_name = group_name
        item.remove = previous_selection.get(group_name, True)

    obj.panda_vertex_group_scan_complete = True


class PANDA_PG_unused_vertex_group(bpy.types.PropertyGroup):
    """One removable group in the most recent scan result."""

    group_name: StringProperty(name="Vertex Group", options={"SKIP_SAVE"})
    remove: BoolProperty(
        name="Remove",
        description="Remove this vertex group",
        default=True,
        options={"SKIP_SAVE"},
    )


class PANDA_OT_scan_unused_vertex_groups(bpy.types.Operator):
    """Find vertex groups which have no vertices with a positive weight"""

    bl_idname = "panda_tool.scan_unused_vertex_groups"
    bl_label = "Scan Unused Groups"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "MESH"

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            self.report({"INFO"}, "Select an active Mesh Object.")
            return {"CANCELLED"}

        # An in-place extension update can leave RNA properties removed by
        # the previous version's unregister callback. Restore them on demand.
        register_properties()
        _refresh_scan_results(obj)
        count = len(obj.panda_unused_vertex_groups)
        if count:
            obj.panda_vertex_group_status = (
                f"{count} unused group{'s' if count != 1 else ''} found."
            )
        else:
            obj.panda_vertex_group_status = "No unused vertex groups found."

        self.report({"INFO"}, obj.panda_vertex_group_status)
        return {"FINISHED"}


class PANDA_OT_remove_unused_vertex_groups(bpy.types.Operator):
    """Remove checked groups which are still unused"""

    bl_idname = "panda_tool.remove_unused_vertex_groups"
    bl_label = "Remove Unused Groups"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (
            obj is not None
            and obj.type == "MESH"
            and getattr(obj, "panda_vertex_group_scan_complete", False)
            and any(
                item.remove
                for item in getattr(obj, "panda_unused_vertex_groups", ())
            )
        )

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            self.report({"INFO"}, "Select an active Mesh Object.")
            return {"CANCELLED"}
        if not getattr(obj, "panda_vertex_group_scan_complete", False):
            self.report({"INFO"}, "Scan unused vertex groups first.")
            return {"CANCELLED"}

        previous_selection = {
            item.group_name: item.remove
            for item in obj.panda_unused_vertex_groups
        }
        selected_names = {
            item.group_name
            for item in obj.panda_unused_vertex_groups
            if item.remove
        }
        if not selected_names:
            self.report({"INFO"}, "No unused vertex groups selected.")
            return {"CANCELLED"}

        # Re-scan immediately before modification. A group that acquired a
        # positive weight since the visible scan must never be removed.
        still_unused = set(_unused_group_names(obj))
        removable_names = selected_names & still_unused

        removed_count = 0
        for group in list(obj.vertex_groups):
            if group.name in removable_names:
                obj.vertex_groups.remove(group)
                removed_count += 1

        _refresh_scan_results(obj, previous_selection)
        if removed_count:
            obj.panda_vertex_group_status = (
                f"{removed_count} unused vertex group"
                f"{'s' if removed_count != 1 else ''} removed."
            )
            self.report({"INFO"}, obj.panda_vertex_group_status)
            return {"FINISHED"}

        obj.panda_vertex_group_status = "No selected unused groups were removed."
        self.report({"INFO"}, obj.panda_vertex_group_status)
        return {"CANCELLED"}


CLASSES = (
    PANDA_PG_unused_vertex_group,
    PANDA_OT_scan_unused_vertex_groups,
    PANDA_OT_remove_unused_vertex_groups,
)


def register_properties():
    if not hasattr(bpy.types.Object, "panda_unused_vertex_groups"):
        bpy.types.Object.panda_unused_vertex_groups = CollectionProperty(
            type=PANDA_PG_unused_vertex_group,
            options={"SKIP_SAVE"},
        )
    if not hasattr(bpy.types.Object, "panda_vertex_group_scan_complete"):
        bpy.types.Object.panda_vertex_group_scan_complete = BoolProperty(
            default=False,
            options={"SKIP_SAVE"},
        )
    if not hasattr(bpy.types.Object, "panda_vertex_group_status"):
        bpy.types.Object.panda_vertex_group_status = StringProperty(
            default="",
            options={"SKIP_SAVE"},
        )


def unregister_properties():
    for property_name in (
        "panda_vertex_group_status",
        "panda_vertex_group_scan_complete",
        "panda_unused_vertex_groups",
    ):
        if hasattr(bpy.types.Object, property_name):
            delattr(bpy.types.Object, property_name)
