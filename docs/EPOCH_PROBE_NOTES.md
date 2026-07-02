# EPOCH Particle Probe Notes

This note records the EPOCH source-code behavior checked for the no5 PIC
source extraction workflow.

## What `begin:probe` Records

In EPOCH 4.20.1, a particle probe is a plane-crossing diagnostic.

Checked source path on BSCC:

```text
/publicfs10/fs10-m9/home/m9s003861/pic/software/epoch_release-4.20.1/epoch2d/src
```

Relevant behavior:

```text
deck/deck_particle_probe_block.F90:
  the probe uses a point and normal to define a plane through Hessian normal form

particles.F90:
  d_init  = normal dot (point - initial_position)
  d_final = normal dot (point - final_position)
  if d_final < 0 and d_init >= 0, the particle crossed the probe plane

io/probes.F90:
  write_probes writes sampled_particles to SDF
  after writing, destroy_partlist(current_probe%sampled_particles) is called
```

Therefore:

```text
probe geometry: true plane-crossing diagnostic
probe direction: unidirectional, set by the sign of the normal
SDF file content: particles collected since the previous probe write
full source: concatenate all probe windows, or run one deliberately long window
```

For our decks, `normal = (1, 0)` at `rear+N um` records particles moving from
upstream to downstream across that vertical plane. A postprocessing `px > 0`
filter is redundant for this geometry, but harmless as a guard.

## Practical Consequence

Do not treat a single late SDF probe file as the full source unless the output
was intentionally configured as one long window. With `dt_snapshot = 250 fs`,
each nonempty probe file is a 250 fs time window. The Stage B source should be
built by concatenating the windows through the accepted end time.

The end time is accepted only when the latest window contributes less than
about 5-10% of the integrated source weight and the integrated spectrum/angle
metrics change by about 5-10% or less after adding the latest window.
