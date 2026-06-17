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
