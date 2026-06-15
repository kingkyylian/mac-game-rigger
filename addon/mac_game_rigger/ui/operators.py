from pathlib import Path

import bpy

from ..core.armature_builder import build_armature_from_template, collect_landmark_positions
from ..core.export_profiles import load_builtin_export_profile
from ..core.fbx_export import export_fbx_with_profile
from ..core.landmarks import Landmark, mirror_landmark, missing_landmarks
from ..core.pose_tests import (
    apply_humanoid_arm_raise,
    apply_humanoid_knee_bend,
    apply_neck_turn,
    reset_pose,
)
from ..core.preview import render_preview_png
from ..core.qa_report import RigQAReport, save_qa_report
from ..core.templates import load_template
from ..core.weight_cleanup import cleanup_mesh_weights
from ..core.weight_cleanup import (
    find_unweighted_vertices,
    find_vertices_over_influence_limit,
)
from ..core.weight_binding import (
    apply_capsule_weights_to_mesh,
    find_mgr_armature,
    selected_meshes,
)


LANDMARK_PREFIX = "MGR_Landmark_"
TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"


class MGR_OT_analyze_asset(bpy.types.Operator):
    bl_idname = "mgr.analyze_asset"
    bl_label = "Analyze Selected Mesh"
    bl_options = {"REGISTER"}

    def execute(self, context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if not selected_meshes:
            self.report({"WARNING"}, "Select at least one mesh to analyze")
            context.scene.pop("mgr_last_analysis", None)
            return {"CANCELLED"}

        mesh = selected_meshes[0]
        message = f"Selected mesh: {mesh.name}"
        context.scene["mgr_last_analysis"] = message
        self.report({"INFO"}, message)
        return {"FINISHED"}


class MGR_OT_create_landmark(bpy.types.Operator):
    bl_idname = "mgr.create_landmark"
    bl_label = "Create Landmark"
    bl_options = {"REGISTER", "UNDO"}

    landmark_name: bpy.props.StringProperty(name="Landmark Name", default="")

    def execute(self, context):
        landmark_name = (self.landmark_name or context.scene.mgr_landmark_name).strip()
        if not landmark_name:
            self.report({"WARNING"}, "Enter a landmark name")
            return {"CANCELLED"}

        bpy.ops.object.empty_add(type="SPHERE", location=context.scene.cursor.location)
        landmark = context.object
        landmark.name = f"{LANDMARK_PREFIX}{landmark_name}"
        landmark.empty_display_size = 0.15
        self.report({"INFO"}, f"Created {landmark.name}")
        return {"FINISHED"}


class MGR_OT_clear_landmarks(bpy.types.Operator):
    bl_idname = "mgr.clear_landmarks"
    bl_label = "Clear Landmarks"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        landmarks = [obj for obj in context.scene.objects if obj.name.startswith(LANDMARK_PREFIX)]
        for landmark in landmarks:
            bpy.data.objects.remove(landmark, do_unlink=True)

        self.report({"INFO"}, f"Cleared {len(landmarks)} landmarks")
        return {"FINISHED"}


class MGR_OT_validate_landmarks(bpy.types.Operator):
    bl_idname = "mgr.validate_landmarks"
    bl_label = "Validate Landmarks"
    bl_options = {"REGISTER"}

    def execute(self, context):
        template, missing = _validate_scene_landmarks(context.scene)

        if missing:
            message = f"Missing landmarks: {', '.join(missing)}"
            _set_validation_message(context.scene, message)
            self.report({"WARNING"}, message)
            return {"FINISHED"}

        message = f"All {template.category} landmarks present"
        _set_validation_message(context.scene, message)
        self.report({"INFO"}, message)
        return {"FINISHED"}


class MGR_OT_generate_armature(bpy.types.Operator):
    bl_idname = "mgr.generate_armature"
    bl_label = "Generate Armature"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        template, missing = _validate_scene_landmarks(context.scene)
        if missing:
            message = f"Missing landmarks: {', '.join(missing)}"
            _set_validation_message(context.scene, message)
            self.report({"WARNING"}, message)
            return {"CANCELLED"}

        armature = build_armature_from_template(
            template,
            collect_landmark_positions(context.scene),
        )
        self.report({"INFO"}, f"Generated {armature.name}")
        return {"FINISHED"}


class MGR_OT_mirror_landmarks(bpy.types.Operator):
    bl_idname = "mgr.mirror_landmarks"
    bl_label = "Mirror Landmarks"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        mirrored_count = 0
        left_landmarks = [
            obj
            for obj in context.scene.objects
            if obj.name.startswith(LANDMARK_PREFIX) and obj.name.endswith(".L")
        ]

        for left_obj in left_landmarks:
            source = Landmark(
                name=left_obj.name.removeprefix(LANDMARK_PREFIX),
                position=tuple(left_obj.location),
            )
            mirrored = mirror_landmark(source)
            target_name = f"{LANDMARK_PREFIX}{mirrored.name}"
            target = bpy.data.objects.get(target_name)
            if target is None:
                bpy.ops.object.empty_add(type="SPHERE", location=mirrored.position)
                target = context.object
                target.name = target_name
                target.empty_display_size = left_obj.empty_display_size
            else:
                target.location = mirrored.position
            target.empty_display_type = "SPHERE"
            mirrored_count += 1

        message = f"Mirrored {mirrored_count} landmarks"
        self.report({"INFO"}, message)
        return {"FINISHED"}


class MGR_OT_fix_bone_rolls(bpy.types.Operator):
    bl_idname = "mgr.fix_bone_rolls"
    bl_label = "Fix Bone Rolls"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        armature = bpy.data.objects.get("MGR_Armature")
        if armature is None or armature.type != "ARMATURE":
            self.report({"WARNING"}, "Create MGR_Armature first")
            context.scene["mgr_last_bone_roll_count"] = 0
            return {"CANCELLED"}

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        armature.select_set(True)
        context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode="EDIT")

        changed_count = 0
        for bone in armature.data.edit_bones:
            if not _uses_humanoid_roll_preset(bone.name):
                continue
            if round(bone.roll, 6) != 0.0:
                changed_count += 1
            bone.roll = 0.0

        bpy.ops.object.mode_set(mode="OBJECT")
        context.scene["mgr_last_bone_roll_count"] = changed_count
        self.report({"INFO"}, f"Fixed roll on {changed_count} bones")
        return {"FINISHED"}


class MGR_OT_bind_automatic_weights(bpy.types.Operator):
    bl_idname = "mgr.bind_automatic_weights"
    bl_label = "Bind Automatic Weights"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        meshes = selected_meshes(context)
        armature = find_mgr_armature(bpy)
        if not meshes:
            self.report({"WARNING"}, "Select at least one mesh")
            return {"CANCELLED"}
        if armature is None:
            self.report({"WARNING"}, "Generate MGR_Armature first")
            return {"CANCELLED"}

        bound_count = 0
        for mesh in meshes:
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
            mesh.select_set(True)
            armature.select_set(True)
            context.view_layer.objects.active = armature
            bpy.ops.object.parent_set(type="ARMATURE_AUTO")
            bound_count += 1

        self.report({"INFO"}, f"Bound {bound_count} mesh objects")
        return {"FINISHED"}


class MGR_OT_apply_capsule_weights(bpy.types.Operator):
    bl_idname = "mgr.apply_capsule_weights"
    bl_label = "Apply Capsule Weights"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        meshes = selected_meshes(context)
        armature = find_mgr_armature(bpy)
        if not meshes:
            self.report({"WARNING"}, "Select at least one mesh")
            context.scene["mgr_last_capsule_weighted_vertices"] = 0
            return {"CANCELLED"}
        if armature is None:
            self.report({"WARNING"}, "Generate MGR_Armature first")
            context.scene["mgr_last_capsule_weighted_vertices"] = 0
            return {"CANCELLED"}

        weighted_vertices = 0
        for mesh in meshes:
            result = apply_capsule_weights_to_mesh(mesh, armature)
            weighted_vertices += result.weighted_vertices

        context.scene["mgr_last_capsule_weighted_vertices"] = weighted_vertices
        self.report({"INFO"}, f"Capsule-weighted {weighted_vertices} vertices")
        return {"FINISHED"}


class MGR_OT_cleanup_weights(bpy.types.Operator):
    bl_idname = "mgr.cleanup_weights"
    bl_label = "Cleanup Weights"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        meshes = selected_meshes(context)
        if not meshes:
            self.report({"WARNING"}, "Select at least one mesh")
            _set_weight_cleanup_message(context.scene, "No mesh selected")
            return {"CANCELLED"}

        totals = {
            "unweighted": 0,
            "over_limit": 0,
            "removed_empty": 0,
            "pruned": 0,
            "normalized": 0,
        }
        for mesh in meshes:
            result = cleanup_mesh_weights(mesh)
            totals["unweighted"] += result.unweighted_vertices
            totals["over_limit"] += result.over_limit_vertices
            totals["removed_empty"] += result.removed_empty_groups
            totals["pruned"] += result.pruned_weights
            totals["normalized"] += result.normalized_vertices

        message = (
            f"unweighted={totals['unweighted']} "
            f"over_limit={totals['over_limit']} "
            f"removed_empty={totals['removed_empty']} "
            f"pruned={totals['pruned']} "
            f"normalized={totals['normalized']}"
        )
        _set_weight_cleanup_message(context.scene, message)
        self.report({"INFO"}, message)
        return {"FINISHED"}


class MGR_OT_reset_pose(bpy.types.Operator):
    bl_idname = "mgr.reset_pose"
    bl_label = "Reset Pose"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        return _execute_pose_test(
            context,
            self,
            reset_pose,
            "Reset pose",
        )


class MGR_OT_pose_arm_raise(bpy.types.Operator):
    bl_idname = "mgr.pose_arm_raise"
    bl_label = "Pose Arm Raise"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        return _execute_pose_test(
            context,
            self,
            apply_humanoid_arm_raise,
            "Arm raise",
        )


class MGR_OT_pose_knee_bend(bpy.types.Operator):
    bl_idname = "mgr.pose_knee_bend"
    bl_label = "Pose Knee Bend"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        return _execute_pose_test(
            context,
            self,
            apply_humanoid_knee_bend,
            "Knee bend",
        )


class MGR_OT_pose_neck_turn(bpy.types.Operator):
    bl_idname = "mgr.pose_neck_turn"
    bl_label = "Pose Neck Turn"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        return _execute_pose_test(
            context,
            self,
            apply_neck_turn,
            "Neck turn",
        )


class MGR_OT_write_qa_report(bpy.types.Operator):
    bl_idname = "mgr.write_qa_report"
    bl_label = "Write QA Report"
    bl_options = {"REGISTER"}

    def execute(self, context):
        output_path = Path(context.scene.mgr_qa_report_path).expanduser()
        report = _build_scene_qa_report(context.scene)
        save_qa_report(report, output_path)
        message = f"Wrote QA report: {output_path}"
        _set_qa_report_message(context.scene, message)
        self.report({"INFO"}, message)
        return {"FINISHED"}


class MGR_OT_render_front_preview(bpy.types.Operator):
    bl_idname = "mgr.render_front_preview"
    bl_label = "Render Front Preview"
    bl_options = {"REGISTER"}

    def execute(self, context):
        return _execute_preview_render(context, self, pose_function=None)


class MGR_OT_render_pose_preview(bpy.types.Operator):
    bl_idname = "mgr.render_pose_preview"
    bl_label = "Render Pose Preview"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        return _execute_preview_render(context, self, pose_function=apply_neck_turn)


class MGR_OT_export_unity_fbx(bpy.types.Operator):
    bl_idname = "mgr.export_unity_fbx"
    bl_label = "Export Unity FBX"
    bl_options = {"REGISTER"}

    def execute(self, context):
        return _execute_fbx_export(
            context,
            self,
            profile_slug="unity_fbx",
            output_path=Path(context.scene.mgr_unity_export_path).expanduser(),
        )


class MGR_OT_export_unreal_fbx(bpy.types.Operator):
    bl_idname = "mgr.export_unreal_fbx"
    bl_label = "Export Unreal FBX"
    bl_options = {"REGISTER"}

    def execute(self, context):
        return _execute_fbx_export(
            context,
            self,
            profile_slug="unreal_fbx",
            output_path=Path(context.scene.mgr_unreal_export_path).expanduser(),
        )


def _execute_pose_test(context, operator, pose_function, label):
    armature = find_mgr_armature(bpy)
    if armature is None:
        message = "Generate MGR_Armature first"
        _set_pose_test_message(context.scene, message)
        operator.report({"WARNING"}, message)
        return {"CANCELLED"}

    result = pose_function(armature)
    if result.missing_bones:
        message = f"Missing pose bones: {', '.join(result.missing_bones)}"
        report_type = {"WARNING"}
    else:
        message = f"{label}: changed={result.changed_bones}"
        report_type = {"INFO"}
    _set_pose_test_message(context.scene, message)
    operator.report(report_type, message)
    return {"FINISHED"}


def _execute_fbx_export(context, operator, profile_slug: str, output_path: Path):
    profile = load_builtin_export_profile(profile_slug)
    export_fbx_with_profile(bpy, output_path, profile)
    report = _build_scene_qa_report(context.scene, export_profile=profile.slug)
    save_qa_report(report, output_path.with_suffix(".qa.json"))
    message = (
        f"Exported {profile.name}: {output_path} "
        f"add_leaf_bones={profile.add_leaf_bones}"
    )
    _set_export_message(context.scene, message)
    operator.report({"INFO"}, message)
    return {"FINISHED"}


def _execute_preview_render(context, operator, pose_function=None):
    if pose_function is not None:
        armature = find_mgr_armature(bpy)
        if armature is not None:
            pose_function(armature)
    output_path = Path(context.scene.mgr_preview_output_path).expanduser()
    render_preview_png(bpy, output_path)
    message = f"Wrote preview PNG: {output_path}"
    _set_preview_message(context.scene, message)
    operator.report({"INFO"}, message)
    return {"FINISHED"}


def _build_scene_qa_report(scene, export_profile=None):
    meshes = [obj for obj in scene.objects if obj.type == "MESH"]
    armature = find_mgr_armature(bpy)
    unweighted_vertices = sum(len(find_unweighted_vertices(mesh)) for mesh in meshes)
    over_limit_vertices = sum(
        len(find_vertices_over_influence_limit(mesh))
        for mesh in meshes
    )
    warnings = []
    errors = []
    if armature is None:
        errors.append("MGR_Armature missing")
    if unweighted_vertices:
        warnings.append(f"Unweighted vertices: {unweighted_vertices}")
    if over_limit_vertices:
        warnings.append(f"Over-limit vertices: {over_limit_vertices}")

    return RigQAReport(
        mesh_count=len(meshes),
        vertex_count=sum(len(mesh.data.vertices) for mesh in meshes),
        bone_count=len(armature.data.bones) if armature is not None else 0,
        unweighted_vertices=unweighted_vertices,
        over_limit_vertices=over_limit_vertices,
        export_profile=export_profile,
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def _uses_humanoid_roll_preset(bone_name):
    return any(
        token in bone_name
        for token in ("Arm", "Hand", "Leg", "Foot")
    )


def _validate_scene_landmarks(scene):
    template_name = scene.mgr_current_template.strip()
    template_path = TEMPLATE_DIR / f"{template_name}.json"
    template = load_template(template_path)
    placed_landmarks = [
        Landmark(
            name=obj.name.removeprefix(LANDMARK_PREFIX),
            position=tuple(obj.location),
        )
        for obj in scene.objects
        if obj.name.startswith(LANDMARK_PREFIX)
    ]
    return template, missing_landmarks(template.required_landmarks, placed_landmarks)


def _set_validation_message(scene, message):
    scene.mgr_landmark_validation_message = message
    scene["mgr_landmark_validation_message"] = message


def _set_weight_cleanup_message(scene, message):
    scene.mgr_weight_cleanup_message = message
    scene["mgr_weight_cleanup_message"] = message


def _set_pose_test_message(scene, message):
    scene.mgr_pose_test_message = message
    scene["mgr_pose_test_message"] = message


def _set_qa_report_message(scene, message):
    scene.mgr_qa_report_message = message
    scene["mgr_qa_report_message"] = message


def _set_preview_message(scene, message):
    scene.mgr_preview_message = message
    scene["mgr_preview_message"] = message


def _set_export_message(scene, message):
    scene.mgr_export_message = message
    scene["mgr_export_message"] = message


def register_properties():
    bpy.types.Scene.mgr_landmark_name = bpy.props.StringProperty(
        name="Landmark Name",
        default="hips",
    )
    bpy.types.Scene.mgr_current_template = bpy.props.StringProperty(
        name="Current Template",
        default="humanoid",
    )
    bpy.types.Scene.mgr_landmark_validation_message = bpy.props.StringProperty(
        name="Landmark Validation",
        default="",
    )
    bpy.types.Scene.mgr_weight_cleanup_message = bpy.props.StringProperty(
        name="Weight Cleanup",
        default="",
    )
    bpy.types.Scene.mgr_pose_test_message = bpy.props.StringProperty(
        name="Pose Test",
        default="",
    )
    bpy.types.Scene.mgr_qa_report_path = bpy.props.StringProperty(
        name="QA Report Path",
        default=str(Path.cwd() / "qa_report.json"),
        subtype="FILE_PATH",
    )
    bpy.types.Scene.mgr_qa_report_message = bpy.props.StringProperty(
        name="QA Report",
        default="",
    )
    bpy.types.Scene.mgr_preview_output_path = bpy.props.StringProperty(
        name="Preview PNG Path",
        default=str(Path.cwd() / "preview.png"),
        subtype="FILE_PATH",
    )
    bpy.types.Scene.mgr_preview_message = bpy.props.StringProperty(
        name="Preview",
        default="",
    )
    bpy.types.Scene.mgr_unity_export_path = bpy.props.StringProperty(
        name="Unity FBX Path",
        default=str(Path.cwd() / "result_unity.fbx"),
        subtype="FILE_PATH",
    )
    bpy.types.Scene.mgr_unreal_export_path = bpy.props.StringProperty(
        name="Unreal FBX Path",
        default=str(Path.cwd() / "result_unreal.fbx"),
        subtype="FILE_PATH",
    )
    bpy.types.Scene.mgr_export_message = bpy.props.StringProperty(
        name="Export",
        default="",
    )


def unregister_properties():
    if hasattr(bpy.types.Scene, "mgr_landmark_name"):
        del bpy.types.Scene.mgr_landmark_name
    if hasattr(bpy.types.Scene, "mgr_current_template"):
        del bpy.types.Scene.mgr_current_template
    if hasattr(bpy.types.Scene, "mgr_landmark_validation_message"):
        del bpy.types.Scene.mgr_landmark_validation_message
    if hasattr(bpy.types.Scene, "mgr_weight_cleanup_message"):
        del bpy.types.Scene.mgr_weight_cleanup_message
    if hasattr(bpy.types.Scene, "mgr_pose_test_message"):
        del bpy.types.Scene.mgr_pose_test_message
    if hasattr(bpy.types.Scene, "mgr_qa_report_path"):
        del bpy.types.Scene.mgr_qa_report_path
    if hasattr(bpy.types.Scene, "mgr_qa_report_message"):
        del bpy.types.Scene.mgr_qa_report_message
    if hasattr(bpy.types.Scene, "mgr_preview_output_path"):
        del bpy.types.Scene.mgr_preview_output_path
    if hasattr(bpy.types.Scene, "mgr_preview_message"):
        del bpy.types.Scene.mgr_preview_message
    if hasattr(bpy.types.Scene, "mgr_unity_export_path"):
        del bpy.types.Scene.mgr_unity_export_path
    if hasattr(bpy.types.Scene, "mgr_unreal_export_path"):
        del bpy.types.Scene.mgr_unreal_export_path
    if hasattr(bpy.types.Scene, "mgr_export_message"):
        del bpy.types.Scene.mgr_export_message


classes = [
    MGR_OT_analyze_asset,
    MGR_OT_create_landmark,
    MGR_OT_clear_landmarks,
    MGR_OT_validate_landmarks,
    MGR_OT_mirror_landmarks,
    MGR_OT_generate_armature,
    MGR_OT_fix_bone_rolls,
    MGR_OT_bind_automatic_weights,
    MGR_OT_apply_capsule_weights,
    MGR_OT_cleanup_weights,
    MGR_OT_reset_pose,
    MGR_OT_pose_arm_raise,
    MGR_OT_pose_knee_bend,
    MGR_OT_pose_neck_turn,
    MGR_OT_write_qa_report,
    MGR_OT_render_front_preview,
    MGR_OT_render_pose_preview,
    MGR_OT_export_unity_fbx,
    MGR_OT_export_unreal_fbx,
]
