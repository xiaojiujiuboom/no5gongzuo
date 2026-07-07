"""Quantify the impact of discarding deuterons above 9.8 MeV.

The baseline Stage B source builder does not hard-code a 9.8 MeV cut. This
script answers the conservative sensitivity question: if all incident
deuterons with E_D > 9.8 MeV were discarded before building the CD2 D(d,n)
source, how many neutrons and natural-lithium Li7 tritium counts would be lost?
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from interfaces.schema import read_deuteron_beam, read_neutron_source, write_deuteron_beam
from moduleA_pic.parametric_beam import generate_parametric_beam
from moduleB_source.build_source_fast import (
    _build_yield_table,
    _dd_neutron_lab_vectorized,
    build_neutron_source_fast,
)
from moduleC_openmc.run import build_model

from scripts.run_c1_part1_3 import (
    C0_ROOT,
    CROSS_SECTIONS,
    NO6_ROOT,
    OPENMC_BIN,
    OUT_ROOT as C1_OUT_ROOT,
    PIC_ROOT,
    li_tag_c0,
    run_model_if_needed,
    tally_sum,
)


OUT_ROOT = NO6_ROOT / "openmc_c1_20260706" / "cutoff_9p8MeV_sensitivity"
CUTOFF_MEV = 9.8
LI6_NATURAL = 7.59


@dataclass(frozen=True)
class CaseSpec:
    source_id: str
    family: str
    deuteron_h5: Path
    full_neutron_h5: Path
    full_case_b_statepoint: Path


CASES = [
    CaseSpec(
        source_id="pic2d_a0_20_t_3um",
        family="pic2d",
        deuteron_h5=PIC_ROOT / "pic2d_a0_20_t_3um" / "deuteron_beam.h5",
        full_neutron_h5=PIC_ROOT / "pic2d_a0_20_t_3um" / "neutron_source_pstar.h5",
        full_case_b_statepoint=C0_ROOT / f"caseB_prod_pic2d_a0_20_t_3um_li6_{li_tag_c0(LI6_NATURAL)}_pstar" / "statepoint.100.h5",
    ),
]


def configure_env() -> None:
    os.environ["OPENMC_CROSS_SECTIONS"] = str(CROSS_SECTIONS)
    path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{OPENMC_BIN}:{path}"


def truncate_deuterons(spec: CaseSpec) -> Path:
    beam = read_deuteron_beam(spec.deuteron_h5)
    keep = beam.E <= CUTOFF_MEV
    outdir = OUT_ROOT / spec.source_id
    outdir.mkdir(parents=True, exist_ok=True)
    truncated = outdir / "deuteron_beam_Ele9p8MeV.h5"
    write_deuteron_beam(
        truncated,
        beam.E[keep],
        beam.dir[keep],
        beam.weight[keep],
        beam.t[keep],
        attrs={
            **beam.attrs,
            "cutoff_sensitivity": "discard incident deuterons with E_D > 9.8 MeV",
            "E_D_cutoff_MeV": CUTOFF_MEV,
            "n_input_original": int(beam.E.size),
            "n_input_kept": int(np.sum(keep)),
            "weight_original": float(np.sum(beam.weight)),
            "weight_kept": float(np.sum(beam.weight[keep])),
            "weight_discarded": float(np.sum(beam.weight[~keep])),
        },
    )
    return truncated


def build_truncated_source(spec: CaseSpec, seed: int) -> Path:
    truncated_d = truncate_deuterons(spec)
    truncated_n = OUT_ROOT / spec.source_id / "neutron_source_pstar_Ed_le_9p8MeV.h5"
    if not truncated_n.exists():
        build_neutron_source_fast(
            truncated_d,
            truncated_n,
            seed=seed,
            stopping_table=ROOT / "data/stopping_D_in_CD2.csv",
            table_grid=8192,
        )
    return truncated_n


def build_high_deuteron_component_source(spec: CaseSpec, seed: int, min_samples: int = 100_000) -> Path:
    """Build the neutron source contributed only by incident D with E > cutoff."""
    beam = read_deuteron_beam(spec.deuteron_h5)
    high = beam.E > CUTOFF_MEV
    if not np.any(high):
        raise ValueError(f"{spec.source_id} has no deuterons above {CUTOFF_MEV} MeV")

    E0 = beam.E[high]
    direction0 = beam.dir[high]
    weight0 = beam.weight[high]
    t0 = beam.t[high]
    repeats = max(1, int(np.ceil(min_samples / E0.size)))
    E = np.repeat(E0, repeats)
    direction = np.repeat(direction0, repeats, axis=0)
    weight = np.repeat(weight0 / repeats, repeats)
    t = np.repeat(t0, repeats)

    outdir = OUT_ROOT / spec.source_id
    outdir.mkdir(parents=True, exist_ok=True)
    high_n = outdir / "neutron_source_pstar_Ed_gt_9p8MeV_component.h5"
    if high_n.exists():
        return high_n

    rng = np.random.default_rng(seed)
    grid, cumulative = _build_yield_table(
        float(np.max(beam.E)) if beam.E.size else 1.0,
        12000,
        1.06,
        ROOT / "data/stopping_D_in_CD2.csv",
    )
    y = np.interp(E, grid, cumulative, left=0.0, right=float(cumulative[-1]))
    targets = rng.random(E.size) * y
    e_react = np.interp(targets, cumulative, grid, left=float(grid[0]), right=float(grid[-1]))
    e_react = np.minimum(e_react, E)
    e_n, dir_n = _dd_neutron_lab_vectorized(e_react, direction, rng)
    w_n = weight * y

    from interfaces.schema import write_neutron_source

    write_neutron_source(
        high_n,
        e_n,
        dir_n,
        w_n,
        t,
        attrs={
            "source_model": "semi_analytic_ddn_external_thick_cd2_converter_fast_table_high_Ed_component",
            "input": str(spec.deuteron_h5),
            "seed": seed,
            "E_D_component_cut_MeV": CUTOFF_MEV,
            "component": "incident deuterons with E_D > 9.8 MeV",
            "n_input_high_original": int(E0.size),
            "sample_repeats": int(repeats),
            "n_component_samples": int(E.size),
            "rho_cd2_g_cm3": 1.06,
            "stopping_table": str(ROOT / "data/stopping_D_in_CD2.csv"),
            "table_grid": 12000,
            "yield_table_E_max_MeV": float(grid[-1]),
        },
    )
    return high_n


def run_case_b_openmc(source_id: str, neutron_h5: Path, threads: int, force: bool, tag: str) -> Path:
    run_dir = OUT_ROOT / "openmc_runs" / f"caseB_{source_id}_{tag}_li6_7p59"
    model = build_model(
        "B",
        LI6_NATURAL,
        str(ROOT / "config.yaml"),
        neutron_h5=str(neutron_h5),
        production=False,
        batches=100,
        particles=1_000_000,
    )
    return run_model_if_needed(model, run_dir, threads=threads, force=force)


def run_truncated_openmc(spec: CaseSpec, neutron_h5: Path, threads: int, force: bool) -> Path:
    return run_case_b_openmc(spec.source_id, neutron_h5, threads, force, tag="Ed_le_9p8MeV")


def source_stats(deuteron_h5: Path, neutron_h5: Path) -> dict[str, float]:
    beam = read_deuteron_beam(deuteron_h5)
    src = read_neutron_source(neutron_h5)
    total_w = float(np.sum(beam.weight))
    high = beam.E > CUTOFF_MEV
    return {
        "D_macro_count": float(beam.E.size),
        "D_E_max_MeV": float(np.max(beam.E)) if beam.E.size else float("nan"),
        "D_weight_total": total_w,
        "D_weight_above_9p8": float(np.sum(beam.weight[high])),
        "D_weight_frac_above_9p8": float(np.sum(beam.weight[high]) / total_w) if total_w > 0 else float("nan"),
        "neutron_Y_total": float(np.sum(src.weight)),
        "neutron_E_mean_MeV": float(np.average(src.E, weights=src.weight)) if np.sum(src.weight) > 0 else float("nan"),
        "neutron_E_max_MeV": float(np.max(src.E)) if src.E.size else float("nan"),
        "neutron_frac_E_gt_4MeV": float(np.sum(src.weight[src.E > 4.0]) / np.sum(src.weight)) if np.sum(src.weight) > 0 else float("nan"),
    }


def prepare_kT4_highstat(seed: int, n: int = 1_000_000) -> CaseSpec:
    """Build a higher-statistics paired kT4 source for cutoff differencing.

    The archived kT4 source has only 50k macroparticles. That is enough for the
    smooth C1 trend, but tail-difference estimates are too sensitive to the
    single sampled D(d,n) reaction energy per incident deuteron. This local
    paired source keeps the same distribution and uses 1M macroparticles.
    """
    source_id = "param_kT4_theta20_Emax40_highstat"
    outdir = OUT_ROOT / source_id
    outdir.mkdir(parents=True, exist_ok=True)
    deuteron_h5 = outdir / "deuteron_beam.h5"
    neutron_h5 = outdir / "neutron_source_pstar.h5"
    if not deuteron_h5.exists():
        E, direction, weight, t = generate_parametric_beam(
            n=n,
            total_deuterons=1.0e12,
            kT_MeV=4.0,
            theta_max_deg=20.0,
            E_min_MeV=0.1,
            E_max_MeV=40.0,
            seed=seed,
        )
        write_deuteron_beam(
            deuteron_h5,
            E,
            direction,
            weight,
            t,
            attrs={
                "source_type": "parametric_tnsa_c1_scan_highstat_cutoff_sensitivity",
                "kT_MeV": 4.0,
                "theta_max_deg": 20.0,
                "E_min_MeV": 0.1,
                "E_max_MeV": 40.0,
                "n_deuterons_total": 1.0e12,
                "seed": seed,
            },
        )
    if not neutron_h5.exists():
        build_neutron_source_fast(
            deuteron_h5,
            neutron_h5,
            seed=seed,
            stopping_table=ROOT / "data/stopping_D_in_CD2.csv",
            table_grid=12000,
        )
    full_sp = OUT_ROOT / "openmc_runs" / f"caseB_{source_id}_full_li6_7p59" / "statepoint.100.h5"
    return CaseSpec(
        source_id=source_id,
        family="parametric_highstat",
        deuteron_h5=deuteron_h5,
        full_neutron_h5=neutron_h5,
        full_case_b_statepoint=full_sp,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threads", type=int, default=12)
    parser.add_argument("--force-openmc", action="store_true")
    args = parser.parse_args()

    configure_env()
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    rows = []
    specs = list(CASES)
    kT4_spec = prepare_kT4_highstat(seed=20261209, n=1_000_000)
    run_case_b_openmc(kT4_spec.source_id, kT4_spec.full_neutron_h5, args.threads, args.force_openmc, tag="full")
    specs.append(kT4_spec)

    for i, spec in enumerate(specs):
        full_stats = source_stats(spec.deuteron_h5, spec.full_neutron_h5)
        high_n = build_high_deuteron_component_source(spec, seed=20260707 + 1200 + i)
        high_src = read_neutron_source(high_n)
        high_Y = float(np.sum(high_src.weight))
        high_sp = run_case_b_openmc(spec.source_id, high_n, args.threads, args.force_openmc, tag="Ed_gt_9p8MeV_component")

        full_li7, full_li7_std, full_li7_rel = tally_sum(spec.full_case_b_statepoint, "TPR_Li7")
        high_li7, high_li7_std, high_li7_rel = tally_sum(high_sp, "TPR_Li7")
        full_li7_abs = full_stats["neutron_Y_total"] * full_li7
        high_li7_abs = high_Y * high_li7

        rows.append(
            {
                "source_id": spec.source_id,
                "family": spec.family,
                "cutoff_MeV": CUTOFF_MEV,
                **{f"full_{k}": v for k, v in full_stats.items()},
                "high_component_neutron_Y_total": high_Y,
                "high_component_neutron_E_mean_MeV": float(np.average(high_src.E, weights=high_src.weight)) if high_Y > 0 else float("nan"),
                "high_component_neutron_E_max_MeV": float(np.max(high_src.E)) if high_src.E.size else float("nan"),
                "high_component_neutron_frac_E_gt_4MeV": float(np.sum(high_src.weight[high_src.E > 4.0]) / high_Y) if high_Y > 0 else float("nan"),
                "neutron_loss_per_shot": high_Y,
                "neutron_loss_fraction": high_Y / full_stats["neutron_Y_total"] if full_stats["neutron_Y_total"] else float("nan"),
                "full_Li7_TPR_per_source_neutron": full_li7,
                "full_Li7_TPR_rel_err": full_li7_rel,
                "high_component_Li7_TPR_per_source_neutron": high_li7,
                "high_component_Li7_TPR_rel_err": high_li7_rel,
                "full_Li7_T_per_shot": full_li7_abs,
                "Li7_loss_per_shot": high_li7_abs,
                "Li7_loss_fraction": high_li7_abs / full_li7_abs if full_li7_abs else float("nan"),
                "full_caseB_statepoint": str(spec.full_case_b_statepoint),
                "high_component_caseB_statepoint": str(high_sp),
                "full_neutron_h5": str(spec.full_neutron_h5),
                "high_component_neutron_h5": str(high_n),
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUT_ROOT / "cutoff_9p8MeV_loss_summary.csv", index=False)
    lines = [
        "# 9.8 MeV deuteron-cutoff sensitivity",
        "",
        "Question: if all incident deuterons above 9.8 MeV were discarded before the CD2 D(d,n) source build, how much neutron yield and natural-lithium Li7 tritium signal would be lost?",
        "",
        "The production Stage B builder does not hard-code this cut; this is a conservative sensitivity test for wording the result as a lower bound.",
        "",
        "| source | neutron loss | Li7 loss | full Li7 T/shot | high-E_D Li7 T/shot |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in df.itertuples():
        lines.append(
            f"| `{r.source_id}` | {100*r.neutron_loss_fraction:.3f}% | {100*r.Li7_loss_fraction:.3f}% | {r.full_Li7_T_per_shot:.6e} | {r.Li7_loss_per_shot:.6e} |"
        )
    lines.extend(
        [
            "",
            "Files:",
            "",
            "- `cutoff_9p8MeV_loss_summary.csv`: numeric summary.",
            "- `*/neutron_source_pstar_Ed_gt_9p8MeV_component.h5`: local high-E_D component sources, not for git.",
            "- `openmc_runs/`: local OpenMC statepoints, not for git.",
            "",
        ]
    )
    (OUT_ROOT / "README.md").write_text("\n".join(lines))
    print(f"wrote {OUT_ROOT / 'cutoff_9p8MeV_loss_summary.csv'}")
    print(f"wrote {OUT_ROOT / 'README.md'}")


if __name__ == "__main__":
    main()
