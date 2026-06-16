import json
from pathlib import Path
import subprocess


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "create_evidence_skeleton.py"
MANIFEST_PATH = REPO_ROOT / "samples" / "manifest.json"


def run_skeleton(tmp_path, *args):
    return subprocess.run(
        [
            str(SCRIPT_PATH),
            "--manifest",
            str(MANIFEST_PATH),
            "--evidence-root",
            str(tmp_path),
            *args,
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_create_evidence_skeleton_creates_default_trial_slots(tmp_path):
    result = run_skeleton(tmp_path)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert payload["slotCount"] == 10
    assert (tmp_path / "evidence" / "H-001" / "notes.md").is_file()
    assert (tmp_path / "evidence" / "Q-001" / "notes.md").is_file()
    assert (tmp_path / "evidence" / "C-001" / "notes.md").is_file()
    assert (tmp_path / "evidence" / "P-001" / "notes.md").is_file()
    notes = (tmp_path / "evidence" / "H-001" / "notes.md").read_text(encoding="utf-8")
    assert "scripts/register_asset_evidence.py" in notes
    assert "--slot H-001" in notes
    assert "`qa-report.json`" in notes


def test_create_evidence_skeleton_dry_run_does_not_write(tmp_path):
    result = run_skeleton(tmp_path, "--dry-run")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "ready"
    assert not (tmp_path / "evidence").exists()
    assert payload["createdNotes"]


def test_create_evidence_skeleton_preserves_existing_notes(tmp_path):
    notes_path = tmp_path / "evidence" / "H-001" / "notes.md"
    notes_path.parent.mkdir(parents=True)
    notes_path.write_text("custom notes\n", encoding="utf-8")

    result = run_skeleton(tmp_path, "--slot", "H-001")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["skippedNotes"] == [str(notes_path)]
    assert notes_path.read_text(encoding="utf-8") == "custom notes\n"


def test_create_evidence_skeleton_can_overwrite_notes(tmp_path):
    notes_path = tmp_path / "evidence" / "H-001" / "notes.md"
    notes_path.parent.mkdir(parents=True)
    notes_path.write_text("custom notes\n", encoding="utf-8")

    result = run_skeleton(tmp_path, "--slot", "H-001", "--overwrite-notes")

    assert result.returncode == 0
    assert "custom notes" not in notes_path.read_text(encoding="utf-8")


def test_create_evidence_skeleton_reports_missing_slot(tmp_path):
    result = run_skeleton(tmp_path, "--slot", "BAD-001")

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked"
    assert payload["missingSlots"] == ["BAD-001"]
