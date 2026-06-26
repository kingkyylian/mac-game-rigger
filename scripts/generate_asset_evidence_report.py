#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from validate_asset_evidence import DEFAULT_MANIFEST, load_manifest, validate_manifest


REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIGURED_ANIMATOR_GATE_ISSUE_MARKERS = (
    "configuredAnimatorSmoke is required",
    "configuredAnimatorSmoke.passed",
    "configured animatorCount",
    "configured Animator",
)
CONFIGURED_ANIMATOR_MISSING_WARNING = "configuredAnimatorSmoke is not recorded yet"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Markdown production-trial evidence progress report."
    )
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Manifest JSON path.")
    parser.add_argument(
        "--evidence-root",
        default=str(REPO_ROOT),
        help="Root used to resolve relative evidence file paths.",
    )
    parser.add_argument(
        "--check-evidence-files",
        action="store_true",
        help="Include local evidence file existence checks.",
    )
    parser.add_argument("--output", help="Write Markdown report to this path.")
    return parser.parse_args()


def checkbox(value: bool) -> str:
    return "pass" if value else "missing"


def table_cell(value: object) -> str:
    text = "" if value is None else str(value)
    return text.replace("\n", " ").replace("|", "\\|")


def load_pose_deformation_by_slot(evidence_root: Path, slots: list[dict]) -> dict[str, str]:
    pose_by_slot: dict[str, str] = {}
    for slot in slots:
        slot_id = slot["id"]
        summary_path = evidence_root / "evidence" / slot_id / "workflow-summary.json"
        if not summary_path.exists():
            pose_by_slot[slot_id] = ""
            continue
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pose_by_slot[slot_id] = "invalid"
            continue
        pose_by_slot[slot_id] = pose_deformation_cell(summary.get("poseDeformation"))
    return pose_by_slot


def load_weight_diagnostics_by_slot(evidence_root: Path, slots: list[dict]) -> dict[str, str]:
    weight_by_slot: dict[str, str] = {}
    for slot in slots:
        slot_id = slot["id"]
        summary_path = evidence_root / "evidence" / slot_id / "workflow-summary.json"
        if not summary_path.exists():
            weight_by_slot[slot_id] = ""
            continue
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            weight_by_slot[slot_id] = "invalid"
            continue
        weight_by_slot[slot_id] = weight_diagnostics_cell(
            summary.get("weightDiagnostics"),
            prop_diagnostics=summary.get("propDiagnostics"),
            humanoid_diagnostics=summary.get("humanoidDiagnostics"),
        )
    return weight_by_slot


def load_mesh_count_by_slot(evidence_root: Path, slots: list[dict]) -> dict[str, int | str]:
    mesh_count_by_slot: dict[str, int | str] = {}
    for slot in slots:
        slot_id = slot["id"]
        summary_path = evidence_root / "evidence" / slot_id / "workflow-summary.json"
        if not summary_path.exists():
            mesh_count_by_slot[slot_id] = ""
            continue
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            mesh_count_by_slot[slot_id] = "invalid"
            continue
        mesh_count = summary.get("meshCount")
        qa = summary.get("qa")
        if not isinstance(mesh_count, int) and isinstance(qa, dict):
            mesh_count = qa.get("mesh_count")
        mesh_count_by_slot[slot_id] = mesh_count if isinstance(mesh_count, int) else ""
    return mesh_count_by_slot


def pose_deformation_cell(pose_deformation: object) -> str:
    if not isinstance(pose_deformation, dict):
        return ""
    status = pose_deformation.get("status")
    if not status:
        return ""
    max_ratio = pose_deformation.get("maxAxisExpansionRatio")
    expanded_axes = pose_deformation.get("expandedAxes")
    warning_axes = pose_deformation.get("warningAxes")
    allowed_axes = pose_deformation.get("allowedExpandedAxes")
    axes = expanded_axes if expanded_axes else warning_axes
    parts = [str(status)]
    if isinstance(max_ratio, (int, float)):
        parts.append(f"{max_ratio:g}x")
    if isinstance(axes, list) and axes:
        parts.append(",".join(str(axis) for axis in axes))
    if isinstance(allowed_axes, list) and allowed_axes:
        parts.append(f"allowed:{','.join(str(axis) for axis in allowed_axes)}")
    return " ".join(parts)


def _dominant_vertices(regions: dict[str, object], region_name: str) -> int:
    region = regions.get(region_name)
    if not isinstance(region, dict):
        return 0
    value = region.get("dominantVertices")
    return value if isinstance(value, int) else 0


def weight_diagnostics_cell(
    weight_diagnostics: object,
    *,
    prop_diagnostics: object = None,
    humanoid_diagnostics: object = None,
) -> str:
    if not isinstance(weight_diagnostics, dict):
        return ""
    regions = weight_diagnostics.get("regions")
    if not isinstance(regions, dict):
        return ""
    core = _dominant_vertices(regions, "core")
    neck = _dominant_vertices(regions, "neckHead")
    arm = (
        _dominant_vertices(regions, "upperArm")
        + _dominant_vertices(regions, "lowerArm")
        + _dominant_vertices(regions, "hand")
    )
    leg = _dominant_vertices(regions, "upperLeg") + _dominant_vertices(regions, "lowerLeg")
    foot = _dominant_vertices(regions, "foot")
    prop_base = _dominant_vertices(regions, "propBase")
    prop_hinge = _dominant_vertices(regions, "propHinge")
    prop_moving = _dominant_vertices(regions, "propMovingPart")
    parts = []
    if core:
        parts.append(f"core {core}")
    if neck:
        parts.append(f"neck {neck}")
    if arm:
        parts.append(f"arm {arm}")
    if leg:
        parts.append(f"leg {leg}")
    if foot:
        parts.append(f"foot {foot}")
    if prop_base:
        parts.append(f"prop base {prop_base}")
    if prop_hinge:
        parts.append(f"hinge {prop_hinge}")
    if prop_moving:
        parts.append(f"moving {prop_moving}")
    prop_cell = prop_diagnostics_cell(prop_diagnostics)
    if prop_cell:
        parts.append(prop_cell)
    humanoid_cell = humanoid_diagnostics_cell(humanoid_diagnostics)
    if humanoid_cell:
        parts.append(humanoid_cell)
    return " ".join(parts)


def prop_diagnostics_cell(prop_diagnostics: object) -> str:
    if not isinstance(prop_diagnostics, dict):
        return ""
    status = prop_diagnostics.get("status")
    if not status:
        return ""
    parts = [f"prop qa {status}"]
    warnings = prop_diagnostics.get("warnings")
    if isinstance(warnings, list) and warnings:
        parts.append(",".join(str(warning) for warning in warnings))
    return " ".join(parts)


def humanoid_diagnostics_cell(humanoid_diagnostics: object) -> str:
    if not isinstance(humanoid_diagnostics, dict):
        return ""
    status = humanoid_diagnostics.get("status")
    if not status:
        return ""
    parts = [f"humanoid qa {status}"]
    warnings = humanoid_diagnostics.get("warnings")
    if isinstance(warnings, list) and warnings:
        parts.append(",".join(str(warning) for warning in warnings))
    return " ".join(parts)


def _preview_bounds_width(diagnostics: dict[str, object], key: str) -> int | None:
    stats = diagnostics.get(key)
    if not isinstance(stats, dict):
        return None
    bounds = stats.get("foregroundBounds")
    if not isinstance(bounds, dict):
        return None
    width = bounds.get("width")
    return width if isinstance(width, int) and width > 0 else None


def _preview_center_shift_ratio(diagnostics: dict[str, object], key: str) -> float | None:
    stats = diagnostics.get(key)
    if not isinstance(stats, dict):
        return None
    ratio = stats.get("verticalCenterShiftRatio")
    return ratio if isinstance(ratio, (int, float)) else None


def preview_diagnostics_cell(slot: dict[str, object]) -> str:
    diagnostics = slot.get("previewDiagnostics")
    if not isinstance(diagnostics, dict):
        return ""

    neutral_side_width = _preview_bounds_width(diagnostics, "previewNeutralSide")
    pose_side_width = _preview_bounds_width(diagnostics, "previewPoseSide")
    if neutral_side_width and pose_side_width:
        parts = [
            f"side {neutral_side_width}->{pose_side_width}px {pose_side_width / neutral_side_width:.2f}x"
        ]
        pose_side_shift = _preview_center_shift_ratio(diagnostics, "previewPoseSide")
        if pose_side_shift is not None:
            parts.append(f"lean {pose_side_shift:.2f}")
        return " ".join(parts)

    neutral = diagnostics.get("previewNeutral")
    if not isinstance(neutral, dict):
        return ""
    foreground_ratio = neutral.get("foregroundPixelRatio")
    fill_ratio = neutral.get("foregroundFillRatio")
    if not isinstance(foreground_ratio, (int, float)) or not isinstance(fill_ratio, (int, float)):
        return ""
    return f"fg {foreground_ratio * 100:.1f}% fill {fill_ratio * 100:.1f}%"


def configured_animator_strict_gate(report: dict[str, object]) -> dict[str, object]:
    missing_slots: list[str] = []
    for slot in report["slots"]:
        slot_id = str(slot["id"])
        issues = slot.get("issues")
        if isinstance(issues, list) and any(
            any(marker in str(issue) for marker in CONFIGURED_ANIMATOR_GATE_ISSUE_MARKERS)
            for issue in issues
        ):
            missing_slots.append(slot_id)
            continue
        warnings = slot.get("warnings")
        if not isinstance(warnings, list):
            continue
        if any(CONFIGURED_ANIMATOR_MISSING_WARNING in str(warning) for warning in warnings):
            missing_slots.append(slot_id)
    return {
        "status": "pass" if not missing_slots else "blocked",
        "missingSlots": missing_slots,
    }


def real_separate_mesh_humanoid_gate(report: dict[str, object]) -> dict[str, object]:
    mesh_count_by_slot = report.get("meshCountBySlot")
    if not isinstance(mesh_count_by_slot, dict):
        mesh_count_by_slot = {}
    candidate_slots: list[str] = []
    for slot in report["slots"]:
        if slot.get("category") != "humanoid":
            continue
        if not slot.get("hasRealAsset") or not slot.get("evidenceComplete"):
            continue
        score = slot.get("deformationScore")
        if not isinstance(score, int) or score < 3:
            continue
        slot_id = str(slot["id"])
        mesh_count = mesh_count_by_slot.get(slot_id)
        if isinstance(mesh_count, int) and mesh_count > 1:
            return {"status": "pass", "missingSlots": []}
        candidate_slots.append(slot_id)
    return {
        "status": "blocked",
        "missingSlots": candidate_slots or ["no complete score >= 3 humanoid evidence"],
    }


def render_report(report: dict[str, object]) -> str:
    gate = report["productionTrialGate"]
    requirements = gate["requirements"]
    category_counts = gate["categoryCounts"]
    lines: list[str] = [
        "# Asset Evidence Progress Report",
        "",
        f"Schema status: **{report['schemaStatus']}**",
        f"Production trial gate: **{gate['status']}**",
        f"Evidence file check: **{report['evidenceFileCheck']}**",
        f"Evidence root: `{report['evidenceRoot']}`",
        "",
        "## Summary",
        "",
        f"- Slots: {report['slotCount']}",
        f"- Real assets registered: {report['realAssetCount']}",
        f"- Complete evidence entries: {report['completeEvidenceCount']}",
        f"- Score >= 3 count: {gate['score3PlusCount']}",
        f"- Score >= 3 ratio: {gate['score3PlusRatio']}",
        "",
        "## Production Trial Requirements",
        "",
        "| Requirement | Status |",
        "|---|---|",
    ]

    for name, passed in requirements.items():
        lines.append(f"| `{table_cell(name)}` | {checkbox(bool(passed))} |")

    missing = gate["missing"]
    if missing:
        lines.extend(["", "## Missing Gate Items", ""])
        lines.extend(f"- `{item}`" for item in missing)

    strict_configured_animator_gate = report.get("strictConfiguredAnimatorGate")
    if not isinstance(strict_configured_animator_gate, dict):
        strict_configured_animator_gate = configured_animator_strict_gate(report)
    real_separate_mesh_gate = report.get("realSeparateMeshHumanoidGate")
    if not isinstance(real_separate_mesh_gate, dict):
        real_separate_mesh_gate = real_separate_mesh_humanoid_gate(report)
    lines.extend(
        [
            "",
            "## Strict Quality Gates",
            "",
            "| Gate | Status | Missing Slots |",
            "|---|---|---|",
            (
                "| `configuredAnimatorSmokeForHumanoidScore3` | "
                f"{strict_configured_animator_gate['status']} | "
                f"{table_cell(', '.join(strict_configured_animator_gate['missingSlots']))} |"
            ),
            (
                "| `realSeparateMeshHumanoidEvidence` | "
                f"{real_separate_mesh_gate['status']} | "
                f"{table_cell(', '.join(real_separate_mesh_gate['missingSlots']))} |"
            ),
        ]
    )

    lines.extend(
        [
            "",
            "## Category Counts",
            "",
            "| Category | Complete Evidence Count |",
            "|---|---:|",
        ]
    )
    for category in ("humanoid", "quadruped", "tail creature", "wing creature", "prop"):
        lines.append(f"| {category} | {category_counts.get(category, 0)} |")

    lines.extend(
        [
            "",
            "## Slot Status",
            "",
            "| Slot | Category | Real Asset | Evidence | Score | Meshes | Pose QA | Visual | Unity | Unreal | Preview | Weight | Warnings | Issues |",
            "|---|---|---|---|---:|---:|---|---|---|---|---|---|---|---|",
        ]
    )
    pose_deformation_by_slot = report.get("poseDeformationBySlot", {})
    weight_diagnostics_by_slot = report.get("weightDiagnosticsBySlot", {})
    mesh_count_by_slot = report.get("meshCountBySlot", {})
    if not isinstance(mesh_count_by_slot, dict):
        mesh_count_by_slot = {}
    for slot in report["slots"]:
        issues = "; ".join(slot["issues"]) if slot["issues"] else ""
        warnings = "; ".join(slot.get("warnings", [])) if slot.get("warnings") else ""
        lines.append(
            "| "
            f"{table_cell(slot['id'])} | "
            f"{table_cell(slot['category'])} | "
            f"{checkbox(bool(slot['hasRealAsset']))} | "
            f"{checkbox(bool(slot['evidenceComplete']))} | "
            f"{table_cell(slot['deformationScore'])} | "
            f"{table_cell(mesh_count_by_slot.get(slot['id'], ''))} | "
            f"{table_cell(pose_deformation_by_slot.get(slot['id'], ''))} | "
            f"{table_cell(slot['visualReviewStatus'])} | "
            f"{table_cell(slot['unityImportStatus'])} | "
            f"{table_cell(slot['unrealImportStatus'])} | "
            f"{table_cell(preview_diagnostics_cell(slot))} | "
            f"{table_cell(weight_diagnostics_by_slot.get(slot['id'], ''))} | "
            f"{table_cell(warnings)} | "
            f"{table_cell(issues)} |"
        )

    structural_issues = report["structuralIssues"]
    if structural_issues:
        lines.extend(["", "## Structural Issues", ""])
        lines.extend(f"- {issue}" for issue in structural_issues)

    incomplete = report["incompleteRealAssets"]
    if incomplete:
        lines.extend(["", "## Incomplete Real Assets", ""])
        for slot in incomplete:
            lines.append(f"### {slot['id']}")
            lines.extend(f"- {issue}" for issue in slot["issues"])
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    args = parse_args()
    try:
        manifest = load_manifest(Path(args.manifest))
        evidence_root = Path(args.evidence_root)
        report = validate_manifest(
            manifest,
            evidence_root=evidence_root,
            check_files=args.check_evidence_files,
        )
        strict_report = validate_manifest(
            manifest,
            evidence_root=evidence_root,
            check_files=args.check_evidence_files,
            require_configured_animator_smoke=True,
        )
        report["strictConfiguredAnimatorGate"] = configured_animator_strict_gate(strict_report)
        report["poseDeformationBySlot"] = load_pose_deformation_by_slot(
            evidence_root,
            report["slots"],
        )
        report["weightDiagnosticsBySlot"] = load_weight_diagnostics_by_slot(
            evidence_root,
            report["slots"],
        )
        report["meshCountBySlot"] = load_mesh_count_by_slot(
            evidence_root,
            report["slots"],
        )
        report["realSeparateMeshHumanoidGate"] = real_separate_mesh_humanoid_gate(report)
    except Exception as exc:
        print(f"Failed to generate report: {exc}", file=sys.stderr)
        return 1

    markdown = render_report(report)
    if args.output:
        Path(args.output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")
    return 0 if report["schemaStatus"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
