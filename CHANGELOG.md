# Changelog

All notable changes to this repository are documented here.

The format is [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Draft investigation report
  `reports/20261126-ultralytics-repository-review.md` (Ultralytics at
  `v8.4.219` / `3a31e32`: 233 files / 83.6k LOC, 230 tests, AGPL-3.0 +
  Enterprise dual licensing, the vendor's public position that even private
  internal use requires publishing the whole app, default Google Analytics /
  Sentry / auto-install / `weights_only=False`, YOLO26 paper and Pi 5/Orin
  numbers, YOLO27 unreleased, and the fit with the existing five-backend
  perception stack). Adds the source record
  `references/perception/ultralytics-repository.md` and the pre-registered
  `experiments/20261126-ultralytics-runtime-audit/design.md` (MVE-1…3; not run).
- Draft investigation report
  `reports/20261126-rlinf-piper-pico-data-collection.md` (RLinf at
  `ed0e1b83`: the PICO VR chain is implemented, but `PiperEnv` rejects every
  teleop device (`TELEOP = ()`) and lacks the kinematics that `PicoJoint`
  requires; the vendor `pyAgxArm` layer does support `piper_x`, `move_p()` and
  TCP/flange conversion, so the route is a CARTESIAN_POSE environment rather
  than hand-written IK; includes community implementations and their licences).
  Adds the source record `references/manipulation/rlinf-piper-pico.md` and the
  pre-registered `experiments/20261126-rlinf-piper-pico-mve/design.md` (MVE-0…3;
  not run).
- Ran a 30-minute advisory-service soak on the Orin: 1,800 s / 180
  requests / 0 errors, 162 judge / 18 no-mask, p50 1.04 s / p95 2.32 s;
  service RSS +3 MB and Qwen RSS +7 MB (plateau), no crash. Data
  `experiments/20261126-agx-orin-stack-probe/data/ds_advisor_soak30.{json,csv}`.
- Ran a local advisory HTTP service on the Orin (SAM3 + Qwen, T1 +
  score≥0.8): 60 requests, 58 judge / 2 no-mask, p50 **2.04 s** / p95 2.08 s,
  no crash; RSS grew 1.39→2.09 GB over 220 s (longer soak needed). Summary
  `experiments/20261126-agx-orin-stack-probe/data/ds_advisor_service.json`.
- Ran the 200-frame fixed-policy stability test on the Orin (T1 + SAM3
  score≥0.8, frontA/B + wristA/B): **183 judged / 182 correct = 99.45%**,
  16/16 wrong pairs, one high-score edge false negative (f21), 30 NO_MASK +
  3 low-score skips, no reboot. CSV
  `experiments/20261126-agx-orin-stack-probe/data/ds_stability200.csv`.
- Validated the fixed judge policy on the Orin: T1 + SAM3 score≥0.8 over
  18 cases (7 easy, 7 hard negatives, 4 partials) gave **15 judged / 15
  correct**, with 3 low-score masks skipped (clear/right-edge). CSV
  `experiments/20261126-agx-orin-stack-probe/data/ds_t1gate.csv`.
- Draft investigation report `reports/20261126-sam3-sst-open-source-attempt-route.md`
  (SAM 3 in the SST post-competition repository: vendored SAM3, offline data
  chain, online stream server, prompt/judge contracts, gated weights, SAM
  License, consumer-GPU evidence, and a staged ArmPi route), with the source
  record updates in `references/perception/sam3.md` and
  `references/manipulation/sst-repo-audit.md`, and the pre-registered
  `experiments/20261126-sam3-6gb-feasibility/design.md` (MVE-0…3; not run,
  blocked on HF gated weights).
- Draft investigation report `reports/20261126-agx-orin-sam3-qwen-deployment.md`
  (Jetson AGX Orin 64GB, JetPack 6.2: Qwen3-VL-8B via llama.cpp, SAM 3.0 at
  1008 px + bf16 autocast, 19V PSU requirement, shelf calibration and
  100-frame front/wrist pipelines, judge template sensitivity), the source
  record `references/perception/jetson-agx-orin.md`, and the
  `experiments/20261126-agx-orin-stack-probe/` design/result/data (MVE-0/1/2
  run; MVE-3 partial).
- Draft investigation report `reports/20261125-lingbot-vla-sst-foreground-prompting.md`
  (LingBot-VLA 2.0 / SST foreground-prompting evaluation), eight source records
  under `references/`, and the MVE-0 desk re-analysis under
  `experiments/20261125-lingbot-sst-reanalysis/` (design, data, script, log, result).
- Draft investigation report `reports/20261125-glovla-hybrid-factorization-eval.md`
  (GloVLA geometry + local-VLA factorization assessment), self-reviewed, and the
  MVE-0 handoff-budget desk calculation under
  `experiments/20261125-glovla-handoff-budget/` (design, script, data, log, result).
- Chinese DOCX edition of the GloVLA report and a compressed local copy of the
  paper (`references/manipulation/papers/20261125-glovla.pdf`, CC BY-NC-SA 4.0),
  with the source record `references/manipulation/glovla.md`.
- Batch investigation `reports/20261125-paper-batch-mobile-manipulation.md`
  (ten 2026 papers on industrial vision, bin picking, mobile grasping and
  lightweight VLA), with ten per-paper source records under
  `references/manipulation/` and `references/perception/`; four offline MVEs
  are designed but not run. Papers 02/05/12 could not be obtained and are
  outside the batch boundary.
- Thematic source-record index `references/README.md` and a README per theme
  (`system/`, `perception/`, `mobile/`, `ops/`, `manipulation/`,
  `datasets-benchmarks/`) stating the theme scope, owner and filing rules.
- Themed report index `reports/README.md` covering the investigation reports,
  task books and experiments, with status and related artefacts.
- Piper X simulation data map (`reports/20261126-piper-x-simulation-data-map.md`),
  the source record `references/manipulation/piper-x-assets.md`, and MVE-1
  (`experiments/20261126-piper-x-gazebo-plant/`): a Gazebo Harmonic 8.15 plant
  generated from `agx_arm_urdf@680fa925` on domain 43 under `/sim/piper_x`.
  MVE-1 passes URDF load, 22 mesh paths, joint limits, controller activation and
  domain isolation; the added joint-tracking check fails for joint2/joint3, and
  neither DART nor bullet-featherstone implements SDF mimic. MVE-2…4 not run.

### Changed

- Reorganized `references/` by ecosystem theme, mirroring the product
  repositories, with `datasets-benchmarks/` for cross-cutting material; source
  records and their local PDF copies moved into the theme directories. Report,
  experiment and source-record links updated to the new paths.

## [0.1.0] — 2026-11-25

### Added

- Initial repository: the investigation protocol (`AGENTS.md`), the 13-section
  report template, and the `reports/`, `experiments/`, `references/` output
  contract.
- Repository gate (`scripts/check_repo_gate.sh`) and CI workflow `research-gate`
  checking the document set, output directories, absence of `LICENSE`, secrets,
  model weights, recorded data and files larger than 5 MB.
- Bilingual `README.md` / `README.zh-CN.md`, `ROADMAP.md`, `ACCEPTANCE.md` and
  `LICENSE-REVIEW.md` following the organization documentation standard.
