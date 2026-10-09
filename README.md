# Song (2026) Sierra Negra reproduction

**Status: partial reproduction with actual waveform detection, spectral classification, template matching and independent GNSS processing.** The original archive contains 219 events on 26 June 2018. Nine seismic stations are acquired: eight complete and SN02 gapped; VCH1 is skipped as requested. The public Volpick checkpoint produces 8,573 P and 8,001 S picks across the nine stations. Using the declared published Tepp et al. 1-D approximation gives 716 candidate associations. An independent HypoDD pilot runs but fails location validation; it is archived separately and rejected.

A separate seven-station baseline gives 536 associated candidates (96 LP, 438 VT, two unclassified). A full-day search with 447 templates recovers every template and adds 1,007 candidates, giving 1,543 events with inherited classifications: 453 LP, 1,088 VT and two unclassified. Direct spectra are measurable for 646 new detections and agree with inherited labels in 520 cases. These are independent candidate results, not the published enhanced catalog or verified false-positive-free earthquake counts. See [processing and sensitivity details](docs/candidate_waveform_analysis.md).

GV09 independent float PPP gives a 1.867-m hourly uplift at the fault earthquake, consistent with the reported lower bound. GV03 has an observation outage across that earthquake. The project also provides partial main figures, four independently processed PAYG day plots (S5), and an original conceptual Figure 6. Raw waveforms and model weights remain outside Git.
- [Compiled report](report/main.pdf), [LaTeX source](report/main.tex), [executed notebook](report/analysis.ipynb)
- [Reproducibility assessment](docs/reproducibility.md), [supplementary-methods audit](docs/supplementary_methods.md), [limitations](docs/limitations.md)
- [Comparison table](results/tables/comparison.csv), [original catalog](results/catalogs/original_20180626.csv), [catalog provenance](results/tables/catalog_provenance.json)
- [Waveform coverage](results/tables/waveform_coverage.csv), [stations](results/tables/stations.csv), [raw-source checksums](results/tables/raw_file_checksums.json)
- [PAYG S5 figure](results/figures/figS05_payg_dayplots.png), [processing settings](results/tables/payg_processing.json)

Study: Song et al. (2026), https://doi.org/10.1038/s41467-026-68645-4. Original archive: Bell et al., https://doi.org/10.5281/zenodo.4389190 (CC-BY-4.0). IGUANA: https://doi.org/10.7914/SN/8G_2018. Public Volpick checkpoint: https://github.com/zhong-yy/volpick. These sources are distinct: the Bell catalog is not Song's enhanced catalog.

## Rebuild from a fresh environment

Work on a drive with room for waveform archives and scientific dependencies. Source `scripts/env.sh` from the repository root to keep temporary files, model weights and caches in this repository on the data drive.

```bash
source scripts/env.sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r environment/waveforms-lock.txt
bash scripts/build.sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/rebuild_from_csv.py
.venv/bin/python scripts/acquire.py --only IGUANA_Cat_V1.eventlist
.venv/bin/python scripts/analyze.py --catalog data/raw/IGUANA_Cat_V1.eventlist
```

Use `scripts/acquire.py --help` for additional named files. To regenerate S5, acquire `8G_20180626.mseed`, `stations.xml`, `PAYG_stations.xml`, and `PAYG_YYYY-MM-DD.mseed` for 2018-06-26, 2005-10-22, 2005-04-16 and 1999-12-22. Then run:

```bash
.venv/bin/python scripts/analyze_waveform_archive.py
.venv/bin/python scripts/make_notebook.py
cd report
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
```

Full source catalog MD5 is `8935d6cc8189ff1991ba966666aacd66`; it is verified locally. Archive metadata specify CC-BY-4.0. Raw-source checksums and processed figure settings are retained. Missing data are not filled silently. S5 response stabilization and display gain are independent documented choices, so exact amplitude agreement is not claimed.

## Detection and remaining analyses

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=8 .venv/bin/python scripts/pick_waveforms.py
.venv/bin/python scripts/summarize_picks.py
```

`scripts/pick_waveforms.py` runs the public Volpick checkpoint with published 0.2 thresholds and 50% window overlap on acquired 100-Hz records. It uses the checkpoint's own batch pre/forward/post methods and averages finite overlapping predictions; the asynchronous wrapper stalled in this environment. It records preprocessing and checkpoint assumptions. `summarize_picks.py` records counts, checkpoint hashes and coverage limitations. It outputs candidate phase picks, which require association and relocation before they become an earthquake catalog. `config/paper.json` distinguishes known settings from unresolved inputs. Filter order, phase convention, normalization, blinding and stacking are explicit independent choices where the supplement is silent.

`scripts/analyze_windows.py --help` describes classification, clustering and recurrence analysis on actual preprocessed arrival windows. It requires explicit lag, interval pairing, regression transform and standard-deviation choices. The existing regression routine uses OLS; Supplementary Figure 9 uses log–log RANSAC with unspecified controls. Synthetic numerical tests validate algorithms and are excluded from volcanic results.

Missing station coverage, original association/location controls and event/family catalogs prevent an exact full reproduction. Authenticated GNSS is now validated and independently processed; Tepp et al. (2014) Table 1 Model F supplies published P/S speeds for approximate locations. All departures from the source methods are documented. Correlation and timing alone do not establish a unique fluid-triggering mechanism.

## Additional retrieval and publication

```bash
.venv/bin/python scripts/acquire.py --remaining
.venv/bin/python scripts/inventory_remaining_data.py
```

Additional records and response metadata include EC SN02/SN06. [Combined coverage](results/tables/acquired_station_coverage.csv) reports the common three-component fraction, including SN02 gaps. The [VCH1 subset](results/catalogs/vch1_original_20180626.csv) is a separate original catalog; it is not merged with the located catalog because event equivalence is unverified. GNSS DOI metadata provide GV03/GV09 map coordinates, not deformation observations. See [access requirements](docs/data_access.md) for GNSS and VCH1 waveforms.

The project is public at https://github.com/maochuan-zhang-UW/song2026-sierra-negra-reproduction. Verify a checkout with:

```bash
gh repo view maochuan-zhang-UW/song2026-sierra-negra-reproduction --json url,visibility
git ls-remote origin refs/heads/main
```

Raw waveforms, authentication material, checkpoint weights and caches remain excluded from Git. The MIT license applies to original project code; third-party instructions and data retain their own attribution and licenses.

Completed actual-waveform Volpick execution processed all 168 acquired 8G station-hours: **6,908 P and 6,379 S candidate picks** (13,287 total). The supplement reports 13,144 P and 12,196 S candidates before association across the study network. Differences are -6,236 P and -5,817 S, with station coverage and processing/checkpoint choices differing; these are not earthquake-count differences or evidence of detection completeness. The [execution record](results/tables/volpick_execution.json) and checkpoint hashes document the run. No false-pick rate or event completeness has been estimated.

## Independent GNSS results and approximate locations

GV03 and GV09 Unix-compressed Hatanaka observations are decompressed and validated. GV09 has 2,880 epochs; GV03 has 1,431, with a long outage spanning the fault earthquake. VCH1 retrieval is skipped at the user's instruction and remains a seismic coverage gap.

Independent RTKLIB float PPP uses ESA final precise orbits/clocks and IGS20 antenna calibration. At GV09 the one-hour after-minus-before vertical mean is **1.86707 m**, consistent with the paper's **at least 1.83 m** lower bound. This does not establish exact agreement with its GIPSY/VMF1/FES2004 processing. GV03 has no coseismic estimate. A separate relative-baseline calculation retains 1,363 fixed and 47 float solutions and rejects stale-reference/single-point estimates. See [PPP figure](results/figures/gnss_independent_ppp.png), [relative figure](results/figures/gnss_relative_baseline.png), [validation](results/tables/gnss_rinex_validation.json), [PPP results](results/tables/gnss_ppp_analysis.json), and [methods and caveats](docs/gnss_and_velocity.md).

```bash
source scripts/env.sh
# EarthScope CLI must already be authenticated; no credentials go into Git.
bash scripts/run_gnss_relative.sh
bash scripts/run_gnss_ppp.sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python scripts/associate_approximate.py
```

Approximate PyOcto locations use [Tepp et al. (2014) Table 1 Model F](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2013JB010227), with published P/S values, piecewise-linear interpolation and documented elevation correction. They are candidate associations; no reproduction of the original HypoInverse/HypoDD workflow is claimed; independently estimated magnitudes are documented separately. Configuration and differences from Song's model are described in `docs/gnss_and_velocity.md`.

Approximate association now yields **536 candidates**, with 2,730 P and 2,408 S assigned arrivals. All satisfy four P, one S and the 0.5-s tolerance. Time-only matching finds 199 original entries within two seconds, without establishing event identity or completeness. See [candidate catalog](results/catalogs/approximate_associated_events.csv), [validation](results/tables/approximate_association_validation.json) and [figure](results/figures/approximate_association.png). About 53.9% occupy the shallowest 0.46875-km grid node; depth interpretation requires finer relocation.

## Executed waveform extension

From the repository root, after activating the waveform environment and retrieving inputs:

```bash
source scripts/env.sh
bash scripts/build.sh
.venv/bin/python scripts/pick_ec_waveforms.py
.venv/bin/python scripts/associate_approximate.py --label nine_station --picks results/catalogs/combined_volpick_picks.csv --inventories data/raw/stations.xml data/raw/EC_responses.xml
.venv/bin/python scripts/extract_candidate_windows.py
.venv/bin/python scripts/analyze_candidate_families.py
.venv/bin/python scripts/prepare_matching_velocity.py
.venv/bin/python scripts/match_candidate_templates.py
.venv/bin/python scripts/extract_matched_windows.py
.venv/bin/python scripts/analyze_candidate_families.py --enhanced
.venv/bin/python scripts/estimate_candidate_magnitudes.py
.venv/bin/python scripts/estimate_matched_magnitudes.py
.venv/bin/python scripts/analyze_observed_recurrence.py
.venv/bin/python scripts/plot_candidate_properties.py
```

The seven-station association must exist before window extraction (`associate_approximate.py` without arguments). The nine-station association is a separate coverage experiment and is not silently combined with seven-station templates. Magnitudes use explicit independent Wood–Anderson and amplitude-ratio conventions; execution records describe differences from the source methods.

Further sensitivity products are generated by `analyze_family_screen_sensitivity.py`, `analyze_observed_recurrence.py --permissive`, `summarize_matching_sensitivity.py`, `analyze_gnss_change.py`, `plot_enhanced_catalog.py` and `plot_waveform_supplements.py`. Regenerate the saved-output notebook with `make_notebook.py`; compile the report with `latexmk -cd -pdf -interaction=nonstopmode -halt-on-error report/main.tex`. Twenty-four numerical tests pass.

Numerical topography is retrieved and plotted by `plot_topographic_catalog.py`; the Copernicus attribution is preserved in [data documentation](data/README.md). `plot_remaining_supplements.py` supplies partial S2/S3/S4/S7 counterparts. S1 calibration identities and S6 original amplitude–magnitude calibration samples remain gaps. The nearest-distance map uses approximate inherited locations; histogram modes do not establish true detection completeness.

A full-day phase-randomized waveform-shape control is available via `match_candidate_templates.py --null-control`. It uses ten LP and ten VT templates, preserving each channel's amplitude spectrum while independently randomizing phases. The same detection thresholds yield zero raw control peaks. This is a specificity check with a smaller library, not an earthquake false-positive-rate estimate.

Independent station validation now supports 111 of the 1,007 template additions with P and S agreement at SN02 or SN06 within 0.5 s; shifted-time controls average 10.076. See [validation and relocation methods](docs/heldout_and_relocation.md). Regenerate with `python scripts/validate_heldout_stations.py` and `python scripts/plot_heldout_validation.py`. HypoDD author code is built by `bash scripts/setup_hypodd.sh`; pilot inputs are written by `python scripts/prepare_hypodd.py`. gfortran and make are required. The independent pilot uses catalog differential times and declared alternative controls.

Run the differential-location diagnostic with `python scripts/run_hypodd_pilot.py` and audit it with `python scripts/analyze_hypodd_ct.py`. The baseline pilot retains 206 events but shows 35.02-km median horizontal drift; these locations are rejected. This diagnostic is not an enhanced relocated catalog.

The unchanged author example can be rerun with `python scripts/validate_hypodd_build.py`. The native zero-depth sensitivity uses `python scripts/run_hypodd_pilot.py --keep-shallow-events` and `python scripts/analyze_hypodd_ct.py --keep-shallow-events`. This setting freezes negative-depth updates; it does not freely locate events above sea level.

The depth-policy sensitivity retains 709 events (700 inside the initial domain), with median horizontal shift 0.624 km. Large outliers and 1,219 repeated negative-depth step warnings remain; this catalog is a diagnostic, not validated source locations. Both pilot audits and held-out station results are included in the report.

The fixed-pick absolute-arrival audit (`scripts/audit_relocation_arrivals.py`)
compares 7,481 observations using the association model before and after IAQ=0
relocation. RMS increases from 0.170 to 0.247 s. This is model-consistency
analysis on fitted arrivals, not independent location validation; different
velocity-layer representations prevent attributing the change uniquely to
location error. See [audit methods](docs/heldout_and_relocation.md).
