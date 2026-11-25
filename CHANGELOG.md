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
