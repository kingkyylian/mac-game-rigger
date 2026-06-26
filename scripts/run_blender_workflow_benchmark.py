#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
import subprocess
import struct
import sys
import time
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_SCRIPT = REPO_ROOT / "tools/blender_asset_workflow.py"
DEFAULT_EVIDENCE_ROOT = REPO_ROOT / "build/blender-workflow-benchmark"


@dataclass(frozen=True)
class BenchmarkCase:
    asset: Path
    template: str
    synthetic_spec: dict[str, Any] | None = None
    slot_id: str | None = None


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
        default=[],
        help="Asset to process. May be passed multiple times.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Sample manifest used by --slot real-asset benchmark cases.",
    )
    parser.add_argument(
        "--slot",
        action="append",
        dest="slots",
        default=[],
        help="Manifest slot id to process. May be passed multiple times.",
    )
    parser.add_argument(
        "--synthetic-humanoid-vertices",
        type=int,
        action="append",
        dest="synthetic_humanoid_vertices",
        default=[],
        help="Generate a synthetic humanoid OBJ with this vertex count before benchmarking.",
    )
    parser.add_argument(
        "--synthetic-multimesh-humanoid-vertices",
        type=int,
        action="append",
        dest="synthetic_multimesh_humanoid_vertices",
        default=[],
        help="Generate a multi-mesh synthetic humanoid glTF with this vertex count.",
    )
    parser.add_argument(
        "--synthetic-quadruped-vertices",
        type=int,
        action="append",
        dest="synthetic_quadruped_vertices",
        default=[],
        help="Generate a synthetic quadruped OBJ with this vertex count.",
    )
    parser.add_argument(
        "--synthetic-tail-creature-vertices",
        type=int,
        action="append",
        dest="synthetic_tail_creature_vertices",
        default=[],
        help="Generate a synthetic tail creature OBJ with this vertex count.",
    )
    parser.add_argument(
        "--synthetic-prop-hinge-vertices",
        type=int,
        action="append",
        dest="synthetic_prop_hinge_vertices",
        default=[],
        help="Generate a synthetic prop hinge OBJ with this vertex count.",
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


def template_for_manifest_slot(slot: dict[str, Any]) -> str:
    category = str(slot.get("category") or "").strip().lower()
    rig_target = str(slot.get("rigTarget") or "").strip().lower()
    if category == "humanoid" or "humanoid" in rig_target:
        return "humanoid"
    if category in {"tail creature", "wing creature"} or "tail" in rig_target:
        return "tail_creature"
    if category == "quadruped" or "quadruped" in rig_target:
        return "quadruped"
    if category == "prop" or "prop" in rig_target or "hinge" in rig_target:
        return "prop_hinge"
    raise ValueError(f"Cannot infer template for slot {slot.get('id')!r}")


def manifest_slot_cases(manifest_path: Path, slot_ids: list[str]) -> list[BenchmarkCase]:
    if not slot_ids:
        return []
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    slots_by_id = {
        slot.get("id"): slot
        for slot in payload.get("slots", [])
        if isinstance(slot, dict) and isinstance(slot.get("id"), str)
    }
    cases: list[BenchmarkCase] = []
    for slot_id in slot_ids:
        slot = slots_by_id.get(slot_id)
        if slot is None:
            raise ValueError(f"Manifest slot not found: {slot_id}")
        real_asset = slot.get("realAsset")
        if not isinstance(real_asset, dict):
            raise ValueError(f"Manifest slot {slot_id} does not define realAsset")
        external_path = real_asset.get("externalPath")
        if not isinstance(external_path, str) or not external_path:
            raise ValueError(f"Manifest slot {slot_id} does not define realAsset.externalPath")
        cases.append(
            BenchmarkCase(
                asset=Path(external_path),
                template=template_for_manifest_slot(slot),
                slot_id=slot_id,
            )
        )
    return cases


def vector_sub(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def vector_add(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vector_scale(
    a: tuple[float, float, float],
    scale: float,
) -> tuple[float, float, float]:
    return (a[0] * scale, a[1] * scale, a[2] * scale)


def vector_cross(
    a: tuple[float, float, float],
    b: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def vector_length(a: tuple[float, float, float]) -> float:
    return math.sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])


def vector_normalize(a: tuple[float, float, float]) -> tuple[float, float, float]:
    length = vector_length(a)
    if length <= 0:
        return (1.0, 0.0, 0.0)
    return (a[0] / length, a[1] / length, a[2] / length)


def allocate_part_counts(vertex_count: int, part_count: int) -> list[int]:
    if vertex_count < part_count * 3:
        raise ValueError(f"synthetic humanoid vertex count must be at least {part_count * 3}")
    base = [max(3, vertex_count // part_count) for _ in range(part_count)]
    remainder = vertex_count - sum(base)
    index = 0
    while remainder > 0:
        base[index % part_count] += 1
        remainder -= 1
        index += 1
    while remainder < 0:
        target = index % part_count
        if base[target] > 3:
            base[target] -= 1
            remainder += 1
        index += 1
    return base


def synthetic_humanoid_parts() -> list[dict[str, object]]:
    return [
        {
            "name": "torso",
            "start": (0.0, 0.0, -0.2),
            "end": (0.0, 0.0, 2.05),
            "rx": 0.52,
            "ry": 0.26,
        },
        {
            "name": "head",
            "start": (0.0, 0.0, 2.05),
            "end": (0.0, 0.0, 3.05),
            "rx": 0.34,
            "ry": 0.30,
        },
        {
            "name": "left_arm",
            "start": (-0.42, 0.0, 1.85),
            "end": (-2.2, 0.0, 1.2),
            "rx": 0.18,
            "ry": 0.14,
        },
        {
            "name": "right_arm",
            "start": (0.42, 0.0, 1.85),
            "end": (2.2, 0.0, 1.2),
            "rx": 0.18,
            "ry": 0.14,
        },
        {
            "name": "left_leg",
            "start": (-0.25, 0.0, -0.15),
            "end": (-0.42, -0.05, -2.35),
            "rx": 0.22,
            "ry": 0.16,
        },
        {
            "name": "right_leg",
            "start": (0.25, 0.0, -0.15),
            "end": (0.42, -0.05, -2.35),
            "rx": 0.22,
            "ry": 0.16,
        },
    ]


def synthetic_multimesh_humanoid_parts() -> list[dict[str, object]]:
    return [
        {**part, "ry": max(float(part["ry"]), 0.72)}
        for part in synthetic_humanoid_parts()
    ]


def synthetic_quadruped_parts() -> list[dict[str, object]]:
    return [
        {
            "name": "body",
            "start": (-1.55, 0.0, 0.9),
            "end": (1.3, 0.0, 1.0),
            "rx": 0.38,
            "ry": 0.26,
        },
        {
            "name": "neck_head",
            "start": (1.1, 0.0, 1.05),
            "end": (2.0, 0.0, 1.45),
            "rx": 0.22,
            "ry": 0.18,
        },
        {
            "name": "front_leg_left",
            "start": (0.85, -0.25, 0.75),
            "end": (0.95, -0.25, -0.75),
            "rx": 0.13,
            "ry": 0.10,
        },
        {
            "name": "front_leg_right",
            "start": (0.85, 0.25, 0.75),
            "end": (0.95, 0.25, -0.75),
            "rx": 0.13,
            "ry": 0.10,
        },
        {
            "name": "rear_leg_left",
            "start": (-1.0, -0.25, 0.72),
            "end": (-1.12, -0.25, -0.78),
            "rx": 0.15,
            "ry": 0.11,
        },
        {
            "name": "rear_leg_right",
            "start": (-1.0, 0.25, 0.72),
            "end": (-1.12, 0.25, -0.78),
            "rx": 0.15,
            "ry": 0.11,
        },
        {
            "name": "tail",
            "start": (-1.45, 0.0, 0.98),
            "end": (-2.55, 0.0, 1.28),
            "rx": 0.12,
            "ry": 0.09,
        },
    ]


def synthetic_tail_creature_parts() -> list[dict[str, object]]:
    return [
        {
            "name": "body",
            "start": (-0.6, 0.0, 0.75),
            "end": (1.3, 0.0, 1.05),
            "rx": 0.44,
            "ry": 0.25,
        },
        {
            "name": "neck_head",
            "start": (1.1, 0.0, 1.05),
            "end": (2.25, 0.0, 1.75),
            "rx": 0.20,
            "ry": 0.15,
        },
        {
            "name": "tail_base",
            "start": (-0.65, 0.0, 0.82),
            "end": (-2.0, 0.0, 0.78),
            "rx": 0.24,
            "ry": 0.16,
        },
        {
            "name": "tail_tip",
            "start": (-2.0, 0.0, 0.78),
            "end": (-3.35, 0.0, 0.55),
            "rx": 0.15,
            "ry": 0.10,
        },
        {
            "name": "front_leg_left",
            "start": (0.85, -0.22, 0.65),
            "end": (0.8, -0.22, -0.45),
            "rx": 0.11,
            "ry": 0.09,
        },
        {
            "name": "front_leg_right",
            "start": (0.85, 0.22, 0.65),
            "end": (0.8, 0.22, -0.45),
            "rx": 0.11,
            "ry": 0.09,
        },
        {
            "name": "rear_leg_left",
            "start": (-0.35, -0.22, 0.55),
            "end": (-0.45, -0.22, -0.45),
            "rx": 0.12,
            "ry": 0.09,
        },
        {
            "name": "rear_leg_right",
            "start": (-0.35, 0.22, 0.55),
            "end": (-0.45, 0.22, -0.45),
            "rx": 0.12,
            "ry": 0.09,
        },
    ]


def synthetic_prop_hinge_parts() -> list[dict[str, object]]:
    return [
        {
            "name": "base_panel",
            "start": (-0.95, 0.0, 0.0),
            "end": (-0.1, 0.0, 1.55),
            "rx": 0.18,
            "ry": 0.08,
        },
        {
            "name": "moving_panel",
            "start": (0.1, 0.0, 0.0),
            "end": (1.05, 0.0, 1.55),
            "rx": 0.18,
            "ry": 0.08,
        },
    ]


def synthetic_part_vertices(
    *,
    start: tuple[float, float, float],
    end: tuple[float, float, float],
    rx: float,
    ry: float,
    count: int,
) -> list[tuple[float, float, float]]:
    axis = vector_sub(end, start)
    axis_unit = vector_normalize(axis)
    reference = (0.0, 0.0, 1.0)
    if abs(axis_unit[2]) > 0.9:
        reference = (0.0, 1.0, 0.0)
    basis_x = vector_normalize(vector_cross(axis_unit, reference))
    basis_y = vector_normalize(vector_cross(axis_unit, basis_x))
    vertices: list[tuple[float, float, float]] = []
    golden_angle = math.pi * (3.0 - math.sqrt(5.0))
    for index in range(count):
        t = (index + 0.5) / count
        angle = index * golden_angle
        taper = 0.75 + 0.25 * math.sin(math.pi * t)
        center = vector_add(start, vector_scale(axis, t))
        offset = vector_add(
            vector_scale(basis_x, math.cos(angle) * rx * taper),
            vector_scale(basis_y, math.sin(angle) * ry * taper),
        )
        vertices.append(vector_add(center, offset))
    return vertices


def synthetic_faces(count: int) -> list[tuple[int, int, int]]:
    return [(index, index + 1, index + 2) for index in range(0, max(count - 2, 0))]


def write_synthetic_obj(
    path: Path,
    *,
    vertex_count: int,
    parts: list[dict[str, object]],
    spec_type: str,
    object_per_part: bool,
) -> dict[str, Any]:
    counts = allocate_part_counts(vertex_count, len(parts))
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Mac Game Rigger {spec_type} benchmark asset",
        f"# vertex_count={vertex_count}",
    ]
    if not object_per_part:
        lines.append(f"o MGR_{spec_type}")
    faces: list[tuple[int, int, int]] = []
    next_index = 1
    for part, count in zip(parts, counts):
        if object_per_part:
            lines.append(f"o MGR_{spec_type}_{part['name']}")
        part_vertices = synthetic_part_vertices(
            start=part["start"],
            end=part["end"],
            rx=part["rx"],
            ry=part["ry"],
            count=count,
        )
        for vertex in part_vertices:
            lines.append(f"v {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}")
        for local_index, local_index_b, local_index_c in synthetic_faces(count):
            faces.append(
                (
                    next_index + local_index,
                    next_index + local_index_b,
                    next_index + local_index_c,
                )
            )
        next_index += count
    lines.extend(f"f {a} {b} {c}" for a, b, c in faces)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "type": spec_type,
        "format": "obj",
        "vertexCount": vertex_count,
        "partCount": len(parts),
        "meshCount": len(parts) if object_per_part else 1,
    }


def align_buffer(buffer: bytearray, alignment: int = 4) -> None:
    while len(buffer) % alignment:
        buffer.append(0)


def append_buffer_view(buffer: bytearray, payload: bytes, buffer_views: list[dict[str, Any]]) -> int:
    align_buffer(buffer)
    offset = len(buffer)
    buffer.extend(payload)
    buffer_views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(payload)})
    return len(buffer_views) - 1


def pack_positions(vertices: list[tuple[float, float, float]]) -> bytes:
    return b"".join(struct.pack("<fff", *vertex) for vertex in vertices)


def gltf_source_vertex_from_blender_vertex(
    vertex: tuple[float, float, float],
) -> tuple[float, float, float]:
    return (vertex[0], vertex[2], -vertex[1])


def pack_indices(faces: list[tuple[int, int, int]]) -> bytes:
    return b"".join(struct.pack("<III", *face) for face in faces)


def bounds_for_vertices(vertices: list[tuple[float, float, float]]) -> tuple[list[float], list[float]]:
    return (
        [min(vertex[axis] for vertex in vertices) for axis in range(3)],
        [max(vertex[axis] for vertex in vertices) for axis in range(3)],
    )


def write_synthetic_multimesh_humanoid_gltf(path: Path, vertex_count: int) -> dict[str, Any]:
    parts = synthetic_multimesh_humanoid_parts()
    counts = allocate_part_counts(vertex_count, len(parts))
    path.parent.mkdir(parents=True, exist_ok=True)
    buffer = bytearray()
    buffer_views: list[dict[str, Any]] = []
    accessors: list[dict[str, Any]] = []
    meshes: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []

    for part, count in zip(parts, counts):
        vertices = synthetic_part_vertices(
            start=part["start"],
            end=part["end"],
            rx=part["rx"],
            ry=part["ry"],
            count=count,
        )
        faces = synthetic_faces(count)
        gltf_vertices = [gltf_source_vertex_from_blender_vertex(vertex) for vertex in vertices]
        position_view = append_buffer_view(buffer, pack_positions(gltf_vertices), buffer_views)
        min_bounds, max_bounds = bounds_for_vertices(gltf_vertices)
        position_accessor = len(accessors)
        accessors.append(
            {
                "bufferView": position_view,
                "componentType": 5126,
                "count": len(vertices),
                "type": "VEC3",
                "min": min_bounds,
                "max": max_bounds,
            }
        )
        index_view = append_buffer_view(buffer, pack_indices(faces), buffer_views)
        index_accessor = len(accessors)
        accessors.append(
            {
                "bufferView": index_view,
                "componentType": 5125,
                "count": len(faces) * 3,
                "type": "SCALAR",
                "min": [0],
                "max": [max(len(vertices) - 1, 0)],
            }
        )
        mesh_index = len(meshes)
        meshes.append(
            {
                "name": f"MGR_{part['name']}",
                "primitives": [
                    {
                        "attributes": {"POSITION": position_accessor},
                        "indices": index_accessor,
                        "mode": 4,
                    }
                ],
            }
        )
        nodes.append({"name": f"MGR_{part['name']}", "mesh": mesh_index})

    payload = {
        "asset": {"version": "2.0", "generator": "Mac Game Rigger synthetic benchmark"},
        "scene": 0,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": meshes,
        "buffers": [
            {
                "uri": "data:application/octet-stream;base64,"
                + base64.b64encode(bytes(buffer)).decode("ascii"),
                "byteLength": len(buffer),
            }
        ],
        "bufferViews": buffer_views,
        "accessors": accessors,
    }
    path.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    return {
        "type": "synthetic_multimesh_humanoid",
        "format": "gltf",
        "vertexCount": vertex_count,
        "partCount": len(parts),
        "meshCount": len(parts),
    }


def write_synthetic_humanoid_obj(path: Path, vertex_count: int) -> dict[str, Any]:
    return write_synthetic_obj(
        path,
        vertex_count=vertex_count,
        parts=synthetic_humanoid_parts(),
        spec_type="synthetic_humanoid",
        object_per_part=False,
    )


def write_synthetic_multimesh_humanoid_obj(path: Path, vertex_count: int) -> dict[str, Any]:
    return write_synthetic_multimesh_humanoid_gltf(path, vertex_count)


def write_synthetic_quadruped_obj(path: Path, vertex_count: int) -> dict[str, Any]:
    return write_synthetic_obj(
        path,
        vertex_count=vertex_count,
        parts=synthetic_quadruped_parts(),
        spec_type="synthetic_quadruped",
        object_per_part=False,
    )


def write_synthetic_tail_creature_obj(path: Path, vertex_count: int) -> dict[str, Any]:
    return write_synthetic_obj(
        path,
        vertex_count=vertex_count,
        parts=synthetic_tail_creature_parts(),
        spec_type="synthetic_tail_creature",
        object_per_part=False,
    )


def write_synthetic_prop_hinge_obj(path: Path, vertex_count: int) -> dict[str, Any]:
    return write_synthetic_obj(
        path,
        vertex_count=vertex_count,
        parts=synthetic_prop_hinge_parts(),
        spec_type="synthetic_prop_hinge",
        object_per_part=False,
    )


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


def prepare_cases(args: argparse.Namespace) -> list[BenchmarkCase]:
    cases = [BenchmarkCase(asset=asset, template=args.template) for asset in args.assets]
    if args.slots:
        if args.manifest is None:
            raise ValueError("--manifest is required when --slot is used")
        cases.extend(manifest_slot_cases(args.manifest, args.slots))
    synthetic_root = args.evidence_root.expanduser().resolve() / "_synthetic-assets"
    for vertex_count in args.synthetic_humanoid_vertices:
        if vertex_count <= 0:
            raise ValueError("synthetic humanoid vertex counts must be positive")
        asset_path = synthetic_root / f"synthetic-humanoid-{vertex_count}.obj"
        spec = write_synthetic_humanoid_obj(asset_path, vertex_count)
        cases.append(BenchmarkCase(asset=asset_path, template="humanoid", synthetic_spec=spec))
    for vertex_count in args.synthetic_multimesh_humanoid_vertices:
        if vertex_count <= 0:
            raise ValueError("synthetic multi-mesh humanoid vertex counts must be positive")
        asset_path = synthetic_root / f"synthetic-multimesh-humanoid-{vertex_count}.gltf"
        spec = write_synthetic_multimesh_humanoid_obj(asset_path, vertex_count)
        cases.append(BenchmarkCase(asset=asset_path, template="humanoid", synthetic_spec=spec))
    for vertex_count in args.synthetic_quadruped_vertices:
        if vertex_count <= 0:
            raise ValueError("synthetic quadruped vertex counts must be positive")
        asset_path = synthetic_root / f"synthetic-quadruped-{vertex_count}.obj"
        spec = write_synthetic_quadruped_obj(asset_path, vertex_count)
        cases.append(BenchmarkCase(asset=asset_path, template="quadruped", synthetic_spec=spec))
    for vertex_count in args.synthetic_tail_creature_vertices:
        if vertex_count <= 0:
            raise ValueError("synthetic tail creature vertex counts must be positive")
        asset_path = synthetic_root / f"synthetic-tail-creature-{vertex_count}.obj"
        spec = write_synthetic_tail_creature_obj(asset_path, vertex_count)
        cases.append(BenchmarkCase(asset=asset_path, template="tail_creature", synthetic_spec=spec))
    for vertex_count in args.synthetic_prop_hinge_vertices:
        if vertex_count <= 0:
            raise ValueError("synthetic prop hinge vertex counts must be positive")
        asset_path = synthetic_root / f"synthetic-prop-hinge-{vertex_count}.obj"
        spec = write_synthetic_prop_hinge_obj(asset_path, vertex_count)
        cases.append(BenchmarkCase(asset=asset_path, template="prop_hinge", synthetic_spec=spec))
    return cases


def run_case(index: int, benchmark_case: BenchmarkCase, args: argparse.Namespace) -> dict[str, Any]:
    asset_path = benchmark_case.asset.expanduser().resolve()
    evidence_dir = args.evidence_root.expanduser().resolve() / case_slug(
        index, asset_path, benchmark_case.template
    )
    summary_path = evidence_dir / "workflow-summary.json"
    command = command_for_case(
        blender=args.blender,
        asset_path=asset_path,
        evidence_dir=evidence_dir,
        summary_path=summary_path,
        template=benchmark_case.template,
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
        "template": benchmark_case.template,
        "slotId": benchmark_case.slot_id,
        "syntheticSpec": benchmark_case.synthetic_spec,
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


def build_report(args: argparse.Namespace, cases_to_run: list[BenchmarkCase]) -> dict[str, Any]:
    cases = [
        run_case(index, benchmark_case, args)
        for index, benchmark_case in enumerate(cases_to_run, start=1)
    ]
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
    try:
        cases_to_run = prepare_cases(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not cases_to_run:
        print(
            "Pass at least one --asset or --synthetic-humanoid-vertices value",
            file=sys.stderr,
        )
        return 2
    missing_assets = [
        str(benchmark_case.asset)
        for benchmark_case in cases_to_run
        if not benchmark_case.asset.expanduser().exists()
    ]
    if missing_assets:
        print("Missing asset(s): " + ", ".join(missing_assets), file=sys.stderr)
        return 2
    report = build_report(args, cases_to_run)
    payload = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
