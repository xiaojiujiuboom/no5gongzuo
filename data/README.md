# Data Tables

`stopping_D_in_CD2.csv` is the currently implemented stopping-power table used
by Stage B software bring-up. The intended CD2 workflow is:

```text
PSTAR proton stopping in polyethylene or SRIM D-in-CD2
-> same-velocity conversion for deuterons if using PSTAR: S_D(E_D) ~= S_p(E_D / 2)
-> convert mass stopping power to MeV/cm with the selected CD2 density
```

The current committed CSV is a provisional PSTAR-style seed table for software and sensitivity work. Before final paper numbers, replace it with a directly exported SRIM/PSTAR table and record the source, density, and conversion in this directory.

For the adopted TiD2 baseline, add a separate `stopping_D_in_TiD2.csv` from
SRIM or an equivalent documented source. Do not reuse the CD2 table under a new
name; TiD2 has different stopping and a different deuteron density.

Also note that the current Bosch-Hale D(d,n)3He fit is only evaluated in its nominal 0.5-4900 keV center-of-mass range. Values outside that interval are set to zero in code until a verified evaluated-data treatment is added. The `D(d,p)T` branch still needs a verified cross-section implementation before direct triton yields can be used for final numbers.
