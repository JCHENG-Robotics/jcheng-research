# License review — jcheng-research

> Status: **pending** as of 2026-11-25.
> This repository has no `LICENSE` and all rights are reserved, following the
> organization rule that no `LICENSE` is added before the review is signed off
> (`.github/docs/license-review.md`).

## 1. Current facts

| Item | Fact |
|---|---|
| `LICENSE` | Absent |
| Content type | Markdown protocol, templates and reports; no runtime code, no vendored code |
| Tracked third-party code | None |
| Dependencies | None |
| Access | Public repository; no `LICENSE` yet, all rights reserved |

## 2. Why the review still matters

This repository **quotes and summarizes third-party work** — papers, vendor
documentation, upstream repositories. Copyright in quoted figures, tables and
long excerpts is separate from the repository license, and publishing the
repository does not remove that obligation.

Before the review closes, decide:

1. Whether reports may reproduce figures/tables from papers and vendor documents,
   and under what quotation limit; otherwise link and describe.
2. Whether cited code snippets are reproduced or only referenced by path and SHA.
3. Whether this repository is published at all; if it is, whether it joins the
   ecosystem license decision or remains all-rights-reserved.
4. The copyright holder string, consistent with the ecosystem decision.

## 3. Rules until then

- Do not add a `LICENSE` file; `scripts/check_repo_gate.sh` fails if one appears.
- Keep third-party excerpts short, attributed and linked; put source records in
  `references/`.
- Do not commit vendor source, firmware, model weights or third-party
  confidential material.

## 4. Open questions

- Does the private-to-public transition of this repository need its own
  acceptance entry, separate from the ecosystem v1.0 review?
- Are report authors other than the owner planned? If so, a contribution policy
  is needed before the first external contribution.
