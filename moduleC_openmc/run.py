"""Generate and optionally run an OpenMC lithium-target case."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from moduleC_openmc._compat import require_openmc
from moduleC_openmc.geometry import make_geometry
from moduleC_openmc.materials import make_materials
from moduleC_openmc.source import make_case_a_source, make_case_b_sources
from moduleC_openmc.tallies import make_tallies
from utils.config import load_config


def build_model(
    case: str,
    li6_atpct: float,
    config_path: str,
    neutron_h5: str | None = None,
    production: bool = False,
    batches: int | None = None,
    particles: int | None = None,
):
    openmc = require_openmc()
    cfg = load_config(config_path)
    li_cfg = cfg.get("lithium", {})
    omc_cfg = cfg.get("openmc", {})
    bin_cfg = cfg.get("source_bins", {})

    radius = float(li_cfg.get("radius_cm", 10.0))
    height = float(li_cfg.get("height_cm", 20.0))
    cavity = float(li_cfg.get("cavity_radius_cm", 1.0))
    density = float(li_cfg.get("density_g_cm3", 0.534))
    materials = make_materials(li6_atpct, density)
    geometry = make_geometry(materials[0], radius, height, cavity)
    tallies = make_tallies(radius, height)

    settings = openmc.Settings()
    settings.run_mode = "fixed source"
    settings.batches = int(
        batches if batches is not None else omc_cfg.get("batches_production" if production else "batches_debug", 20)
    )
    settings.particles = int(
        particles
        if particles is not None
        else omc_cfg.get("particles_production" if production else "particles_debug", 100_000)
    )
    settings.photon_transport = False
    if case.upper() == "A":
        settings.source = make_case_a_source()
    elif case.upper() == "B":
        if neutron_h5 is None:
            raise ValueError("Case B requires --nsrc neutron_source.h5")
        settings.source = make_case_b_sources(
            neutron_h5,
            n_mu=int(bin_cfg.get("n_mu", 15)),
            n_E=int(bin_cfg.get("n_E", 100)),
        )
    else:
        raise ValueError("case must be A or B")

    return openmc.Model(geometry=geometry, materials=materials, settings=settings, tallies=tallies)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--case", choices=["A", "B"], required=True)
    parser.add_argument("--li6", type=float, default=90.0)
    parser.add_argument("--nsrc", default=None, help="neutron_source.h5 for Case B")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--production", action="store_true")
    parser.add_argument("--batches", type=int, default=None)
    parser.add_argument("--particles", type=int, default=None)
    parser.add_argument("--cross-sections", default=None, help="Path to OpenMC cross_sections.xml")
    parser.add_argument("--run", action="store_true", help="run OpenMC after exporting XML")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.cross_sections:
        os.environ["OPENMC_CROSS_SECTIONS"] = str(Path(args.cross_sections).expanduser().resolve())
    model = build_model(
        args.case,
        args.li6,
        args.config,
        args.nsrc,
        args.production,
        batches=args.batches,
        particles=args.particles,
    )
    outdir = Path(args.output_dir or f"openmc_case_{args.case}_li6_{args.li6:g}")
    outdir.mkdir(parents=True, exist_ok=True)
    model.export_to_xml(outdir)
    print(f"exported OpenMC XML to {outdir}")
    if args.run:
        model.run(cwd=outdir)


if __name__ == "__main__":
    main()
