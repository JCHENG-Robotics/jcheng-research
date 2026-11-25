# Competition rules — Robbyant Embodied AI Challenge (preliminary, RoboTwin track)

- **Type**: secondary source (Tianchi forum post), read via search summary
- **Accessed**: 2026-11-25
- **Read scope**: the forum page body was **not retrievable** (JavaScript-rendered;
  only title/metadata returned). The rules below are from a search-engine summary
  of the post and are therefore **B-grade**, not A-grade. The rulebook PDF was not
  accessed.
- **URL**: <https://tianchi.aliyun.com/forum/post/1081761>

## Rules as summarized

| Item | Rule |
|---|---|
| Training data | RoboTwin 2.0 Aloha-AgileX 50 tasks, **clean** data only: 50 trajectories per task, 2,500 demos |
| `demo_randomized` | Evaluation only; **prohibited** for training |
| External data | Prohibited (real-robot, third-party robot datasets, etc.) |
| Supervision | Must come from official clean demonstrations |
| Evaluation | 100 trials/task, `demo_clean` (easy) and `demo_randomized` (hard) |
| Allowed techniques | training parameters, training strategy, pixel-level augmentation (brightness/color/noise/blur/cutout/JPEG), state perturbation, data filtering, instruction replacement within the seen pool, statistical reweighting, model structure, inference strategy |
| Blacklisted | background swapping, object-level CutMix/Copy-Paste, geometry changes, re-lighting, generative models creating new observations, semantic tampering |
| Compliance test | data must come from RoboTwin release assets; learning must stay within behavior cloning with supervision from demonstrations |

## Consequences

1. The SST recipe is a **clean-only** solution. Its 58.22% randomized result is not
   comparable to the official clean+randomized 92.80%; the latter uses at least
   500 randomized demos per task and is forbidden in the competition.
2. SAM foreground replacement is pixel-level processing of the official demos and
   uses no new environment data. Whether it counts as allowed "data processing"
   or as blacklisted "semantic tampering" is a gray area; the team's result was
   accepted by the organizers, but this review found no written ruling. Treat
   compliance as **C-grade inference**.
3. For JCHENG the rule is irrelevant except as an explanation of why SST chose a
   clean-only budget. A real project is not bound by it and should compare against
   the clean+randomized recipe before investing in input masking.
