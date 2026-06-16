# Unreal Import Verification

Unreal import validation is not yet complete. This document defines the missing gate and the first implementation target.

## Current Status

`UnrealEditor` is not currently available on `PATH`, so alpha smoke has not verified a real Unreal import.

Unity import verification has passed once, but Unity success does not prove Unreal success. Unreal can expose separate FBX problems:

- bone axis mismatch;
- root bone naming;
- scale mismatch;
- leaf bone behavior;
- material import differences;
- skeleton asset creation issues.

## Required Local Inputs

To run Unreal import verification, the machine needs:

- an installed Unreal Editor;
- the full path to `UnrealEditor`;
- an exported FBX from Mac Game Rigger;
- a temporary project or scripted throwaway project location.

Candidate editor path examples:

```text
/Applications/Epic Games/UE_5.4/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor
/Users/Shared/Epic Games/UE_5.4/Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor
```

## Target Command Shape

The future verifier should follow this pattern:

```bash
scripts/verify_unreal_fbx_import.sh \
  --fbx <exported.fbx> \
  --unreal <path-to-UnrealEditor> \
  --timeout-seconds 240
```

Expected successful output should be machine-readable:

```json
{"status":"pass","assetPath":"/Game/MacGameRiggerImportCandidate/<file>"}
```

## Minimum Checks

The first Unreal verifier should check:

- Unreal starts in unattended/batch mode;
- the FBX can be imported;
- a skeletal mesh or static mesh asset is created as expected;
- skeleton/root bone information is available for skeletal imports;
- import logs do not contain fatal FBX errors;
- the script exits non-zero on failure.

## Production Trial Gate

Before production trial, collect:

- at least 1 humanoid Unreal import pass;
- at least 1 non-humanoid or quadruped Unreal import pass;
- scale/orientation notes;
- imported skeleton naming notes;
- FBX export profile used for each import.

## Current Blocker

The blocker is environment availability, not add-on code: `UnrealEditor` needs to be installed or its path supplied before the verifier can be implemented and tested end to end.
