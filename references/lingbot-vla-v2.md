# LingBot-VLA 2.0 — paper, repository, weights, and the SST derivative

- **Type**: primary paper + official repository + model weights + competition derivative
- **Accessed**: 2026-11-25
- **Read scope**: paper abstract and HTML body (the HTML body was checked for
  RoboTwin content and does **not** contain it); official README, `robotwin.yaml`,
  and `assets/training_data/robotwin.txt` read directly from `main`; SST report
  page and repository read separately (see `sst-repo-audit.md`). The full PDF was
  not read end to end.

## Primary paper

- Wu, Wang, Lu, Sun, Liu, Wang, et al. *From Foundation to Application:
  Improving VLA Models in Practice* (LingBot-VLA 2.0). arXiv:2607.06403,
  v1 2026-07-07. <https://arxiv.org/abs/2607.06403>
- Claimed contributions (abstract/HTML): ~60,000 h pretraining data (50,000 h
  robot trajectories over 20 embodiments + 10,000 h egocentric human video);
  55-dimensional canonical state/action vector; sparse-MoE action expert;
  dual-query distillation from LingBot-Depth (geometry) and DINO-Video (temporal).
- Reported benchmarks in the paper: GM-100 (AgileX Cobot Magic average success
  34.4%, Galaxea R1Pro 15.6%; the progress/success split is from a search summary,
  not re-read in the HTML), long-horizon mobile manipulation, LARYBench. The paper
  body does **not** report RoboTwin 2.0 numbers.
- Stated limitations (HTML body): uneven task progress; embodiment factors
  (kinematics, camera viewpoints, action-space alignment) remain hard; OOD
  degradation.

## Official repository

- <https://github.com/Robbyant/lingbot-vla-v2>, Apache-2.0, accessed 2026-11-25.
- README exact text: "Below we use **RoboTwin 2.0** 50 tasks, trained with clean
  and randomized data together, as an example." (README line 138; repeated at
  line 146.)
- RoboTwin post-training table (README line 164): Muon **93.52 clean / 92.80
  randomized**, 5.93 s/it. The comparison columns are π0.5 (82.74/76.76) and
  LingBot-VLA 1.0 (88.56/86.68) (README lines 251–252).
- Data list `assets/training_data/robotwin.txt`: per task, one
  `*_randomized_500-1000` entry plus one `*_clean_50-50` entry. So the 92.80
  randomized number uses a randomized pool named `*_randomized_500-1000`
  (500–1,000 demonstrations per task; the list does not state the exact count)
  plus 50 clean demonstrations per task — at least 10× the clean-only budget
  the competition allows.
- Evaluation caveat (README line 190): "Release validation of the published
  checkpoint uses **FP32 inference**; BF16 uses less GPU memory, but can produce
  materially different success rates."
- Released weights: `robbyant/lingbot-vla-v2-6b` (native depth) and
  `robbyant/lingbot-vla-v2-6b-robotwin` (2026-07-25).
- Real-robot inference latency: ~130 ms on an RTX 4090D with 10 denoising steps
  and `--use_length 25` (README deployment section).

## Competition derivative (SST)

- Report: <https://yzmyalier.github.io/Lingbot-Challenge-SST/>
- Code: <https://github.com/YzmYalier/Lingbot-Challenge-SST>, commit
  `8797aa31dd9798a6e931d57857f32cd5de372b6c`.
- Dataset: <https://huggingface.co/datasets/yydsyangsdyy/Lingbot-Challenge-SST>,
  revision `7111c726e5f45e045e5ead62816a1d175a826a9e`.
- SST trains on `demo_clean-50` only (2,500 episodes), which is the competition
  constraint (see `competition-rules.md`). Its baseline and final model are
  therefore not comparable to the official clean+randomized recipe.

## Relevance to JCHENG

The upstream repository (Apache-2.0) is the only legally reusable part. SST's own
additions have no root license. The 93.52/92.80 numbers are evidence that
additional randomized demonstrations, not foreground prompting, are the dominant
lever when the data budget is not constrained.
