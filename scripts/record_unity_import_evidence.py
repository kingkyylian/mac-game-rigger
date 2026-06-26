#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import shlex
import subprocess
import sys


def default_output_path(fbx: Path) -> Path:
    return fbx.parent / "unity-import.json"


def wrap_unity_import_result(
    verifier_payload: dict,
    *,
    checked_on: str,
    unity_editor: str,
    fbx: Path,
    verification_command: list[str],
) -> dict:
    return {
        "schemaVersion": 1,
        "status": verifier_payload.get("status", "unknown"),
        "checkedOn": checked_on,
        "unityEditor": unity_editor,
        "fbx": str(fbx),
        "verificationCommand": shlex.join(verification_command),
        "result": verifier_payload,
    }


def build_verification_command(args: argparse.Namespace) -> list[str]:
    return [
        str(args.verifier),
        "--fbx",
        str(args.fbx),
        "--unity",
        args.unity,
        "--timeout-seconds",
        str(args.timeout_seconds),
    ]


def failure_hint(stderr: str) -> str:
    licensing_markers = [
        "LicenseClient-",
        "[Licensing::Module]",
        "com.unity.editor.headless",
    ]
    if any(marker in stderr for marker in licensing_markers):
        return (
            "\nUnity licensing/bootstrap failure detected. "
            "Open Unity Hub or the Unity Editor once to refresh licensing, "
            "then rerun this recorder outside the sandbox.\n"
        )
    if "Unity-Upm-" in stderr or "listen EPERM" in stderr:
        return (
            "\nUnity Package Manager socket failure detected. "
            "Rerun this recorder outside the sandbox so Unity can open its local IPC socket.\n"
        )
    return ""


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Unity FBX verifier and write evidence/<slot>/unity-import.json."
    )
    parser.add_argument("--fbx", type=Path, required=True)
    parser.add_argument("--unity", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=180)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--checked-on", default=date.today().isoformat())
    parser.add_argument("--verifier", type=Path, default=Path("scripts/verify_unity_fbx_import.sh"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    command = build_verification_command(args)
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        sys.stderr.write(failure_hint(result.stderr))
        return result.returncode

    try:
        verifier_payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"Unity verifier did not return valid JSON: {exc}\n")
        return 1

    output_path = args.output or default_output_path(args.fbx)
    wrapped = wrap_unity_import_result(
        verifier_payload,
        checked_on=args.checked_on,
        unity_editor=args.unity,
        fbx=args.fbx,
        verification_command=command,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(wrapped, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
