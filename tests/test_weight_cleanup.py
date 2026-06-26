import importlib.util
from pathlib import Path
import sys


MODULE_PATH = Path(__file__).resolve().parents[1] / "addon/mac_game_rigger/core/weight_cleanup.py"
spec = importlib.util.spec_from_file_location("weight_cleanup", MODULE_PATH)
weight_cleanup = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = weight_cleanup
spec.loader.exec_module(weight_cleanup)


class FakeVertexGroup:
    def __init__(self, name, index):
        self.name = name
        self.index = index


class FakeVertexGroups(list):
    def get(self, name):
        for group in self:
            if group.name == name:
                return group
        return None

    def remove(self, group):
        super().remove(group)


class FakeVertexWeight:
    def __init__(self, group, weight):
        self.group = group
        self.weight = weight


class FakeVertex:
    def __init__(self, index, groups):
        self.index = index
        self.groups = groups


class FakeMeshData:
    def __init__(self, vertices):
        self.vertices = vertices


class FakeMesh:
    name = "Mesh"

    def __init__(self):
        self.vertex_groups = FakeVertexGroups(
            [
                FakeVertexGroup("UpperArm.L", 0),
                FakeVertexGroup("LowerArm.L", 1),
                FakeVertexGroup("Hand.L", 2),
            ]
        )
        self.data = FakeMeshData(
            [
                FakeVertex(0, [FakeVertexWeight(0, 1.0)]),
                FakeVertex(1, [FakeVertexWeight(2, 1.0)]),
            ]
        )


def test_find_empty_vertex_group_names_reports_groups_without_positive_weights():
    mesh = FakeMesh()

    assert weight_cleanup.find_empty_vertex_group_names(mesh) == ("LowerArm.L",)


def test_cleanup_mesh_weights_preserves_removed_empty_group_names():
    mesh = FakeMesh()

    result = weight_cleanup.cleanup_mesh_weights(mesh)

    assert result.removed_empty_groups == 1
    assert result.removed_empty_group_names == ("LowerArm.L",)
