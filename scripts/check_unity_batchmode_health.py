#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from record_unity_import_evidence import failure_hint


DEFAULT_UNITY = "/Applications/Unity/Hub/Editor/6000.4.1f1/Unity.app/Contents/MacOS/Unity"


def tail_text(path: Path, line_count: int = 80) -> str:
    if not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-line_count:])


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check whether Unity batchmode can start cleanly.")
    parser.add_argument("--unity", default=DEFAULT_UNITY)
    parser.add_argument("--timeout-seconds", type=int, default=90)
    parser.add_argument("--output", type=Path, help="Write a machine-readable JSON health report.")
    return parser.parse_args(argv)


def write_health_report(
    output_path: Path | None,
    *,
    status: str,
    exit_code: int,
    timed_out: bool,
    unity: str,
    timeout_seconds: int,
    log_tail: str,
    stderr: str = "",
) -> None:
    if output_path is None:
        return
    hint = failure_hint("\n".join(item for item in (stderr, log_tail) if item)).strip()
    payload = {
        "schemaVersion": 1,
        "status": status,
        "exitCode": exit_code,
        "timedOut": timed_out,
        "unity": unity,
        "timeoutSeconds": timeout_seconds,
        "hint": hint,
        "stderr": stderr,
        "logTail": log_tail,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    with tempfile.TemporaryDirectory(prefix="mac-game-rigger-unity-health.") as tmpdir:
        log_path = Path(tmpdir) / "unity-batchmode-health.log"
        command = [
            args.unity,
            "-batchmode",
            "-quit",
            "-nographics",
            "-logFile",
            str(log_path),
        ]
        try:
            result = subprocess.run(
                command,
                text=True,
                capture_output=True,
                check=False,
                timeout=args.timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            log_tail = tail_text(log_path)
            write_health_report(
                args.output,
                status="timeout",
                exit_code=124,
                timed_out=True,
                unity=args.unity,
                timeout_seconds=args.timeout_seconds,
                log_tail=log_tail,
            )
            sys.stderr.write(f"Unity batchmode health check timed out after {args.timeout_seconds} seconds\n")
            if log_tail:
                sys.stderr.write(log_tail + "\n")
                sys.stderr.write(failure_hint(log_tail))
            return 124

        log_tail = tail_text(log_path)
        combined_error = "\n".join(item for item in (result.stderr, log_tail) if item)
        if result.returncode != 0:
            write_health_report(
                args.output,
                status="fail",
                exit_code=result.returncode,
                timed_out=False,
                unity=args.unity,
                timeout_seconds=args.timeout_seconds,
                log_tail=log_tail,
                stderr=result.stderr,
            )
            sys.stderr.write(f"Unity batchmode health check failed with exit code {result.returncode}\n")
            if combined_error:
                sys.stderr.write(combined_error + "\n")
                sys.stderr.write(failure_hint(combined_error))
            return result.returncode

        write_health_report(
            args.output,
            status="pass",
            exit_code=0,
            timed_out=False,
            unity=args.unity,
            timeout_seconds=args.timeout_seconds,
            log_tail=log_tail,
            stderr=result.stderr,
        )
        print("Unity batchmode health check passed")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
