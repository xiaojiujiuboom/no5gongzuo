"""Build neutron_source.h5 from deuteron_beam.h5 using the semi-analytic model."""

from __future__ import annotations

import argparse
import warnings
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from interfaces.schema import read_deuteron_beam, write_neutron_source
from moduleB_source.kinematics import dd_neutron_lab
from moduleB_source.thick_target import sample_reaction_energy, thick_target_yield


def build_neutron_source(
    deuteron_h5: str | Path,
    output_h5: str | Path,
    seed: int = 20260701,
    max_particles: int | None = None,
) -> None:
    beam = read_deuteron_beam(deuteron_h5)
    E = beam.E
    direction = beam.dir
    weight = beam.weight
    t = beam.t
    if max_particles is not None and E.size > max_particles:
        E = E[:max_particles]
        direction = direction[:max_particles]
        weight = weight[:max_particles]
        t = t[:max_particles]

    rng = np.random.default_rng(seed)
    n = E.size
    E_n = np.empty(n, dtype=float)
    dir_n = np.empty((n, 3), dtype=float)
    w_n = np.empty(n, dtype=float)

    with warnings.catch_warnings():
        warnings.simplefilter("once", RuntimeWarning)
        for i in range(n):
            y = thick_target_yield(float(E[i]))
            E_react = sample_reaction_energy(float(E[i]), rng)
            E_lab, d_lab = dd_neutron_lab(E_react, direction[i], rng=rng)
            E_n[i] = E_lab
            dir_n[i] = d_lab
            w_n[i] = weight[i] * y

    write_neutron_source(
        output_h5,
        E_n,
        dir_n,
        w_n,
        t,
        attrs={
            "source_model": "semi_analytic_ddn_placeholder_stopping",
            "input": str(deuteron_h5),
            "seed": seed,
            "n_input_used": int(n),
        },
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("deuteron_h5")
    parser.add_argument("-o", "--output", default="neutron_source.h5")
    parser.add_argument("--seed", type=int, default=20260701)
    parser.add_argument("--max-particles", type=int, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    build_neutron_source(args.deuteron_h5, args.output, args.seed, args.max_particles)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
