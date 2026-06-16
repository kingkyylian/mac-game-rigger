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


def test_unreal_import_verifier_fails_when_editor_writes_no_result(tmp_path):
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

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "fail"
    assert payload["reason"] == "unreal_result_missing"
    assert payload["unrealExitCode"] == 0


def test_unreal_import_verifier_runs_prepared_workspace_and_reads_result(tmp_path):
    fbx_path = tmp_path / "sample.fbx"
    fbx_path.write_bytes(b"Kaydara FBX Binary  \x00\x1a\x00")
    project_path = tmp_path / "PreparedProject"
    fake_unreal = tmp_path / "fake-unreal"
    fake_unreal.write_text(
        """#!/usr/bin/env bash
python3 - "$MAC_GAME_RIGGER_UNREAL_CONFIG" <<'PY'
import json
from pathlib import Path
import sys

config = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
Path(config["resultPath"]).write_text(
    json.dumps(
        {
            "status": "pass",
            "fbxPath": config["fbxPath"],
            "destinationPath": config["destinationPath"],
            "importedObjectPaths": ["/Game/MacGameRiggerImportCandidate/sample"],
        },
        sort_keys=True,
    )
    + "\\n",
    encoding="utf-8",
)
PY
""",
        encoding="utf-8",
    )
    fake_unreal.chmod(0o755)

    result = subprocess.run(
        [
            str(SCRIPT_PATH),
            "--fbx",
            str(fbx_path),
            "--unreal",
            str(fake_unreal),
            "--project",
            str(project_path),
            "--timeout-seconds",
            "5",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "pass"
    assert payload["unrealExitCode"] == 0
    assert payload["projectPath"] == str(project_path)
    assert payload["importedObjectPaths"] == ["/Game/MacGameRiggerImportCandidate/sample"]
    assert Path(payload["resultPath"]).exists()


def test_unreal_import_verifier_prepare_only_creates_workspace_without_editor(tmp_path):
    fbx_path = tmp_path / "sample.fbx"
    fbx_path.write_bytes(b"Kaydara FBX Binary  \x00\x1a\x00")
    project_path = tmp_path / "PreparedProject"

    result = subprocess.run(
        [
            str(SCRIPT_PATH),
            "--fbx",
            str(fbx_path),
            "--project",
            str(project_path),
            "--prepare-only",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "prepared"
    assert payload["projectPath"] == str(project_path)
    assert Path(payload["copiedFbx"]).read_bytes() == fbx_path.read_bytes()
    assert Path(payload["scriptPath"]).read_text(encoding="utf-8").startswith(
        '"""Unreal Editor Python entrypoint'
    )
    assert Path(payload["configPath"]).exists()
    assert payload["resultPath"].endswith("Saved/MacGameRiggerImportCheck/import-result.json")
