import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "samples" / "manifest.json"


def test_samples_manifest_has_unique_complete_slots():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    assert manifest["schemaVersion"] == 1
    slots = manifest["slots"]
    assert len(slots) == 25

    slot_ids = [slot["id"] for slot in slots]
    assert len(slot_ids) == len(set(slot_ids))

    for slot in slots:
        assert slot["id"]
        assert slot["category"] in {
            "humanoid",
            "quadruped",
            "tail creature",
            "wing creature",
            "prop",
        }
        assert slot["targetFilename"].startswith(f"{slot['id']}-")
        assert slot["preferredFormat"]
        assert slot["rigTarget"]
        assert isinstance(slot["expectedRisks"], list)
        assert "realAsset" in slot
        assert isinstance(slot["evidence"], dict)
