#!/usr/bin/env python3
"""Generate Sobol/LHS source points for the four expensive EPOCH variables."""

from __future__ import annotations

import argparse
import csv
import math
import random
from pathlib import Path


BOUNDS = {
    "I0_Wcm2": (5.0e19, 3.0e20, "log"),
    "tau_FWHM_fs": (20.0, 60.0, "linear"),
    "d_CH_um": (0.2, 3.0, "log"),
    "L_pre_um": (0.0, 1.0, "linear")
}


def _scale(u: float, lo: float, hi: float, mode: str) -> float:
    if mode == "log":
        return 10 ** (math.log10(lo) + u * (math.log10(hi) - math.log10(lo)))
    return lo + u * (hi - lo)


def _lhs(n: int, dim: int, seed: int) -> list[list[float]]:
    rng = random.Random(seed)
    cols = []
    for _ in range(dim):
        values = [(i + rng.random()) / n for i in range(n)]
        rng.shuffle(values)
        cols.append(values)
    return [[cols[j][i] for j in range(dim)] for i in range(n)]


def _unit_points(n: int, dim: int, seed: int) -> list[list[float]]:
    try:
        from scipy.stats import qmc

        sampler = qmc.Sobol(d=dim, scramble=True, seed=seed)
        m = math.ceil(math.log2(n))
        return sampler.random_base2(m)[:n].tolist()
    except Exception:
        return _lhs(n, dim, seed)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--n-points", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260630)
    parser.add_argument("--out", type=Path, default=Path("data/objectives/initial_epoch_sources.csv"))
    args = parser.parse_args()

    names = list(BOUNDS)
    unit = _unit_points(args.n_points, len(names), args.seed)
    rows = []
    for idx, point in enumerate(unit, 1):
        row = {"sample_id": f"sobol_{idx:04d}"}
        for name, u in zip(names, point):
            lo, hi, mode = BOUNDS[name]
            row[name] = f"{_scale(u, lo, hi, mode):.10g}"
        rows.append(row)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["sample_id", *names])
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} EPOCH source points to {args.out}")


if __name__ == "__main__":
    main()

