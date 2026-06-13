import importlib.util
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).resolve().parents[1] / "addon/mac_game_rigger/core/landmarks.py"
spec = importlib.util.spec_from_file_location("landmarks", MODULE_PATH)
landmarks = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = landmarks
spec.loader.exec_module(landmarks)

Landmark = landmarks.Landmark
mirror_landmark = landmarks.mirror_landmark
missing_landmarks = landmarks.missing_landmarks


def test_mirror_landmark_flips_x_axis_and_swaps_left_suffix():
    landmark = Landmark(name="upper_arm.L", position=(1.25, 2.0, -0.5))

    mirrored = mirror_landmark(landmark)

    assert mirrored == Landmark(name="upper_arm.R", position=(-1.25, 2.0, -0.5))


def test_mirror_landmark_swaps_right_suffix():
    landmark = Landmark(name="front_paw.R", position=(-0.4, 0.2, 1.1))

    mirrored = mirror_landmark(landmark)

    assert mirrored == Landmark(name="front_paw.L", position=(0.4, 0.2, 1.1))


def test_missing_landmarks_returns_required_names_not_present_in_order():
    required = ("hips", "spine", "head", "upper_arm.L", "upper_arm.R")
    placed = [
        Landmark(name="hips", position=(0.0, 0.0, 0.0)),
        Landmark(name="head", position=(0.0, 0.0, 1.8)),
        Landmark(name="upper_arm.R", position=(-0.5, 0.0, 1.3)),
    ]

    assert missing_landmarks(required, placed) == ("spine", "upper_arm.L")
