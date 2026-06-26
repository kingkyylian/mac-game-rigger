# Performance Benchmarks

Date: 2026-06-26

These benchmarks track Mac Game Rigger runtime risk separately from visual rig
quality. They split the deterministic core weight math from the full Blender
asset workflow so regressions can be isolated quickly.

## Capsule Weight Binding

Command:

```bash
python3 scripts/run_performance_benchmark.py \
  --vertex-count 10000 \
  --vertex-count 50000 \
  --vertex-count 100000 \
  --output build/performance-benchmark.json
```

Result:

| Vertex Count | Bone Count | Weighted Vertices | Duration Seconds | Vertices / Second |
|---:|---:|---:|---:|---:|
| 10,000 | 17 | 10,000 | 0.488191 | 20,483.79 |
| 50,000 | 17 | 50,000 | 2.249841 | 22,223.79 |
| 100,000 | 17 | 100,000 | 4.604221 | 21,719.20 |

Status: `pass`

## Blender Asset Workflow

Command:

```bash
scripts/run_blender_workflow_benchmark.py \
  --blender blender \
  --asset local_assets/H-006/H-006-quaternius-animated-woman.fbx \
  --template humanoid \
  --evidence-root build/blender-workflow-benchmark \
  --output build/blender-workflow-benchmark.json \
  --timeout-seconds 300 \
  --max-seconds-per-case 120
```

Result:

| Asset | Template | Vertices | Bones | Duration Seconds | QA | Pose Deformation | Export |
|---|---|---:|---:|---:|---|---|---|
| `H-006-quaternius-animated-woman.fbx` | humanoid | 954 | 17 | 3.142040 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |

Status: `pass`

Notes:

- The passing run was executed outside the Codex sandbox because Blender 4.5.10
  crashed inside the sandbox with exit code 139 before producing a workflow
  summary.
- The benchmark includes import, source-rig stripping, landmark generation,
  armature generation, capsule weights, cleanup, QA report, four preview renders,
  pose deformation check, and Unity FBX export.
- This is a first real-asset workflow baseline, not a broad scalability proof.

## Real Asset Family Workflow

Command:

```bash
scripts/run_blender_workflow_benchmark.py \
  --blender blender \
  --manifest samples/manifest.json \
  --slot H-003 \
  --slot H-004 \
  --slot H-005 \
  --slot H-009 \
  --slot H-010 \
  --slot Q-001 \
  --slot Q-002 \
  --slot C-001 \
  --slot P-001 \
  --slot P-002 \
  --evidence-root build/blender-workflow-real-asset-family-benchmark \
  --output build/blender-workflow-real-asset-family-benchmark.json \
  --timeout-seconds 300 \
  --max-seconds-per-case 120
```

Result:

| Slot | Asset | Template | Vertices | Bones | Duration Seconds | QA | Pose Deformation | Export |
|---|---|---|---:|---:|---:|---|---|---|
| H-003 | `H-003-quaternius-knight-male.fbx` | humanoid | 1,484 | 17 | 1.774947 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |
| H-004 | `H-004-quaternius-wizard.fbx` | humanoid | 3,366 | 17 | 1.901814 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |
| H-005 | `H-005-quaternius-pirate-male.fbx` | humanoid | 1,383 | 17 | 1.760538 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |
| H-009 | `H-009-quaternius-soldier-male.fbx` | humanoid | 1,515 | 17 | 1.771729 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |
| H-010 | `H-010-quaternius-elf.fbx` | humanoid | 1,314 | 17 | 1.731110 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |
| Q-001 | `Q-001-quaternius-husky.fbx` | quadruped | 962 | 23 | 1.820218 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |
| Q-002 | `Q-002-quaternius-fox.fbx` | quadruped | 926 | 23 | 1.855413 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |
| C-001 | `C-001-quaternius-apatosaurus.fbx` | tail_creature | 723 | 25 | 1.600824 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |
| P-001 | `P-001-local-wooden-door.fbx` | prop_hinge | 360 | 3 | 1.477657 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |
| P-002 | `P-002-local-treasure-chest.fbx` | prop_hinge | 118 | 3 | 1.446091 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |

Status: `pass`

Notes:

- This benchmark uses `samples/manifest.json` slot ids so real asset paths and
  rig templates are resolved from the canonical production-trial manifest.
- The run covers bulky/armored humanoids, robe/accessory humanoids, thin-limb
  humanoids, quadrupeds, one tail creature, and hinge props.
- These results prove workflow runtime and structural QA on real assets; they
  still do not replace Unity configured Animator evidence or artist visual
  approval.

## Synthetic Blender Workflow Scaling

Command:

```bash
scripts/run_blender_workflow_benchmark.py \
  --blender blender \
  --synthetic-humanoid-vertices 10000 \
  --synthetic-humanoid-vertices 50000 \
  --synthetic-humanoid-vertices 100000 \
  --evidence-root build/blender-workflow-synthetic-benchmark \
  --output build/blender-workflow-synthetic-benchmark.json \
  --timeout-seconds 600 \
  --max-seconds-per-case 180
```

Result:

| Target Vertices | Imported Vertices | Bones | Duration Seconds | QA | Pose Deformation | Export |
|---:|---:|---:|---:|---|---|---|
| 10,000 | 10,000 | 17 | 3.195480 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |
| 50,000 | 50,000 | 17 | 5.995934 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |
| 100,000 | 100,000 | 17 | 10.817145 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |

Status: `pass`

Notes:

- Synthetic assets are deterministic OBJ humanoid stress meshes generated by
  `scripts/run_blender_workflow_benchmark.py`.
- Pose deformation passes on the deterministic synthetic humanoid scaling cases;
  this still remains a workflow scalability benchmark, not a visual deformation
  quality score.
- The imported Blender QA vertex count matches the requested target vertex count
  for all three cases.

## Synthetic Template Family Workflow

Command:

```bash
scripts/run_blender_workflow_benchmark.py \
  --blender blender \
  --synthetic-multimesh-humanoid-vertices 10000 \
  --synthetic-quadruped-vertices 10000 \
  --synthetic-tail-creature-vertices 10000 \
  --synthetic-prop-hinge-vertices 10000 \
  --evidence-root build/blender-workflow-template-family-benchmark \
  --output build/blender-workflow-template-family-benchmark.json \
  --timeout-seconds 600 \
  --max-seconds-per-case 180
```

Result:

| Synthetic Type | Template | Format | Meshes | Vertices | Bones | Duration Seconds | QA | Pose Deformation | Export |
|---|---|---|---:|---:|---:|---:|---|---|---|
| multi-mesh humanoid | humanoid | glTF | 6 | 10,000 | 17 | 2.609815 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |
| quadruped | quadruped | OBJ | 1 | 10,000 | 23 | 2.669343 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |
| tail creature | tail_creature | OBJ | 1 | 10,000 | 25 | 2.642737 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |
| prop hinge | prop_hinge | OBJ | 1 | 10,000 | 3 | 1.958864 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |

Status: `pass`

Notes:

- The multi-mesh humanoid case imports as six Blender meshes and exercises
  separated source objects.
- Quadruped, tail creature, and prop hinge cases extend workflow timing beyond
  humanoids at a consistent 10k vertex target.
- These generated assets are scalability probes, not substitutes for real
  artist asset review.

## Coverage Gap

Product performance still needs measured runtime for larger synthetic and real
assets:

- real multi-mesh humanoids with hair/accessory parts;
- Blender 4.2 target version timing, not only Blender 4.5.10 LTS.
