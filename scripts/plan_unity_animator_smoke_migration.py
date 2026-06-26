#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import sys


DEFAULT_UNITY = "/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity"


def evidence_status(value: object) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        status = value.get("status")
        return status if isinstance(status, str) else None
    return None


def has_configured_animator_smoke(evidence_root: Path, slot_id: str) -> bool:
    path = evidence_root / "evidence" / slot_id / "unity-import.json"
    if not path.is_file():
        return False
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    result = payload.get("result")
    return isinstance(result, dict) and "configuredAnimatorSmoke" in result


def build_command(fbx: str, unity: str, timeout_seconds: int) -> list[str]:
    return [
        "scripts/record_unity_import_evidence.py",
        "--fbx",
        fbx,
        "--unity",
        unity,
        "--timeout-seconds",
        str(timeout_seconds),
    ]


def find_migration_gaps(
    manifest: dict,
    evidence_root: Path,
    *,
    unity: str = DEFAULT_UNITY,
    timeout_seconds: int = 240,
) -> list[dict]:
    gaps: list[dict] = []
    for slot in manifest.get("slots", []):
        evidence = slot.get("evidence")
        if not isinstance(evidence, dict):
            continue
        slot_id = slot.get("id")
        if not isinstance(slot_id, str) or not slot_id:
            continue
        if slot.get("category") != "humanoid":
            continue
        score = evidence.get("deformationScore")
        if not isinstance(score, int) or score < 3:
            continue
        if evidence_status(evidence.get("unityImport")) != "pass":
            continue
        if has_configured_animator_smoke(evidence_root, slot_id):
            continue
        fbx = evidence.get("exportUnityFbx")
        if not isinstance(fbx, str) or not fbx:
            continue
        command = build_command(fbx, unity, timeout_seconds)
        gaps.append(
            {
                "slot": slot_id,
                "fbx": fbx,
                "unity": unity,
                "timeoutSeconds": timeout_seconds,
                "command": command,
            }
        )
    return gaps


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List humanoid Unity import evidence files missing configuredAnimatorSmoke."
    )
    parser.add_argument("--manifest", default="samples/manifest.json")
    parser.add_argument("--evidence-root", default=".")
    parser.add_argument("--unity", default=DEFAULT_UNITY)
    parser.add_argument("--timeout-seconds", type=int, default=240)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    gaps = find_migration_gaps(
        manifest,
        Path(args.evidence_root),
        unity=args.unity,
        timeout_seconds=args.timeout_seconds,
    )
    if args.json:
        print(json.dumps({"gaps": gaps}, indent=2))
        return 0

    if not gaps:
        print("No configured Animator smoke migration gaps found.")
        return 0
    for gap in gaps:
        print(f"{gap['slot']}: {shlex.join(gap['command'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
