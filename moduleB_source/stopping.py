"""Stopping power table for deuterons in CD2."""

from __future__ import annotations

from pathlib import Path
from io import StringIO

import numpy as np


DEFAULT_STOPPING_TABLE = Path(__file__).resolve().parents[1] / "data" / "stopping_D_in_CD2.csv"


class StoppingTable:
    def __init__(self, path: str | Path = DEFAULT_STOPPING_TABLE):
        self.path = Path(path).expanduser().resolve()
        with self.path.open("r", encoding="utf-8") as f:
            payload = "".join(line for line in f if not line.lstrip().startswith("#"))
        data = np.genfromtxt(StringIO(payload), delimiter=",", names=True)
        self.E_MeV = np.asarray(data["E_MeV"], dtype=float)
        self.S_MeV_cm = np.asarray(data["S_MeV_cm"], dtype=float)
        self._validate()

    def _validate(self) -> None:
        if self.E_MeV.ndim != 1 or self.E_MeV.size < 2:
            raise ValueError(f"{self.path} must contain at least two rows")
        if np.any(~np.isfinite(self.E_MeV)) or np.any(~np.isfinite(self.S_MeV_cm)):
            raise ValueError(f"{self.path} contains non-finite values")
        if np.any(self.E_MeV <= 0) or np.any(self.S_MeV_cm <= 0):
            raise ValueError(f"{self.path} energies and stopping powers must be positive")
        if np.any(np.diff(self.E_MeV) <= 0):
            raise ValueError(f"{self.path} energies must be strictly increasing")

    def __call__(self, E_d_MeV: np.ndarray | float) -> np.ndarray:
        E = np.asarray(E_d_MeV, dtype=float)
        clipped = np.clip(E, self.E_MeV[0], self.E_MeV[-1])
        logS = np.interp(np.log(clipped), np.log(self.E_MeV), np.log(self.S_MeV_cm))
        return np.exp(logS)


_DEFAULT_TABLE: StoppingTable | None = None


def stopping_power_MeV_per_cm(
    E_d_MeV: np.ndarray | float,
    table_path: str | Path = DEFAULT_STOPPING_TABLE,
) -> np.ndarray:
    global _DEFAULT_TABLE
    path = Path(table_path).expanduser().resolve()
    if _DEFAULT_TABLE is None or _DEFAULT_TABLE.path != path:
        _DEFAULT_TABLE = StoppingTable(path)
    return _DEFAULT_TABLE(E_d_MeV)
