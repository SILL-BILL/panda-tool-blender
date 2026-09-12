"""3D View sidebar panels."""

import bpy


class PANDA_PT_rig_tools(bpy.types.Panel):
    bl_label = "Rig"
    bl_idname = "PANDA_PT_rig_tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Panda Tool"

    def draw(self, context):
        self.layout.operator("panda_tool.create_anchor", icon="BONE_DATA")
        self.layout.operator("panda_tool.disconnect_bones", icon="UNLINKED")


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
        if not obj.panda_vertex_group_scan_complete:
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
