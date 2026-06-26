import importlib.util
import math
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools/blender_asset_workflow.py"
spec = importlib.util.spec_from_file_location("blender_asset_workflow", MODULE_PATH)
blender_asset_workflow = importlib.util.module_from_spec(spec)
spec.loader.exec_module(blender_asset_workflow)


def test_humanoid_landmarks_from_bbox_contains_required_template_points():
    bbox = {
        "min_x": -1.0,
        "max_x": 1.0,
        "min_y": -0.25,
        "max_y": 0.25,
        "min_z": 0.0,
        "max_z": 5.0,
    }

    landmarks = blender_asset_workflow.humanoid_landmarks_from_bbox(bbox)

    assert set(landmarks) == {
        "hips",
        "spine",
        "chest",
        "neck",
        "head",
        "hip.L",
        "hip.R",
        "shoulder.L",
        "upper_arm.L",
        "lower_arm.L",
        "hand.L",
        "shoulder.R",
        "upper_arm.R",
        "lower_arm.R",
        "hand.R",
        "upper_leg.L",
        "lower_leg.L",
        "foot.L",
        "toe.L",
        "upper_leg.R",
        "lower_leg.R",
        "foot.R",
        "toe.R",
    }
    assert landmarks["shoulder.L"][0] > 0
    assert landmarks["shoulder.R"][0] < 0
    assert landmarks["hip.L"][0] > landmarks["hips"][0]
    assert landmarks["hip.R"][0] < landmarks["hips"][0]
    assert landmarks["foot.L"][1] < landmarks["hips"][1]
    assert landmarks["toe.L"][1] < landmarks["foot.L"][1]
    assert landmarks["head"][2] > landmarks["chest"][2] > landmarks["hips"][2]


def test_humanoid_landmarks_place_side_hips_near_center_pelvis_height():
    bbox = {
        "min_x": -1.0,
        "max_x": 1.0,
        "min_y": -0.25,
        "max_y": 0.25,
        "min_z": 0.0,
        "max_z": 5.0,
    }

    landmarks = blender_asset_workflow.humanoid_landmarks_from_bbox(bbox)

    assert landmarks["hip.L"][2] == landmarks["hips"][2]
    assert landmarks["hip.R"][2] == landmarks["hips"][2]
    assert landmarks["hip.L"][0] < landmarks["upper_leg.L"][0]
    assert landmarks["hip.R"][0] > landmarks["upper_leg.R"][0]


def test_humanoid_landmarks_keep_arm_chain_near_shoulder_band():
    bbox = {
        "min_x": -1.0,
        "max_x": 1.0,
        "min_y": -0.25,
        "max_y": 0.25,
        "min_z": 0.0,
        "max_z": 5.0,
    }

    landmarks = blender_asset_workflow.humanoid_landmarks_from_bbox(bbox)

    assert landmarks["upper_arm.L"][2] >= landmarks["chest"][2]
    assert landmarks["lower_arm.L"][2] >= landmarks["chest"][2]
    assert landmarks["hand.L"][2] >= landmarks["chest"][2]
    assert landmarks["upper_arm.R"][2] >= landmarks["chest"][2]
    assert landmarks["lower_arm.R"][2] >= landmarks["chest"][2]
    assert landmarks["hand.R"][2] >= landmarks["chest"][2]


def test_humanoid_landmarks_use_depth_as_lateral_axis_for_wide_arm_span():
    bbox = {
        "min_x": -0.5,
        "max_x": 0.5,
        "min_y": -4.0,
        "max_y": 4.0,
        "min_z": 0.0,
        "max_z": 5.0,
    }

    landmarks = blender_asset_workflow.humanoid_landmarks_from_bbox(bbox)

    assert landmarks["shoulder.L"][0] == landmarks["shoulder.R"][0]
    assert landmarks["shoulder.L"][1] > landmarks["hips"][1]
    assert landmarks["shoulder.R"][1] < landmarks["hips"][1]
    assert landmarks["hand.L"][1] > landmarks["shoulder.L"][1]
    assert landmarks["hand.R"][1] < landmarks["shoulder.R"][1]
    assert landmarks["hip.L"][0] > landmarks["hips"][0]
    assert landmarks["hip.R"][0] < landmarks["hips"][0]


def test_humanoid_landmarks_do_not_use_arm_span_depth_for_foot_forward_offset():
    bbox = {
        "min_x": -0.44,
        "max_x": 0.61,
        "min_y": -5.52,
        "max_y": 0.02,
        "min_z": -2.95,
        "max_z": 2.95,
    }

    landmarks = blender_asset_workflow.humanoid_landmarks_from_bbox(bbox)

    hips_y = landmarks["hips"][1]
    width = bbox["max_x"] - bbox["min_x"]
    assert abs(landmarks["foot.L"][1] - hips_y) <= width * 0.15
    assert abs(landmarks["toe.L"][1] - hips_y) <= width * 0.40
    assert abs(landmarks["foot.R"][1] - hips_y) <= width * 0.15
    assert abs(landmarks["toe.R"][1] - hips_y) <= width * 0.40


def test_pose_preview_uses_visible_humanoid_stress_pose():
    assert blender_asset_workflow.pose_preview_operator_name() == "pose_humanoid_stress"


def test_side_pose_preview_uses_side_review_pose():
    assert blender_asset_workflow.side_pose_preview_operator_name() == "pose_humanoid_side_review"


def test_pose_preview_uses_quadruped_gait_pose_for_quadruped_template():
    assert blender_asset_workflow.pose_preview_operator_name("quadruped") == "pose_quadruped_gait"


def test_side_pose_preview_uses_quadruped_side_review_pose_for_quadruped_template():
    assert blender_asset_workflow.side_pose_preview_operator_name("quadruped") == "pose_quadruped_side_review"


def test_pose_preview_uses_tail_creature_reach_pose_for_tail_creature_template():
    assert blender_asset_workflow.pose_preview_operator_name("tail_creature") == "pose_tail_creature_reach"


def test_side_pose_preview_uses_tail_creature_side_review_pose_for_tail_creature_template():
    assert blender_asset_workflow.side_pose_preview_operator_name("tail_creature") == "pose_tail_creature_side_review"


def test_pose_preview_uses_prop_hinge_open_pose_for_prop_hinge_template():
    assert blender_asset_workflow.pose_preview_operator_name("prop_hinge") == "pose_prop_hinge_open"


def test_side_pose_preview_uses_prop_hinge_side_review_pose_for_prop_hinge_template():
    assert blender_asset_workflow.side_pose_preview_operator_name("prop_hinge") == "pose_prop_hinge_side_review"


def test_quadruped_landmarks_from_bbox_contains_required_template_points():
    bbox = {
        "min_x": -1.0,
        "max_x": 1.0,
        "min_y": -3.0,
        "max_y": 3.0,
        "min_z": 0.0,
        "max_z": 2.0,
    }

    landmarks = blender_asset_workflow.quadruped_landmarks_from_bbox(bbox)

    assert set(landmarks) == {
        "pelvis",
        "spine",
        "chest",
        "neck",
        "head",
        "muzzle",
        "front_leg.L",
        "front_knee.L",
        "front_ankle.L",
        "front_paw.L",
        "front_leg.R",
        "front_knee.R",
        "front_ankle.R",
        "front_paw.R",
        "rear_leg.L",
        "rear_knee.L",
        "rear_ankle.L",
        "rear_paw.L",
        "rear_leg.R",
        "rear_knee.R",
        "rear_ankle.R",
        "rear_paw.R",
        "tail_base",
        "tail_mid",
        "tail_tip",
    }
    assert landmarks["muzzle"][1] < landmarks["head"][1] < landmarks["neck"][1]
    assert landmarks["tail_tip"][1] > landmarks["tail_mid"][1] > landmarks["tail_base"][1]
    assert landmarks["front_leg.L"][0] > landmarks["front_leg.R"][0]
    assert landmarks["rear_leg.L"][0] > landmarks["rear_leg.R"][0]
    assert landmarks["front_paw.L"][2] < landmarks["front_knee.L"][2] < landmarks["front_leg.L"][2]


def test_tail_creature_landmarks_from_bbox_extends_neck_and_tail_for_sauropod_shape():
    bbox = {
        "min_x": -0.8,
        "max_x": 0.8,
        "min_y": -5.0,
        "max_y": 6.0,
        "min_z": 0.0,
        "max_z": 3.0,
    }

    landmarks = blender_asset_workflow.tail_creature_landmarks_from_bbox(bbox)

    assert set(landmarks) == {
        "pelvis",
        "spine",
        "chest",
        "neck_base",
        "neck_mid",
        "head",
        "muzzle",
        "front_leg.L",
        "front_knee.L",
        "front_ankle.L",
        "front_paw.L",
        "front_leg.R",
        "front_knee.R",
        "front_ankle.R",
        "front_paw.R",
        "rear_leg.L",
        "rear_knee.L",
        "rear_ankle.L",
        "rear_paw.L",
        "rear_leg.R",
        "rear_knee.R",
        "rear_ankle.R",
        "rear_paw.R",
        "tail_base",
        "tail_mid",
        "tail_tip",
    }
    assert landmarks["muzzle"][1] < landmarks["head"][1] < landmarks["neck_mid"][1]
    assert landmarks["neck_mid"][2] > landmarks["neck_base"][2]
    assert landmarks["tail_tip"][1] > landmarks["tail_mid"][1] > landmarks["tail_base"][1]
    assert landmarks["tail_tip"][2] < landmarks["tail_base"][2]


def test_prop_hinge_landmarks_from_bbox_places_hinge_on_one_side_and_moving_tip_opposite():
    bbox = {
        "min_x": -2.0,
        "max_x": 2.0,
        "min_y": -0.5,
        "max_y": 0.5,
        "min_z": 0.0,
        "max_z": 3.0,
    }

    landmarks = blender_asset_workflow.prop_hinge_landmarks_from_bbox(bbox)

    assert set(landmarks) == {"base", "hinge", "moving_part", "moving_tip"}
    assert landmarks["hinge"][0] < landmarks["base"][0]
    assert landmarks["moving_part"][0] > landmarks["hinge"][0]
    assert landmarks["moving_tip"][0] > landmarks["moving_part"][0]
    assert landmarks["hinge"][2] == landmarks["moving_part"][2]


def test_prop_hinge_landmarks_accept_artist_pivot_and_origin_controls():
    bbox = {
        "min_x": -2.0,
        "max_x": 2.0,
        "min_y": -0.5,
        "max_y": 0.5,
        "min_z": 0.0,
        "max_z": 3.0,
    }

    landmarks = blender_asset_workflow.prop_hinge_landmarks_from_bbox(
        bbox,
        hinge_pivot_x=0.05,
        base_origin_x=0.12,
    )

    assert landmarks["hinge"][0] == -1.8
    assert landmarks["base"][0] == -1.52
    assert landmarks["hinge"][0] < landmarks["base"][0] < landmarks["moving_part"][0]


def test_prop_hinge_landmarks_can_follow_y_axis_for_chest_like_props():
    bbox = {
        "min_x": 0.0,
        "max_x": 10.0,
        "min_y": -2.0,
        "max_y": 8.0,
        "min_z": 2.0,
        "max_z": 6.0,
    }

    landmarks = blender_asset_workflow.prop_hinge_landmarks_from_bbox(
        bbox,
        hinge_pivot_x=0.10,
        base_origin_x=0.22,
        layout_axis="y",
    )

    assert landmarks["hinge"] == (5.0, -1.0, 4.0)
    assert landmarks["base"] == (5.0, 0.2, 2.64)
    assert landmarks["moving_part"] == (5.0, 2.5, 4.0)
    assert landmarks["moving_tip"] == (5.0, 7.2, 4.0)


def test_landmarks_from_bbox_passes_prop_hinge_pivot_controls():
    bbox = {
        "min_x": 0.0,
        "max_x": 10.0,
        "min_y": -0.5,
        "max_y": 0.5,
        "min_z": 0.0,
        "max_z": 3.0,
    }

    landmarks = blender_asset_workflow.landmarks_from_bbox(
        "prop_hinge",
        bbox,
        prop_hinge_pivot_x=0.10,
        prop_hinge_base_x=0.22,
    )

    assert landmarks["hinge"][0] == 1.0
    assert landmarks["base"][0] == 2.2


def test_landmarks_from_bbox_passes_prop_hinge_axis_control():
    bbox = {
        "min_x": 0.0,
        "max_x": 10.0,
        "min_y": -2.0,
        "max_y": 8.0,
        "min_z": 2.0,
        "max_z": 6.0,
    }

    landmarks = blender_asset_workflow.landmarks_from_bbox(
        "prop_hinge",
        bbox,
        prop_hinge_pivot_x=0.10,
        prop_hinge_base_x=0.22,
        prop_hinge_axis="y",
    )

    assert landmarks["hinge"] == (5.0, -1.0, 4.0)
    assert landmarks["base"] == (5.0, 0.2, 2.64)


def test_parse_args_accepts_quadruped_template():
    args = blender_asset_workflow.parse_args(
        [
            "--asset",
            "dog.fbx",
            "--evidence-dir",
            "evidence/Q-001",
            "--summary",
            "evidence/Q-001/workflow-summary.json",
            "--template",
            "quadruped",
        ]
    )

    assert args.template == "quadruped"


def test_parse_args_accepts_tail_creature_template():
    args = blender_asset_workflow.parse_args(
        [
            "--asset",
            "apatosaurus.fbx",
            "--evidence-dir",
            "evidence/C-001",
            "--summary",
            "evidence/C-001/workflow-summary.json",
            "--template",
            "tail_creature",
        ]
    )

    assert args.template == "tail_creature"


def test_parse_args_accepts_prop_hinge_template():
    args = blender_asset_workflow.parse_args(
        [
            "--asset",
            "turret.fbx",
            "--evidence-dir",
            "evidence/P-001",
            "--summary",
            "evidence/P-001/workflow-summary.json",
            "--template",
            "prop_hinge",
        ]
    )

    assert args.template == "prop_hinge"


def test_parse_args_accepts_prop_hinge_pivot_and_origin_controls():
    args = blender_asset_workflow.parse_args(
        [
            "--asset",
            "door.fbx",
            "--evidence-dir",
            "evidence/P-001",
            "--summary",
            "evidence/P-001/workflow-summary.json",
            "--template",
            "prop_hinge",
            "--prop-hinge-pivot-x",
            "0.08",
            "--prop-hinge-base-x",
            "0.18",
        ]
    )

    assert args.prop_hinge_pivot_x == 0.08
    assert args.prop_hinge_base_x == 0.18


def test_parse_args_accepts_prop_hinge_axis_control():
    args = blender_asset_workflow.parse_args(
        [
            "--asset",
            "chest.fbx",
            "--evidence-dir",
            "evidence/P-002",
            "--summary",
            "evidence/P-002/workflow-summary.json",
            "--template",
            "prop_hinge",
            "--prop-hinge-axis",
            "y",
        ]
    )

    assert args.prop_hinge_axis == "y"


def test_parse_args_rejects_out_of_range_prop_hinge_controls():
    try:
        blender_asset_workflow.parse_args(
            [
                "--asset",
                "door.fbx",
                "--evidence-dir",
                "evidence/P-001",
                "--summary",
                "evidence/P-001/workflow-summary.json",
                "--template",
                "prop_hinge",
                "--prop-hinge-pivot-x",
                "1.4",
            ]
        )
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected argparse to reject out-of-range pivot")


def test_workflow_controls_summary_records_prop_hinge_pivot_values():
    summary = blender_asset_workflow.workflow_controls_summary(
        "prop_hinge",
        prop_hinge_pivot_x=0.08,
        prop_hinge_base_x=0.18,
        prop_hinge_axis="y",
    )

    assert summary == {
        "propHinge": {
            "pivotX": 0.08,
            "baseX": 0.18,
            "axis": "y",
        }
    }


def test_orientation_plan_rotates_y_up_mesh_to_z_up():
    plan = blender_asset_workflow.orientation_normalization_plan_from_dimensions(
        (2.3, 5.3, 2.2)
    )

    assert plan == {
        "sourceUpAxis": "y",
        "rotationAxis": "X",
        "rotationRadians": math.pi / 2,
    }


def test_orientation_plan_leaves_z_up_mesh_unchanged():
    assert (
        blender_asset_workflow.orientation_normalization_plan_from_dimensions(
            (2.1, 1.2, 5.2)
        )
        is None
    )


def test_mesh_transform_plan_applies_non_unit_scale_for_z_up_mesh():
    plan = blender_asset_workflow.mesh_transform_normalization_plan(
        dimensions=(2.1, 1.2, 5.2),
        scale=(0.01, 0.01, 0.01),
    )

    assert plan == {
        "sourceUpAxis": None,
        "rotationAxis": None,
        "rotationRadians": 0.0,
        "applyScale": True,
    }


def test_normalize_mesh_orientation_uses_scene_level_plan_for_multimesh_assets(monkeypatch):
    class FakeEuler:
        def __init__(self):
            self.rotations = []

        def rotate_axis(self, axis, radians):
            self.rotations.append((axis, radians))

    class FakeObject:
        def __init__(self, name, dimensions):
            self.name = name
            self.type = "MESH"
            self.dimensions = dimensions
            self.scale = (1.0, 1.0, 1.0)
            self.rotation_euler = FakeEuler()
            self.selected = False

        def select_set(self, value):
            self.selected = value

    torso = FakeObject("torso", (1.0, 4.0, 0.4))
    arm = FakeObject("arm", (2.4, 0.6, 0.4))

    class FakeObjectOps:
        applied = []

        @staticmethod
        def mode_set(*, mode):
            return None

        @staticmethod
        def select_all(*, action):
            for obj in FakeBpy.context.scene.objects:
                obj.select_set(False)

        @staticmethod
        def transform_apply(*, location, rotation, scale):
            FakeObjectOps.applied.append(
                {
                    "active": FakeBpy.context.view_layer.objects.active.name,
                    "rotation": rotation,
                    "scale": scale,
                }
            )

    FakeObjectOps.mode_set.poll = lambda: True

    class FakeViewObjects:
        active = None

    class FakeViewLayer:
        objects = FakeViewObjects()

    class FakeScene:
        objects = [torso, arm]

    class FakeContext:
        scene = FakeScene()
        view_layer = FakeViewLayer()

    class FakeOps:
        object = FakeObjectOps()

    class FakeBpy:
        context = FakeContext()
        ops = FakeOps()

    monkeypatch.setattr(
        blender_asset_workflow,
        "mesh_bbox",
        lambda _bpy: {
            "min_x": -1.2,
            "max_x": 1.2,
            "min_y": -2.0,
            "max_y": 2.0,
            "min_z": -0.2,
            "max_z": 0.2,
        },
    )

    result = blender_asset_workflow.normalize_mesh_orientation(FakeBpy)

    assert [item["objectName"] for item in result] == ["torso", "arm"]
    assert torso.rotation_euler.rotations == [("X", math.pi / 2)]
    assert arm.rotation_euler.rotations == [("X", math.pi / 2)]
    assert FakeObjectOps.applied == [
        {"active": "torso", "rotation": True, "scale": False},
        {"active": "arm", "rotation": True, "scale": False},
    ]


def test_default_camera_axis_is_front_view_after_orientation_normalization():
    args = blender_asset_workflow.parse_args(
        [
            "--asset",
            "asset.fbx",
            "--evidence-dir",
            "evidence",
            "--summary",
            "summary.json",
        ]
    )

    assert args.camera_axis == "x"


def test_camera_plan_uses_orthographic_scale_from_asset_height():
    bbox = {
        "min_x": -1.0,
        "max_x": 1.0,
        "min_y": -0.5,
        "max_y": 0.5,
        "min_z": 0.0,
        "max_z": 5.0,
    }

    plan = blender_asset_workflow.camera_plan_from_bbox(bbox)

    assert plan["orthographicScale"] >= 5.5
    assert plan["cameraLocation"][1] < bbox["min_y"]
    assert plan["target"][2] == 2.5


def test_camera_plan_can_use_x_axis_for_side_oriented_assets():
    bbox = {
        "min_x": -1.0,
        "max_x": 1.0,
        "min_y": -0.5,
        "max_y": 0.5,
        "min_z": 0.0,
        "max_z": 5.0,
    }

    plan = blender_asset_workflow.camera_plan_from_bbox(bbox, axis="x")

    assert plan["cameraLocation"][0] < bbox["min_x"]
    assert plan["cameraLocation"][1] == 0.0


def test_camera_plan_extends_clip_end_past_large_deformed_bbox():
    bbox = {
        "min_x": -53.5,
        "max_x": 45.0,
        "min_y": -241.0,
        "max_y": 241.0,
        "min_z": -1.7,
        "max_z": 528.6,
    }

    plan = blender_asset_workflow.camera_plan_from_bbox(bbox, axis="x")
    camera_location = plan["cameraLocation"]
    target = plan["target"]
    distance_to_target = abs(target[0] - camera_location[0])

    assert plan["clipEnd"] > distance_to_target + plan["orthographicScale"]


def test_unity_export_scale_normalization_plan_scales_severe_humanoid_to_warning_limit():
    bbox = {
        "min_x": -53.4423,
        "max_x": 44.9455,
        "min_y": -240.9125,
        "max_y": 240.9125,
        "min_z": -1.6634,
        "max_z": 528.5285,
    }

    plan = blender_asset_workflow.unity_export_scale_normalization_plan(
        "humanoid",
        bbox,
    )

    assert plan["applied"] is True
    assert plan["category"] == "humanoid"
    assert plan["sourceMaxDimension"] == 530.1919
    assert plan["targetMaxDimension"] == 9.5
    assert plan["scaleFactor"] == round(9.5 / 530.1919, 6)


def test_unity_export_scale_normalization_plan_leaves_normal_humanoid_size_unchanged():
    bbox = {
        "min_x": -0.5,
        "max_x": 0.5,
        "min_y": -0.25,
        "max_y": 0.25,
        "min_z": 0.0,
        "max_z": 5.0,
    }

    plan = blender_asset_workflow.unity_export_scale_normalization_plan(
        "humanoid",
        bbox,
    )

    assert plan == {
        "applied": False,
        "category": "humanoid",
        "sourceMaxDimension": 5.0,
        "targetMaxDimension": 9.5,
        "scaleFactor": 1.0,
        "reason": "withinSevereLimit",
    }


def test_preview_material_name_is_stable_for_evidence_renders():
    assert blender_asset_workflow.preview_material_name() == "MGR_Evidence_Preview_Material"


def test_preview_artifact_paths_include_front_and_side_views(tmp_path):
    paths = blender_asset_workflow.preview_artifact_paths(tmp_path)

    assert paths == {
        "neutral_front": tmp_path / "preview-neutral.png",
        "pose_front": tmp_path / "preview-pose.png",
        "neutral_side": tmp_path / "preview-neutral-side.png",
        "pose_side": tmp_path / "preview-pose-side.png",
    }


def test_preview_artifact_summary_uses_stable_manifest_keys(tmp_path):
    paths = blender_asset_workflow.preview_artifact_paths(tmp_path)

    summary = blender_asset_workflow.preview_artifact_summary(paths)

    assert summary == {
        "previewNeutral": str(tmp_path / "preview-neutral.png"),
        "previewPose": str(tmp_path / "preview-pose.png"),
        "previewNeutralSide": str(tmp_path / "preview-neutral-side.png"),
        "previewPoseSide": str(tmp_path / "preview-pose-side.png"),
    }


def test_pose_deformation_summary_flags_extreme_bbox_expansion():
    neutral_bbox = {
        "min_x": -1.0,
        "max_x": 1.0,
        "min_y": -0.5,
        "max_y": 0.5,
        "min_z": 0.0,
        "max_z": 5.0,
    }
    pose_bbox = {
        "min_x": -12.0,
        "max_x": 12.0,
        "min_y": -0.5,
        "max_y": 0.5,
        "min_z": 0.0,
        "max_z": 5.0,
    }

    summary = blender_asset_workflow.pose_deformation_summary(
        neutral_bbox,
        pose_bbox,
    )

    assert summary["status"] == "fail"
    assert summary["maxAxisExpansionRatio"] == 12.0
    assert summary["expandedAxes"] == ["x"]


def test_pose_deformation_summary_allows_prop_hinge_open_axis_expansion():
    neutral_bbox = {
        "min_x": -0.35,
        "max_x": 0.35,
        "min_y": -0.03,
        "max_y": 0.03,
        "min_z": 0.2,
        "max_z": 1.4,
    }
    pose_bbox = {
        "min_x": -0.35,
        "max_x": 0.2,
        "min_y": -0.03,
        "max_y": 0.42,
        "min_z": 0.2,
        "max_z": 1.4,
    }

    summary = blender_asset_workflow.pose_deformation_summary(
        neutral_bbox,
        pose_bbox,
        template="prop_hinge",
    )

    assert summary["status"] == "pass"
    assert summary["expandedAxes"] == []
    assert summary["allowedExpandedAxes"] == ["y"]


def test_pose_deformation_summary_passes_moderate_stress_pose_expansion():
    neutral_bbox = {
        "min_x": -1.0,
        "max_x": 1.0,
        "min_y": -0.5,
        "max_y": 0.5,
        "min_z": 0.0,
        "max_z": 5.0,
    }
    pose_bbox = {
        "min_x": -2.0,
        "max_x": 2.0,
        "min_y": -0.5,
        "max_y": 0.5,
        "min_z": 0.0,
        "max_z": 5.2,
    }

    summary = blender_asset_workflow.pose_deformation_summary(
        neutral_bbox,
        pose_bbox,
    )

    assert summary["status"] == "pass"
    assert summary["maxAxisExpansionRatio"] == 2.0
    assert summary["expandedAxes"] == []


def test_cleanup_summary_from_scene_parses_removed_empty_groups():
    class FakeScene:
        mgr_weight_cleanup_message = (
            "unweighted=0 over_limit=0 removed_empty=13 pruned=0 normalized=2"
        )
        mgr_removed_empty_group_names = "UpperArm.L,LowerArm.L,Hand.L"

    assert blender_asset_workflow.cleanup_summary_from_scene(FakeScene()) == {
        "unweightedVertices": 0,
        "overLimitVertices": 0,
        "removedEmptyGroups": 13,
        "removedEmptyGroupNames": ["UpperArm.L", "LowerArm.L", "Hand.L"],
        "prunedWeights": 0,
        "normalizedVertices": 2,
    }


def test_weight_region_summary_groups_influences_by_semantic_body_region():
    class FakeGroup:
        def __init__(self, name, index):
            self.name = name
            self.index = index

    class FakeWeight:
        def __init__(self, group, weight):
            self.group = group
            self.weight = weight

    class FakeVertex:
        def __init__(self, groups):
            self.groups = groups

    class FakeMeshData:
        vertices = [
            FakeVertex([FakeWeight(0, 0.8), FakeWeight(1, 0.2)]),
            FakeVertex([FakeWeight(1, 0.7), FakeWeight(0, 0.3)]),
            FakeVertex([FakeWeight(2, 0.6), FakeWeight(3, 0.4)]),
            FakeVertex([FakeWeight(4, 0.9), FakeWeight(5, 0.1)]),
        ]

    class FakeMesh:
        name = "RiggedMesh"
        vertex_groups = [
            FakeGroup("Chest", 0),
            FakeGroup("UpperArm.L", 1),
            FakeGroup("LowerArm.L", 2),
            FakeGroup("Hand.L", 3),
            FakeGroup("UpperLeg.L", 4),
            FakeGroup("Foot.L", 5),
        ]
        data = FakeMeshData()

    summary = blender_asset_workflow.weight_region_summary([FakeMesh()])

    assert summary["meshCount"] == 1
    assert summary["vertexCount"] == 4
    assert summary["regions"]["core"] == {
        "influencedVertices": 2,
        "dominantVertices": 1,
        "averageWeight": 0.55,
    }
    assert summary["regions"]["upperArm"] == {
        "influencedVertices": 2,
        "dominantVertices": 1,
        "averageWeight": 0.45,
    }
    assert summary["regions"]["hand"] == {
        "influencedVertices": 1,
        "dominantVertices": 0,
        "averageWeight": 0.4,
    }
    assert summary["regions"]["upperLeg"]["dominantVertices"] == 1
    assert summary["topBones"][:3] == [
        {"bone": "Chest", "totalWeight": 1.1},
        {"bone": "UpperLeg.L", "totalWeight": 0.9},
        {"bone": "UpperArm.L", "totalWeight": 0.9},
    ]


def test_weight_region_summary_keeps_neck_and_head_separate_from_torso_core():
    class FakeGroup:
        def __init__(self, name, index):
            self.name = name
            self.index = index

    class FakeWeight:
        def __init__(self, group, weight):
            self.group = group
            self.weight = weight

    class FakeVertex:
        def __init__(self, groups):
            self.groups = groups

    class FakeMeshData:
        vertices = [
            FakeVertex([FakeWeight(0, 1.0)]),
            FakeVertex([FakeWeight(1, 1.0)]),
        ]

    class FakeMesh:
        name = "RiggedMesh"
        vertex_groups = [
            FakeGroup("Chest", 0),
            FakeGroup("Neck", 1),
        ]
        data = FakeMeshData()

    summary = blender_asset_workflow.weight_region_summary([FakeMesh()])

    assert summary["regions"]["core"]["dominantVertices"] == 1
    assert summary["regions"]["neckHead"]["dominantVertices"] == 1


def test_weight_region_summary_groups_prop_hinge_bones_by_prop_regions():
    class FakeGroup:
        def __init__(self, name, index):
            self.name = name
            self.index = index

    class FakeWeight:
        def __init__(self, group, weight):
            self.group = group
            self.weight = weight

    class FakeVertex:
        def __init__(self, groups):
            self.groups = groups

    class FakeMeshData:
        vertices = [
            FakeVertex([FakeWeight(0, 1.0)]),
            FakeVertex([FakeWeight(1, 1.0)]),
            FakeVertex([FakeWeight(2, 1.0)]),
            FakeVertex([FakeWeight(2, 0.8), FakeWeight(1, 0.2)]),
        ]

    class FakeMesh:
        name = "PropRiggedMesh"
        vertex_groups = [
            FakeGroup("PropBase", 0),
            FakeGroup("Hinge", 1),
            FakeGroup("MovingPart", 2),
        ]
        data = FakeMeshData()

    summary = blender_asset_workflow.weight_region_summary([FakeMesh()])

    assert "other" not in summary["regions"]
    assert summary["regions"]["propBase"]["dominantVertices"] == 1
    assert summary["regions"]["propHinge"]["dominantVertices"] == 1
    assert summary["regions"]["propMovingPart"]["dominantVertices"] == 2


def test_prop_diagnostics_summary_passes_balanced_prop_hinge_coverage():
    weight_diagnostics = {
        "vertexCount": 360,
        "regions": {
            "propBase": {"dominantVertices": 138},
            "propHinge": {"dominantVertices": 12},
            "propMovingPart": {"dominantVertices": 210},
        },
    }

    summary = blender_asset_workflow.prop_diagnostics_summary(
        weight_diagnostics,
        template="prop_hinge",
    )

    assert summary == {
        "status": "pass",
        "coverageRatios": {
            "propBase": 0.3833,
            "propHinge": 0.0333,
            "propMovingPart": 0.5833,
        },
        "warnings": [],
    }


def test_prop_diagnostics_summary_warns_for_weak_hinge_coverage():
    weight_diagnostics = {
        "vertexCount": 360,
        "regions": {
            "propBase": {"dominantVertices": 140},
            "propHinge": {"dominantVertices": 1},
            "propMovingPart": {"dominantVertices": 219},
        },
    }

    summary = blender_asset_workflow.prop_diagnostics_summary(
        weight_diagnostics,
        template="prop_hinge",
    )

    assert summary["status"] == "warn"
    assert summary["warnings"] == ["weakPropHingeCoverage"]


def test_prop_diagnostics_summary_fails_when_moving_part_has_no_coverage():
    weight_diagnostics = {
        "vertexCount": 360,
        "regions": {
            "propBase": {"dominantVertices": 350},
            "propHinge": {"dominantVertices": 10},
        },
    }

    summary = blender_asset_workflow.prop_diagnostics_summary(
        weight_diagnostics,
        template="prop_hinge",
    )

    assert summary["status"] == "fail"
    assert summary["warnings"] == ["missingPropMovingPartCoverage"]


def test_humanoid_diagnostics_summary_warns_when_foot_coverage_is_too_low():
    weight_diagnostics = {
        "vertexCount": 791,
        "regions": {
            "core": {"dominantVertices": 615},
            "upperArm": {"dominantVertices": 10},
            "lowerArm": {"dominantVertices": 54},
            "hand": {"dominantVertices": 10},
            "upperLeg": {"dominantVertices": 24},
            "lowerLeg": {"dominantVertices": 63},
            "foot": {"dominantVertices": 15},
        },
    }

    summary = blender_asset_workflow.humanoid_diagnostics_summary(
        weight_diagnostics,
        template="humanoid",
    )

    assert summary["status"] == "warn"
    assert summary["coverageRatios"]["foot"] == 0.019
    assert summary["warnings"] == ["weakHumanoidFootCoverage"]


def test_weight_region_summary_reports_dominant_regions_by_height_band():
    class FakeGroup:
        def __init__(self, name, index):
            self.name = name
            self.index = index

    class FakeWeight:
        def __init__(self, group, weight):
            self.group = group
            self.weight = weight

    class FakeVertex:
        def __init__(self, z, groups):
            self.co = (0.0, 0.0, z)
            self.groups = groups

    class FakeMatrix:
        def __matmul__(self, value):
            return value

    class FakeMeshData:
        vertices = [
            FakeVertex(0.0, [FakeWeight(0, 1.0)]),
            FakeVertex(1.0, [FakeWeight(1, 1.0)]),
            FakeVertex(2.0, [FakeWeight(1, 1.0)]),
        ]

    class FakeMesh:
        name = "RiggedMesh"
        matrix_world = FakeMatrix()
        vertex_groups = [
            FakeGroup("Hips", 0),
            FakeGroup("Neck", 1),
        ]
        data = FakeMeshData()

    summary = blender_asset_workflow.weight_region_summary([FakeMesh()])

    assert summary["heightBands"]["lower"]["dominantRegions"] == {"core": 1}
    assert summary["heightBands"]["lower"]["minZ"] == 0.0
    assert summary["heightBands"]["lower"]["maxZ"] == 0.0
    assert summary["heightBands"]["torso"]["dominantRegions"] == {"neckHead": 1}
    assert summary["heightBands"]["torso"]["minZ"] == 1.0
    assert summary["heightBands"]["torso"]["maxZ"] == 1.0
    assert summary["heightBands"]["upper"]["dominantRegions"] == {"neckHead": 1}


def test_bone_weight_diagnostics_reports_per_bone_bounds_and_weight_samples():
    class FakePoint:
        def __init__(self, x, y, z):
            self.x = x
            self.y = y
            self.z = z

    class FakeMatrix:
        def __matmul__(self, value):
            return FakePoint(value[0] + 10.0, value[1] - 1.0, value[2] + 0.5)

    class FakeGroup:
        def __init__(self, name, index):
            self.name = name
            self.index = index

    class FakeWeight:
        def __init__(self, group, weight):
            self.group = group
            self.weight = weight

    class FakeVertex:
        def __init__(self, index, co, groups):
            self.index = index
            self.co = co
            self.groups = groups

    class FakeMeshData:
        vertices = [
            FakeVertex(0, (0.0, 0.0, 0.0), [FakeWeight(0, 0.8), FakeWeight(1, 0.2)]),
            FakeVertex(1, (1.0, 2.0, 3.0), [FakeWeight(1, 0.7), FakeWeight(0, 0.3)]),
            FakeVertex(2, (-1.0, 4.0, 2.0), [FakeWeight(2, 0.6)]),
            FakeVertex(3, (3.0, 5.0, 1.0), [FakeWeight(1, 0.9)]),
        ]

    class FakeMesh:
        name = "RiggedMesh"
        matrix_world = FakeMatrix()
        vertex_groups = [
            FakeGroup("Foot.L", 0),
            FakeGroup("LowerLeg.L", 1),
            FakeGroup("Chest", 2),
        ]
        data = FakeMeshData()

    summary = blender_asset_workflow.bone_weight_diagnostics([FakeMesh()], sample_limit=2)

    assert summary["meshCount"] == 1
    assert summary["vertexCount"] == 4
    assert summary["bones"]["Foot.L"] == {
        "region": "foot",
        "influencedVertices": 2,
        "dominantVertices": 1,
        "totalWeight": 1.1,
        "averageWeight": 0.55,
        "influencedBounds": {
            "minX": 10.0,
            "maxX": 11.0,
            "minY": -1.0,
            "maxY": 1.0,
            "minZ": 0.5,
            "maxZ": 3.5,
        },
        "dominantBounds": {
            "minX": 10.0,
            "maxX": 10.0,
            "minY": -1.0,
            "maxY": -1.0,
            "minZ": 0.5,
            "maxZ": 0.5,
        },
        "topWeightedVertices": [
            {"mesh": "RiggedMesh", "index": 0, "weight": 0.8, "world": [10.0, -1.0, 0.5]},
            {"mesh": "RiggedMesh", "index": 1, "weight": 0.3, "world": [11.0, 1.0, 3.5]},
        ],
    }
    assert summary["bones"]["LowerLeg.L"]["dominantVertices"] == 2
    assert summary["bones"]["LowerLeg.L"]["topWeightedVertices"] == [
        {"mesh": "RiggedMesh", "index": 3, "weight": 0.9, "world": [13.0, 4.0, 1.5]},
        {"mesh": "RiggedMesh", "index": 1, "weight": 0.7, "world": [11.0, 1.0, 3.5]},
    ]
    assert summary["topBones"] == [
        {"bone": "LowerLeg.L", "totalWeight": 1.8},
        {"bone": "Foot.L", "totalWeight": 1.1},
        {"bone": "Chest", "totalWeight": 0.6},
    ]


def test_capsule_bind_weight_diagnostics_reports_bone_bounds_in_capsule_space(monkeypatch):
    class FakeGroup:
        def __init__(self, name, index):
            self.name = name
            self.index = index

    class FakeWeight:
        def __init__(self, group, weight):
            self.group = group
            self.weight = weight

    class FakeVertex:
        def __init__(self, index, co, groups):
            self.index = index
            self.co = co
            self.groups = groups

    class FakeMeshData:
        vertices = [
            FakeVertex(0, (0.0, 0.0, 0.0), [FakeWeight(0, 1.0)]),
            FakeVertex(1, (10.0, 0.0, 10.0), [FakeWeight(0, 0.4), FakeWeight(1, 0.6)]),
        ]

    class FakeMesh:
        name = "RiggedMesh"
        vertex_groups = [
            FakeGroup("Foot.L", 0),
            FakeGroup("LowerLeg.L", 1),
        ]
        data = FakeMeshData()

    class FakeWeightBindingCore:
        @staticmethod
        def mesh_bind_vertex_points(mesh, target_bounds=None):
            assert target_bounds == {
                "min": (-1.0, -1.0, -1.0),
                "max": (11.0, 1.0, 21.0),
            }
            return {
                0: (-1.0, -1.0, -1.0),
                1: (11.0, 1.0, 21.0),
            }

    monkeypatch.setattr(blender_asset_workflow, "load_weight_binding_core", lambda: FakeWeightBindingCore)

    summary = blender_asset_workflow.capsule_bind_weight_diagnostics(
        [FakeMesh()],
        [
            {
                "name": "Foot.L",
                "head": (0.0, 0.0, 0.0),
                "tail": (10.0, 0.0, 20.0),
                "radius": 1.0,
            }
        ],
        sample_limit=2,
    )

    assert summary["space"] == "capsuleBind"
    assert summary["targetBounds"] == {
        "minX": -1.0,
        "maxX": 11.0,
        "minY": -1.0,
        "maxY": 1.0,
        "minZ": -1.0,
        "maxZ": 21.0,
    }
    assert summary["bones"]["Foot.L"]["dominantBounds"] == {
        "minX": -1.0,
        "maxX": -1.0,
        "minY": -1.0,
        "maxY": -1.0,
        "minZ": -1.0,
        "maxZ": -1.0,
    }
    assert summary["bones"]["Foot.L"]["topWeightedVertices"] == [
        {"mesh": "RiggedMesh", "index": 0, "weight": 1.0, "bind": [-1.0, -1.0, -1.0]},
        {"mesh": "RiggedMesh", "index": 1, "weight": 0.4, "bind": [11.0, 1.0, 21.0]},
    ]
    assert summary["bones"]["LowerLeg.L"]["dominantBounds"] == {
        "minX": 11.0,
        "maxX": 11.0,
        "minY": 1.0,
        "maxY": 1.0,
        "minZ": 21.0,
        "maxZ": 21.0,
    }


def test_capsule_assignment_diagnostics_summarizes_nearest_fallback_by_bone(monkeypatch):
    class FakeVertex:
        def __init__(self, index, co):
            self.index = index
            self.co = co

    class FakeMeshData:
        vertices = [
            FakeVertex(0, (0.0, 0.0, 0.0)),
            FakeVertex(1, (10.0, 0.0, 10.0)),
            FakeVertex(2, (5.0, 0.0, 5.0)),
        ]

    class FakeMesh:
        name = "RiggedMesh"
        data = FakeMeshData()

    class FakeWeightBindingCore:
        MAX_VERTEX_INFLUENCES = 4

        @staticmethod
        def mesh_bind_vertex_points(mesh, target_bounds=None):
            return {
                0: (0.0, 0.0, 0.0),
                1: (1.0, 0.0, 0.0),
                2: (2.0, 0.0, 0.0),
            }

        @staticmethod
        def capsule_assignment_details(point, bones, max_influences):
            if point[0] == 0.0:
                return {
                    "mode": "capsule",
                    "weights": {"LowerLeg.L": 1.0},
                    "nearestBone": "LowerLeg.L",
                    "nearestBoneRegion": "limb",
                    "nearestDistance": 0.0,
                    "nearestRadius": 0.4,
                    "nearestDistanceRatio": 0.0,
                }
            return {
                "mode": "nearestFallback",
                "weights": {"Foot.L": 1.0},
                "nearestBone": "Foot.L",
                "nearestBoneRegion": "distal",
                "nearestDistance": point[0],
                "nearestRadius": 0.2,
                "nearestDistanceRatio": point[0] / 0.2,
            }

    monkeypatch.setattr(blender_asset_workflow, "load_weight_binding_core", lambda: FakeWeightBindingCore)

    summary = blender_asset_workflow.capsule_assignment_diagnostics(
        [FakeMesh()],
        [
            {
                "name": "Foot.L",
                "head": (0.0, 0.0, 0.0),
                "tail": (1.0, 0.0, 0.0),
                "radius": 0.2,
            }
        ],
        sample_limit=1,
    )

    assert summary["space"] == "capsuleBind"
    assert summary["vertexCount"] == 3
    assert summary["capsuleAssignedVertices"] == 1
    assert summary["nearestFallbackVertices"] == 2
    assert summary["fallbackByBone"]["Foot.L"] == {
        "region": "distal",
        "vertexCount": 2,
        "averageDistanceRatio": 7.5,
        "maxDistanceRatio": 10.0,
        "samples": [
            {
                "mesh": "RiggedMesh",
                "index": 2,
                "bind": [2.0, 0.0, 0.0],
                "distance": 2.0,
                "distanceRatio": 10.0,
            }
        ],
    }


def test_capsule_diagnostics_summary_serializes_world_space_capsules():
    summary = blender_asset_workflow.capsule_diagnostics_summary(
        [
            {
                "name": "Neck",
                "head": (0.123456, 0.0, 2.0),
                "tail": (0.0, 0.0, 2.4),
                "radius": 0.333333,
                "verticalMin": 2.0,
                "verticalMax": 2.4,
            }
        ]
    )

    assert summary == [
        {
            "name": "Neck",
            "head": [0.1235, 0.0, 2.0],
            "tail": [0.0, 0.0, 2.4],
            "radius": 0.3333,
            "verticalMin": 2.0,
            "verticalMax": 2.4,
        }
    ]


def test_bind_space_summary_reports_raw_and_normalized_z_ranges():
    class FakeMatrix:
        def __matmul__(self, value):
            return value

    class FakeVertex:
        def __init__(self, index, co):
            self.index = index
            self.co = co

    class FakeMeshData:
        vertices = [
            FakeVertex(0, (0.0, 0.0, 0.0)),
            FakeVertex(1, (0.0, 0.0, 100.0)),
        ]

    class FakeMesh:
        name = "ScaledMesh"
        matrix_world = FakeMatrix()
        bound_box = [
            (0.0, 0.0, 0.0),
            (0.0, 0.0, 1.0),
        ]
        data = FakeMeshData()

    summary = blender_asset_workflow.bind_space_summary([FakeMesh()])

    assert summary == [
        {
            "mesh": "ScaledMesh",
            "rawMinZ": 0.0,
            "rawMaxZ": 100.0,
            "bindMinZ": 0.0,
            "bindMaxZ": 1.0,
        }
    ]


def test_render_preview_frame_reframes_from_current_mesh_bbox_before_render(monkeypatch, tmp_path):
    current_bbox = {
        "min_x": -10.0,
        "max_x": 20.0,
        "min_y": -30.0,
        "max_y": 40.0,
        "min_z": -1.0,
        "max_z": 100.0,
    }
    camera_calls = []

    class FakeRenderOps:
        def __call__(self):
            return {"FINISHED"}

    class FakeMgrOps:
        render_front_preview = FakeRenderOps()

    class FakeOps:
        mgr = FakeMgrOps()

    class FakeScene:
        mgr_preview_output_path = ""

    class FakeContext:
        scene = FakeScene()

    class FakeBpy:
        context = FakeContext()
        ops = FakeOps()

    def fake_setup_camera(bpy_module, bbox, *, axis):
        camera_calls.append((bpy_module, bbox, axis))

    monkeypatch.setattr(blender_asset_workflow, "mesh_bbox", lambda bpy_module: current_bbox)
    monkeypatch.setattr(blender_asset_workflow, "setup_camera_and_light", fake_setup_camera)

    output_path = tmp_path / "preview.png"

    blender_asset_workflow.render_preview_frame(FakeBpy, output_path, axis="x")

    assert FakeBpy.context.scene.mgr_preview_output_path == str(output_path)
    assert camera_calls == [(FakeBpy, current_bbox, "x")]


def test_select_export_objects_includes_mgr_armature_with_meshes():
    class FakeObject:
        def __init__(self, name, obj_type):
            self.name = name
            self.type = obj_type
            self.selected = False

        def select_set(self, value):
            self.selected = bool(value)

    mesh = FakeObject("CharacterMesh", "MESH")
    armature = FakeObject("MGR_Armature", "ARMATURE")
    landmark = FakeObject("MGR_Landmark_head", "EMPTY")

    class FakeObjectMap(dict):
        def get(self, name, default=None):
            return super().get(name, default)

    class FakeScene:
        objects = [mesh, armature, landmark]

    class FakeViewLayer:
        class Objects:
            active = None

        objects = Objects()

    class FakeContext:
        scene = FakeScene()
        view_layer = FakeViewLayer()

    class FakeObjectOps:
        @staticmethod
        def select_all(action):
            assert action == "DESELECT"
            for obj in FakeScene.objects:
                obj.select_set(False)

    class FakeOps:
        object = FakeObjectOps()

    class FakeData:
        objects = FakeObjectMap({"MGR_Armature": armature})

    class FakeBpy:
        context = FakeContext()
        ops = FakeOps()
        data = FakeData()

    selected = blender_asset_workflow.select_export_objects(FakeBpy)

    assert selected == [mesh, armature]
    assert mesh.selected is True
    assert armature.selected is True
    assert landmark.selected is False
    assert FakeBpy.context.view_layer.objects.active is armature


def test_apply_unity_export_scale_normalization_scales_meshes_and_mgr_armature(monkeypatch):
    class FakeObject:
        def __init__(self, name, obj_type, scale=(1.0, 1.0, 1.0)):
            self.name = name
            self.type = obj_type
            self.scale = list(scale)

    mesh = FakeObject("CharacterMesh", "MESH")
    armature = FakeObject("MGR_Armature", "ARMATURE", scale=(2.0, 2.0, 2.0))
    landmark = FakeObject("MGR_Landmark_head", "EMPTY")

    class FakeViewLayer:
        updated = False

        @classmethod
        def update(cls):
            cls.updated = True

    class FakeScene:
        objects = [mesh, armature, landmark]

    class FakeContext:
        scene = FakeScene()
        view_layer = FakeViewLayer()

    class FakeBpy:
        context = FakeContext()

    bbox = {
        "min_x": 0.0,
        "max_x": 1.0,
        "min_y": -240.0,
        "max_y": 240.0,
        "min_z": 0.0,
        "max_z": 530.0,
    }
    monkeypatch.setattr(blender_asset_workflow, "mesh_bbox", lambda bpy_module: bbox)

    summary = blender_asset_workflow.apply_unity_export_scale_normalization(
        FakeBpy,
        "humanoid",
    )

    assert summary["applied"] is True
    assert summary["scaleFactor"] == round(9.5 / 530.0, 6)
    assert tuple(mesh.scale) == (summary["scaleFactor"],) * 3
    assert tuple(armature.scale) == (round(2.0 * summary["scaleFactor"], 6),) * 3
    assert landmark.scale == [1.0, 1.0, 1.0]
    assert FakeViewLayer.updated is True
