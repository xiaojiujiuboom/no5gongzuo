# Data Tables

`stopping_D_in_CD2.csv` is the stopping-power table used by Stage B. The intended final workflow is:

```text
PSTAR proton stopping in polyethylene or SRIM D-in-CD2
-> same-velocity conversion for deuterons if using PSTAR: S_D(E_D) ~= S_p(E_D / 2)
-> convert mass stopping power to MeV/cm with the selected CD2 density
```

The current committed CSV is a provisional PSTAR-style seed table for software and sensitivity work. Before final paper numbers, replace it with a directly exported SRIM/PSTAR table and record the source, density, and conversion in this directory.

Also note that the current Bosch-Hale D(d,n)3He fit is only evaluated in its nominal 0.5-4900 keV center-of-mass range. Values outside that interval are set to zero in code until a verified evaluated-data treatment is added.
