# Contact Harness — paper, project page and code release

Source record for the Contact Harness investigation report
[`reports/20261128-contact-harness.md`](../../reports/20261128-contact-harness.md).
Facts, read scope and access date only; the report carries the judgement and the
evidence grades.

## Identity

| Item | Value |
|---|---|
| Paper | *Contact Harness: Enabling VLM Agents to Perform Contact-Rich Manipulation* |
| Authors | Shilin Shan, Yuxuan Hu, Chuhao Zhou, Yimeng Dong, Bohan Hou, Jiaqi Bai, Boyu Ma, Jiahua Dong, Jianfei Yang (MARS Lab, Nanyang Technological University) |
| arXiv | `arXiv:2611.29377` v1, submitted 2026-11-22; 45 pages, 21 figures; cs.RO / cs.CV |
| Venue / DOI | None at access; preprint, no peer review |
| Paper PDF | <https://ntumars.github.io/ContactHarness/paper.pdf> (35,313,207 bytes) |
| Project page | <https://ntumars.github.io/ContactHarness/> |
| Project-page repo | `NTUMARS/ContactHarness`, commit `a4d8b382d8f497cd5f5fd5d4d2caf656391239d7` (2026-11-26), Apache-2.0 |
| Code repo | `NTUMARS/Contact-Harness`, commit `5827438a166667f5eb24761e2d37827b59cc64f7` (2026-11-22), MIT |
| Dataset | Contact-4 demonstrations, <https://huggingface.co/datasets/ntumars/Contact-4>; README claims 8.6 GB, 50 demos/task, LeRobot v2.1, CC BY 4.0 |
| Lab | <https://marslab.tech> |
| Access date | 2026-11-28 |

## What was read

### Paper

- Full 45-page PDF: main text, Algorithm 1, Tables 1–5.
- Appendices read: A (related-work comparison, Table S1), B.2 (compliant
  execution and force clipping), D.1 (real-robot failure analysis), E.3 (VLM
  baseline adaptations), E.5 (Contact Harness simulation results), G (token
  usage), H (limitations).
- Appendices read selectively: C (prompt summaries), E.1/E.2 (simulated task
  construction and success criteria), E.4 (VLA baseline training details).
- Not read: the full text of the cited baseline papers (CaP-X, GenCHiP,
  Show-Harness, π0.5, ForceVLA, CompliantVLA, and the other related work). They
  are recorded here only as the Contact Harness paper describes and adapts them.

### Code repository (`5827438`)

Read statically; nothing was executed.

| Area | Files |
|---|---|
| Real Franka harness | `harness/franka/README.md`, `motion_server.py`, `observation_server.py`, `franka_robot_server.py`, `terminal_command.py`, `get_observation.py`, `start_robot_server.sh`, `config/observation.yaml` |
| Franka tests | `tests/test_frame_conventions.py`, `test_motion_server.py`, `test_observation.py`, `test_robot_server_action_queue.py`, `test_robot_server_configuration.py`, `test_soft_force_truncation.py` |
| Simulation benchmark | `contact4/README.md`, `setup.sh`, `run_codex_episode.sh`, `episode_ctl.py`, `sim_task_server.py`, `sim_robot_server.py`, `peg_tasks.py`, `write_tasks.py`, `pivot_tasks.py`, `place_tasks.py`, `render_video.py` |
| Simulated harness copy | `contact4/stack/motion_server.py`, `contact4/stack/observation_server.py`, `contact4/stack/terminal_command.py`, `contact4/stack/get_observation.py`, `contact4/stack/robot_support/` |
| Agent isolation | `contact4/agent_guard.py`, `contact4/codex_guard.py`, `contact4/agent_cc.sh`, `contact4/run_codex_episode.sh` |
| Prompts and skills | `contact4/prompts/agent_prompt.txt`, `contact4/prompts/task_prompt_peg_insertion.txt`, `contact4/prompts/task_prompt_wipe_table.txt`, `contact4/prompts/task_prompt_write_board.txt`, `contact4/prompts/task_prompt_pivot_box.txt`, `contact4/prompts/task_prompt_place_bowl.txt`, `contact4/prompts/task_prompt_stack_cubes.txt`; `harness/franka/docs/agent_prompt.txt`, `task_prompt_cable_insertion.txt`, `task_prompt_peeling.txt`, `task_prompt_pivot.txt`; `harness/rokae/docs/agent_prompt.txt`, `task_prompt_wipe_board.txt`, `task_prompt_write_alphabet.txt` |
| Dependencies and licence | `requirements-harness.txt`, `requirements-sim.txt`, `harness/franka/requirements.txt`, `LICENSE`, `third_party/franka_controllers/` |

### Repository facts at access

- `NTUMARS/Contact-Harness`: 106 files, 13,395 Python lines, 1 commit, 0 tags,
  no `.github/` or CI, 14 stars, 0 forks, 0 issues, default branch `main`,
  MIT. `harness/rokae/` contains a README and three prompt files only; the
  README says "Only the prompts are included."
- `NTUMARS/ContactHarness`: project page only; `docs/` static site, 1 commit,
  7 stars, Apache-2.0; `docs/paper.pdf` is the 45-page paper.
- No model weights, no local-model path and no Rokae robot/motion/observation
  server are included. The released real-robot path is Franka (force only, no
  tactile); simulation is MuJoCo/robosuite with synthesized tactile feedback.

## What the paper reports (not independently verified)

These are the authors' numbers, recorded for traceability. The report grades
them B (self-reported, no independent replication) and explains the caveats.

- 15 connector types on Rokae, 10 trials each: 136/150 = 90.7% full insertion;
  378 s mean, 23.1 decisions, 20.0 N median peak force.
- Seven additional real-robot tasks: 70/70 (wipe 308 s, write 413 s, Franka
  USB-A 203 s, peel 227 s, pivot 266 s, stack 284 s, pick-and-place 357 s).
- Real PC, three connectors, lighting/background/position changed together:
  29/30 (IEC C13 10/10, earphone 9/10, USB-A 10/10).
- Speed tests: C13 315 s; C13 fast 183 s; C13 fast+memory 96 s; Franka USB-A
  fast+memory 147 s; 30/30.
- Simulation, six tasks, 10 runs each: Contact Harness 96.7% (Astra), 98.3%
  (Fable 5.1/5.2); best trained baseline ForceVLA 68.3%; π0.5 46.7%; CaP-X
  23.3%; GenCHiP 33.3%; Show-Harness 16.7%.
- Ablation, four contact tasks: full 95.0%; w/o force observations 82.5%;
  w/o textual skills 42.5%; w/o compliance and soft limit 62.5% (Insert 0/10).
- Token usage: ~1.62M per real USB-A insertion (95% cached); ~1.49M per
  simulated run (96% cached); reasoning 84.7% of execution time.
- Simulation used Ubuntu 22.04 and an RTX 5090; the real Franka control PC
  requires ROS 1 Noetic, `franka_ros` 0.10.2 and a real-time kernel.

## Read scope and gaps

- **Read in full:** the paper PDF and the files listed above.
- **Partially read:** appendices C, E.1/E.2 and E.4; the cited baseline papers
  were not read.
- **Not executed:** any test, simulation episode or robot run. Code conclusions
  are static reading at `5827438`.
- **Not verified:** Hugging Face dataset metadata (API timeout); GPT-6 Astra /
  Claude Fable access, pricing and version behaviour; the Rokae control stack
  (not released); the 15-connector prompt as a file (the paper puts a condensed
  version in Fig. S2).
- **Access limitation:** the arXiv PDF endpoint was slow from this host
  (~6 KB/s); the paper was read from the project page's `docs/paper.pdf`, the
  same 45-page document by title/date, not byte-compared with the arXiv upload.

## Licence notes

- Code: MIT (`LICENSE`).
- Project page: Apache-2.0.
- `third_party/franka_controllers/`: MIT, adapted from an open-source Franka
  controller package.
- `franka_ros` launch/config: Apache-2.0.
- Isaac Lab Factory peg/hole meshes: BSD-3-Clause.
- LIBERO bowl/plate assets: MIT.
- Demonstrations: CC BY 4.0 per README.

No third-party code, model weights, videos or dataset files were copied into
this repository. The paper PDF is not stored locally; it is linked by URL.
