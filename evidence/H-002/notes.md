# H-002 Split-Mesh Humanoid Review Packet

## Source

- Source name: KayKit Adventurers
- Source URL: https://kaylousberg.itch.io/kaykit-adventurers
- License: CC0
- Source mesh count: 8
- Suggested category: humanoid

## Workflow

- Rig workflow mesh count: 8
- QA status: pass
- Pose deformation status: pass

## Manual Review

- Manual review status: pass
- Deformation score: 3
- Visual review notes: Exportable split-mesh structure is preserved through source import, rig workflow, and Unity FBX export. Neutral and stress-pose silhouettes remain coherent with no catastrophic mesh explosion or detached body parts.
- Cleanup limitations: Evidence is accepted as a first production split-mesh humanoid pass, not as final animator-quality output. The GLTF importer creates a 42-vertex `Icosphere` helper mesh in `glTF_not_exported`; the workflow now prunes that non-exportable helper before source counts, rigging, QA, and FBX export. Exportable QA/export report 8 meshes, 7734 vertices, 0 unweighted vertices, and 0 over-limit vertices. Unity configured Animator smoke now passes with 8 skinned mesh renderers, a controller-backed Animator, one generated state, and positive sampled Hips rotation. Previews are still silhouette-only without material/textured inspection.

Registered conservatively with deformation score 3; use this asset to drive textured visual QA and cleanup scoring next rather than treating the current binder as finished.
