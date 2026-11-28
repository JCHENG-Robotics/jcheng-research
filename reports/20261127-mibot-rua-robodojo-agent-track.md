# Mibot-RUA on the RoboDojo agent track — what 83.94 / 79.33% actually measures

> Report status: **draft**. Date: 2026-11-27.
> Author: ZCode research agent. Reviewer: pending.
> Decision this informs: whether Mibot-RUA is evidence of a Xiaomi VLA capability,
> a reproducible agent-track reference, or a rule-flagged leaderboard data point —
> and which RoboDojo protocol rules should enter the JCHENG benchmark/acceptance
> process.
> Research boundary: public web, GitHub API, the robodojo-benchmark.com single-page
> application bundle (not rendered in a browser), Hugging Face metadata, and arXiv
> abstract pages. No RoboDojo run; no knowledge-archive download (the dataset is
> gated); no robot session; no access to GPT-6-Astra.

## 01. Executive Summary

**The entry is a simulation agent-track row, not a model score.** "Add Mibot-RUA*
(Avg. (w/o Open): 83.94 / 79.33%, contributed by Xiaomi Robotics) to the sim
leaderboard (agent track)" is the changelog entry dated 2026/11/26 on
robodojo-benchmark.com. `83.94` is the Score and `79.33%` the success rate under
the agent-track metric **`Avg. (w/o Open)`**, defined in the site bundle as the
mean of four dimensions: generalization (standard and randomized averaged),
precision, long-horizon, and memory. It is not the five-dimension average used on
the main simulation board. (A)

**It is not Xiaomi's VLA.** The only public technical artifact is XPolicyLab pull
request #204, `[policy] Mibot_RSI: add eval-only RoboDojo agent adapter`, open
since 2026-10-26. Its agent is **GPT-6-Astra through the Responses API**: it sees
three RGB cameras plus robot state, writes Python against a small robot SDK, and
moves an **ARX X5** with joint targets. Xiaomi's actual VLA, Xiaomi-Robotics-1
(XR-1), is a separate entry on the main simulation board at **20.07 / 13.93**. (A)

**The asterisk is substantive.** The committee's own findings for Mibot-RUA are
(A):

1. *Task-routed RSI distilled knowledge, experience, demo analyses, and tools*:
   `load_knowledge()` routes by `task_name` (mapping `_random` variants back to the
   base task) and mounts a frozen per-task directory for 34 Standard + 12
   `_random` tasks; only the 8 Open tasks use a general snapshot. Each episode gets
   34 task-specific briefs (23 of 34 include Seed-0 official dev score tables), 289
   task-specific skills, 7,231 task-specific dev-experience entries, 65
   task-specific vision/geometry tools, and 34 offline demo-video analyses.
2. *Task-specific scene and mechanism priors beyond the Detail Description*: 27
   entries in `prompts/priors.json`, including opponent-trigger mechanics in
   `play_tic_tac_toe`, simulator-step behaviour in `make_kong`,
   `match_and_pick_from_conveyor`, `imitate_sorting_sequence`, and which objects
   are fixed in 23 tasks.

Agent Track Rules §2 (Permitted Information) and §4 (General Skill Library,
Harness, VLA, and VLM Use) prohibit exactly this: reusable components must not use
task-specific prompts, memories, action programs, or scoring information prepared
before testing, and task identity must not select a workflow, memory, code path, or
action trajectory. (A)

**Evidence is one seed, not three.** PR #204 reports seed 1 only: 42 tasks × 50
episodes = 2,100 episodes, marked `33.3% † (42/126)`, with **Avg SR 78.43% / Avg
Score 83.75**. The board shows 83.94 / 79.33; the two are close but not identical,
and the board publishes no seed count or standard deviation. The protocol requires
three seeds as mean ± std for simulation results. (A for the PR statement; C for
mapping the board row to that run)

**The agent track is mostly starred.** Of the 15 entries whose manifest type
contains `agent` (`Q()` in the bundle), 11 are in the committee's findings set; the
top nine by the agent metric are all starred. The highest unstarred entry is
WorldScape-R²SI at **45.93 / 37.31**. The agent track is therefore not a clean
compliance ranking, and a star is not proof of non-compliance for unstarred rows
either — it is the committee's disclosure marker. (A)

**Recommendation.** Treat Mibot-RUA as a rule-flagged, single-seed agent-track data
point. Do not cite 83.94 as a Xiaomi VLA capability, as a reproducible SOTA, or as
directly comparable to XR-1's 20.07. Do not attempt RoboDojo reproduction on the
current hardware. Adopt the benchmark's evaluation discipline — three seeds with
mean ± std, hidden-layout checks, artifact release, star/exception marking,
agent-versus-model separation, and explicit `w/o Open` disclosure — not its
task-routed knowledge pattern. (A/C)

**Main risk.** Three independent mismatches make the headline easy to misread:
agent versus VLA, `w/o Open` versus five-dimension, and starred/one-seed versus a
compliant three-seed result. Each alone changes the comparison; together they make
"Xiaomi's model beats the leaderboard" a wrong statement. (A)

## 02. Research Questions

The question as asked: investigate the RoboDojo changelog item "Add Mibot-RUA*
(Avg. (w/o Open): 83.94 / 79.33%, contributed by Xiaomi Robotics) to the sim
leaderboard (agent track)".

Sub-questions:

1. **Identity.** What system is behind `Mibot-RUA`; who submitted it; is it a
   model, an agent, or a re-labelled preview?
2. **Metric.** What exactly do 83.94 and 79.33% measure; which dimensions enter the
   average; how does the agent track differ from the main simulation board?
3. **Compliance.** Why does the entry carry an asterisk; what do the committee's
   findings say; which rules are engaged?
4. **Comparability.** How does it compare with SOLVE, Q0-Preview, PyRUA-Lean, and
   Xiaomi's own XR-1; which comparisons are valid?
5. **Reproducibility.** What is public (code, checkpoint, knowledge, logs); what is
   closed; what would it cost to reproduce?
6. **Applicability.** What, if anything, should JCHENG adopt, monitor, or reject?

Constraints: the ArmPi Ultra is a 5-DoF single arm on a Pi 5; the operator laptop
has an RTX 3060 Laptop (6 GB class); the AGX Orin is ARM/JetPack; there is no
16 GB-VRAM x86 RTX host, no Isaac Sim installation, no GPT-6-Astra endpoint or key,
and no authorization for a hardware session. The deliverable is a public-source
assessment, not a run.

## 03. Current System Analysis

JCHENG's runtime is deliberately narrower than anything RoboDojo evaluates
(`~/jcheng/AGENTS.md` §3, §7, §8):

- **L2 `jcheng-system`** is the only origin of motion: `ExecuteMotion`, lease,
  deadman, limits and the stop latch. Capabilities publish intent; they do not
  drive actuators.
- **L3 `jcheng-perception`, `jcheng-mobile`, `jcheng-learning`, `jcheng-teleop`**
  run on domains 42 (capability) or, for perception in practice, domain 0 with the
  vendor stack; they must not open vendor devices or fabricate TF/odometry.
- **L4 `jcheng-studio`, `jcheng-applications`** are HTTP/WS gateway clients only;
  `jcheng-applications` is an offline planning/runner core over an abstract gateway
  port, not a DDS or device path.
- **SIM `jcheng-simulation`** is the offline plant on domain 43 (deterministic mock
  + Gazebo Harmonic), never a motion source; **BENCH `jcheng-benchmark`** is an
  offline, read-only harness with strict JSONL and provenance-labelled reports.
- **Hardware**: ArmPi Ultra = Raspberry Pi 5 (8 GB), 5-DoF bus-servo arm + gripper,
  D435i/Aurora, LSLIDAR M10 not yet connected; `/joint_states` from the vendor
  stack is a command cache, not measurement; there is no e-stop, brake, encoder or
  self-collision model. The operator laptop is an RTX 3060 Laptop (6 GB class); the
  AGX Orin (64 GB, JetPack 6.2) is ARM and is used for SAM3/Qwen inference, not for
  Isaac Sim.

This matters because RoboDojo's simulation stack is **Isaac Sim 5.1 on Ubuntu
22.04 x86-64**, with documented requirements of **32 GB RAM, 16 GB+ VRAM, NVIDIA
driver 570/580, CUDA 12.8, and 300 GB free disk** for the Docker path. None of the
current machines meets the GPU/OS combination: the 3060 Laptop is below the VRAM
floor, and the Orin is ARM/JetPack rather than x86 Ubuntu 22.04. (A for the
requirements; A for the hardware inventory per the workspace record)

The relevant prior work is the Piper X Gazebo plant (MVE-1, joint2/joint3 tracking
failure still open) and the AGX Orin SAM3/Qwen service. Both follow the same
pattern this report uses: offline evidence first, explicit grades, no hardware
claim without a dated artifact.

## 04. Research Methodology

**Search terms.** `Mibot-RUA`, `Mibot-RSI`, `Mibot_RSI`, `RoboDojo`, `Avg. (w/o
Open)`, `Agent Track Rules`, `Xiaomi-Robotics-1`, `MiBot`, `ffanyt`.

**Primary sources read.**

| Source | Version / identity | What was read |
|---|---|---|
| robodojo-benchmark.com leaderboard bundle | `assets/index-GzJO5R6C.js`, 498,357 bytes, sha256 `a23d17587b8b062304d4d97067ca6260c9d2b01cced7d2f01629069cd4756195`, fetched 2026-11-27 | Embedded `Bo` (simulation rows), `rn` (real-world rows), `qo` (starred-entry findings), changelog array, Agent Track Rules text, metric and rank helpers |
| RoboDojo repository | `RoboDojo-Benchmark/RoboDojo` @ `c3af1ac6ad7302c0c09d17f4b050fd3a5c68c921` (2026-11-19) | `README.md` in full; install/download doc page |
| RoboDojo paper | arXiv:2607.04434, v1 2026-07-05, v3 2026-07-08 | Abstract page only |
| XPolicyLab repository | `XPolicyLab/XPolicyLab` @ `24c49cb3e217080af6c66bd7704711d78562fbe0` (2026-11-26) | `policy/` listing (83 directories); `policy/Xiaomi_Robotics_1/README.md` |
| XPolicyLab PR #204 | `ffanyt/XPolicyLab:mibot-rsi`, head `c048d3b3f111de2d2607dbfc3e7c14bf243c0cf8`, open, 11 commits, 50 files, +11,692 | PR body in full; file list; `README.md`, `runtime/EXPORT.json`, `release.json` (head), `prompts/priors.json`, `submission.py` lines 455–525, `runtime/context.py` lines 60–100, `knowledge/store.py` lines 930–1000 |
| Hugging Face dataset | `ffanyt/Mibot-RSI-knowledge-latest`, gated `manual`, public, last modified 2026-11-11, revision `a182734b5f271d522c6ff9b8718bac7553a7dbb9` | Metadata and file list only; no archive download |
| Xiaomi XR-1 | `XiaomiRobotics/Xiaomi-Robotics-1` @ `0dd7aef8dc87296246aae812a1f59ccb708e5546` (2026-09-09), Apache-2.0; HF `XiaomiRobotics/Xiaomi-Robotics-1-5B`; arXiv:2607.15330 | README/model card; paper abstract |
| PyRUA-Lean | `DAGroup-PKU/PyRUA-Lean` @ `8543207e80e17176f2f0d010cb52303d446e951a` (2026-11-26), Apache-2.0; arXiv:2610.01939 | `README.md` news and claims; paper not read |
| Xiaomi Robotics GitHub org | 3 public repositories | Repository list only |
| PR author profile | `ffanyt` | Public profile fields only |

**Exclusion criteria.** Search-engine summaries without a resolvable URL were not
used as evidence; unrelated "Mibot" hits (KG Motors microcar, head-massage robot,
vacuum brand) were discarded. The PR's full 11,692-line diff, the knowledge
archives, the RoboDojo paper body, and the XPolicyLab paper were not read; claims
that would require them are marked accordingly.

**Why the scope was cut.** The leaderboard has no public JSON API; the SPA bundle
is the authoritative static data. There is no GPU that satisfies Isaac Sim 5.1 and
no GPT-6-Astra credential, so a run is not possible in this environment. The
knowledge dataset is manually gated, so its contents could not be inspected beyond
the pinned manifest and the PR's own description.

## 05. Literature Review

**RoboDojo (arXiv:2607.04434).** *Read scope: abstract only; no ablation or
baseline judgement.* The paper frames existing manipulation benchmarks as
short-horizon or single-mode (sim-only or real-only) and proposes a unified
sim-and-real benchmark: 42 simulation tasks and 18 real-world tasks, five
simulation dimensions (generalization, memory, precision, long-horizon execution,
open-vocabulary instruction following), heterogeneous parallel simulation in Isaac
Sim, a reproducible real-world system (RoboDojo-RealEval) with cloud access and
standardized hardware, and XPolicyLab as the integration layer. It reports 30
policies integrated and a public leaderboard. The repository README confirms the
release is eval-only, the real tasks use ARX X5, Piper and Piper X, and the license
is MIT. The relevant fact for this report is the five-dimension definition: **Open
means open-vocabulary instruction following**, not "open source". (A for the
README and abstract; B for details that would require the full paper)

**Xiaomi-Robotics-1 (arXiv:2607.15330).** *Read scope: abstract + repository
README + model card.* XR-1 is a 5B VLA initialized from Qwen3-VL-4B-Instruct,
coupled to a Diffusion Transformer through a Mixture-of-Transformers; pre-trained
on more than 100K hours of embodiment-free UMI trajectories and post-trained on
more than 10K hours of cross-embodiment data. The abstract claims 57.4% on
RoboCasa365 (previous best 46.6%) and **20.07 average on RoboDojo** (previous best
13.07). The code and the `model_states.pt` checkpoint are public under Apache-2.0.
This is the actual Xiaomi VLA entry on the main board; it is not Mibot-RUA. (A)

**XPolicyLab (arXiv:2608.09892, cited by the RoboDojo README).** *Not read.* The
repository is the policy-integration layer behind RoboDojo: 83 policy directories,
one `deploy.yml`/`eval.sh` per policy, and a shared websocket protocol. The
`Xiaomi_Robotics_1` adapter is the official XR-1 integration; its README still says
"Paper: Not released | arXiv: Not released", which is stale relative to
arXiv:2607.15330. (A for the repository layout and README; the paper is unread)

**PyRUA-Lean (arXiv:2610.01939).** *Read scope: repository README only.* The
PKU DAGroup agent holds the pre-Mibot agent-track top spot. Its README claims
"Score 55.26 and a 50.35% average success rate" (the five-dimension average) and
later "82.82% average success rate (Score 87.16)" for the offline RSI variant on
seed 0. On the agent-track metric computed from the same board data, PyRUA-Lean is
**53.93 / 48.37** (four dimensions). The gap between 55.26 and 53.93 is the Open
dimension, not a data error. PyRUA-Lean is Apache-2.0 with released programs and is
the most reproducible agent reference in this group. (A for the board arithmetic;
B for the README's self-reported numbers)

**Mibot-RUA / Mibot_RSI.** *No paper, no technical report.* The only public
description is PR #204 and its runtime. The name "MiBot" is Xiaomi's family name
for the XR-0/XR-1 codebase and its `mibot` conda environment, not a published model
called "Mibot-RUA". (A)

## 06. Repository Investigation

### 6.1 PR #204 — the only Mibot-RUA artifact

- **State.** Open, created 2026-10-26, last updated 2026-11-12, head
  `ffanyt/XPolicyLab:mibot-rsi` at `c048d3b3f111de2d2607dbfc3e7c14bf243c0cf8`;
  11 commits, 50 files, +11,692 lines. No review comments. (A)
- **Policy name.** `Mibot_RSI`; the leaderboard row is `Mibot-RUA`, and the
  2026/11/14 changelog calls the pending entry `Mibot-RUA-Preview`. The rename is
  not explained publicly, but the committee's finding cites "XPolicyLab PR #204",
  so the mapping is direct. (A)
- **Architecture.** Eval-only agent: `GPT-6-Astra` via the Responses API observes
  three RGB cameras and robot state, writes Python against a small robot SDK, and
  issues end-effector motions that are converted to joint targets and executed
  through `TASK_ENV.take_action` on an ARX X5 (`bench_name=RoboDojo`,
  `env_cfg_type=arx_x5`, `action_type=joint`, `eval_batch=false`). No network is
  trained; `process_data.sh` and `train.sh` are omitted. (A)
- **Runtime.** `policy/Mibot_RSI/runtime/` is an export of the agent code, pinned
  by `EXPORT.json` (36 files, each with a sha256; the export commit is
  `42e0d7c7637adf655d7ad8e6a31875ac645213f9`). `runtime/v2/knowledge/store.py` is
  1,254 lines, `runtime/v2/submission.py` 1,257 lines, `runtime/v2/runtime/context.py`
  380 lines, `runtime/v2/runtime/loop.py` 1,101 lines; the agent runs in a
  subprocess inside the evaluation client. (A)
- **Knowledge.** `release.json` pins dataset `ffanyt/Mibot-RSI-knowledge-latest`
  at revision `a182734b5f271d522c6ff9b8718bac7553a7dbb9`; `knowledge.ckpt_name` is
  `eval`. It pins 34 per-task archives plus a `general` archive (927,432 bytes, 50
  files) whose `tasks` list is exactly the eight Open tasks: `align_blocks`,
  `classify_objects_by_language`, `general_pickup`,
  `pick_from_conveyor_by_image`, `pour_by_language`, `solve_equation`,
  `stack_blocks_by_language`, `store_tools_in_toolbox`. (A)
- **Task routing.** `load_knowledge(task, root, policy_dir, ckpt)` in
  `runtime/v2/submission.py` (the `load_knowledge` definition begins around line
  464) maps the task to its base task (`standard_task(task)`), resolves
  `<root>/<knowledge_task>`, checks `release.json` pins, verifies every file
  against the manifest, and refuses to run with an empty, unpinned or altered
  snapshot. A `_random` variant reads its standard task's snapshot; a task with no
  snapshot reads the general snapshot only if `release.json` pins it. (A)
- **Priors.** `runtime/v2/runtime/context.py` `actor_instructions(episode,
  instruction, prior=None, knowledge=None, handoff=None)` passes `prior` into
  `task_section(...)`; `prompts/priors.json` has 27 task keys, including mechanics
  absent from the official description: `play_tic_tac_toe`'s opponent trigger
  ("whenever the cells hold exactly one more of your pieces than of the opponent's
  and both your arms are back near their initial poses"), `make_kong`'s
  simulator-step behaviour, the conveyor behaviour in
  `match_and_pick_from_conveyor`, the demonstrator replay in
  `imitate_sorting_sequence`, and the fixed-object lists for 23 tasks. (A)
- **Knowledge contents.** `knowledge/store.py` `prompt_text(task)` returns the task
  brief, skill index and tool list; `build_generated()` writes `INDEX.md` and
  `stats.json`. The committee's finding quantifies the snapshot: 34 task briefs
  (23 with Seed-0 official dev score tables), 289 skills, 7,231 experience
  entries, 65 vision/geometry tools, and 34 demo-video analyses. (A for the code
  path; B for the counts, which come from the committee's review rather than a
  downloaded archive)
- **Evaluation reported in the PR.** 42 tasks × 50 episodes, **seed 1 only**;
  the summary is marked `33.3% † (42/126)`, i.e. one seed of three. Reported
  averages: **SR 78.43% / Score 83.75**; Generalization 73.83 / 79.97; Precision
  72.50 / 75.83; Long-Horizon 75.25 / 86.36; Memory 96.33 / 97.45; Open 74.25 /
  79.12; Generalization standard/random halves SR 76.67 / 71.00 and Score 82.37 /
  77.58. (A)
- **Cost and failure handling.** In a 162-episode sample: median 34 min per
  episode (max 118), median 55 model calls, about 3M input tokens (91% served from
  cache) and 15k output tokens; 0.3–1 GB of agent records per episode; 6-hour
  episode limit; infrastructure failures exit 99 and replay the layout with the
  same `ROBODOJO_RUN_ID`, up to 9 retries. (A)

### 6.2 Committee findings for Mibot-RUA

The bundle's `qo` object carries the committee's starred-entry findings. For
Mibot-RUA there are two, with evidence citations to the PR:

1. *Task-routed RSI distilled knowledge, experience, demo analyses, and tools* —
   `submission.py:464–515`; `store.py:947–984`; `context.py:74–89`.
2. *Task-specific scene and mechanism priors beyond the Detail Description* —
   `context.py:43–57`; `prompts/priors.json`.

The second finding explicitly says the priors disclose conditions absent from the
official Detail Description and that "a documented historical source does not by
itself make that information permissible" (this sentence appears in the
neighbouring entry, but the same logic applies to the two Mibot-RUA findings). The
rules' §4 adds: "Preparing a complete operating procedure for a single task before
testing is not compliant", "Selecting prewritten task-specific action-output code
using the task name, task_id, seed, layout, or object identity is not compliant",
and "Packaging a single-task workflow prepared before testing as a skill, lesson,
recipe, memory, or knowledge artifact is not compliant." (A)

### 6.3 Leaderboard data and metric

- The bundle carries the simulation rows in `Bo` and the real-world rows in `rn`.
  Each simulation row has `generalizationStd`, `generalizationRand`, `precision`,
  `longHorizon`, `memory`, optional `open`, and `average`, each as
  `o(score, successRate)`.
- `ln(e)` builds the row: for an agent-typed entry (`Q()` is true), `overall` is
  `mean([mean(generalizationStd, generalizationRand), precision, longHorizon,
  memory])`, stored as `dimensions.sft`; for other entries, `overall` is the
  five-dimension `average`. The display label for `sft` is **`Avg. (w/o Open)`**.
- `Mp(e, "sim", ...)` filters `!Q(n)`, i.e. the main simulation board excludes
  agents; the bundle titles it `RoboDojo Sim Leaderboard (w/o Agent)`. The agent
  track is the complementary set.
- `kc(model, board)` returns `null` when the model is an agent and its name is in
  the starred set (`Qe()`), so a starred agent has no computed rank in that helper;
  the table's `ra()` still assigns a display rank by sorting. This report
  therefore reports the sorted position as a data property, not as an official
  compliant rank. (A for the code; C for how the UI finally renders it, which was
  not browser-verified)

For Mibot-RUA the numbers are: generalization standard 74.87 / 70, randomized
75.27 / 69.67, precision 76.39 / 73.5, long-horizon 87.09 / 77, memory 97.23 / 97,
average 83.94 / 79.33, and **no `open` value**. The four-dimension mean reproduces
83.94 / 79.33 exactly: `(75.07 + 76.39 + 87.09 + 97.23) / 4 = 83.945` and
`(69.835 + 73.5 + 77 + 97) / 4 = 79.334`. (A; reproduced from the bundle)

### 6.4 The public Xiaomi artifacts

- `XiaomiRobotics/Xiaomi-Robotics-1`: 764 stars, Apache-2.0, paper
  arXiv:2607.15330, 5B checkpoint `model_states.pt`, Qwen3-VL-4B-Instruct backbone.
  The RoboDojo entry is **Xiaomi-Robotics-1, 20.07 / 13.93** (five-dimension
  average). The paper's own claim is 20.07, "significantly outperforming the prior
  state-of-the-art (13.07)". (A)
- `XiaomiRobotics/Xiaomi-Robotics-0`, `Xiaomi-Robotics-U0`: two more public VLA
  repositories; no Mibot-RUA repository. The organization has exactly three public
  repositories. (A)
- The `Xiaomi_Robotics_1` XPolicyLab adapter says it is "the adapter for Xiaomi's
  MiBot model" and uses a Qwen3-VL-4B-Instruct processor; its header still says
  "Paper: Not released | arXiv: Not released", which is stale. (A)

### 6.5 Attribution

The leaderboard credits **Xiaomi Robotics**. PR #204's contributor line says
**"Mibot-RSI team"**, and the GitHub account `ffanyt` lists
**Harbin Institute of Technology** as its company and has five public repositories,
none of them Mibot. Additional checks at access time:

- All 11 PR commits use `ffanyt@users.noreply.github.com` or
  `96506495+ffanyt@users.noreply.github.com`; no commit carries a corporate
  address such as `@xiaomi.com`.
- GitHub code search for `Mibot_RSI` returns nine hits, all in one third-party
  "Awesome-Embodied-Memory" list; `Mibot-RUA` returns zero. GitHub commit search
  for `Mibot-RSI` returns zero. There is no Xiaomi organization repository.
- The official Xiaomi-Robotics-1 project page reports RoboDojo **13.93** (the VLA)
  and does not mention an agent or Mibot-RUA.
- The leaderboard's logo mapping uses `/data/mibot-xiaomi-logo.png`, a
  Xiaomi-branded asset, so the committee accepted a Xiaomi-branded submission
  rather than an anonymous one.

The defensible reading is: **the leaderboard and its changelog attribute the entry
to Xiaomi Robotics; the public code trail does not independently confirm a Xiaomi
employment, ownership, or authorization relationship.** The "MiBot" name is
consistent with Xiaomi's family name (the `Xiaomi_Robotics_1` adapter calls XR-1
"Xiaomi's MiBot model"), but the adapter and the agent are different systems, and
naming is not attribution. Plausible explanations are a Xiaomi team submitting
through an individual account, a joint Xiaomi–HIT team, a stale GitHub profile, or
a misattribution; the public record cannot distinguish them. (A for the statements
and checks; C for the interpretation)

## 07. Comparative Analysis

### 7.1 Same-track comparison (agent metric, `Avg. (w/o Open)`)

Computed from the bundle's `Bo` rows, sorted by the four-dimension mean; starred
means the committee published at least one finding (A):

| # | Entry | Manifest type | Score / SR | Open | Starred |
|---:|---|---|---:|---|---|
| 1 | **Mibot-RUA** | agent | **83.94 / 79.33%** | none | yes |
| 2 | SOLVE (NVIDIA) | agent | 79.50 / 74.96% | none | yes |
| 3 | Q0-Preview (Qoo Tech) | agent | 73.20 / 67.34% | 78.20 / 75.00 | yes |
| 4 | Agent-as-Policy (Realworld Labs) | agent | 63.46 / 54.42% | 57.94 / 56.75 | yes |
| 5 | GO-3 Nano Preview (AGIBOT) | agent-wam | 61.95 / 56.71% | 61.71 / 55.25 | yes |
| 6 | SenseNova-RoboRSI | agent-vla | 57.10 / 49.17% | 58.56 / 55.50 | yes |
| 7 | PyRUA-Lean (PKU DAGroup) | agent | 53.93 / 48.37% | 60.56 / 58.25 | yes |
| 8 | HexaShell-Preview (HexaFuture) | agent | 51.98 / 44.75% | 57.97 / 55.25 | yes |
| 9 | JoyAI-VL (Joy Future Academy) | agent | 48.67 / 41.21% | 47.50 / 45.50 | yes |
| 10 | WorldScape-R²SI (Manifold AI) | agent-wam | 45.93 / 37.31% | 49.16 / 47.50 | no |
| 11 | EmbodiedEvo (Einsia.AI) | agent | 43.40 / 36.38% | 51.81 / 49.25 | yes |
| 12 | PhysicalRSI (HKU MMLab & KAI) | agent-vla | 38.12 / 33.00% | 28.88 / 24.92 | yes |
| 13 | GPT-6-Astra (RoboDojo Team) | agent | 27.63 / 20.36% | 34.36 / 31.00 | no |
| 14 | DeepSeek-Flash (RoboDojo Team) | agent | 2.12 / 0.83% | 6.50 / 6.25 | no |
| 15 | GPT-5.5 (RoboDojo Team) | agent | 0.70 / 0.42% | 2.87 / 2.75 | no |

Two observations follow directly. First, the top nine are all starred; the best
unstarred row is WorldScape at 45.93. Second, the top two rows (Mibot-RUA and
SOLVE) have no Open value, while the rows below them do; the `w/o Open` metric is
the same for all, but the completeness of the evaluation differs. (A)

### 7.2 Cross-track comparison (not directly comparable)

| Entry | Track / type | Published metric | Score / SR | Open | Starred | Seeds | Public artifact |
|---|---|---|---:|---|---|---|---|
| Mibot-RUA | sim agent | Avg. (w/o Open) | 83.94 / 79.33% | none | yes | 1 (PR) | PR #204, gated knowledge, closed API |
| SOLVE | sim agent | Avg. (w/o Open) | 79.50 / 74.96% | none | yes | n/a | PR (not inspected) |
| PyRUA-Lean | sim agent | Avg. (w/o Open) | 53.93 / 48.37% | 60.56 / 58.25 | yes | n/a | Apache-2.0 repo + programs |
| Xiaomi-Robotics-1 | sim VLA model | Average (5-dim) | 20.07 / 13.93% | 3.94 / 3.58 | no | paper | Apache-2.0 repo + 5B checkpoint |
| Xiaomi-Robotics-0 | sim VLA model | Average (5-dim) | 6.93 / 4.18% | 0.22 / 0.17 | no | n/a | public repo |

The 83.94-versus-20.07 gap is not a like-for-like model comparison: it crosses the
agent/model track boundary, the `w/o Open`/five-dimension metric boundary, and the
starred/one-seed versus paper/three-seed boundary. The only defensible statement is
that **Xiaomi Robotics has two entries of different kinds**: an agent that uses
GPT-6-Astra plus task-specific knowledge and is flagged, and a 5B VLA that scores
20.07 under the main-board metric. (A/C)

### 7.3 Contradictions and stale documents

- **PyRUA-Lean's 55.26 versus 53.93.** The README's 55.26 is the five-dimension
  score; the agent-track `sft` is 53.93. Both are correct for their metric; the
  changelog's dynamic `ne()` helper renders the agent metric. (A)
- **XR-1 adapter README versus XR-1 paper.** The adapter says the paper is not
  released; arXiv:2607.15330 exists and the repository links it. The adapter text
  is stale, not evidence that the model is unpublished. (A)
- **Board 83.94 versus PR 83.75.** The PR's seed-1 summary is 83.75 / 78.43; the
  board shows 83.94 / 79.33. The dimension values also differ
  (e.g. long-horizon score 87.09 on the board versus 86.36 in the PR). The most
  likely explanation is a later official run or a different aggregation; there is
  no public note. Treat the board row as authoritative for the displayed number and
  the PR as the closest public run description, without assuming they are the same
  execution. (A for the discrepancy; C for the explanation)
- **Agent-track governance.** The 2026/11/14 changelog says all starred entries
  were tested before the latest rules and that Mibot-RUA-Preview was "the final
  entry whose testing had already begun before the latest Agent Track Rules took
  effect". The 2026/11/26 entry then appears as `Mibot-RUA*`. The star is therefore
  both a timing marker and, for this entry, a substantive knowledge/priors finding.
  (A)

## 08. Critical Findings

1. **Mibot-RUA is an agent, not a VLA.** It uses GPT-6-Astra as the decision
   maker, Python as the action medium, and a robot SDK for joint execution. Its
   scores say nothing about Xiaomi's VLA weights. (A)
2. **The knowledge is task-routed and pre-tested.** 34 per-task snapshots plus a
   general snapshot for the 8 Open tasks; 289 skills, 7,231 experiences, 65 tools,
   34 video analyses; 27 priors beyond the official description. Rules §2/§4
   prohibit exactly this; the committee's findings cite the code lines. (A)
3. **The result is single-seed.** The PR marks itself 33.3% complete (42/126
   cells); the protocol requires three seeds as mean ± std. No std is published on
   the board. (A)
4. **The headline metric is `w/o Open`.** The agent track deliberately excludes
   the open-vocabulary dimension; the main board uses five dimensions and excludes
   agents. Comparing 83.94 with 20.07 without saying this is a category error. (A)
5. **The top of the agent track is starred.** 11 of 15 agent-typed rows carry
   findings; the top nine are all starred; the best unstarred row is 45.93. The
   board is a disclosure list, not a clean compliance ranking. (A)
6. **Reproduction is gated.** The decision maker is a closed API endpoint
   (`MIBOT_RSI_BASE_URL` / `MIBOT_RSI_API_KEY`); the knowledge is a manually gated
   HF dataset; the practice code that produced the snapshots is promised "within
   three days of the leaderboard listing" (listing 2026-11-26, so by 2026-11-29)
   but was not present at access time; the PR is still open. (A)
7. **The cost is not a local-robot cost.** Median 34 min and 55 model calls per
   episode, ~3M input tokens (91% cached), 2,100 episodes for one seed. That is
   roughly 1,190 episode-hours and ~6.3B input tokens per seed if serial (derived,
   C), before considering the simulator's GPU time. (A for the per-episode figures;
   C for the extrapolation)
8. **Attribution is unresolved.** The leaderboard says Xiaomi Robotics; the PR's
   contributor is "Mibot-RSI team"; the public GitHub account lists HIT; no Xiaomi
   repository, model card, paper, or announcement for Mibot-RUA was found. (A/C)
9. **The board row lacks Open.** The PR reports Open 74.25 / 79.12 for seed 1, but
   the board row has no `open` key. This does not change the agent metric (which
   excludes Open), but it means the public row cannot be used to assess
   open-vocabulary behaviour. (A)
10. **What would change the conclusion.** A three-seed, rules-compliant rerun
    without task-routed knowledge and without task-specific priors, with the
    practice code and full logs released and the star removed, would make this a
    legitimate agent-track result. A Xiaomi statement or paper naming Mibot-RUA
    would settle attribution. Neither exists as of 2026-11-27. (C/D for the
    counterfactual)

## 09. Engineering Applicability

**Hardware: not runnable here.** RoboDojo's simulation requires Ubuntu 22.04
x86-64, 32 GB RAM, 16 GB+ VRAM, driver 570/580, CUDA 12.8, Isaac Sim 5.1, and
300 GB free disk for the Docker path. The 3060 Laptop is 6 GB class; the AGX Orin
is ARM/JetPack, not x86 Ubuntu 22.04; the Pi 5 is not an Isaac Sim host. The gap is
not a configuration detail; it is a different machine class. (A for the
requirements; A for the hardware inventory)

**Embodiment: not the ArmPi.** The simulation embodiments are ARX X5 (dual arm) and
the real track uses ARX X5, Piper and Piper X. The ArmPi Ultra is a 5-DoF single
arm with a gripper; RoboDojo has no ArmPi profile. Piper X is the closest
embodiment the owner has studied, but the owner has a Gazebo plant, not a RoboDojo
real-track setup. (A)

**API and cost: not a local option.** Mibot-RUA needs a Responses API endpoint
serving `gpt-6-astra` plus a key; the PR explicitly stores neither. The per-episode
token and latency figures make a full 42-task × 50-episode × 3-seed run a
cloud-billed workload, not a laptop experiment. (A)

**Safety: no path into L2.** RoboDojo is an eval-only harness; it does not use
JCHENG's lease, stop latch, or `ExecuteMotion`. Nothing in this investigation
changes `jcheng-system`'s safety boundary. Importing an LLM agent that writes
Python and commands joints into the L2 path would violate the existing layer rules
and would not inherit the stop latch; this is rejected. (A/C)

**What transfers (protocol, not code):**

- **Three seeds, mean ± std** for simulation results; a single-seed number is not a
  leaderboard claim. (A)
- **Hidden-layout verification** as an auxiliary consistency check; public layouts
  remain the primary set. (A)
- **Artifact release**: checkpoints, training/deployment code, configs, and
  reproduction instructions within three days of listing; "Pending verification"
  until reviewed. (A)
- **Star/exception marking** with a public explanation of the specific deviation,
  and separate display of the result. (A)
- **Agent-versus-model separation** in the ranking and in the metric; the agent
  track's `w/o Open` average is disclosed rather than folded into the main board.
  (A)
- **Task identity may select the official instruction and permitted demonstrations,
  but must not select a workflow, memory, code path, or action trajectory.** This is
  the cleanest one-sentence rule in the protocol and is directly reusable in
  `jcheng-benchmark`/`ACCEPTANCE`. (A)

**What does not transfer:** the task-routed knowledge snapshots, the 27 priors, the
GPT-6-Astra dependency, the Isaac Sim stack, and the ARX X5 dual-arm assumptions.
Adopting the knowledge pattern would make any JCHENG generalization claim
non-compliant under the same rules, and it would not fit the 5-DoF ArmPi anyway.
(A)

## 10. Recommended Approach

**Recommended.**

1. **Classify, do not cite.** Record Mibot-RUA as a starred, single-seed
   agent-track result, not as a Xiaomi VLA capability and not as a reproducible
   SOTA. If a number is quoted, quote it with the four qualifiers: agent track,
   `Avg. (w/o Open)`, starred, one seed. (A)
2. **Adopt the protocol rules, not the method.** Add the six transferable rules in
   §09 to the `jcheng-benchmark`/`ACCEPTANCE` review checklist; in particular, ban
   task-specific pre-tested knowledge and require three-seed mean ± std for any
   claim labelled "benchmark". (A/C)
3. **Use open references if reproduction is ever attempted.** PyRUA-Lean
   (Apache-2.0, 53.93/48.37 on the agent metric) and XR-1 (Apache-2.0, 20.07 on the
   main board) are the reproducible baselines; Mibot-RUA is not, because its
   decision maker and knowledge are gated. (A)
4. **Monitor two dates.** PR #204's merge/review state and the promised practice-code
   release (due by 2026-11-29); and whether a three-seed result or a star removal
   appears. Re-open this report only if one of those changes. (C)

**Alternatives.**

- **Defer entirely** until a compliant three-seed result exists. Cost: nothing;
  benefit: no risk of quoting a flagged number. This is acceptable if the only goal
  is a trend line.
- **Reproduce PyRUA-Lean on a rented 24 GB x86 GPU** on four tasks and one seed, to
  measure the agent-versus-VLA gap without the closed API. Cost: GPU rental plus
  Isaac Sim setup; benefit: an independently measured agent baseline.
- **Run an agent-style MVE on the existing Piper X Gazebo plant** (not RoboDojo) to
  test whether an LLM writing Python against a bounded SDK beats a scripted policy
  on 2–3 tasks. This is the cheapest way to learn the same lesson without Isaac
  Sim.

**Rejected.**

- Running RoboDojo on the 3060 Laptop or the Orin: the VRAM/OS gate is hard.
- Citing 83.94 as "Xiaomi's model" or as a VLA result: category error.
- Adopting the task-routed knowledge pattern for JCHENG claims: explicitly
  non-compliant, and it teaches the wrong lesson (task-specific memorization, not
  generalization).
- Treating the board row as independently verified: the number is the committee's,
  the run is one seed, and the PR is open.

## 11. Experimental Design

**MVE-0 (run, static): recompute the agent-track metric.** Hypothesis: the
published 83.94 / 79.33% is exactly the four-dimension mean of the row's
generalization (std+rand)/2, precision, long-horizon, and memory. Baseline: the
bundle's own `average` field. Variables: none (deterministic). Environment: the
SPA bundle at the sha256 above, parsed with Node and Python. Metrics: score and SR
to two decimals. Acceptance: reproduce both numbers and the 15-row agent ordering.
Failure: any mismatch greater than 0.01. Result: **pass**; 83.945 → 83.94 and
79.334 → 79.33; the ordering is the table in §7.1. Recording: this report and the
bundle hash. Rollback: none (read-only).

**MVE-1 (run, static): audit the task routing and priors.** Hypothesis: the PR
routes knowledge by `task_name`, mounts per-task snapshots for 34 Standard + 12
`_random` tasks, and injects 27 task-specific priors. Baseline: the committee's two
findings. Variables: none. Environment: PR #204 head `c048d3b`, raw files. Metrics:
presence of `standard_task(task)` routing, `release.json` task pins, `priors.json`
key count, and the `actor_instructions(..., prior=...)` call. Acceptance: all four
present with file/line evidence. Failure: any claim unsupported by the files.
Result: **pass**; see §6.1. Recording: this report. Rollback: none.

**MVE-2 (not run): reproduce an open agent and an open VLA on a small RoboDojo
subset.** Hypothesis: on the same four tasks and one seed, an open agent
(PyRUA-Lean) exceeds an open VLA (XR-1) by more than 20 points on the agent metric.
Baseline: the published per-task numbers. Independent variable: policy. Controlled
variables: tasks, seed 0, assets, camera configuration, episode count. Environment:
a rented x86 Ubuntu 22.04 host with ≥24 GB VRAM, Isaac Sim 5.1, 300 GB disk.
Metrics: per-task SR and score, the four-dimension mean, wall-clock per episode,
and failure modes. Acceptance: reproduce the published per-task numbers within
±10 points. Failure: a deviation above ±20 points, or an infrastructure failure that
prevents a complete seed. Recording: `runs/`, `summarize` output, a JSONL log with
the commit SHAs. Rollback: none (offline); delete the rented instance. **Status: not
run; no such host or budget was available.**

**MVE-3 (not run): protocol audit of `jcheng-benchmark`.** Hypothesis: the current
harness lacks explicit rules for task-specific pre-tested knowledge, three-seed
mean ± std, and star/exception marking. Baseline: the existing gate. Variables:
none. Environment: the repository. Metrics: a nine-rule checklist mapped to
existing tests/gates. Acceptance: each rule is either covered by a test or listed
as a gap. Failure: a rule cannot be mapped. Recording: a checklist in the report or
a follow-up issue. Rollback: none (documentation only). **Status: not run.**

## 12. Limitations & Uncertainties

- **The leaderboard is a SPA snapshot.** The data was read from
  `assets/index-GzJO5R6C.js` (sha256 in §4), not from an API or a rendered page.
  The bundle's `updated_at` constant is `2026-11-18T00:00:00.000Z` while the
  changelog contains a 2026-11-26 entry; the site may rebuild with different data.
  I did not open a browser, so the final visible rank/asterisk rendering is
  inferred from the bundle code, not observed. (B)
- **The board row and the PR run may not be the same execution.** The board shows
  83.94 / 79.33; the PR's seed-1 summary is 83.75 / 78.43, with different
  dimension values. The mapping is plausible but unproven. (C)
- **The seed count and standard deviation are not published on the board.** The PR
  says one seed of three; the board does not repeat that. The protocol's three-seed
  requirement is therefore not evidenced as satisfied. (A/C)
- **The knowledge archives were not downloaded.** The HF dataset is gated
  (`manual`), and the committee's counts (289 skills, 7,231 experiences, 65 tools)
  come from its review, not from my inspection. The `release.json` pins and the
  `priors.json` keys were read directly. (B for the counts)
- **The PR is open and may change.** Head `c048d3b` (2026-11-12); the leaderboard
  entry was added 2026-11-26. A later commit could add the practice code or change
  the numbers. (A for the state at access; C for the future)
- **Attribution is unresolved.** The leaderboard credits Xiaomi Robotics; the PR
  author's public profile lists HIT; all PR commits use GitHub noreply addresses;
  GitHub code/commit search finds no Xiaomi repository; the official XR-1 project
  page does not mention the agent. This report does not assert an employment
  relationship in either direction; it quotes the board's attribution and marks
  the gap. (C)
- **`Open` semantics.** The RoboDojo paper defines Open as open-vocabulary
  instruction following. The agent track excludes it; the Mibot-RUA row has no
  `open` value; the PR reports Open numbers. I cannot tell whether the board
  intentionally omits it for this row or the submission did not provide it. (A/C)
- **Dates and timezone.** The changelog dates are likely UTC+8; this report uses
  the dates as displayed and the access date 2026-11-27.
- **No independent verification.** The 83.94 is the committee's number. MVE-2
  would be the first independent check; it was not run.

## 13. References

**Leaderboard and protocol**

1. RoboDojo leaderboard: <https://robodojo-benchmark.com/leaderboard> (accessed
   2026-11-27). The SPA bundle is
   <https://robodojo-benchmark.com/assets/index-GzJO5R6C.js>, 498,357 bytes,
   sha256 `a23d17587b8b062304d4d97067ca6260c9d2b01cced7d2f01629069cd4756195`.
2. Changelog entry 2026/11/26: "Add Mibot-RUA* (Avg. (w/o Open): 83.94 / 79.33%,
   contributed by Xiaomi Robotics) to the sim leaderboard (agent track)." Also the
   2026/11/14 entry on starred entries and the Mibot-RUA-Preview.
3. Agent Track Rules, sections 2 (Permitted Information), 3 (No Iterative
   Optimization from Layout Rollout Feedback), 4 (General Skill Library, Harness,
   VLA, and VLM Use), 8 (Leaderboard Display and Official Endorsement); the
   protocol's three-seed requirement is in the evaluation-policy requirements.

**RoboDojo**

4. `RoboDojo-Benchmark/RoboDojo`, MIT, 960 stars, HEAD
   `c3af1ac6ad7302c0c09d17f4b050fd3a5c68c921` (2026-11-19):
   <https://github.com/RoboDojo-Benchmark/RoboDojo>; `README.md` read in full.
5. RoboDojo paper, arXiv:2607.04434, v1 2026-07-05, v3 2026-07-08:
   <https://arxiv.org/abs/2607.04434> (abstract only).
6. RoboDojo installation requirements:
   <https://robodojo-benchmark.com/doc/usage/install-and-download/> (Ubuntu 22.04
   x86-64, 32 GB RAM, 16 GB+ VRAM, driver 570/580, CUDA 12.8, Isaac Sim 5.1,
   300 GB disk).

**Mibot-RUA / Mibot_RSI**

7. XPolicyLab PR #204, `[policy] Mibot_RSI: add eval-only RoboDojo agent adapter`,
   open, created 2026-10-26, head `ffanyt/XPolicyLab:mibot-rsi`
   `c048d3b3f111de2d2607dbfc3e7c14bf243c0cf8`:
   <https://github.com/XPolicyLab/XPolicyLab/pull/204>.
8. `policy/Mibot_RSI/README.md`, `runtime/EXPORT.json` (commit
   `42e0d7c7637adf655d7ad8e6a31875ac645213f9`), `release.json`,
   `runtime/v2/prompts/priors.json`, `runtime/v2/submission.py` (lines 455–525),
   `runtime/v2/runtime/context.py` (lines 60–100), `runtime/v2/knowledge/store.py`
   (lines 930–1000), read from the PR head.
9. Hugging Face dataset `ffanyt/Mibot-RSI-knowledge-latest`, gated `manual`,
   public, last modified 2026-11-11, revision
   `a182734b5f271d522c6ff9b8718bac7553a7dbb9`:
   <https://huggingface.co/datasets/ffanyt/Mibot-RSI-knowledge-latest> (metadata
   and file list only; archives not downloaded).

**Xiaomi XR-1**

10. `XiaomiRobotics/Xiaomi-Robotics-1`, Apache-2.0, 764 stars, HEAD
    `0dd7aef8dc87296246aae812a1f59ccb708e5546` (2026-09-09):
    <https://github.com/XiaomiRobotics/Xiaomi-Robotics-1>; `README.md`.
11. XR-1 paper, arXiv:2607.15330, v1 2026-07-16, v2 2026-07-22:
    <https://arxiv.org/abs/2607.15330> (abstract only).
12. HF checkpoint `XiaomiRobotics/Xiaomi-Robotics-1-5B`, Apache-2.0, created
    2026-07-28: <https://huggingface.co/XiaomiRobotics/Xiaomi-Robotics-1-5B>.
13. XPolicyLab `policy/Xiaomi_Robotics_1/README.md`, which calls the model
    "Xiaomi's MiBot model" and says the paper is not released (stale).

**Other**

14. `DAGroup-PKU/PyRUA-Lean`, Apache-2.0, HEAD
    `8543207e80e17176f2f0d010cb52303d446e951a` (2026-11-26):
    <https://github.com/DAGroup-PKU/PyRUA-Lean>; `README.md`.
15. PyRUA-Lean paper, arXiv:2610.01939: <https://arxiv.org/abs/2610.01939> (not
    read).
16. XPolicyLab repository, HEAD
    `24c49cb3e217080af6c66bd7704711d78562fbe0` (2026-11-26):
    <https://github.com/XPolicyLab/XPolicyLab>; `policy/` listing (83 directories).
17. XPolicyLab paper, arXiv:2608.09892, cited by the RoboDojo README (not read).
18. Xiaomi Robotics GitHub organization: <https://github.com/XiaomiRobotics> (three
    public repositories: Xiaomi-Robotics-0, Xiaomi-Robotics-1,
    Xiaomi-Robotics-U0).
19. GitHub profile `ffanyt` (public fields only), accessed 2026-11-27.

**Evidence grades.** S = reproduced on this system (none of the robot results);
A = direct primary source or code; B = credible indirect evidence; C = inference
requiring verification; D = unverified hypothesis. This report's S-class
reproduction is limited to arithmetic on published data (MVE-0) and static code
reading (MVE-1); no robot or simulator run was performed.
