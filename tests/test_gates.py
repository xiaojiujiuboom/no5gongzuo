"""Minimal physics and interface gates for the bring-up pipeline."""

from __future__ import annotations

import tempfile
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from interfaces.schema import read_deuteron_beam, read_neutron_source
from moduleA_pic.parametric_beam import generate_parametric_beam
from moduleB_source.build_source import build_neutron_source
from moduleB_source.cross_section import sigma_ddn_bosch_hale_mb
from moduleB_source.kinematics import dd_neutron_lab
from moduleB_source.stopping import stopping_power_MeV_per_cm
from moduleB_source.thick_target import thick_target_yield
from interfaces.schema import write_deuteron_beam
from utils.config import load_config


def assert_close(value: float, expected: float, tol: float, name: str) -> None:
    if abs(value - expected) > tol:
        raise AssertionError(f"{name}: got {value:.6g}, expected {expected:.6g} +/- {tol}")


def gate_schema_and_pipeline(tmp: Path) -> None:
    beam_path = tmp / "deuteron_beam.h5"
    source_path = tmp / "neutron_source.h5"
    E, direction, weight, t = generate_parametric_beam(
        n=2000,
        total_deuterons=1.0e9,
        kT_MeV=2.0,
        theta_max_deg=15.0,
        E_min_MeV=0.1,
        E_max_MeV=6.0,
        seed=7,
    )
    write_deuteron_beam(beam_path, E, direction, weight, t, attrs={"source_type": "test"})
    beam = read_deuteron_beam(beam_path)
    if beam.E.size != 2000:
        raise AssertionError("beam size mismatch")
    build_neutron_source(beam_path, source_path, seed=8, max_particles=500)
    source = read_neutron_source(source_path)
    if source.E.size != 500:
        raise AssertionError("source size mismatch")
    if float(source.attrs["Y_total"]) <= 0.0:
        raise AssertionError("Y_total must be positive")
    if not np.any(source.E > 2.82):
        raise AssertionError("expected some source neutrons above the Li7 threshold")


def gate_cross_section() -> None:
    energies = np.array([10.0, 50.0, 100.0, 500.0])
    sigma = sigma_ddn_bosch_hale_mb(energies)
    if not np.all(np.isfinite(sigma)) or not np.all(sigma > 0):
        raise AssertionError("cross section must be finite and positive")
    if not sigma[2] > sigma[1] > sigma[0]:
        raise AssertionError("D-D cross section should rise from 10 to 100 keV")


def gate_stopping_and_yield() -> None:
    E = np.array([0.1, 1.0, 10.0])
    S = stopping_power_MeV_per_cm(E)
    if not np.all(np.isfinite(S)) or not np.all(S > 0):
        raise AssertionError("stopping power must be finite and positive")
    if not S[0] > S[1] > S[2]:
        raise AssertionError("expected stopping power to decrease from 0.1 to 10 MeV")
    y1 = thick_target_yield(1.0)
    y3 = thick_target_yield(3.0)
    if not (0.0 < y1 < y3):
        raise AssertionError("thick-target yield should be positive and rise with E0")


def gate_config() -> None:
    cfg = load_config()
    geom = cfg.get("physics", {}).get("geometry_lock")
    if geom != "laser_thin_foil_deuteron_source_plus_external_thick_cd2_converter":
        raise AssertionError("physics.geometry_lock is not set to the external converter geometry")
    thickness = cfg.get("hpc_pic", {}).get("first_2d_scan", {}).get("target_thickness_um")
    if thickness != [5]:
        raise AssertionError("first 2D scan should be the 6-source matrix with thickness fixed at 5 um")


def gate_kinematics() -> None:
    z = np.array([0.0, 0.0, 1.0])
    E0, _ = dd_neutron_lab(0.0, z, cm_dir_unit=z)
    Ef, _ = dd_neutron_lab(1.0, z, cm_dir_unit=z)
    Eb, _ = dd_neutron_lab(1.0, z, cm_dir_unit=-z)
    assert_close(E0, 2.449, 0.005, "E_d=0 neutron energy")
    assert_close(Ef, 4.14, 0.05, "E_d=1 MeV forward neutron energy")
    assert_close(Eb, 1.76, 0.05, "E_d=1 MeV backward neutron energy")


def main() -> None:
    gate_config()
    gate_cross_section()
    gate_stopping_and_yield()
    gate_kinematics()
    with tempfile.TemporaryDirectory() as td:
        gate_schema_and_pipeline(Path(td))
    print("PASS: config, schema, stopping table, sigma, kinematics, and Stage A->B gates")


if __name__ == "__main__":
    main()
