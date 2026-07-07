"""Run C1 Part 1-3 OpenMC source-decomposition workflow.

The workflow keeps large HDF5/OpenMC products under the no6 data area and only
uses this repository for reusable code. Case B construction is intentionally
left unchanged; Case A-prime uses a separate source builder that preserves the
source energy spectrum and strips angular correlations.
"""

from __future__ import annotations

import argparse
import csv
import math
import os
from dataclasses import dataclass
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from interfaces.schema import read_neutron_source, write_deuteron_beam
from moduleA_pic.parametric_beam import generate_parametric_beam
from moduleB_source.build_source_fast import build_neutron_source_fast
from moduleC_openmc._compat import require_openmc
from moduleC_openmc.geometry import make_geometry
from moduleC_openmc.materials import make_materials
from moduleC_openmc.source import make_case_aprime_source
from moduleC_openmc.tallies import make_tallies
from moduleC_openmc.run import build_model
from utils.config import load_config


NO6_ROOT = Path("/Volumes/billboom/paperwork/no6/stageB_inputs_20260706")
PIC_ROOT = NO6_ROOT / "stageB_inputs_7points"
C0_ROOT = NO6_ROOT / "openmc_pstar_20260706"
OUT_ROOT = NO6_ROOT / "openmc_c1_20260706" / "part1_3_decomposition"
CROSS_SECTIONS = Path("/Users/oomb/Downloads/mcnp_endfb71/cross_sections.xml")
OPENMC_BIN = Path("/opt/miniconda3/envs/openmc-env/bin")
PHYS_LI7_THRESHOLD_MEV = 2.467 * 8.0 / 7.0
LIB_LI7_THRESHOLD_MEV = 3.1454

PIC_SOURCE_IDS = [
    "pic2d_a0_10_t_1um",
    "pic2d_a0_10_t_2um",
    "pic2d_a0_05_t_3um",
    "pic2d_a0_10_t_3um",
    "pic2d_a0_15_t_3um",
    "pic2d_a0_20_t_3um",
    "pic2d_a0_10_t_4um",
]
LI6_CASES = [7.59, 90.0]
PARAM_SPECTRA = [
    (0.08, 2.5),
    (0.25, 4.0),
    (0.60, 6.0),
    (1.20, 12.0),
    (1.80, 16.0),
    (4.00, 40.0),
]
PARAM_THETA = [180.0, 30.0, 20.0, 10.0]
_LI7_MT205_CACHE: tuple[np.ndarray, np.ndarray] | None = None


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    family: str
    neutron_h5: Path
    deuteron_h5: Path | None = None
    kT_MeV: float | None = None
    theta_max_deg: float | None = None
    E_max_MeV: float | None = None


def li_tag(li6: float) -> str:
    return "7p59" if abs(li6 - 7.59) < 1.0e-12 else "90p0"


def li_tag_c0(li6: float) -> str:
    return "7p59" if abs(li6 - 7.59) < 1.0e-12 else "90"


def param_id(kT: float, theta: float, emax: float) -> str:
    def fmt(v: float) -> str:
        return ("%g" % v).replace(".", "p")

    return f"param_kT{fmt(kT)}_theta{fmt(theta)}_Emax{fmt(emax)}"


def configure_openmc_env() -> None:
    os.environ["OPENMC_CROSS_SECTIONS"] = str(CROSS_SECTIONS)
    path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{OPENMC_BIN}:{path}"


def _li7_h5_path(cross_sections: Path) -> Path:
    root = ET.parse(cross_sections).getroot()
    for elem in root.findall("library"):
        materials = set((elem.attrib.get("materials") or "").split())
        if elem.attrib.get("type") == "neutron" and "Li7" in materials:
            path = Path(elem.attrib["path"])
            if not path.is_absolute():
                path = cross_sections.parent / path
            return path.resolve()
    raise ValueError(f"Li7 neutron data not listed in {cross_sections}")


def li7_mt205_xs() -> tuple[np.ndarray, np.ndarray]:
    global _LI7_MT205_CACHE
    if _LI7_MT205_CACHE is None:
        li7_h5 = _li7_h5_path(CROSS_SECTIONS)
        with h5py.File(li7_h5, "r") as h5:
            reaction = h5["Li7/reactions/reaction_205"]
            xs_node = reaction["294K/xs"]
            threshold_idx = int(xs_node.attrs["threshold_idx"])
            sigma_b = np.asarray(xs_node[:], dtype=float)
            E_eV = np.asarray(h5["Li7/energy/294K"][threshold_idx : threshold_idx + sigma_b.size], dtype=float)
        _LI7_MT205_CACHE = (E_eV / 1.0e6, sigma_b)
    return _LI7_MT205_CACHE


def li7_mt205_sigma_at(E_MeV: np.ndarray) -> np.ndarray:
    xs_E, xs_b = li7_mt205_xs()
    return np.interp(E_MeV, xs_E, xs_b, left=0.0, right=float(xs_b[-1]))


def build_aprime_model(neutron_h5: Path, li6_atpct: float, batches: int, particles: int):
    openmc = require_openmc()
    cfg = load_config(ROOT / "config.yaml")
    li_cfg = cfg.get("lithium", {})
    bin_cfg = cfg.get("source_bins", {})
    radius = float(li_cfg.get("radius_cm", 10.0))
    height = float(li_cfg.get("height_cm", 20.0))
    cavity = float(li_cfg.get("cavity_radius_cm", 1.0))
    density = float(li_cfg.get("density_g_cm3", 0.534))
    materials = make_materials(li6_atpct, density)
    geometry = make_geometry(materials[0], radius, height, cavity)
    tallies = make_tallies(radius, height)
    settings = openmc.Settings()
    settings.run_mode = "fixed source"
    settings.batches = int(batches)
    settings.particles = int(particles)
    settings.photon_transport = False
    settings.source = make_case_aprime_source(neutron_h5, n_E=int(bin_cfg.get("n_E", 100)))
    return openmc.Model(geometry=geometry, materials=materials, settings=settings, tallies=tallies)


def run_model_if_needed(model, outdir: Path, threads: int, force: bool = False) -> Path:
    sp = outdir / "statepoint.100.h5"
    if sp.exists() and not force:
        return sp
    outdir.mkdir(parents=True, exist_ok=True)
    model.export_to_xml(outdir)
    model.run(cwd=outdir, threads=threads)
    if not sp.exists():
        raise FileNotFoundError(f"OpenMC did not write {sp}")
    return sp


def prepare_parametric_sources(n_macro: int, force: bool = False) -> list[SourceSpec]:
    outdir = OUT_ROOT / "parametric_sources"
    outdir.mkdir(parents=True, exist_ok=True)
    specs: list[SourceSpec] = []
    rows: list[dict[str, object]] = []
    for i, (kT, emax) in enumerate(PARAM_SPECTRA):
        for j, theta in enumerate(PARAM_THETA):
            sid = param_id(kT, theta, emax)
            sdir = outdir / sid
            sdir.mkdir(parents=True, exist_ok=True)
            deuteron_h5 = sdir / "deuteron_beam.h5"
            neutron_h5 = sdir / "neutron_source_pstar.h5"
            seed = 20260707 + 100 * i + j
            if force or not neutron_h5.exists():
                E, direction, weight, t = generate_parametric_beam(
                    n=n_macro,
                    total_deuterons=1.0e12,
                    kT_MeV=kT,
                    theta_max_deg=theta,
                    E_min_MeV=0.1,
                    E_max_MeV=emax,
                    seed=seed,
                )
                write_deuteron_beam(
                    deuteron_h5,
                    E,
                    direction,
                    weight,
                    t,
                    attrs={
                        "source_type": "parametric_tnsa_c1_scan",
                        "kT_MeV": kT,
                        "theta_max_deg": theta,
                        "E_min_MeV": 0.1,
                        "E_max_MeV": emax,
                        "seed": seed,
                    },
                )
                build_neutron_source_fast(
                    deuteron_h5,
                    neutron_h5,
                    seed=seed,
                    stopping_table=ROOT / "data/stopping_D_in_CD2.csv",
                    table_grid=8192,
                )
            spec = SourceSpec(
                source_id=sid,
                family="parametric",
                neutron_h5=neutron_h5,
                deuteron_h5=deuteron_h5,
                kT_MeV=kT,
                theta_max_deg=theta,
                E_max_MeV=emax,
            )
            specs.append(spec)
            rows.append(source_description_row(spec))
    pd.DataFrame(rows).to_csv(outdir / "parametric_source_manifest.csv", index=False)
    return specs


def pic_sources() -> list[SourceSpec]:
    return [
        SourceSpec(
            source_id=sid,
            family="pic2d",
            neutron_h5=PIC_ROOT / sid / "neutron_source_pstar.h5",
            deuteron_h5=PIC_ROOT / sid / "deuteron_beam.h5",
        )
        for sid in PIC_SOURCE_IDS
    ]


def source_description_row(spec: SourceSpec) -> dict[str, object]:
    src = read_neutron_source(spec.neutron_h5)
    w = src.weight
    total = float(np.sum(w))
    if total <= 0.0:
        raise ValueError(f"{spec.neutron_h5} has non-positive total weight")
    forward = src.dir[:, 2] > 0.8
    sigma_li7_b = li7_mt205_sigma_at(src.E)
    return {
        "source_id": spec.source_id,
        "family": spec.family,
        "neutron_h5": str(spec.neutron_h5),
        "deuteron_h5": str(spec.deuteron_h5) if spec.deuteron_h5 else "",
        "kT_MeV": spec.kT_MeV if spec.kT_MeV is not None else "",
        "theta_max_deg": spec.theta_max_deg if spec.theta_max_deg is not None else "",
        "E_max_MeV": spec.E_max_MeV if spec.E_max_MeV is not None else "",
        "source_N": int(src.E.size),
        "source_weight_sum_shape_only": total,
        "source_E_mean_MeV": float(np.average(src.E, weights=w)),
        "source_E_max_MeV": float(np.max(src.E)),
        "frac_E_gt_2p82": float(np.sum(w[src.E > PHYS_LI7_THRESHOLD_MEV]) / total),
        "frac_E_gt_3p1454": float(np.sum(w[src.E > LIB_LI7_THRESHOLD_MEV]) / total),
        "frac_E_gt_4MeV": float(np.sum(w[src.E > 4.0]) / total),
        "li7_mt205_fluxavg_b": float(np.sum(w * sigma_li7_b) / total),
        "frac_mu_gt_0p8": float(np.sum(w[forward]) / total),
        "frac_E_gt_2p82_mu_gt_0p8": float(np.sum(w[(src.E > PHYS_LI7_THRESHOLD_MEV) & forward]) / total),
        "frac_E_gt_3p1454_mu_gt_0p8": float(np.sum(w[(src.E > LIB_LI7_THRESHOLD_MEV) & forward]) / total),
    }


def tally_sum(sp_path: Path, tally_name: str) -> tuple[float, float, float]:
    openmc = require_openmc()
    with openmc.StatePoint(sp_path) as sp:
        tally = sp.get_tally(name=tally_name)
        mean = np.asarray(tally.mean, dtype=float)
        std = np.asarray(tally.std_dev, dtype=float)
        total = float(np.sum(mean))
        total_std = float(np.sqrt(np.sum(std * std)))
        rel = total_std / abs(total) if total else float("nan")
        return total, total_std, rel


def run_openmc_cases(sources: list[SourceSpec], threads: int, force: bool = False) -> None:
    configure_openmc_env()
    run_root = OUT_ROOT / "openmc_runs"
    run_root.mkdir(parents=True, exist_ok=True)
    batches = 100
    particles = 1_000_000

    for li6 in LI6_CASES:
        odir = run_root / f"caseA_li6_{li_tag(li6)}"
        model = build_model(
            "A",
            li6,
            str(ROOT / "config.yaml"),
            production=False,
            batches=batches,
            particles=particles,
        )
        run_model_if_needed(model, odir, threads=threads, force=force)

    for spec in sources:
        for li6 in LI6_CASES:
            odir = run_root / f"caseAprime_{spec.source_id}_li6_{li_tag(li6)}"
            model = build_aprime_model(spec.neutron_h5, li6, batches=batches, particles=particles)
            print(f"RUN Aprime {spec.source_id} Li6={li6:g}", flush=True)
            run_model_if_needed(model, odir, threads=threads, force=force)

            if spec.family == "pic2d":
                # C0 already ran production Case B with the same library and settings.
                continue
            odir = run_root / f"caseB_{spec.source_id}_li6_{li_tag(li6)}"
            model = build_model(
                "B",
                li6,
                str(ROOT / "config.yaml"),
                neutron_h5=str(spec.neutron_h5),
                production=False,
                batches=batches,
                particles=particles,
            )
            print(f"RUN B {spec.source_id} Li6={li6:g}", flush=True)
            run_model_if_needed(model, odir, threads=threads, force=force)


def statepoint_for(case: str, spec: SourceSpec | None, li6: float) -> Path:
    run_root = OUT_ROOT / "openmc_runs"
    if case == "A":
        return run_root / f"caseA_li6_{li_tag(li6)}" / "statepoint.100.h5"
    if spec is None:
        raise ValueError("spec required")
    if case == "Aprime":
        return run_root / f"caseAprime_{spec.source_id}_li6_{li_tag(li6)}" / "statepoint.100.h5"
    if case == "B" and spec.family == "pic2d":
        return C0_ROOT / f"caseB_prod_{spec.source_id}_li6_{li_tag_c0(li6)}_pstar" / "statepoint.100.h5"
    if case == "B":
        return run_root / f"caseB_{spec.source_id}_li6_{li_tag(li6)}" / "statepoint.100.h5"
    raise ValueError(case)


def summarize(sources: list[SourceSpec]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    descriptions = {spec.source_id: source_description_row(spec) for spec in sources}
    for spec in sources:
        desc = descriptions[spec.source_id]
        for li6 in LI6_CASES:
            vals: dict[str, dict[str, float]] = {}
            for case in ["A", "Aprime", "B"]:
                sp = statepoint_for(case, spec if case != "A" else None, li6)
                li6_v, li6_s, li6_r = tally_sum(sp, "TPR_Li6")
                li7_v, li7_s, li7_r = tally_sum(sp, "TPR_Li7")
                total = li6_v + li7_v
                total_std = float(math.sqrt(li6_s * li6_s + li7_s * li7_s))
                vals[case] = {
                    "Li6": li6_v,
                    "Li6_std": li6_s,
                    "Li6_rel_err": li6_r,
                    "Li7": li7_v,
                    "Li7_std": li7_s,
                    "Li7_rel_err": li7_r,
                    "total": total,
                    "total_std": total_std,
                    "total_rel_err": total_std / total if total else float("nan"),
                }
            row: dict[str, object] = {
                **desc,
                "li6_atpct": li6,
                "CaseA_statepoint": str(statepoint_for("A", None, li6)),
                "CaseAprime_statepoint": str(statepoint_for("Aprime", spec, li6)),
                "CaseB_statepoint": str(statepoint_for("B", spec, li6)),
            }
            for case in ["A", "Aprime", "B"]:
                for tally in ["Li6", "Li7", "total"]:
                    row[f"{case}_TPR_{tally}_per_n"] = vals[case][tally]
                    row[f"{case}_TPR_{tally}_std"] = vals[case][f"{tally}_std"]
                    row[f"{case}_TPR_{tally}_rel_err"] = vals[case][f"{tally}_rel_err"]
            for tally in ["Li6", "Li7", "total"]:
                a = vals["A"][tally]
                ap = vals["Aprime"][tally]
                b = vals["B"][tally]
                row[f"ratio_Aprime_over_A_{tally}"] = ap / a if a else float("nan")
                row[f"ratio_B_over_Aprime_{tally}"] = b / ap if ap else float("nan")
                row[f"ratio_B_over_A_{tally}"] = b / a if a else float("nan")
                product = (ap / a) * (b / ap) if a and ap else float("nan")
                row[f"ratio_closure_product_minus_B_over_A_{tally}"] = product - (b / a) if a else float("nan")
            rows.append(row)
    df = pd.DataFrame(rows)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_ROOT / "c1_part1_3_source_decomposition_summary.csv", index=False)
    pd.DataFrame([source_description_row(spec) for spec in sources]).to_csv(
        OUT_ROOT / "c1_part1_3_source_descriptors.csv", index=False
    )
    return df


def _plot_ratio_panel(df: pd.DataFrame, xcol: str, xlabel: str, suffix: str) -> None:
    figdir = OUT_ROOT / "figures"
    figdir.mkdir(parents=True, exist_ok=True)
    for li6 in LI6_CASES:
        sel = df[df["li6_atpct"] == li6].copy()
        fig, ax = plt.subplots(figsize=(8.8, 5.2))
        for family, marker, label in [("parametric", "-", "parametric trend"), ("pic2d", "o", "PIC points")]:
            part = sel[sel["family"] == family].sort_values(xcol)
            if family == "parametric":
                ax.plot(part[xcol], part["ratio_Aprime_over_A_total"], color="tab:blue", lw=1.5, alpha=0.8, label="A'/A spectrum")
                ax.plot(part[xcol], part["ratio_B_over_Aprime_total"], color="tab:orange", lw=1.5, alpha=0.8, label="B/A' angle")
                ax.plot(part[xcol], part["ratio_B_over_A_total"], color="tab:green", lw=2.0, alpha=0.9, label="B/A total")
            else:
                ax.scatter(part[xcol], part["ratio_Aprime_over_A_total"], color="tab:blue", marker=marker, s=42, edgecolors="black", linewidths=0.4)
                ax.scatter(part[xcol], part["ratio_B_over_Aprime_total"], color="tab:orange", marker=marker, s=42, edgecolors="black", linewidths=0.4)
                ax.scatter(part[xcol], part["ratio_B_over_A_total"], color="tab:green", marker=marker, s=48, edgecolors="black", linewidths=0.5, label=label)
        ax.axhline(1.0, color="0.25", ls="--", lw=1.0)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("TPR ratio per source neutron")
        ax.set_title(f"C1 decomposition, Li6={li6:g} at%")
        ax.grid(alpha=0.22)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(figdir / f"c1_part1_3_main_ratios_{suffix}_li6_{li_tag(li6)}.png", dpi=240)
        plt.close(fig)


def plot_main(df: pd.DataFrame) -> None:
    _plot_ratio_panel(
        df,
        "frac_E_gt_2p82",
        "Weighted neutron-source fraction E > 2.819 MeV",
        "frac2p82",
    )
    _plot_ratio_panel(
        df,
        "li7_mt205_fluxavg_b",
        "Weighted source-average Li7 MT205 cross section (barn)",
        "li7_fluxavg_xs",
    )
    _plot_ratio_panel(
        df,
        "frac_E_gt_4MeV",
        "Weighted neutron-source fraction E > 4 MeV",
        "frac4MeV",
    )

    figdir = OUT_ROOT / "figures"
    figdir.mkdir(parents=True, exist_ok=True)
    for li6 in LI6_CASES:
        sel = df[df["li6_atpct"] == li6].copy()
        fig, ax = plt.subplots(figsize=(8.8, 5.2))
        for family, marker, label in [("parametric", "-", "parametric"), ("pic2d", "o", "PIC")]:
            part = sel[sel["family"] == family].sort_values("li7_mt205_fluxavg_b")
            if family == "parametric":
                ax.plot(part["li7_mt205_fluxavg_b"], part["B_TPR_Li6_per_n"], color="tab:blue", lw=1.5, label="Li6")
                ax.plot(part["li7_mt205_fluxavg_b"], part["B_TPR_Li7_per_n"], color="tab:red", lw=1.5, label="Li7")
                ax.plot(part["li7_mt205_fluxavg_b"], part["B_TPR_total_per_n"], color="tab:green", lw=2.0, label="total")
            else:
                ax.scatter(part["li7_mt205_fluxavg_b"], part["B_TPR_Li6_per_n"], color="tab:blue", marker=marker, s=42, edgecolors="black", linewidths=0.4)
                ax.scatter(part["li7_mt205_fluxavg_b"], part["B_TPR_Li7_per_n"], color="tab:red", marker=marker, s=42, edgecolors="black", linewidths=0.4)
                ax.scatter(part["li7_mt205_fluxavg_b"], part["B_TPR_total_per_n"], color="tab:green", marker=marker, s=48, edgecolors="black", linewidths=0.5, label="PIC")
        ax.set_xlabel("Weighted source-average Li7 MT205 cross section (barn)")
        ax.set_ylabel("Case B TPR per source neutron")
        ax.set_yscale("log")
        ax.set_title(f"C1 Case B Li6/Li7 TPR, Li6={li6:g} at%")
        ax.grid(alpha=0.22)
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(figdir / f"c1_part1_3_caseB_tpr_li6_{li_tag(li6)}.png", dpi=240)
        plt.close(fig)


def write_report(df: pd.DataFrame) -> None:
    pic = df[df["family"] == "pic2d"]
    param = df[df["family"] == "parametric"]
    param_desc = param.drop_duplicates("source_id")
    n_spectral = len(param_desc[["kT_MeV", "E_max_MeV"]].drop_duplicates())
    n_theta = len(param_desc["theta_max_deg"].drop_duplicates())
    closure = df[[c for c in df.columns if c.startswith("ratio_closure_product_minus")]].abs().max().max()
    lines = [
        "# C1 Part 1-3 source decomposition",
        "",
        "Scope: Case A is the ideal 2.45 MeV isotropic reference, Case A-prime uses the real source energy spectrum with isotropic angles, and Case B uses the existing energy-angle correlated source builder. All tallies are per source neutron.",
        "",
        "## Inputs",
        "",
        f"- Nuclear data: `{CROSS_SECTIONS}`",
        "- Statistics: 100 batches x 1,000,000 particles for all newly run OpenMC cases.",
        "- PIC sources: 7 pstar sources from `stageB_inputs_7points/`.",
        f"- Parametric sources: {n_spectral} spectral settings x {n_theta} theta settings.",
        "- The hardest parametric setting is included as a high-energy-tail anchor for the natural-lithium Li7 response.",
        "",
        "## Acceptance checks",
        "",
        f"- PIC `frac_E_gt_2p82` span: {pic['frac_E_gt_2p82'].min():.4f} to {pic['frac_E_gt_2p82'].max():.4f}.",
        f"- Parametric `frac_E_gt_2p82` span: {param['frac_E_gt_2p82'].min():.4f} to {param['frac_E_gt_2p82'].max():.4f}.",
        f"- PIC `li7_mt205_fluxavg_b` span: {pic['li7_mt205_fluxavg_b'].min():.4e} to {pic['li7_mt205_fluxavg_b'].max():.4e} barn.",
        f"- Parametric `li7_mt205_fluxavg_b` span: {param['li7_mt205_fluxavg_b'].min():.4e} to {param['li7_mt205_fluxavg_b'].max():.4e} barn.",
        f"- PIC `frac_E_gt_4MeV` span: {pic['frac_E_gt_4MeV'].min():.4f} to {pic['frac_E_gt_4MeV'].max():.4f}.",
        f"- Parametric `frac_E_gt_4MeV` span: {param['frac_E_gt_4MeV'].min():.4f} to {param['frac_E_gt_4MeV'].max():.4f}.",
        f"- Ratio closure max absolute residual `(A'/A)*(B/A') - B/A`: {closure:.3e}.",
        "",
        "## Files",
        "",
        "- `c1_part1_3_source_descriptors.csv`: all source descriptors.",
        "- `c1_part1_3_source_decomposition_summary.csv`: Li6/Li7/total TPR and ratios for all sources.",
        "- `figures/c1_part1_3_main_ratios_li7_fluxavg_xs_li6_*.png`: main decomposition plots vs Li7 flux-averaged MT205 cross section.",
        "- `figures/c1_part1_3_main_ratios_frac4MeV_li6_*.png`: cross-check decomposition plots vs source fraction above 4 MeV.",
        "- `figures/c1_part1_3_main_ratios_frac2p82_li6_*.png`: legacy threshold-fraction decomposition plots.",
        "- `figures/c1_part1_3_caseB_tpr_li6_*.png`: Case B channel TPR plots.",
        "- OpenMC statepoints remain local under `openmc_runs/` and should not be committed.",
        "",
    ]
    (OUT_ROOT / "README.md").write_text("\n".join(lines))


def run_all(args: argparse.Namespace) -> None:
    param = prepare_parametric_sources(args.param_n, force=args.force_sources)
    sources = pic_sources() + param
    pd.DataFrame([source_description_row(spec) for spec in sources]).to_csv(
        OUT_ROOT / "c1_part1_3_source_descriptors.csv", index=False
    )
    if args.prepare_only:
        print(f"wrote {OUT_ROOT / 'c1_part1_3_source_descriptors.csv'}")
        print("prepare-only requested; skipped OpenMC and summary")
        return
    if args.run_openmc:
        run_openmc_cases(sources, threads=args.threads, force=args.force_openmc)
    df = summarize(sources)
    plot_main(df)
    write_report(df)
    print(f"wrote {OUT_ROOT / 'c1_part1_3_source_decomposition_summary.csv'}")
    print(f"wrote {OUT_ROOT / 'README.md'}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--param-n", type=int, default=50000)
    parser.add_argument("--threads", type=int, default=12)
    parser.add_argument("--run-openmc", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--force-sources", action="store_true")
    parser.add_argument("--force-openmc", action="store_true")
    return parser


if __name__ == "__main__":
    run_all(build_parser().parse_args())
