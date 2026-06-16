# Deformation Scoring Rubric

This rubric turns visual rig review into a repeatable score.

## Score Scale

| Score | Meaning | Production Trial Status |
|---:|---|---|
| 5 | Clean deformation in standard poses; only minor polish needed. | usable |
| 4 | Small visible issues, but acceptable for gameplay prototype. | usable |
| 3 | Noticeable issues that need targeted cleanup. | usable with cleanup |
| 2 | Major deformation failures in one or more critical joints. | not acceptable |
| 1 | Rig is structurally or visually unusable. | not acceptable |

## Critical Review Areas

Humanoid:

- neck;
- shoulders;
- elbows;
- wrists;
- spine;
- hips;
- knees;
- ankles;
- fingers if present;
- cloth, coat, hair, or accessory intersections.

Quadruped:

- neck;
- spine;
- shoulder/foreleg root;
- elbow/front knee;
- wrist/paw;
- hip/hindleg root;
- knee/hock;
- ankle/paw;
- tail base if present.

Tail or wing creature:

- tail base;
- tail mid-chain;
- tail tip;
- wing root;
- wing mid-chain;
- wing tip;
- shoulder/body transition.

Prop:

- hinge pivot;
- parent-child transform;
- mechanical separation;
- rotation axis.

## Required Pose Views

For each real asset, capture at least:

- neutral pose;
- arm or front-leg raise;
- elbow/knee bend;
- neck turn;
- hip/leg stress pose;
- tail or wing stress pose when relevant.

## Automatic QA Signals

Structural QA can support the score but cannot replace review.

Useful signals:

- unweighted vertex count;
- vertices over influence limit;
- empty vertex groups;
- missing expected bones;
- asymmetrical landmark placement;
- bone count mismatch;
- export/import warnings.

## Reviewer Notes

Every score below 4 must include:

- failing joint or region;
- likely cause;
- cleanup recommendation;
- whether the issue is acceptable for gameplay prototype.

## Gate Thresholds

Internal alpha:

- at least one engine import pass;
- known deformation gaps documented.

Production trial:

- 10 real assets reviewed;
- at least 70% score 3 or higher;
- at least 3 Unity import passes;
- at least 1 Unreal import pass or explicit Unreal blocker.

Beta:

- 20 real assets reviewed;
- at least 80% score 3 or higher;
- at least 50% score 4 or higher;
- Unity and Unreal import verification both repeatable.
