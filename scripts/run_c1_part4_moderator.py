"""Run C1 Part 4 HDPE moderator control cases.

This is a separate geometry variant: a spherical HDPE shell is inserted between
the central source cavity and the lithium cylinder. Baseline C1 geometry and
Case A/B source builders are left untouched.
"""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from moduleC_openmc._compat import require_openmc
from moduleC_openmc.geometry import make_geometry_with_spherical_moderator
from moduleC_openmc.materials import make_materials_with_hdpe
from moduleC_openmc.source import make_case_a_source, make_case_b_sources
from moduleC_openmc.tallies import make_tallies
from utils.config import load_config

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


OUT_ROOT = NO6_ROOT / "openmc_c1_20260706" / "part4_hdpe_moderator"
SOURCE_IDS = ["pic2d_a0_10_t_3um", "pic2d_a0_20_t_3um"]
HDPE_CM = [0.0, 2.0, 5.0]


def configure_env() -> None:
    os.environ["OPENMC_CROSS_SECTIONS"] = str(CROSS_SECTIONS)
    path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{OPENMC_BIN}:{path}"


def thickness_tag(value: float) -> str:
    return ("%g" % value).replace(".", "p")


def build_moderator_model(
    case: str,
    li6_atpct: float,
    hdpe_cm: float,
    neutron_h5: Path | None,
    batches: int,
    particles: int,
):
    openmc = require_openmc()
    cfg = load_config(ROOT / "config.yaml")
    li_cfg = cfg.get("lithium", {})
    bin_cfg = cfg.get("source_bins", {})
    radius = float(li_cfg.get("radius_cm", 10.0))
    height = float(li_cfg.get("height_cm", 20.0))
    cavity = float(li_cfg.get("cavity_radius_cm", 1.0))
    li_density = float(li_cfg.get("density_g_cm3", 0.534))

    materials = make_materials_with_hdpe(li6_atpct, li_density_g_cm3=li_density)
    geometry = make_geometry_with_spherical_moderator(
        materials[0],
        materials[1],
        radius,
        height,
        cavity,
        hdpe_cm,
    )
    tallies = make_tallies(radius, height)
    settings = openmc.Settings()
    settings.run_mode = "fixed source"
    settings.batches = int(batches)
    settings.particles = int(particles)
    settings.photon_transport = False
    if case == "A":
        settings.source = make_case_a_source()
    elif case == "B":
        if neutron_h5 is None:
            raise ValueError("Case B requires neutron_h5")
        settings.source = make_case_b_sources(
            neutron_h5,
            n_mu=int(bin_cfg.get("n_mu", 15)),
            n_E=int(bin_cfg.get("n_E", 100)),
        )
    else:
        raise ValueError(case)
    return openmc.Model(geometry=geometry, materials=materials, settings=settings, tallies=tallies)


def summarize_statepoint(sp: Path) -> dict[str, float]:
    li6_v, li6_s, li6_r = tally_sum(sp, "TPR_Li6")
    li7_v, li7_s, li7_r = tally_sum(sp, "TPR_Li7")
    total = li6_v + li7_v
    total_s = float(math.sqrt(li6_s * li6_s + li7_s * li7_s))
    return {
        "TPR_Li6_per_n": li6_v,
        "TPR_Li6_std": li6_s,
        "TPR_Li6_rel_err": li6_r,
        "TPR_Li7_per_n": li7_v,
        "TPR_Li7_std": li7_s,
        "TPR_Li7_rel_err": li7_r,
        "TPR_total_per_n": total,
        "TPR_total_std": total_s,
        "TPR_total_rel_err": total_s / total if total else float("nan"),
    }


def run_all(args: argparse.Namespace) -> pd.DataFrame:
    configure_env()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    run_root = OUT_ROOT / "openmc_runs"
    run_root.mkdir(parents=True, exist_ok=True)

    sources = {
        sid: PIC_ROOT / sid / "neutron_source_pstar.h5"
        for sid in SOURCE_IDS
    }
    rows: list[dict[str, object]] = []
    source_desc = {
        sid: source_description_row(SimpleNamespace(
            source_id=sid,
            family="pic2d",
            neutron_h5=nsrc,
            deuteron_h5=PIC_ROOT / sid / "deuteron_beam.h5",
            kT_MeV=None,
            theta_max_deg=None,
            E_max_MeV=None,
        ))
        for sid, nsrc in sources.items()
    }

    for hdpe in HDPE_CM:
        for li6 in LI6_CASES:
            case_a_dir = run_root / f"caseA_hdpe_{thickness_tag(hdpe)}cm_li6_{li_tag(li6)}"
            model = build_moderator_model("A", li6, hdpe, None, args.batches, args.particles)
            print(f"RUN Part4 Case A HDPE={hdpe:g} cm Li6={li6:g}", flush=True)
            sp_a = run_model_if_needed(model, case_a_dir, threads=args.threads, force=args.force_openmc)
            a_vals = summarize_statepoint(sp_a)

            for sid, nsrc in sources.items():
                case_b_dir = run_root / f"caseB_{sid}_hdpe_{thickness_tag(hdpe)}cm_li6_{li_tag(li6)}"
                model = build_moderator_model("B", li6, hdpe, nsrc, args.batches, args.particles)
                print(f"RUN Part4 Case B {sid} HDPE={hdpe:g} cm Li6={li6:g}", flush=True)
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
    df.to_csv(OUT_ROOT / "c1_part4_hdpe_moderator_summary.csv", index=False)
    plot(df)
    write_report(df)
    return df


def plot(df: pd.DataFrame) -> None:
    figdir = OUT_ROOT / "figures"
    figdir.mkdir(parents=True, exist_ok=True)
    for li6 in LI6_CASES:
        fig, ax = plt.subplots(figsize=(7.8, 4.8))
        for sid, marker in [("pic2d_a0_10_t_3um", "o"), ("pic2d_a0_20_t_3um", "s")]:
            part = df[(df["li6_atpct"] == li6) & (df["source_id"] == sid)].sort_values("hdpe_cm")
            ax.plot(part["hdpe_cm"], part["ratio_B_over_A_total"], marker=marker, lw=1.8, label=sid)
        ax.axhline(1.0, color="0.25", ls="--", lw=1.0)
        ax.set_xlabel("HDPE shell thickness (cm)")
        ax.set_ylabel("Case B / Case A total TPR")
        ax.set_title(f"C1 Part 4 moderation effect, Li6={li6:g} at%")
        ax.grid(alpha=0.22)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(figdir / f"c1_part4_hdpe_B_over_A_li6_{li_tag(li6)}.png", dpi=240)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(7.8, 4.8))
        for sid, marker in [("pic2d_a0_10_t_3um", "o"), ("pic2d_a0_20_t_3um", "s")]:
            part = df[(df["li6_atpct"] == li6) & (df["source_id"] == sid)].sort_values("hdpe_cm")
            ax.plot(part["hdpe_cm"], part["B_TPR_total_per_n"], marker=marker, lw=1.8, label=sid)
        ax.set_xlabel("HDPE shell thickness (cm)")
        ax.set_ylabel("Case B total TPR per source neutron")
        ax.set_title(f"C1 Part 4 total TPR with moderation, Li6={li6:g} at%")
        ax.grid(alpha=0.22)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(figdir / f"c1_part4_hdpe_total_tpr_li6_{li_tag(li6)}.png", dpi=240)
        plt.close(fig)


def write_report(df: pd.DataFrame) -> None:
    lines = [
        "# C1 Part 4 HDPE moderator control",
        "",
        "Geometry variant: the source cavity is wrapped in a spherical HDPE shell of 0/2/5 cm, then surrounded by the same lithium cylinder used in the baseline.",
        "",
        f"- Nuclear data: `{CROSS_SECTIONS}`",
        "- Tallies are per source neutron.",
        "- Statistics: 100 batches x 1,000,000 particles for the production run.",
        "- Sources: `pic2d_a0_10_t_3um` and `pic2d_a0_20_t_3um`.",
        "",
        "## Acceptance view",
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
            "- `c1_part4_hdpe_moderator_summary.csv`: all A/B tallies and ratios.",
            "- `figures/c1_part4_hdpe_B_over_A_li6_*.png`: B/A vs HDPE thickness.",
            "- `figures/c1_part4_hdpe_total_tpr_li6_*.png`: total TPR/n vs HDPE thickness.",
            "- OpenMC statepoints remain local under `openmc_runs/` and should not be committed.",
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
    print(f"wrote {OUT_ROOT / 'c1_part4_hdpe_moderator_summary.csv'}")
    print(f"wrote {OUT_ROOT / 'README.md'}")


if __name__ == "__main__":
    main()
