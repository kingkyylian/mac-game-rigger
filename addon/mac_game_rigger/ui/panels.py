import bpy


class MGR_PT_main_panel(bpy.types.Panel):
    bl_label = "Mac Game Rigger"
    bl_idname = "MGR_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Mac Game Rigger"

    def draw(self, context):
        layout = self.layout
        layout.label(text="Mac Game Rigger Alpha")
        layout.label(text="Assisted rigging workbench")
        layout.operator("mgr.analyze_asset", text="Analyze Selected Mesh")


classes = [MGR_PT_main_panel]
