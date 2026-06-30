#!/usr/bin/env python3
"""Compute weighted neutron timing metrics from histogram or event CSV files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def _read_csv(path: Path) -> tuple[list[float], list[float]]:
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"{path} has no CSV header")

        time_col = None
        for name in ("time_ps", "t_ps", "exit_time_ps", "detector_time_ps"):
            if name in reader.fieldnames:
                time_col = name
                break
        if time_col is None:
            raise ValueError(
                f"{path} must contain one of: time_ps, t_ps, exit_time_ps, detector_time_ps"
            )

        weight_col = None
        for name in ("weight", "count", "counts", "neutron_weight"):
            if name in reader.fieldnames:
                weight_col = name
                break

        times: list[float] = []
        weights: list[float] = []
        for row in reader:
            t = float(row[time_col])
            w = float(row[weight_col]) if weight_col else 1.0
            if w > 0:
                times.append(t)
                weights.append(w)
    return times, weights


def weighted_fwhm(times: list[float], weights: list[float]) -> float | None:
    """Return FWHM in the same time units as input.

    This expects histogram-like rows or event rows already binned by the caller.
    For sparse event rows, pass a histogram CSV instead of raw events.
    """

    if not times:
        return None

    pairs = sorted(zip(times, weights), key=lambda item: item[0])
    max_w = max(w for _, w in pairs)
    if max_w <= 0:
        return None

    half = 0.5 * max_w
    above = [(t, w) for t, w in pairs if w >= half]
    if not above:
        return None

    return above[-1][0] - above[0][0]


def weighted_mean(times: list[float], weights: list[float]) -> float | None:
    total = sum(weights)
    if total <= 0:
        return None
    return sum(t * w for t, w in zip(times, weights)) / total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    times, weights = _read_csv(args.csv_file)
    result = {
        "input": str(args.csv_file),
        "total_weight": sum(weights),
        "time_weighted_mean_ps": weighted_mean(times, weights),
        "time_FWHM_ps": weighted_fwhm(times, weights),
        "n_rows": len(times)
    }

    text = json.dumps(result, indent=2, sort_keys=True)
    if args.out:
        args.out.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()

