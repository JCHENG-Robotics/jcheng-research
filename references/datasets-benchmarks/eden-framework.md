# Eden (embodied-ai-nexus) — source record

- **Source group**: `embodied-ai-nexus/Eden` (code, docs, releases, PyPI) and
  the related `Genesis-Embodied-AI/genesis-world` README listing.
- **Access date**: 2026-11-28.
- **Version / commit**: Eden `v0.1.1`, PyPI `eden-world==0.1.1`, repository
  commit `a52315871572` (2026-11-27), tag `v0.1.1` =
  `1a39eb9205f94b6f8c0983fb8ace89d1353aae72`; `genesis-world` head
  `beae8af2af4a29f6c1873db0aa2c7421c5782eef` (2026-11-27).
- **URLs**: <https://github.com/embodied-ai-nexus/Eden>,
  <https://embodied-ai-nexus.github.io/Eden/>,
  <https://pypi.org/project/eden-world/>,
  <https://github.com/Genesis-Embodied-AI/genesis-world>.

## What was read

Full text:

- `README.md`, `AGENTS.md`, `pyproject.toml`, `LICENSE` (presence and type),
  `.github/workflows/ci.yml`, `eden/tasks/__init__.py`,
  `eden/extensions/deployment/__init__.py`.
- Documentation at the commit above: `docs/guides/deployment.md` (including
  "The operator state machine" and "Safety"),
  `docs/guides/deployment-hardware.md`, `docs/getting-started/installation.md`,
  `docs/getting-started/assets.md`, `docs/tasks/index.md`,
  `docs/api/options/robots.md`, `docs/api/terms/catalog.md` (generated).
- Release notes for `v0.1.1`; PyPI JSON metadata for `eden-world`.

Partial:

- `eden/extensions/deployment/base.py` (head only; the file is 145 KB),
  `eden/extensions/deployment/unitree_dds.py` (head only).
- `genesis-world` `README.md` (the section listing Eden) and the commit history
  around commit `3a6c9877` ("List Eden in the README as an application built on
  Genesis", 2026-11-17).

Metadata only (GitHub REST API): repository metadata, tags, releases, commits,
contributors, open issues, recursive tree (2,782 entries, not truncated).

## What was not read or run

- The full `eden/` source tree (975 Python modules); test bodies; solver,
  manager and task implementations.
- Any Isaac Lab, mjlab, ManiSkill or LeRobot source.
- Eden was **not installed**, no task was built, no training or ONNX export was
  run, no DDS domain or robot was touched.
- No Eden paper exists; the citation block is a `@misc` entry. An arXiv API
  query on 2026-11-28 returned no matching paper.

## Facts recorded

- Owner `embodied-ai-nexus` (created 2026-03-19, one public repository); main
  author `Kashu7100` (Kashu Yamazaki, CMU). 345 stars, 22 forks, 15 open
  issues, ~30 commits on `main`, 3 contributors (2026-11-28).
- Apache-2.0 code; assets (robots, objects, scenes, policy checkpoints, motion
  datasets) download from the Hugging Face Hub on first use into
  `~/.cache/eden/assets/`; the assets page states no per-asset licence.
- Hard pin `genesis-world==1.4.7`; `torch>=2.9.2`; Python `>=3.12,<3.14`;
  Linux x86_64 + NVIDIA GPU is the primary platform.
- 7 hardware deployment backends (Unitree G1/Go1/Go2, LimX Oli, Franka
  Panda/FR3, RoboTera XHand, Wuji Hand 1/2) plus MuJoCo sim-to-sim; vendor
  SDKs, no ROS 2 dependency and no ROS 2 package in the tree.
- Deployment uses a shared INIT/START/STOP/KILL operator state machine; the
  safety section documents that a stalled control thread keeps republishing
  the last command, so a receive-side watchdog does not engage.
- Local host at access date: RTX 3060 Laptop GPU, 6144 MiB, driver 595.99.02,
  compute capability 8.6; Python 3.12.3; ROS 2 Jazzy.

## Used by

- [Eden report](../../reports/20261128-eden-genesis-robot-learning-framework.md)
  (draft, 2026-11-28).
