# Independent GNSS processing and approximate velocity model

## Observation validation

Authenticated EarthScope observations are genuine Unix-compressed Hatanaka CRINEX 1.0/RINEX 2.11 GPS files. `validate_gnss.py` decompresses them with the Hatanaka tools, checks monotonic unique epoch/satellite records, and measures coverage and dual-frequency observables. Neither header coordinates nor carrier phases alone are deformation estimates. Detailed hashes and counts are in `results/tables/gnss_rinex_validation.json`.

The sampling interval is 30 s. Header epochs are GPS time: subtract 18 s to obtain UTC. The daily file starts at 23:59:42 UTC on 25 June. GV09 contains all 2,880 epochs with at least nine satellites carrying L1/L2/C1/P2. GV03 contains 1,431 epochs (49.6875%) and nine internal gaps. Its largest gap extends from 03:21:42 to 12:46:12 UTC, preventing a coseismic estimate at GV03. No observations are interpolated through these gaps. VCH1 retrieval is skipped at the user's instruction and remains a seismic coverage gap.

## Independent precise point positioning

`run_gnss_ppp.sh` executes pinned RTKLIB 2.4.2 on GPS dual-frequency observations, with ESA final reprocessed five-minute SP3 orbits, 30-second clocks and IGS20 antenna calibration. Clock headers identify IGS20 calibration. Both stations' broadcast navigation files are needed for initialization and satellite information: using GV03 navigation alone loses GV09 solutions across the GV03 outage. ESA SP3 filenames are converted to lowercase extensions to accommodate an RTKLIB suffix-reading bug. Download sources and hashes are recorded; observations and auxiliary products remain outside Git.

Settings are in `config/gnss_ppp.conf`: forward kinematic float ambiguities, ionosphere-free dual-frequency combination, 15-degree elevation mask, estimated zenith tropospheric delay with Saastamoinen processing, solid Earth tides, no ocean loading, receiver antenna from the RINEX header. These are independent alternatives to the paper's GIPSY-OASIS II 6.3, VMF1 and FES2004 processing. The downloaded current IGS20 calibration is not asserted to match the exact historical ESA calibration revision. No reference-frame or absolute-position accuracy claim follows from this calculation.

ECEF solutions are projected into east/north/up axes at the header approximate coordinate. Changes use the 01:00–02:00 UTC mean as a datum. Screening retains Q=6, at least five satellites, and at least one hour since the first solution or a gap exceeding five minutes. This explicitly chosen convergence screen is conservative, not a published criterion or proof of convergence. Raw solutions and screening flags remain available. The pipeline yields 2,880 GV09 and 1,431 GV03 PPP epochs; 2,760 and 836 respectively survive screening.

At the catalog fault-earthquake time 09:15:32.299 UTC, the difference between one-hour post- and pre-event GV09 means is east −0.09460 m, north +0.84616 m, up +1.86707 m (120 epochs in each window). The vertical within-window standard deviations are 0.00788 m before and 0.02528 m after; they measure scatter and evolving deformation, not confidence intervals. The paper reports **at least 1.83 m** uplift at GV09. The independent result is consistent with that lower bound, exceeding it by 0.03707 m; the published number is not an exact target suitable for percentage error. Different correction models, time windows, and postseismic motion limit agreement. No instantaneous-step fit or independent eruption-onset estimate is claimed.

## Relative-baseline cross-check

`run_gnss_relative.sh` computes the GV09–GV03 baseline using combined forward/backward dual-frequency kinematic processing, broadcast navigation, 15-degree mask, continuous ambiguity resolution and ratio threshold 3. The computational base coordinate is fixed to its header value, although GV03 physically moves. Thus this measures relative motion. Single-point solutions, solutions with nonzero reference age, and epochs lacking simultaneous GV03 observations are rejected. Of 2,140 output epochs, 1,410 are valid relative solutions: 1,363 fixed and 47 float; 730 are rejected. Fixed ambiguities are a quality indicator, not proof against a false fix.

The relative datum is 00:30–01:30 UTC. No relative coseismic result is computed because both fault-earthquake averaging windows are missing. Later relative deformation is plotted without connecting gaps. Intrusion/eruption annotations are literature times. Window comparisons are descriptive differences over an evolving trajectory, not unique causal tests. Relative and PPP products are separate and do not assume either station is stable.

## Published velocity-model approximation

The adopted model is **Tepp et al. (2014), Table 1, Model F**, DOI [10.1002/2013JB010227](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2013JB010227). Numerical P and S speeds are copied from the table rather than estimated from a figure. `config/tepp2014_model_f.csv` uses original Model F nodes at sea-level depths 0, 2, 4, 8, 12, 20 and 40 km. The −2 km value uses the explicitly published top grid-layer Model F value (3.95/2.19 km/s). The combination with the original nodes, piecewise-linear interpolation, and PyOcto surface elevation correction at 4.29/2.38 km/s are declared implementation approximations. They are not Song's/Rezaeifar's exact model. The published S values are used directly; no new Vp/Vs is invented.

`associate_approximate.py` constructs 0.1-km travel-time tables, applies a 0.5-s match/model tolerance, and requires at least four P and one S pick. The declared domain is latitude −0.90 to −0.76, longitude −91.22 to −91.08, depths 0–30 km below sea level, with 1-km location nodes and 2-s minimum interevent time. The domain center and remaining PyOcto defaults are independent choices. Stations use archived elevations. Events above sea level are excluded by PyOcto 1-D limitations. Only the seven already-picked 8G stations enter this run. Computational time slices are 300 s with 16 workers; these are independent processing settings. Initial attempts were stopped without catalog output after identifying a pandas microsecond/nanosecond conversion error. Explicit nanosecond conversion and a regression test correct the error; no counts are claimed from the stopped attempts. HypoInverse, HypoDD and magnitude estimation are not executed, so outputs are approximate associated candidates rather than the paper's 694 relocated events or 1,935-event enhanced catalog.

The PPP/relative processing cross-check has 814 common screened ambiguity-fixed epochs. After alignment over 60 epochs at 01:00–01:30 UTC and projection into the same base-station axes, RMS differences are 0.03169 m east, 0.01625 m north and 0.06474 m up. Shared observation errors are correlated, so this measures method consistency rather than independent accuracy. Details are in `results/tables/gnss_method_crosscheck.json`.

The completed nominal run yields 536 events and 5,138 assigned arrivals (2,730 P, 2,408 S), median absolute residual 0.09821 s and maximum 0.49953 s. Validation verifies phase counts, residuals, unique station/phase assignments and geographic bounds. Time-only matching finds 199 distinct original entries within two seconds; identities, false alarms and completeness are not established. Approximately 53.9% of candidates lie at the shallowest 0.46875-km location node, which bounds interpretation of source depths.

## Velocity sensitivity

Uniform P/S speed factors 0.95 and 1.05 are declared sensitivity cases, not uncertainty confidence bounds. They produce 536 and 534 candidates after enforcing final residual ≤0.5 s and phase minimums. The nominal count is 536. There are 531 and 530 mutual nearest time matches within two seconds, respectively. On those matches the median horizontal/depth shift is zero at this coarse grid, while 90th-percentile shifts are about 1.373 km horizontally and 0.938 km in depth in both cases. The unchanged median does not imply precise or robust locations. Two and three arrivals are removed from the perturbed runs because PyOcto refinement updates returned residuals beyond the initial match tolerance. No nominal arrivals are removed. Regenerate with:

```bash
.venv/bin/python scripts/associate_approximate.py --speed-scale .95 --label velocity_slow
.venv/bin/python scripts/associate_approximate.py --speed-scale 1.05 --label velocity_fast
.venv/bin/python scripts/validate_association.py
.venv/bin/python scripts/summarize_velocity_sensitivity.py
```

`results/tables/velocity_sensitivity.json` retains matched-event shifts and limitations. The timestamp fix also applies to the future recurrence-window CLI; its synthetic end-to-end test now checks actual 120-s intervals, rather than only row counts. Observed family recurrence statistics have not been computed.
