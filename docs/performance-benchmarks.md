# Performance Benchmarks

Date: 2026-06-26

These benchmarks track Mac Game Rigger runtime risk separately from visual rig
quality. The current benchmark covers deterministic capsule weight-binding math
without Blender UI, preview rendering, or FBX export overhead.

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

## Coverage Gap

This benchmark does not replace end-to-end Blender workflow timing. Product
performance still needs measured runtime for:

- mesh analysis;
- landmark workflow;
- armature generation;
- Blender automatic weights;
- cleanup diagnostics;
- pose tests;
- preview rendering;
- FBX export.
