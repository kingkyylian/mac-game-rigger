#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEST_GLOB = "blender_tests/test_*.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Mac Game Rigger Blender compatibility checks."
    )
    parser.add_argument(
        "--blender",
        action="append",
        default=[],
        help="Path to a Blender executable. May be passed multiple times.",
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Also discover Blender from BLENDER_BIN, PATH, Homebrew, and /Applications.",
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Only collect Blender version metadata.",
    )
    parser.add_argument(
        "--require-version-prefix",
        action="append",
        default=[],
        help=(
            "Require at least one passing Blender version line to start with this "
            "prefix, e.g. 'Blender 4.2'. May be passed multiple times."
        ),
    )
    parser.add_argument(
        "--test-glob",
        default=DEFAULT_TEST_GLOB,
        help=f"Glob of Blender Python tests to run. Default: {DEFAULT_TEST_GLOB}",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=180,
        help="Timeout per Blender test file.",
    )
    parser.add_argument(
        "--output",
        help="Write JSON result to this path.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print JSON to stdout. Use with --output for quieter evidence runs.",
    )
    return parser.parse_args()


def unique_existing_executables(paths: list[str]) -> list[Path]:
    seen: set[Path] = set()
    result: list[Path] = []
    for raw_path in paths:
        if not raw_path:
            continue
        path = Path(raw_path).expanduser()
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved in seen or not resolved.is_file() or not os.access(resolved, os.X_OK):
            continue
        seen.add(resolved)
        result.append(resolved)
    return result


def discover_blenders(explicit_paths: list[str], include_discovery: bool) -> list[Path]:
    candidates = list(explicit_paths)
    if include_discovery:
        candidates.append(os.environ.get("BLENDER_BIN", ""))
        path_blender = shutil.which("blender")
        if path_blender:
            candidates.append(path_blender)
        candidates.extend(
            [
                "/opt/homebrew/bin/blender",
                "/Applications/Blender.app/Contents/MacOS/Blender",
            ]
        )
        candidates.extend(
            glob.glob("/Applications/Blender*.app/Contents/MacOS/Blender")
        )
    return unique_existing_executables(candidates)


def tail(text: str, max_chars: int = 4000) -> str:
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def collect_version(blender: Path, timeout_seconds: int) -> dict[str, object]:
    started = time.monotonic()
    try:
        result = subprocess.run(
            [str(blender), "--version"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "timeout",
            "durationSeconds": round(time.monotonic() - started, 3),
            "stdoutTail": tail(exc.stdout or ""),
            "stderrTail": tail(exc.stderr or ""),
        }

    lines = result.stdout.splitlines()
    version_line = lines[0] if lines else ""
    platform_line = next((line.strip() for line in lines if "build platform:" in line), "")
    return {
        "status": "pass" if result.returncode == 0 else "fail",
        "returnCode": result.returncode,
        "durationSeconds": round(time.monotonic() - started, 3),
        "versionLine": version_line,
        "platformLine": platform_line,
        "stdoutTail": tail(result.stdout),
        "stderrTail": tail(result.stderr),
    }


def run_blender_test(blender: Path, test_path: Path, timeout_seconds: int) -> dict[str, object]:
    started = time.monotonic()
    try:
        result = subprocess.run(
            [
                str(blender),
                "--background",
                "--factory-startup",
                "--python",
                str(test_path),
            ],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "path": str(test_path),
            "status": "timeout",
            "durationSeconds": round(time.monotonic() - started, 3),
            "stdoutTail": tail(exc.stdout or ""),
            "stderrTail": tail(exc.stderr or ""),
        }

    return {
        "path": str(test_path),
        "status": "pass" if result.returncode == 0 else "fail",
        "returnCode": result.returncode,
        "durationSeconds": round(time.monotonic() - started, 3),
        "stdoutTail": tail(result.stdout),
        "stderrTail": tail(result.stderr),
    }


def run_matrix(args: argparse.Namespace) -> tuple[int, dict[str, object]]:
    blenders = discover_blenders(args.blender, args.discover)
    tests = sorted(Path(path) for path in glob.glob(str(REPO_ROOT / args.test_glob)))

    matrix: dict[str, object] = {
        "schemaVersion": 1,
        "repoRoot": str(REPO_ROOT),
        "testGlob": args.test_glob,
        "skipTests": args.skip_tests,
        "requiredVersionPrefixes": args.require_version_prefix,
        "blenders": [],
    }

    if not blenders:
        matrix["status"] = "blocked"
        matrix["reason"] = "no_blender_executable_found"
        return 2, matrix

    overall_status = "pass"
    blender_results: list[dict[str, object]] = []

    for blender in blenders:
        version = collect_version(blender, args.timeout_seconds)
        test_results: list[dict[str, object]] = []
        blender_status = version["status"]

        if version["status"] == "pass" and not args.skip_tests:
            for test_path in tests:
                test_result = run_blender_test(blender, test_path, args.timeout_seconds)
                test_results.append(test_result)
                if test_result["status"] != "pass":
                    blender_status = "fail"
        elif version["status"] != "pass":
            blender_status = "fail"

        if blender_status != "pass":
            overall_status = "fail"

        blender_results.append(
            {
                "path": str(blender),
                "status": blender_status,
                "version": version,
                "tests": test_results,
            }
        )

    discovered_version_lines = [
        str(result.get("version", {}).get("versionLine") or "")
        for result in blender_results
        if isinstance(result.get("version"), dict)
    ]
    if args.require_version_prefix and not any(
        version_line.startswith(prefix)
        for version_line in discovered_version_lines
        for prefix in args.require_version_prefix
    ):
        matrix["status"] = "blocked"
        matrix["reason"] = "required_blender_version_not_found"
        matrix["discoveredVersionLines"] = discovered_version_lines
        matrix["blenders"] = blender_results
        return 2, matrix

    matrix["status"] = overall_status
    matrix["blenders"] = blender_results
    return 0 if overall_status == "pass" else 1, matrix


def main() -> int:
    args = parse_args()
    if args.timeout_seconds < 1:
        print("--timeout-seconds must be >= 1", file=sys.stderr)
        return 64

    exit_code, matrix = run_matrix(args)
    payload = json.dumps(matrix, indent=2, sort_keys=True)
    if not args.quiet:
        print(payload)
    if args.output:
        Path(args.output).write_text(f"{payload}\n", encoding="utf-8")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
