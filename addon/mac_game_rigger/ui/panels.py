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
        layout.separator()
        layout.prop(context.scene, "mgr_landmark_name")
        layout.operator("mgr.create_landmark", text="Create Landmark")
        layout.operator("mgr.mirror_landmarks", text="Mirror Landmarks")
        layout.operator("mgr.clear_landmarks", text="Clear Landmarks")
        layout.separator()
        layout.prop(context.scene, "mgr_current_template")
        layout.operator("mgr.validate_landmarks", text="Validate Landmarks")
        layout.operator("mgr.generate_armature", text="Generate Armature")
        layout.operator("mgr.fix_bone_rolls", text="Fix Bone Rolls")
        layout.operator("mgr.bind_automatic_weights", text="Bind Automatic Weights")
        layout.operator("mgr.apply_capsule_weights", text="Apply Capsule Weights")
        layout.operator("mgr.cleanup_weights", text="Cleanup Weights")
        layout.separator()
        layout.operator("mgr.reset_pose", text="Reset Pose")
        layout.operator("mgr.pose_arm_raise", text="Pose Arm Raise")
        layout.operator("mgr.pose_knee_bend", text="Pose Knee Bend")
        layout.operator("mgr.pose_neck_turn", text="Pose Neck Turn")
        layout.separator()
        layout.prop(context.scene, "mgr_qa_report_path")
        layout.operator("mgr.write_qa_report", text="Write QA Report")
        if context.scene.mgr_landmark_validation_message:
            layout.label(text=context.scene.mgr_landmark_validation_message)
        if context.scene.mgr_weight_cleanup_message:
            layout.label(text=context.scene.mgr_weight_cleanup_message)
        if context.scene.mgr_pose_test_message:
            layout.label(text=context.scene.mgr_pose_test_message)
        if context.scene.mgr_qa_report_message:
            layout.label(text=context.scene.mgr_qa_report_message)


classes = [MGR_PT_main_panel]
