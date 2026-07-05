#!/usr/bin/env python3
"""Compare normalized rear+10 deuteron spectra at 3 ps and 4 ps.

The primary comparison is D-D-yield weighted, i.e. each deuteron contributes
``weight * Y_DD(E)`` before the spectrum is normalized. This avoids judging
source convergence from cold-particle counts alone.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from moduleB_source.thick_target import cd2_deuteron_density_cm3, yield_integrand_per_MeV


@dataclass
class SpectrumStats:
    name: str
    n_rows_seen: int
    n_rows_pass: int
    hist_w: np.ndarray
    hist_y: np.ndarray
    weight_sum: float
    yield_weight_sum: float
    ew_sum: float
    ey_sum: float
    e_max: float
    gt_w: dict[float, float]
    gt_y: dict[float, float]


def build_yield_table(e_max_mev: float, n_grid: int = 20000) -> tuple[np.ndarray, np.ndarray]:
    grid = np.linspace(1.0e-4, e_max_mev, n_grid)
    integrand = yield_integrand_per_MeV(grid, cd2_deuteron_density_cm3())
    cumulative = np.zeros_like(grid)
    cumulative[1:] = np.cumsum(0.5 * (integrand[1:] + integrand[:-1]) * np.diff(grid))
    return grid, cumulative


def interp_yield(e_mev: np.ndarray, e_grid: np.ndarray, y_grid: np.ndarray) -> np.ndarray:
    clipped = np.clip(e_mev, e_grid[0], e_grid[-1])
    return np.interp(clipped, e_grid, y_grid)


def stream_spectrum(
    name: str,
    paths: list[Path],
    bins: np.ndarray,
    e_grid: np.ndarray,
    y_grid: np.ndarray,
    e_min_mev: float,
    thresholds: tuple[float, ...],
    chunksize: int,
) -> SpectrumStats:
    hist_w = np.zeros(len(bins) - 1, dtype=float)
    hist_y = np.zeros(len(bins) - 1, dtype=float)
    n_rows_seen = 0
    n_rows_pass = 0
    weight_sum = 0.0
    yield_weight_sum = 0.0
    ew_sum = 0.0
    ey_sum = 0.0
    e_max = 0.0
    gt_w = {thr: 0.0 for thr in thresholds}
    gt_y = {thr: 0.0 for thr in thresholds}

    usecols = ["E_MeV", "weight", "px"]
    for path in paths:
        for chunk in pd.read_csv(path, usecols=usecols, chunksize=chunksize):
            n_rows_seen += len(chunk)
            e = chunk["E_MeV"].to_numpy(dtype=float)
            w = chunk["weight"].to_numpy(dtype=float)
            px = chunk["px"].to_numpy(dtype=float)
            mask = np.isfinite(e) & np.isfinite(w) & np.isfinite(px) & (w > 0.0) & (px > 0.0) & (e > e_min_mev)
            if not np.any(mask):
                continue
            e = e[mask]
            w = w[mask]
            y_per_d = interp_yield(e, e_grid, y_grid)
            yw = w * y_per_d

            n_rows_pass += len(e)
            weight_sum += float(np.sum(w))
            yield_weight_sum += float(np.sum(yw))
            ew_sum += float(np.sum(e * w))
            ey_sum += float(np.sum(e * yw))
            e_max = max(e_max, float(np.max(e)))
            hist_w += np.histogram(e, bins=bins, weights=w)[0]
            hist_y += np.histogram(e, bins=bins, weights=yw)[0]
            for thr in thresholds:
                m = e > thr
                if np.any(m):
                    gt_w[thr] += float(np.sum(w[m]))
                    gt_y[thr] += float(np.sum(yw[m]))

    return SpectrumStats(
        name=name,
        n_rows_seen=n_rows_seen,
        n_rows_pass=n_rows_pass,
        hist_w=hist_w,
        hist_y=hist_y,
        weight_sum=weight_sum,
        yield_weight_sum=yield_weight_sum,
        ew_sum=ew_sum,
        ey_sum=ey_sum,
        e_max=e_max,
        gt_w=gt_w,
        gt_y=gt_y,
    )


def combine(name: str, a: SpectrumStats, b: SpectrumStats) -> SpectrumStats:
    return SpectrumStats(
        name=name,
        n_rows_seen=a.n_rows_seen + b.n_rows_seen,
        n_rows_pass=a.n_rows_pass + b.n_rows_pass,
        hist_w=a.hist_w + b.hist_w,
        hist_y=a.hist_y + b.hist_y,
        weight_sum=a.weight_sum + b.weight_sum,
        yield_weight_sum=a.yield_weight_sum + b.yield_weight_sum,
        ew_sum=a.ew_sum + b.ew_sum,
        ey_sum=a.ey_sum + b.ey_sum,
        e_max=max(a.e_max, b.e_max),
        gt_w={k: a.gt_w[k] + b.gt_w[k] for k in a.gt_w},
        gt_y={k: a.gt_y[k] + b.gt_y[k] for k in a.gt_y},
    )


def norm(hist: np.ndarray) -> np.ndarray:
    total = float(np.sum(hist))
    if total <= 0.0:
        return np.zeros_like(hist, dtype=float)
    return hist / total


def binned_mean(hist: np.ndarray, centers: np.ndarray) -> float:
    total = float(np.sum(hist))
    return float(np.sum(hist * centers) / total) if total > 0.0 else float("nan")


def binned_quantile(hist: np.ndarray, centers: np.ndarray, q: float) -> float:
    total = float(np.sum(hist))
    if total <= 0.0:
        return float("nan")
    cdf = np.cumsum(hist) / total
    return float(np.interp(q, cdf, centers))


def shape_metrics(p: np.ndarray, q: np.ndarray) -> dict[str, float]:
    p = norm(p)
    q = norm(q)
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


def stat_rows(stats: list[SpectrumStats], centers: np.ndarray, thresholds: tuple[float, ...]) -> list[dict[str, float | str]]:
    rows: list[dict[str, float | str]] = []
    for s in stats:
        for label, hist, total, ew_sum, gt in [
            ("D_weighted", s.hist_w, s.weight_sum, s.ew_sum, s.gt_w),
            ("DD_yield_weighted", s.hist_y, s.yield_weight_sum, s.ey_sum, s.gt_y),
        ]:
            row: dict[str, float | str] = {
                "source": s.name,
                "metric": label,
                "rows_seen": s.n_rows_seen,
                "rows_pass_gate": s.n_rows_pass,
                "total_weight": total,
                "E_mean_MeV": float(ew_sum / total) if total > 0 else float("nan"),
                "E_mean_binned_MeV": binned_mean(hist, centers),
                "E_p50_MeV": binned_quantile(hist, centers, 0.50),
                "E_p90_MeV": binned_quantile(hist, centers, 0.90),
                "E_p95_MeV": binned_quantile(hist, centers, 0.95),
                "E_p99_MeV": binned_quantile(hist, centers, 0.99),
                "E_max_seen_MeV": s.e_max,
            }
            for thr in thresholds:
                row[f"frac_E_gt_{thr:g}_MeV"] = float(gt[thr] / total) if total > 0 else float("nan")
            rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--three-ps-dir", type=Path, default=ROOT / "hpc/results/phase_space/rear10_0to3ps")
    parser.add_argument("--four-ps-dir", type=Path, default=Path("/tmp/no5_4ps_check/phase"))
    parser.add_argument("--out-prefix", type=Path, default=ROOT / "hpc/results/pic3d_stage1_rear10_3ps_vs_4ps")
    parser.add_argument("--e-min-MeV", type=float, default=0.4)
    parser.add_argument("--e-max-MeV", type=float, default=1.6)
    parser.add_argument("--bin-width-MeV", type=float, default=0.02)
    parser.add_argument("--chunksize", type=int, default=200000)
    args = parser.parse_args()

    three_paths = sorted(p for p in args.three_ps_dir.glob("*_D_rear10_phase.csv") if not p.name.startswith("._"))
    four_paths = sorted(p for p in args.four_ps_dir.glob("phase_D_rear10_001[3-6].csv") if not p.name.startswith("._"))
    if not three_paths:
        raise FileNotFoundError(f"no 3 ps phase CSVs found in {args.three_ps_dir}")
    if not four_paths:
        raise FileNotFoundError(f"no 3-4 ps phase CSVs found in {args.four_ps_dir}")

    bins = np.arange(args.e_min_MeV, args.e_max_MeV + 0.5 * args.bin_width_MeV, args.bin_width_MeV)
    centers = 0.5 * (bins[:-1] + bins[1:])
    e_grid, y_grid = build_yield_table(args.e_max_MeV)
    y_centers = interp_yield(centers, e_grid, y_grid)
    thresholds = (0.5, 0.6, 0.8, 1.0, 1.2)

    s3 = stream_spectrum("0to3ps", three_paths, bins, e_grid, y_grid, args.e_min_MeV, thresholds, args.chunksize)
    sadd = stream_spectrum("3to4ps", four_paths, bins, e_grid, y_grid, args.e_min_MeV, thresholds, args.chunksize)
    s4 = combine("0to4ps", s3, sadd)

    args.out_prefix.parent.mkdir(parents=True, exist_ok=True)

    spectrum = pd.DataFrame(
        {
            "E_low_MeV": bins[:-1],
            "E_high_MeV": bins[1:],
            "E_mid_MeV": centers,
            "Y_DD_per_deuteron": y_centers,
            "D_weight_norm_0to3ps": norm(s3.hist_w),
            "D_weight_norm_3to4ps": norm(sadd.hist_w),
            "D_weight_norm_0to4ps": norm(s4.hist_w),
            "DD_yield_norm_0to3ps": norm(s3.hist_y),
            "DD_yield_norm_3to4ps": norm(sadd.hist_y),
            "DD_yield_norm_0to4ps": norm(s4.hist_y),
        }
    )
    spectrum_path = args.out_prefix.with_name(args.out_prefix.name + "_normalized_spectrum.csv")
    spectrum.to_csv(spectrum_path, index=False)

    summary_rows = stat_rows([s3, sadd, s4], centers, thresholds)
    for label, attr in [("D_weighted", "hist_w"), ("DD_yield_weighted", "hist_y")]:
        metrics = shape_metrics(getattr(s3, attr), getattr(s4, attr))
        summary_rows.append(
            {
                "source": "0to3ps_vs_0to4ps",
                "metric": label + "_shape_distance",
                "rows_seen": "",
                "rows_pass_gate": "",
                "total_weight": "",
                "E_mean_MeV": "",
                "E_mean_binned_MeV": "",
                "E_p50_MeV": "",
                "E_p90_MeV": "",
                "E_p95_MeV": "",
                "E_p99_MeV": "",
                "E_max_seen_MeV": "",
                **metrics,
            }
        )
    summary_rows.append(
        {
            "source": "3to4ps_fraction_of_0to4ps",
            "metric": "D_weighted_total_fraction",
            "total_weight": float(sadd.weight_sum / s4.weight_sum) if s4.weight_sum > 0 else float("nan"),
        }
    )
    summary_rows.append(
        {
            "source": "3to4ps_fraction_of_0to4ps",
            "metric": "DD_yield_weighted_total_fraction",
            "total_weight": float(sadd.yield_weight_sum / s4.yield_weight_sum) if s4.yield_weight_sum > 0 else float("nan"),
        }
    )
    summary_path = args.out_prefix.with_name(args.out_prefix.name + "_spectrum_summary.csv")
    pd.DataFrame(summary_rows).to_csv(summary_path, index=False)

    fig, axes = plt.subplots(2, 1, figsize=(8.0, 7.0), sharex=True)
    axes[0].step(centers, norm(s3.hist_y), where="mid", label="0-3 ps", linewidth=1.8)
    axes[0].step(centers, norm(s4.hist_y), where="mid", label="0-4 ps", linewidth=1.8)
    axes[0].step(centers, norm(sadd.hist_y), where="mid", label="3-4 ps only", linewidth=1.2, linestyle="--")
    axes[0].set_ylabel("Normalized DD-yield weight")
    axes[0].legend(frameon=False)
    axes[0].grid(alpha=0.25)

    axes[1].step(centers, norm(s3.hist_w), where="mid", label="0-3 ps", linewidth=1.8)
    axes[1].step(centers, norm(s4.hist_w), where="mid", label="0-4 ps", linewidth=1.8)
    axes[1].step(centers, norm(sadd.hist_w), where="mid", label="3-4 ps only", linewidth=1.2, linestyle="--")
    axes[1].set_ylabel("Normalized D weight")
    axes[1].set_xlabel("Deuteron energy at rear+10 (MeV)")
    axes[1].grid(alpha=0.25)
    axes[1].legend(frameon=False)

    gate_label = "all E" if args.e_min_MeV <= 0.0 else f"E>{args.e_min_MeV:g} MeV"
    fig.suptitle(f"rear+10 {gate_label} normalized spectra: 3 ps vs 4 ps")
    fig.tight_layout()
    plot_path = args.out_prefix.with_name(args.out_prefix.name + "_normalized_spectrum.png")
    fig.savefig(plot_path, dpi=220)

    print(f"wrote {spectrum_path}")
    print(f"wrote {summary_path}")
    print(f"wrote {plot_path}")
    print(pd.DataFrame(summary_rows).to_string(index=False))


if __name__ == "__main__":
    main()
