# ROADMAP

> Status: v0.1.0, last updated 2026-11-26. English canonical.

## Current state

| Item | State | Evidence |
|---|---|---|
| Repository skeleton, protocol, report template, gate | Complete | `scripts/check_repo_gate.sh`; CI `research-gate` |
| Investigation reports | Complete, drafts pending review (2026-11-26) | `reports/20261125-lingbot-vla-sst-foreground-prompting.md`; `reports/20261126-ultralytics-repository-review.md`; `reports/20261126-rlinf-piper-pico-data-collection.md` |
| AGX Orin / SAM3 advisory-service experiments | Complete; results recorded, review pending (2026-11-26) | `experiments/20261126-agx-orin-stack-probe/` (60/1800 s/500-request runs, 200-frame stability) |
| Minimum viable experiments | Complete or designed; review pending (2026-11-26) | `experiments/20261125-lingbot-sst-reanalysis/`; `experiments/20261126-ultralytics-runtime-audit/design.md`; `experiments/20261126-rlinf-piper-pico-mve/design.md` |

## Milestones

| Milestone | Scope | State | Exit criterion | Evidence |
|---|---|---|---|---|
| R0 | Protocol, report template, output contract, repository gate | Complete (2026-11-25) | Gate passes locally and in CI | `ACCEPTANCE.md` |
| R1 | First investigation report | Complete, draft review pending (2026-11-26) | `reports/` contains 13-section reports whose key conclusions carry S–D grades and recorded sources | `reports/20261125-lingbot-vla-sst-foreground-prompting.md`; `reports/20261126-ultralytics-repository-review.md`; `reports/20261126-rlinf-piper-pico-data-collection.md` |
| R2 | First minimum viable experiment | Complete, review pending (2026-11-26) | `experiments/<id>/` contains design, data, logs and result, with the rollback statement and the actual run date | `experiments/20261125-lingbot-sst-reanalysis/`; `experiments/20261126-agx-orin-stack-probe/` |

## Next

1. **R1 — review the first draft.** The LingBot-VLA 2.0 / SST report is a draft;
   review its grades and decide whether to cite it. Candidate open risks for the
   next report, not yet prioritised:
   - the constant 10–14 mm cross-view offset in the perception fixed-point run
     (external extrinsic suspect);
   - LiDAR mount pose and `/scan` quality before any mobile navigation;
   - the unverified S7 stale-state injection and S9 runtime publisher detection;
   - replay-vs-hardware gap for MoveIt plan-only and the full G8 sequence.
2. **R2 — run MVE-2 (data-integrity gate) on the next demo set**, or MVE-1 if a
   learned-policy track is approved. Hardware execution still needs the separate per-session operator
   authorization defined in the ecosystem root `AGENTS.md`.

## Out of scope

- Runtime, driver, launch or configuration code that the robot could load.
- ROS, DDS, device or bus access of any kind.
- Accepting a claim on behalf of a product repository; `ACCEPTANCE.md` here
  covers this repository only.
- Publishing private plan material or third-party confidential material.

## Dependencies

- No runtime dependency in either direction.
- Reports may cite `jcheng-interfaces` v0.1.0
  (`sha256:0b8d72ced7f54d444d6851d8b99a51a78e2bed3f687324f51a15f76557f24b42`);
  citing a contract does not create a dependency.
- Hardware experiments inherit the authorization and safety rules of the
  ecosystem root `AGENTS.md` and the owning repository.
