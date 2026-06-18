import importlib.util
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
    assert landmarks["foot.L"][1] < landmarks["hips"][1]
    assert landmarks["toe.L"][1] < landmarks["foot.L"][1]
    assert landmarks["head"][2] > landmarks["chest"][2] > landmarks["hips"][2]


def test_pose_preview_uses_visible_arm_raise_pose():
    assert blender_asset_workflow.pose_preview_operator_name() == "pose_arm_raise"


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


def test_preview_material_name_is_stable_for_evidence_renders():
    assert blender_asset_workflow.preview_material_name() == "MGR_Evidence_Preview_Material"


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
