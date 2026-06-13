from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Landmark:
    name: str
    position: tuple[float, float, float]


def mirror_landmark(landmark: Landmark) -> Landmark:
    x, y, z = landmark.position
    return Landmark(
        name=_mirror_name(landmark.name),
        position=(-x, y, z),
    )


def missing_landmarks(required_names: Iterable[str], placed_landmarks: Iterable[Landmark]) -> tuple[str, ...]:
    placed_names = {landmark.name for landmark in placed_landmarks}
    return tuple(name for name in required_names if name not in placed_names)


def _mirror_name(name: str) -> str:
    if name.endswith(".L"):
        return f"{name[:-2]}.R"
    if name.endswith(".R"):
        return f"{name[:-2]}.L"
    return name
