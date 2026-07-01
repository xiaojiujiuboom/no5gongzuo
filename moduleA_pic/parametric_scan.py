"""Generate a small grid of parametric fallback deuteron sources."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from moduleA_pic.parametric_beam import generate_parametric_beam
from interfaces.schema import write_deuteron_beam
from utils.config import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--output-dir", default="outputs/parametric_sources")
    parser.add_argument("--n", type=int, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    cfg = load_config(args.config)
    beam = cfg.get("beam", {})
    scan = beam.get("parametric_scan", {})
    kT_values = scan.get("kT_MeV", [beam.get("kT_MeV", 2.0)])
    theta_values = scan.get("theta_max_deg", [beam.get("theta_max_deg", 15.0)])
    n = args.n if args.n is not None else int(beam.get("n_macroparticles", 200_000))
    total_deuterons = float(beam.get("n_deuterons", 1.0e12))
    E_min_MeV = float(beam.get("E_min_MeV", 0.1))
    E_max_MeV = float(beam.get("E_max_MeV", 10.0))
    seed0 = int(beam.get("seed", 20260701))
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    count = 0
    for i, kT in enumerate(kT_values):
        for j, theta in enumerate(theta_values):
            seed = seed0 + 100 * i + j
            E, direction, weight, t = generate_parametric_beam(
                n=n,
                total_deuterons=total_deuterons,
                kT_MeV=float(kT),
                theta_max_deg=float(theta),
                E_min_MeV=E_min_MeV,
                E_max_MeV=E_max_MeV,
                seed=seed,
            )
            output = outdir / f"deuteron_beam_kT{kT:g}_theta{theta:g}.h5"
            write_deuteron_beam(
                output,
                E,
                direction,
                weight,
                t,
                attrs={
                    "source_type": "parametric_tnsa_scan",
                    "kT_MeV": float(kT),
                    "theta_max_deg": float(theta),
                    "E_min_MeV": E_min_MeV,
                    "E_max_MeV": E_max_MeV,
                    "seed": seed,
                },
            )
            print(output)
            count += 1
    print(f"generated {count} parametric sources in {outdir}")


if __name__ == "__main__":
    main()
