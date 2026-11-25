#!/usr/bin/env python3
"""Reproduce the desk re-analysis of the SST published success counts.

Input: derived counts in data/ (success/total per run, plus per-task counts for
N0 and N5). Source: the SST report's data/results.csv and data/evidence.json at
commit 8797aa31dd9798a6e931d57857f32cd5de372b6c, read 2026-11-25.

Scope: this is a statistical re-analysis of published counts. It is not a robot
experiment, not a re-evaluation of the checkpoints (they are not released), and
it cannot recover seed-level pairing. The two-proportion z-test below ignores
task clustering, so its p-values are optimistic.
"""

from __future__ import annotations

import csv
import math
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"


def read_counts(path: Path) -> dict[tuple[str, str], tuple[int, int]]:
    out: dict[tuple[str, str], tuple[int, int]] = {}
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            out[(row["stage"], row["scene"])] = (int(row["success"]), int(row["total"]))
    return out


def wilson(success: int, total: int, z: float = 1.96) -> tuple[float, float]:
    p = success / total
    denom = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return 100 * (centre - half), 100 * (centre + half)


def two_proportion(a: tuple[int, int], b: tuple[int, int]) -> tuple[float, float]:
    sa, na = a
    sb, nb = b
    pa, pb = sa / na, sb / nb
    se = math.sqrt(pa * (1 - pa) / na + pb * (1 - pb) / nb)
    diff = 100 * (pb - pa)
    z = diff / (100 * se)
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return diff, p


def main() -> None:
    counts = read_counts(DATA / "main_chain_counts.csv")
    print("Table 1. Main chain, published counts")
    print(f"{'stage':8s} {'scene':16s} {'success':>8s} {'total':>6s} "
          f"{'rate%':>7s} {'Wilson95':>16s}")
    for (stage, scene), (s, n) in counts.items():
        lo, hi = wilson(s, n)
        print(f"{stage:8s} {scene:16s} {s:8d} {n:6d} {100*s/n:7.2f} "
              f"[{lo:5.2f},{hi:5.2f}]")

    print("\nTable 2. Unpaired two-proportion z-tests (optimistic: ignores task clustering)")
    comparisons = [
        ("N0", "N1", "foreground replacement (single->multi)"),
        ("N1", "N2", "mask review + 0.1 rendering"),
        ("N2", "N3", "raw teachers + foreground weighting"),
        ("N3", "N4", "module-wise learning rates"),
        ("N4_30k", "N5", "data repair at equal 30k steps"),
    ]
    for scene in ("demo_randomized", "demo_clean"):
        print(f"  scene: {scene}")
        for a, b, label in comparisons:
            diff, p = two_proportion(counts[(a, scene)], counts[(b, scene)])
            print(f"    {a:6s}->{b:3s} {label:38s} d={diff:+6.2f}pp  p={p:.4f}")

    # Per-task descriptive analysis (N0 15k vs N5 30k, 100 episodes/task).
    rows = list(csv.DictReader((DATA / "per_task_n0_n5.csv").open(newline="")))
    for scene in ("clean", "randomized"):
        deltas = []
        for r in rows:
            if r["scene"] != scene:
                continue
            sa, na = int(r["n0_success"]), int(r["n0_total"])
            sb, nb = int(r["n5_success"]), int(r["n5_total"])
            deltas.append((100 * (sb / nb - sa / na), r["task"], sa, sb))
        deltas.sort(reverse=True)
        print(f"\nTable 3. Per-task delta, {scene} (N0 15k -> N5 30k, n=100/task)")
        print(f"  tasks={len(deltas)} mean={statistics.mean(d for d, *_ in deltas):+.2f}pp "
              f"median={statistics.median(d for d, *_ in deltas):+.2f}pp "
              f"improved={sum(d > 0 for d, *_ in deltas)} "
              f"worse={sum(d < 0 for d, *_ in deltas)} "
              f"same={sum(d == 0 for d, *_ in deltas)}")
        print("  top +5:", [(t, round(d, 1), f"{a}->{b}") for d, t, a, b in deltas[:5]])
        print("  top -5:", [(t, round(d, 1), f"{a}->{b}") for d, t, a, b in deltas[-5:]])
        click = sum(d for d, t, *_ in deltas if t in ("click_bell", "click_alarmclock"))
        total_extra = sum(b - a for _, _, a, b in deltas)
        print(f"  click tasks contribute {click:+.1f}pp of the {total_extra/len(deltas):+.2f}pp mean "
              f"({100*click/total_extra:.0f}% of all extra successes)")


if __name__ == "__main__":
    main()
