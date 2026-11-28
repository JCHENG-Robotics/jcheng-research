# Eden (embodied-ai-nexus): a Genesis-based robot-learning framework — what it is, what it is not, and whether it fits JCHENG

> Report status: **draft**. Date: 2026-11-28.
> Author: ZCode research agent. Reviewer: pending.
> Decision this informs: whether Eden should enter the JCHENG stack as an
> offline training/simulation tool, be kept as a design reference only, or be
> rejected for the fixed-cell Piper program.
> Research boundary: public GitHub API and repository files at commit
> `a52315871572` (2026-11-27), PyPI metadata, the project's documentation
> pages, and local host facts. **No install, no training run, no benchmark
> reproduction, no DDS/robot session, no Isaac Lab source review.** The project
> moves daily; every repository claim is pinned to the stated SHA.

## 01. Executive Summary

**Eden is real, substantial, and not a Genesis-team product.** It is
`embodied-ai-nexus/Eden`, Apache-2.0, at `v0.1.1` (2026-11-19), built on
`genesis-world==1.4.7` by a one-repository organisation created 2026-03-19 and
authored mainly by Kashu Yamazaki (CMU PhD student, GitHub `Kashu7100`). The
Genesis project lists Eden in its own README as "one example of the application
layer" (commit `3a6c9877`, 2026-11-17), and Yamazaki has commits in
`genesis-world`; that is the likely origin of the "Genesis team" description.
Eden is an application built on Genesis, not a Genesis-org deliverable. (A)

**Technically it is a serious GPU-RL framework, not a thin demo.** 975 Python
modules under `eden/`, 752 test files, 66 registered tasks, 21 published-policy
adapters, 7 real-robot deployment backends, one Pydantic task config, Genesis
multi-physics plus the Mochi coupled solver, and ONNX/TorchScript export. (A)

**It does not fit JCHENG as a runtime component.** There is no ROS 2 package,
launch file or `rclpy`/`rospy` dependency; deployment speaks vendor SDKs
(Unitree CycloneDDS `rt/lowstate`/`rt/lowcmd`, `panda_py`, `limxsdk`,
`xhand_controller`, `wujihandpy`). It ships its own INIT/START/STOP/KILL
operator state machine, not the `ExecuteMotion` + lease + stop-latch boundary.
Its own documentation records a failure mode JCHENG forbids: a stalled control
thread keeps republishing the last command, so a receive-side watchdog never
engages. Eden supports **no Piper or ArmPi** asset. (A)

**The binding local constraint is 6 GB of VRAM.** This workstation's
"RTX 3060" is a **Laptop GPU with 6144 MiB**, not 8 GB (S, `nvidia-smi`
2026-11-28). Eden's quick start defaults to 4096 parallel environments — a
datacenter-GPU setting. Any local evaluation must be sized for 6 GB, and
camera-rendering tasks are the first to fail. (S for the hardware fact; C for
the consequence.)

**Recommendation: keep Eden as a design reference, not a dependency.** Do not
adopt it as a runtime, do not use its deploy path on the fixed cell, and do not
add it to `jcheng-learning`/`jcheng-simulation` before a concrete RL (not VLA)
need exists. If that need appears, run the MVE in §11 first — Piper URDF build,
256-env training, ONNX export on 6 GB — and gate adoption on the result.

## 02. Research Questions

The request: investigate Eden, described as "the Genesis team's open-source
robot-learning framework".

Sub-questions that make it answerable:

1. **Provenance** — who owns Eden, what is its relationship to Genesis, and is
   the "Genesis team" attribution correct?
2. **Substance** — what is actually implemented, at which version and commit,
   and which headline numbers are verifiable from code/docs rather than README?
3. **Maturity and governance** — release cadence, API stability, test/CI
   coverage, contributor concentration, issue load, licensing.
4. **Safety and integration** — how does it command real hardware, and does
   that respect JCHENG's motion authority, DDS domains and lease semantics?
5. **Fit** — which JCHENG layer could consume it, at what compute and
   maintenance cost, and what is the rollback path?
6. **Decision** — adopt, reference, defer or reject, and what minimum
   experiment would change the answer.

Constraints: no hardware session; no long unattended install (the torch/Genesis
stack is multi-GB); no DDS domain 0/41/42 traffic; no changes to any runtime
repository; the investigation must stay inside `jcheng-research/`.

Deliverable: this report plus a source record under
`references/datasets-benchmarks/eden-framework.md`, with a graded recommendation
and an unrun MVE design.

## 03. Current System Analysis

JCHENG is a layered ROS 2 ecosystem, not a single simulator:

- **L2 `jcheng-system`** is the only origin of motion (`ExecuteMotion`), with
  lease, deadman, limit and stop-latch enforcement. L3 capabilities publish
  intent only; L4 consoles use HTTP/WS and join no DDS domain. Domains are 0
  vendor, 41 privileged, 42 capability, 43 simulation
  (`jcheng-robotics/AGENTS.md` §3, §8).
- **`jcheng-learning`** is offline-only (datasets, training, policy artifacts);
  its M3 skill-intent surface only proposes to the system layer.
- **`jcheng-simulation`** is an offline plant on domain 43 (deterministic mock +
  Gazebo Harmonic arm/camera/LiDAR), never imported by a runtime repository.
- **`jcheng-benchmark`** is an offline, read-only harness; no hardware/DDS path.
- The current manipulation program is a fixed cell with a Piper-class execution
  arm; the older ArmPi Ultra baseline is frozen. Either way, Eden supports
  neither robot out of the box.

Host toolchain on this machine: ROS 2 Jazzy only, Python 3.12.3, NVIDIA GeForce
RTX 3060 **Laptop** GPU with **6144 MiB**, driver 595.99.02, compute capability
8.6. Robots run Humble; host tools and CI use Jazzy.

The relevant question is therefore narrow: Eden is a **Python/GPU RL world**,
while JCHENG's runtime is a **ROS 2 safety-and-intent graph**. The only
non-conflicting slot is offline training/simulation, outside the dependency
graph — the same slot `jcheng-learning`, `jcheng-simulation` and
`jcheng-benchmark` already occupy.

## 04. Research Methodology

Search and retrieval, 2026-11-28:

- Web search for the Chinese/English framing "Genesis team Eden robot learning
  framework"; the search tool returned AI-generated summaries without stable
  links, so **none of those summaries is cited as evidence**. One recurring
  claim — coding agents build tasks 1.6–4× faster than Isaac Lab with Claude
  Opus 5 — could not be located in the repository, docs or release notes and is
  graded D (§08).
- GitHub REST API: repository metadata, org repository lists, tags, releases,
  commits, contributors, issues, recursive tree (`2782` entries, not truncated),
  and `git ls-remote` for tag/head SHAs.
- Repository files read at `a52315871572`: `README.md`, `AGENTS.md`,
  `pyproject.toml`, `LICENSE` (presence/type), `.github/workflows/ci.yml`,
  `eden/extensions/deployment/__init__.py`, the head of
  `eden/extensions/deployment/base.py`, the head of
  `eden/extensions/deployment/unitree_dds.py`, and `eden/tasks/__init__.py`.
- Documentation read: `docs/guides/deployment.md` (state machine and safety
  sections), `docs/guides/deployment-hardware.md`, `docs/getting-started/
  installation.md`, `docs/getting-started/assets.md`, `docs/tasks/index.md`,
  `docs/api/options/robots.md`, `docs/api/terms/catalog.md`.
- PyPI JSON for `eden-world`; arXiv API search for an Eden paper.
- `genesis-world` README and commit history for the Eden listing.

**Not read**: the full 975-module source tree; `base.py` beyond its head; any
Isaac Lab, mjlab, ManiSkill or LeRobot source; Eden's test bodies. **Not run**:
Eden itself, any training, any deployment, any ONNX export. The conclusion is
therefore a source-and-docs review with one local hardware measurement, not an
empirical evaluation.

## 05. Literature Review

There is **no Eden paper**. The repository's citation block is a `@misc` entry
("Eden: One Task Definition from Simulation to Real Robots", November 2026),
not a preprint or peer-reviewed article (A). An arXiv API query for "Eden" plus
robot/embodied terms returned no matching paper; the closest hit is an unrelated
2025 navigation paper, `EDEN: Entorhinal Driven Egocentric Navigation`
(arXiv:2506.03046). The claim that Eden is "the Genesis team's framework" is
not supported by any paper, and the Genesis project's own README calls it an
application-layer example.

Consequences for this review:

- No independent baseline, ablation or statistical claim can be checked; the
  README's numbers are author claims (B), not reviewed results.
- The "1.6–4× faster than Isaac Lab" comparison has no located primary source
  and no methodology in the repository (D). It must not enter any decision
  record as fact.
- The underlying Genesis engine is documented by its own repository and docs;
  this review did not audit the engine's physics fidelity. Any fidelity claim
  about Eden inherits that unverified dependency (C).

Literature review is therefore thin **by the object's nature**, not by omission:
the artefact is a code release, and §06 is the substantive review.

## 06. Repository Investigation

### 6.1 Provenance and project shape

| Fact | Value | Grade |
|---|---|---|
| Repository | `embodied-ai-nexus/Eden` | A |
| Owner | "Embodied AI Nexus", created 2026-03-19, **1 public repo** | A |
| Main author | Kashu Yamazaki (`Kashu7100`), CMU Robotics PhD, 103 public repos | A |
| Genesis relationship | `genesis-world` README lists Eden as "one example of the application layer"; listing commit `3a6c9877` (2026-11-17) is authored by `Kashu7100` | A |
| Licence | Apache-2.0 (`LICENSE`, 11,345 bytes) | A |
| Version | `v0.1.0` 2026-11-12, `v0.1.1` 2026-11-19; PyPI `eden-world==0.1.1` | A |
| Python | `>=3.12,<3.14` | A |
| Stars / forks / open issues | 345 / 22 / 15 (2026-11-28) | A |
| Commits on `main` | ~30 (API pagination: last page 30 at `per_page=1`) | A |
| Contributors | 3 (`Kashu7100` 26, `Michi-Tsubaki` 3, `lalit-jayanti` 1) | A |
| Changelog | none (`CHANGELOG.md` 404); release notes serve that role | A |

The commit count and contributor concentration are the strongest governance
signals: a 975-module codebase with ~30 commits on `main` and one dominant
author. This is consistent with a research-first, single-maintainer project
(squashed or bulk-imported history), not an organisation-backed platform. (A
for the counts; C for the interpretation.)

### 6.2 Architecture (static reading)

- **One typed config per task.** `eden/options` (130 modules) holds Pydantic
  option objects; a task subclasses `EdenRLConfig` with `env_options`,
  `scene_options`, observation/action/command/reward/termination managers and a
  runner. Variants are `TaskMod` classes exposed as CLI flags
  (`docs/tasks/index.md`; README example `eden/tasks/benchmark/reacher/config.py`).
- **Registries and terms.** `eden/managers` (92 modules) implements observation,
  reward, termination, event, curriculum and metric managers; a decorated
  function becomes a term. The generated catalog reports **247** registered
  terms (`docs/api/terms/catalog.md`, generated by
  `python -m eden.managers.catalog`), while the README says **245** — a small
  documentation drift, not a defect. (A)
- **Tasks.** 230 Python modules under `eden/tasks/`; `docs/tasks/index.md`
  states "66 registered tasks", including locomotion, motion tracking,
  manipulation, dexterous and MoChi tasks plus ports of robosuite, LIBERO,
  SIMPLER and PolaRiS. (A for the doc/code shape; B for the exact count.)
- **Policies.** 21 directories under `eden/extensions/policies/`: `amo`,
  `beyondmimic_moves`, `cosmos3`, `galaxeavla`, `gmt`, `gr00t`, `holosoma`,
  `homie`, `humanoid_gpt`, `husky`, `limx_oli_loco`, `metamotivo`, `molmoact2`,
  `octo`, `omnireset`, `omnixtreme`, `pi`, `protomotionv3`, `simtoolreal`,
  `sonic`, `twist2`. These are adapters/clients, not retrained models. (A)
- **Deployment.** 7 hardware backends plus MuJoCo sim-to-sim:
  Unitree G1 (SDK2 DDS, `rt/lowstate`/`rt/lowcmd`), Go2, Go1 (legacy SDK),
  LimX Oli, Franka Panda/FR3 (`panda_py`), RoboTera XHand, Wuji Hand 1/2;
  composite rigs drive each part through its own binding. (A)
- **Scale in the tree**: 975 `.py` files in `eden/`, 752 under `tests/`, 195
  under `examples/`, 2,782 blobs total. (A)

### 6.3 Dependencies, CI and tests

`pyproject.toml` pins `genesis-world==1.4.7` (exact), `torch>=2.9.2`,
`torchvision>=0.19.0`, `numpy>=1.26.4`, `mujoco>=3.3.6,<3.17`, `rsl-rl-lib>=3.0`,
PyYAML and others; optional extras cover `vis`, `nyx`, `batch-splat`, `gello`,
`pico`, `wuji`, `onnx`/`onnx-gpu`, `pose` and real-robot SDKs. The comments are
unusually candid about brittleness: the Nyx plugin and Genesis are "a matched
pair", the renderer coupling "has already broken once", several extras are
capped because a plugin release dropped a symbol, and `onnxruntime` and
`onnxruntime-gpu` overwrite each other. (A)

CI (`.github/workflows/ci.yml`) runs pre-commit, install-and-import,
`eden list` registry resolution, docs, and an `rsl_rl` test job on CPU; tests
mirror `eden/` (`docs/guides/testing.md`). 752 test files is a healthy ratio,
but the CI evidence is import/registry/unit-level, not a hardware or
sim-to-real validation. (A for CI structure; B for effective coverage.)

### 6.4 Real-robot command path and safety model

`eden deploy` is a single control loop with an **INIT / START / STOP / KILL**
operator state machine shared by every backend:

- boots in STOP, holds the measured pose; no remote and no TTY means it stays
  in STOP forever;
- INIT ramps to `--init_target`; START hands over to the active policy slot;
  KILL leaves the loop and `close()` settles the robot (G1/Go2/Go1/Oli ramp to
  damping, kp = 0);
- inputs are keyboard line commands (works over SSH) and vendor remotes;
- safety mechanisms include fail-before-connect validation, torque/velocity
  clamps per robot, stale-observation clearing, and a required physical e-stop
  within reach. (A)

The documented limit is decisive for JCHENG:

> "A stalled control thread is reported, not acted on… the re-send loop keeps
> sending the last command for as long as the process lives… any receive-side
> watchdog it has will not engage: it holds the last commanded pose, at the
> gains it was commanded with, until the process goes away."
> — `docs/guides/deployment.md`, §Safety

This is precisely the class of wedge JCHENG's stop latch and lease expiry are
designed to bound. Eden's model is a competent **operator-supervised** deploy
loop, not a substitute for the system layer. (A for the text; C for the
comparison.)

### 6.5 Assets and licensing

Eden ships code, not meshes: robots, objects, scenes, policy checkpoints and
motion datasets download from the Hugging Face Hub on first use into
`~/.cache/eden/assets/`. `docs/getting-started/assets.md` explains paths,
offline pre-fetch and cluster use, but contains **no per-asset licence
statement** (grep for licence/copyright/commercial/redistribute returned
nothing). Datasets in the gallery include AMASS, which carries its own
non-commercial terms. Apache-2.0 covers the Eden code; it does not automatically
cover downloaded robot meshes or datasets. (A for the absence; C for the legal
consequence — counsel review required before any commercial use.)

## 07. Comparative Analysis

The candidates below solve different problems, so they are compared only on the
question "what could JCHENG use for offline Piper training/simulation?".

| Option | What it is | Strength for this question | Constraint / gap | Grade |
|---|---|---|---|---|
| **Eden 0.1.1** | Genesis-based GPU RL framework, Python, Apache-2.0 | Broad task/term library, multi-physics, ONNX export, pip-installable | No ROS 2, no Piper asset, 0.1.x API, 6 GB VRAM limit, vendor-SDK deploy path | A (facts), C (fit) |
| **Isaac Lab** | NVIDIA's Isaac-Sim-based RL framework | Mature ecosystem, large task library | Isaac Sim/Omniverse stack; not reviewed here; NVIDIA-centric | B, not reviewed |
| **MuJoCo / mjlab / MuJoCo Playground** | Physics + RL environments | Lightweight, CPU/GPU, strong contact fidelity | Narrower task/asset library than Eden; still not ROS 2 | C/D, not reviewed |
| **Current JCHENG plant** | Gazebo Harmonic + deterministic mock, domain 43 | ROS-native, already inside the contract/safety story | Weaker GPU throughput for RL; no built-in RL task library | A (workspace docs) |
| **LeRobot / RLinf / VLA stacks** | Data collection, imitation/VLA training, RL infra | Matches the current data-driven manipulation line | Different problem class from Eden's RL environments | A (workspace reports) |

Directly comparable results do not exist: no shared benchmark was run, and
Eden's only comparative claim (vs Isaac Lab) has no located primary source.
There is no defensible ranking, only a scope statement: **Eden is the broadest
pip-installable RL world among these, and the least compatible with a ROS 2
safety graph.** The simpler alternative for JCHENG is to keep the Gazebo plant
and write a narrow RL environment only if an RL question actually appears —
less capability, far less integration and licensing surface. (C)

## 08. Critical Findings

1. **The premise is partially wrong, in a way that matters.** Eden is not a
   Genesis-org release. It is a third-party application built on Genesis, listed
   in Genesis's README by its own author. Treating it as "official Genesis"
   would overstate its stability and support. (A)
2. **No paper, no independent reproduction.** Every capability claim is
   self-reported; the citation is `@misc`. (A)
3. **Single-maintainer risk.** 3 contributors, ~30 commits on `main`, one public
   repo in the org, 15 open issues, two releases in eight days. (A)
4. **API churn at 0.1.x is real.** `v0.1.1` alone ports to a new Genesis solver
   API, retires `collision_friction`, changes gripper collision behaviour on
   several benchmarks (invalidating 0.1.0 checkpoints on those tasks), and
   changes config fields. A dependency now means tracking a moving target. (A)
5. **The dependency graph is fragile by design.** Exact `genesis-world==1.4.7`
   pin, matched Nyx plugin caps, renderer/plugin symbol removals, mutually
   exclusive ONNX runtimes. This is a research stack, not a platform with a
   compatibility promise. (A)
6. **Hardware coverage excludes JCHENG.** Seven vendor backends; no Piper, no
   ArmPi, no generic ROS 2 bridge. Adding Piper means writing a backend and
   owning it. (A)
7. **The deploy safety model is incompatible with the motion authority.**
   Vendor-SDK command path, its own state machine, keyboard/remote operator,
   physical e-stop, and the documented "stalled thread keeps the last command"
   behaviour. Using it on the fixed cell would bypass `ExecuteMotion`, lease and
   stop latch. (A)
8. **6 GB VRAM is the local ceiling.** The default 4096 envs is not a laptop
   setting; the actual GPU is 6144 MiB. Camera rendering and large scenes will
   hit OOM first. (S for hardware; C for the limit.)
9. **The headline benchmark is unverified.** The "1.6–4× faster than Isaac Lab"
   table is absent from the repository, docs and release notes; only secondary
   AI-generated summaries repeat it. Do not use it. (D)
10. **Asset licensing is unaddressed.** Apache-2.0 code plus Hugging Face assets
    with no per-asset terms; AMASS-class datasets are non-commercial. A licence
    audit is a prerequisite, not a footnote. (A for absence; C for risk.)

What would change the conclusion: a peer-reviewed paper or independent
reproduction; a 0.2+ release with a compatibility policy and more maintainers;
an upstream Piper/ROS 2 backend; a measured MVE showing useful throughput on
6 GB; and a written asset-licence position. None exists today.

## 09. Engineering Applicability

**Layer mapping.** Eden can only sit outside the runtime graph, alongside
`jcheng-learning` and `jcheng-simulation`:

| JCHENG layer | Eden fit | Reason |
|---|---|---|
| L2 `jcheng-system` | **No** | Eden would be a second motion origin; no lease, no `ExecuteMotion`, vendor SDK path |
| L3 capabilities | **No** | No ROS 2 node/package; would need a bridge that then violates intent-only rules |
| L4 studio/applications | **No** | Different problem; L4 is HTTP/WS orchestration |
| `jcheng-learning` (offline) | **Possible, narrow** | RL training and ONNX export for a Piper task; no dataset/weights in git |
| `jcheng-simulation` (offline) | **Possible, reference** | Independent physics cross-check; not a replacement for domain-43 plant |
| `jcheng-benchmark` | **No** | Eden is a world, not a read-only benchmark protocol |

**Costs.** A separate environment is mandatory: `torch>=2.9.2` plus
`genesis-world==1.4.7` is a multi-GB install with numpy/torch constraints that
must not touch the ROS 2 Jazzy/Humble environments. First use downloads assets
from Hugging Face; offline clusters need pre-fetch. 6 GB VRAM caps parallel
envs and rendering. Maintenance means pinning Eden, Genesis and its plugins
together and re-validating on each 0.1.x bump.

**Gains.** If an RL need appears: a large library of tasks/terms, multi-physics
(rigid/PBD/MPM/SPH/FEM + Mochi cloth/soft/rod), motion retargeting, 21 policy
adapters, and ONNX/TorchScript export into a policy artifact that JCHENG could
run behind its own gate. The design patterns — one typed config, fail-fast
validation, generated term catalog, state-check recipes before a hardware run —
are worth borrowing even if the dependency is not. (B)

**Risks.** Dependency conflicts with the ROS toolchain; no Piper asset and
unverified URDF joint/axis conventions; asset licences; safety bypass if anyone
runs `eden deploy` on the cell; maintenance drag from 0.1.x churn.

**Rollback.** Delete the isolated venv and `~/.cache/eden`; no runtime repo
change, no contract hash, no DDS domain. This is why a reference-only stance is
cheap.

## 10. Recommended Approach

**Recommended: reference only, for now.**

- Read Eden's task-config/registry design and its AGENTS.md rules; borrow the
  fail-fast config pattern and the "state-check recipe before hardware" habit.
- Do **not** add Eden as a dependency of any JCHENG repo, do not add its
  contracts to `jcheng-interfaces`, and do not run `eden deploy` on the fixed
  cell.
- Revisit when at least two of these hold: a peer-reviewed paper or independent
  reproduction; a 0.2+ release with a compatibility policy and wider
  maintainership; an upstream Piper backend; a measured 6 GB MVE.
- If a learned policy is ever adopted, export it (ONNX/TorchScript) and run it
  behind `jcheng-system`'s `ExecuteMotion` with lease, limits and stop latch —
  never through Eden's vendor-SDK loop.

**Alternative (conditional): isolated MVE-0.** If an RL question is opened for
the fixed cell (e.g. contact-rich insertion where imitation data is thin), run
the §11 experiment in a throwaway `uv` environment on this laptop. It is
allowed to fail; it is not a route to deployment.

**Rejected options.**

- *Runtime dependency* — violates the motion-authority, DDS-domain and
  no-hardware-in-L3 rules; rejected on architecture, not on quality.
- *Eden as the simulation authority* — would replace the domain-43 plant and
  its contract story with a moving 0.1.x dependency; rejected.
- *Adopting its safety model* — operator state machine + physical e-stop is
  weaker than lease + stop latch + watchdog for an unattended cell; rejected.
- *Adopting now on the strength of the README* — no paper, no reproduction, no
  Piper support, 6 GB VRAM; rejected as premature.

## 11. Experimental Design

**MVE-0 — Piper-class task on a 6 GB laptop (designed, not run).**

- **Hypothesis.** Eden 0.1.1 can import a Piper URDF, build a reaching task, and
  train for 10 minutes at 256 parallel environments on the 6 GB RTX 3060 Laptop
  without OOM, then export an ONNX policy that loads in `onnxruntime`.
- **Baseline.** The existing Gazebo plant's kinematic replay of the same Piper
  URDF (joint limits, axes, link frames), plus a CPU-only Eden run as the
  fallback.
- **Independent variables.** `num_envs` ∈ {64, 256, 1024}; rendering on/off;
  task complexity (reacher → lift).
- **Controlled variables.** Eden `v0.1.1` + `genesis-world==1.4.7`; Python
  3.12.3; driver 595.99.02; same URDF; fixed seed; identical episode length.
- **Environment.** Isolated `uv` venv; no ROS 2 sourced; no DDS domain
  0/41/42/43; network only for Hugging Face assets; no robot, no motion.
- **Metrics.** Build success; peak VRAM (`nvidia-smi` sampled every 2 s);
  steps/s; time to first non-zero reward; ONNX export/load parity (max absolute
  action difference); joint-limit violations in rollout.
- **Acceptance.** Piper URDF builds with documented joint mapping; 256 envs
  trains 10 min with peak VRAM < 5.5 GB; ONNX loads and matches the PyTorch
  policy within tolerance; all commands reproducible from the log.
- **Failure.** OOM at 256 envs; unresolved URDF axis/frame mismatch; export
  mismatch; or an asset licence that forbids the intended use.
- **Recording.** `experiments/20261128-eden-piper-feasibility/` with `design.md`,
  `data/` (VRAM and steps/s CSV), `logs/`, and `result.md`; commit SHA and
  config JSON recorded.
- **Rollback.** Delete the venv and `~/.cache/eden`; no repository dependency,
  no contract change, no hardware state.

Status: **not run**. No install was performed in this investigation.

## 12. Limitations & Uncertainties

- **No execution.** Nothing was installed or trained; throughput, OOM and
  export claims are inferences from docs and hardware, not measurements.
- **Partial source review.** 975 modules exist; this review read the deployment
  entry points, CI, packaging and generated docs, not the solver, manager or
  task implementations. A code-level defect could be missed.
- **No Isaac Lab comparison.** The relative-performance question is unresolved;
  the only public claim is unverified (D).
- **Moving target.** Eden was pushed to on 2026-11-28; `main` may differ from
  `a52315871572` by the time this is read.
- **Search-tool summaries were unusable.** Several secondary summaries repeated
  the "Genesis team" and "Opus 5 / Isaac Lab" claims without links; they were
  excluded rather than cited.
- **Asset licences unverified.** No per-asset terms were found; legal review is
  required before any commercial or redistributed use.
- **Piper URDF fidelity unverified.** The URDF's joint conventions have not been
  checked against Eden's asset parser; this is exactly what MVE-0 would test.

## 13. References

- Eden repository: <https://github.com/embodied-ai-nexus/Eden>, Apache-2.0,
  commit `a52315871572` (2026-11-27), tag `v0.1.1` =
  `1a39eb9205f94b6f8c0983fb8ace89d1353aae72` (2026-11-19).
- Eden release notes: <https://github.com/embodied-ai-nexus/Eden/releases/tag/v0.1.1>.
- Eden docs: <https://embodied-ai-nexus.github.io/Eden/>; key pages read:
  `docs/guides/deployment.md`, `docs/guides/deployment-hardware.md`,
  `docs/getting-started/installation.md`, `docs/getting-started/assets.md`,
  `docs/tasks/index.md`, `docs/api/options/robots.md`,
  `docs/api/terms/catalog.md` at the commit above.
- PyPI: <https://pypi.org/project/eden-world/>, version 0.1.1, requires
  Python `>=3.12,<3.14`.
- Genesis World: <https://github.com/Genesis-Embodied-AI/genesis-world>,
  Apache-2.0, head `beae8af2af4a29f6c1873db0aa2c7421c5782eef` (2026-11-27);
  README line listing Eden, commit
  `3a6c9877` ("List Eden in the README as an application built on Genesis",
  2026-11-17).
- Genesis release pin: `genesis-world==1.4.7` (`pyproject.toml`, Eden
  `v0.1.1`).
- arXiv API query for Eden + robot/embodied, 2026-11-28: no matching paper;
  nearest unrelated hit arXiv:2506.03046.
- Local host measurement: `nvidia-smi` 2026-11-28 — RTX 3060 Laptop GPU,
  6144 MiB, driver 595.99.02, compute capability 8.6; Python 3.12.3; ROS 2
  Jazzy.
- JCHENG layering and domain rules: `jcheng-robotics/AGENTS.md` §3, §7, §8;
  offline-only boundaries of `jcheng-learning`, `jcheng-simulation`,
  `jcheng-benchmark`.
- Source record: [`references/datasets-benchmarks/eden-framework.md`](../references/datasets-benchmarks/eden-framework.md).

---

Evidence grades: **S** reproduced on this system · **A** direct primary source
or code · **B** credible indirect evidence · **C** inference from existing
evidence · **D** unverified hypothesis.
