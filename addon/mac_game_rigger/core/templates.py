from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BoneSpec:
    name: str
    parent: str | None
    head_landmark: str
    tail_landmark: str


@dataclass(frozen=True)
class RigTemplate:
    name: str
    category: str
    required_landmarks: tuple[str, ...]
    bones: tuple[BoneSpec, ...]
    mirror_pairs: dict[str, str]


def load_template(path: str | Path) -> RigTemplate:
    template_path = Path(path)
    data = json.loads(template_path.read_text(encoding="utf-8"))
    return RigTemplate(
        name=_required_str(data, "name"),
        category=_required_str(data, "category"),
        required_landmarks=tuple(_required_list(data, "required_landmarks")),
        bones=tuple(_load_bone(item) for item in _required_list(data, "bones")),
        mirror_pairs=dict(data.get("mirror_pairs", {})),
    )


def _load_bone(data: dict[str, Any]) -> BoneSpec:
    return BoneSpec(
        name=_required_str(data, "name"),
        parent=data.get("parent"),
        head_landmark=_required_str(data, "head_landmark"),
        tail_landmark=_required_str(data, "tail_landmark"),
    )


def _required_str(data: dict[str, Any], key: str) -> str:
    value = data[key]
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string")
    return value


def _required_list(data: dict[str, Any], key: str) -> list[Any]:
    value = data[key]
    if not isinstance(value, list):
        raise TypeError(f"{key} must be a list")
    return value
