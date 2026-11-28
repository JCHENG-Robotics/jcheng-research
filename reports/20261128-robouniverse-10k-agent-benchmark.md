# RoboUniverse-10K — what the release actually contains, and whether the fixed-cell Piper program can use it

> Report status: **draft**. Date: 2026-11-28.
> Author: ZCode research agent. Reviewer: pending.
> Decision this informs: whether RoboUniverse-10K should enter the JCHENG stack as
> (a) an offline benchmark, (b) a Piper Isaac Sim asset source, or (c) a
> design reference only — and what must be true before any run.
> Research boundary: public web, arXiv:2611.31002v1 full HTML, GitHub API and raw
> files, Hugging Face API/raw plus **one** task archive (1.76 MB). No GPU, no
> Isaac Sim execution, no model serving, no robot session. Hugging Face throughput
> from this host was ≈20 KB/s, so the 18.6 GB corpus and the 72 GB weights were
> not downloaded.

## 01. Executive Summary

**RoboUniverse-10K is an evaluation corpus and harness for LLM coding agents that
program robot arms, not a robotics framework.** It ships 10,807 Isaac Sim 5.1
manipulation environments (4,132 Franka single-arm, 6,675 AgileX Piper dual-arm),
a Harbor/Docker harness that hides the verifier, a 500-task zero-shot benchmark
(`RoboUniverse-Verified`), and one SFT model (`RoboUniverse-35B-A3B`). The agent
writes Python against a 9-dimensional joint-target API at 20 Hz and never sees
object poses, reference solutions, or grading logic. (A)

**Recommendation: do not adopt it as a runtime or training dependency now; adopt
it as a design reference, and keep one asset pointer under license review.** The
three facts that carry this:

1. **The hardware floor is far above this workspace.** Each simulation needs
   18–44 GiB of VRAM per the release README (the task pack declares a 6 GiB
   reservation, which is not the measured need); the model server needs 67 GB of
   bf16 weights plus KV cache. The operator laptop's RTX 3060 (6 GB) cannot run
   it, and the simulation host must be Linux x86_64 with an RTX GPU — the AGX
   Orin is not a target. (A for the stated requirements; C for the hardware-fit
   inference.)
2. **It is not ROS and has no motion path.** The harness is Python 3.12 +
   Docker Compose + Harbor 0.25.0 + Isaac Sim; actions are joint targets inside a
   container. There is no DDS, no `ExecuteMotion`, no lease and no path to the
   real cell. It can only live outside the runtime dependency graph, like
   `jcheng-benchmark`. (A)
3. **The released scope is narrower than the headline.** The repository contains
   evaluation and inference code only; the Real2Sim builder/QA pipeline that
   produced the environments is described in the paper but not released. The
   dataset card has **no license field**, and third-party assets (NVIDIA Franka,
   `agilexrobotics/piper_isaac_sim`, RoboDojo assets) stay under upstream terms.
   (A)

The main risk is not technical: it is reading the headline numbers (85.8% frontier,
21.2% after SFT) as evidence about real manipulation or about Piper. They are
single-attempt results on a 500-task suite curated by the same pipeline, under two
specific agent harnesses, with no error bars and no executed real-robot reliability
trial. (A/C)

## 02. Research Questions

As asked: *调研 RoboUniverse-10K 这个工具* — what is it, and is it useful here?

Sub-questions:

1. **What exactly is released?** Environments, harness, model, pipeline — which
   parts are code, which are data, which are paper-only?
2. **What does a task actually contain and how is success judged?** Is the
   verifier genuinely isolated, or is the claim only in the README?
3. **Are the reported numbers comparable to anything we do?** Same task
   distribution as training? Same metric as policy benchmarks? Any variance?
4. **Can the fixed-cell Piper program use it?** Hardware, software, contracts,
   safety boundary, licensing, maintenance.

Constraints: no new GPU spend without approval; no real-robot motion; no Isaac Sim
installation on the Pi or the operator laptop; cross-repo contracts only through
`jcheng-interfaces`.

## 03. Current System Analysis

The workspace targets a fixed cell with **AgileX Piper X as the execution arm**
(the 2026-11-28 platform decision; the workspace `AGENTS.md` still names ArmPi
Ultra and has not been updated — C). Relevant facts:

- `jcheng-simulation` is the offline plant: Gazebo Harmonic + deterministic mock,
  domain 43 only, `/sim/*` topics, no hardware path. It is deliberately outside
  the dependency graph.
- `jcheng-benchmark` is the offline, read-only benchmark harness: suite
  declarations, strict JSONL runner, metrics/thresholds, provenance-labelled
  reports. No DDS, no hardware.
- `jcheng-system` is the only origin of motion (`ExecuteMotion`), with lease,
  deadman, limits and stop latch. Capabilities publish intent on domain 42.
- Host toolchain: ROS 2 Jazzy, Python 3.12; the operator laptop has an RTX 3060
  (6 GB); an AGX Orin is used for perception experiments.
- Existing sim work on Piper is Gazebo-based and has an open joint2/joint3
  tracking failure (`experiments/20261126-piper-x-gazebo-plant/`), so a second
  plant would add integration cost, not remove it.

There is no Isaac Sim installation, no NVIDIA Omniverse account in the repo
record, and no GPU with ≥18 GiB in the current inventory. That is the factual
baseline against which §09 is written.

## 04. Research Methodology

Sources and access (2026-11-28):

| Source | What was read | Grade |
|---|---|---|
| arXiv:2611.31002v1 HTML | Abstract, §2–§4, §6, §7.1–7.3, §8.1, Tables 5–7 | A |
| GitHub `Einsia/RoboUniverse-10K` | README, `requirements.txt`, `evaluate.py` (169 lines), both Dockerfiles, API metadata, commit list | A |
| HF dataset `Einsia/RoboUniverse-10K` | Card (2,804 B), commit history (1 commit), `catalog.csv` (10,807 rows), `heldout500.csv` (500 rows), `THIRD_PARTY.md`, one task ZIP (47 files) | A/S for package structure |
| Project page `lab.einsia.ai/robo-universe` | Numbers and stated caveats; cross-checked against paper | B (consistent) |
| AI News, 2026-11-25 | Claim of 68 replaced tasks / 38 revised graders on the dataset card | **D** (not reproducible) |

Search terms: RoboUniverse-10K, Real2Sim, Harbor Terminal-Bench, AgileX Piper Isaac
Sim, RoboCasa365, RoboTwin 2.0, EmbodiedSWE, agentic robotics benchmark. Sources
were included only if they were the paper, the repository, the dataset, or a
named upstream; secondary commentary was used only to locate claims, then checked
against primary sources. The 13-section structure follows
`templates/research-report.md`.

Exclusions: no full-paper PDF read (HTML only, which omits some appendix detail);
no model inference; no simulation run; no peer-reviewed version exists yet.

## 05. Literature Review

**Problem.** Agentic robotics — an LLM coding agent writes programs that drive a
robot — lacks large, executable, resettable environments. Policy benchmarks
(LIBERO, RoboCasa, RoboTwin) are hand-built, in the tens-to-hundreds of tasks,
and often train and test in the same distribution. The paper's analogy is SWE
benchmarks mined from real pull requests; here the "pull request" is a real
manipulation video. (A)

**Contribution.** (1) An automated Real2Sim pipeline: curated videos → coding
agent with SAM 3.1 segmentation, DA3 depth, an asset library and Isaac Sim →
scene code, reference controller, verifier; iterate by comparing renders to the
source video and by physics-execution feedback. (2) An independent QA agent that
audits fidelity, reset/replay consistency and verifier robustness, then 10 human
experts check four criteria on the 500 test candidates; unfixable tasks are
removed. (3) 10,807 packaged environments. (4) A 500-task zero-shot benchmark.
(5) A 35B-A3B SFT model trained on ~17K GPT-6 Astra trajectories. (A)

**Mechanism and assumptions.** Each environment is a Harbor task: instruction,
Isaac Sim scene, observation/control client, reference solution and verifier. The
agent gets `describe()`, `observe()`, `save_images()`, `step()`, `step_chunk()`,
`finish()`; physics advances only on step calls, so reasoning time is free.
Actions are joint position targets; there is no IK service, so the agent must
build its own kinematic reasoning. The verifier runs in a separate, no-network
container on simulator-collected evidence. (A)

**Evaluation design.** Single attempt per task, 250–4,000 control steps (median
3,000), binary reward, 11 models under Codex or Claude Code. No seeds, no
confidence intervals, no per-task variance — one attempt is the protocol, so the
reported percentage has no measured uncertainty. (A)

**Baselines and ablations.** Eleven models is a broad model comparison, but there
is no ablation of the Real2Sim pipeline itself: no experiment varies scene
fidelity, verifier strictness, or QA acceptance and measures the score change.
The SFT result is one training run; there is no data-size or data-mixture
ablation. The claimed causal story — scale of environments → capability — is
supported by the 0.8→21.2 jump, not by a controlled sweep. (A/C)

**Limitations the authors state.** Simplified scenes and poorly modelled
dynamics ("latch resistance, hinge friction, and contact mechanics are difficult
to recover accurately from video alone"); short atomic skills rather than
long-horizon workflows. They do not discuss benchmark selection bias beyond
"candidate tasks are drawn by stratified sampling" and "tasks that cannot be
fixed are removed". (A)

**Reproducibility.** Code, environments and weights are released; the builder/QA
pipeline is not. The paper's appendix contains the builder, QA and rollout
prompts (§9.1–9.3), so the method is partially reproducible at the prompt level,
not at the code level. (A)

## 06. Repository Investigation

**Anatomy.** `Einsia/RoboUniverse-10K` is 1,653 KB, one commit
(`532745c834`, 2026-11-26), Apache-2.0 with NOTICE, 95 stars, 1 fork, 0 open
issues. Contents: `evaluate.py`, `inference.py`, `summarize.py`,
`verify_anonymous.py`, `verify_published.py`, `docker/sim-base`,
`docker/agent-base`, `assets/`, `requirements.txt`. There is no test suite, no
CI workflow and no package metadata. (A)

**`evaluate.py` call chain (static reading).** `materialize()` verifies the ZIP
digest and `release.json` case identity, extracts with path-traversal guards,
fetches upstream assets with per-file sha256, injects per-role bearer tokens,
copies Dockerfiles, then:
- raises sim CPUs to `max(task, 8)` and documents the measurement: on one RTX PRO
  5000 host, 4 CPUs never became ready in 244 s, 8 CPUs ≤117 s, 16 CPUs ≤76 s;
- patches the sim sidecar because NVIDIA's standalone Isaac Sim image exposes
  `VERSION` but not the `isaacsim` package metadata;
- pins base packages in a constraints file after `--upgrade` once pulled numpy 2.x
  and broke the sidecar;
- adds the EULA env var and read-only bind mounts for `connection.json` /
  `instance.json`.
Then it calls `harbor run -p <task> -a <agent> -e docker -n 1 --force-build
--max-retries 0`. (A)

This is real engineering, and it is also a fragility signal: the public evaluator
modifies task internals at materialisation time, so Harbor, Isaac Sim image and
task-format versions must move together. The README pins `harbor==0.25.0`,
SGLang 0.5.21, Claude Code 2.1.283 and Isaac Sim 5.1. (A)

**Task package (static audit of `000247_rotate_twist`, S).** 47 files, 1.76 MB:
- `instruction.md` (2,280 B) gives the task and the operating protocol; it tells
  the agent not to assume joint count, frequency or gripper convention.
- `task.toml`: agent timeout 7,200 s; verifier timeout 600 s,
  `environment_mode="separate"`, `network_mode="no-network"`; sim `cpus=6`,
  `memory_mb=32768`, `storage_mb=30720`, `gpus=1`, `gpu_memory_mb=6144`.
- `env_spec.json`: `joint_position_target`, 9 dims (7 joints + 2 fingers), 20 Hz
  control, 120 Hz physics; explicit lower/upper limits and a probe action.
- `verify.py` (93 lines): requires 120 Hz private arrays (`time`, `contact_graph`,
  `q/qd`, `forces`, `mug_p/q/v/w`, hand pose, finger positions), checks strictly
  increasing time, max evidence gap 0.04 s, target prim identity and sha256 of
  `scene.py`, `env_backend.py`, `drive_config.json`, `task_definition.json`;
  returns `inconclusive` on missing or inconsistent evidence; it explicitly
  disclaims proving visual fidelity or excluding every mesh penetration.
- `tests/grade.py` (22 lines): rejects `infra_error.json`, requires verdict in
  {success, failure, inconclusive}, and requires `reward` to equal
  `int(verdict=="success")`; writes `reward.txt`.
- `environment/roboenv_client.py` (110 lines): stdlib-only HTTP client with bearer
  token, no simulator imports, idempotent retries for mutating calls.
- `solution/oracle.py` is two lines calling `/oracle`.

So the isolation claim is **not just README language**: the agent image contains
only a stdlib client, the verifier is a separate no-network service, and grading
rejects infrastructure failures rather than scoring them. (S for this one
package; A for the design.)

**Not released.** The builder/QA pipeline code, the QA agent implementation, and
any cluster tooling (`workspace/README.md` still references an internal
`embody_data.cluster simulate` queue). The public evaluator replaces that with
Docker Compose. (A)

## 07. Comparative Analysis

| Suite | Tasks | Train | Test | Held-out | Bimanual | Deformable | Agent/code interface |
|---|---:|---:|---:|---|---|---|---|
| LIBERO | 130 | 130 | 40 | ✗ | ✗ | ✗ | ✗ |
| BEHAVIOR-1K | 1,000 | 3 | 3 | ✗ | ✓ | ✓ | ✗ |
| RoboTwin 2.0 | 50 | 50 | 50 | ✗ | ✓ | ✗ | ✗ |
| RoboCasa365 | 365 | 300 | 50 | ✓ | ✗ | ✗ | ✗ |
| RoboDojo | 42 | 34 | 42 | ✗ | ✓ | ✓ | ✓ |
| Embodied First Exam | 1,156 | 0 | 1,156 | ✗ | ✓ | ✓ | ✓ |
| EmbodiedSWE | 428 | 400 | 28 | ✓ | ✓ | ✓ | ✓ |
| **RoboUniverse-10K** | **10,807** | **10,307** | **500** | ✓ | ✓ | ✓ | ✓ |

Source: paper Table 5, with the paper's own definitions. Task counts are the
authors' units and are not directly comparable across suites: LIBERO's 130
includes 40 test tasks; RoboDojo's "42 test" counts its evaluation set
differently. The meaningful comparison is **interface and scale**: RoboUniverse is
the only suite here with >10K executable environments and a dual-arm Piper
embodiment, and it evaluates coding agents rather than visuomotor policies.

What is **not** comparable: success percentages. A policy benchmark measures a
trained policy in-distribution; RoboUniverse measures an LLM writing code under a
specific harness, with hidden verifiers and one attempt. Its 85.8% and 21.2% do
not transfer to RoboCasa/LIBERO numbers, and the paper does not claim they do
(its cross-benchmark transfer is qualitative "zero-shot completions", not rates).

Against the workspace's existing reference: the RoboDojo agent track is smaller
(42 tasks) but has an operational leaderboard and was already assessed on
2026-11-27 (`reports/20261127-mibot-rua-robodojo-agent-track.md`). RoboUniverse
is a larger corpus with a cleaner isolation design, but no leaderboard, one
commit and a much heavier hardware floor. They are alternatives for different
questions, not substitutes.

## 08. Critical Findings

**F1 — The headline is a curated suite, not a random sample of 10,807.** The 500
test tasks come from the same Real2Sim pipeline, are stratified by embodiment and
family, and every retained task passed expert verification; unfixable tasks were
removed. That is defensible benchmark construction (a task must be solvable), but
it means the score estimates performance on *this curated suite*, not on the
population of real manipulation tasks. The paper reports no contamination audit
and no residual distributional-overlap measurement. (A)

**F2 — The "68 replacements / 38 revised graders" claim is not supported.** A
2026-11-25 AI News article says the dataset card discloses those numbers and warns
against blind sampling. The HF repository has exactly one commit
(`0775b48`, 2026-11-26) and its card contains none of that language; the paper
does not mention it either. I cannot reproduce the claim, so it must not be cited
as fact. The weaker, verifiable statement stands: test selection was not blind.
(D for the specific numbers; A for "not blind".)

**F3 — Scores are harness-bound.** GPT models ran in Codex, the others in Claude
Code, at different effort settings; the model comparison therefore mixes model and
harness. The paper's own released-model instructions use Claude Code 2.1.283,
thinking off, 14,400 s per task. Any reproduction that changes the harness is not
comparable. (A)

**F4 — Physical fidelity is the acknowledged weak point.** The authors name latch
resistance, hinge friction and contact mechanics as hard to recover from video;
the verifier itself disclaims proving visual fidelity or excluding every mesh
penetration. The failure analysis is consistent: 46–47% of weak-model failures
occur before contact, ~80% of frontier failures after contact. A sim-only score
is a statement about the sim. (A)

**F5 — Resource declarations conflict.** The task pack declares
`gpu_memory_mb=6144`, while the README states 18–44 GiB per simulation in
practice; `evaluate.py` raises CPUs but not GPU memory. A host provisioned from
`task.toml` alone is likely to OOM or fail readiness. The pack also requests
32 GB RAM and 30 GB storage per simulation, neither mentioned in the README's
"8 cores" guidance. Treat the README's measured range as operative. (A for the
values; C for the failure consequence.)

**F6 — Licensing is incomplete.** Repository code is Apache-2.0. The dataset card
has no `license` field; `THIRD_PARTY.md` says third-party assets keep upstream
terms; Franka assets come from NVIDIA's Isaac tree, Piper from
`agilexrobotics/piper_isaac_sim` (which has **no LICENSE file**), and some
materials from Poly Haven. Isaac Sim requires EULA acceptance. The SFT model's
base (Qwen3.6-35B-A3B) license and the terms of GPT-6-Astra-generated training
data are not discussed. Commercial or redistributive use needs a legal review,
not a README reading. (A for the facts; C for the legal conclusion.)

**F7 — The strongest reusable part is the grading discipline, not the tasks.**
Concretely: verifier in a separate no-network container; binary verdict with
`inconclusive` for missing evidence; reward must equal `int(verdict=="success")`;
infrastructure errors are not scored; verifier binds evidence to source-file
hashes; agent image has no simulator dependency. This is directly applicable to
`jcheng-benchmark` and acceptance design, independent of Isaac Sim. (S for the
code; C for transferability.)

**F8 — Real-robot evidence is thin.** The paper's sim-to-real claim is a Franka
drawing a logo; no repeated-trial success rate is reported. The secondary
coverage repeats this. It is a qualitative existence demo, not a reliability
measurement. (A/B)

**What would change the conclusion:** a measured, low-variance reproduction of
the benchmark on a 20–50 task subset with a local model; a released builder
pipeline that could regenerate scenes for our Piper cell; a license grant for the
Piper assets; or a ≥48 GB GPU already in inventory. None is true today.

## 09. Engineering Applicability

| Dimension | Assessment |
|---|---|
| Architecture fit | None at runtime. No ROS 2, no DDS, no `ExecuteMotion`; Python/Docker/Isaac Sim only. Can only live outside the dependency graph (like `jcheng-benchmark`), never in `jcheng-simulation` or `jcheng-system`. (A) |
| Hardware | Sim host: x86_64 Linux, RTX GPU, 18–44 GiB VRAM per concurrent sim, ≥8 cores, 32 GB RAM and 30 GB storage per task pack. Model server: 67 GB bf16 + KV. Current inventory (RTX 3060 6 GB laptop, AGX Orin) cannot run it; the README explicitly targets x86_64. (A/C) |
| Compute cost | Not priced here. A single oracle smoke test is minutes-to-tens-of-minutes of GPU; a 500-task frontier run is a multi-GPU-hour campaign plus a 72 GB model endpoint. Any spend needs separate approval. (C) |
| Migration effort | High for actual use: Isaac Sim install, NVIDIA EULA, Harbor 0.25.0, Docker Compose, 72 GB weights, task-format version lock. Low for design reuse: read `task.toml`/`verify.py`/`grade.py`. (A/C) |
| Safety | No path to the real cell, so no new motion risk. If someone later bridges it, the joint-target API would bypass lease/limits/stop latch — that would violate the layer rules and must not be built. (A) |
| Maintenance | One commit, one lab, fast-moving pins (Isaac 5.1, Harbor 0.25.0, SGLang 0.5.21, Claude Code 2.1.283). Abandonment or breaking upstream moves are plausible. (B) |
| Asset reuse | `agilexrobotics/piper_isaac_sim` @ `8e1f88f` is the Piper model source used by 6,675 tasks. It is a candidate asset for future Isaac work, but it has no LICENSE file — do not vendor it before review. (A) |
| Expected gain | As a benchmark: no direct gain for the Piper cell (no matching controller, no real-robot loop). As a design reference: high — the isolation/grading pattern is better than what the workspace currently documents. (C) |

## 10. Recommended Approach

**Recommended — reference-only adoption (no code dependency).** Copy four design
patterns into the benchmark/acceptance discussion, not the code:

1. **Execution–verification isolation**: verifier in a separate, no-network
   container; the agent image has no simulator imports.
2. **Binary verdict with `inconclusive`**: missing or inconsistent evidence is
   not a failure and not a success; infrastructure errors are unscored.
3. **Reward–verdict consistency check**: `reward == int(verdict=="success")`
   enforced by the grader, not trusted from the runner.
4. **Evidence binding**: verifier hashes the scene/backend/config files so a
   passing run cannot be replayed against a different scene.

**Watch item — Piper Isaac Sim assets.** Track `agilexrobotics/piper_isaac_sim`
@ `8e1f88f` as a possible future plant for the fixed cell. Precondition: license
review (no LICENSE file today) and a GPU that can run Isaac Sim. Do not vendor
now.

**Rejected options and why:**

- **Run the benchmark locally now.** Hardware floor unmet; 6 GB vs 18–44 GiB.
- **Use it as VLA/policy training data.** The environments target coding agents;
  there is no policy-training recipe, and the SFT data is GPT-6-Astra
  trajectories, not demonstrations for our arm.
- **Wire it to the real robot.** It would bypass `ExecuteMotion`, lease, limits
  and the stop latch — a layer-rule violation, not an integration.
- **Treat 85.8% / 21.2% as capability evidence for Piper.** Different embodiment,
  different harness, curated suite, no real-robot reliability trial.
- **Adopt RoboDojo instead right now.** It remains the closer operational
  reference (already assessed 2026-11-27); RoboUniverse does not replace it.

**Alternative if a ≥24 GB GPU appears:** run only the oracle smoke test and a
10-task subset, as MVE-1 below, and treat the result as a harness check — not a
model evaluation.

## 11. Experimental Design

**MVE-0 — package audit (desk, no GPU). Status: partially run 2026-11-28.**
Hypothesis: a released archive contains exactly the components the paper claims,
and the agent image contains no privileged data.
Method: download one archive per family, statically list and read
`task.toml`, `instruction.md`, `verify.py`, `tests/grade.py`, the agent client.
Result so far: `000247_rotate_twist` passes — 47 files, verifier present,
stdlib-only client, no object poses in the client, source-hash binding present.
Acceptance: all sampled packages have instruction + verifier + solution and no
privileged state in the agent image. Failure: missing verifier, plaintext
reference solution in the agent image, or a package that fails its own sha256.
Remaining: three AgileX packages, blocked by ≈20 KB/s HF throughput; resume
later, no approval needed (≈6 MB total).

**MVE-1 — oracle smoke test (needs one RTX GPU with ≥24 GB). Status: not run.**
Hypothesis: the README path reproduces "one scored success" for
`000247_rotate_twist` on a clean host.
Baseline: none (the oracle is the reference controller). Variables: GPU model,
driver, Isaac Sim image, Harbor 0.25.0. Metrics: verdict, wall-clock, peak VRAM,
CPU count, infra-error count.
Acceptance: 1/1 scored success, no infra error, wall-clock within the task's
7,200 s agent timeout.
Failure: any infra error, `inconclusive`, or OOM at 6–8 GiB (confirms F5).
Recording: keep the work dir private (contains tokens), record commit + dataset
revision + GPU + driver; write results to `experiments/20261128-*/result.md`.
Rollback: delete work dirs; no repo changes.

**MVE-2 — 10-task oracle subset (same GPU). Status: not run.**
Hypothesis: the verifier has a low false-negative rate on reference solutions.
Acceptance: 10/10 scored successes. Failure: ≤9/10 — then inspect whether the
cause is scene readiness, asset fetch or verifier strictness before any model run.
This is the minimum evidence needed before quoting any model score.

**MVE-3 — model reproduction (optional, needs an API endpoint or the 72 GB
weights). Status: not run; blocked on access and GPU.** Only meaningful after
MVE-2 passes; 20 tasks, same harness and effort as the paper, report per-task
verdicts rather than an aggregate.

## 12. Limitations & Uncertainties

- **No execution.** Every claim about runtime behaviour is static reading or the
  authors' report. The package audit covers one Franka task; AgileX packages were
  not downloaded.
- **Network.** Hugging Face throughput was ≈20 KB/s; the 18.6 GB corpus and 72 GB
  weights were not fetched, so archive-level variety is unverified.
- **Paper v1 only.** No peer review, no appendix PDF read (HTML may omit detail),
  no author clarification.
- **The 68/38 claim remains unexplained, not disproved.** It is absent from the
  only dataset revision; the article may have described an internal draft or may
  be wrong. Either way it is not citable.
- **Hardware-fit inference** relies on the README's measured range and on the
  known 6 GB laptop GPU; no Isaac Sim run was attempted to confirm OOM.
- **Licensing** is a documentary finding, not legal advice; the Piper upstream
  has no LICENSE file, which is a risk flag, not a conclusion.
- **Model names and dates** (GPT-6.2 Astra, Claude Opus 5.5, Qwen3.6, 2026) are
  reported exactly as published; this report does not independently verify the
  models exist or their access terms.

## 13. References

1. Liu, J., Wang, Y., et al. *RoboUniverse-10K: Toward the Scaling Era of Agentic
   Robotics via Real-to-Sim Environments.* arXiv:2611.31002v1, 2026-11-23.
   <https://arxiv.org/abs/2611.31002> (CC BY 4.0).
2. Project page. <https://lab.einsia.ai/robo-universe> (accessed 2026-11-28).
3. Evaluation repository. <https://github.com/Einsia/RoboUniverse-10K> @
   `532745c834` (2026-11-26), Apache-2.0.
4. Dataset. <https://huggingface.co/datasets/Einsia/RoboUniverse-10K> @
   `0775b4832b70` (2026-11-26); `catalog.csv` 1,785,642 B, 10,807 rows;
   `splits/heldout500.csv` 500 rows.
5. Task archive. `tasks/franka/000/000247_rotate_twist.zip`, 1,757,355 B,
   inspected 2026-11-28 (static only).
6. Harbor / Terminal-Bench. arXiv:2601.11868; `harbor==0.25.0` per
   `requirements.txt`.
7. AgileX Piper Isaac Sim assets.
   <https://github.com/agilexrobotics/piper_isaac_sim> @
   `8e1f88fdb7afca49c40e9a0c1c01cc588e86f0d2` (no LICENSE file).
8. AI News, "RoboUniverse opens 10,807 robot tasks — but its released evaluation
   split carries a crucial selection warning", 2026-11-25 (secondary; the
   68/38 claim is not reproduced — D).
9. Workspace context: `AGENTS.md`; `jcheng-simulation/docs/ARCHITECTURE.md`;
   `jcheng-benchmark/README.md`;
   `reports/20261127-mibot-rua-robodojo-agent-track.md`.

Source record: [references/datasets-benchmarks/robouniverse-10k.md](../references/datasets-benchmarks/robouniverse-10k.md).
