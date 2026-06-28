import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools/blender_asset_import_smoke.py"
spec = importlib.util.spec_from_file_location("blender_asset_import_smoke", MODULE_PATH)
blender_asset_import_smoke = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(blender_asset_import_smoke)


def test_remove_non_exportable_import_objects_drops_gltf_not_exported_meshes():
    class FakeCollection:
        def __init__(self, name):
            self.name = name

    class FakeObject:
        def __init__(self, name, obj_type, collection_names):
            self.name = name
            self.type = obj_type
            self.users_collection = [FakeCollection(name) for name in collection_names]

    visible_mesh = FakeObject("VisibleMesh", "MESH", ["Collection"])
    not_exported_mesh = FakeObject("Icosphere", "MESH", ["glTF_not_exported"])
    hidden_empty = FakeObject("HiddenEmpty", "EMPTY", ["glTF_not_exported"])
    removed = []

    class FakeObjects(list):
        def remove(self, obj, do_unlink):
            assert do_unlink is True
            removed.append(obj.name)
            super().remove(obj)

    class FakeScene:
        objects = FakeObjects([visible_mesh, not_exported_mesh, hidden_empty])

    class FakeData:
        objects = FakeScene.objects

    class FakeContext:
        scene = FakeScene()

    class FakeBpy:
        context = FakeContext()
        data = FakeData()

    summary = blender_asset_import_smoke.remove_non_exportable_import_objects(FakeBpy)

    assert summary == {
        "removedObjects": 1,
        "removedObjectNames": ["Icosphere"],
    }
    assert removed == ["Icosphere"]
    assert [obj.name for obj in FakeScene.objects] == ["VisibleMesh", "HiddenEmpty"]
