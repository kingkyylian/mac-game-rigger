import importlib.util
from pathlib import Path
import sys

import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "addon/mac_game_rigger/core/weight_binding.py"
spec = importlib.util.spec_from_file_location("weight_binding", MODULE_PATH)
weight_binding = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = weight_binding
spec.loader.exec_module(weight_binding)


def test_distance_point_to_segment_returns_perpendicular_distance_inside_segment():
    distance = weight_binding.distance_point_to_segment(
        point=(1.0, 1.0, 0.0),
        segment_start=(0.0, 0.0, 0.0),
        segment_end=(2.0, 0.0, 0.0),
    )

    assert distance == pytest.approx(1.0)


def test_distance_point_to_segment_clamps_before_segment_start():
    distance = weight_binding.distance_point_to_segment(
        point=(-1.0, 0.0, 0.0),
        segment_start=(0.0, 0.0, 0.0),
        segment_end=(2.0, 0.0, 0.0),
    )

    assert distance == pytest.approx(1.0)


def test_distance_point_to_segment_handles_zero_length_segment():
    distance = weight_binding.distance_point_to_segment(
        point=(0.0, 3.0, 4.0),
        segment_start=(0.0, 0.0, 0.0),
        segment_end=(0.0, 0.0, 0.0),
    )

    assert distance == pytest.approx(5.0)


def test_capsule_weight_falls_off_linearly_until_radius():
    assert weight_binding.capsule_weight(
        point=(0.0, 0.0, 0.0),
        segment_start=(0.0, 0.0, 0.0),
        segment_end=(2.0, 0.0, 0.0),
        radius=1.0,
    ) == pytest.approx(1.0)
    assert weight_binding.capsule_weight(
        point=(0.0, 0.5, 0.0),
        segment_start=(0.0, 0.0, 0.0),
        segment_end=(2.0, 0.0, 0.0),
        radius=1.0,
    ) == pytest.approx(0.5)
    assert weight_binding.capsule_weight(
        point=(0.0, 2.0, 0.0),
        segment_start=(0.0, 0.0, 0.0),
        segment_end=(2.0, 0.0, 0.0),
        radius=1.0,
    ) == pytest.approx(0.0)


def test_capsule_weight_rejects_non_positive_radius():
    with pytest.raises(ValueError, match="radius must be positive"):
        weight_binding.capsule_weight(
            point=(0.0, 0.0, 0.0),
            segment_start=(0.0, 0.0, 0.0),
            segment_end=(1.0, 0.0, 0.0),
            radius=0.0,
        )


def test_normalize_weights_keeps_positive_weights_and_sums_to_one():
    normalized = weight_binding.normalize_weights(
        {"UpperArm.L": 2.0, "Spine": 1.0, "Head": 0.0}
    )

    assert normalized == {
        "UpperArm.L": pytest.approx(2.0 / 3.0),
        "Spine": pytest.approx(1.0 / 3.0),
    }
    assert sum(normalized.values()) == pytest.approx(1.0)


def test_normalize_weights_returns_empty_when_no_positive_weights_exist():
    assert weight_binding.normalize_weights({"Spine": 0.0, "Head": -0.25}) == {}
