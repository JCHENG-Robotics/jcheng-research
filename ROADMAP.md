# ROADMAP

> Status: v0.1.0, last updated 2026-11-25. English canonical.

## Current state

| Item | State | Evidence |
|---|---|---|
| Repository skeleton, protocol, report template, gate | Complete | `scripts/check_repo_gate.sh`; CI `research-gate` |
| First investigation report | Not started | — |
| First minimum viable experiment | Not started | — |

## Milestones

| Milestone | Scope | State | Exit criterion | Evidence |
|---|---|---|---|---|
| R0 | Protocol, report template, output contract, repository gate | Complete (2026-11-25) | Gate passes locally and in CI | `ACCEPTANCE.md` |
| R1 | First investigation report | Not started | `reports/` contains a 13-section report whose key conclusions carry S–D grades, whose sources are recorded in `references/`, and which ends in a decision or a minimum viable experiment | — |
| R2 | First minimum viable experiment | Not started | `experiments/<id>/` contains design, data, logs and result, with the rollback statement and the actual run date | — |

## Next

1. **R1 — pick the first question.** Candidate open risks in the ecosystem, not
   yet prioritised:
   - the constant 10–14 mm cross-view offset in the perception fixed-point run
     (external extrinsic suspect);
   - LiDAR mount pose and `/scan` quality before any mobile navigation;
   - the unverified S7 stale-state injection and S9 runtime publisher detection;
   - replay-vs-hardware gap for MoveIt plan-only and the full G8 sequence.
2. **R2 — execute one experiment** for whichever R1 question produces a testable
   hypothesis. Hardware execution still needs the separate per-session operator
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
