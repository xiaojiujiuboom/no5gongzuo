"""Convert an EPOCH deuteron NPZ extract to deuteron_beam.h5."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from interfaces.schema import write_deuteron_beam

M_D_KG = 3.3435837724e-27
C_M_S = 299792458.0
J_PER_MEV = 1.602176634e-13


def convert(npz_path: str | Path, output: str | Path, source_type: str = "epoch2d_smoke") -> None:
    data = np.load(npz_path)
    px = np.asarray(data["px_kg_m_s"], dtype=float)
    py = np.asarray(data["py_kg_m_s"], dtype=float)
    pz = np.zeros_like(px)
    p2 = px * px + py * py + pz * pz
    total_E_J = np.sqrt((M_D_KG * C_M_S * C_M_S) ** 2 + p2 * C_M_S * C_M_S)
    kinetic_MeV = (total_E_J - M_D_KG * C_M_S * C_M_S) / J_PER_MEV
    pnorm = np.sqrt(p2)
    direction = np.zeros((px.size, 3), dtype=float)
    moving = pnorm > 0
    direction[moving, 0] = px[moving] / pnorm[moving]
    direction[moving, 1] = py[moving] / pnorm[moving]
    direction[~moving, 0] = 1.0
    weight = np.asarray(data["weight"], dtype=float)
    t_ns = np.asarray(data["t_ns"], dtype=float)
    write_deuteron_beam(
        output,
        kinetic_MeV,
        direction,
        weight,
        t_ns,
        attrs={
            "source_type": source_type,
            "source_npz": str(npz_path),
            "source_sdf": str(data["source_sdf"]) if "source_sdf" in data else "",
            "note": "2D EPOCH smoke conversion; production normalization requires review",
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("npz")
    parser.add_argument("-o", "--output", default="deuteron_beam.h5")
    parser.add_argument("--source-type", default="epoch2d_smoke")
    args = parser.parse_args()
    convert(args.npz, args.output, args.source_type)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()

