# Reports — indexed by theme

Reports stay flat and date-named (`reports/YYYYMMDD-<slug>.md`) so their identity
does not change; this index is the themed view over them. It records metadata
only — each report keeps its own status, evidence grades and conclusions, and a
draft is never upgraded by appearing here. Themes follow
[references/README.md](../references/README.md) and the product repositories.

## Investigation reports

| Report | Theme | Decision it informs | Status (2026-11-28) | Related experiment |
|---|---|---|---|---|
| [LingBot-VLA 2.0 / SST foreground-prompting evaluation](20261125-lingbot-vla-sst-foreground-prompting.md) | manipulation | whether to adopt the RoboTwin post-training recipe: foreground prompting, module learning rates, data repair | draft; review pending | [MVE-0 desk re-analysis](../experiments/20261125-lingbot-sst-reanalysis/result.md) |
| [GloVLA factorization assessment](20261125-glovla-hybrid-factorization-eval.md) | manipulation | whether to adopt the geometry-move + local-VLA factorization; GPU and demo prerequisites | reviewed (self-review only); independent review pending | [MVE-0 handoff budget](../experiments/20261125-glovla-handoff-budget/result.md) |
| [10-paper mobile-manipulation batch assessment](20261125-paper-batch-mobile-manipulation.md) | manipulation (cross: perception, mobile) | which segmentation/6D-pose/VLA components to prototype offline; what to reject or defer | reviewed (self-review only); independent review pending | MVE-0…3 designed in §11; not run |
| [SAM 3 in the SST open-source repo + ArmPi attempt route](20261126-sam3-sst-open-source-attempt-route.md) | perception | whether/how to adopt SAM3-class open-vocabulary segmentation: offline-first route, 6 GB gates, fallback to SAM2.1 | draft; review pending | [MVE-0…3 designed](../experiments/20261126-sam3-6gb-feasibility/design.md); not run |
| [AGX Orin SAM3 + Qwen deployment](20261126-agx-orin-sam3-qwen-deployment.md) | perception | whether AGX Orin is the SAM3+Qwen host, which stack/model size, and what to probe first | draft; Qwen3-VL-8B + SAM3 3.0 run; shelf calibration and 100-frame pipelines; judge template-sensitive (fix T1+score>=0.8; 18-case 15/15; 200-frame 182/183 = 99.45%, 1 edge FN); advisory service 30-min soak 180 req, 0 error, RSS +3 MB; 500-request test 0 error, p95 3.77 s (G4 p95<1.5 s not met), RSS +3 MB; 500 unique frames over laptop→Orin Wi-Fi 0 error, p50 2.15 s / p95 3.74 s, RSS plateau; two-camera 1 Hz capacity 0.519 req/s, 30% processed, p50 4.44 s | [MVE-0/MVE-1/MVE-2 run; MVE-3 partial; MVE-4 partial](../experiments/20261126-agx-orin-stack-probe/result.md) |
| [Piper X simulation data map](20261126-piper-x-simulation-data-map.md) | manipulation | which GitHub assets to pin, where they belong, and whether to open a CAN profile contract | draft; review pending | [MVE-0 asset materialisation; MVE-1 run](../experiments/20261126-piper-x-gazebo-plant/result.md) — MVE-1 has an open joint2/3 tracking failure; MVE-2…4 designed, not run |
| [RLinf PICO→Piper X data-collection assessment](20261126-rlinf-piper-pico-data-collection.md) | manipulation | whether RLinf is a viable PICO VR data-collection path for the AgileX Piper X, and what must be built/verified before a hardware session | draft; review pending | [MVE-0…3 designed](../experiments/20261126-rlinf-piper-pico-mve/design.md); not run |
| [Ultralytics repository review](20261126-ultralytics-repository-review.md) | perception | whether to keep Ultralytics as the perception detector backend/training tool, and under which license, version and runtime boundary | draft; review pending | [MVE-1…3 designed](../experiments/20261126-ultralytics-runtime-audit/design.md); not run |
| [Contact Harness — frozen-VLM contact-rich manipulation](20261128-contact-harness.md) | manipulation | whether to adopt, borrow or reject Contact Harness for contact-rich manipulation, and which part (if any) to prototype first | draft; review pending | MVE-0 (Contact-4 sim smoke test) and MVE-1 (harness-to-gateway mapping) designed in §11; not run |

Chinese edition: [GloVLA report DOCX](20261125-glovla-hybrid-factorization-eval.zh-CN.docx);
the Markdown report remains the traceable version.

## Task books and experiments

| Document | Theme | State | Report |
|---|---|---|---|
| [VP-VLA ArmPi task book](../experiments/20261125-vp-vla-armpi/design.md) | manipulation | pre-registered design; not run | none yet |
| [LingBot/SST MVE-0 re-analysis](../experiments/20261125-lingbot-sst-reanalysis/result.md) | manipulation | desk re-analysis run 2026-11-25 | LingBot-VLA / SST report above |
| [GloVLA handoff-budget MVE-0](../experiments/20261125-glovla-handoff-budget/result.md) | manipulation | desk calculation run 2026-11-25 | GloVLA report above |
| [Piper X Gazebo plant MVE-1](../experiments/20261126-piper-x-gazebo-plant/result.md) | manipulation | run 2026-11-26; A1–A5/A7 pass, A6 fails on joint2/joint3; mimic structural only | Piper X report above |
| [RLinf PICO→Piper X MVE-0…3](../experiments/20261126-rlinf-piper-pico-mve/design.md) | manipulation | pre-registered design; not run | RLinf report above |
| [Ultralytics runtime audit MVE-1…3](../experiments/20261126-ultralytics-runtime-audit/design.md) | perception | pre-registered design; not run | Ultralytics report above |
| [SAM3 6 GB feasibility MVE-0…3](../experiments/20261126-sam3-6gb-feasibility/design.md) | perception | pre-registered design; not run (MVE-0 blocked on HF gated weights) | SAM3 / SST report above |
| [AGX Orin stack probe MVE-0…4](../experiments/20261126-agx-orin-stack-probe/design.md) | perception | MVE-0/1/2 run; MVE-3 partial; judge template sensitivity found | AGX Orin report above |

## Themes with no report yet

- [system/](../references/system/README.md) — safety, arbitration, motion
  execution; no investigation report yet.
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
