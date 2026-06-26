# Asset Evidence Progress Report

Schema status: **pass**
Production trial gate: **pass**
Evidence file check: **enabled**
Evidence root: `.`

## Summary

- Slots: 25
- Real assets registered: 12
- Complete evidence entries: 12
- Score >= 3 count: 11
- Score >= 3 ratio: 0.917

## Production Trial Requirements

| Requirement | Status |
|---|---|
| `completeRealAssetsAtLeast10` | pass |
| `humanoidsAtLeast3` | pass |
| `quadrupedsAtLeast2` | pass |
| `lowPolyHumanoidIncluded` | pass |
| `thinLimbHumanoidIncluded` | pass |
| `wideShoulderOrBulkyIncluded` | pass |
| `tailCreatureIncluded` | pass |
| `propOrAccessoryIncluded` | pass |
| `score3PlusAtLeast70Percent` | pass |
| `unityImportPassesAtLeast3` | pass |
| `unrealPassOrExplicitBlocker` | pass |

## Strict Quality Gates

| Gate | Status | Missing Slots |
|---|---|---|
| `configuredAnimatorSmokeForHumanoidScore3` | blocked | H-003, H-004, H-005, H-009, H-010 |
| `realSeparateMeshHumanoidEvidence` | blocked | H-003, H-004, H-005, H-006, H-009, H-010 |

## Category Counts

| Category | Complete Evidence Count |
|---|---:|
| humanoid | 7 |
| quadruped | 2 |
| tail creature | 1 |
| wing creature | 0 |
| prop | 2 |

## Slot Status

| Slot | Category | Real Asset | Evidence | Score | Source Meshes | Rig Meshes | Pose QA | Visual | Unity | Unreal | Preview | Weight | Warnings | Issues |
|---|---|---|---|---:|---:|---:|---|---|---|---|---|---|---|---|
| H-001 | humanoid | pass | pass | 2 | 1 | 1 | pass 1.207x | fail | blocked | blocked | side 54->54px 1.00x lean 0.04 | core 615 arm 74 leg 87 foot 15 humanoid qa warn weakHumanoidFootCoverage |  |  |
| H-002 | humanoid | missing | missing |  |  |  |  |  |  |  |  |  |  |  |
| H-003 | humanoid | pass | pass | 3 | 1 | 1 | pass 1x | pass | pass | blocked | side 256->256px 1.00x lean 0.00 | core 1307 neck 5 arm 38 leg 96 foot 38 humanoid qa pass | H-003: Unity import configuredAnimatorSmoke is not recorded yet |  |
| H-004 | humanoid | pass | pass | 3 | 1 | 1 | pass 1x | pass | pass | blocked | side 120->120px 1.00x lean 0.05 | core 2984 neck 3 arm 86 leg 207 foot 86 humanoid qa pass | H-004: Unity import configuredAnimatorSmoke is not recorded yet |  |
| H-005 | humanoid | pass | pass | 3 | 1 | 1 | pass 1.0018x | pass | pass | blocked | side 100->102px 1.02x lean 0.05 | core 1175 neck 1 arm 36 leg 135 foot 36 humanoid qa pass | H-005: Unity import configuredAnimatorSmoke is not recorded yet |  |
| H-006 | humanoid | pass | pass | 3 | 1 | 1 | pass 1.6538x | pass | pass | blocked | side 54->51px 0.94x lean 0.01 | core 716 arm 52 leg 115 foot 71 humanoid qa pass |  |  |
| H-007 | humanoid | missing | missing |  |  |  |  |  |  |  |  |  |  |  |
| H-008 | humanoid | missing | missing |  |  |  |  |  |  |  |  |  |  |  |
| H-009 | humanoid | pass | pass | 3 | 1 | 1 | pass 1.0118x | pass | pass | blocked | side 92->92px 1.00x lean 0.05 | core 1249 arm 158 leg 70 foot 38 humanoid qa pass | H-009: Unity import configuredAnimatorSmoke is not recorded yet |  |
| H-010 | humanoid | pass | pass | 3 | 1 | 1 | pass 1x | pass | pass | blocked | side 120->120px 1.00x lean 0.05 | core 984 neck 3 arm 34 leg 259 foot 34 humanoid qa pass | H-010: Unity import configuredAnimatorSmoke is not recorded yet |  |
| Q-001 | quadruped | pass | pass | 3 | 1 | 1 | pass 1.2246x | pass | pass | blocked | side 72->84px 1.17x lean 0.03 | core 447 leg 59 foot 456 |  |  |
| Q-002 | quadruped | pass | pass | 3 | 1 | 1 | pass 1.3102x | pass | pass | blocked | side 52->62px 1.19x lean 0.02 | core 164 neck 1 leg 155 foot 532 |  |  |
| Q-003 | quadruped | missing | missing |  |  |  |  |  |  |  |  |  |  |  |
| Q-004 | quadruped | missing | missing |  |  |  |  |  |  |  |  |  |  |  |
| Q-005 | quadruped | missing | missing |  |  |  |  |  |  |  |  |  |  |  |
| C-001 | tail creature | pass | pass | 3 | 1 | 1 | pass 1.209x | pass | pass | blocked | side 32->34px 1.06x lean 0.00 | core 323 leg 75 foot 168 |  |  |
| C-002 | wing creature | missing | missing |  |  |  |  |  |  |  |  |  |  |  |
| C-003 | tail creature | missing | missing |  |  |  |  |  |  |  |  |  |  |  |
| C-004 | wing creature | missing | missing |  |  |  |  |  |  |  |  |  |  |  |
| C-005 | tail creature | missing | missing |  |  |  |  |  |  |  |  |  |  |  |
| P-001 | prop | pass | pass | 3 | 1 | 1 | pass 4.7475x allowed:y | pass | pass | blocked | side 176->168px 0.95x lean 0.01 | prop base 156 moving 204 prop qa fail missingPropHingeCoverage |  |  |
| P-002 | prop | pass | pass | 3 | 1 | 1 | pass 1.5075x allowed:y | pass | pass | blocked | side 183->180px 0.98x lean 0.01 | prop base 64 moving 54 prop qa fail missingPropHingeCoverage |  |  |
| P-003 | prop | missing | missing |  |  |  |  |  |  |  |  |  |  |  |
| P-004 | prop | missing | missing |  |  |  |  |  |  |  |  |  |  |  |
| P-005 | prop | missing | missing |  |  |  |  |  |  |  |  |  |  |  |
