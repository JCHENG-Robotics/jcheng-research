# <Investigation title>

> Report status: **draft** (draft | reviewed | superseded). Date: YYYY-MM-DD.
> Author: <name>. Reviewer: pending.
> Decision this informs: <one sentence; the decision, not the topic>.
> Research boundary: <tools, permissions, time or material limits, or "none">.

## 01. Executive Summary

The conclusion first: recommended option, the two or three facts that carry it,
and the main risk. Graded claims only (see the legend at the end).

## 02. Research Questions

The question as asked; the sub-questions that make it answerable; constraints
(hardware, contracts, safety boundary, budget, time); the deliverable.

## 03. Current System Analysis

What the ecosystem actually does today, with paths and commit SHAs — not what the
README says. Relevant repositories, contracts, evidence files and measured values.

## 04. Research Methodology

Search terms and synonyms, sources consulted and their versions, inclusion and
exclusion criteria, what was read in full and what only in abstract, and the
reason the remaining scope was cut.

## 05. Literature Review

Per paper: problem, contribution, mechanism, assumptions, baselines, ablations,
sample size, statistical reliability, limitations, reproducibility, and the cost
of transferring the result to this platform. No abstract-only judgements.

## 06. Repository Investigation

Per candidate repository: entry points, call chains, dependencies and versions,
configuration, tests and CI, error handling, concurrency, issues/PRs, commit
history, license, and real-deployment evidence. File path + symbol + line + SHA
for every code claim. Mark static analysis versus executed result versus inference.

## 07. Comparative Analysis

Candidates against the same question. Which results are directly comparable and
which are not; contradictory findings; maturity; hidden engineering cost; simpler
alternatives. No unsupported ranking.

## 08. Critical Findings

Counter-examples, failure cases, negative results, technical limits, and the gaps
where evidence is missing. What would change the conclusion.

## 09. Engineering Applicability

Fit with the current architecture, migration effort, hardware and compute cost,
maintenance cost, expected gain, safety and reliability risk, effect on existing
behaviour, extensibility, and the rollback path.

## 10. Recommended Approach

Recommended option, alternatives, and rejected options — each with its reason.
State what is *not* recommended and why, not only what is.

## 11. Experimental Design

Minimum viable experiment: hypothesis, baseline, independent and controlled
variables, environment, quantitative metrics, acceptance criteria, failure
criteria, recording method, and rollback. Mark clearly whether it has been run;
an unrun experiment is never described as completed.

## 12. Limitations & Uncertainties

Open questions, thin evidence, where the conclusion would break, and what access
or data would be needed to close each gap.

## 13. References

Papers (DOI/link), repositories (URL + commit SHA), vendor documents (version +
date), datasets (version + access date). Mirror each source in `references/`.

---

Evidence grades: **S** reproduced on this system · **A** direct primary source or
code · **B** credible indirect evidence · **C** inference from existing evidence ·
**D** unverified hypothesis.
