#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


DEFAULT_CANDIDATES = "samples/split_mesh_humanoid_candidates.json"


def load_candidate_registry(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    candidates = payload.get("candidates")
    return [candidate for candidate in candidates if isinstance(candidate, dict)] if isinstance(candidates, list) else []


def find_candidate(candidates: list[dict[str, Any]], candidate_id: str) -> dict[str, Any]:
    for candidate in candidates:
        if candidate.get("id") == candidate_id:
            return candidate
    raise ValueError(f"Candidate not found: {candidate_id}")


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def candidate_summary(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": candidate.get("id"),
        "sourceName": candidate.get("sourceName"),
        "sourceUrl": candidate.get("sourceUrl"),
        "license": candidate.get("license"),
    }


def preflight_candidate(candidate: dict[str, Any], source_smoke: Path) -> dict[str, Any]:
    issues: list[str] = []
    smoke = read_json(source_smoke)
    metrics = smoke.get("metrics") if isinstance(smoke, dict) else None
    mesh_count = metrics.get("meshCount") if isinstance(metrics, dict) else None
    suggested_category = metrics.get("suggestedCategory") if isinstance(metrics, dict) else None

    if not isinstance(candidate.get("sourceName"), str) or not candidate.get("sourceName"):
        issues.append("candidate sourceName is required")
    if not isinstance(candidate.get("sourceUrl"), str) or not candidate.get("sourceUrl"):
        issues.append("candidate sourceUrl is required")
    if not isinstance(candidate.get("license"), str) or not candidate.get("license"):
        issues.append("candidate license is required")
    if smoke is None:
        issues.append("source import smoke JSON is missing or invalid")
    elif smoke.get("status") != "pass":
        issues.append("source import smoke must pass")
    if smoke is not None:
        if not isinstance(mesh_count, int):
            issues.append("source import mesh count is missing")
        elif mesh_count <= 1:
            issues.append("source import mesh count must be > 1")
        if suggested_category != "humanoid":
            issues.append("source import suggested category must be humanoid")

    return {
        "status": "pass" if not issues else "blocked",
        "candidate": candidate_summary(candidate),
        "sourceSmoke": str(source_smoke),
        "sourceMeshCount": mesh_count if isinstance(mesh_count, int) else None,
        "suggestedCategory": suggested_category if isinstance(suggested_category, str) else None,
        "issues": issues,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preflight a split-mesh humanoid source import smoke result before workflow intake."
    )
    parser.add_argument("--candidates", default=DEFAULT_CANDIDATES)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--source-smoke", required=True, type=Path)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args(argv)


def print_text(result: dict[str, Any]) -> None:
    print(f"Status: {result['status']}")
    print(f"Candidate: {result['candidate']['id']}")
    print(f"Source meshes: {result['sourceMeshCount']}")
    if result["issues"]:
        print("Issues:")
        for issue in result["issues"]:
            print(f"- {issue}")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        candidate = find_candidate(load_candidate_registry(Path(args.candidates)), args.candidate)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    result = preflight_candidate(candidate, args.source_smoke)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print_text(result)
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
