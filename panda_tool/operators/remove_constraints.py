"""Remove all constraints from selected objects or selected pose bones."""

import bpy


class PANDA_OT_remove_constraints(bpy.types.Operator):
    """Remove all constraints from the selection in Object or Pose Mode"""

    bl_idname = "panda_tool.remove_constraints"
    bl_label = "Remove Constraints"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.mode == "OBJECT":
            selected = context.selected_objects
        elif context.mode == "POSE":
            selected = context.selected_pose_bones
        else:
            cls.poll_message_set("Use Object Mode or Pose Mode.")
            return False
        if not selected:
            cls.poll_message_set("Select at least one object or pose bone.")
            return False
        return True

    def execute(self, context):
        if context.mode == "OBJECT":
            selected = list(context.selected_objects)
            target_label = "objects"
        elif context.mode == "POSE":
            selected = list(context.selected_pose_bones or ())
            target_label = "bones"
        else:
            self.report({"WARNING"}, "Use Object Mode or Pose Mode.")
            return {"CANCELLED"}

        if not selected:
            self.report({"WARNING"}, "Select at least one object or pose bone.")
            return {"CANCELLED"}

        # Validate the whole selection before removing anything. Overrides can
        # contain inherited constraints which cannot safely be removed.
        for target in selected:
            owner = target.id_data
            if not owner.is_editable or owner.override_library is not None:
                self.report(
                    {"WARNING"},
                    f"Cannot edit constraints on '{owner.name}': "
                    "linked data and library overrides are not supported.",
                )
                return {"CANCELLED"}

        removed_count = sum(len(target.constraints) for target in selected)
        if removed_count:
            # Individual remove() also deletes associated animation/Drivers
            # in Blender 5.1. Clear APIs preserve those data and their paths.
            if context.mode == "OBJECT":
                for target in selected:
                    target.constraints.clear()
            else:
                # PoseBoneConstraints has no clear(). Use Blender's selected
                # pose-bone operator without an extra nested Undo checkpoint.
                if bpy.ops.pose.constraints_clear("EXEC_DEFAULT", False) != {"FINISHED"}:
                    self.report({"WARNING"}, "Could not remove pose bone constraints.")
                    return {"CANCELLED"}

        if removed_count:
            self.report(
                {"INFO"},
                f"Removed {removed_count} constraints from "
                f"{len(selected)} {target_label}.",
            )
        else:
            self.report({"INFO"}, "No constraints found.")
        return {"FINISHED"}
