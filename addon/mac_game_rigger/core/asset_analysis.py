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

    if _looks_like_unrigged_prop(stats):
        return "prop"

    if stats.depth > stats.height * 1.2:
        return "quadruped"

    thin_axis = stats.depth / max(min(stats.width, stats.height), 0.001)
    if thin_axis < 0.16 and stats.vertex_count < 5000:
        return "prop"

    height_to_width = stats.height / max(stats.width, 0.001)
    if height_to_width > 1.6:
        return "humanoid"
    return "unknown"


def _looks_like_unrigged_prop(stats: MeshStats) -> bool:
    if stats.has_armature or stats.vertex_count >= 5000:
        return False

    max_horizontal = max(stats.width, stats.depth, 0.001)
    min_horizontal = max(min(stats.width, stats.depth), 0.001)
    height_to_horizontal = stats.height / max_horizontal
    horizontal_ratio = max_horizontal / min_horizontal

    is_chunky_box_prop = height_to_horizontal <= 0.85 and horizontal_ratio <= 1.5
    is_low_long_prop = height_to_horizontal <= 0.38 and horizontal_ratio <= 3.0
    return is_chunky_box_prop or is_low_long_prop
