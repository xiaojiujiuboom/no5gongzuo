#!/usr/bin/env python3
"""Mark Pareto-optimal rows for neutron yield/FWHM objective tables."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def _float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    if value == "":
        return float("nan")
    return float(value)


def _dominates(
    a: dict[str, str],
    b: dict[str, str],
    yield_key: str,
    fwhm_key: str,
) -> bool:
    ay = _float(a, yield_key)
    by = _float(b, yield_key)
    at = _float(a, fwhm_key)
    bt = _float(b, fwhm_key)
    if any(math.isnan(v) for v in (ay, by, at, bt)):
        return False
    return (ay >= by and at <= bt) and (ay > by or at < bt)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("objectives_csv", type=Path)
    parser.add_argument("--out", type=Path, default=Path("data/objectives/pareto.csv"))
    parser.add_argument("--yield-key", default="log10_Y_n_forward_detector_per_J")
    parser.add_argument("--yield-source-key", default="Y_n_forward_detector_per_J")
    parser.add_argument("--fwhm-key", default="tau_forward_detector_FWHM_ps")
    args = parser.parse_args()

    with args.objectives_csv.open(newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    if args.yield_key not in fieldnames:
        fieldnames.append(args.yield_key)
        for row in rows:
            y = _float(row, args.yield_source_key)
            row[args.yield_key] = str(math.log10(y)) if y > 0 else ""

    if "is_pareto" not in fieldnames:
        fieldnames.append("is_pareto")

    for i, row in enumerate(rows):
        dominated = any(
            _dominates(other, row, args.yield_key, args.fwhm_key)
            for j, other in enumerate(rows)
            if i != j
        )
        row["is_pareto"] = "true" if not dominated else "false"

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    n_pareto = sum(row["is_pareto"] == "true" for row in rows)
    print(f"wrote {args.out} with {n_pareto} Pareto rows out of {len(rows)}")


if __name__ == "__main__":
    main()
