"""Fast Stage B builder for PIC-derived deuteron probe sources.

This uses the same D(d,n) thick-target model as ``build_source.py``, but avoids
per-particle quadrature. The yield integral is tabulated once as

    F(E) = int_0^E n_D sigma_DDn(E'/2) / S(E') dE'

and each particle uses interpolation for both total yield and sampled reaction
energy. This is appropriate for the current stop-to-rest CD2 converter model.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from interfaces.schema import read_deuteron_beam, write_neutron_source
from moduleB_source.kinematics import M_D_C2_MEV, M_HE3_C2_MEV, M_N_C2_MEV, Q_DDN_MEV
from moduleB_source.thick_target import cd2_deuteron_density_cm3, yield_integrand_per_MeV
from utils.config import load_config


def _build_yield_table(
    e_max_mev: float,
    n_grid: int,
    rho_cd2_g_cm3: float,
    stopping_table: str | Path,
) -> tuple[np.ndarray, np.ndarray]:
    e_hi = max(float(e_max_mev), 1.0e-3)
    grid = np.linspace(1.0e-4, e_hi, int(n_grid), dtype=float)
    integrand = yield_integrand_per_MeV(
        grid,
        cd2_deuteron_density_cm3(rho_cd2_g_cm3),
        stopping_table,
    )
    cumulative = np.zeros_like(grid)
    cumulative[1:] = np.cumsum(0.5 * (integrand[1:] + integrand[:-1]) * np.diff(grid))
    return grid, cumulative


def _sample_unit_vectors(rng: np.random.Generator, n: int) -> np.ndarray:
    v = rng.normal(size=(n, 3))
    norm = np.linalg.norm(v, axis=1)
    bad = norm <= 0.0
    while np.any(bad):
        v[bad] = rng.normal(size=(int(np.sum(bad)), 3))
        norm = np.linalg.norm(v, axis=1)
        bad = norm <= 0.0
    return v / norm[:, None]


def _dd_neutron_lab_vectorized(
    e_react_mev: np.ndarray,
    dir_d_unit: np.ndarray,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    u_cm = _sample_unit_vectors(rng, e_react_mev.size)
    beta_cm = 0.5 * np.sqrt(np.maximum(2.0 * e_react_mev / M_D_C2_MEV, 0.0))
    e_avail = 0.5 * e_react_mev + Q_DDN_MEV
    e_n_cm = e_avail * M_HE3_C2_MEV / (M_N_C2_MEV + M_HE3_C2_MEV)
    beta_n_cm = np.sqrt(np.maximum(2.0 * e_n_cm / M_N_C2_MEV, 0.0))
    beta_lab = beta_cm[:, None] * dir_d_unit + beta_n_cm[:, None] * u_cm
    b2 = np.sum(beta_lab * beta_lab, axis=1)
    e_n_lab = 0.5 * M_N_C2_MEV * b2
    norm = np.linalg.norm(beta_lab, axis=1)
    good = norm > 0.0
    dir_n = np.zeros_like(beta_lab)
    dir_n[good] = beta_lab[good] / norm[good, None]
    if np.any(~good):
        dir_n[~good] = np.array([0.0, 0.0, 1.0])
    return e_n_lab, dir_n


def build_neutron_source_fast(
    deuteron_h5: str | Path,
    output_h5: str | Path,
    seed: int = 20260701,
    max_particles: int | None = None,
    rho_cd2_g_cm3: float = 1.06,
    stopping_table: str | Path = "data/stopping_D_in_CD2.csv",
    table_grid: int = 8192,
) -> dict[str, float]:
    beam = read_deuteron_beam(deuteron_h5)
    E = beam.E
    direction = beam.dir
    weight = beam.weight
    t = beam.t
    if max_particles is not None and E.size > max_particles:
        E = E[:max_particles]
        direction = direction[:max_particles]
        weight = weight[:max_particles]
        t = t[:max_particles]

    rng = np.random.default_rng(seed)
    grid, cumulative = _build_yield_table(float(np.max(E)) if E.size else 1.0, table_grid, rho_cd2_g_cm3, stopping_table)
    y = np.interp(E, grid, cumulative, left=0.0, right=float(cumulative[-1]))
    targets = rng.random(E.size) * y
    e_react = np.interp(targets, cumulative, grid, left=float(grid[0]), right=float(grid[-1]))
    e_react = np.minimum(e_react, E)
    e_n, dir_n = _dd_neutron_lab_vectorized(e_react, direction, rng)
    w_n = weight * y

    write_neutron_source(
        output_h5,
        e_n,
        dir_n,
        w_n,
        t,
        attrs={
            "source_model": "semi_analytic_ddn_external_thick_cd2_converter_fast_table",
            "input": str(deuteron_h5),
            "seed": seed,
            "n_input_used": int(E.size),
            "rho_cd2_g_cm3": rho_cd2_g_cm3,
            "stopping_table": str(stopping_table),
            "table_grid": int(table_grid),
            "yield_table_E_max_MeV": float(grid[-1]),
        },
    )
    total = float(np.sum(w_n))
    return {
        "N_macro": float(E.size),
        "Y_total": total,
        "E_weighted_mean_MeV": float(np.average(e_n, weights=w_n)) if total > 0 else float("nan"),
        "E_max_MeV": float(np.max(e_n)) if E.size else float("nan"),
        "source_weight_frac_E_gt_3p1454": float(np.sum(w_n[e_n > 3.1454]) / total) if total > 0 else float("nan"),
        "source_weight_frac_mu_gt_0p8": float(np.sum(w_n[dir_n[:, 2] > 0.8]) / total) if total > 0 else float("nan"),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("deuteron_h5")
    parser.add_argument("-o", "--output", default="neutron_source.h5")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--max-particles", type=int, default=None)
    parser.add_argument("--table-grid", type=int, default=8192)
    parser.add_argument("--summary", type=Path, default=None)
    return parser


def main() -> None:
    import pandas as pd

    args = build_parser().parse_args()
    cfg = load_config(args.config)
    beam_cfg = cfg.get("beam", {})
    cd2_cfg = cfg.get("target_cd2", {})
    seed = args.seed if args.seed is not None else int(beam_cfg.get("seed", 20260701))
    summary = build_neutron_source_fast(
        args.deuteron_h5,
        args.output,
        seed=seed,
        max_particles=args.max_particles,
        rho_cd2_g_cm3=float(cd2_cfg.get("rho_g_cm3", 1.06)),
        stopping_table=cd2_cfg.get("stopping_table", "data/stopping_D_in_CD2.csv"),
        table_grid=args.table_grid,
    )
    print(f"wrote {args.output}")
    for key, value in summary.items():
        print(f"{key}: {value:.8g}")
    if args.summary:
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([summary]).to_csv(args.summary, index=False)


if __name__ == "__main__":
    main()
