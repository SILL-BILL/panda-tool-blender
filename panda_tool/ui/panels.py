"""3D View sidebar panels."""

import bpy


class PANDA_PT_apply_modifier(bpy.types.Panel):
    bl_label = "Panda Apply Modifier"
    bl_idname = "PANDA_PT_apply_modifier"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Panda Tool"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        is_mesh = obj is not None and obj.type == "MESH"
        is_object_mode = is_mesh and obj.mode == "OBJECT"
        has_modifiers = is_mesh and len(obj.modifiers) > 0

        if not is_mesh:
            layout.label(text="Select an active Mesh Object.", icon="INFO")
            return

        layout.prop_search(
            obj,
            "panda_apply_modifier_name",
            obj,
            "modifiers",
            text="Modifier",
        )

        shape_keys = obj.data.shape_keys
        shape_key_count = len(shape_keys.key_blocks) if shape_keys else 0
        layout.label(text=f"Shape Keys: {shape_key_count}")
        layout.label(text=f"Vertices: {len(obj.data.vertices)}")

        selected = obj.modifiers.get(obj.panda_apply_modifier_name)
        is_armature = selected is not None and selected.type == "ARMATURE"
        apply_row = layout.row()
        apply_row.enabled = (
            is_object_mode
            and has_modifiers
            and selected is not None
        )
        apply_row.operator("panda.apply_modifier", icon="CHECKMARK")

        if not is_object_mode:
            layout.label(text="Use Object Mode.", icon="INFO")
        elif not has_modifiers:
            layout.label(text="This Object has no Modifiers.", icon="INFO")
        elif is_armature:
            layout.label(text="Current Armature pose will be baked.", icon="ERROR")
            layout.label(text="Armature data itself will not be modified.")


class PANDA_PT_rig_tools(bpy.types.Panel):
    bl_label = "Rig"
    bl_idname = "PANDA_PT_rig_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Panda Tool"

    def draw(self, context):
        layout = self.layout
        layout.operator("panda_tool.create_anchor", icon="BONE_DATA")
        layout.operator("panda_tool.disconnect_bones", icon="UNLINKED")

        layout.separator()
        obj = context.active_object
        is_mesh_object_mode = (
            obj is not None and obj.type == "MESH" and obj.mode == "OBJECT"
        )
        scan_row = layout.row()
        scan_row.enabled = is_mesh_object_mode
        scan_row.operator(
            "panda_tool.scan_unregistered_bones",
            icon="VIEWZOOM",
        )

        if not is_mesh_object_mode:
            layout.label(
                text="Select a Mesh in Object Mode for cleanup.",
                icon="INFO",
            )
            return
        if not getattr(obj, "panda_bone_cleanup_scan_complete", False):
            return

        layout.label(text="Bones Missing Vertex Groups")
        for item in obj.panda_unregistered_bones:
            row = layout.row(align=True)
            row.prop(item, "remove", text=item.bone_name)
            if not item.is_deform:
                row.label(text="Non-Deform", icon="LOCKED")

        count = len(obj.panda_unregistered_bones)
        layout.label(text=f"{count} candidate{'s' if count != 1 else ''} found.")

        selection_row = layout.row(align=True)
        selection_row.enabled = count > 0
        select_all = selection_row.operator(
            "panda_tool.set_unregistered_bone_selection",
            text="All",
        )
        select_all.select = True
        select_none = selection_row.operator(
            "panda_tool.set_unregistered_bone_selection",
            text="None",
        )
        select_none.select = False

        delete_row = layout.row()
        delete_row.enabled = count > 0 and any(
            item.remove for item in obj.panda_unregistered_bones
        )
        delete_row.operator(
            "panda_tool.delete_unregistered_bones",
            icon="TRASH",
        )

        if obj.panda_bone_cleanup_status:
            layout.label(text=obj.panda_bone_cleanup_status, icon="INFO")


class PANDA_PT_vertex_group_tools(bpy.types.Panel):
    bl_label = "Vertex Groups"
    bl_idname = "PANDA_PT_vertex_group_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Panda Tool"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        is_mesh = obj is not None and obj.type == "MESH"

        scan_row = layout.row()
        scan_row.enabled = is_mesh
        scan_row.operator("panda_tool.scan_unused_vertex_groups", icon="VIEWZOOM")

        if not is_mesh:
            layout.label(text="Select an active Mesh Object.", icon="INFO")
            return
        if not getattr(obj, "panda_vertex_group_scan_complete", False):
            return

        layout.separator()
        layout.label(text="Unused Vertex Groups")
        for item in obj.panda_unused_vertex_groups:
            layout.prop(item, "remove", text=item.group_name)

        count = len(obj.panda_unused_vertex_groups)
        count_text = f"{count} unused group{'s' if count != 1 else ''} found."
        layout.label(text=count_text)
        scan_status = (
            count_text if count else "No unused vertex groups found."
        )
        if (
            obj.panda_vertex_group_status
            and obj.panda_vertex_group_status != scan_status
        ):
            layout.label(text=obj.panda_vertex_group_status, icon="INFO")

        remove_row = layout.row()
        remove_row.enabled = count > 0 and any(
            item.remove for item in obj.panda_unused_vertex_groups
        )
        remove_row.operator(
            "panda_tool.remove_unused_vertex_groups",
            icon="TRASH",
        )
