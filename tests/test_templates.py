import importlib.util
import json
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).resolve().parents[1] / "addon/mac_game_rigger/core/templates.py"
spec = importlib.util.spec_from_file_location("templates", MODULE_PATH)
templates = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = templates
spec.loader.exec_module(templates)

BoneSpec = templates.BoneSpec
RigTemplate = templates.RigTemplate
load_template = templates.load_template

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_loads_humanoid_template_from_json_and_counts_bones(tmp_path):
    template_path = tmp_path / "humanoid.json"
    template_path.write_text(
        json.dumps(
            {
                "name": "Humanoid",
                "category": "humanoid",
                "required_landmarks": ["hips", "spine", "head"],
                "mirror_pairs": {"UpperArm.L": "UpperArm.R"},
                "bones": [
                    {
                        "name": "Hips",
                        "parent": None,
                        "head_landmark": "hips",
                        "tail_landmark": "spine",
                    },
                    {
                        "name": "Spine",
                        "parent": "Hips",
                        "head_landmark": "spine",
                        "tail_landmark": "head",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    template = load_template(template_path)

    assert isinstance(template, RigTemplate)
    assert template.name == "Humanoid"
    assert template.category == "humanoid"
    assert template.required_landmarks == ("hips", "spine", "head")
    assert template.mirror_pairs == {"UpperArm.L": "UpperArm.R"}
    assert len(template.bones) == 2
    assert template.bones[0] == BoneSpec(
        name="Hips",
        parent=None,
        head_landmark="hips",
        tail_landmark="spine",
    )
    assert template.bones[1].parent == "Hips"


def test_loads_builtin_humanoid_template_with_core_game_bones():
    template = load_template(REPO_ROOT / "addon/mac_game_rigger/templates/humanoid.json")
    bone_names = {bone.name for bone in template.bones}

    assert template.category == "humanoid"
    assert len(template.bones) == 17
    assert {"Hips", "Spine", "UpperArm.L", "UpperLeg.R", "Foot.L", "Foot.R"}.issubset(
        bone_names
    )
    assert template.required_landmarks
    assert {"hips", "spine", "chest", "neck", "head"}.issubset(template.required_landmarks)
    assert {"hip.L", "hip.R"}.issubset(template.required_landmarks)
    assert {"upper_arm.L", "upper_arm.R", "upper_leg.L", "upper_leg.R"}.issubset(
        template.required_landmarks
    )
    assert template.mirror_pairs["UpperArm.L"] == "UpperArm.R"
    assert template.mirror_pairs["UpperLeg.L"] == "UpperLeg.R"
    upper_leg_l = next(bone for bone in template.bones if bone.name == "UpperLeg.L")
    upper_leg_r = next(bone for bone in template.bones if bone.name == "UpperLeg.R")
    assert upper_leg_l.head_landmark == "hip.L"
    assert upper_leg_r.head_landmark == "hip.R"


def test_loads_builtin_quadruped_template_with_tail_and_leg_chains():
    template = load_template(REPO_ROOT / "addon/mac_game_rigger/templates/quadruped.json")
    bone_names = {bone.name for bone in template.bones}

    assert template.category == "quadruped"
    assert len(template.bones) >= 20
    assert {"FrontUpperLeg.L", "RearUpperLeg.R", "Tail.001"}.issubset(bone_names)
    assert {"pelvis", "spine", "chest", "neck", "head"}.issubset(
        template.required_landmarks
    )
    assert {"front_leg.L", "front_leg.R", "rear_leg.L", "rear_leg.R"}.issubset(
        template.required_landmarks
    )
    assert {"tail_base", "tail_tip"}.issubset(template.required_landmarks)
    assert template.mirror_pairs["FrontUpperLeg.L"] == "FrontUpperLeg.R"
    assert template.mirror_pairs["RearUpperLeg.L"] == "RearUpperLeg.R"


def test_loads_builtin_tail_creature_template_with_long_neck_and_tail_chains():
    template = load_template(REPO_ROOT / "addon/mac_game_rigger/templates/tail_creature.json")
    bone_names = {bone.name for bone in template.bones}

    assert template.category == "tail creature"
    assert {"Neck.001", "Neck.002", "Tail.001", "Tail.002", "Tail.003"}.issubset(
        bone_names
    )
    assert {"neck_base", "neck_mid", "head", "tail_base", "tail_mid", "tail_tip"}.issubset(
        template.required_landmarks
    )
    neck_001 = next(bone for bone in template.bones if bone.name == "Neck.001")
    neck_002 = next(bone for bone in template.bones if bone.name == "Neck.002")
    tail_003 = next(bone for bone in template.bones if bone.name == "Tail.003")
    assert neck_001.parent == "Chest"
    assert neck_002.parent == "Neck.001"
    assert tail_003.parent == "Tail.002"


def test_loads_builtin_prop_hinge_template_with_base_and_moving_part():
    template = load_template(REPO_ROOT / "addon/mac_game_rigger/templates/prop_hinge.json")
    bone_names = {bone.name for bone in template.bones}

    assert template.category == "prop"
    assert {"PropBase", "Hinge", "MovingPart"}.issubset(bone_names)
    assert {"base", "hinge", "moving_part", "moving_tip"}.issubset(
        template.required_landmarks
    )
    hinge = next(bone for bone in template.bones if bone.name == "Hinge")
    moving_part = next(bone for bone in template.bones if bone.name == "MovingPart")
    assert hinge.parent == "PropBase"
    assert moving_part.parent == "Hinge"
