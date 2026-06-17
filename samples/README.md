# Benchmark Sample Asset Slots

This folder will hold representative local test assets for Mac Game Rigger Alpha.

The alpha benchmark intentionally starts with **asset slots**, not bundled assets. Each slot describes the kind of model the tool must be tested against. Real files can be added later from team-owned assets, generated test meshes, or licensed sample packs.

## Slot Rules

- Every slot must have a stable ID.
- Every slot must declare a category.
- Every real asset added later should keep the slot ID in its filename.
- Assets should be committed only if licensing permits repository storage.
- Large binary assets can be stored outside git and referenced from this file.

## Required Slot Counts

| Category | Required Count | Current Count |
|---|---:|---:|
| humanoid | 10 | 10 |
| quadruped | 5 | 5 |
| tail/wing creature | 5 | 5 |
| prop | 5 | 5 |
| **Total** | **25** | **25** |

## Humanoid Slots

| Slot ID | Category | Target Filename | Preferred Format | Rig Target | Notes |
|---|---|---|---|---|---|
| H-001 | humanoid | `H-001-humanoid-clean-neutral.glb` | GLB | Humanoid template | Clean neutral biped with normal proportions. |
| H-002 | humanoid | `H-002-humanoid-stylized-chibi.glb` | GLB | Humanoid template | Large head and short limbs stress template scaling. |
| H-003 | humanoid | `H-003-humanoid-armored.fbx` | FBX | Humanoid template | Rigid armor pieces should reveal binding bleed. |
| H-004 | humanoid | `H-004-humanoid-long-coat.glb` | GLB | Humanoid template | Coat is expected to need manual cleanup. |
| H-005 | humanoid | `H-005-humanoid-separate-hair.glb` | GLB | Humanoid template | Separate hair mesh tests multi-mesh handling. |
| H-006 | humanoid | `H-006-humanoid-lowpoly.glb` | GLB | Humanoid template | Low-poly deformation quality check. |
| H-007 | humanoid | `H-007-humanoid-generated.obj` | OBJ | Humanoid template | Generated topology stress case. |
| H-008 | humanoid | `H-008-humanoid-vrm-avatar.vrm` | VRM | Humanoid template | VRM import/export compatibility check. |
| H-009 | humanoid | `H-009-humanoid-wide-shoulders.glb` | GLB | Humanoid template | Shoulder deformation stress case. |
| H-010 | humanoid | `H-010-humanoid-thin-limbs.glb` | GLB | Humanoid template | Thin limbs test capsule weighting stability. |

## Quadruped Slots

| Slot ID | Category | Target Filename | Preferred Format | Rig Target | Notes |
|---|---|---|---|---|---|
| Q-001 | quadruped | `Q-001-quadruped-dog.glb` | GLB | Quadruped template | Baseline four-legged mammal. |
| Q-002 | quadruped | `Q-002-quadruped-cat.glb` | GLB | Quadruped template | Smaller body and tail base. |
| Q-003 | quadruped | `Q-003-quadruped-horse.fbx` | FBX | Quadruped template | Long legs and clear hoof targets. |
| Q-004 | quadruped | `Q-004-quadruped-lizard.glb` | GLB | Quadruped + tail helper | Low body and long tail. |
| Q-005 | quadruped | `Q-005-quadruped-generated-creature.obj` | OBJ | Quadruped template | Generated creature stress case. |

## Tail and Wing Creature Slots

| Slot ID | Category | Target Filename | Preferred Format | Rig Target | Notes |
|---|---|---|---|---|---|
| C-001 | tail creature | `C-001-tail-creature-dragon.glb` | GLB | Quadruped + tail + wing helpers | Dragon-like model with tail and wings. |
| C-002 | wing creature | `C-002-wing-creature-bird.glb` | GLB | Wing helper | Wing deformation and mirror test. |
| C-003 | tail creature | `C-003-tail-character-biped.glb` | GLB | Humanoid + tail helper | Biped character with tail. |
| C-004 | wing creature | `C-004-wing-character-humanoid.fbx` | FBX | Humanoid + wing helper | Humanoid body with wings. |
| C-005 | tail creature | `C-005-tail-creature-serpent.glb` | GLB | Tail chain helper | Long continuous body/tail stress case. |

## Prop Slots

| Slot ID | Category | Target Filename | Preferred Format | Rig Target | Notes |
|---|---|---|---|---|---|
| P-001 | prop | `P-001-prop-door-hinge.glb` | GLB | Prop hinge template | Single hinge rotation check. |
| P-002 | prop | `P-002-prop-treasure-chest.fbx` | FBX | Prop hinge template | Lid hinge and base separation. |
| P-003 | prop | `P-003-prop-robot-arm.glb` | GLB | Prop hinge template | Multi-segment mechanical articulation. |
| P-004 | prop | `P-004-prop-turret.glb` | GLB | Prop hinge template | Yaw and pitch hierarchy check. |
| P-005 | prop | `P-005-prop-crane-claw.glb` | GLB | Prop hinge template | Multiple child hinges. |

## Adding Real Assets

Use `samples/asset-source-candidates.json` and
`docs/production-trial-asset-source-plan.md` to pick the first public candidate
pack for a slot. Candidate source selection is not the same as real evidence:
do not fill `realAsset` in `samples/manifest.json` until the exact binary path
or storage reference is known.

When a real asset is added, update the matching row with:

- actual filename
- source/license
- polygon/vertex estimate
- whether it has an existing armature
- any expected failure areas

Example:

```text
H-001-humanoid-clean-neutral.glb
```

Do not overwrite the slot ID when changing filenames. The slot ID is the stable benchmark identity.
