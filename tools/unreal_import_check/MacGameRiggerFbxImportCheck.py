"""Unreal Editor Python entrypoint for Mac Game Rigger FBX import checks.

Run this inside Unreal Editor with a config JSON path supplied through
MAC_GAME_RIGGER_UNREAL_CONFIG. The verifier prepares that config under:

  Saved/MacGameRiggerImportCheck/import-config.json

This script writes a machine-readable result JSON instead of relying on editor
logs alone.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import traceback


def _default_config_path() -> Path:
    project_root = Path(__file__).resolve().parents[2]
    return project_root / "Saved" / "MacGameRiggerImportCheck" / "import-config.json"


def _load_config() -> dict:
    config_path = Path(os.environ.get("MAC_GAME_RIGGER_UNREAL_CONFIG", _default_config_path()))
    with config_path.open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    config["_configPath"] = str(config_path)
    return config


def _write_result(result_path: str, payload: dict) -> None:
    path = Path(result_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _set_if_available(obj, property_name: str, value) -> None:
    try:
        obj.set_editor_property(property_name, value)
    except Exception:
        pass


def main() -> int:
    config = _load_config()
    result_path = config["resultPath"]

    try:
        import unreal  # type: ignore

        fbx_path = config["fbxPath"]
        destination_path = config.get("destinationPath", "/Game/MacGameRiggerImportCandidate")

        task = unreal.AssetImportTask()
        task.filename = fbx_path
        task.destination_path = destination_path
        task.automated = True
        task.replace_existing = True
        task.save = True

        import_ui = unreal.FbxImportUI()
        _set_if_available(import_ui, "import_mesh", True)
        _set_if_available(import_ui, "import_as_skeletal", True)
        _set_if_available(import_ui, "import_materials", True)
        _set_if_available(import_ui, "import_textures", True)
        task.options = import_ui

        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        imported_paths = list(getattr(task, "imported_object_paths", []) or [])

        status = "pass" if imported_paths else "fail"
        _write_result(
            result_path,
            {
                "status": status,
                "fbxPath": fbx_path,
                "destinationPath": destination_path,
                "importedObjectPaths": imported_paths,
                "configPath": config["_configPath"],
            },
        )
        return 0 if status == "pass" else 1
    except Exception as exc:
        _write_result(
            result_path,
            {
                "status": "fail",
                "reason": "unreal_python_import_exception",
                "message": str(exc),
                "traceback": traceback.format_exc(),
                "configPath": config.get("_configPath"),
            },
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
