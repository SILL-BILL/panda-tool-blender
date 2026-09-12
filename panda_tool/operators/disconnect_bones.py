"""Disconnect selected edit bones while preserving their parent relationships."""

import bpy


class PANDA_OT_disconnect_bones(bpy.types.Operator):
    """Disable Connected for the selected edit bones"""

    bl_idname = "panda_tool.disconnect_bones"
    bl_label = "Disconnect Bones"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "ARMATURE" and obj.mode == "EDIT"

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "ARMATURE" or obj.mode != "EDIT":
            self.report({"ERROR"}, "Select an armature in Edit Mode.")
            return {"CANCELLED"}

        selected = [bone for bone in obj.data.edit_bones if bone.select]
        if not selected:
            self.report({"WARNING"}, "No bones selected.")
            return {"CANCELLED"}

        for bone in selected:
            bone.use_connect = False

        count = len(selected)
        self.report(
            {"INFO"},
            f"Disconnected {count} bone{'s' if count != 1 else ''}.",
        )
        return {"FINISHED"}
