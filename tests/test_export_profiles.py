import importlib.util
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).resolve().parents[1] / "addon/mac_game_rigger/core/export_profiles.py"
spec = importlib.util.spec_from_file_location("export_profiles", MODULE_PATH)
export_profiles = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = export_profiles
spec.loader.exec_module(export_profiles)

ExportProfile = export_profiles.ExportProfile
load_export_profile = export_profiles.load_export_profile
load_builtin_export_profile = export_profiles.load_builtin_export_profile


def test_loads_unity_builtin_export_profile():
    profile = load_builtin_export_profile("unity_fbx")

    assert isinstance(profile, ExportProfile)
    assert profile.name == "Unity FBX"
    assert profile.slug == "unity_fbx"
    assert profile.forward_axis == "-Z"
    assert profile.up_axis == "Y"
    assert profile.add_leaf_bones is False
    assert profile.apply_unit_scale is True
    assert profile.use_selection is True
    assert profile.global_scale == 1.0


def test_loads_unreal_builtin_export_profile():
    profile = load_builtin_export_profile("unreal_fbx")

    assert isinstance(profile, ExportProfile)
    assert profile.name == "Unreal FBX"
    assert profile.slug == "unreal_fbx"
    assert profile.forward_axis == "X"
    assert profile.up_axis == "Z"
    assert profile.add_leaf_bones is False
    assert profile.apply_unit_scale is True
    assert profile.use_selection is True
    assert profile.global_scale == 1.0


def test_load_export_profile_from_custom_json(tmp_path):
    profile_path = tmp_path / "custom.json"
    profile_path.write_text(
        """
{
  "name": "Custom FBX",
  "slug": "custom_fbx",
  "forward_axis": "-Z",
  "up_axis": "Y",
  "add_leaf_bones": false,
  "apply_unit_scale": true,
  "use_selection": false,
  "global_scale": 0.5
}
""".strip(),
        encoding="utf-8",
    )

    profile = load_export_profile(profile_path)

    assert profile == ExportProfile(
        name="Custom FBX",
        slug="custom_fbx",
        forward_axis="-Z",
        up_axis="Y",
        add_leaf_bones=False,
        apply_unit_scale=True,
        use_selection=False,
        global_scale=0.5,
    )
