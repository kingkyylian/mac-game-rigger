#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plan_unity_animator_smoke_migration as planner


def build_recorder_command(
    *,
    recorder: str,
    fbx: str,
    unity: str,
    timeout_seconds: int,
) -> list[str]:
    return [
        recorder,
        "--fbx",
        fbx,
        "--unity",
        unity,
        "--timeout-seconds",
        str(timeout_seconds),
    ]


def build_health_command(
    *,
    health_checker: str,
    unity: str,
    timeout_seconds: int,
    output: str,
) -> list[str]:
    return [
        health_checker,
        "--unity",
        unity,
        "--timeout-seconds",
        str(timeout_seconds),
        "--output",
        output,
    ]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run configured Animator smoke migration recorder commands for current gaps."
    )
    parser.add_argument("--manifest", default="samples/manifest.json")
    parser.add_argument("--evidence-root", default=".")
    parser.add_argument("--unity", default=planner.DEFAULT_UNITY)
    parser.add_argument("--timeout-seconds", type=int, default=240)
    parser.add_argument("--recorder", default="scripts/record_unity_import_evidence.py")
    parser.add_argument("--health-checker", default="scripts/check_unity_batchmode_health.py")
    parser.add_argument("--preflight-timeout-seconds", type=int, default=90)
    parser.add_argument(
        "--preflight-output",
        default="build/unity-batchmode-health.json",
        help="Path where Unity batchmode health JSON should be written.",
    )
    parser.add_argument("--skip-preflight", action="store_true", help="Skip Unity batchmode health check.")
    parser.add_argument("--dry-run", action="store_true", help="List commands without running them.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    gaps = planner.find_migration_gaps(
        manifest,
        Path(args.evidence_root),
        unity=args.unity,
        timeout_seconds=args.timeout_seconds,
    )
    if not gaps:
        print("No configured Animator smoke migration gaps found.")
        return 0

    planned = [
        {
            **gap,
            "command": build_recorder_command(
                recorder=args.recorder,
                fbx=gap["fbx"],
                unity=args.unity,
                timeout_seconds=args.timeout_seconds,
            ),
        }
        for gap in gaps
    ]

    if args.dry_run:
        print("DRY RUN")
        for gap in planned:
            print(f"{gap['slot']}: {shlex.join(gap['command'])}")
        return 0

    if not args.skip_preflight:
        health_command = build_health_command(
            health_checker=args.health_checker,
            unity=args.unity,
            timeout_seconds=args.preflight_timeout_seconds,
            output=args.preflight_output,
        )
        print(f"Unity preflight: {shlex.join(health_command)}")
        health_result = subprocess.run(health_command, text=True, capture_output=True, check=False)
        if health_result.stdout:
            sys.stdout.write(health_result.stdout)
        if health_result.stderr:
            sys.stderr.write(health_result.stderr)
        if health_result.returncode != 0:
            sys.stderr.write(f"Unity preflight failed with exit code {health_result.returncode}\n")
            return health_result.returncode

    for gap in planned:
        command = gap["command"]
        print(f"{gap['slot']}: {shlex.join(command)}")
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        if result.stdout:
            sys.stdout.write(result.stdout)
        if result.stderr:
            sys.stderr.write(result.stderr)
        if result.returncode != 0:
            sys.stderr.write(f"{gap['slot']} failed with exit code {result.returncode}\n")
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
