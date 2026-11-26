# Reports — indexed by theme

Reports stay flat and date-named (`reports/YYYYMMDD-<slug>.md`) so their identity
does not change; this index is the themed view over them. It records metadata
only — each report keeps its own status, evidence grades and conclusions, and a
draft is never upgraded by appearing here. Themes follow
[references/README.md](../references/README.md) and the product repositories.

## Investigation reports

| Report | Theme | Decision it informs | Status (2026-11-26) | Related experiment |
|---|---|---|---|---|
| [LingBot-VLA 2.0 / SST foreground-prompting evaluation](20261125-lingbot-vla-sst-foreground-prompting.md) | manipulation | whether to adopt the RoboTwin post-training recipe: foreground prompting, module learning rates, data repair | draft; review pending | [MVE-0 desk re-analysis](../experiments/20261125-lingbot-sst-reanalysis/result.md) |
| [GloVLA factorization assessment](20261125-glovla-hybrid-factorization-eval.md) | manipulation | whether to adopt the geometry-move + local-VLA factorization; GPU and demo prerequisites | reviewed (self-review only); independent review pending | [MVE-0 handoff budget](../experiments/20261125-glovla-handoff-budget/result.md) |
| [10-paper mobile-manipulation batch assessment](20261125-paper-batch-mobile-manipulation.md) | manipulation (cross: perception, mobile) | which segmentation/6D-pose/VLA components to prototype offline; what to reject or defer | reviewed (self-review only); independent review pending | MVE-0…3 designed in §11; not run |
| [Piper X simulation data map](20261126-piper-x-simulation-data-map.md) | manipulation | which GitHub assets to pin, where they belong, and whether to open a CAN profile contract | draft; review pending | [MVE-0 asset materialisation; MVE-1 run](../experiments/20261126-piper-x-gazebo-plant/result.md) — MVE-1 has an open joint2/3 tracking failure; MVE-2…4 designed, not run |

Chinese edition: [GloVLA report DOCX](20261125-glovla-hybrid-factorization-eval.zh-CN.docx);
the Markdown report remains the traceable version.

## Task books and experiments

| Document | Theme | State | Report |
|---|---|---|---|
| [VP-VLA ArmPi task book](../experiments/20261125-vp-vla-armpi/design.md) | manipulation | pre-registered design; not run | none yet |
| [LingBot/SST MVE-0 re-analysis](../experiments/20261125-lingbot-sst-reanalysis/result.md) | manipulation | desk re-analysis run 2026-11-25 | LingBot-VLA / SST report above |
| [GloVLA handoff-budget MVE-0](../experiments/20261125-glovla-handoff-budget/result.md) | manipulation | desk calculation run 2026-11-25 | GloVLA report above |
| [Piper X Gazebo plant MVE-1](../experiments/20261126-piper-x-gazebo-plant/result.md) | manipulation | run 2026-11-26; A1–A5/A7 pass, A6 fails on joint2/joint3; mimic structural only | Piper X report above |

## Themes with no report yet

- [system/](../references/system/README.md) — safety, arbitration, motion
  execution; no investigation report yet.
- [perception/](../references/perception/README.md) — vision, depth/TF, fusion,
  calibration; no investigation report yet.
- [mobile/](../references/mobile/README.md) — LiDAR, ICP odometry, SLAM, Nav2; no
  investigation report yet.
- [ops/](../references/ops/README.md) — probes, watchdog, self-healing; no
  investigation report yet.
- [datasets-benchmarks/](../references/datasets-benchmarks/README.md) —
  cross-cutting; no standalone report, currently cited by the manipulation
  reports.

## Adding a report

1. Start from `templates/research-report.md` and save it as
   `reports/YYYYMMDD-<slug>.md`.
2. Add a row under the matching theme with the decision it informs and its
   status; file its source records under `references/<theme>/`.
3. Register any experiment as `experiments/YYYYMMDD-<slug>/` and link it from the
   row.
