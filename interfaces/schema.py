"""HDF5 schema helpers for the deuteron beam and neutron source contracts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import h5py
import numpy as np


@dataclass(frozen=True)
class ParticleSet:
    E: np.ndarray
    dir: np.ndarray
    weight: np.ndarray
    t: np.ndarray
    attrs: dict


def _as_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def _require_1d(name: str, values: np.ndarray) -> None:
    if values.ndim != 1:
        raise ValueError(f"{name} must be 1D, got shape {values.shape}")
    if not np.all(np.isfinite(values)):
        raise ValueError(f"{name} contains non-finite values")


def _validate_common(data: ParticleSet, total_attr: str) -> None:
    E = np.asarray(data.E, dtype=float)
    direction = np.asarray(data.dir, dtype=float)
    weight = np.asarray(data.weight, dtype=float)
    t = np.asarray(data.t, dtype=float)

    _require_1d("E", E)
    _require_1d("weight", weight)
    _require_1d("t", t)
    if direction.shape != (E.size, 3):
        raise ValueError(f"dir must have shape ({E.size}, 3), got {direction.shape}")
    if weight.size != E.size or t.size != E.size:
        raise ValueError("E, weight and t must have the same length")
    if not np.all(np.isfinite(direction)):
        raise ValueError("dir contains non-finite values")
    if np.any(E < 0):
        raise ValueError("E must be non-negative")
    if np.any(weight < 0):
        raise ValueError("weight must be non-negative")

    norms = np.linalg.norm(direction, axis=1)
    if E.size and not np.allclose(norms, 1.0, rtol=1e-5, atol=1e-7):
        raise ValueError("dir rows must be unit vectors")

    expected = float(np.sum(weight))
    actual = float(data.attrs.get(total_attr, np.nan))
    if not np.isfinite(actual):
        raise ValueError(f"missing or invalid attr {total_attr}")
    scale = max(1.0, abs(expected))
    if abs(actual - expected) > 1e-6 * scale:
        raise ValueError(f"attr {total_attr}={actual} does not match sum(weight)={expected}")


def write_deuteron_beam(
    path: str | Path,
    E: np.ndarray,
    direction: np.ndarray,
    weight: np.ndarray,
    t: np.ndarray | None = None,
    attrs: Mapping[str, object] | None = None,
) -> None:
    """Write deuteron_beam.h5 with units E[MeV], dir[-], weight[deuterons/shot], t[ns]."""
    E = np.asarray(E, dtype=float)
    direction = np.asarray(direction, dtype=float)
    weight = np.asarray(weight, dtype=float)
    if t is None:
        t = np.zeros_like(E)
    t = np.asarray(t, dtype=float)

    file_attrs = dict(attrs or {})
    file_attrs["n_deuterons_total"] = float(np.sum(weight))
    data = ParticleSet(E=E, dir=direction, weight=weight, t=t, attrs=file_attrs)
    _validate_common(data, "n_deuterons_total")

    with h5py.File(_as_path(path), "w") as h5:
        h5.create_dataset("E", data=E)
        h5.create_dataset("dir", data=direction)
        h5.create_dataset("weight", data=weight)
        h5.create_dataset("t", data=t)
        for key, value in file_attrs.items():
            h5.attrs[key] = value


def write_neutron_source(
    path: str | Path,
    E: np.ndarray,
    direction: np.ndarray,
    weight: np.ndarray,
    t: np.ndarray | None = None,
    attrs: Mapping[str, object] | None = None,
) -> None:
    """Write neutron_source.h5 with units E[MeV], dir[-], weight[neutrons/shot], t[ns]."""
    E = np.asarray(E, dtype=float)
    direction = np.asarray(direction, dtype=float)
    weight = np.asarray(weight, dtype=float)
    if t is None:
        t = np.zeros_like(E)
    t = np.asarray(t, dtype=float)

    file_attrs = dict(attrs or {})
    file_attrs["Y_total"] = float(np.sum(weight))
    data = ParticleSet(E=E, dir=direction, weight=weight, t=t, attrs=file_attrs)
    _validate_common(data, "Y_total")

    with h5py.File(_as_path(path), "w") as h5:
        h5.create_dataset("E", data=E)
        h5.create_dataset("dir", data=direction)
        h5.create_dataset("weight", data=weight)
        h5.create_dataset("t", data=t)
        for key, value in file_attrs.items():
            h5.attrs[key] = value


def read_particle_set(path: str | Path, total_attr: str) -> ParticleSet:
    with h5py.File(_as_path(path), "r") as h5:
        data = ParticleSet(
            E=h5["E"][:],
            dir=h5["dir"][:],
            weight=h5["weight"][:],
            t=h5["t"][:] if "t" in h5 else np.zeros_like(h5["E"][:]),
            attrs=dict(h5.attrs.items()),
        )
    _validate_common(data, total_attr)
    return data


def read_deuteron_beam(path: str | Path) -> ParticleSet:
    return read_particle_set(path, "n_deuterons_total")


def read_neutron_source(path: str | Path) -> ParticleSet:
    return read_particle_set(path, "Y_total")


def validate_deuteron_beam(path: str | Path) -> None:
    read_deuteron_beam(path)


def validate_neutron_source(path: str | Path) -> None:
    read_neutron_source(path)

