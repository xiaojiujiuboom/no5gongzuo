# Results Summary

1. The best one-dimensional descriptor for source hardness is the flux-averaged Li7 MT205 cross section, `<sigma_Li7>`. The PIC sources span `<sigma_Li7> = 6.55e-4` to `1.93e-2 b`; the parameterized sources span `0` to `4.33e-2 b`, so the parametric scan brackets the PIC points instead of extrapolating beyond them.

2. In natural lithium, the source spectrum strongly changes tritium production per source neutron. The baseline PIC source `pic2d_a0_10_t_3um` gives `B/A = 0.9827`, while the hard PIC source `pic2d_a0_20_t_3um` gives `B/A = 1.5406`; the hard-source total TPR is `1.724e-2 T/n`, with `7.024e-3 T/n` coming from Li7. The decomposition shows the effect is mainly spectral: for `a0_20`, `A'/A = 1.5201` and `B/A' = 1.0135`.

3. In 90 at.% Li6 enriched lithium, the response is much more robust to source hardness because Li6 dominates the tritium score. The same two PIC sources give `B/A = 1.0062` for `a0_10_t_3um` and `0.9861` for `a0_20_t_3um`; the Li7 contribution in the hard case is only `8.061e-4 T/n` out of a total `1.265e-1 T/n`.

4. A moderator can deliberately remove the hard-source dependence. For natural lithium and the hard PIC source, adding a 2 cm HDPE shell changes `B/A` from `1.5406` to `1.0161`, while total TPR rises from `1.724e-2` to `4.164e-2 T/n`; at 5 cm HDPE the same case over-moderates to `B/A = 0.9268` but total TPR increases further to `1.644e-1 T/n`.

5. The 9.8 MeV incident-deuteron cutoff is a conservative-loss issue for the real PIC hard source. For `pic2d_a0_20_t_3um`, deuterons above 9.8 MeV contribute only `3.13%` of the D(d,n) neutron yield but `32.8%` of the natural-lithium Li7 tritium signal; omitting them would therefore make the reported Li7 response a lower bound. For the synthetic `kT4` hard anchor, the high-energy component is not a stable additive "loss" diagnostic: it contributes `32.4%` of neutrons and a Li7 component equal to `168.6%` of the archived full-source Li7 signal, so it should be described as a hardness upper-bound stress test, not as a cutoff correction.
