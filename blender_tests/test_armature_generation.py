import sys
from pathlib import Path
import traceback

import bpy


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "addon"))

try:
    from mac_game_rigger.core.armature_builder import (  # noqa: E402
        build_armature_from_template,
        collect_landmark_positions,
    )
    from mac_game_rigger.core.templates import BoneSpec, RigTemplate, load_template  # noqa: E402
except Exception:
    traceback.print_exc()
    raise SystemExit(1)


def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()


def add_landmark(name, location):
    bpy.ops.object.empty_add(type="SPHERE", location=location)
    bpy.context.object.name = f"MGR_Landmark_{name}"


def seed_humanoid_landmarks(required_names):
    for index, name in enumerate(required_names):
        x = -0.4 if name.endswith(".R") else 0.4 if name.endswith(".L") else 0.0
        y = index * 0.01
        z = 0.5 + index * 0.08
        add_landmark(name, (x, y, z))


def run_test():
    reset_scene()

    template = load_template(REPO_ROOT / "addon/mac_game_rigger/templates/humanoid.json")
    seed_humanoid_landmarks(template.required_landmarks)
    positions = collect_landmark_positions(bpy.context.scene)

    assert "hips" in positions
    assert "head" in positions

    armature = build_armature_from_template(template, positions)

    assert armature.name == "MGR_Armature"
    assert armature.type == "ARMATURE"
    assert "Hips" in armature.data.bones
    assert "Spine" in armature.data.bones
    assert "UpperArm.L" in armature.data.bones
    assert armature.data.bones["Spine"].parent == armature.data.bones["Hips"]
    assert armature.data.bones["Chest"].parent == armature.data.bones["Spine"]

    zero_template = RigTemplate(
        name="Zero Test",
        category="test",
        required_landmarks=("same",),
        bones=(
            BoneSpec(
                name="ZeroLength",
                parent=None,
                head_landmark="same",
                tail_landmark="same",
            ),
        ),
        mirror_pairs={},
    )
    zero_armature = build_armature_from_template(
        zero_template,
        {"same": (0.0, 0.0, 0.0)},
        name="MGR_Zero_Armature",
    )
    assert zero_armature.data.bones["ZeroLength"].length > 0.0


try:
    try:
        run_test()
    except Exception:
        traceback.print_exc()
        raise SystemExit(1)
finally:
    pass

print("MGR_ARMATURE_GENERATION_TEST_OK")
