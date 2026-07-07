"""OpenMC materials for lithium target cases."""

from __future__ import annotations

from moduleC_openmc._compat import require_openmc


def make_lithium(li6_atpct: float, density_g_cm3: float = 0.534):
    openmc = require_openmc()
    li = openmc.Material(name=f"Li6_{li6_atpct:g}_atpct")
    li.add_nuclide("Li6", li6_atpct / 100.0, "ao")
    li.add_nuclide("Li7", (100.0 - li6_atpct) / 100.0, "ao")
    li.set_density("g/cm3", density_g_cm3)
    return li


def make_materials(li6_atpct: float, density_g_cm3: float = 0.534):
    openmc = require_openmc()
    lithium = make_lithium(li6_atpct, density_g_cm3)
    return openmc.Materials([lithium])


def make_hdpe(density_g_cm3: float = 0.95):
    openmc = require_openmc()
    hdpe = openmc.Material(name="HDPE")
    hdpe.add_element("H", 2.0, "ao")
    hdpe.add_element("C", 1.0, "ao")
    hdpe.set_density("g/cm3", density_g_cm3)
    return hdpe


def make_materials_with_hdpe(li6_atpct: float, li_density_g_cm3: float = 0.534, hdpe_density_g_cm3: float = 0.95):
    openmc = require_openmc()
    lithium = make_lithium(li6_atpct, li_density_g_cm3)
    hdpe = make_hdpe(hdpe_density_g_cm3)
    return openmc.Materials([lithium, hdpe])
