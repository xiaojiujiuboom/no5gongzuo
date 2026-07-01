"""External source definitions for OpenMC Case A and Case B."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from interfaces.schema import read_neutron_source
from moduleC_openmc._compat import require_openmc


def make_case_a_source(E_MeV: float = 2.45):
    openmc = require_openmc()
    return openmc.IndependentSource(
        space=openmc.stats.Point((0.0, 0.0, 0.0)),
        angle=openmc.stats.Isotropic(),
        energy=openmc.stats.Discrete([E_MeV * 1.0e6], [1.0]),
        strength=1.0,
        particle="neutron",
    )


def _histogram_tabular(openmc, E_eV: np.ndarray, weight: np.ndarray, n_bins: int):
    lo = max(1.0, float(np.min(E_eV)))
    hi = max(lo * 1.001, float(np.max(E_eV)))
    edges = np.linspace(lo, hi, n_bins + 1)
    hist, _ = np.histogram(E_eV, bins=edges, weights=weight)
    widths = np.diff(edges)
    density = hist / np.maximum(widths, 1.0e-30)
    if np.sum(density) <= 0:
        density[:] = 1.0
    p = np.append(density, 0.0)
    return openmc.stats.Tabular(edges, p, interpolation="histogram")


def make_case_b_sources(neutron_h5: str | Path, n_mu: int = 15, n_E: int = 100):
    """Build angular-bin sources that preserve E-mu correlation."""
    openmc = require_openmc()
    src = read_neutron_source(neutron_h5)
    E_eV = src.E * 1.0e6
    mu = src.dir[:, 2]
    weight = src.weight
    bins = np.linspace(-1.0, 1.0, n_mu + 1)
    sources = []
    for i in range(n_mu):
        sel = (mu >= bins[i]) & (mu < bins[i + 1])
        if i == n_mu - 1:
            sel = (mu >= bins[i]) & (mu <= bins[i + 1])
        if not np.any(sel):
            continue
        source = openmc.IndependentSource(
            space=openmc.stats.Point((0.0, 0.0, 0.0)),
            angle=openmc.stats.PolarAzimuthal(
                mu=openmc.stats.Uniform(float(bins[i]), float(bins[i + 1])),
                phi=openmc.stats.Uniform(0.0, 2.0 * np.pi),
                reference_uvw=(0.0, 0.0, 1.0),
            ),
            energy=_histogram_tabular(openmc, E_eV[sel], weight[sel], n_E),
            strength=float(np.sum(weight[sel])),
            particle="neutron",
        )
        sources.append(source)
    if not sources:
        raise ValueError(f"no nonempty source bins found in {neutron_h5}")
    return sources

