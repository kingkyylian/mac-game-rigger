from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


PROFILE_DIR = Path(__file__).resolve().parents[1] / "export_profiles"


@dataclass(frozen=True)
class ExportProfile:
    name: str
    slug: str
    forward_axis: str
    up_axis: str
    add_leaf_bones: bool
    apply_unit_scale: bool
    use_selection: bool
    global_scale: float


def load_export_profile(path: Path) -> ExportProfile:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return ExportProfile(
        name=payload["name"],
        slug=payload["slug"],
        forward_axis=payload["forward_axis"],
        up_axis=payload["up_axis"],
        add_leaf_bones=bool(payload["add_leaf_bones"]),
        apply_unit_scale=bool(payload["apply_unit_scale"]),
        use_selection=bool(payload["use_selection"]),
        global_scale=float(payload["global_scale"]),
    )


def load_builtin_export_profile(slug: str) -> ExportProfile:
    return load_export_profile(PROFILE_DIR / f"{slug}.json")
