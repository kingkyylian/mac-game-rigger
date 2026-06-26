#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time


REPO_ROOT = Path(__file__).resolve().parents[1]
WEIGHT_BINDING_PATH = REPO_ROOT / "addon/mac_game_rigger/core/weight_binding.py"


def load_weight_binding_module():
    spec = importlib.util.spec_from_file_location("weight_binding", WEIGHT_BINDING_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


weight_binding = load_weight_binding_module()


DEFAULT_VERTEX_COUNTS = (10_000, 50_000, 100_000)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark deterministic Mac Game Rigger weight-binding math."
    )
    parser.add_argument(
        "--vertex-count",
        type=int,
        action="append",
        dest="vertex_counts",
        help="Synthetic vertex count to benchmark. May be passed multiple times.",
    )
    parser.add_argument("--output", type=Path, help="Write JSON report to this path.")
    parser.add_argument(
        "--max-seconds-per-case",
        type=float,
        help="Fail if any case takes longer than this budget.",
    )
    parser.add_argument("--max-influences", type=int, default=4)
    return parser.parse_args(argv)


def synthetic_humanoid_bones() -> list[dict[str, object]]:
    return [
        {"name": "Hips", "head": (0.0, 0.0, 0.0), "tail": (0.0, 0.0, 0.8), "radius": 1.0},
        {"name": "Spine", "head": (0.0, 0.0, 0.8), "tail": (0.0, 0.0, 1.8), "radius": 1.1},
        {"name": "Chest", "head": (0.0, 0.0, 1.8), "tail": (0.0, 0.0, 2.8), "radius": 1.2},
        {"name": "Neck", "head": (0.0, 0.0, 2.8), "tail": (0.0, 0.0, 3.2), "radius": 0.35},
        {"name": "Head", "head": (0.0, 0.0, 3.2), "tail": (0.0, 0.0, 3.9), "radius": 0.55},
        {"name": "UpperArm.L", "head": (-0.45, 0.0, 2.55), "tail": (-1.25, 0.0, 2.1), "radius": 0.35},
        {"name": "LowerArm.L", "head": (-1.25, 0.0, 2.1), "tail": (-1.9, 0.0, 1.65), "radius": 0.28},
        {"name": "Hand.L", "head": (-1.9, 0.0, 1.65), "tail": (-2.25, 0.0, 1.5), "radius": 0.2},
        {"name": "UpperArm.R", "head": (0.45, 0.0, 2.55), "tail": (1.25, 0.0, 2.1), "radius": 0.35},
        {"name": "LowerArm.R", "head": (1.25, 0.0, 2.1), "tail": (1.9, 0.0, 1.65), "radius": 0.28},
        {"name": "Hand.R", "head": (1.9, 0.0, 1.65), "tail": (2.25, 0.0, 1.5), "radius": 0.2},
        {"name": "UpperLeg.L", "head": (-0.28, 0.0, 0.0), "tail": (-0.55, 0.0, -1.2), "radius": 0.4},
        {"name": "LowerLeg.L", "head": (-0.55, 0.0, -1.2), "tail": (-0.45, 0.0, -2.3), "radius": 0.32},
        {"name": "Foot.L", "head": (-0.45, 0.0, -2.3), "tail": (-0.45, -0.35, -2.55), "radius": 0.22},
        {"name": "UpperLeg.R", "head": (0.28, 0.0, 0.0), "tail": (0.55, 0.0, -1.2), "radius": 0.4},
        {"name": "LowerLeg.R", "head": (0.55, 0.0, -1.2), "tail": (0.45, 0.0, -2.3), "radius": 0.32},
        {"name": "Foot.R", "head": (0.45, 0.0, -2.3), "tail": (0.45, -0.35, -2.55), "radius": 0.22},
    ]


def synthetic_vertices(vertex_count: int) -> dict[int, weight_binding.Vector3]:
    if vertex_count <= 0:
        raise ValueError("vertex counts must be positive")
    points: dict[int, weight_binding.Vector3] = {}
    for index in range(vertex_count):
        column = index % 101
        row = (index // 101) % 101
        layer = index // (101 * 101)
        x = ((column / 100.0) - 0.5) * 4.4
        y = ((row / 100.0) - 0.5) * 1.2
        z = -2.6 + (((index * 37 + layer * 11) % 650) / 100.0)
        points[index] = (x, y, z)
    return points


def run_case(
    *,
    vertex_count: int,
    bones: list[dict[str, object]],
    max_influences: int,
    max_seconds: float | None,
) -> dict[str, object]:
    vertex_points = synthetic_vertices(vertex_count)
    started = time.perf_counter()
    vertex_weights = {
        vertex_index: weight_binding.capsule_assignment_details(
            point,
            bones,
            max_influences,
        )["weights"]
        for vertex_index, point in vertex_points.items()
    }
    vertex_weights = weight_binding.ensure_minimum_bone_coverage(
        vertex_weights=vertex_weights,
        vertex_points=vertex_points,
        bones=bones,
        min_vertices_per_bone=weight_binding.MIN_BONE_COVERAGE_VERTICES,
        max_influences=max_influences,
    )
    duration = max(time.perf_counter() - started, 0.000001)
    weighted_vertices = sum(1 for weights in vertex_weights.values() if weights)
    status = "pass"
    if max_seconds is not None and duration > max_seconds:
        status = "fail"
    return {
        "status": status,
        "vertexCount": vertex_count,
        "boneCount": len(bones),
        "weightedVertices": weighted_vertices,
        "maxInfluences": max_influences,
        "durationSeconds": round(duration, 6),
        "verticesPerSecond": round(vertex_count / duration, 2),
    }


def build_report(args: argparse.Namespace) -> dict[str, object]:
    vertex_counts = args.vertex_counts or list(DEFAULT_VERTEX_COUNTS)
    bones = synthetic_humanoid_bones()
    cases = [
        run_case(
            vertex_count=vertex_count,
            bones=bones,
            max_influences=args.max_influences,
            max_seconds=args.max_seconds_per_case,
        )
        for vertex_count in vertex_counts
    ]
    return {
        "schemaVersion": 1,
        "benchmark": "capsule_weight_binding",
        "status": "pass" if all(case["status"] == "pass" for case in cases) else "fail",
        "cases": cases,
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.max_influences <= 0:
        print("--max-influences must be positive", file=sys.stderr)
        return 2
    try:
        report = build_report(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
