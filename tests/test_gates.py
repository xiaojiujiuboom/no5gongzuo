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
from moduleB_source.build_source_fast import build_neutron_source_fast
from moduleB_source.cross_section import sigma_ddn_bosch_hale_mb
from moduleB_source.kinematics import dd_neutron_lab
from moduleB_source.stopping import stopping_power_MeV_per_cm
from moduleB_source.thick_target import thick_target_yield
from moduleC_openmc.nuclear_data import LI7_MT205_THRESHOLD_MEV
from interfaces.schema import write_deuteron_beam
from utils.config import load_config


def assert_close(value: float, expected: float, tol: float, name: str) -> None:
    if abs(value - expected) > tol:
        raise AssertionError(f"{name}: got {value:.6g}, expected {expected:.6g} +/- {tol}")


def gate_schema_and_pipeline(tmp: Path) -> None:
    beam_path = tmp / "deuteron_beam.h5"
    source_path = tmp / "neutron_source.h5"
    fast_source_path = tmp / "neutron_source_fast.h5"
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
    if not np.any(source.E > LI7_MT205_THRESHOLD_MEV):
        raise AssertionError("expected some source neutrons above the Li7 threshold")
    build_neutron_source_fast(beam_path, fast_source_path, seed=8, max_particles=500, table_grid=4096)
    fast_source = read_neutron_source(fast_source_path)
    rel_delta = abs(float(fast_source.attrs["Y_total"]) - float(source.attrs["Y_total"])) / float(source.attrs["Y_total"])
    if rel_delta > 5.0e-3:
        raise AssertionError("fast Stage B yield table disagrees with the reference builder")


def sanity_cross_section_shape() -> None:
    energies = np.array([10.0, 50.0, 100.0, 500.0])
    sigma = sigma_ddn_bosch_hale_mb(energies)
    if not np.all(np.isfinite(sigma)) or not np.all(sigma > 0):
        raise AssertionError("cross section must be finite and positive")
    if not sigma[2] > sigma[1] > sigma[0]:
        raise AssertionError("D-D cross section should rise from 10 to 100 keV")
    outside = sigma_ddn_bosch_hale_mb(np.array([0.1, 6000.0]))
    if not np.all(outside == 0.0):
        raise AssertionError("cross section should be zero outside Bosch-Hale fit range")


def sanity_stopping_and_yield_shape() -> None:
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
    if geom != "laser_thin_foil_deuteron_source_plus_external_thick_deuteride_converter":
        raise AssertionError("physics.geometry_lock is not set to the external deuteride converter geometry")
    scan = cfg.get("hpc_pic", {}).get("formal_2d_scan", {})
    if scan.get("status") != "completed_full_stageB_stageC":
        raise AssertionError("formal 2D scan should point at the completed 7-point Stage B/C matrix")
    if scan.get("job_ids") != [1937305, 1937306, 1937307, 1937308, 1937309, 1937310, 1937311]:
        raise AssertionError("formal 2D scan job IDs do not match the completed low-cost matrix")
    grid = scan.get("grid", {})
    if (grid.get("nx"), grid.get("ny"), grid.get("dx_nm"), grid.get("dy_nm")) != (2000, 500, 16, 40):
        raise AssertionError("formal 2D scan grid should be the completed 16x40 nm low-cost matrix")
    a0 = scan.get("a0_scan", {}).get("a0")
    thickness = scan.get("thickness_scan", {}).get("target_thickness_um")
    if a0 != [5, 10, 15, 20] or thickness != [1, 2, 3, 4]:
        raise AssertionError("formal 2D scan should contain the current a0 and thickness sweeps")
    full_chain = scan.get("full_chain", {})
    if full_chain.get("result_dir") != "hpc/results/full_chain_20260706":
        raise AssertionError("formal 2D full-chain result directory is not recorded")
    converter = cfg.get("target_converter", {})
    if converter.get("baseline_material") != "CD2":
        raise AssertionError("current paper baseline converter must remain CD2 unless Stage B is reimplemented")
    if converter.get("baseline_status") != "current_paper_scope_cd2_per_source_neutron_fidelity":
        raise AssertionError("converter scope should be the narrowed CD2 per-source-neutron paper scope")
    if converter.get("report_channels", {}).get("direct_triton_DdpT") != "future_work_not_in_current_scope":
        raise AssertionError("direct D(d,p)T must not be treated as current-scope output")
    if cfg.get("physics", {}).get("current_paper_scope") != "cd2_converter_per_source_neutron_li_tpr_fidelity":
        raise AssertionError("physics.current_paper_scope should lock the narrowed paper claim")


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
    sanity_cross_section_shape()
    sanity_stopping_and_yield_shape()
    gate_kinematics()
    with tempfile.TemporaryDirectory() as td:
        gate_schema_and_pipeline(Path(td))
    print("PASS: config, schema, provisional sigma/stopping sanity, kinematics, and Stage A->B interface checks")


if __name__ == "__main__":
    main()
