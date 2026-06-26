import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "addon/mac_game_rigger/core/asset_analysis.py"
spec = importlib.util.spec_from_file_location("asset_analysis", MODULE_PATH)
asset_analysis = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(asset_analysis)

MeshStats = asset_analysis.MeshStats
suggest_category = asset_analysis.suggest_category


def test_suggests_humanoid_for_tall_mesh():
    stats = MeshStats(
        mesh_count=1,
        vertex_count=12000,
        face_count=24000,
        width=1.0,
        depth=0.6,
        height=2.0,
        has_armature=False,
    )

    assert suggest_category(stats) == "humanoid"


def test_suggests_quadruped_for_long_mesh():
    stats = MeshStats(
        mesh_count=1,
        vertex_count=14000,
        face_count=28000,
        width=0.8,
        depth=2.4,
        height=1.0,
        has_armature=False,
    )

    assert suggest_category(stats) == "quadruped"


def test_suggests_quadruped_for_long_narrow_animal_before_tall_ratio():
    stats = MeshStats(
        mesh_count=1,
        vertex_count=962,
        face_count=990,
        width=0.99,
        depth=3.8892,
        height=3.1825,
        has_armature=True,
    )

    assert suggest_category(stats) == "quadruped"


def test_suggests_prop_for_thin_flat_door_like_mesh_before_tall_ratio():
    stats = MeshStats(
        mesh_count=1,
        vertex_count=360,
        face_count=378,
        width=0.7025,
        depth=0.0668,
        height=1.1375,
        has_armature=False,
    )

    assert suggest_category(stats) == "prop"


def test_suggests_prop_for_chunky_box_like_mechanical_asset():
    stats = MeshStats(
        mesh_count=1,
        vertex_count=900,
        face_count=1400,
        width=1.2,
        depth=1.0,
        height=0.8,
        has_armature=False,
    )

    assert suggest_category(stats) == "prop"


def test_suggests_prop_for_low_long_mechanical_asset_before_quadruped():
    stats = MeshStats(
        mesh_count=1,
        vertex_count=1500,
        face_count=2400,
        width=1.0,
        depth=2.1,
        height=0.7,
        has_armature=False,
    )

    assert suggest_category(stats) == "prop"


def test_suggests_unknown_for_invalid_height():
    stats = MeshStats(
        mesh_count=1,
        vertex_count=100,
        face_count=200,
        width=1.0,
        depth=1.0,
        height=0.0,
        has_armature=False,
    )

    assert suggest_category(stats) == "unknown"
