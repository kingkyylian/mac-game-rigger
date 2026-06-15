from pathlib import Path

import bpy

from ..core.armature_builder import build_armature_from_template, collect_landmark_positions
from ..core.landmarks import Landmark, mirror_landmark, missing_landmarks
from ..core.templates import load_template


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


def unregister_properties():
    if hasattr(bpy.types.Scene, "mgr_landmark_name"):
        del bpy.types.Scene.mgr_landmark_name
    if hasattr(bpy.types.Scene, "mgr_current_template"):
        del bpy.types.Scene.mgr_current_template
    if hasattr(bpy.types.Scene, "mgr_landmark_validation_message"):
        del bpy.types.Scene.mgr_landmark_validation_message


classes = [
    MGR_OT_analyze_asset,
    MGR_OT_create_landmark,
    MGR_OT_clear_landmarks,
    MGR_OT_validate_landmarks,
    MGR_OT_mirror_landmarks,
    MGR_OT_generate_armature,
]
