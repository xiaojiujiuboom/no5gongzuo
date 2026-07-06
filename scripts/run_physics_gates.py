"""Generate Stage B physics-gate artifacts for cross sections and stopping.

G1 compares the D(d,n)3He cross section used by Stage B with an independent
Bosch-Hale implementation over the energy range sampled by the thick-target
integral.

G2 replaces the old placeholder stopping table with a documented NIST PSTAR
same-velocity proxy for D in CD2, then compares old vs new neutron spectra.
This is an entity table from an official source, but it is not a SRIM export.
If a SRIM output table is later supplied, this script is the place to add it.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from io import StringIO
from pathlib import Path
import re
import shutil
import sys
import urllib.parse
import urllib.request

import h5py
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA_DIR = ROOT / "data"
RESULT_DIR = ROOT / "hpc" / "results" / "physics_gates_20260706"
OUTPUT_DIR = ROOT / "outputs" / "physics_gates_20260706"

PSTAR_URL = "https://physics.nist.gov/cgi-bin/Star/ap_table-t.pl"
PSTAR_DOC_URL = "https://physics.nist.gov/PhysRefData/Star/Text/PSTAR.html"
PSTAR_MATNO_POLYETHYLENE = "221"
RHO_CD2_G_CM3 = 1.06
ACCESS_DATE = "2026-07-06"

BH_E_MIN_KEV = 0.5
BH_E_MAX_KEV = 4900.0
BH_BG = 31.3970
BH_A = (5.3701e4, 3.3027e2, -1.2706e-1, 2.9327e-5, -2.5151e-9)

DDN_POINTS_KEV = np.array([25.0, 100.0, 250.0, 500.0, 1000.0, 2500.0, 4500.0])
E_D_TABLE_MEV = np.array(
    [
        0.002,
        0.005,
        0.010,
        0.020,
        0.050,
        0.100,
        0.200,
        0.500,
        1.000,
        2.000,
        3.000,
        5.000,
        7.500,
        10.000,
        15.000,
        20.000,
        30.000,
    ]
)

SOURCE_IDS = [
    "pic2d_a0_10_t_1um",
    "pic2d_a0_10_t_2um",
    "pic2d_a0_05_t_3um",
    "pic2d_a0_10_t_3um",
    "pic2d_a0_15_t_3um",
    "pic2d_a0_20_t_3um",
    "pic2d_a0_10_t_4um",
]


def bosch_hale_reference_mb(E_cm_keV: np.ndarray | float) -> np.ndarray:
    """Independent Bosch-Hale D(d,n)3He cross-section implementation."""
    E = np.asarray(E_cm_keV, dtype=float)
    sigma = np.zeros_like(E, dtype=float)
    mask = (E >= BH_E_MIN_KEV) & (E <= BH_E_MAX_KEV)
    Em = E[mask]
    a1, a2, a3, a4, a5 = BH_A
    S = a1 + Em * (a2 + Em * (a3 + Em * (a4 + Em * a5)))
    sigma[mask] = np.maximum(S / (Em * np.exp(BH_BG / np.sqrt(Em))), 0.0)
    return sigma


def write_cross_section_check() -> None:
    from moduleB_source.cross_section import sigma_ddn_bosch_hale_mb

    used = sigma_ddn_bosch_hale_mb(DDN_POINTS_KEV)
    ref = bosch_hale_reference_mb(DDN_POINTS_KEV)
    df = pd.DataFrame(
        {
            "E_cm_keV": DDN_POINTS_KEV,
            "sigma_used_mb": used,
            "sigma_ref_mb": ref,
            "ratio_used_over_ref": used / ref,
            "used_source": "moduleB_source.cross_section.sigma_ddn_bosch_hale_mb",
            "ref_source": "independent Bosch-Hale analytic implementation; Bosch & Hale, Nucl. Fusion 32 (1992), doi:10.1088/0029-5515/32/4/I07",
            "formula_note": "sigma_mb=S(E)/(E*exp(BG/sqrt(E))); S(E)=A1+E*(A2+E*(A3+E*(A4+E*A5))); E in keV",
            "acceptance": "pass_if_ratio_within_0.85_1.15",
        }
    )
    df.to_csv(RESULT_DIR / "ddn_cross_section_check.csv", index=False)


def fetch_pstar_polyethylene(E_p_MeV: np.ndarray) -> pd.DataFrame:
    payload = urllib.parse.urlencode(
        {
            "prog": "PSTAR",
            "matno": PSTAR_MATNO_POLYETHYLENE,
            "Energies": "\n".join(f"{x:.8g}" for x in E_p_MeV),
        }
    ).encode()
    req = urllib.request.Request(
        PSTAR_URL,
        data=payload,
        headers={
            "User-Agent": "Mozilla/5.0 no5-physics-gates/1.0 (+https://github.com/xiaojiujiuboom/no5gongzuo)",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        html = response.read().decode("utf-8", errors="replace")
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = unescape(re.sub(r"<[^>]+>", " ", html))
    rows: list[list[float]] = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) == 7:
            try:
                rows.append([float(x) for x in parts])
            except ValueError:
                pass
    if not rows:
        raise RuntimeError("NIST PSTAR response did not contain numeric stopping rows")
    return pd.DataFrame(
        rows,
        columns=[
            "E_p_MeV",
            "STOP_e_MeV_cm2_g",
            "STOP_n_MeV_cm2_g",
            "STOP_t_MeV_cm2_g",
            "RANGE_c_g_cm2",
            "RANGE_p_g_cm2",
            "DETOUR",
        ],
    )


def write_stopping_table() -> tuple[Path, Path]:
    current = DATA_DIR / "stopping_D_in_CD2.csv"
    backup = DATA_DIR / "stopping_D_in_CD2_placeholder_20260706.csv"
    if current.exists() and not backup.exists():
        shutil.copy2(current, backup)

    E_p = E_D_TABLE_MEV / 2.0
    pstar = fetch_pstar_polyethylene(E_p)
    if len(pstar) != len(E_p):
        raise RuntimeError(f"NIST PSTAR returned {len(pstar)} rows for {len(E_p)} requested energies")
    if not np.allclose(pstar["E_p_MeV"].to_numpy(float), E_p, rtol=1.0e-8, atol=1.0e-10):
        raise RuntimeError("NIST PSTAR returned proton energies in an unexpected order")
    out = pd.DataFrame(
        {
            "E_MeV": E_D_TABLE_MEV,
            "S_MeV_cm": pstar["STOP_t_MeV_cm2_g"].to_numpy() * RHO_CD2_G_CM3,
            "E_p_same_velocity_MeV": pstar["E_p_MeV"].to_numpy(),
            "PSTAR_STOP_t_MeV_cm2_g": pstar["STOP_t_MeV_cm2_g"].to_numpy(),
        }
    )
    header = "\n".join(
        [
            "# D-in-CD2 stopping table for Stage B.",
            f"# Source: NIST PSTAR proton stopping in polyethylene, material 221, accessed {ACCESS_DATE}.",
            f"# Source URL: {PSTAR_DOC_URL}",
            "# Method: same-velocity proxy for deuterons, E_p = E_D / 2 in the nonrelativistic MeV range.",
            "# Linear stopping: S_D(E_D) = PSTAR_STOP_t(E_p=E_D/2) * rho_CD2.",
            f"# rho_CD2_g_cm3 = {RHO_CD2_G_CM3}.",
            "# Units: E_MeV is deuteron kinetic energy; S_MeV_cm is linear stopping power.",
            "# NOTE: This is a documented PSTAR-derived entity table, not a SRIM export.",
            "# Exact SRIM G2 closure still requires a SRIM D-in-CD2 output table.",
        ]
    )
    with current.open("w", encoding="utf-8") as f:
        f.write(header + "\n")
        out[["E_MeV", "S_MeV_cm"]].to_csv(f, index=False, float_format="%.9g")
    pstar.to_csv(RESULT_DIR / "nist_pstar_polyethylene_raw.csv", index=False)
    out.to_csv(RESULT_DIR / "stopping_D_in_CD2_pstar_same_velocity.csv", index=False)
    return current, backup


@dataclass
class StoppingTable:
    E: np.ndarray
    S: np.ndarray

    @classmethod
    def read(cls, path: Path) -> "StoppingTable":
        with path.open("r", encoding="utf-8") as f:
            payload = "".join(line for line in f if not line.lstrip().startswith("#"))
        df = pd.read_csv(StringIO(payload))
        return cls(df["E_MeV"].to_numpy(float), df["S_MeV_cm"].to_numpy(float))

    def __call__(self, E: np.ndarray) -> np.ndarray:
        clipped = np.clip(np.asarray(E, dtype=float), self.E[0], self.E[-1])
        return np.exp(np.interp(np.log(clipped), np.log(self.E), np.log(self.S)))


def write_stopping_comparison(new_table: Path, old_table: Path) -> None:
    old = StoppingTable.read(old_table)
    new = StoppingTable.read(new_table)
    E = E_D_TABLE_MEV
    old_s = old(E)
    new_s = new(E)
    pd.DataFrame(
        {
            "E_D_MeV": E,
            "S_placeholder_MeV_cm": old_s,
            "S_pstar_same_velocity_MeV_cm": new_s,
            "ratio_pstar_over_placeholder": new_s / old_s,
        }
    ).to_csv(RESULT_DIR / "stopping_placeholder_vs_pstar.csv", index=False)


def read_source_h5(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with h5py.File(path, "r") as h5:
        return h5["E"][:], h5["dir"][:], h5["weight"][:]


def weighted_quantile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    order = np.argsort(values)
    v = values[order]
    w = weights[order]
    c = np.cumsum(w)
    if c[-1] <= 0:
        return float("nan")
    return float(np.interp(q * c[-1], c, v))


def summarize_neutron_source(path: Path, bins: np.ndarray) -> dict[str, float | np.ndarray]:
    E, direction, weight = read_source_h5(path)
    total = float(weight.sum())
    hist, _ = np.histogram(E, bins=bins, weights=weight)
    norm = hist / total if total > 0 else hist
    return {
        "Y_total": total,
        "E_mean": float(np.average(E, weights=weight)) if total > 0 else float("nan"),
        "E_p50": weighted_quantile(E, weight, 0.50),
        "E_p90": weighted_quantile(E, weight, 0.90),
        "E_p99": weighted_quantile(E, weight, 0.99),
        "E_max": float(E.max()) if E.size else float("nan"),
        "frac_E_gt_3p1454": float(weight[E > 3.1454].sum() / total) if total > 0 else float("nan"),
        "frac_mu_gt_0p8": float(weight[direction[:, 2] > 0.8].sum() / total) if total > 0 else float("nan"),
        "hist_norm": norm,
    }


def write_domain_summary() -> None:
    rows = []
    for source_id in SOURCE_IDS:
        beam_path = ROOT / "outputs" / "full_chain_20260706" / source_id / "deuteron_beam.h5"
        E, _, weight = read_source_h5(beam_path)
        total = weight.sum()
        outside = E > (2.0 * BH_E_MAX_KEV / 1000.0)
        rows.append(
            {
                "source_id": source_id,
                "D_E_max_MeV": float(E.max()) if E.size else float("nan"),
                "E_cm_max_keV": float(E.max() * 500.0) if E.size else float("nan"),
                "BH_nonzero_E_cm_max_keV": BH_E_MAX_KEV,
                "D_weight_frac_above_BH_domain": float(weight[outside].sum() / total) if total > 0 else float("nan"),
                "D_macro_frac_above_BH_domain": float(outside.mean()) if E.size else float("nan"),
            }
        )
    pd.DataFrame(rows).to_csv(RESULT_DIR / "ddn_cross_section_domain_summary.csv", index=False)


def write_spectrum_comparison(old_table: Path, new_table: Path) -> None:
    from moduleB_source.build_source_fast import build_neutron_source_fast

    bins = np.linspace(0.0, 12.0, 121)
    rows = []
    hist_rows = []
    for source_id in SOURCE_IDS:
        beam = ROOT / "outputs" / "full_chain_20260706" / source_id / "deuteron_beam.h5"
        source_dir = OUTPUT_DIR / source_id
        source_dir.mkdir(parents=True, exist_ok=True)
        old_h5 = source_dir / "neutron_source_placeholder.h5"
        new_h5 = source_dir / "neutron_source_pstar.h5"
        build_neutron_source_fast(beam, old_h5, seed=20260706, stopping_table=old_table, table_grid=12000)
        build_neutron_source_fast(beam, new_h5, seed=20260706, stopping_table=new_table, table_grid=12000)
        old = summarize_neutron_source(old_h5, bins)
        new = summarize_neutron_source(new_h5, bins)
        tv = 0.5 * np.abs(new["hist_norm"] - old["hist_norm"]).sum()
        rows.append(
            {
                "source_id": source_id,
                "Y_placeholder": old["Y_total"],
                "Y_pstar": new["Y_total"],
                "Y_ratio_pstar_over_placeholder": new["Y_total"] / old["Y_total"],
                "E_mean_placeholder_MeV": old["E_mean"],
                "E_mean_pstar_MeV": new["E_mean"],
                "E_mean_shift_MeV": new["E_mean"] - old["E_mean"],
                "E_p90_placeholder_MeV": old["E_p90"],
                "E_p90_pstar_MeV": new["E_p90"],
                "frac_E_gt_3p1454_placeholder": old["frac_E_gt_3p1454"],
                "frac_E_gt_3p1454_pstar": new["frac_E_gt_3p1454"],
                "frac_E_gt_3p1454_delta": new["frac_E_gt_3p1454"] - old["frac_E_gt_3p1454"],
                "normalized_spectrum_total_variation": tv,
            }
        )
        for i in range(len(bins) - 1):
            hist_rows.append(
                {
                    "source_id": source_id,
                    "E_low_MeV": bins[i],
                    "E_high_MeV": bins[i + 1],
                    "placeholder_norm": old["hist_norm"][i],
                    "pstar_norm": new["hist_norm"][i],
                }
            )
    pd.DataFrame(rows).to_csv(RESULT_DIR / "stopping_spectrum_comparison.csv", index=False)
    pd.DataFrame(hist_rows).to_csv(RESULT_DIR / "stopping_spectrum_histograms.csv", index=False)
    make_spectrum_plot(pd.DataFrame(hist_rows))


def make_spectrum_plot(hist: pd.DataFrame) -> None:
    anchors = ["pic2d_a0_10_t_3um", "pic2d_a0_20_t_3um"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), constrained_layout=True)
    for ax, source_id in zip(axes, anchors):
        sub = hist[hist["source_id"] == source_id].copy()
        centers = 0.5 * (sub["E_low_MeV"].to_numpy() + sub["E_high_MeV"].to_numpy())
        ax.step(centers, sub["placeholder_norm"], where="mid", label="old placeholder")
        ax.step(centers, sub["pstar_norm"], where="mid", label="NIST PSTAR-derived")
        ax.axvline(3.1454, color="tab:red", ls="--", lw=1.0, label="Li7 threshold" if ax is axes[0] else None)
        ax.set_yscale("log")
        ax.set_ylim(1.0e-7, 1.0)
        ax.set_xlabel("neutron energy MeV")
        ax.set_title(source_id)
        ax.grid(alpha=0.25)
    axes[0].set_ylabel("normalized source weight per bin")
    axes[0].legend()
    fig.suptitle("Stage B neutron spectrum: old stopping placeholder vs NIST PSTAR-derived table")
    fig.savefig(RESULT_DIR / "stopping_spectrum_anchor_overlay.png", dpi=220)
    plt.close(fig)


def write_report() -> None:
    report = RESULT_DIR / "README.md"
    xs = pd.read_csv(RESULT_DIR / "ddn_cross_section_check.csv")
    domain = pd.read_csv(RESULT_DIR / "ddn_cross_section_domain_summary.csv")
    spectrum = pd.read_csv(RESULT_DIR / "stopping_spectrum_comparison.csv")
    report.write_text(
        "\n".join(
            [
                "# Physics Gates G1/G2, 2026-07-06",
                "",
                "Generated by `python3 scripts/run_physics_gates.py`.",
                "",
                "## G1 cross section",
                "",
                "- File: `ddn_cross_section_check.csv`.",
                "- Stage B used cross section is compared against an independent Bosch-Hale D(d,n)3He implementation.",
                "- Acceptance target: ratio within 0.85-1.15 at sampled E_cm points.",
                "- Domain warning file: `ddn_cross_section_domain_summary.csv` quantifies deuteron weight above the Bosch-Hale nonzero domain.",
                f"- Result: ratio range = {xs['ratio_used_over_ref'].min():.3f}-{xs['ratio_used_over_ref'].max():.3f}.",
                f"- Domain result: maximum above-domain D weight fraction = {domain['D_weight_frac_above_BH_domain'].max():.3e}.",
                "",
                "## G2 stopping",
                "",
                "- Default table replaced: `data/stopping_D_in_CD2.csv`.",
                "- Old placeholder backed up: `data/stopping_D_in_CD2_placeholder_20260706.csv`.",
                "- Entity table source: NIST PSTAR proton stopping in polyethylene, same-velocity deuteron proxy, density-scaled to CD2.",
                "- Important: this is not an SRIM export. Exact SRIM closure remains pending unless a SRIM D-in-CD2 table is supplied.",
                "- Comparison files: `stopping_placeholder_vs_pstar.csv`, `stopping_spectrum_comparison.csv`, and `stopping_spectrum_anchor_overlay.png`.",
                f"- Result: `Y_pstar/Y_placeholder = {spectrum['Y_ratio_pstar_over_placeholder'].min():.3f}-{spectrum['Y_ratio_pstar_over_placeholder'].max():.3f}`.",
                f"- Result: normalized spectrum total variation = {spectrum['normalized_spectrum_total_variation'].min():.3f}-{spectrum['normalized_spectrum_total_variation'].max():.3f}.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_cross_section_check()
    new_table, old_table = write_stopping_table()
    write_stopping_comparison(new_table, old_table)
    write_domain_summary()
    write_spectrum_comparison(old_table, new_table)
    write_report()
    print(f"wrote {RESULT_DIR}")
    print(f"updated {new_table}")
    print(f"backup {old_table}")


if __name__ == "__main__":
    main()
