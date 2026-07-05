"""Small nuclear-data constants used by the Stage C diagnostics."""

from __future__ import annotations

# OpenMC HDF5 Li7/reactions/reaction_205 at 294 K starts at 3.1454 MeV
# in both the local ENDF/B-VII.1-LANL and FENDL-3.2 libraries checked here.
LI7_MT205_THRESHOLD_MEV = 3.1454
LI7_MT205_SCORE = "H3-production"
LI7_MT205_LABEL = "(n,Xt)"

