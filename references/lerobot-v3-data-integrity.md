# LeRobot v3.0 data integrity — external corroboration

- **Type**: issue tracker (secondary but primary-adjacent: maintainers' and users'
  reproductions)
- **Accessed**: 2026-11-25
- **Read scope**: issue pages were read through a search-index summary, not opened
  individually. Treat as B-grade corroboration; the SST repair code is the
  A-grade primary evidence for the specific RoboTwin defect.

## What is documented

- **huggingface/lerobot issue #5039** — `lerobot/berkeley_autolab_ur5` v3.0:
  28 of 31 video files are missing their last episode; episode metadata assigns
  the missing episode to a file with `from_timestamp`/`to_timestamp` past the end
  of the video. Example error: `Invalid frame index=3839 ... must be less than
  3839`; in every short file the gap equals the length of the last episode
  assigned to that file.
  <https://github.com/huggingface/lerobot/issues/5039>
- **Good First Issue tracker #5187 (DATA-04)** — the same class affects 12
  datasets (`aloha_mobile_*`, `berkeley_rpt`, `stanford_hydra_dataset`,
  `taco_play`, `toto`, `utaustin_mutex`, ...). Root cause attributed to converter
  code removed in commit `59d108a80`: at rollover, the current episode's metadata
  was written against the old file, and the next file started with that episode.
  <https://github.com/huggingface/lerobot/issues/5187>
- **PR #5051** — adds a load-time check; issue #2189 is the original crash report.
- A separate frame-exact slicing bug is documented in Hebbian-Robotics/hflow
  commit `720329dc`: a stream-copied slice at a non-keyframe boundary can drop
  frames, and a window ending exactly on a frame boundary can pull in the next
  episode's first frame (source end timestamps are exclusive); one corpus showed
  226 vs 227 access units.

## Why this matters

SST claims the **official RoboTwin LeRobot v3.0** release has episodes whose last
frames bleed into the next episode, and that v2.1 is correct. That exact claim is
the authors' own (A for their code/report), but the **bug class is independently
documented in LeRobot**. The SST repair (`tools/rebuild_robotwin_v30_from_v21.py`)
rebuilds videos from v2.1 while preserving v3.0 episode IDs and state/action
bytes; `data_inputs/preparation_report.json` records 2,500 episodes, 548,893
frames, 250,000 instruction slots, and "exact full chronological state/action
float32 bytes and shapes" matching.

## Relevance to JCHENG

Any future imitation dataset assembled from LeRobot (or any segmented video)
should ship three checks before training: (1) decoded frame count equals the
parquet row count per episode; (2) PTS is monotonic and equals `i/fps`;
(3) first/last frame decode and a content hash. These are cheap and catch the
documented failure class. The SST tool is a good reference implementation, but it
is unlicensed (see `sst-repo-audit.md`).
