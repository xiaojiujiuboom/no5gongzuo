"""Simple cylindrical lithium target with a central source cavity."""

from __future__ import annotations

from moduleC_openmc._compat import require_openmc


def make_geometry(lithium_material, radius_cm: float, height_cm: float, cavity_radius_cm: float):
    openmc = require_openmc()
    outer = openmc.ZCylinder(r=radius_cm, boundary_type="vacuum")
    zmin = openmc.ZPlane(z0=-0.5 * height_cm, boundary_type="vacuum")
    zmax = openmc.ZPlane(z0=0.5 * height_cm, boundary_type="vacuum")
    cavity = openmc.Sphere(r=cavity_radius_cm)

    li_region = -outer & +zmin & -zmax & +cavity
    cavity_region = -cavity

    li_cell = openmc.Cell(name="lithium", fill=lithium_material, region=li_region)
    cavity_cell = openmc.Cell(name="source_cavity", region=cavity_region)
    root = openmc.Universe(cells=[li_cell, cavity_cell])
    return openmc.Geometry(root)

