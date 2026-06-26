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
        if context.scene.mgr_current_template == "prop_hinge":
            layout.label(text="Prop Hinge Controls")
            layout.prop(context.scene, "mgr_prop_hinge_pivot_x")
            layout.prop(context.scene, "mgr_prop_hinge_base_x")
            layout.prop(context.scene, "mgr_prop_hinge_axis")
            layout.prop(context.scene, "mgr_prop_hinge_open_angle")
            layout.prop(context.scene, "mgr_prop_hinge_swing_direction")
            layout.prop(context.scene, "mgr_prop_hinge_rotation_axis")
            layout.operator("mgr.generate_prop_hinge_landmarks", text="Generate Prop Hinge Landmarks")
            layout.operator("mgr.refresh_prop_hinge_visual_guides", text="Refresh Hinge Visual Guides")
            layout.operator("mgr.commit_prop_hinge_guides", text="Commit Hinge Guides")
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
        layout.operator("mgr.pose_humanoid_stress", text="Pose Humanoid Stress")
        layout.operator("mgr.pose_quadruped_gait", text="Pose Quadruped Gait")
        layout.operator("mgr.pose_quadruped_side_review", text="Pose Quadruped Side Review")
        layout.operator("mgr.pose_tail_creature_reach", text="Pose Tail Creature Reach")
        layout.operator("mgr.pose_tail_creature_side_review", text="Pose Tail Creature Side Review")
        layout.operator("mgr.pose_prop_hinge_open", text="Pose Prop Hinge Open")
        layout.operator("mgr.pose_prop_hinge_side_review", text="Pose Prop Hinge Side Review")
        layout.separator()
        layout.prop(context.scene, "mgr_qa_report_path")
        layout.operator("mgr.write_qa_report", text="Write QA Report")
        layout.separator()
        layout.prop(context.scene, "mgr_preview_output_path")
        layout.operator("mgr.render_front_preview", text="Render Front Preview")
        layout.operator("mgr.render_pose_preview", text="Render Pose Preview")
        layout.separator()
        layout.prop(context.scene, "mgr_unity_export_path")
        layout.operator("mgr.export_unity_fbx", text="Export Unity FBX")
        layout.prop(context.scene, "mgr_unreal_export_path")
        layout.operator("mgr.export_unreal_fbx", text="Export Unreal FBX")
        if context.scene.mgr_landmark_validation_message:
            layout.label(text=context.scene.mgr_landmark_validation_message)
        if context.scene.mgr_weight_cleanup_message:
            layout.label(text=context.scene.mgr_weight_cleanup_message)
        if context.scene.mgr_pose_test_message:
            layout.label(text=context.scene.mgr_pose_test_message)
        if context.scene.mgr_qa_report_message:
            layout.label(text=context.scene.mgr_qa_report_message)
        if context.scene.mgr_preview_message:
            layout.label(text=context.scene.mgr_preview_message)
        if context.scene.mgr_export_message:
            layout.label(text=context.scene.mgr_export_message)


classes = [MGR_PT_main_panel]
