#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_SCRIPT = REPO_ROOT / "tools/blender_asset_workflow.py"
DEFAULT_EVIDENCE_ROOT = REPO_ROOT / "build/blender-workflow-benchmark"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark the end-to-end Mac Game Rigger Blender asset workflow."
    )
    parser.add_argument("--blender", default="blender", help="Blender executable to run.")
    parser.add_argument(
        "--asset",
        type=Path,
        action="append",
        dest="assets",
        required=True,
        help="Asset to process. May be passed multiple times.",
    )
    parser.add_argument("--template", default="humanoid")
    parser.add_argument("--camera-axis", choices=("x", "y"), default="x")
    parser.add_argument("--evidence-root", type=Path, default=DEFAULT_EVIDENCE_ROOT)
    parser.add_argument("--output", type=Path, help="Write JSON report to this path.")
    parser.add_argument(
        "--max-seconds-per-case",
        type=float,
        help="Fail if any workflow case exceeds this runtime budget.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=300,
        help="Subprocess timeout per Blender workflow case.",
    )
    parser.add_argument("--prop-hinge-pivot-x", type=float)
    parser.add_argument("--prop-hinge-base-x", type=float)
    parser.add_argument("--prop-hinge-axis", choices=("x", "y", "z"))
    return parser.parse_args(argv)


def case_slug(index: int, asset_path: Path, template: str) -> str:
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]+", "-", asset_path.stem).strip("-") or "asset"
    return f"{index:02d}-{template}-{safe_stem}"


def workflow_summary_payload(summary_path: Path) -> dict[str, Any] | None:
    if not summary_path.exists():
        return None
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    return {
        "status": payload.get("status"),
        "template": payload.get("template"),
        "meshCount": payload.get("meshCount"),
        "poseDeformationStatus": (payload.get("poseDeformation") or {}).get("status"),
        "qa": payload.get("qa"),
        "artifacts": payload.get("artifacts"),
    }


def command_for_case(
    *,
    blender: str,
    asset_path: Path,
    evidence_dir: Path,
    summary_path: Path,
    template: str,
    camera_axis: str,
    args: argparse.Namespace,
) -> list[str]:
    command = [
        blender,
        "--background",
        "--factory-startup",
        "--python",
        str(WORKFLOW_SCRIPT),
        "--",
        "--asset",
        str(asset_path),
        "--evidence-dir",
        str(evidence_dir),
        "--summary",
        str(summary_path),
        "--template",
        template,
        "--camera-axis",
        camera_axis,
    ]
    if args.prop_hinge_pivot_x is not None:
        command.extend(["--prop-hinge-pivot-x", str(args.prop_hinge_pivot_x)])
    if args.prop_hinge_base_x is not None:
        command.extend(["--prop-hinge-base-x", str(args.prop_hinge_base_x)])
    if args.prop_hinge_axis is not None:
        command.extend(["--prop-hinge-axis", args.prop_hinge_axis])
    return command


def tail(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def run_case(index: int, asset: Path, args: argparse.Namespace) -> dict[str, Any]:
    asset_path = asset.expanduser().resolve()
    evidence_dir = args.evidence_root.expanduser().resolve() / case_slug(
        index, asset_path, args.template
    )
    summary_path = evidence_dir / "workflow-summary.json"
    command = command_for_case(
        blender=args.blender,
        asset_path=asset_path,
        evidence_dir=evidence_dir,
        summary_path=summary_path,
        template=args.template,
        camera_axis=args.camera_axis,
        args=args,
    )
    started = time.perf_counter()
    timed_out = False
    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            timeout=args.timeout_seconds,
            check=False,
        )
        exit_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = None
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
    duration = max(time.perf_counter() - started, 0.000001)
    budget_exceeded = (
        args.max_seconds_per_case is not None and duration > args.max_seconds_per_case
    )
    status = "pass"
    if timed_out or exit_code != 0 or budget_exceeded:
        status = "fail"
    summary_payload = workflow_summary_payload(summary_path)
    return {
        "status": status,
        "asset": str(asset_path),
        "template": args.template,
        "evidenceDir": str(evidence_dir),
        "summary": str(summary_path),
        "summaryExists": summary_path.exists(),
        "workflowSummary": summary_payload,
        "exitCode": exit_code,
        "timedOut": timed_out,
        "timeoutSeconds": args.timeout_seconds,
        "durationSeconds": round(duration, 6),
        "maxSecondsPerCase": args.max_seconds_per_case,
        "budgetExceeded": budget_exceeded,
        "command": command,
        "stdoutTail": tail(stdout),
        "stderrTail": tail(stderr),
    }


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    cases = [run_case(index, asset, args) for index, asset in enumerate(args.assets, start=1)]
    return {
        "schemaVersion": 1,
        "benchmark": "blender_asset_workflow",
        "status": "pass" if all(case["status"] == "pass" for case in cases) else "fail",
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.timeout_seconds <= 0:
        print("--timeout-seconds must be positive", file=sys.stderr)
        return 2
    missing_assets = [str(asset) for asset in args.assets if not asset.expanduser().exists()]
    if missing_assets:
        print("Missing asset(s): " + ", ".join(missing_assets), file=sys.stderr)
        return 2
    report = build_report(args)
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
