# Result — MVE-0 re-analysis (run 2026-11-25)

**This is a desk re-analysis of published counts, not a robot experiment and not a
re-evaluation of the checkpoints.** Inputs: `data/main_chain_counts.csv` and
`data/per_task_n0_n5.csv`, derived from the SST report's `data/results.csv` and
`data/evidence.json` at commit `8797aa31`. Reproduce with
`python3 -I analysis.py`; raw output in `logs/analysis.txt`.

## Main chain

| Stage | Clean (95% Wilson) | Randomized (95% Wilson) |
|---|---|---|
| N0 15k | 77.14 [75.96, 78.28] | 36.20 [34.88, 37.54] |
| N1 15k | 78.04 [76.37, 79.62] | 47.84 [45.89, 49.80] |
| N2 15k | 75.96 [74.25, 77.59] | 50.84 [48.88, 52.80] |
| N3 15k | 76.52 [74.82, 78.14] | 53.12 [51.16, 55.07] |
| N4 15k | 78.20 [76.54, 79.77] | 55.36 [53.40, 57.30] |
| N4 30k | 80.88 [79.29, 82.37] | 54.24 [52.28, 56.18] |
| N5 30k | 81.86 [80.77, 82.90] | 58.22 [56.85, 59.58] |

## Stage tests (unpaired, optimistic)

| Comparison | Δ randomized | p | Verdict |
|---|---:|---:|---|
| N0→N1 foreground replacement | +11.64 pp | < 0.0001 | established |
| N1→N2 review + 0.1 rendering | +3.00 pp | 0.034 | marginal |
| N2→N3 raw teachers + FG weight | +2.28 pp | 0.107 | not established |
| N3→N4 module-wise LR | +2.24 pp | 0.112 | not established |
| N4@30k→N5 data repair | +3.98 pp | 0.001 | established |

The same N3→N4 effect appears at 25k (53.00% → 55.24%, +2.24 pp, p ≈ 0.11). Two
checkpoints with the same direction and magnitude are suggestive (Stouffer
Z ≈ 2.25, p ≈ 0.02 if treated as independent), but this is not a paired test and
the two runs are not independent samples of the same checkpoint.

Clean scene: no stage change is significant at p < 0.05; N1→N2 is −2.08 pp
(p = 0.081).

## Per-task structure

**Clean (N0 15k → N5 30k)**: mean +4.72 pp, median +1.0 pp; 29 tasks improved,
16 worse, 5 unchanged. `click_bell` 5→98 and `click_alarmclock` 34→96 contribute
155 of 236 extra successes (**66% of the clean gain**). Worst: `stack_blocks_three`
−13, `beat_block_hammer` −10, `move_stapler_pad` −10, `place_mouse_pad` −9,
`place_fan` −8.

**Randomized**: mean +22.02 pp, median +19.0 pp; 46 tasks improved, 3 worse, 1
unchanged. Top: `stack_bowls_two` +57, `open_laptop` +48, `place_fan` +47,
`stack_bowls_three` +46, `handover_mic` +43. Worst: `place_burger_fries` −11.

## Interpretation

1. The foreground-replacement gain is large enough to survive clustering concerns
   (z ≈ 9.6); it is the one robust result.
2. The intermediate +2–3 pp steps are at or below the noise floor at 50
   episodes/task. The report's narrative "each stage adds a few points" is not
   statistically established.
3. The clean headline is not a broad improvement; it is dominated by two click
   tasks that the padding/frame repair fixes. The randomized improvement is broad.
4. These numbers cannot settle causality for N5: the repair combined two changes
   (padding mask, frame alignment) and changed the data pipeline; the 30k N4 vs
   30k N5 comparison is the cleanest available, but still not paired.

## What this does not establish

- No statement about the real robot; the data are simulation only.
- No statement about SST's checkpoints; they are not released.
- No correction for multiple comparisons across the 77 published runs.
