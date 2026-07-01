"""Thick-target D-D yield helpers.

The default stopping model is a placeholder for pipeline bring-up only. Replace
it with SRIM/PSTAR data before using absolute yields in a paper.
"""

from __future__ import annotations

import warnings

import numpy as np

from moduleB_source.cross_section import sigma_ddn_cm2

N_A = 6.02214e23


def cd2_deuteron_density_cm3(rho_g_cm3: float = 1.06) -> float:
    molar_mass_cd2 = 12.011 + 2.0 * 2.014
    n_unit = rho_g_cm3 * N_A / molar_mass_cd2
    return 2.0 * n_unit


def placeholder_stopping_power_MeV_per_cm(E_d_MeV: np.ndarray | float) -> np.ndarray:
    """Crude positive stopping power for smoke tests, not final physics."""
    warnings.warn(
        "using placeholder D-in-CD2 stopping power; replace with SRIM/PSTAR for results",
        RuntimeWarning,
        stacklevel=2,
    )
    E = np.asarray(E_d_MeV, dtype=float)
    return 2.5e4 * (0.2 + np.sqrt(np.maximum(E, 1.0e-6)))


def yield_integrand_per_MeV(E_d_MeV: np.ndarray, n_D_cm3: float) -> np.ndarray:
    E_cm_keV = 0.5 * E_d_MeV * 1000.0
    sigma = sigma_ddn_cm2(E_cm_keV)
    stopping = placeholder_stopping_power_MeV_per_cm(E_d_MeV)
    return n_D_cm3 * sigma / stopping


def thick_target_yield(E0_MeV: float, n_grid: int = 512, rho_cd2_g_cm3: float = 1.06) -> float:
    if E0_MeV <= 0:
        return 0.0
    grid = np.linspace(1.0e-4, E0_MeV, n_grid)
    y = yield_integrand_per_MeV(grid, cd2_deuteron_density_cm3(rho_cd2_g_cm3))
    return float(np.trapezoid(y, grid))


def sample_reaction_energy(
    E0_MeV: float,
    rng: np.random.Generator,
    n_grid: int = 512,
    rho_cd2_g_cm3: float = 1.06,
) -> float:
    if E0_MeV <= 0:
        return 0.0
    grid = np.linspace(1.0e-4, E0_MeV, n_grid)
    pdf = yield_integrand_per_MeV(grid, cd2_deuteron_density_cm3(rho_cd2_g_cm3))
    area = np.trapezoid(pdf, grid)
    if not np.isfinite(area) or area <= 0:
        return 0.0
    cdf = np.zeros_like(grid)
    cdf[1:] = np.cumsum(0.5 * (pdf[1:] + pdf[:-1]) * np.diff(grid))
    cdf /= cdf[-1]
    return float(np.interp(rng.random(), cdf, grid))

