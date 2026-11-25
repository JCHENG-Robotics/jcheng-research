#!/usr/bin/env bash
# Repository gate for jcheng-research.
# Checks the document set, the output-directory contract, relative links,
# and that no LICENSE, secret, model weight, recorded data or oversized file
# is tracked. Run locally and in CI (job: research-gate).

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

fail=0
require_file() {
  if [[ ! -f "$1" ]]; then
    echo "MISSING: $1" >&2
    fail=1
  fi
}

for f in \
  README.md \
  README.zh-CN.md \
  ROADMAP.md \
  CHANGELOG.md \
  ACCEPTANCE.md \
  LICENSE-REVIEW.md \
  AGENTS.md \
  VERSION \
  .gitignore \
  templates/research-report.md \
  scripts/check_repo_gate.sh \
  references/README.md \
  reports/README.md \
  .github/workflows/ci.yml
do
  require_file "$f"
done

for d in reports experiments references \
  references/system references/perception references/mobile \
  references/ops references/manipulation references/datasets-benchmarks; do
  if [[ ! -d "$d" ]]; then
    echo "MISSING DIR: $d" >&2
    fail=1
  fi
done

# The ecosystem license review is open: a LICENSE file must not appear.
if [[ -e LICENSE ]]; then
  echo "ERROR: LICENSE must not exist before the license review is approved." >&2
  fail=1
fi

# No credentials. The script itself is excluded because it contains the pattern.
if grep -RIlE \
  --exclude-dir=.git \
  --exclude='check_repo_gate.sh' \
  'ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN [A-Z ]*PRIVATE KEY-----' \
  . >/dev/null 2>&1; then
  echo "ERROR: possible secret material found." >&2
  fail=1
fi

# No model weights or recorded data.
if find . -path ./.git -prune -o \
    \( -name '*.pt' -o -name '*.onnx' -o -name '*.engine' \
       -o -name '*_openvino_model' -o -name '*.bag' -o -name '*.db3' \
       -o -name '*.mcap' -o -name '*.mp4' -o -name '*.avi' \) -print \
    | grep -q .; then
  echo "ERROR: model weights or recorded data found; keep them outside the repository." >&2
  fail=1
fi

# No oversized files (catches accidental blobs before they enter history).
big="$(find . -path ./.git -prune -o -type f -size +5M -print)"
if [[ -n "${big}" ]]; then
  echo "ERROR: files larger than 5 MB:" >&2
  echo "${big}" >&2
  fail=1
fi

# Relative Markdown links must resolve from the file that contains them.
while IFS= read -r f; do
  dir="$(dirname "${f}")"
  while IFS= read -r link; do
    case "${link}" in
      http://*|https://*|mailto:*|'#'*|'') continue ;;
    esac
    target="${link%%#*}"
    [[ -z "${target}" ]] && continue
    if [[ ! -e "${dir}/${target}" ]]; then
      echo "BROKEN LINK in ${f}: ${link}" >&2
      fail=1
    fi
  done < <(grep -oE '\]\([^)]+\)' "${f}" | sed -e 's/^](//' -e 's/)$//')
done < <(find . -path ./.git -prune -o -name '*.md' -print)

if [[ "${fail}" -ne 0 ]]; then
  echo "Repository gate FAILED" >&2
  exit 1
fi

echo "Repository gate OK: document set, output directories, links, no LICENSE, no secrets, no weights, no oversized files"
