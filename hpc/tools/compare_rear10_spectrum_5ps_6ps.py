#!/usr/bin/env python3
"""Compare cumulative rear+10 normalized spectra at 5 ps and 6 ps."""

from __future__ import annotations

import argparse
from pathlib import Path

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
    prev_d_total = float(
        prev_sum[(prev_sum["source"] == "0to5ps") & (prev_sum["metric"] == "D_weighted")][
            "total_weight"
        ].iloc[0]
    )
    prev_y_total = float(
        prev_sum[(prev_sum["source"] == "0to5ps") & (prev_sum["metric"] == "DD_yield_weighted")][
            "total_weight"
        ].iloc[0]
    )
    prev_d = prev_spec["D_weight_norm_0to5ps"].to_numpy(dtype=float) * prev_d_total
    prev_y = prev_spec["DD_yield_norm_0to5ps"].to_numpy(dtype=float) * prev_y_total
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
            "D_weight_norm_0to5ps": norm(prev_d),
            "D_weight_norm_5to6ps": norm(inc_d),
            "D_weight_norm_0to6ps": norm(total_d),
            "DD_yield_norm_0to5ps": norm(prev_y),
            "DD_yield_norm_5to6ps": norm(inc_y),
            "DD_yield_norm_0to6ps": norm(total_y),
        }
    )
    spectrum_path = out_prefix.with_name(out_prefix.name + "_normalized_spectrum.csv")
    spectrum.to_csv(spectrum_path, index=False)

    rows: list[dict[str, float | str]] = []
    for name, d_hist, y_hist in [
        ("0to5ps", prev_d, prev_y),
        ("5to6ps", inc_d, inc_y),
        ("0to6ps", total_d, total_y),
    ]:
        rows.append(stats(name, "D_weighted", d_hist, centers))
        rows.append(stats(name, "DD_yield_weighted", y_hist, centers))
    for metric, pair in [("D_weighted", (prev_d, total_d)), ("DD_yield_weighted", (prev_y, total_y))]:
        rows.append({"source": "0to5ps_vs_0to6ps", "metric": metric + "_shape_distance", **shape_metrics(*pair)})
    rows.append(
        {
            "source": "5to6ps_fraction_of_0to6ps",
            "metric": "D_weighted_total_fraction",
            "total_weight": float(np.sum(inc_d) / np.sum(total_d)),
        }
    )
    rows.append(
        {
            "source": "5to6ps_fraction_of_0to6ps",
            "metric": "DD_yield_weighted_total_fraction",
            "total_weight": float(np.sum(inc_y) / np.sum(total_y)),
        }
    )
    summary = pd.DataFrame(rows)
    summary_path = out_prefix.with_name(out_prefix.name + "_spectrum_summary.csv")
    summary.to_csv(summary_path, index=False)

    fig, axes = plt.subplots(2, 1, figsize=(8.0, 7.0), sharex=True)
    axes[0].step(centers, norm(prev_y), where="mid", label="0-5 ps", linewidth=1.8)
    axes[0].step(centers, norm(total_y), where="mid", label="0-6 ps", linewidth=1.8)
    axes[0].step(centers, norm(inc_y), where="mid", label="5-6 ps only", linewidth=1.2, linestyle="--")
    axes[0].set_ylabel("Normalized DD-yield weight")
    axes[0].legend(frameon=False)
    axes[0].grid(alpha=0.25)
    axes[1].step(centers, norm(prev_d), where="mid", label="0-5 ps", linewidth=1.8)
    axes[1].step(centers, norm(total_d), where="mid", label="0-6 ps", linewidth=1.8)
    axes[1].step(centers, norm(inc_d), where="mid", label="5-6 ps only", linewidth=1.2, linestyle="--")
    axes[1].set_ylabel("Normalized D weight")
    axes[1].set_xlabel("Deuteron energy at rear+10 (MeV)")
    axes[1].legend(frameon=False)
    axes[1].grid(alpha=0.25)
    gate_label = "all E" if gate == "allE" else "E>0.4 MeV"
    fig.suptitle(f"rear+10 {gate_label} normalized spectra: 5 ps vs 6 ps")
    fig.tight_layout()
    plot_path = out_prefix.with_name(out_prefix.name + "_normalized_spectrum.png")
    fig.savefig(plot_path, dpi=220)
    plt.close(fig)
    return spectrum_path, summary_path, plot_path


def write_convergence(increment_dir: Path, out_dir: Path) -> tuple[Path, Path]:
    previous = pd.read_csv(out_dir / "pic3d_stage1_rear10_5ps_dd_yield_windows.csv")
    frames = [previous]
    for gate, filename in [
        ("allE", "probe_dd_yield_5to6ps_allE.csv"),
        ("Egt0p4", "probe_dd_yield_5to6ps_Egt0p4.csv"),
    ]:
        df = pd.read_csv(increment_dir / filename)
        df = df[df["probe"] == "D_rear10"].copy()
        df.insert(0, "gate", gate)
        df.insert(1, "span", "5to6")
        df.insert(3, "window_start_fs", df["time_fs"] - 250.0)
        df.insert(4, "window_end_fs", df["time_fs"])
        frames.append(df[previous.columns])
    windows = pd.concat(frames, ignore_index=True)
    windows_path = out_dir / "pic3d_stage1_rear10_6ps_dd_yield_windows.csv"
    windows.to_csv(windows_path, index=False)

    prev_summary = pd.read_csv(out_dir / "pic3d_stage1_rear10_5ps_dd_yield_convergence_summary.csv")
    rows: list[dict[str, float | str | bool]] = []
    for gate, group in windows.groupby("gate", sort=False):
        prev = prev_summary[prev_summary["gate"] == gate].iloc[0]
        y_0to5 = float(prev["ddn_yield_0to5ps"])
        y_5to6 = float(group[group["span"] == "5to6"]["ddn_yield_sum"].sum())
        y_0to6 = y_0to5 + y_5to6
        last = float(group[(group["span"] == "5to6") & (group["sdf"] == "0024.sdf")]["ddn_yield_sum"].iloc[0])
        last_frac = last / y_0to6
        rows.append(
            {
                "gate": gate,
                "ddn_yield_0to5ps": y_0to5,
                "ddn_yield_5to6ps": y_5to6,
                "ddn_yield_0to6ps": y_0to6,
                "frac_5to6_of_0to6": y_5to6 / y_0to6,
                "last_250fs_yield_5p75to6ps": last,
                "last_250fs_frac_of_0to6": last_frac,
                "last_250fs_frac_of_5to6": last / y_5to6,
                "converged_by_10pct_last_window": bool(last_frac < 0.10),
                "decision": "accept_6ps_for_absolute_yield" if last_frac < 0.10 else "extend_or_use_spectrum_only",
            }
        )
    summary = pd.DataFrame(rows)
    summary_path = out_dir / "pic3d_stage1_rear10_6ps_dd_yield_convergence_summary.csv"
    summary.to_csv(summary_path, index=False)
    return windows_path, summary_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "hpc/results")
    parser.add_argument("--increment-dir", type=Path, default=Path("/tmp/no5_6ps_check"))
    args = parser.parse_args()

    jobs = [
        (
            "Egt0p4",
            ROOT / "hpc/results/pic3d_stage1_rear10_4ps_vs_5ps_normalized_spectrum.csv",
            ROOT / "hpc/results/pic3d_stage1_rear10_4ps_vs_5ps_spectrum_summary.csv",
            args.increment_dir / "hist_D_rear10_5to6ps_Egt0p4.csv",
            args.out_dir / "pic3d_stage1_rear10_5ps_vs_6ps",
        ),
        (
            "allE",
            ROOT / "hpc/results/pic3d_stage1_rear10_4ps_vs_5ps_allE_normalized_spectrum.csv",
            ROOT / "hpc/results/pic3d_stage1_rear10_4ps_vs_5ps_allE_spectrum_summary.csv",
            args.increment_dir / "hist_D_rear10_5to6ps_allE.csv",
            args.out_dir / "pic3d_stage1_rear10_5ps_vs_6ps_allE",
        ),
    ]
    for job in jobs:
        paths = compare(*job)
        for path in paths:
            print(path)
    for path in write_convergence(args.increment_dir, args.out_dir):
        print(path)


if __name__ == "__main__":
    main()
