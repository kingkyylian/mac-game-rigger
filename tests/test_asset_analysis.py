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
