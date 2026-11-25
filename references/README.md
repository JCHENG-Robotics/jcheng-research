# References — source records by theme

One file per source group. Each record states what was actually read (full text,
abstract only, code at a commit SHA), the version or commit, and the access date,
following the output contract in [README.md §6](../README.md#6-output-contract).

Records are filed under the ecosystem theme they inform: one theme per runtime
product repository, plus `datasets-benchmarks/` for material that has no single
runtime owner.

| Theme | Owner | Scope | Records |
|---|---|---|---|
| [system/](system/) | [`jcheng-system`](https://github.com/JCHENG-Robotics/jcheng-system) (L2) | Safety state machine, leases, arbiter, `ExecuteMotion`, MoveIt plan-only, hardware bridge, gateways, telemetry, DDS domains | 0 |
| [perception/](perception/) | [`jcheng-perception`](https://github.com/JCHENG-Robotics/jcheng-perception) (L3) | Acquisition, depth/TF timestamps, back-projection, two-view fusion, Kalman, detection and segmentation, calibration | 3 |
| [mobile/](mobile/) | [`jcheng-mobile`](https://github.com/JCHENG-Robotics/jcheng-mobile) (L3) | LiDAR, ICP odometry, SLAM, Nav2, `/cmd_vel` chassis intent | 0 |
| [ops/](ops/) | [`jcheng-ops`](https://github.com/JCHENG-Robotics/jcheng-ops) (OPS) | Health probes, hardware watchdog, systemd self-healing, deployment and recovery | 0 |
| [manipulation/](manipulation/) | [`jcheng-manipulation`](https://github.com/JerichoCheng/jcheng-manipulation) (frozen v1.0.0 baseline) + the ArmPi Ultra arm | VLA models and training, action chunking, grasp and handoff, arm and gripper control | 14 |
| [datasets-benchmarks/](datasets-benchmarks/) | Cross-cutting — no runtime repository | Datasets, data integrity, benchmarks, competition rules, evaluation protocol | 3 |

## Filing rules

1. File a source under the theme of its **primary consumer**. If two themes
   consume it, keep one record and cross-link it from the other theme's README;
   never duplicate the file.
2. Material that informs no single runtime repository — datasets, benchmarks,
   competition rules, evaluation methodology — goes to `datasets-benchmarks/`.
3. Records are `references/<theme>/<slug>.md`, one file per source group. The
   access date and the read scope live inside the file; the filename carries no
   date.
4. Local PDF copies are `references/<theme>/papers/YYYYMMDD-<slug>.pdf` and are
   linked from the record. Check the license before storing a copy; keep
   third-party material out of git when redistribution is not allowed. The 5 MB
   size gate applies.
5. Each theme has a `README.md` listing its records and any cross-theme links.
   Adding or renaming a theme changes `scripts/check_repo_gate.sh` in the same
   commit.
6. Evidence grades S–D are assigned in the report, not here. A record states
   facts, read scope and access date; the report carries the judgement.

`reports/` and `experiments/` stay flat and date-named (`YYYYMMDD-<slug>`);
[reports/README.md](../reports/README.md) is the themed view, and every report
links the records it used.
