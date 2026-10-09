# Independent station validation and differential-location pilot

The seven-station search was constructed from 8G waveforms. EC stations SN02
and SN06 therefore supply waveforms excluded from template construction. The
public picker is shared, and the velocity model is shared; this is independent
station evidence, not independent model calibration.

`validate_heldout_stations.py` predicts P and S times with the actual PyOcto
travel-time table and the same elevation correction used in association. Real
common three-component intervals and five-second picker blind edges constrain
availability. A primary match requires both P and S at the same station within
0.5 seconds, with S following P. The result is 440/1543 supported candidates:
329/536 seeds and 111/1007 template additions. Five hundred shared-catalog time
controls use independent circular shifts of 60–3540 seconds in each UTC hour,
then reapply availability. They preserve within-hour temporal clustering but
assume approximate stationarity within each hour. Mean support is 14.988 for
all candidates and 10.076 for additions; the addition control's 95% range is
4.475–16. The empirical upper-tail probability is 1/501, limited by the number
of controls. Tolerances of 0.2, 1 and 2 seconds are also reported.

Missing support is not proof of a false earthquake: station coverage, picker
sensitivity and approximate inherited locations affect the prediction. These
controls do not estimate a calibrated earthquake false-positive rate. Nor do
they validate classification, location accuracy or family membership.

## Author code and independent pilot

HypoDD is fetched from the [author's repository](https://github.com/fwaldhauser/HypoDD)
at revision `fb40407fb768cbdc23a11e27bc841f5d4a98abb7` by
`scripts/setup_hypodd.sh`. Unmodified Fortran source builds with gfortran,
legacy syntax and the medium memory model. Source and binaries remain in
ignored scratch storage. The unchanged author example1 executes successfully:
16 event IDs agree with the distributed reference, maximum horizontal
Cartesian difference is 0.806 m, maximum depth difference is 1 m and maximum
seconds-field difference is zero. Small differences are not treated as exact
binary agreement.

`prepare_hypodd.py` generates real differential phase times from the nine-station
716-candidate catalog. Pairs are separated by at most 5 km initially and share
at least four station-phase observations (not four distinct stations). There
are 151447 pairs and 1195493 observations. Unknown magnitude and input location
errors are -9 placeholders, never measured values. Event times are rounded to
10 ms consistently with the input format. Equal P/S unit weights, ten LSQR
iterations and damping 20 are explicitly independent choices. Model F's nodes
become piecewise constant HypoDD layers rather than PyOcto's interpolation.
No cross-correlation differential times, HypoInverse initialization, original
bootstrap uncertainties or author-specific settings are claimed.

The source's airquake rule checks negative depth relative to zero, not the
local volcanic surface. This is restrictive for an edifice above sea level.
The pilot records this boundary and all removed IDs; removal is not evidence
that an event is false. Pilot outputs remain separate from the template catalog.

The baseline pilot completed but failed validation: 206 of 716 inputs survive, only three within the initial domain. Median horizontal drift is 35.02 km and median absolute depth drift is 56.74 km. Seven inputs lack accepted links; 503 connected events are removed alongside negative-depth warnings. No output is scientifically accepted. `analyze_hypodd_ct.py` preserves all input IDs and status fields in an audit CSV, with missing magnitudes omitted. `run_hypodd_pilot.py --keep-shallow-events` tests the native IAQ=0 policy: it retains events but freezes updates that would cross zero depth. This is a boundary sensitivity, not unconstrained above-sea-level relocation.

Reproduce the code validation with `python scripts/validate_hypodd_build.py` after setup. Execute the baseline with `python scripts/run_hypodd_pilot.py`, then `python scripts/analyze_hypodd_ct.py`; add `--keep-shallow-events` to both commands for the native IAQ=0 sensitivity. All working inputs, source and binary files remain under the project scratch cache.

The IAQ=0 sensitivity completes with 709 retained events, 700 in the original domain. Median horizontal shift is 0.62377 km (90th percentile 1.36701 km), median absolute depth shift 0.35525 km. Maximum horizontal shift is 110.6203 km and maximum depth 58.684 km. Its 1219 negative-depth warnings count repeated proposed steps, not unique earthquakes. It remains an unvalidated boundary-conditioned diagnostic. The contrast with the removal case establishes strong policy sensitivity and does not identify the source catalog.
