"""Small helpers for inspecting OpenMC TPR tally convergence."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from moduleC_openmc._compat import require_openmc


def summarize_statepoint(path: str | Path) -> None:
    openmc = require_openmc()
    with openmc.StatePoint(path) as sp:
        for name in ["TPR_Li6", "TPR_Li7", "TPR_Li7_vs_E", "TPR_mesh"]:
            tally = sp.get_tally(name=name)
            mean = tally.mean
            std = tally.std_dev
            rel = np.full_like(mean, np.nan, dtype=float)
            mask = mean > 0
            rel[mask] = std[mask] / mean[mask]
            finite = rel[mask]
            worst = float(finite.max()) if finite.size else float("nan")
            print(f"{name}: mean_sum={float(mean.sum()):.6e}, worst_rel_err={worst:.3g}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("statepoint")
    args = parser.parse_args()
    summarize_statepoint(args.statepoint)


if __name__ == "__main__":
    main()
