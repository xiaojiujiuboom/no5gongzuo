"""Generate a parametric TNSA-like deuteron beam for pipeline bring-up."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from interfaces.schema import write_deuteron_beam
from utils.config import load_config


def sample_cone(n: int, theta_max_deg: float, rng: np.random.Generator) -> np.ndarray:
    theta_max = np.deg2rad(theta_max_deg)
    mu_min = np.cos(theta_max)
    mu = rng.uniform(mu_min, 1.0, size=n)
    phi = rng.uniform(0.0, 2.0 * np.pi, size=n)
    sin_theta = np.sqrt(np.maximum(0.0, 1.0 - mu * mu))
    return np.column_stack((sin_theta * np.cos(phi), sin_theta * np.sin(phi), mu))


def sample_truncated_exponential(
    n: int,
    kT_MeV: float,
    E_min_MeV: float,
    E_max_MeV: float,
    rng: np.random.Generator,
) -> np.ndarray:
    if not (0 <= E_min_MeV < E_max_MeV):
        raise ValueError("require 0 <= E_min_MeV < E_max_MeV")
    if kT_MeV <= 0:
        raise ValueError("kT_MeV must be positive")
    lo = np.exp(-E_min_MeV / kT_MeV)
    hi = np.exp(-E_max_MeV / kT_MeV)
    u = rng.uniform(hi, lo, size=n)
    return -kT_MeV * np.log(u)


def generate_parametric_beam(
    n: int,
    total_deuterons: float,
    kT_MeV: float,
    theta_max_deg: float,
    E_min_MeV: float,
    E_max_MeV: float,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    E = sample_truncated_exponential(n, kT_MeV, E_min_MeV, E_max_MeV, rng)
    direction = sample_cone(n, theta_max_deg, rng)
    weight = np.full(n, total_deuterons / n, dtype=float)
    t = np.zeros(n, dtype=float)
    return E, direction, weight, t


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml", help="YAML config path")
    parser.add_argument("-o", "--output", default="deuteron_beam.h5")
    parser.add_argument("--n", type=int, default=None)
    parser.add_argument("--total-deuterons", type=float, default=None)
    parser.add_argument("--kT-MeV", type=float, default=None)
    parser.add_argument("--theta-max-deg", type=float, default=None)
    parser.add_argument("--E-min-MeV", type=float, default=None)
    parser.add_argument("--E-max-MeV", type=float, default=None)
    parser.add_argument("--seed", type=int, default=None)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    cfg = load_config(args.config)
    beam_cfg = cfg.get("beam", {})
    n = args.n if args.n is not None else int(beam_cfg.get("n_macroparticles", 200_000))
    total_deuterons = (
        args.total_deuterons if args.total_deuterons is not None else float(beam_cfg.get("n_deuterons", 1.0e12))
    )
    kT_MeV = args.kT_MeV if args.kT_MeV is not None else float(beam_cfg.get("kT_MeV", 2.0))
    theta_max_deg = (
        args.theta_max_deg if args.theta_max_deg is not None else float(beam_cfg.get("theta_max_deg", 15.0))
    )
    E_min_MeV = args.E_min_MeV if args.E_min_MeV is not None else float(beam_cfg.get("E_min_MeV", 0.1))
    E_max_MeV = args.E_max_MeV if args.E_max_MeV is not None else float(beam_cfg.get("E_max_MeV", 10.0))
    seed = args.seed if args.seed is not None else int(beam_cfg.get("seed", 20260701))

    if n <= 0:
        raise SystemExit("--n must be positive")
    E, direction, weight, t = generate_parametric_beam(
        n=n,
        total_deuterons=total_deuterons,
        kT_MeV=kT_MeV,
        theta_max_deg=theta_max_deg,
        E_min_MeV=E_min_MeV,
        E_max_MeV=E_max_MeV,
        seed=seed,
    )
    write_deuteron_beam(
        Path(args.output),
        E,
        direction,
        weight,
        t,
        attrs={
            "source_type": "parametric_tnsa",
            "kT_MeV": kT_MeV,
            "theta_max_deg": theta_max_deg,
            "E_min_MeV": E_min_MeV,
            "E_max_MeV": E_max_MeV,
            "seed": seed,
        },
    )
    print(f"wrote {args.output} with {n} macroparticles")


if __name__ == "__main__":
    main()
