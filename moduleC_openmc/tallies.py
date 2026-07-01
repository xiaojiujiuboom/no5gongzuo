"""OpenMC tritium-production tallies."""

from __future__ import annotations

import numpy as np

from moduleC_openmc._compat import require_openmc


def make_tallies(radius_cm: float, height_cm: float, mesh_r: int = 20, mesh_z: int = 20):
    openmc = require_openmc()
    tallies = openmc.Tallies()

    t_li6 = openmc.Tally(name="TPR_Li6")
    t_li6.nuclides = ["Li6"]
    t_li6.scores = ["H3-production"]
    tallies.append(t_li6)

    t_li7 = openmc.Tally(name="TPR_Li7")
    t_li7.nuclides = ["Li7"]
    t_li7.scores = ["H3-production"]
    tallies.append(t_li7)

    mesh = openmc.RegularMesh()
    mesh.dimension = [mesh_r, mesh_r, mesh_z]
    mesh.lower_left = [-radius_cm, -radius_cm, -0.5 * height_cm]
    mesh.upper_right = [radius_cm, radius_cm, 0.5 * height_cm]
    t_map = openmc.Tally(name="TPR_mesh")
    t_map.filters = [openmc.MeshFilter(mesh)]
    t_map.scores = ["H3-production"]
    tallies.append(t_map)

    efilter = openmc.EnergyFilter(np.logspace(3.0, 7.3, 60))
    t_li7_e = openmc.Tally(name="TPR_Li7_vs_E")
    t_li7_e.filters = [efilter]
    t_li7_e.nuclides = ["Li7"]
    t_li7_e.scores = ["H3-production"]
    tallies.append(t_li7_e)
    return tallies

