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
| `H-006-quaternius-animated-woman.fbx` | humanoid | 954 | 17 | 2.727215 | 0 unweighted, 0 over-limit, 0 warnings/errors | pass | Unity FBX pass |

Status: `pass`

Notes:

- The passing run was executed outside the Codex sandbox because Blender 4.5.10
  crashed inside the sandbox with exit code 139 before producing a workflow
  summary.
- The benchmark includes import, source-rig stripping, landmark generation,
  armature generation, capsule weights, cleanup, QA report, four preview renders,
  pose deformation check, and Unity FBX export.
- This is a first real-asset workflow baseline, not a broad scalability proof.

## Coverage Gap

Product performance still needs measured runtime for larger synthetic and real
assets:

- 10k / 50k / 100k vertex end-to-end Blender workflow cases;
- multi-mesh humanoids with hair/accessory parts;
- quadruped and tail creature workflow timing;
- prop hinge workflow timing;
- Blender 4.2 target version timing, not only Blender 4.5.10 LTS.
