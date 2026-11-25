#!/usr/bin/env python3
"""GloVLA handoff geometry: desk recomputation of Eq. (12).

This is a desk calculation. It uses the spatial parameters reported in
GloVLA Fig. 2 and measured error magnitudes from jcheng-perception evidence.
It does not run a policy, a simulator, or a robot.

Run: python3 -I analysis.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

# GloVLA Fig. 2 (paper, p. 3): extraction radii and fixed offsets (metres).
PHASES = {
    "grasp": {
        "r": 0.12,
        "delta": (0.04, 0.0, 0.08),
        "source": "GloVLA Fig. 2: r_o=0.12, rho_o=(0.04,0.0), z_g=0.08",
    },
    "place": {
        "r": 0.18,
        "delta": (0.005, 0.005, 0.12),
        "source": "GloVLA Fig. 2: r_b=0.18, rho_b=(0.005,0.005), z_p=0.12",
    },
}

# Localization-error magnitudes, in metres. These are NOT calibrated object-centre
# errors; they are the measured cross-view / fused-track differences recorded in
# jcheng-perception. They are used as a conservative proxy for eta.
ETA_CASES = [
    ("static cross-view 1.55 mm (2026-11-24 split-edge)", 0.00155),
    ("run 9 cross-view 3.37 mm (2026-11-24 tag verify)", 0.00337),
    ("run 9 fused max 10.03 mm (transient)", 0.01003),
    ("translation error-budget RSS 13.33 mm (not eta)", 0.01333),
    ("hypothetical 30 mm object-centre error", 0.03000),
]

# The paper does not report epsilon; enumerate plausible controller tolerances.
EPS_CASES = [0.005, 0.010, 0.020]


def norm(v: tuple[float, float, float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def main() -> None:
    out_dir = Path(__file__).resolve().parent
    data_dir = out_dir / "data"
    data_dir.mkdir(exist_ok=True)

    rows = []
    for name, phase in PHASES.items():
        d = norm(phase["delta"])
        slack = phase["r"] - d
        rows.append(
            {
                "phase": name,
                "r_m": phase["r"],
                "delta_m": phase["delta"],
                "delta_norm_m": d,
                "slack_eps_plus_eta_m": slack,
                "source": phase["source"],
            }
        )

    print("GloVLA Eq. (12) containment: epsilon + eta <= r - ||delta||")
    print("Desk calculation; no policy, simulator or robot was run.\n")
    print(f"{'phase':6} {'r (m)':>7} {'||delta|| (m)':>14} {'slack (mm)':>11}")
    for row in rows:
        print(
            f"{row['phase']:6} {row['r_m']:7.3f} "
            f"{row['delta_norm_m']:14.4f} "
            f"{row['slack_eps_plus_eta_m'] * 1000:11.2f}"
        )

    print("\nPass/fail matrix (P = epsilon + eta <= slack):")
    header = "eta \\ epsilon"
    print(f"{header:>46} " + " ".join(f"{e * 1000:5.0f}mm" for e in EPS_CASES))
    matrix = []
    for eta_name, eta in ETA_CASES:
        cells = []
        for eps in EPS_CASES:
            grasp_ok = eps + eta <= rows[0]["slack_eps_plus_eta_m"]
            place_ok = eps + eta <= rows[1]["slack_eps_plus_eta_m"]
            cells.append("P" if grasp_ok else "F")
            matrix.append(
                {
                    "phase": "grasp",
                    "eta_case": eta_name,
                    "eta_m": eta,
                    "epsilon_m": eps,
                    "margin_m": rows[0]["slack_eps_plus_eta_m"] - eps - eta,
                    "pass": grasp_ok,
                }
            )
            matrix.append(
                {
                    "phase": "place",
                    "eta_case": eta_name,
                    "eta_m": eta,
                    "epsilon_m": eps,
                    "margin_m": rows[1]["slack_eps_plus_eta_m"] - eps - eta,
                    "pass": place_ok,
                }
            )
        print(f"{eta_name:>44}  " + "   ".join(cells) + "   [grasp]")

    print("\nMaximum epsilon allowed for each eta (grasp phase):")
    for eta_name, eta in ETA_CASES:
        allowed = rows[0]["slack_eps_plus_eta_m"] - eta
        verdict = "no epsilon can satisfy" if allowed < 0 else f"{allowed * 1000:.1f} mm"
        print(f"  {eta_name:>44}: {verdict}")

    payload = {
        "source": "GloVLA arXiv:2609.06256v1, Fig. 2 and Eq. (12)",
        "note": "Desk calculation only; eta is a cross-view proxy, not a calibrated object-centre error.",
        "phases": rows,
        "matrix": matrix,
        "eps_cases_m": EPS_CASES,
    }
    (data_dir / "handoff_budget.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"\nWrote {data_dir / 'handoff_budget.json'}")


if __name__ == "__main__":
    main()
