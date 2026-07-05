#!/usr/bin/env python3
"""Compare cumulative rear+10 normalized spectra at 4 ps and 5 ps."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def norm(hist: np.ndarray) -> np.ndarray:
    total = float(np.sum(hist))
    return hist / total if total > 0.0 else np.zeros_like(hist, dtype=float)


def shape_metrics(p_hist: np.ndarray, q_hist: np.ndarray) -> dict[str, float]:
    p = norm(p_hist)
    q = norm(q_hist)
    m = 0.5 * (p + q)
    eps = 1.0e-300
    kl_pm = np.sum(np.where(p > 0, p * np.log2((p + eps) / (m + eps)), 0.0))
    kl_qm = np.sum(np.where(q > 0, q * np.log2((q + eps) / (m + eps)), 0.0))
    js = 0.5 * (kl_pm + kl_qm)
    return {
        "l1": float(np.sum(np.abs(p - q))),
        "total_variation": float(0.5 * np.sum(np.abs(p - q))),
        "js_distance": float(np.sqrt(max(js, 0.0))),
        "cosine_similarity": float(np.dot(p, q) / max(np.linalg.norm(p) * np.linalg.norm(q), eps)),
    }


def qtile(hist: np.ndarray, centers: np.ndarray, q: float) -> float:
    total = float(np.sum(hist))
    if total <= 0.0:
        return float("nan")
    cdf = np.cumsum(hist) / total
    return float(np.interp(q, cdf, centers))


def stats(name: str, metric: str, hist: np.ndarray, centers: np.ndarray) -> dict[str, float | str]:
    total = float(np.sum(hist))
    row: dict[str, float | str] = {
        "source": name,
        "metric": metric,
        "total_weight": total,
        "E_mean_binned_MeV": float(np.sum(hist * centers) / total) if total > 0 else float("nan"),
        "E_p50_MeV": qtile(hist, centers, 0.50),
        "E_p90_MeV": qtile(hist, centers, 0.90),
        "E_p95_MeV": qtile(hist, centers, 0.95),
        "E_p99_MeV": qtile(hist, centers, 0.99),
    }
    for thr in (0.5, 0.6, 0.8, 1.0, 1.2):
        mask = centers > thr
        row[f"frac_E_gt_{thr:g}_MeV"] = float(np.sum(hist[mask]) / total) if total > 0 else float("nan")
    return row


def compare(
    gate: str,
    previous_spectrum: Path,
    previous_summary: Path,
    increment_hist: Path,
    out_prefix: Path,
) -> tuple[Path, Path, Path]:
    prev_spec = pd.read_csv(previous_spectrum)
    prev_sum = pd.read_csv(previous_summary)
    inc = pd.read_csv(increment_hist, comment="#")
    inc = inc.copy()
    inc["bin_key"] = inc["E_mid_MeV"].round(9)
    prev_spec = prev_spec.copy()
    prev_spec["bin_key"] = prev_spec["E_mid_MeV"].round(9)
    inc = prev_spec[["bin_key"]].merge(inc, on="bin_key", how="left")
    for col in ("D_weight_sum", "DD_yield_weight_sum"):
        inc[col] = inc[col].fillna(0.0)

    centers = prev_spec["E_mid_MeV"].to_numpy(dtype=float)
    if not np.allclose(centers, inc["E_mid_MeV"].fillna(prev_spec["E_mid_MeV"]).to_numpy(dtype=float), rtol=0.0, atol=1.0e-9):
        raise ValueError(f"bin centers do not match for {gate}")

    prev_d_total = float(prev_sum[(prev_sum["source"] == "0to4ps") & (prev_sum["metric"] == "D_weighted")]["total_weight"].iloc[0])
    prev_y_total = float(prev_sum[(prev_sum["source"] == "0to4ps") & (prev_sum["metric"] == "DD_yield_weighted")]["total_weight"].iloc[0])
    prev_d = prev_spec["D_weight_norm_0to4ps"].to_numpy(dtype=float) * prev_d_total
    prev_y = prev_spec["DD_yield_norm_0to4ps"].to_numpy(dtype=float) * prev_y_total
    inc_d = inc["D_weight_sum"].to_numpy(dtype=float)
    inc_y = inc["DD_yield_weight_sum"].to_numpy(dtype=float)
    total_d = prev_d + inc_d
    total_y = prev_y + inc_y

    out_prefix.parent.mkdir(parents=True, exist_ok=True)
    spectrum = pd.DataFrame(
        {
            "E_low_MeV": prev_spec["E_low_MeV"],
            "E_high_MeV": prev_spec["E_high_MeV"],
            "E_mid_MeV": centers,
            "D_weight_norm_0to4ps": norm(prev_d),
            "D_weight_norm_4to5ps": norm(inc_d),
            "D_weight_norm_0to5ps": norm(total_d),
            "DD_yield_norm_0to4ps": norm(prev_y),
            "DD_yield_norm_4to5ps": norm(inc_y),
            "DD_yield_norm_0to5ps": norm(total_y),
        }
    )
    spectrum_path = out_prefix.with_name(out_prefix.name + "_normalized_spectrum.csv")
    spectrum.to_csv(spectrum_path, index=False)

    rows: list[dict[str, float | str]] = []
    for name, d_hist, y_hist in [
        ("0to4ps", prev_d, prev_y),
        ("4to5ps", inc_d, inc_y),
        ("0to5ps", total_d, total_y),
    ]:
        rows.append(stats(name, "D_weighted", d_hist, centers))
        rows.append(stats(name, "DD_yield_weighted", y_hist, centers))
    for metric, attr in [("D_weighted", (prev_d, total_d)), ("DD_yield_weighted", (prev_y, total_y))]:
        rows.append({"source": "0to4ps_vs_0to5ps", "metric": metric + "_shape_distance", **shape_metrics(*attr)})
    rows.append({"source": "4to5ps_fraction_of_0to5ps", "metric": "D_weighted_total_fraction", "total_weight": float(np.sum(inc_d) / np.sum(total_d))})
    rows.append({"source": "4to5ps_fraction_of_0to5ps", "metric": "DD_yield_weighted_total_fraction", "total_weight": float(np.sum(inc_y) / np.sum(total_y))})
    summary = pd.DataFrame(rows)
    summary_path = out_prefix.with_name(out_prefix.name + "_spectrum_summary.csv")
    summary.to_csv(summary_path, index=False)

    fig, axes = plt.subplots(2, 1, figsize=(8.0, 7.0), sharex=True)
    axes[0].step(centers, norm(prev_y), where="mid", label="0-4 ps", linewidth=1.8)
    axes[0].step(centers, norm(total_y), where="mid", label="0-5 ps", linewidth=1.8)
    axes[0].step(centers, norm(inc_y), where="mid", label="4-5 ps only", linewidth=1.2, linestyle="--")
    axes[0].set_ylabel("Normalized DD-yield weight")
    axes[0].legend(frameon=False)
    axes[0].grid(alpha=0.25)
    axes[1].step(centers, norm(prev_d), where="mid", label="0-4 ps", linewidth=1.8)
    axes[1].step(centers, norm(total_d), where="mid", label="0-5 ps", linewidth=1.8)
    axes[1].step(centers, norm(inc_d), where="mid", label="4-5 ps only", linewidth=1.2, linestyle="--")
    axes[1].set_ylabel("Normalized D weight")
    axes[1].set_xlabel("Deuteron energy at rear+10 (MeV)")
    axes[1].legend(frameon=False)
    axes[1].grid(alpha=0.25)
    gate_label = "all E" if gate == "allE" else "E>0.4 MeV"
    fig.suptitle(f"rear+10 {gate_label} normalized spectra: 4 ps vs 5 ps")
    fig.tight_layout()
    plot_path = out_prefix.with_name(out_prefix.name + "_normalized_spectrum.png")
    fig.savefig(plot_path, dpi=220)
    plt.close(fig)
    return spectrum_path, summary_path, plot_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "hpc/results")
    parser.add_argument("--increment-dir", type=Path, default=Path("/tmp/no5_5ps_check"))
    args = parser.parse_args()

    jobs = [
        (
            "Egt0p4",
            ROOT / "hpc/results/pic3d_stage1_rear10_3ps_vs_4ps_normalized_spectrum.csv",
            ROOT / "hpc/results/pic3d_stage1_rear10_3ps_vs_4ps_spectrum_summary.csv",
            args.increment_dir / "hist_D_rear10_4to5ps_Egt0p4.csv",
            args.out_dir / "pic3d_stage1_rear10_4ps_vs_5ps",
        ),
        (
            "allE",
            ROOT / "hpc/results/pic3d_stage1_rear10_3ps_vs_4ps_allE_normalized_spectrum.csv",
            ROOT / "hpc/results/pic3d_stage1_rear10_3ps_vs_4ps_allE_spectrum_summary.csv",
            args.increment_dir / "hist_D_rear10_4to5ps_allE.csv",
            args.out_dir / "pic3d_stage1_rear10_4ps_vs_5ps_allE",
        ),
    ]
    for job in jobs:
        paths = compare(*job)
        for path in paths:
            print(path)


if __name__ == "__main__":
    main()
