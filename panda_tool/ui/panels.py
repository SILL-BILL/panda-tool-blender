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
