#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys
from typing import Any, Callable, NamedTuple


REPO_ROOT = Path(__file__).resolve().parents[1]
PLANNER_PATH = REPO_ROOT / "scripts" / "plan_split_mesh_humanoid_intake.py"
DEFAULT_MANIFEST = "samples/manifest.json"
DEFAULT_CANDIDATES = "samples/split_mesh_humanoid_candidates.json"
DEFAULT_EVIDENCE_ROOT = "."
DEFAULT_BLENDER = "blender"


class CommandResult(NamedTuple):
    returncode: int
    stdout: str
    stderr: str


def load_planner():
    spec = importlib.util.spec_from_file_location("plan_split_mesh_humanoid_intake", PLANNER_PATH)
    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise RuntimeError(f"Cannot load planner: {PLANNER_PATH}")
    spec.loader.exec_module(module)
    return module


def build_runner_plan(
    manifest: dict[str, Any],
    *,
    slot_id: str,
    asset: Path,
    candidate: dict[str, Any],
    source_name: str,
    source_url: str,
    license_name: str,
    blender: str = DEFAULT_BLENDER,
    manifest_path: str = DEFAULT_MANIFEST,
    evidence_root: Path = Path(DEFAULT_EVIDENCE_ROOT),
) -> dict[str, Any]:
    planner = load_planner()
    slot = planner.find_slot(manifest, slot_id)
    if not planner.is_empty_slot(slot):
        raise ValueError(f"Slot {slot_id} is not empty")
    intake = planner.build_intake_plan(
        manifest,
        slot_id=slot_id,
        asset=asset,
        candidate=candidate,
        source_name=source_name,
        source_url=source_url,
        license_name=license_name,
        blender=blender,
        manifest_path=manifest_path,
        evidence_root=evidence_root,
    )
    commands = intake["commands"]
    if "candidatePreflight" not in commands:
        raise ValueError("candidatePreflight is required for split-mesh humanoid intake runner")

    return {
        "status": "ready",
        "slot": intake["slot"],
        "asset": intake["asset"],
        "evidenceDir": intake["evidenceDir"],
        "candidate": intake.get("candidate"),
        "acceptance": intake["acceptance"],
        "workflowSummary": str(Path(intake["evidenceDir"]) / "workflow-summary.json"),
        "reviewPacket": [
            "scripts/create_split_mesh_review_packet.py",
            "--slot",
            intake["slot"],
            "--source-smoke",
            str(Path(intake["evidenceDir"]) / "asset-import-smoke.json"),
            "--workflow-summary",
            str(Path(intake["evidenceDir"]) / "workflow-summary.json"),
            "--output",
            str(Path(intake["evidenceDir"]) / "notes.md"),
            "--force",
            "--json",
        ],
        "phases": [
            {"name": "sourceImportSmoke", "command": commands["sourceImportSmoke"]},
            {"name": "candidatePreflight", "command": commands["candidatePreflight"]},
            {"name": "workflow", "command": commands["workflow"]},
        ],
        "registration": {
            "status": "manual_review_required",
            "command": commands["registerEvidence"],
            "requiredFields": [
                "deformationScore",
                "visualReviewStatus",
                "visualReviewNotes",
                "cleanupLimitations",
            ],
        },
        "generateEvidenceReport": commands["generateEvidenceReport"],
        "strictVerifier": [
            "scripts/verify_split_mesh_humanoid_evidence.py",
            "--manifest",
            manifest_path,
            "--evidence-root",
            str(evidence_root),
            "--slot",
            intake["slot"],
            "--json",
        ],
    }


def run_command(command: list[str]) -> CommandResult:
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    return CommandResult(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def workflow_mesh_count(summary_path: Path) -> int | None:
    payload = read_json(summary_path)
    if not isinstance(payload, dict):
        return None
    mesh_count = payload.get("meshCount")
    if isinstance(mesh_count, int):
        return mesh_count
    qa = payload.get("qa")
    mesh_count = qa.get("mesh_count") if isinstance(qa, dict) else None
    return mesh_count if isinstance(mesh_count, int) else None


def validate_workflow_split_mesh(summary_path: Path) -> dict[str, Any]:
    mesh_count = workflow_mesh_count(summary_path)
    issues = []
    if not isinstance(mesh_count, int):
        issues.append("rig workflow mesh count is missing")
    elif mesh_count <= 1:
        issues.append("rig workflow mesh count must be > 1")
    return {
        "status": "pass" if not issues else "blocked",
        "summary": str(summary_path),
        "rigMeshCount": mesh_count,
        "issues": issues,
    }


def run_phases(
    plan: dict[str, Any],
    *,
    runner: Callable[[list[str]], CommandResult] = run_command,
) -> dict[str, Any]:
    completed = []
    for phase in plan["phases"]:
        command = phase["command"]
        result = runner(command)
        phase_result = {
            "name": phase["name"],
            "command": command,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
        completed.append(phase_result)
        if result.returncode != 0:
            return {
                "status": "failed",
                "failedPhase": phase["name"],
                "completedPhases": completed,
                "registrationCommand": plan["registration"]["command"],
            }

    split_mesh_check = validate_workflow_split_mesh(Path(plan["workflowSummary"]))
    if split_mesh_check["status"] != "pass":
        return {
            "status": "blocked",
            "failedPhase": "workflowSplitMeshCheck",
            "completedPhases": completed,
            "workflowSplitMeshCheck": split_mesh_check,
            "issues": split_mesh_check["issues"],
            "registrationCommand": plan["registration"]["command"],
        }

    review_packet = runner(plan["reviewPacket"])
    review_packet_result = {
        "command": plan["reviewPacket"],
        "returncode": review_packet.returncode,
        "stdout": review_packet.stdout,
        "stderr": review_packet.stderr,
    }
    if review_packet.returncode != 0:
        return {
            "status": "failed",
            "failedPhase": "reviewPacket",
            "completedPhases": completed,
            "workflowSplitMeshCheck": split_mesh_check,
            "reviewPacket": review_packet_result,
            "registrationCommand": plan["registration"]["command"],
        }

    return {
        "status": "needs_registration_review",
        "completedPhases": completed,
        "workflowSplitMeshCheck": split_mesh_check,
        "reviewPacket": review_packet_result,
        "registrationCommand": plan["registration"]["command"],
        "nextCommand": plan["strictVerifier"],
        "notes": [
            "Review generated previews before registering evidence.",
            "Set deformation score and visual review status manually; do not auto-register from structural QA alone.",
        ],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run guarded source-smoke, preflight, and workflow phases for split-mesh humanoid intake."
    )
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--candidates", default=DEFAULT_CANDIDATES)
    parser.add_argument("--evidence-root", default=DEFAULT_EVIDENCE_ROOT)
    parser.add_argument("--slot", help="Humanoid manifest slot to use. Defaults to first empty humanoid slot.")
    parser.add_argument("--asset", required=True, type=Path)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--blender", default=DEFAULT_BLENDER)
    parser.add_argument("--dry-run", action="store_true", help="Print the guarded runner plan without executing phases.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args(argv)


def print_text(payload: dict[str, Any]) -> None:
    print(f"Status: {payload['status']}")
    if "phases" in payload:
        for phase in payload["phases"]:
            print(f"{phase['name']}: {shlex.join(phase['command'])}")
    if "registration" in payload:
        print(f"registration: {payload['registration']['status']}")
        print(f"registrationCommand: {shlex.join(payload['registration']['command'])}")
    if "registrationCommand" in payload:
        print(f"registrationCommand: {shlex.join(payload['registrationCommand'])}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    planner = load_planner()
    try:
        manifest = planner.load_manifest(Path(args.manifest))
        candidate = planner.find_candidate(planner.load_candidate_registry(Path(args.candidates)), args.candidate)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    source_name = str(candidate.get("sourceName") or "Split-mesh humanoid candidate")
    source_url = str(candidate.get("sourceUrl") or "manual-intake")
    license_name = str(candidate.get("license") or "manual-review-required")
    open_slots = planner.find_open_humanoid_slots(manifest)
    slot_id = args.slot or (str(open_slots[0]["id"]) if open_slots else "")
    if not slot_id:
        print("No open humanoid slot is available.", file=sys.stderr)
        return 2

    try:
        plan = build_runner_plan(
            manifest,
            slot_id=slot_id,
            asset=args.asset,
            candidate=candidate,
            source_name=source_name,
            source_url=source_url,
            license_name=license_name,
            blender=args.blender,
            manifest_path=args.manifest,
            evidence_root=Path(args.evidence_root),
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    payload = plan if args.dry_run else run_phases(plan)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print_text(payload)
    return 0 if payload["status"] in {"ready", "needs_registration_review"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
