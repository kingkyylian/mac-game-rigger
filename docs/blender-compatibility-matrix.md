# Blender Compatibility Matrix

Mac Game Rigger targets Blender 4.2 on macOS, but local alpha validation currently has Blender 4.5.10 LTS available at:

```text
/opt/homebrew/bin/blender
```

The compatibility gap is explicit: Blender 4.2 must still run the same matrix before beta.

## Matrix Runner

Run version-only discovery:

```bash
scripts/run_blender_compat_matrix.py --discover --skip-tests
```

Run the full Blender headless matrix for one executable:

```bash
scripts/run_blender_compat_matrix.py --blender /opt/homebrew/bin/blender
```

Write JSON evidence:

```bash
scripts/run_blender_compat_matrix.py \
  --blender /opt/homebrew/bin/blender \
  --output docs/blender-compatibility-results.local.json \
  --quiet
```

For Blender 4.2, pass the explicit executable path:

```bash
scripts/run_blender_compat_matrix.py \
  --blender /Applications/Blender.app/Contents/MacOS/Blender
```

## Result Semantics

The runner emits JSON with:

- `status: pass` when every supplied Blender binary reports a version and all selected Blender tests pass;
- `status: fail` when a binary starts but a version or test command fails;
- `status: blocked` when no executable Blender binary is found.

Each Blender entry includes:

- executable path;
- version output;
- platform line when available;
- per-test status;
- stdout/stderr tails for triage.

## Required Beta Evidence

Before beta, collect and commit or archive evidence for:

| Blender Version | Required Status | Notes |
|---|---|---|
| 4.2.x LTS | pass | Product target; required before beta. |
| 4.5.x LTS | pass | Current local validation line. |

## Current Known State

| Version | Path | Evidence |
|---|---|---|
| 4.5.10 LTS | `/opt/homebrew/bin/blender` | Full matrix passed outside the sandbox: 15 Blender headless tests, 0 failures. |
| 4.2.x LTS | not installed locally | Missing evidence; install or provide path before beta. |

## Codex Sandbox Note

Direct top-level `blender --background ...` commands can pass, but launching Blender as a subprocess from the matrix runner may fail inside the sandbox with `Segmentation fault: 11`. Run the matrix outside the sandbox for authoritative Blender evidence.
