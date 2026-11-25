# SST repository audit — Lingbot-Challenge-SST

- **Type**: source-code audit (static analysis; nothing executed)
- **Repository**: <https://github.com/YzmYalier/Lingbot-Challenge-SST>
- **Commit**: `8797aa31dd9798a6e931d57857f32cd5de372b6c` (main), pushed
  2026-11-19; created 2026-11-18. Five commits total (one squashed release plus
  four docs commits); second branch `page` holds the GitHub Pages site.
- **Size**: ~4,517 tree entries, ~17.5 MB repository size, 78 MB working tree;
  Python ~7.97 MB, CUDA ~349 KB, shell ~103 KB (GitHub languages API).
- **License**: **no root LICENSE**; GitHub API returns `license: null`. The
  vendored `Lingbot-vla-challenge/LICENSE` is Apache-2.0, and `RoboTwin/` and
  `sam3/` carry their own licenses. SST's own additions (`auto_mask/`, `tools/`,
  `inference/`, `data_inputs/`) therefore have no explicit grant.
- **Checkpoints**: not released; README badge says "Coming soon" and the report
  nav points to a placeholder. Only the 8.33 GiB dataset is released.
- **Read scope**: full README, configs, entry scripts, key source files, tests,
  `base.json`, `public_weights.json` documentation; no code was run, no model was
  downloaded, no GPU was used.

## Layout and call chain

```text
process_data.sh --stage raw      -> tools/rebuild_robotwin_v30_from_v21.py
process_data.sh --stage masks    -> auto_mask/pipeline_lerobot.py
                                    -> Qwen phrase extraction (vLLM)
                                    -> SAM3 service (sam3/tools/...)
                                    -> Qwen mask judge (sam3/tools/sam3_mask_judge.py)
                                    -> mask_style.py rendering
process_data.sh --stage assemble -> paired raw + SAM datasets
train.sh                         -> Lingbot-vla-challenge/train_multinode.sh
                                    -> tasks/vla/train_lingbotvla.py + recipe yaml
eval.sh                          -> script_sam.sh
                                    -> inference/cam_high_masker.py (online mask)
                                    -> policy server + RoboTwin env
```

## Code claims (file + symbol + line at the pinned commit)

| Claim | Location |
|---|---|
| Padding is excluded from both loss numerator and denominator; fp32 accumulation | `Lingbot-vla-challenge/lingbotvla/models/vla/lingbot_vla/action_loss.py:6-45` (`masked_action_loss`) |
| `mask_action_pad` selects the masked reduction | `.../modeling_lingbot_vla_v2.py:1297` |
| Module-wise LR with 7 modules, unknown-key validation, freeze at 0 | `.../optim/module_lr.py:29-125` (`MODULE_NAMES`, `resolve_module_lr_mult`, `freeze_zero_lr_modules`, `build_module_param_groups`) |
| Teachers read the unmasked source recorded in `sam_info.json`; episode counts must match | `.../data/vla_data/base_dataset.py:101-131`, `.../data/dataset.py:94` |
| Eval renders masks with the style recorded in the checkpoint's `sam_info.json` | `tools/evaluation_config.py:41-44` |
| Prompt is a hand-curated 73-line dictionary with per-category "MISSED" workarounds; always includes `robot, robot arm` | `vllm_space/sam3_prompt.py` (73 lines) |
| SAM3 detection thresholds | `auto_mask/pipeline_lerobot.py:100` (`score_threshold_detection=0.3`, `new_det_thresh=0.5`) |
| Judge: two-image yes/no question, logprob ratio, threshold 0.5, regrow re-judge | `sam3/tools/sam3_mask_judge.py:37-45,109`; `auto_mask/pipeline_lerobot.py:1174,1194` |
| Repair verifies PTS (`frame.pts * time_base == i/fps`), SHA-256 and content hash | `tools/rebuild_robotwin_v30_from_v21.py:119,145-155,326` |
| Data provenance: 2,500 episodes, 548,893 frames, 250,000 slots, exact float32 match | `data_inputs/preparation_report.json` |

## Engineering quality

- **Strong**: data provenance (SHA-256, manifests, `validation_summary.json`),
  explicit validation limits, correct padding-mask math, eval style read from the
  checkpoint, startup checks for episode-count mismatch, tests for numerical
  identity and LR grouping.
- **Weak for reuse**: `base.json` contains machine-specific interpreter paths
  (`/home/pc/miniconda3/...`, `/usr/local/cuda-13.0`, `/data1/szh/...`); four conda
  environments; a vLLM source build pinned to v0.20.2 (`bc150f5`); ~103 GB of
  weights/inputs; evaluation adds a mask-Qwen service and a SAM3 service to the
  policy (their evidence header records 8 GPU × 4 slots for policy+simulator). No
  CI and no `.github` directory.
- **Tests**: 10 files in `Lingbot-vla-challenge/tests/`, 3 in `tests/`, 3 in
  `auto_mask/`; mostly CPU data-integrity and unit tests, none end-to-end on GPU
  or on the robot.
- **Docs vs code**: the `page` branch `blog.md` is a stale draft (duplicated §7,
  numbers that differ from the published page); the published `index.html` and
  `data/results.csv` are the consistent sources. `inference/cam_high_masker.py`
  still documents a default `outside_scale=0.2`, while the final dataset and eval
  use 0.1 + 2 px outline (the eval path overrides the default).

## Executed vs inferred

- **Executed**: none of SST's code. The only computation performed here is the
  statistical re-analysis of their published counts
  (`experiments/20261125-lingbot-sst-reanalysis/`).
- **Static**: all file/line claims above.
- **Inferred**: the real-robot final's solution is not in this repository; the
  released experiments are the RoboTwin preliminary track. No claim is made about
  the final's real-robot stack.
