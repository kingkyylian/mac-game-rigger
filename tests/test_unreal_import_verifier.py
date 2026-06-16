import json
import os
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "verify_unreal_fbx_import.sh"


def test_unreal_import_verifier_reports_missing_editor(tmp_path):
    fbx_path = tmp_path / "sample.fbx"
    fbx_path.write_bytes(b"Kaydara FBX Binary  \x00\x1a\x00")

    result = subprocess.run(
        [
            str(SCRIPT_PATH),
            "--fbx",
            str(fbx_path),
            "--unreal",
            str(tmp_path / "missing-unreal"),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "Unreal Editor not found" in result.stderr


def test_unreal_import_verifier_reports_missing_fbx(tmp_path):
    fake_unreal = tmp_path / "fake-unreal"
    fake_unreal.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    fake_unreal.chmod(0o755)

    result = subprocess.run(
        [
            str(SCRIPT_PATH),
            "--fbx",
            str(tmp_path / "missing.fbx"),
            "--unreal",
            str(fake_unreal),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 66
    assert "FBX file not found" in result.stderr


def test_unreal_import_verifier_dry_run_reports_ready(tmp_path):
    fbx_path = tmp_path / "sample.fbx"
    fbx_path.write_bytes(b"Kaydara FBX Binary  \x00\x1a\x00")
    fake_unreal = tmp_path / "fake-unreal"
    fake_unreal.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    fake_unreal.chmod(0o755)

    result = subprocess.run(
        [
            str(SCRIPT_PATH),
            "--fbx",
            str(fbx_path),
            "--unreal",
            str(fake_unreal),
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        env={**os.environ, "PATH": os.environ["PATH"]},
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["fbx"] == str(fbx_path)
    assert payload["unrealEditor"] == str(fake_unreal)


def test_unreal_import_verifier_reports_blocked_until_importer_exists(tmp_path):
    fbx_path = tmp_path / "sample.fbx"
    fbx_path.write_bytes(b"Kaydara FBX Binary  \x00\x1a\x00")
    fake_unreal = tmp_path / "fake-unreal"
    fake_unreal.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    fake_unreal.chmod(0o755)

    result = subprocess.run(
        [
            str(SCRIPT_PATH),
            "--fbx",
            str(fbx_path),
            "--unreal",
            str(fake_unreal),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 78
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked"
    assert payload["reason"] == "unreal_batch_import_not_implemented"

