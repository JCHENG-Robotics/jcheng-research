# Contact Harness — frozen-VLM contact-rich manipulation, and what the release actually supports

> Report status: **draft**. Date: 2026-11-28.
> Author: ZCode research agent. Reviewer: pending.
> Decision this informs: whether JCHENG should adopt, borrow or reject Contact Harness
> for contact-rich manipulation, and which part (if any) to prototype first.
> Research boundary: public web, GitHub API, static reading of
> `NTUMARS/Contact-Harness` at `5827438`, `NTUMARS/ContactHarness` at `a4d8b38`,
> and the 45-page arXiv v1 PDF served by the project page. No test, simulation or
> robot run; no GPT-6 Astra / Claude Fable access; Hugging Face metadata timed out.
> All performance numbers are the authors' self-report, not an independent
> replication.

## 01. Executive Summary

**Contact Harness is a harness, not a model.** It connects a frozen VLM agent to a
robot through three services (robot server, guarded motion server, observation
server), a set of hand-written textual skills, and a force-aware motion-clipping
layer on top of Cartesian impedance control. The paper's claim is that this
combination performs contact-rich manipulation with no fine-tuning, no task
demonstrations and no simulation training. (A for the architecture and code; B for
the performance claims.)

**The headline real-robot result is not reproducible from the release.** The
90.7% full-insertion result across 15 connector types (136/150) was obtained on a
7-DoF Rokae arm with DM-Tac W2 tactile sensors. The released `harness/rokae/`
contains only an agent prompt and two task prompts (wipe, write); there is no
Rokae robot server, no Rokae motion server and no connector-insertion prompt file.
The released real-robot path is Franka (force only, no tactile), and the released
simulation path is MuJoCo/robosuite. (A for what is absent in the repository; B
for the result itself.)

**"Zero-shot" means no training and no demonstrations, not no task engineering.**
The agent reads a system prompt (7.7–8.7 KB) and a task prompt (4.2–16.4 KB) that
encode phase order, mandatory visual entry gates, numeric thresholds (5 mm, 7 cm,
a seven-adjustment cap), camera-to-world mappings and failure recovery. Removing
the textual skills drops the simulated contact-task mean to 42.5% from 95.0%. The
prompt is therefore a primary contributor, and the honest description is
*train-free but prompt-engineered*. (A for prompt sizes and the ablation numbers;
C for the interpretation.)

**Safety is research-grade.** The soft force limit is a bound, not a force cap;
there is no torque limit; rotation continues while translation is clipped; a hard
50 N event aborts the batch and holds the target rather than retracting; the force
estimate is an estimate and can report force without contact. The harness is not
an e-stop substitute. Its engineering hygiene is nevertheless better than typical
research code: no motion at startup, refusal to start when the robot's collision
threshold is below the software hard limit, raw force always participates in the
hard check, and every step is acknowledged before the next. (A for the code and
the paper's own statements.)

**Fit for JCHENG: not directly.** ArmPi Ultra is a 5-DoF bus-servo arm with a
gripper, no six-axis force/torque sensor, no tactile sensor, no Cartesian
impedance mode, and a ROS 2 Humble vendor stack; the paper's real-robot stacks
are ROS 1 Noetic + `franka_ros` for Franka and an unreleased Rokae stack.
JCHENG also has a stricter motion-authority model: only `jcheng-system`'s
`ExecuteMotion` originates motion, with lease, deadman, limits and stop latch.
The reusable parts are the **episode/evaluation protocol**, the **observation /
motion service separation**, the **force-clipping algorithm as a future L2 safety
filter**, and the **skill-text structure as an input to schema-validated recipes**
— not the runtime. (B/C for the fit assessment.)

**Recommendation.** Track Contact Harness as a research and benchmark reference;
do not adopt it as a runtime. If a prototype is wanted, run Contact-4 in
simulation on the RTX 3060 (MVE-0) and map the harness interface onto
`jcheng-applications`' abstract gateway port with a mock (MVE-1). No robot
experiment is warranted before force sensing and compliant control exist at L2,
and every real-robot motion would still need separate, explicit, per-session
operator authorization. (C.)

**Main risk.** Reading 90.7% as a platform-independent capability, or as evidence
that ArmPi can perform contact-rich insertion without new sensing, would be
wrong on both the hardware and the evidence. (A/C.)

## 02. Research Questions

The question as asked: *investigate `ntumars.github.io/ContactHarness/`*. The URL
resolves to a project page, not to the code repository, so the investigation was
split into the project page, the paper and the released code.

Sub-questions:

1. **Q1 — What is Contact Harness?** What problem does it claim to solve, with
   what mechanism, and under what assumptions?
2. **Q2 — What does the release actually implement?** Which robots, services,
   sensors, models and tests are present, at which commit?
3. **Q3 — Are the headline results reproducible?** Can an independent reader
   reproduce the real-robot and simulated numbers from the released artifacts?
4. **Q4 — Do the claims survive critical review?** Baselines, ablations, sample
   size, statistics, safety, cost and model dependency.
5. **Q5 — Is it compatible with JCHENG and ArmPi Ultra?** Layers, motion
   authority, sensors, middleware, compute and safety.
6. **Q6 — What is worth adopting, and what would test it?** A minimum viable
   experiment (MVE) and an explicit reject list.

Constraints:

- **Hardware:** no robot session, no camera, no force sensor; ArmPi Ultra is not
  a Franka and has no F/T sensing.
- **Contracts and safety:** motion may only originate in `jcheng-system`; a
  research report cannot grant motion authority or a hardware claim.
- **Access:** no GPT-6 Astra or Claude Fable credentials; no Rokae stack; no
  Hugging Face download.
- **Deliverable:** this report, one source record under `references/`, and an
  MVE design. No runtime code and no experiment execution.

## 03. Current System Analysis

This section records what the JCHENG ecosystem actually does today, from the
workspace `AGENTS.md` (status 2026-11-27) and the repository boundaries it
declares. No JCHENG code was modified or executed for this report.

### 3.1 Layer and motion authority

| Layer | Repository | What it may do | What it must not do |
|---|---|---|---|
| L2 | `jcheng-system` | Safety state machine, leases, arbiter, hardware bridge, gateways, read-only telemetry, MoveIt plan-only; **the only origin of motion (`ExecuteMotion`)** | Import or depend on L3/L4 at runtime |
| L3 | `jcheng-perception`, `jcheng-mobile`, `jcheng-learning`, `jcheng-teleop`, `jcheng-devices`, `jcheng-scenarios` | Publish intent; perception/mobile may join domain 42 (perception in practice runs on domain 0 with CycloneDDS) | Open serial/CAN/GPIO/video devices, publish vendor topics, fabricate data, originate motion |
| L4 | `jcheng-studio`, `jcheng-applications` | Gateway HTTP/WS only | DDS, device access, `ExecuteMotion`, a lease of their own |
| OPS | `jcheng-ops` | HTTP health probes and watchdogs | Join DDS |
| SIM | `jcheng-simulation` | Offline plant on domain 43 | Join 0/41/42, act as a motion source |

Consequences for Contact Harness:

- Its `motion_server.py` directly commands a robot and reads devices. That is an
  L2-shaped component, not an L3 capability and certainly not an L4 application.
  Importing it into `jcheng-applications` or `jcheng-studio` would violate the
  layer rules and the "L2 is the only origin of motion" invariant. (A.)
- Its `observation_server.py` opens cameras and sensors directly. In JCHENG that
  belongs to the system hardware bridge or to `jcheng-perception`, not to an L4
  agent. (A.)
- An LLM agent with `home`/`recover`/motion commands is exactly the authority
  model JCHENG forbids: capabilities publish intent; the system layer applies
  lease, deadman, limits and the stop latch. (A.)

### 3.2 ArmPi Ultra capability envelope

| Property | ArmPi Ultra | What Contact Harness assumes |
|---|---|---|
| Arm | 5-DoF bus-servo arm + gripper | 7-DoF Rokae / Franka with Cartesian impedance |
| Force sensing | None (no six-axis F/T; bus-servo load is not calibrated as a wrench) | Six-axis wrist wrench or joint-torque estimate |
| Tactile | None | DM-Tac W2 on each finger (Rokae); none on Franka |
| Control | Vendor position stack | 1 kHz Cartesian impedance, 50 Hz target loop (Franka) |
| Middleware | ROS 2 Humble (vendor), CycloneDDS | ROS 1 Noetic + `franka_ros` 0.10.2 (Franka) |
| Compute | Pi 5 8 GB; operator RTX 3060 | Simulator on an NVIDIA GPU; paper used RTX 5090 |
| Model | No local frontier VLM | GPT-6 Astra via Codex CLI, or Claude Fable via Claude Code |

The visual side is the closest match: JCHENG already runs a wrist camera plus an
external view with a timestamp/TF discipline, while Contact Harness uses two or
three 640×480 RGB-D views and a "latest sample with a 0.5 s age limit" policy.
That is a downgrade in time discipline, but not the blocking gap. The blocking
gaps are force sensing and compliant control. (A for the hardware facts; C for
the gap assessment.)

### 3.3 What JCHENG already has that is relevant

- `jcheng-applications` v0.1.0: recipe validation, deterministic plans and a
  fail-closed runner over an **abstract gateway port**; no HTTP/WS client yet.
- `jcheng-scenarios` v0.1.0: declarative scenario catalog with typed profiles and
  an offline validator; task-success semantics live here.
- `jcheng-benchmark` v0.1.0: offline, read-only suite declarations, strict JSONL
  runner, metrics/thresholds and provenance-labelled reports.
- `jcheng-simulation`: domain-43 offline plant; not a motion source.
- `jcheng-manipulation` v1.0.0: frozen capstone baseline; not to be rewritten.

These are the natural consumers of the reusable parts: recipe/skill structure,
scenario success criteria, benchmark protocol, and a simulated plant. (A for the
repository roles; C for the mapping.)

## 04. Research Methodology

### 4.1 Search and source selection

Search terms and synonyms: *Contact Harness*, *VLM contact-rich manipulation*,
*force-aware motion clipping*, *compliant execution VLM*, *textual skills robot*,
*Contact-4 benchmark*, *NTUMARS*, *MARS Lab NTU*, *GPT-6 Astra robot agent*.

Sources consulted:

1. Project page `https://ntumars.github.io/ContactHarness/` (accessed
   2026-11-28), its source repository `NTUMARS/ContactHarness` at `a4d8b38`, and
   the page's `docs/paper.pdf` (35,313,207 bytes; 45 pages).
2. arXiv abstract page `arXiv:2611.29377` v1, submitted 2026-11-22, 45 pages,
   21 figures, cs.RO / cs.CV; no venue or DOI.
3. Code repository `NTUMARS/Contact-Harness` at commit
   `5827438a166667f5eb24761e2d37827b59cc64f7` (2026-11-22 22:16 +0800): 106
   files, 13,395 Python lines, MIT, one commit, no tags, no CI.
4. GitHub API metadata for both repositories and the NTUMARS organization.
5. The repository's READMEs, prompts, tests, setup and run scripts, and the
   simulation task definitions.

Inclusion criterion: a source had to describe the method, the release, or the
evaluation protocol. Exclusion: social-media summaries, third-party blog posts,
and AI-generated recaps were not used as evidence. The cited baseline papers
(CaP-X, GenCHiP, Show-Harness, π0.5, ForceVLA, CompliantVLA) were **not**
independently reviewed; they appear only as the authors describe and adapt them.

### 4.2 What was read in full, what only partially

- **Full:** the 45-page paper PDF, including the main text, Algorithm 1, Tables
  1–5, and appendices A (related-work comparison), B.2 (compliant execution),
  D.1 (real-robot failure analysis), E.3 (VLM baseline adaptations), E.5
  (Contact Harness simulation results), G (token usage) and H (limitations).
- **Full:** `harness/franka/README.md`, `contact4/README.md`,
  `harness/rokae/README.md`, `contact4/prompts/agent_prompt.txt`,
  `contact4/prompts/task_prompt_peg_insertion.txt`,
  `harness/franka/docs/task_prompt_cable_insertion.txt`, `contact4/setup.sh`,
  `contact4/run_codex_episode.sh`, `contact4/agent_guard.py`,
  `contact4/codex_guard.py`, and the relevant parts of
  `harness/franka/motion_server.py`, `harness/franka/tests/test_soft_force_truncation.py`
  and the dependency manifests.
- **Partial:** appendix C (prompt summaries, not every task prompt in full),
  appendix E.1/E.2 (task construction and success criteria) and E.4 (VLA
  training details) were read selectively; the cited baseline papers were not
  read.

### 4.3 Boundary and access limitations

- No test suite, simulation episode or robot run was executed. All code
  conclusions are static reading at the pinned SHA.
- The arXiv PDF endpoint was slow from this host (~6 KB/s); the paper was read
  from the project page's `docs/paper.pdf`, which is the same 45-page document
  by title/date but was not byte-compared with the arXiv upload.
- Hugging Face API timed out; the Contact-4 demo size (8.6 GB), format
  (LeRobot v2.1) and license (CC BY 4.0) are taken from the repository README,
  not from the dataset card.
- No GPT-6 Astra / Claude Fable access; no independent model behaviour check.
- No Rokae robot or control stack; the headline real-robot path could only be
  inspected as paper text and prompts.

## 05. Literature Review

### 5.1 The paper's problem and mechanism

The paper starts from a real limitation: vision alone is often insufficient for
contact-state assessment, while force and tactile signals are semantically
ambiguous without task phase and visual context. A second problem is timing: a
VLM decision takes seconds, while contact can change in tens of milliseconds.
Contact Harness addresses both by (i) reusable **textual skills** that tell the
agent how to read each signal in each phase, and (ii) **compliant execution**
that regulates motion with real-time force feedback between decisions.

The loop is: request observations → assess contact state → issue one command or a
short batch → execute under impedance with force-aware clipping → return accepted
reference and measured final poses → repeat. The system prompt describes the
architecture, commands, observations, units and frames; the task prompt gives the
goal, phase order, completion criteria and task-specific rules.

Assumptions:

- The VLM can interpret numeric force/tactile readings if the prompt explains
  their physical meaning and the current phase. (Tested indirectly by the
  force-observation ablation.)
- The robot exposes a wrist wrench or joint-torque estimate and a compliant
  (impedance) control mode. (Explicit in the paper's limitations.)
- The task prompt can encode the relevant procedure and failure recovery. (The
  "w/o skills" ablation tests the counterfactual.)

### 5.2 Experimental design and sample size

Real robot:

- 15 connector types on Rokae, 10 trials each = 150 trials; a single insertion
  prompt; 15-minute limit per trial. Success requires the connector head to reach
  its mechanical insertion limit, not apparent seating in the camera.
- 7 additional tasks (wipe, write, USB-A, peel, pivot, stack, pick-and-place),
  10 trials each = 70.
- Real-PC generalization: 3 connectors × 10 trials = 30, with lighting,
  background and socket position changed together.
- Speed tests: C13, C13 fast, C13 fast+memory, Franka USB-A fast+memory, 10
  trials each = 30. The memory condition runs 10 trials in one agent
  conversation with manual resets, not as independent zero-shot episodes.

Simulation (Contact-4):

- 4 contact tasks (Insert, Wipe, Write, Pivot) + 2 contact-free references
  (Place, Stack), 10 seeds per task (0–9), 30-minute episode limit, success
  windows of 20 minutes for Place/Stack/Insert and 30 minutes for Wipe/Write/
  Pivot.
- Insert is modified from Isaac Lab Factory PegInsert, rebuilt in MuJoCo, with a
  ~0.06 mm radial clearance and a 15 N press-fit resistance beyond 3 mm depth;
  success requires the peg within 1 mm of the hole bottom.
- Wipe requires removing 100 dirt markers; Write requires a person to read
  "ROBOT"; Pivot requires ≥80° tilt, ≤4 mm lowest-corner height, ≤3 cm to the
  wall, and 2 s of stillness without contact.
- 50 teleoperated demonstrations per task (300 episodes, 93,195 frames at 10 Hz,
  8.6 GB, LeRobot v2.1) are provided for training-based baselines.

Statistical reliability: 10 trials per cell, no confidence intervals, no
preregistration, and model-service interruptions that the paper says affected
execution time and some failures but were not counted separately. A 10-trial
8/10 result has a Wilson 95% interval of roughly 49–94% (computed here, C); the
136/150 headline has a much tighter interval, roughly 85–94% (C). The paper's
claims are directional; they are not precision estimates.

### 5.3 Baselines and ablations

The paper compares against:

- **VLM agent baselines:** CaP-X, GenCHiP (reimplemented; no public code), and
  Show-Harness, all with GPT-6 Astra, the same simulator and seeds. The appendix
  documents unusually generous support: tool-tip calibration, added force
  protection, completion checks, ground-truth object positions with 0–4 mm noise
  for GenCHiP, and adapted prompts. CaP-X and GenCHiP also receive the Contact
  Harness task prompt in separate rows.
- **Trained policies:** π0.5, π0.5+force, ForceVLA, CompliantVLA, trained on the
  50 demonstrations per task.
- **Ablations:** no force observations (hidden from the agent only), no textual
  skills, and no compliance/soft limit (stiff position control, no force limit).

The result pattern:

| Method family | Sim mean success | What it shows |
|---|---:|---|
| Contact Harness (Astra) | 96.7% | 58/60; only Insert fails twice |
| Contact Harness (Fable 5.1 / 5.2) | 98.3% | 59/60 each; Insert 9/10 |
| ForceVLA (best trained) | 68.3% | strong on Place/Stack, weak on Insert |
| π0.5 + force | 61.7% | force helps, still weak on Insert |
| π0.5 | 46.7% | no force |
| CompliantVLA | 43.3% | compliance alone does not solve contact decisions |
| GenCHiP (goal only) | 33.3% | open-loop program |
| CaP-X | 23.3% | code-as-policies, open loop per block |
| Show-Harness | 16.7% | 1 cm discrete actions, designed for pick-and-place |

Ablations (4 contact tasks):

| Configuration | Insert | Wipe | Write | Pivot | Mean |
|---|---:|---:|---:|---:|---:|
| Full | 8/10 | 10/10 | 10/10 | 10/10 | 95.0% |
| w/o force observations | 7/10 | 7/10 | 9/10 | 10/10 | 82.5% |
| w/o textual skills | 0/10 | 0/10 | 9/10 | 8/10 | 42.5% |
| w/o compliance & soft limit | 0/10 | 9/10 | 10/10 | 6/10 | 62.5% |

The paper's interpretation is that textual skills and compliant execution are
both necessary for Insert, force observations matter for the *mechanism* of
success (without them, the seven successful Insert runs all rely on the prompt's
forced final push rather than force-guided alignment), and compliance alone
raises peak force to nearly 30 N without improving contact decisions. That is a
coherent story, and the ablations are the strongest part of the evidence. (B for
the numbers; A for what the paper reports.)

### 5.4 Related-work positioning

The paper's Table S1 positions Contact Harness as the only entry that combines
stepwise VLM decisions during contact, force/tactile input to those decisions,
compliant execution, training-free/demo-free operation, and real-robot contact
tasks (15 connectors, wiping, writing, peeling, pivoting). The closest neighbours
are:

- **GPT-6 Astra direct control / GPT-GEAR:** stepwise VLM decisions; GPT-6 Astra
  has no force or tactile input (0/3 on tube and charger insertion), while
  GPT-GEAR uses force only in simulation and has no compliant execution.
- **Show-Harness:** stepwise VLM, real contact tasks, but 1 cm discrete actions
  and no force.
- **GenCHiP:** compliant motion programs with force thresholds, but one model
  call and open-loop execution, not stepwise decisions.
- **ForceVLA / CompliantVLA:** force and compliance, but trained policies rather
  than a frozen VLM deciding each action.
- **Harness VLA / SafeHarness / BATON:** agent orchestration over trained VLAs,
  not force-aware stepwise decisions with a frozen model.

This positioning is the authors' characterization; the cited systems were not
independently reviewed here. Two cautions follow. First, "training-free" is not
"engineering-free": the harness, prompts and force guard are substantial
artifacts. Second, adding the Contact Harness task prompt to CaP-X and GenCHiP
made them worse (0.0% and 16.7%), which suggests the prompt is coupled to the
harness's action primitives and observation interface, not a portable skill. (B
for the comparison; C for the coupling inference.)

### 5.5 Transfer cost to this platform

The paper's own limitations section is unusually candid:

- Execution is slow: 378 s mean insertion, ~90% inference/observation; 96 s best
  case with fast mode + memory, still slower than direct policies.
- Remote model service interruptions can stall or fail a trial.
- Small connectors occupy few pixels; occlusion by fingers is common.
- Token usage is high: ~1.62M tokens per real USB-A insertion, 95% cached;
  ~1.49M per simulated run, 96% cached.
- Some sockets (e.g. HDMI with a hidden inner ring) cannot be distinguished from
  "fully inserted" by force alone when the fingers block the view.
- Uneven contact surfaces break the surface-search procedure; connector-specific
  prompt engineering is required.
- The method currently needs a wrist F/T sensor or joint-torque sensing plus
  compliant control; sensorless estimation is proposed as future work.

These are exactly the constraints that matter for ArmPi. The transfer cost is
therefore dominated by sensing and compliant control, not by the 13k lines of
Python. (A for the limitations; C for the transfer estimate.)

## 06. Repository Investigation

### 6.1 The two repositories

| Repository | Role | License | Commit | State at access |
|---|---|---|---|---|
| `NTUMARS/ContactHarness` | Project page; `docs/` static site, paper PDF, videos | Apache-2.0 | `a4d8b38` | 1 commit, 7 stars, pushed 2026-11-26 |
| `NTUMARS/Contact-Harness` | Code, prompts, tests, simulation | MIT | `5827438` | 1 commit, 14 stars, 0 forks, 0 issues, pushed 2026-11-22 |

The project page is **not** the code repository. Its README explicitly says:
"This repository holds the project page. All website files are in `docs/` … The
code and the textual skills are in `NTUMARS/Contact-Harness`." (A.)

The code repository's single commit is titled "Contact Harness code and textual
skills". There are no tags, no releases, no `.github/` directory, no CI
configuration, and no issue/PR history. This is a snapshot release, not a
maintained project. (A.)

### 6.2 Layout

```text
Contact-Harness/
├── harness/
│   ├── franka/          # real Franka: robot server, motion server, observation server,
│   │                    # CLI clients, prompts (cable insertion, peeling, pivoting), tests
│   └── rokae/           # README + 2 task prompts only; no control stack
├── contact4/            # MuJoCo/robosuite benchmark: 6 tasks, 50 demos/task (external),
│   │                    # sim task server, harness copy, agent guards, run scripts
│   └── stack/           # the agent's working copy of the harness in simulation
├── third_party/
│   └── franka_controllers/  # adapted Franka controller package (MIT)
├── README.md
└── LICENSE              # MIT
```

Key absence: `harness/rokae/README.md` says "Prompts of the whiteboard wiping
and writing tasks on the Rokae arm with an AG-95 gripper and DM-Tac W2 tactile
sensors. **Only the prompts are included.**" There is no Rokae robot server,
motion server or observation server. The paper's headline 15-connector result
therefore has no released control path. (A.)

### 6.3 Call chain and services

Real Franka:

```text
agent (Codex CLI / Claude Code)
  → python terminal_command.py / get_observation.py
    → HTTP (Flask) on localhost
      → motion_server.py / observation_server.py
        → franka_robot_server.py
          → ROS 1 Noetic, franka_ros 0.10.2, Cartesian impedance controller
```

Simulation:

```text
episode_ctl.py start
  → sim_task_server.py (physics, contact force, tactile, success tests)
  → run_motion_server.py / run_observation_server.py (harness services)
  → Codex/Claude agent in contact4/stack/
  → runs/contact_harness/<task>/<task>_s<seed>_<time>/
```

The agent loop is:

```text
get observations → choose command arguments → execute with --wait → repeat
```

The command interface exposes `delta`, `pose`, `gripper`, `status`, `stop`,
`home` and `recover`; commands are batched with `--next`; limits are 0.15 m /
90° per move, 0.035 m/s, 0.08 rad/s, duration 0.05–120 s. The agent can change
the soft force limit while the server is idle. (A.)

### 6.4 Force-aware motion clipping

The core implementation is small and readable. In
`harness/franka/motion_server.py` at `5827438`:

- `constrain_translation(dp, force, threshold)` at line 114:

  ```python
  result = dp.copy()
  blocked = (np.abs(force) > threshold) & (force * dp < 0)
  result[blocked] = 0.0
  return result, blocked
  ```

- `Settings` defaults at lines 130–131: `soft_force_n = 10.0`,
  `hard_force_n = 50.0`.
- `Settings.validate()` at line 151 enforces `0 < soft < hard`, `hard ≤ 50`, and
  a positive step frequency; a soft limit at or above the hard limit is rejected.
- `RobotBackend.start()` at lines 553–557 reads the controller's
  `collision_force_threshold_n` and refuses to start when the software hard limit
  exceeds it:

  ```python
  collision_limit = number(info["collision_force_threshold_n"], "collision threshold")
  if self.cfg.hard_force_n > collision_limit:
      raise ...
  ```

- `_hard()` at lines 1001–1012 always evaluates the **raw** force:

  ```python
  force = wrench[:3]
  if max(np.linalg.norm(force), np.linalg.norm(force - self.cfg.force_bias_n)) >= self.cfg.hard_force_n:
      raise MotionError("hard_force_limit")
  ```

  The comment says: "Raw force ALWAYS participates: a software bias cannot
  conceal a hard stop." This is a good pattern.
- `_execute()` at lines 1147–1201 splits a command into `N = ceil(T / Δt)` steps,
  reads force before each step, clips per axis, discards the clipped part (it is
  not made up later), extends the schedule instead of catching up after jitter,
  and reports `clipped_steps`, `discarded_translation_m`, scheduling delay and
  measured endpoint. Completion is exhaustion of the nominal steps, including
  clipped ones.
- `_stop()` at lines 1315–1339 sends a hold-target stop and records
  `stop_mode="hold_target"`; it does not retract. The README warns that after a
  hard-limit fault the Franka holds its target and the operator must `recover`
  explicitly.

Semantics and limits:

- The soft limit is a **directional bound**, not a force cap: it only removes a
  translation component that pushes further into an already-overloaded axis. A
  new contact, a moving surface, a torque load or a rotation command can still
  increase force. The paper and README say this explicitly.
- There is **no torque limit**. Rotation continues while translation is clipped.
- The hard limit aborts and cancels the remaining batch, but the controller holds
  the target; it is not an emergency retract.
- The force estimate is an estimate. The Franka uses joint-torque estimates; the
  system prompt warns that it can report force without contact.

These are honest limitations, and the implementation is careful within them. (A
for the code; A for the documented semantics.)

### 6.5 Observation service

`harness/franka/observation_server.py` (1,075 lines) continuously reads cameras,
force/tactile and robot state, keeps the latest sample per source, and serves
only requested observations. Default age limit is 0.5 s; a missing or stale
source is returned as an error. The server zeros the wrist wrench by averaging
for one second while the robot is still and free of contact; restarting the
observation server resets the tactile baseline. Samples are explicitly **not
synchronized** across sensors. (A.)

For JCHENG this is the weakest architectural match: `jcheng-perception` already
maintains depth/TF timestamp rings and a two-view fusion path, while Contact
Harness uses a latest-sample, 0.5 s-age policy with no cross-sensor time
synchronization. The visual interface is similar; the temporal contract is not.
(A for the code; C for the comparison.)

### 6.6 Agent isolation and evaluation hygiene

The simulation uses three layers of isolation:

1. **PreToolUse hooks.** `agent_guard.py` (Claude Code) and `codex_guard.py`
   (Codex) allow only a small tool set (`Bash`, `Read`, `Glob`, `Grep`,
   `TodoWrite`/`ToolSearch`, or Codex's `Bash`, `view_image`, `update_plan`,
   `clocksleep`). `agent_guard.check_bash` (line 58) denies `..`, absolute paths
   outside the allowed roots, environment variables, process introspection,
   network tools, simulator names/ports, and run artifacts; `inside()` (line 53)
   resolves paths before checking; the hook fails closed. `codex_guard.allowed`
   (line 24) maps Codex tools onto the same policy.
2. **Per-episode RPC token.** The simulator answers internal requests only with a
   token created per episode; the agent's environment is scrubbed with
   `-u SIM_RPC_TOKEN` (`run_codex_episode.sh:50`).
3. **Isolated agent home.** `CODEX_HOME=contact4/.codex_home` holds only model
   settings and the guard hook; `--ephemeral` avoids history; skills, memories
   and rules are checked for cleanliness before the run.

Strengths: every tool request and decision is logged to `guard.jsonl`; the agent
cannot see simulator state through the intended interface; the run artifacts are
complete (`result.json`, `metrics.jsonl`, `trajectory.npz`,
`agent_stream.jsonl`, `guard.jsonl`, `task.json`).

Weakness: the guard is a **regex filter on the command string**, not a sandbox.
`run_codex_episode.sh:53` starts Codex with `-s workspace-write` and
`sandbox_workspace_write.network_access=true`, and `:56` uses
`--dangerously-bypass-hook-trust`. A script written to `stack/tmp` could contain
forbidden operations without matching the command string; the per-episode token
and path checks are defense-in-depth, not a proof. Against an accidental peek at
ground truth this is adequate; against an adversarial agent it is not. (A for the
code; C for the bypass assessment.)

### 6.7 Tests, dependencies and licenses

- **Tests:** 77 offline tests in `harness/franka/tests/` (9 frame conventions, 10
  action queue, 9 soft-force truncation, 30 motion server, 12 observation, 7
  robot-server configuration). I counted `def test_` occurrences; I did **not**
  run them. `test_soft_force_truncation.py` uses a fake backend to check the
  10 N soft threshold, the 21/49.9/50 N hard-limit boundaries, force-bias
  handling, and the server-limit mismatch refusal.
- **Dependencies:** exact pins; Python 3.10 is asserted in `contact4/setup.sh:8`;
  Franka real robot requires ROS 1 Noetic, `franka_ros` 0.10.2, an RT kernel and
  RealSense; simulation uses MuJoCo 2.3.2 / robosuite 1.4.0, `pin`/`pin-pink`,
  `qpsolvers`/`daqp`, and EGL. The paper's simulation runs used Ubuntu 22.04 and
  an RTX 5090.
- **Licenses:** code MIT; project page Apache-2.0; `third_party/franka_controllers`
  MIT; `franka_ros` launch/config Apache-2.0; Isaac Lab peg/hole BSD-3-Clause;
  LIBERO bowl/plate MIT; demos CC BY 4.0 per README. The license hygiene is
  better than average for a research release.
- **CI/packaging:** none. No Dockerfile, no `pyproject.toml`, no lockfile beyond
  pinned requirements. Installation is a shell script plus two venvs.

### 6.8 Real-deployment evidence

The project page hosts videos and a trial player; the paper reports the trial
counts and success criteria. There is no independent deployment report, no
third-party replication, and no issue tracker activity. The evidence is
**self-reported by the authors**, with videos as supporting material. (B.)

## 07. Comparative Analysis

The question is not "is Contact Harness better than X" in the abstract; it is
"which family fits which JCHENG decision". The candidates are not directly
comparable because they assume different hardware, sensors, models and budgets.

| Family | Example | Strength | Cost / limitation | Comparable to Contact Harness? |
|---|---|---|---|---|
| Classical hybrid force-position / impedance insertion | industrial peg-in-hole, scripted search | Fast, deterministic, mature; excellent when geometry and F/T are known | Task-specific; needs F/T and compliant control; sensitive to part variation | Only on the same task/hardware; the paper does not run a classical baseline |
| Fine-tuned VLA policy | π0.5, ForceVLA, CompliantVLA | Fast inference; improves with data; can use force | Needs demonstrations/training; contact-task success in the paper is ≤68.3% | Yes, within Contact-4; the paper trains them on 50 demos/task |
| VLM agent harness (code-as-policies) | CaP-X, GenCHiP, Show-Harness | General reasoning; no training; interpretable programs | Open-loop blocks or coarse actions; weak contact regulation; prompt-sensitive | Yes, within Contact-4; the paper adapts them generously |
| Frozen-VLM + textual skills + compliant execution | Contact Harness | Stepwise force/tactile decisions; no training; strong contact results in its benchmark | Prompt engineering; closed model; minutes per trial; needs F/T and impedance; unreleased Rokae stack | The subject of this report |
| JCHENG recipe/runner + `ExecuteMotion` | `jcheng-applications` v0.1.0 | Deterministic, auditable, fail-closed, lease/stop-latch governance | No force sensing or compliant control; offline core only | Not a manipulation method yet; a governance/execution layer |

What is directly comparable:

- Within the paper's Contact-4 benchmark, the VLM-agent and VLA rows share the
  simulator, seeds, time limits and success criteria; that comparison is
  internally valid (B).
- The real-robot connector results are comparable only to another run on the same
  Rokae arm, gripper, tactile sensors and socket set; no such independent run
  exists (B/C).
- Cross-paper numbers (e.g. "96.7% vs. another paper's 70%") are **not**
  comparable without matching task construction, success criteria, trial count
  and model version. No ranking is asserted here.

Hidden engineering costs:

- Prompt development and maintenance: task prompts are 4–16 KB, with numeric
  thresholds and camera mappings; changing the camera, gripper or socket geometry
  can invalidate them.
- Model access and version drift: the numbers are tied to GPT-6 Astra / Fable
  5.1/5.2 via specific CLIs; a model update can change behaviour.
- Token cost and latency: ~1.5–1.9M tokens per run; 378 s mean insertion; 84.7%
  of time in reasoning.
- Sensing and control: wrist F/T or joint torque, compliant control, calibration,
  and a safety case.
- Evaluation: 10 trials per cell is enough for a demo, not for a precision claim;
  a production decision needs more trials and held-out scenes.

Simpler alternatives:

- If the goal is **insertion on a known part** and a force sensor can be added, a
  classical force-controlled insertion with a scripted search is simpler, faster
  and easier to certify than an LLM agent.
- If the goal is **data collection**, teleoperation (SpaceMouse/VR) is simpler
  and is what the paper itself uses for its 50 demos/task.
- If the goal is **VLM agent research**, Contact-4 is a ready benchmark; the
  harness is a reasonable baseline, but the closed model is a reproducibility
  risk.

## 08. Critical Findings

1. **The headline real-robot result is not reproducible from the release.** The
   90.7% / 136-150 result is Rokae-specific; `harness/rokae/` has only prompts,
   and the 15-connector prompt is not a file in the repository (the paper puts a
   condensed version in Fig. S2). The released real-robot code is Franka,
   force-only. Grade: **A** for the absence; **B** for the result.

2. **"Zero-shot" is prompt-engineered.** The system prompt is 7.7–8.7 KB and the
   task prompts are 4.2–16.4 KB; they contain mandatory gates, numeric
   thresholds, camera mappings and recovery rules. The "w/o textual skills"
   ablation drops the simulated contact mean from 95.0% to 42.5%. The method is
   training-free and demo-free, but not prior-free. Grade: **A** for the sizes
   and ablation; **C** for the interpretation.

3. **The baseline comparison is asymmetric in resources, though unusually
   generous in support.** VLA baselines get 50 demos/task; the harness gets a
   frontier closed model with ~1.5M tokens/run plus a hand-written prompt. The
   appendix gives the baselines tool calibration, force protection, completion
   checks and (for GenCHiP) ground-truth object positions with noise, which
   strengthens the comparison; it does not equalize inference budget or prompt
   engineering. Grade: **A** for the protocol; **C** for the fairness judgement.

4. **The textual skill is not portable.** Adding the Contact Harness task prompt
   to CaP-X and GenCHiP made them worse (0.0% and 16.7%), which is consistent
   with the prompt being coupled to the harness's observation and action
   primitives. Calling it a "reusable skill" is fair inside the harness; calling
   it a general skill is not supported. Grade: **B**.

5. **Statistics are thin.** Ten trials per cell, no confidence intervals, no
   preregistration; model-service stalls affected timing and some failures but
   were not separated. An 8/10 cell has a Wilson 95% interval of roughly 49–94%
   (computed here). The real-PC generalization test uses only three
   easy/medium connectors (C13, earphone, USB-A) on one arm and one scene; no
   hard connector is tested there. The speed-with-memory result uses one
   conversation and manual resets, not independent zero-shot episodes. Grade:
   **A** for the protocol; **C** for the interval calculation.

6. **Safety is research-grade.** Soft limit is a directional bound, not a cap;
   no torque limit; rotation continues while translation is clipped; hard-limit
   abort holds the target rather than retracting; force is estimated and can be
   wrong; the system has no e-stop, brake or self-collision model. The code's
   interlocks (no motion at startup, collision-threshold refusal, raw-force hard
   check, per-step ACK) are good, but they do not turn it into a certified safety
   system. Grade: **A**.

7. **The closed-model dependency is a reproducibility and cost risk.** The
   numbers are tied to GPT-6 Astra via Codex CLI 0.162.1 and Claude Fable 5.1/5.2
   via Claude Code; the repository has no model weights or local-model path. The
   paper reports ~1.62M tokens per real USB-A insertion (95% cached) and ~1.49M
   per simulated run (96% cached). Model updates, service stalls or price changes
   can change both success and cost. Grade: **A** for the dependency and token
   numbers; **B** for the impact.

8. **The agent isolation is heuristic.** The guard is a regex PreToolUse filter,
   not a sandbox; Codex runs with `workspace-write` and network access enabled.
   The per-episode token and path checks are defense-in-depth. This is adequate
   for an honest agent in a research experiment; it is not a security boundary.
   Grade: **A** for the code; **C** for the bypass risk.

9. **The release is a snapshot, not a maintained project.** One commit, no tags,
   no CI, no issues/PRs, no packaging; Python 3.10 and ROS 1 Noetic pins; paper
   simulation used an RTX 5090. The code quality is good, but the maintenance and
   portability cost is real. Grade: **A**.

10. **What would change the conclusion.** Release of the Rokae control stack and
    the 15-connector prompt; an independent replication on the same hardware; a
    held-out scene/connector test; a sensorless or low-cost-arm variant with
    measured force estimation; and a production safety case. Until then, the
    90.7% is a strong self-reported result, not a transferable capability. Grade:
    **C**.

## 09. Engineering Applicability

### 9.1 Fit with the JCHENG architecture

| Dimension | Contact Harness | JCHENG / ArmPi | Verdict |
|---|---|---|---|
| Motion authority | Motion server commands the robot; agent can `home`/`recover` | Only `jcheng-system` `ExecuteMotion`; lease, deadman, limits, stop latch | **Incompatible as-is**; would need to become an L2 safety filter plus an L4 intent client |
| Observation | Observation server opens cameras/sensors | L2 hardware bridge or L3 perception; L4 HTTP/WS only | **Rewrite the boundary** |
| Skill representation | Free-text task prompt with numeric rules | Schema-validated recipes/scenarios; contract-first | **Not a contract**; only the structure is reusable |
| Force sensing | Wrist F/T or joint torque | None | **Blocking gap** |
| Compliant control | Cartesian impedance at 1 kHz | Vendor position stack | **Blocking gap** |
| Arm DOF | 7-DoF Rokae/Franka | 5-DoF ArmPi | **Fine alignment limited** |
| Middleware | ROS 1 Noetic (Franka), vendor API (Rokae) | ROS 2 Humble / Jazzy | **Rewrite** |
| Model | Closed frontier VLM via CLI | No equivalent local model | **External dependency** |
| Cost/latency | ~1.5M tokens/run; minutes per trial | Production needs deterministic, auditable cycle time | **Not production-fit** |

### 9.2 What would have to be true for ArmPi

For a Contact-Harness-style system to be credible on ArmPi Ultra, all of the
following would need to hold:

1. A calibrated force/torque estimate at the wrist or joints, with a documented
   bias, noise and drift characterization. Bus-servo load feedback is not
   currently characterized as a wrench. (C/D.)
2. A compliant control mode (impedance or admittance) with a bounded force
   response, or a safety-filtered position mode that can approximate it. The
   vendor stack's position control is not enough for the paper's force
   regulation. (C.)
3. Enough wrist DOF for the alignment phase; 5-DoF limits the rotation
   corrections the paper relies on. (C.)
4. A force guard implemented **inside L2**, not in the agent: per-axis clipping,
   raw-force hard limit, rate limits, workspace limits, stop latch and an
   explicit fault/recover state. (A for the design principle; C for the effort.)
5. A safety case: risk assessment, force limits justified per task, operator
   e-stop, guarded workspace, and evidence. The paper's "keep the e-stop within
   reach" is not a substitute. (A.)
6. A model-access and cost plan; if the frontier model is unavailable, a local
   model or a different agent must be evaluated, and the numbers will not
   transfer. (C.)

### 9.3 Migration effort and cost

- **Harness code alone:** small (13k lines, MIT), but not the bottleneck.
- **Real-robot stack:** high. The released Franka path is ROS 1 Noetic; the
  Rokae path is absent; ArmPi is ROS 2 Humble with a vendor stack. A port would
  require a new robot server, IK/kinematics, a compliant control mode, force
  calibration, and safety validation. Estimate: multi-week to multi-month,
  dominated by sensing/control and safety, not by the agent code. (C.)
- **Simulation:** moderate. Contact-4 needs Python 3.10, MuJoCo 2.3.2,
  robosuite 1.4.0, EGL and an NVIDIA GPU; the paper used an RTX 5090, so the
  RTX 3060 performance is untested. (C.)
- **Evaluation:** low. The episode artifacts and ablation flags are directly
  reusable; the protocol is the cheapest part to adopt. (B/C.)

### 9.4 Reliability, safety and rollback

- **Reliability:** the agent is a stochastic, remote, closed model; the harness
  has no CI and one commit. Failure modes include service stalls, prompt drift,
  model updates, camera occlusion, force-estimate bias and guard bypass.
- **Safety:** research-grade; not an e-stop; no torque limit; no certified
  force cap; no self-collision model.
- **Effect on existing behaviour:** none if this report remains a report. If a
  prototype is built, keep it in an isolated simulation worktree/venv; do not
  touch `jcheng-system`, `jcheng-perception` or the vendor container.
- **Rollback:** delete the prototype worktree and venvs; no runtime change, no
  migration, no contract change.

## 10. Recommended Approach

### Recommended

**Track Contact Harness as a research and benchmark reference; borrow the
evaluation and engineering patterns; do not adopt the runtime.**

Adopt now (offline, low risk):

1. **Episode protocol and artifacts** for `jcheng-benchmark` / `jcheng-scenarios`:
   fixed seeds, time limits, `result.json`, `metrics.jsonl`, trajectory,
   agent-event stream, guard log, task parameters, ablation flags, token counts.
2. **Observation/motion service separation as a design pattern**, mapped to
   JCHENG's gateway: the agent gets a read-only observation API and an intent
   API; it never opens devices or commands motion directly.
3. **Force-clipping algorithm as a reference for a future L2 safety filter**:
   per-axis directional clip, raw-force hard limit, per-step acknowledgement,
   no catch-up after jitter, explicit clipped-step accounting. Requires
   calibrated force sensing first.
4. **Skill-text structure** as an input to schema-validated recipes: goal,
   initial state, completion, observations, phase order, entry gates, force
   targets, motion style, recovery. The free text stays a design document; the
   executable contract is a recipe/scenario schema.

### Alternatives

- **A. Sim-only benchmark run (MVE-0).** Run Contact-4 `peg_insertion` seeds 0–2
  on the RTX 3060 with the released harness and a supported agent. This tests
  feasibility and gives a local data point; it does not test ArmPi. Recommended
  if model access exists and the goal is to calibrate expectations.
- **B. Gateway mapping (MVE-1).** Express the peg-insertion skill as a
  schema-validated recipe/skill intent over `jcheng-applications`' abstract
  gateway port with a mock. This tests whether the harness pattern survives
  JCHENG's authority model. Recommended regardless of model access.
- **C. Classical force-controlled insertion.** If a force sensor is added and the
  task is a known connector, a scripted hybrid force-position insertion is
  simpler, faster and easier to certify. Recommended for a production task, not
  for general contact-rich manipulation.

### Rejected

- **Direct port of `motion_server.py` to ArmPi or to L3/L4.** It violates the
  motion-authority and device-access boundaries, and the hardware lacks the
  sensing/control it assumes.
- **An LLM agent with `home`/`recover`/motion authority.** Not acceptable under
  the lease/deadman/stop-latch model.
- **Prompt-as-contract.** A 4–16 KB free-text prompt is not a validated recipe;
  it cannot be the source of truth for a production task.
- **Using 90.7% as an ArmPi target or a platform-independent capability.** The
  number is Rokae-specific and self-reported.
- **A production dependency on a closed frontier model without a fallback.**
  Cost, latency, version drift and service availability are unresolved.

## 11. Experimental Design

Both experiments are **designed, not run**. No robot is involved. Each is
pre-registered here so that a later run cannot silently change the acceptance
criteria.

### MVE-0 — Contact-4 simulation smoke test on the RTX 3060

**Hypothesis.** The released harness and a supported agent can complete
`peg_insertion` seeds 0–2 on the RTX 3060 within the 30-minute episode limit,
without guard violations, at a success rate not inconsistent with the paper's
8/10 (small n; this is a smoke test, not a replication).

**Baseline.** The paper's reported Insert result (8/10, GPT-6 Astra, high
reasoning) is the reference point, not a local control. A local no-skill or
no-force ablation is optional and would require changing the agent prompt, which
this MVE does not do.

**Independent variable.** Evaluation seed (0, 1, 2).

**Controlled variables.** Code commit `5827438`; `contact4` configuration;
MuJoCo 2.3.2 / robosuite 1.4.0; Python 3.10; EGL/NVIDIA driver; agent model and
reasoning effort; episode time limit; success criteria.

**Environment.** Linux host with an NVIDIA RTX 3060, Python 3.10, two isolated
venvs created by `contact4/setup.sh`, `ffmpeg`, EGL vendor file; no robot, no
DDS, no vendor container. The agent runs in `contact4/stack/` with the released
guards.

**Metrics.** Success per seed (simulator success condition); wall-clock time;
number of motion commands/decisions; tokens per run; peak contact force; guard
denials; EGL/driver errors; episode artifacts present.

**Acceptance.** At least 2/3 seeds succeed; every episode terminates (success,
failure or timeout) within 30 minutes; no guard violation; the six artifact files
are present for each run. A 2/3 result is deliberately weak: with a true rate of
0.8, the probability of ≥2/3 is high, so this only detects gross breakage.

**Failure criteria.** Fewer than 2/3 successes; inability to start due to
EGL/Python/model access; missing artifacts; any guard bypass. On failure, record
the logs and stop; do not tune prompts on the evaluation seeds (that would
contaminate the benchmark).

**Recording.** `contact4/runs/contact_harness/peg_insertion/...` plus a short
`result.md` in an experiment directory. Do not commit videos, trajectories or
model outputs to `jcheng-research`; keep them outside the repository and record
only the summary and paths.

**Rollback.** Delete the worktree, venvs and run directory; no repository or
runtime change.

### MVE-1 — Harness-to-gateway mapping (offline)

**Hypothesis.** The harness's observation/command interface can be expressed as a
schema-validated recipe plus a skill intent over `jcheng-applications`' abstract
gateway port, with no DDS/device access and no `ExecuteMotion` bypass, while
remaining expressive enough for the peg-insertion phases.

**Baseline.** The current `jcheng-applications` v0.1.0 recipe runner and its mock
gateway (or a minimal mock written for the experiment).

**Independent variable.** Skill representation: free-text prompt (as in Contact
Harness) vs. structured recipe with phases, gates and force targets.

**Controlled variables.** Task (peg insertion), mock gateway behaviour, failure
injection, logging, no hardware.

**Environment.** Offline Python; `jcheng-applications` at its current checkout;
no ROS, no DDS, no device; the mock gateway records every intent.

**Metrics.** Expressiveness (can the skill encode the paper's phases and gates?);
schema validation result; audit-log completeness; fail-closed behaviour under
injected gateway errors; static proof of no forbidden imports/device access;
number of intents per phase.

**Acceptance.** The peg-insertion skill is expressible as a validated recipe +
intent; every motion intent goes through the mock gateway; a static test proves
no DDS/device/`ExecuteMotion` access from the application layer; injected
failures stop the run and are logged; the recipe can be replayed deterministically.

**Failure criteria.** The skill requires uncheckable free text or direct motion;
the recipe cannot encode the entry gates; the application needs a device or DDS
access; failure injection does not stop the run.

**Recording.** `experiments/20261128-contact-harness/` with `design.md`, the
recipe/mock code, and `result.md`; no hardware, no vendor code.

**Rollback.** Delete the experiment worktree/branch; no runtime change.

### MVE-2 — Deferred: force-sensing prerequisite (hardware)

Not designed here. Any hardware characterization of bus-servo load feedback, let
alone arm motion, requires a separate safety review and explicit per-session
operator authorization. It is a prerequisite for a Contact-Harness-style force
guard on ArmPi, not part of this report's scope.

## 12. Limitations & Uncertainties

- **No execution.** The report is a static review; no test, simulation or robot
  run. Code conclusions are at commit `5827438` and may change upstream.
- **No independent replication.** The performance numbers are the authors'
  self-report. The project page and paper are the same group; their agreement is
  consistency, not independence.
- **No Rokae stack.** The 90.7% result cannot be reproduced from the release; the
  connector prompt is not a file.
- **No model access.** GPT-6 Astra / Claude Fable behaviour, pricing and
  availability were not verified; the token numbers are from the paper.
- **HF metadata unverified.** The 8.6 GB / CC BY 4.0 demo claim comes from the
  repository README; the HF API timed out.
- **Prompt-tuning inference.** The claim that prompts were tuned on the evaluation
  scenes is an inference from their content, not a disclosed fact. It is graded
  C.
- **Statistics.** The Wilson intervals are my calculations, not the authors';
  the paper reports no confidence intervals.
- **Hardware estimates.** RTX 3060 feasibility and ArmPi migration effort are
  estimates, not measurements.
- **Safety.** This report is not a safety case and does not authorize motion.
- **What would close the gaps:** release of the Rokae stack and connector prompt;
  an independent replication on the same hardware; a held-out scene/connector
  test; model access; HF dataset metadata; a force-sensing characterization on
  ArmPi under a separate safety review.

## 13. References

### Primary sources

- **Paper.** Shilin Shan, Yuxuan Hu, Chuhao Zhou, Yimeng Dong, Bohan Hou, Jiaqi
  Bai, Boyu Ma, Jiahua Dong, Jianfei Yang. *Contact Harness: Enabling VLM Agents
  to Perform Contact-Rich Manipulation.* arXiv:2611.29377 v1, submitted
  2026-11-22, 45 pages, 21 figures, cs.RO / cs.CV. No venue, DOI or peer review
  at access. <https://arxiv.org/abs/2611.29377>. PDF:
  <https://ntumars.github.io/ContactHarness/paper.pdf>. Read in full (main text
  and selected appendices) on 2026-11-28.
- **Code repository.** `NTUMARS/Contact-Harness`, commit
  `5827438a166667f5eb24761e2d37827b59cc64f7` (2026-11-22), MIT.
  <https://github.com/NTUMARS/Contact-Harness>. Accessed 2026-11-28. Static
  review of `harness/franka/`, `contact4/`, `harness/rokae/`, tests, prompts and
  dependency manifests; not executed.
- **Project-page repository.** `NTUMARS/ContactHarness`, commit
  `a4d8b38` (2026-11-26), Apache-2.0. <https://github.com/NTUMARS/ContactHarness>.
  Accessed 2026-11-28. Source of `docs/paper.pdf` and the project page.
- **Project page.** <https://ntumars.github.io/ContactHarness/>. Accessed
  2026-11-28.
- **Dataset.** Contact-4 demonstrations, <https://huggingface.co/datasets/ntumars/Contact-4>.
  README claims 8.6 GB, LeRobot v2.1, 50 demos/task, CC BY 4.0; metadata not
  verified (API timeout, 2026-11-28).
- **Lab.** MARS Lab, Nanyang Technological University, <https://marslab.tech>.

### JCHENG sources

- Ecosystem workspace `AGENTS.md` (status 2026-11-27): repository map, layer
  rules, motion authority, hardware facts and DDS domains. Read-only; no JCHENG
  code was modified or executed for this report.
- `jcheng-applications`, `jcheng-scenarios`, `jcheng-benchmark`,
  `jcheng-simulation`, `jcheng-system`, `jcheng-perception` repository roles as
  declared in the workspace `AGENTS.md`; no code-level audit was performed here.

### Source record

- [Contact Harness source record](../references/manipulation/contact-harness.md)
  — URLs, commit SHAs, read scope, access date and the specific files read.

---

Evidence grades: **S** reproduced on this system · **A** direct primary source or
code · **B** credible indirect evidence · **C** inference from existing evidence ·
**D** unverified hypothesis. No S-grade result exists in this report: nothing was
reproduced on JCHENG hardware or in a local run.
