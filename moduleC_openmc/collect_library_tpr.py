"""Collect OpenMC A/B results into a nuclear-data library uncertainty table."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np


def _float_or_nan(value: str) -> float:
    return np.nan if value == "" or value == "nan" else float(value)


def _parse_result_arg(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("--result must be NAME=/path/to/case_comparison_summary.csv")
    name, path = value.split("=", 1)
    csv_path = Path(path).expanduser().resolve()
    if not csv_path.exists():
        raise argparse.ArgumentTypeError(f"result CSV not found: {csv_path}")
    return name, csv_path


def _read_rows(name: str, csv_path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(
                {
                    "library": name,
                    "tally": row["tally"],
                    "case_A_mean": float(row["case_A_mean"]),
                    "case_A_std": float(row["case_A_std"]),
                    "case_A_rel_err": _float_or_nan(row["case_A_rel_err"]),
                    "case_B_mean": float(row["case_B_mean"]),
                    "case_B_std": float(row["case_B_std"]),
                    "case_B_rel_err": _float_or_nan(row["case_B_rel_err"]),
                }
            )
    return rows


def _write_table(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "library",
        "tally",
        "case_A_mean",
        "case_A_std",
        "case_A_rel_err",
        "case_B_mean",
        "case_B_std",
        "case_B_rel_err",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_band(path: Path, rows: list[dict[str, object]], tally: str) -> None:
    vals = np.array([float(row["case_B_mean"]) for row in rows if row["tally"] == tally], dtype=float)
    libs = [str(row["library"]) for row in rows if row["tally"] == tally]
    if vals.size == 0:
        raise ValueError(f"tally not found: {tally}")
    mean = float(np.mean(vals))
    vmin = float(np.min(vals))
    vmax = float(np.max(vals))
    rel_half_range = 0.5 * (vmax - vmin) / mean if mean else np.nan
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["tally", "n_libraries", "mean", "min", "max", "relative_half_range", "libraries"])
        writer.writerow([tally, vals.size, mean, vmin, vmax, rel_half_range, ";".join(libs)])


def _plot(path: Path, rows: list[dict[str, object]], tally: str) -> None:
    import matplotlib.pyplot as plt

    selected = [row for row in rows if row["tally"] == tally]
    labels = [str(row["library"]) for row in selected]
    means = np.array([float(row["case_B_mean"]) for row in selected], dtype=float)
    std = np.array([float(row["case_B_std"]) for row in selected], dtype=float)
    order = np.argsort(labels)
    labels = [labels[i] for i in order]
    means = means[order]
    std = std[order]

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    x = np.arange(len(labels))
    ax.errorbar(x, means, yerr=std, fmt="o", capsize=3, color="tab:blue")
    ax.fill_between([-0.4, len(labels) - 0.6], np.min(means), np.max(means), color="tab:blue", alpha=0.12)
    ax.set_xticks(x, labels, rotation=20, ha="right")
    ax.set_ylabel("Case B Li7 TPR per source neutron")
    ax.set_title("Li7 tritium-production nuclear-data library spread")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=240)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", action="append", type=_parse_result_arg, required=True)
    parser.add_argument("--output-dir", default="hpc/results")
    parser.add_argument("--prefix", default="li7_tpr_library_uncertainty")
    args = parser.parse_args()

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for name, path in args.result:
        rows.extend(_read_rows(name, path))
    _write_table(outdir / f"{args.prefix}.csv", rows)
    _write_band(outdir / f"{args.prefix}_band.csv", rows, "TPR_Li7")
    _plot(outdir / f"{args.prefix}.png", rows, "TPR_Li7")
    print(f"wrote {outdir / f'{args.prefix}.csv'}")
    print(f"wrote {outdir / f'{args.prefix}_band.csv'}")
    print(f"wrote {outdir / f'{args.prefix}.png'}")


if __name__ == "__main__":
    main()
