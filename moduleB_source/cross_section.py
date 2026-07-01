"""Bosch-Hale D(d,n)3He cross section parameterization."""

from __future__ import annotations

import numpy as np

BG = 31.3970
A1 = 5.3701e4
A2 = 3.3027e2
A3 = -1.2706e-1
A4 = 2.9327e-5
A5 = -2.5151e-9
MB_TO_CM2 = 1.0e-27


def sigma_ddn_bosch_hale_mb(E_cm_keV: np.ndarray | float) -> np.ndarray:
    """Return D(d,n)3He cross section in mb for E_cm in keV.

    Validity follows the Bosch-Hale fit range approximately 0.5-4900 keV.
    Values below or equal to zero are returned as zero.
    """
    E = np.asarray(E_cm_keV, dtype=float)
    sigma = np.zeros_like(E, dtype=float)
    mask = E > 0.0
    Em = E[mask]
    S = A1 + Em * (A2 + Em * (A3 + Em * (A4 + Em * A5)))
    sigma[mask] = S / (Em * np.exp(BG / np.sqrt(Em)))
    return sigma


def sigma_ddn_cm2(E_cm_keV: np.ndarray | float) -> np.ndarray:
    return sigma_ddn_bosch_hale_mb(E_cm_keV) * MB_TO_CM2

