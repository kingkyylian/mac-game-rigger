# Benchmark Scorecard

This scorecard tracks whether Mac Game Rigger Alpha is saving real production time. Every row must include a category so results can be grouped by asset type.

## Scoring Scale

| Score | Meaning |
|---:|---|
| 5 | Production-ready or nearly production-ready; cleanup under 5 minutes. |
| 4 | Usable with minor cleanup under 20 minutes. |
| 3 | Usable after moderate cleanup under 45 minutes. |
| 2 | Output exists but needs major repair. |
| 1 | Failed, unusable, or cannot import into target engine. |

## Required Alpha Gate

Alpha should not be called usable until:

- 5 sample slots have smoke test notes.
- At least 1 exported asset has been imported into Unity or Unreal.
- Every tested row records cleanup minutes and export pass/fail.

## Benchmark Rows

| Slot ID | Category | Asset Filename | Template | Time To First Rig | Cleanup Minutes | Deformation Score | FBX Export | Engine Import | Accepted | Notes |
|---|---|---|---|---:|---:|---:|---|---|---|---|
| H-001 | humanoid | `H-001-humanoid-clean-neutral.glb` | Humanoid |  |  |  |  |  |  | Clean neutral biped baseline. |
| H-002 | humanoid | `H-002-humanoid-stylized-chibi.glb` | Humanoid |  |  |  |  |  |  | Large head and short limbs. |
| H-003 | humanoid | `H-003-humanoid-armored.fbx` | Humanoid |  |  |  |  |  |  | Armor binding bleed check. |
| H-004 | humanoid | `H-004-humanoid-long-coat.glb` | Humanoid |  |  |  |  |  |  | Coat deformation risk. |
| H-005 | humanoid | `H-005-humanoid-separate-hair.glb` | Humanoid |  |  |  |  |  |  | Multi-mesh handling. |
| H-006 | humanoid | `H-006-humanoid-lowpoly.glb` | Humanoid |  |  |  |  |  |  | Low-poly deformation quality. |
| H-007 | humanoid | `H-007-humanoid-generated.obj` | Humanoid |  |  |  |  |  |  | Generated topology stress. |
| H-008 | humanoid | `H-008-humanoid-vrm-avatar.vrm` | Humanoid |  |  |  |  |  |  | VRM compatibility. |
| H-009 | humanoid | `H-009-humanoid-wide-shoulders.glb` | Humanoid |  |  |  |  |  |  | Shoulder deformation stress. |
| H-010 | humanoid | `H-010-humanoid-thin-limbs.glb` | Humanoid |  |  |  |  |  |  | Capsule weighting stability. |
| Q-001 | quadruped | `Q-001-quadruped-dog.glb` | Quadruped |  |  |  |  |  |  | Four-legged mammal baseline. |
| Q-002 | quadruped | `Q-002-quadruped-cat.glb` | Quadruped |  |  |  |  |  |  | Smaller body and tail base. |
| Q-003 | quadruped | `Q-003-quadruped-horse.fbx` | Quadruped |  |  |  |  |  |  | Long leg check. |
| Q-004 | quadruped | `Q-004-quadruped-lizard.glb` | Quadruped + Tail |  |  |  |  |  |  | Low body with long tail. |
| Q-005 | quadruped | `Q-005-quadruped-generated-creature.obj` | Quadruped |  |  |  |  |  |  | Generated creature stress. |
| C-001 | tail/wing creature | `C-001-tail-creature-dragon.glb` | Quadruped + Tail + Wing |  |  |  |  |  |  | Dragon-like tail and wing rig. |
| C-002 | wing creature | `C-002-wing-creature-bird.glb` | Wing |  |  |  |  |  |  | Wing deformation and mirror test. |
| C-003 | tail creature | `C-003-tail-character-biped.glb` | Humanoid + Tail |  |  |  |  |  |  | Biped with tail. |
| C-004 | wing creature | `C-004-wing-character-humanoid.fbx` | Humanoid + Wing |  |  |  |  |  |  | Humanoid body with wings. |
| C-005 | tail creature | `C-005-tail-creature-serpent.glb` | Tail Chain |  |  |  |  |  |  | Long continuous body/tail. |
| P-001 | prop | `P-001-prop-door-hinge.glb` | Prop Hinge |  |  |  |  |  |  | Single hinge rotation. |
| P-002 | prop | `P-002-prop-treasure-chest.fbx` | Prop Hinge |  |  |  |  |  |  | Lid and base separation. |
| P-003 | prop | `P-003-prop-robot-arm.glb` | Prop Hinge |  |  |  |  |  |  | Multi-segment mechanical articulation. |
| P-004 | prop | `P-004-prop-turret.glb` | Prop Hinge |  |  |  |  |  |  | Yaw and pitch hierarchy. |
| P-005 | prop | `P-005-prop-crane-claw.glb` | Prop Hinge |  |  |  |  |  |  | Multiple child hinges. |

## Smoke Test Result Format

When a row is tested, fill the columns like this:

- `Time To First Rig`: minutes from asset open to first generated rig.
- `Cleanup Minutes`: manual cleanup estimate after generated rig.
- `Deformation Score`: 1-5 from the scoring scale.
- `FBX Export`: `pass` or `fail`.
- `Engine Import`: `not tested`, `Unity pass`, `Unity fail`, `Unreal pass`, or `Unreal fail`.
- `Accepted`: `yes`, `no`, or `needs review`.

## Category Targets

| Category | Alpha Target |
|---|---|
| humanoid | 8 of 10 usable with cleanup <= 20 minutes. |
| quadruped | 3 of 5 usable with cleanup <= 35 minutes. |
| tail/wing creature | Useful first-pass result or clear failure report. |
| prop | 4 of 5 usable with cleanup <= 20 minutes. |
