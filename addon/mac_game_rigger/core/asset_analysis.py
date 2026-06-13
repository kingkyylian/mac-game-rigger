from dataclasses import dataclass


@dataclass(frozen=True)
class MeshStats:
    mesh_count: int
    vertex_count: int
    face_count: int
    width: float
    depth: float
    height: float
    has_armature: bool


def suggest_category(stats: MeshStats) -> str:
    if stats.height <= 0:
        return "unknown"

    height_to_width = stats.height / max(stats.width, 0.001)
    if height_to_width > 1.6:
        return "humanoid"
    if stats.depth > stats.height * 1.2:
        return "quadruped"
    return "unknown"
