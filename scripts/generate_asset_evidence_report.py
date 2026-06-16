#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from validate_asset_evidence import DEFAULT_MANIFEST, load_manifest, validate_manifest


REPO_ROOT = Path(__file__).resolve().parents[1]


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
            "| Slot | Category | Real Asset | Evidence | Score | Unity | Unreal | Issues |",
            "|---|---|---|---|---:|---|---|---|",
        ]
    )
    for slot in report["slots"]:
        issues = "; ".join(slot["issues"]) if slot["issues"] else ""
        lines.append(
            "| "
            f"{table_cell(slot['id'])} | "
            f"{table_cell(slot['category'])} | "
            f"{checkbox(bool(slot['hasRealAsset']))} | "
            f"{checkbox(bool(slot['evidenceComplete']))} | "
            f"{table_cell(slot['deformationScore'])} | "
            f"{table_cell(slot['unityImportStatus'])} | "
            f"{table_cell(slot['unrealImportStatus'])} | "
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
        report = validate_manifest(
            load_manifest(Path(args.manifest)),
            evidence_root=Path(args.evidence_root),
            check_files=args.check_evidence_files,
        )
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
