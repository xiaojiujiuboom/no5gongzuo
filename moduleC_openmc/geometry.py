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


def make_geometry_with_spherical_moderator(
    lithium_material,
    moderator_material,
    radius_cm: float,
    height_cm: float,
    cavity_radius_cm: float,
    moderator_thickness_cm: float,
):
    """Lithium target with an optional spherical moderator shell around the source cavity."""
    openmc = require_openmc()
    if moderator_thickness_cm <= 0.0:
        return make_geometry(lithium_material, radius_cm, height_cm, cavity_radius_cm)

    outer = openmc.ZCylinder(r=radius_cm, boundary_type="vacuum")
    zmin = openmc.ZPlane(z0=-0.5 * height_cm, boundary_type="vacuum")
    zmax = openmc.ZPlane(z0=0.5 * height_cm, boundary_type="vacuum")
    cavity = openmc.Sphere(r=cavity_radius_cm)
    moderator_outer = openmc.Sphere(r=cavity_radius_cm + moderator_thickness_cm)

    bounded = -outer & +zmin & -zmax
    li_region = bounded & +moderator_outer
    moderator_region = bounded & +cavity & -moderator_outer
    cavity_region = -cavity

    li_cell = openmc.Cell(name="lithium", fill=lithium_material, region=li_region)
    moderator_cell = openmc.Cell(name="hdpe_moderator", fill=moderator_material, region=moderator_region)
    cavity_cell = openmc.Cell(name="source_cavity", region=cavity_region)
    root = openmc.Universe(cells=[li_cell, moderator_cell, cavity_cell])
    return openmc.Geometry(root)
