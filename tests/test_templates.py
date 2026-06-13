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
    assert {"upper_arm.L", "upper_arm.R", "upper_leg.L", "upper_leg.R"}.issubset(
        template.required_landmarks
    )
    assert template.mirror_pairs["UpperArm.L"] == "UpperArm.R"
    assert template.mirror_pairs["UpperLeg.L"] == "UpperLeg.R"
