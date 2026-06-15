from __future__ import annotations

from dataclasses import dataclass


DEFAULT_INFLUENCE_LIMIT = 4
DEFAULT_PRUNE_THRESHOLD = 0.001
NORMALIZE_TOLERANCE = 0.000001


@dataclass(frozen=True)
class WeightCleanupResult:
    mesh_name: str
    unweighted_vertices: int
    over_limit_vertices: int
    removed_empty_groups: int
    pruned_weights: int
    normalized_vertices: int


def find_unweighted_vertices(mesh) -> list[int]:
    return [
        vertex.index
        for vertex in mesh.data.vertices
        if _vertex_positive_weight_total(vertex) <= 0.0
    ]


def find_vertices_over_influence_limit(
    mesh,
    limit: int = DEFAULT_INFLUENCE_LIMIT,
) -> list[int]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    return [
        vertex.index
        for vertex in mesh.data.vertices
        if _positive_influence_count(vertex) > limit
    ]


def remove_empty_vertex_groups(mesh) -> int:
    empty_group_names = [
        vertex_group.name
        for vertex_group in mesh.vertex_groups
        if not _vertex_group_has_positive_weights(mesh, vertex_group.index)
    ]
    for group_name in empty_group_names:
        vertex_group = mesh.vertex_groups.get(group_name)
        if vertex_group is not None:
            mesh.vertex_groups.remove(vertex_group)
    return len(empty_group_names)


def prune_small_weights(
    mesh,
    threshold: float = DEFAULT_PRUNE_THRESHOLD,
) -> int:
    if threshold < 0.0:
        raise ValueError("threshold must be non-negative")

    removals = [
        (vertex.index, group.group)
        for vertex in mesh.data.vertices
        for group in vertex.groups
        if 0.0 < group.weight < threshold
    ]
    for vertex_index, group_index in removals:
        mesh.vertex_groups[group_index].remove([vertex_index])
    return len(removals)


def normalize_mesh_weights(mesh) -> int:
    changed_vertices = 0
    for vertex in mesh.data.vertices:
        positive_groups = [
            group
            for group in vertex.groups
            if group.weight > 0.0
        ]
        total = sum(group.weight for group in positive_groups)
        if total <= 0.0 or abs(total - 1.0) <= NORMALIZE_TOLERANCE:
            continue

        for group in positive_groups:
            mesh.vertex_groups[group.group].add(
                [vertex.index],
                group.weight / total,
                "REPLACE",
            )
        changed_vertices += 1
    return changed_vertices


def cleanup_mesh_weights(
    mesh,
    influence_limit: int = DEFAULT_INFLUENCE_LIMIT,
    prune_threshold: float = DEFAULT_PRUNE_THRESHOLD,
) -> WeightCleanupResult:
    unweighted_vertices = len(find_unweighted_vertices(mesh))
    over_limit_vertices = len(find_vertices_over_influence_limit(mesh, influence_limit))
    removed_empty_groups = remove_empty_vertex_groups(mesh)
    pruned_weights = prune_small_weights(mesh, prune_threshold)
    normalized_vertices = normalize_mesh_weights(mesh)

    return WeightCleanupResult(
        mesh_name=mesh.name,
        unweighted_vertices=unweighted_vertices,
        over_limit_vertices=over_limit_vertices,
        removed_empty_groups=removed_empty_groups,
        pruned_weights=pruned_weights,
        normalized_vertices=normalized_vertices,
    )


def _vertex_positive_weight_total(vertex) -> float:
    return sum(group.weight for group in vertex.groups if group.weight > 0.0)


def _positive_influence_count(vertex) -> int:
    return sum(1 for group in vertex.groups if group.weight > 0.0)


def _vertex_group_has_positive_weights(mesh, vertex_group_index: int) -> bool:
    return any(
        group.group == vertex_group_index and group.weight > 0.0
        for vertex in mesh.data.vertices
        for group in vertex.groups
    )
