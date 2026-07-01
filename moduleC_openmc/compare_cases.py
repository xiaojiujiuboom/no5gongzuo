"""Compare OpenMC Case A/B statepoints and emit tables/figures."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from interfaces.schema import read_neutron_source
from moduleC_openmc._compat import require_openmc


def _combined_mean_std(tally) -> tuple[float, float, float]:
    mean = np.asarray(tally.mean, dtype=float)
    std = np.asarray(tally.std_dev, dtype=float)
    total = float(np.sum(mean))
    total_std = float(np.sqrt(np.sum(std * std)))
    rel = total_std / abs(total) if total else float("nan")
    return total, total_std, rel


def _get_tally_sum(sp, name: str) -> tuple[float, float, float]:
    return _combined_mean_std(sp.get_tally(name=name))


def _energy_bins(openmc, tally):
    efilter = tally.find_filter(openmc.EnergyFilter)
    bins = np.asarray(efilter.bins, dtype=float)
    if bins.ndim == 1:
        return bins[:-1], bins[1:]
    return bins[:, 0], bins[:, 1]


def _energy_rows(openmc, sp, name: str):
    tally = sp.get_tally(name=name)
    e_lo, e_hi = _energy_bins(openmc, tally)
    mean = np.asarray(tally.mean, dtype=float).reshape(len(e_lo), -1).sum(axis=1)
    std = np.asarray(tally.std_dev, dtype=float).reshape(len(e_lo), -1)
    std_sum = np.sqrt(np.sum(std * std, axis=1))
    return e_lo, e_hi, mean, std_sum


def _source_stats(neutron_h5: str | None) -> dict[str, float]:
    if not neutron_h5:
        return {}
    src = read_neutron_source(neutron_h5)
    w = src.weight
    total = float(np.sum(w))
    above = src.E > 2.82
    forward = src.dir[:, 2] > 0.8
    return {
        "source_N": float(src.E.size),
        "source_Y_total": total,
        "source_E_weighted_mean_MeV": float(np.average(src.E, weights=w)),
        "source_E_max_MeV": float(np.max(src.E)),
        "source_weight_frac_E_gt_2p82": float(np.sum(w[above]) / total),
        "source_weight_frac_E_gt_2p82_mu_gt_0p8": float(np.sum(w[above & forward]) / total),
    }


def compare(case_a: str | Path, case_b: str | Path, output_dir: str | Path, source_b: str | None = None) -> None:
    openmc = require_openmc()
    import matplotlib.pyplot as plt

    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    rows = []
    with openmc.StatePoint(case_a) as sp_a, openmc.StatePoint(case_b) as sp_b:
        for tally_name in ["TPR_Li6", "TPR_Li7", "TPR_mesh"]:
            a_mean, a_std, a_rel = _get_tally_sum(sp_a, tally_name)
            b_mean, b_std, b_rel = _get_tally_sum(sp_b, tally_name)
            rel_delta = (b_mean - a_mean) / a_mean if a_mean else float("nan")
            rows.append(
                {
                    "tally": tally_name,
                    "case_A_mean": a_mean,
                    "case_A_std": a_std,
                    "case_A_rel_err": a_rel,
                    "case_B_mean": b_mean,
                    "case_B_std": b_std,
                    "case_B_rel_err": b_rel,
                    "B_minus_A_over_A": rel_delta,
                }
            )

        e_lo_a, e_hi_a, mean_a, std_a = _energy_rows(openmc, sp_a, "TPR_Li7_vs_E")
        e_lo_b, e_hi_b, mean_b, std_b = _energy_rows(openmc, sp_b, "TPR_Li7_vs_E")
        if not np.allclose(e_lo_a, e_lo_b) or not np.allclose(e_hi_a, e_hi_b):
            raise ValueError("Case A/B energy tally bins do not match")

    source_stats = _source_stats(source_b)
    summary_csv = outdir / "case_comparison_summary.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as f:
        fieldnames = list(rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    if source_stats:
        with (outdir / "case_B_source_stats.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["metric", "value"])
            for key, value in source_stats.items():
                writer.writerow([key, value])

    energy_csv = outdir / "li7_tpr_vs_energy.csv"
    with energy_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["E_low_eV", "E_high_eV", "E_mid_MeV", "case_A_mean", "case_A_std", "case_B_mean", "case_B_std"])
        for lo, hi, a, sa, b, sb in zip(e_lo_a, e_hi_a, mean_a, std_a, mean_b, std_b):
            writer.writerow([lo, hi, 0.5 * (lo + hi) / 1.0e6, a, sa, b, sb])

    labels = ["Li6", "Li7"]
    a_vals = [rows[0]["case_A_mean"], rows[1]["case_A_mean"]]
    b_vals = [rows[0]["case_B_mean"], rows[1]["case_B_mean"]]
    x = np.arange(len(labels))
    width = 0.36
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    ax.bar(x - width / 2, a_vals, width, label="Case A")
    ax.bar(x + width / 2, b_vals, width, label="Case B")
    ax.set_xticks(x, labels)
    ax.set_ylabel("TPR per source neutron")
    ax.set_title("Li6/Li7 tritium production")
    ax.legend()
    fig.tight_layout()
    fig.savefig(outdir / "li6_li7_tpr_bar.png", dpi=220)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    e_mid = 0.5 * (e_lo_a + e_hi_a) / 1.0e6
    ax.step(e_mid, mean_a, where="mid", label="Case A")
    ax.step(e_mid, mean_b, where="mid", label="Case B")
    ax.axvline(2.82, color="k", linestyle="--", linewidth=1.0, label="Li7 threshold")
    ax.set_xlabel("Incident neutron energy (MeV)")
    ax.set_ylabel("Li7 TPR per source neutron")
    ax.set_title("Li7 threshold-window contribution")
    ax.set_yscale("symlog", linthresh=1.0e-12)
    ax.legend()
    fig.tight_layout()
    fig.savefig(outdir / "li7_tpr_vs_energy.png", dpi=220)
    plt.close(fig)

    print(f"wrote {summary_csv}")
    print(f"wrote {energy_csv}")
    print(f"wrote figures in {outdir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-a", required=True, help="Case A statepoint.h5")
    parser.add_argument("--case-b", required=True, help="Case B statepoint.h5")
    parser.add_argument("--source-b", default=None, help="Case B neutron_source.h5")
    parser.add_argument("--output-dir", default="outputs/analysis/openmc_compare")
    args = parser.parse_args()
    compare(args.case_a, args.case_b, args.output_dir, args.source_b)


if __name__ == "__main__":
    main()

