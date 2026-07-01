"""OpenMC import helper."""

from __future__ import annotations


def require_openmc():
    try:
        import openmc  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "OpenMC is not installed in this Python environment. Install OpenMC before running Stage C."
        ) from exc
    return openmc

