# Changelog

All notable changes to this repository are documented here.

The format is [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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
