# Paper Figures And Tables

Clean final-stage artifacts for drafting the Results section. Heavy `.h5` sources,
OpenMC statepoints, and SDF files are intentionally excluded.

## Main figures

- `c1_part1_3_main_ratios_li7_fluxavg_xs_li6_7p59.png`: natural lithium, source-shape response ratios versus flux-averaged Li7 MT205 cross section.
- `c1_part1_3_main_ratios_li7_fluxavg_xs_li6_90p0.png`: 90 at.% Li6 enriched lithium, same descriptor.
- `c1_part1_3_main_ratios_frac4MeV_li6_7p59.png`: natural lithium cross-check using neutron fraction above 4 MeV.
- `c1_part1_3_main_ratios_frac4MeV_li6_90p0.png`: enriched lithium cross-check using neutron fraction above 4 MeV.
- `c1_part4_hdpe_B_over_A_li6_7p59.png`: HDPE moderator control, natural lithium B/A ratio.
- `c1_part4_hdpe_B_over_A_li6_90p0.png`: HDPE moderator control, enriched lithium B/A ratio.
- `c1_part4_hdpe_total_tpr_li6_7p59.png`: HDPE moderator control, natural lithium total TPR per source neutron.
- `c1_part4_hdpe_total_tpr_li6_90p0.png`: HDPE moderator control, enriched lithium total TPR per source neutron.

## Tables

- `c1_part1_3_source_decomposition_summary.csv`: full source decomposition table for Case A, Case A-prime, and Case B.
- `c1_part4_hdpe_moderator_summary.csv`: full HDPE moderator control table.
- `cutoff_9p8MeV_loss_summary.csv`: sensitivity table for the incident-deuteron 9.8 MeV cutoff question.
- `final_key_openmc_results.csv`: compact table for the main representative OpenMC results.
- `final_key_hdpe_results.csv`: compact table for the HDPE control.
- `final_key_cutoff_9p8MeV_results.csv`: compact table for the 9.8 MeV cutoff sensitivity.

## Data Roots

The reproducible local calculation outputs are under:

- `/Volumes/billboom/paperwork/no6/stageB_inputs_20260706/openmc_c1_20260706/part1_3_decomposition`
- `/Volumes/billboom/paperwork/no6/stageB_inputs_20260706/openmc_c1_20260706/part4_hdpe_moderator`
- `/Volumes/billboom/paperwork/no6/stageB_inputs_20260706/openmc_c1_20260706/cutoff_9p8MeV_sensitivity`
