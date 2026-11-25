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
- Thematic source-record index `references/README.md` and a README per theme
  (`system/`, `perception/`, `mobile/`, `ops/`, `manipulation/`,
  `datasets-benchmarks/`) stating the theme scope, owner and filing rules.
- Themed report index `reports/README.md` covering the investigation reports,
  task books and experiments, with status and related artefacts.

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
