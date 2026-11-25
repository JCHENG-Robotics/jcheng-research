# Manipulation（操作）

Theme owner: [`jcheng-manipulation`](https://github.com/JerichoCheng/jcheng-manipulation)
(frozen v1.0.0 baseline) plus the ArmPi Ultra arm and gripper. Motion still
executes only through `jcheng-system` `ExecuteMotion`; a source filed here never
grants motion authority.

Scope: VLA models and training, action chunking, grasp and handoff, arm and
gripper control strategies, adapting learned policies to the 5-DoF platform.

| Record | Source | Access | Local copy |
|---|---|---|---|
| [glovla.md](glovla.md) | GloVLA (arXiv:2609.06256) | 2026-11-25 | [papers/20261125-glovla.pdf](papers/20261125-glovla.pdf) |
| [lingbot-vla-v2.md](lingbot-vla-v2.md) | LingBot-VLA 2.0 (arXiv:2607.06403) | 2026-11-25 | — |
| [vp-vla.md](vp-vla.md) | VP-VLA (arXiv:2603.22003) | 2026-11-25 | [papers/20261125-vp-vla.pdf](papers/20261125-vp-vla.pdf) |
| [vla-robustness-and-alternatives.md](vla-robustness-and-alternatives.md) | LIBERO-Plus, RTC, SAM2Act, DP3, π0 | 2026-11-25 | — |
| [fine-tuning-and-judge-bias.md](fine-tuning-and-judge-bias.md) | ULMFiT; LLM-as-a-judge bias | 2026-11-25 | — |
| [sst-repo-audit.md](sst-repo-audit.md) | `YzmYalier/Lingbot-Challenge-SST` audit | 2026-11-25 | — |

Cross-theme records used by this theme:
[SAM 3](../perception/sam3.md) (perception),
[RoboTwin 2.0](../datasets-benchmarks/robotwin-2.md),
[LeRobot v3.0 data integrity](../datasets-benchmarks/lerobot-v3-data-integrity.md) and
[competition rules](../datasets-benchmarks/competition-rules.md) (datasets-benchmarks).

Filing and naming rules: [references/README.md](../README.md).
