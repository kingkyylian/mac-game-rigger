#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "samples" / "manifest.json"
DEFAULT_SLOT_IDS = (
    "H-001",
    "H-002",
    "H-003",
    "H-006",
    "H-009",
    "H-010",
    "Q-001",
    "Q-002",
    "C-001",
    "P-001",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create production-trial evidence folder skeletons without fake artifacts."
    )
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Manifest JSON path.")
    parser.add_argument(
        "--evidence-root",
        default=str(REPO_ROOT),
        help="Root where the evidence/ directory should be created.",
    )
    parser.add_argument(
        "--slot",
        action="append",
        default=[],
        help="Slot id to scaffold. May be passed multiple times. Defaults to production-trial set.",
    )
    parser.add_argument(
        "--overwrite-notes",
        action="store_true",
        help="Overwrite existing notes.md files.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print planned changes without writing.")
    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def slots_by_id(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    slots = manifest.get("slots")
    if not isinstance(slots, list):
        print("Manifest slots must be a list.", file=sys.stderr)
        raise SystemExit(64)
    return {slot["id"]: slot for slot in slots if isinstance(slot, dict) and "id" in slot}


def notes_template(slot: dict[str, Any]) -> str:
    slot_id = slot["id"]
    risks = slot.get("expectedRisks") or []
    risk_lines = "\n".join(f"- {risk}" for risk in risks) if risks else "- none listed"
    return f"""# {slot_id} Evidence Notes

Category: {slot.get("category", "")}
Target filename: `{slot.get("targetFilename", "")}`
Rig target: {slot.get("rigTarget", "")}

## Expected Risks

{risk_lines}

## Required Artifacts

- [ ] `qa-report.json`
- [ ] `preview-neutral.png`
- [ ] `preview-pose.png` when relevant
- [ ] `export-unity.fbx` or `export.fbx`
- [ ] `unity-import.json` when Unity import is run
- [ ] `unreal-import.json` when Unreal import is run or blocked

## Review

Deformation score:
Unity import status:
Unreal import status:
Manual cleanup required:
Failure type:

## Register Command

```bash
scripts/register_asset_evidence.py \\
  --slot {slot_id} \\
  --source-name "<source asset name>" \\
  --source-url "<source url or ticket>" \\
  --license "<license>" \\
  --external-path "<source asset path>" \\
  --qa-report evidence/{slot_id}/qa-report.json \\
  --preview-neutral evidence/{slot_id}/preview-neutral.png \\
  --export-unity-fbx evidence/{slot_id}/export-unity.fbx \\
  --notes evidence/{slot_id}/notes.md \\
  --deformation-score <1-5> \\
  --unity-status <pass|fail|blocked|not tested> \\
  --unreal-status <pass|fail|blocked|not tested> \\
  --evidence-root . \\
  --check-files
```
"""


def create_skeleton(
    manifest: dict[str, Any],
    evidence_root: Path,
    slot_ids: tuple[str, ...],
    *,
    dry_run: bool,
    overwrite_notes: bool,
) -> dict[str, Any]:
    by_id = slots_by_id(manifest)
    created_dirs: list[str] = []
    created_notes: list[str] = []
    skipped_notes: list[str] = []
    missing_slots: list[str] = []

    for slot_id in slot_ids:
        slot = by_id.get(slot_id)
        if slot is None:
            missing_slots.append(slot_id)
            continue

        slot_dir = evidence_root / "evidence" / slot_id
        notes_path = slot_dir / "notes.md"
        if not dry_run:
            existed_before = slot_dir.exists()
            slot_dir.mkdir(parents=True, exist_ok=True)
            if not existed_before:
                created_dirs.append(str(slot_dir))
        else:
            created_dirs.append(str(slot_dir))

        if notes_path.exists() and not overwrite_notes:
            skipped_notes.append(str(notes_path))
            continue
        if not dry_run:
            notes_path.write_text(notes_template(slot), encoding="utf-8")
        created_notes.append(str(notes_path))

    status = "blocked" if missing_slots else "ready"
    return {
        "status": status,
        "slotCount": len(slot_ids),
        "createdDirs": created_dirs,
        "createdNotes": created_notes,
        "skippedNotes": skipped_notes,
        "missingSlots": missing_slots,
    }


def main() -> int:
    args = parse_args()
    slot_ids = tuple(args.slot) if args.slot else DEFAULT_SLOT_IDS
    manifest = load_manifest(Path(args.manifest))
    result = create_skeleton(
        manifest,
        Path(args.evidence_root),
        slot_ids,
        dry_run=args.dry_run,
        overwrite_notes=args.overwrite_notes,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
