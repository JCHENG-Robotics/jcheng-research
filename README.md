# jcheng-research

**Investigation workspace for the JCHENG Robotics ecosystem.** Literature review,
technology selection, root-cause analysis and pre-registered experiment design for
the ArmPi Ultra platform. This repository produces **reports and decisions, not
runtime code**: nothing here is imported by, shipped to, or executed on the robot.

> Status: **Experimental** — v0.1.0 as of 2026-11-25. The repository contains the
> investigation protocol, the report template and the output-directory contract;
> **no investigation is complete**, so it makes no technical claim. It is private
> and sits outside the runtime dependency graph.
> English canonical; see [README.zh-CN.md](README.zh-CN.md) for the Chinese
> translation.

---

## 1. Why this repository exists

Investigation work in this ecosystem has the same failure modes as code: a
conclusion is cited without its source, a mock result is remembered as a
hardware result, a paper's abstract is mistaken for its evaluation, or a
"verified" claim loses the command and date that produced it. The repository
fixes the process instead of trusting memory:

- **[AGENTS.md](AGENTS.md)** is the owner's binding research protocol — primary
  sources, paper and repository review, critical comparison, project fit,
  minimum viable experiment, evidence grades S–D, report outline.
- **[templates/research-report.md](templates/research-report.md)** is the fixed
  13-section report skeleton derived from that protocol.
- **`reports/`, `experiments/`, `references/`** make the three artefacts
  (conclusion, execution, source) separate and individually traceable.

The protocol applies **only inside this repository**. Routine code, build and
deploy work follows the ecosystem root `AGENTS.md` and each product
repository's own rules.

## 2. Scope and boundary

| Item | This repository |
|---|---|
| Layer | **Research** — outside L0–L4 and OPS; no runtime repository depends on it |
| Inputs | the ecosystem repositories, their evidence, published literature, the owner's questions |
| Outputs | `reports/*.md`, `experiments/*/`, `references/<theme>/*.md` |
| Executes on the robot | No |
| Hardware access | `none` — no device, DDS, serial, camera or bus access |
| Runtime dependency | None, in either direction; product repositories must not import from here |
| Forbidden | motion commands; DDS participation; copying vendor code or firmware; model weights, bags or raw video; secrets; private plan material (`MASTER_PLAN_V3_PRIVATE.md`) |
| Claim authority | None. A report can recommend a decision; it cannot accept a hardware claim for another repository |

## 3. Repository layout

```text
jcheng-research/
├── AGENTS.md                  # the investigation protocol (binding, this repo only)
├── README.md / README.zh-CN.md
├── ROADMAP.md                 # milestones and their exit criteria
├── CHANGELOG.md               # Keep a Changelog 1.1.0
├── ACCEPTANCE.md              # what is verified in this repository (L0 only so far)
├── LICENSE-REVIEW.md          # license status while the ecosystem review is open
├── VERSION
├── templates/
│   └── research-report.md     # 13-section report skeleton
├── reports/                   # one report per investigation (index: reports/README.md)
├── experiments/               # one directory per minimum viable experiment
├── references/                # source records by theme (index: references/README.md)
│   ├── system/                # jcheng-system: safety, arbitration, motion
│   ├── perception/            # jcheng-perception: vision, depth/TF, fusion
│   ├── mobile/                # jcheng-mobile: LiDAR, SLAM, Nav2
│   ├── ops/                   # jcheng-ops: probes, watchdog, self-healing
│   ├── manipulation/          # jcheng-manipulation: VLA, grasp, arm control
│   │   └── papers/            # local PDF copies
│   └── datasets-benchmarks/   # cross-cutting: datasets, benchmarks, rules
├── scripts/
│   └── check_repo_gate.sh     # local and CI gate
└── .github/workflows/ci.yml   # research-gate
```

## 4. Requirements

- `bash`, `git`, `grep`, `find` — the gate is the only executable artefact.
- Optional: `python3` for analysis notebooks or scripts inside an
  `experiments/<id>/` directory.
- No ROS, no GPU and no robot access are required to work in this repository.

## 5. Quick start

```bash
git clone git@github.com:JCHENG-Robotics/jcheng-research.git
cd jcheng-research
bash scripts/check_repo_gate.sh     # must print "Repository gate OK"
```

Starting an investigation:

```bash
cp templates/research-report.md reports/$(date +%Y%m%d)-<slug>.md
mkdir -p experiments/$(date +%Y%m%d)-<slug>/{data,logs}
```

## 6. Output contract

**Reports** — `reports/YYYYMMDD-<slug>.md`, one per investigation. The themed
view is [reports/README.md](reports/README.md); files stay flat and date-named.

1. Start from the template; keep the 13-section order.
2. Every key conclusion carries an evidence grade: **S** reproduced on this
   system, **A** direct primary source or code, **B** credible indirect,
   **C** inference, **D** unverified hypothesis.
3. Every external claim links its source; every source record is also listed in
   `references/` with URL/DOI, version or commit SHA, and access date.
4. A failed bound stays failed. Synthetic, mock and replay results are never
   presented as hardware validation; unrun experiments are never described as
   completed.
5. State the research boundary (tools, permissions, time, material) whenever it
   limited the conclusion.

**Experiments** — `experiments/YYYYMMDD-<slug>/` containing `design.md`
(hypothesis, baseline, variables, environment, metrics, acceptance and failure
criteria, logging, rollback), `data/`, `logs/`, and `result.md` when run.

**References** — `references/<theme>/<slug>.md`; one file per source group, with
DOI or URL, version, publication or commit date, and what was actually read
(full text, abstract only, code at a given SHA). Record when access was partial.
Themes mirror the product repositories — `system/`, `perception/`, `mobile/`,
`ops/`, `manipulation/` — plus the cross-cutting `datasets-benchmarks/`. File a
source under the theme of its primary consumer and cross-link it from the other
theme's README instead of duplicating it. Local PDF copies go to
`references/<theme>/papers/YYYYMMDD-<slug>.pdf`; check the license and keep the
5 MB gate in mind. Index and filing rules:
[references/README.md](references/README.md).

**What never enters git**: raw recordings, model weights, vendor source or
firmware, third-party confidential material, secrets, and the private plan.

## 7. Validation status

| Claim | Status | Evidence |
|---|---|---|
| Required document set, protocol, template and output directories exist | Verified (L0, 2026-11-25) | `scripts/check_repo_gate.sh`, CI `research-gate` |
| No secrets, model weights, recorded data or files > 5 MB are tracked | Verified (L0, 2026-11-25) | same gate |
| LingBot-VLA 2.0 / SST evaluation | Draft produced, not reviewed (2026-11-25) | [report](reports/20261125-lingbot-vla-sst-foreground-prompting.md) |
| GloVLA factorization assessment | Draft produced, self-reviewed (2026-11-25); independent review pending | [report](reports/20261125-glovla-hybrid-factorization-eval.md) |

There is no hardware path in this repository, so no L1–L5 result can originate
here. Details and limitations: [ACCEPTANCE.md](ACCEPTANCE.md).

## 8. Related repositories

| Repository | Relationship |
|---|---|
| [`jcheng-interfaces`](https://github.com/JCHENG-Robotics/jcheng-interfaces) | Contract authority; reports may cite its hash |
| [`jcheng-system`](https://github.com/JCHENG-Robotics/jcheng-system) | Privileged runtime; the only motion entry |
| [`jcheng-perception`](https://github.com/JCHENG-Robotics/jcheng-perception) | L3 perception |
| [`jcheng-mobile`](https://github.com/JCHENG-Robotics/jcheng-mobile) | L3 mobile base |
| [`jcheng-ops`](https://github.com/JCHENG-Robotics/jcheng-ops) | Operations and recovery |
| [`jcheng-manipulation`](https://github.com/JerichoCheng/jcheng-manipulation) | Frozen v1.0.0 baseline and design record |
| [`JCHENG-Robotics/.github`](https://github.com/JCHENG-Robotics/.github) | Governance, documentation standard, taxonomy |

While this repository is private it is deliberately **not** listed in the public
repository taxonomy or organization profile.

## 9. License

The license review is pending. This repository has no `LICENSE` and all rights
are reserved; see [LICENSE-REVIEW.md](LICENSE-REVIEW.md).
