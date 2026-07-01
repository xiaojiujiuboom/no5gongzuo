"""Two-body non-relativistic kinematics for D(d,n)3He."""

from __future__ import annotations

import numpy as np

M_D_C2_MEV = 1875.613
M_N_C2_MEV = 939.565
M_HE3_C2_MEV = 2808.391
Q_DDN_MEV = 3.269


def _unit(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, dtype=float)
    norm = np.linalg.norm(v)
    if norm <= 0:
        raise ValueError("zero vector cannot be normalized")
    return v / norm


def random_unit(rng: np.random.Generator) -> np.ndarray:
    v = rng.normal(size=3)
    return _unit(v)


def dd_neutron_lab(
    E_d_MeV: float,
    dir_d_unit: np.ndarray,
    rng: np.random.Generator | None = None,
    cm_dir_unit: np.ndarray | None = None,
) -> tuple[float, np.ndarray]:
    """Sample or evaluate neutron lab energy and direction.

    E_d_MeV is the incident deuteron lab kinetic energy. dir_d_unit is the
    deuteron lab direction. If cm_dir_unit is supplied it is used as the
    neutron direction in the CM frame; otherwise an isotropic CM direction is
    sampled.
    """
    if E_d_MeV < 0:
        raise ValueError("E_d_MeV must be non-negative")
    dir_d = _unit(dir_d_unit)
    if cm_dir_unit is None:
        if rng is None:
            rng = np.random.default_rng()
        u_cm = random_unit(rng)
    else:
        u_cm = _unit(cm_dir_unit)

    beta_cm = 0.5 * np.sqrt(2.0 * E_d_MeV / M_D_C2_MEV)
    E_avail = 0.5 * E_d_MeV + Q_DDN_MEV
    E_n_cm = E_avail * M_HE3_C2_MEV / (M_N_C2_MEV + M_HE3_C2_MEV)
    beta_n_cm = np.sqrt(2.0 * E_n_cm / M_N_C2_MEV)
    beta_lab = beta_cm * dir_d + beta_n_cm * u_cm
    b2 = float(beta_lab @ beta_lab)
    E_n_lab = 0.5 * M_N_C2_MEV * b2
    return E_n_lab, _unit(beta_lab)

