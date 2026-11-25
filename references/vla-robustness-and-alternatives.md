# VLA robustness, action chunking, and alternative policy families

- **Type**: primary papers (abstracts; one full HTML for LIBERO-Plus? no — search
  summary) and official repositories
- **Accessed**: 2026-11-25
- **Read scope**: abstracts and search-index summaries; full PDFs were **not** read
  for RTC, SAM2Act, DP3, π0, or LIBERO-Plus. Treat mechanism claims as B-grade and
  numbers as the authors' reported values, not independently verified.

## LIBERO-Plus — VLA robustness

- Fei, Wang, Shi, et al. *LIBERO-Plus: In-depth Robustness Analysis of
  Vision-Language-Action Models*. arXiv:2510.13626, 2025.
  <https://arxiv.org/abs/2510.13626>
- 10,030 tasks across seven perturbation dimensions: object layouts, camera
  viewpoints, robot initial states, language instructions, lighting, background
  textures, sensor noise.
- Headline: models reporting >95% on LIBERO drop below 30% under modest
  perturbations; camera viewpoint and initial state are the most damaging;
  models largely ignore language; evidence of trajectory memorization.
- **Relevance**: supports the premise that appearance/viewpoint shift is a real
  failure mode, and cautions that benchmark success can be brittle. It also
  suggests that an instruction-conditioned visual prompt may help by injecting
  language into the input, which is a hypothesis SST did not isolate.

## Real-Time Chunking (RTC)

- Black, Galliker, Levine. *Real-Time Execution of Action Chunking Flow
  Policies*. arXiv:2506.07339, NeurIPS 2025.
  <https://arxiv.org/abs/2506.07339>
- Frames real-time execution as inpainting: freeze the prefix that will execute
  during inference and inpaint the rest; soft masking over overlapping actions;
  asynchronous execution; no retraining.
- **Relevance**: SST's conclusion "pick one execution length; 50 is best overall"
  is a static compromise. RTC is the standard alternative when latency and chunk
  boundaries matter, and it would likely beat any single execution length. SST
  did not test it; the competition's inference strategy was allowed.

## SAM2Act — segmentation backbone, not mask preprocessing

- Fang, Grotz, Pumacay, et al. *SAM2Act: Integrating Visual Foundation Model with
  a Memory Architecture for Robotic Manipulation*. arXiv:2501.18564, ICML 2025.
  <https://arxiv.org/abs/2501.18564>
- Uses the SAM 2 **encoder** as the visual backbone of a multi-view transformer
  policy, plus a memory bank (SAM2Act+); 86.8% average on 18 RLBench tasks; 4.3%
  gap under The Colosseum perturbations.
- **Relevance**: an alternative to running SAM 3 + a 27B judge at test time. It
  changes the representation once, at training time, and adds no per-frame
  segmentation service. For JCHENG this is a more plausible architecture than
  SST's pipeline, though still a research track.

## DP3 — 3D diffusion policy

- Ze, Zhang, Zhang, et al. *3D Diffusion Policy: Generalizable Visuomotor Policy
  Learning via Simple 3D Representations*. arXiv:2403.03954, 2024.
  <https://arxiv.org/abs/2403.03954>
- Sparse point clouds + point encoder + diffusion policy; 10 demonstrations
  suffice for most of 72 simulated tasks (24.2% relative improvement over
  baselines); 85% real-robot success with 40 demonstrations; generalization across
  space, viewpoint, appearance and instance.
- **Relevance**: the most practical learned-policy alternative for a depth-equipped
  cell (D435i). It uses geometry instead of appearance, so appearance shift is less
  damaging, and it does not need a 6B VLA or a 27B judge. It still needs reliable
  demonstrations and action labels, which JCHENG does not currently have.
- **Caveat from the RoboTwin paper**: "DP3's strong results partly stem from
  perfect point clouds and clean background segmentation in simulation." Real
  D435i point clouds have holes, noise and missing segments, so DP3's simulated
  advantage should be discounted before committing to it.

## π0 — flow-matching VLA lineage

- Black, Brown, Driess, et al. *π0: A Vision-Language-Action Flow Model for
  General Robot Control*. arXiv:2410.24164, RSS 2025.
  <https://arxiv.org/abs/2410.24164>
- VLM backbone + separate flow-matching action expert; trained across multiple
  robot platforms; fine-tuned for new skills. The abstract does **not** state the
  chunk length or control frequency; those were not verified here.
- **Relevance**: LingBot-VLA 2.0's action expert and dual-system design are in this
  lineage. Cite it for architecture context only.

## Domain randomization

- Tobin, Fong, Ray, et al. *Domain Randomization for Transferring Deep Neural
  Networks from Simulation to the Real World*. arXiv:1703.06907, IROS 2017.
  <https://arxiv.org/abs/1703.06907>
- Randomize rendering during training so the real world looks like another
  variation; a detector trained only on simulated RGB transferred to real
  localization (1.5 cm) and grasping in clutter.
- **Relevance**: the clean+randomized RoboTwin recipe is a direct application. If a
  project can generate or collect diverse data, this is the dominant lever and it
  is simpler than test-time masking.
