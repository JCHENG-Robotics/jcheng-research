# Experiment design — LingBot/SST re-analysis and follow-ups

- **Date**: 2026-11-25
- **Status**: MVE-0 **run** (desk re-analysis); MVE-1 and MVE-2 **not run**
- **Owner**: J. Cheng (decision), ZCode (analysis)
- **Related report**: `reports/20261125-lingbot-vla-sst-foreground-prompting.md`

## MVE-0 — Are the SST stage gains distinguishable from noise? (run)

1. **Hypothesis**: at 50 episodes/task, the intermediate stage gains (+2–3 pp) are
   within sampling noise; only the foreground-replacement jump and the data-repair
   gain at equal steps survive a two-proportion test.
2. **Baseline**: the previous stage in the N0→N5 chain, and N4 at 30k for the
   data-repair comparison at equal training steps.
3. **Variables**: stage (N0…N5), scene (clean/randomized). Controlled: published
   counts, same benchmark, same evaluation harness.
4. **Environment**: no GPU, no robot; Python 3.12 stdlib only; inputs are the
   derived counts in `data/`.
5. **Metrics**: success rate, Wilson 95% CI, unpaired two-proportion z-test
   (optimistic: ignores task clustering), per-task delta distribution.
6. **Acceptance**: the direction and magnitude of the published stage deltas are
   reproduced; a stage is called "established" only if p < 0.05.
7. **Failure criteria**: if the counts do not reconcile with the published rates,
   or the test contradicts the published direction, stop and re-check the input.
8. **Recording**: `analysis.py`, `logs/analysis.txt`, `data/*.csv`, `result.md`.
9. **Rollback**: none needed (read-only desk analysis).

## MVE-1 — Does foreground conditioning help a small policy? (not run)

1. **Hypothesis**: on a 2-task RoboTwin subset, a small BC policy trained with
   instruction-conditioned foreground dimming beats the same policy trained on raw
   images in `demo_randomized`, and is not worse than photometric domain
   randomization.
2. **Baseline**: raw images; second control: photometric augmentation only.
3. **Variables**: input pipeline (raw / foreground-dim / photometric DR);
   controlled: policy, data, seeds, training steps, evaluation protocol.
4. **Environment**: RoboTwin 2.0 simulation, 2 tasks, 50 clean demos/task, 100
   trials/task, fixed seeds; a small ACT or DP3 policy (~10–30M parameters) on one
   consumer GPU. **Not executed.**
5. **Metrics**: success rate per scene; paired McNemar test on identical seeds;
   clean-scene regression; mask-service latency (if used online).
6. **Acceptance**: foreground ≥ +5 pp over raw in randomized with p < 0.05, and
   clean drop ≤ 2 pp. A secondary acceptance: foreground ≥ DR (non-inferior).
7. **Failure criteria**: no randomized gain, or clean drop > 2 pp, or the gain
   disappears when the mask is made instruction-independent (which would indicate
   that the effect is augmentation, not instruction conditioning).
8. **Recording**: fixed seeds, per-episode CSV, raw `stats` files, config hashes.
9. **Rollback**: keep the raw-image policy; do not add a mask service.

**Critical ablation not run by SST**: replace the instruction-conditioned mask with
(a) the same mask for every instruction, and (b) a random-object mask. If the gain
survives (a), it is a foreground/augmentation effect; if it disappears, the gain is
instruction conditioning through pixels. SST's `single` vs `multi` comparison is
consistent with both explanations.

## MVE-2 — Data-integrity gate for a future JCHENG demo set (not run)

1. **Hypothesis**: a 10-episode sample from any future LeRobot-style demo set can
   be validated for frame/row alignment, PTS monotonicity, first/last-frame decode
   and padding masks before training.
2. **Baseline**: the dataset as delivered.
3. **Variables**: none (validation only).
4. **Environment**: CPU; `ffmpeg`/PyAV; no robot.
5. **Metrics**: number of episodes with frame-count ≠ parquet rows; PTS violations;
   decode failures; padded-action count.
6. **Acceptance**: zero mismatches on the sample; all padded positions masked in
   the loader.
7. **Failure criteria**: any mismatch → do not train; repair or drop the episode.
8. **Recording**: per-episode JSON + a summary; keep the checker in the data repo,
   not in `jcheng-research`.
9. **Rollback**: n/a (read-only check).

## MVE-3 — Paired re-evaluation of SST checkpoints (blocked)

If the SST checkpoints are released, re-evaluate N4 and N5 at 30k on identical
seeds, 100 episodes/task, and use McNemar's test on paired outcomes. This is the
only way to settle whether the +3.98 pp data-repair gain is real at the per-episode
level. Blocked: checkpoints are not released as of 2026-11-25.
