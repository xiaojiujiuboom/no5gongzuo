"""Run C3 HDPE moderator thickness sweep.

This extends the C1 Part 4 geometry without overwriting the original Part 4
outputs. All heavy OpenMC products are written under the no6 data area.
"""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_c1_part1_3 import (
    CROSS_SECTIONS,
    LI6_CASES,
    NO6_ROOT,
    OPENMC_BIN,
    PIC_ROOT,
    li_tag,
    run_model_if_needed,
    source_description_row,
    tally_sum,
)
from scripts.run_c1_part4_moderator import build_moderator_model, summarize_statepoint, thickness_tag


OUT_ROOT = NO6_ROOT / "openmc_c1_20260706" / "c3_hdpe_sweep_20260707"
SOURCE_IDS = ["pic2d_a0_10_t_3um", "pic2d_a0_20_t_3um"]
HDPE_CM = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]


def configure_env() -> None:
    os.environ["OPENMC_CROSS_SECTIONS"] = str(CROSS_SECTIONS)
    os.environ["PATH"] = f"{OPENMC_BIN}:{os.environ.get('PATH', '')}"


def run_all(args: argparse.Namespace) -> pd.DataFrame:
    configure_env()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    run_root = OUT_ROOT / "openmc_runs"
    run_root.mkdir(parents=True, exist_ok=True)

    sources = {sid: PIC_ROOT / sid / "neutron_source_pstar.h5" for sid in SOURCE_IDS}
    source_desc = {
        sid: source_description_row(
            SimpleNamespace(
                source_id=sid,
                family="pic2d",
                neutron_h5=nsrc,
                deuteron_h5=PIC_ROOT / sid / "deuteron_beam.h5",
                kT_MeV=None,
                theta_max_deg=None,
                E_max_MeV=None,
            )
        )
        for sid, nsrc in sources.items()
    }

    rows: list[dict[str, object]] = []
    for hdpe in HDPE_CM:
        for li6 in LI6_CASES:
            case_a_dir = run_root / f"caseA_hdpe_{thickness_tag(hdpe)}cm_li6_{li_tag(li6)}"
            model = build_moderator_model("A", li6, hdpe, None, args.batches, args.particles)
            print(f"RUN C3 Case A HDPE={hdpe:g} cm Li6={li6:g}", flush=True)
            sp_a = run_model_if_needed(model, case_a_dir, threads=args.threads, force=args.force_openmc)
            a_vals = summarize_statepoint(sp_a)

            for sid, nsrc in sources.items():
                case_b_dir = run_root / f"caseB_{sid}_hdpe_{thickness_tag(hdpe)}cm_li6_{li_tag(li6)}"
                model = build_moderator_model("B", li6, hdpe, nsrc, args.batches, args.particles)
                print(f"RUN C3 Case B {sid} HDPE={hdpe:g} cm Li6={li6:g}", flush=True)
                sp_b = run_model_if_needed(model, case_b_dir, threads=args.threads, force=args.force_openmc)
                b_vals = summarize_statepoint(sp_b)

                row = {
                    **source_desc[sid],
                    "hdpe_cm": hdpe,
                    "li6_atpct": li6,
                    "CaseA_statepoint": str(sp_a),
                    "CaseB_statepoint": str(sp_b),
                }
                for prefix, vals in [("A", a_vals), ("B", b_vals)]:
                    for key, value in vals.items():
                        row[f"{prefix}_{key}"] = value
                for tally in ["Li6", "Li7", "total"]:
                    a = a_vals[f"TPR_{tally}_per_n"]
                    b = b_vals[f"TPR_{tally}_per_n"]
                    row[f"ratio_B_over_A_{tally}"] = b / a if a else float("nan")
                rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(OUT_ROOT / "c3_hdpe_sweep_summary.csv", index=False)
    make_compact_tables(df)
    plot(df)
    write_report(df, args)
    return df


def make_compact_tables(df: pd.DataFrame) -> None:
    cols = [
        "source_id",
        "li6_atpct",
        "hdpe_cm",
        "A_TPR_Li6_per_n",
        "A_TPR_Li7_per_n",
        "A_TPR_total_per_n",
        "B_TPR_Li6_per_n",
        "B_TPR_Li7_per_n",
        "B_TPR_total_per_n",
        "ratio_B_over_A_total",
        "B_TPR_total_rel_err",
    ]
    df[cols].to_csv(OUT_ROOT / "c3_hdpe_sweep_compact.csv", index=False)


def plot(df: pd.DataFrame) -> None:
    figdir = OUT_ROOT / "figures"
    figdir.mkdir(parents=True, exist_ok=True)
    for li6 in LI6_CASES:
        for ycol, ylabel, name in [
            ("ratio_B_over_A_total", "Case B / Case A total TPR", "B_over_A"),
            ("B_TPR_total_per_n", "Case B total TPR per source neutron", "total_tpr"),
            ("B_TPR_Li7_per_n", "Case B Li7 TPR per source neutron", "li7_tpr"),
        ]:
            fig, ax = plt.subplots(figsize=(7.8, 4.8))
            for sid, marker in [("pic2d_a0_10_t_3um", "o"), ("pic2d_a0_20_t_3um", "s")]:
                part = df[(df["li6_atpct"] == li6) & (df["source_id"] == sid)].sort_values("hdpe_cm")
                ax.plot(part["hdpe_cm"], part[ycol], marker=marker, lw=1.8, label=sid)
            if ycol == "ratio_B_over_A_total":
                ax.axhline(1.0, color="0.25", ls="--", lw=1.0)
            ax.set_xlabel("HDPE shell thickness (cm)")
            ax.set_ylabel(ylabel)
            ax.set_title(f"C3 HDPE sweep, Li6={li6:g} at%")
            ax.grid(alpha=0.22)
            ax.legend(fontsize=8)
            fig.tight_layout()
            fig.savefig(figdir / f"c3_hdpe_sweep_{name}_li6_{li_tag(li6)}.png", dpi=240)
            plt.close(fig)


def write_report(df: pd.DataFrame, args: argparse.Namespace) -> None:
    lines = [
        "# C3 HDPE moderator thickness sweep",
        "",
        "This is a new output directory and does not overwrite C1 Part 4.",
        "",
        f"- Nuclear data: `{CROSS_SECTIONS}`",
        f"- Statistics: `{args.batches}` batches x `{args.particles}` particles.",
        "- Geometry: same spherical HDPE-shell variant as C1 Part 4.",
        "- Thicknesses: 0, 1, 2, 3, 4, 5 cm.",
        "- Sources: `pic2d_a0_10_t_3um` and `pic2d_a0_20_t_3um`.",
        "- Lithium: natural 7.59 at.% Li6 and 90 at.% Li6.",
        "",
        "## Acceptance check",
        "",
    ]
    for li6 in LI6_CASES:
        lines.append(f"### Li6={li6:g} at%")
        for sid in SOURCE_IDS:
            part = df[(df["li6_atpct"] == li6) & (df["source_id"] == sid)].sort_values("hdpe_cm")
            ratios = ", ".join(f"{r.hdpe_cm:g} cm: {r.ratio_B_over_A_total:.4f}" for r in part.itertuples())
            totals = ", ".join(f"{r.hdpe_cm:g} cm: {r.B_TPR_total_per_n:.5g}" for r in part.itertuples())
            lines.append(f"- `{sid}` B/A total: {ratios}.")
            lines.append(f"- `{sid}` Case B total TPR/n: {totals}.")
        lines.append("")
    lines.extend(
        [
            "## Files",
            "",
            "- `c3_hdpe_sweep_summary.csv`: same wide format as C1 Part 4.",
            "- `c3_hdpe_sweep_compact.csv`: compact plotting/result table.",
            "- `figures/c3_hdpe_sweep_*.png`: sweep plots.",
            "- `openmc_runs/`: local OpenMC statepoints, not for git.",
            "",
        ]
    )
    (OUT_ROOT / "README.md").write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threads", type=int, default=12)
    parser.add_argument("--batches", type=int, default=100)
    parser.add_argument("--particles", type=int, default=1_000_000)
    parser.add_argument("--force-openmc", action="store_true")
    args = parser.parse_args()
    run_all(args)
    print(f"wrote {OUT_ROOT / 'c3_hdpe_sweep_summary.csv'}")
    print(f"wrote {OUT_ROOT / 'README.md'}")


if __name__ == "__main__":
    main()
