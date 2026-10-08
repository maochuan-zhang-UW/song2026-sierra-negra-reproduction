# Reproducibility assessment

Status: **partial reproduction from an archived original catalog**. No continuous-waveform, trained-model, association, relocation, enhanced-catalog, or GNSS processing has run. Synthetic numerical tests validate algorithms only. This document is an assessment of the accessible main article and archive, not a completed review of the inaccessible supplement.

## Sources verified on 8 October 2026

- Song et al. (2026), https://doi.org/10.1038/s41467-026-68645-4. Main text, equations, captions and references were accessed as browser text at https://pmc.ncbi.nlm.nih.gov/articles/PMC12946353/ and the publisher PDF text. The publisher HTML encounters an identity-provider redirect. PDF screenshots failed; visual figure comparison is limited to captions and text.
- Supplement link: https://pmc.ncbi.nlm.nih.gov/articles/instance/12946353/bin/41467_2026_68645_MOESM1_ESM.pdf. The browser returned cache/access errors at both PMC and Springer CDN variants. Local downloads fail at DNS. Supplementary methods and figures have **not been reviewed**. Parameters delegated to them remain unknown.
- The accessible main text lists raw seismic and GNSS archives in Data Availability. It contains no separate Code Availability section or linked enhanced catalog. Targeted searches did not identify a Song-specific catalog/code deposit. This is not evidence that none exists; author inquiry may be needed. No author contact was made.
- Bell et al. (2021), https://doi.org/10.1038/s41467-021-21596-4 and https://zenodo.org/records/4389190. The archive explicitly lists the original IGUANA catalog, VCH1 catalog, interferograms, and a GNSS baseline. It is **not** the 2026 enhanced catalog. Browser text recovered the entire June 26 subset: consecutive source rows 348–566 inclusive; adjacent rows are other dates. The full download MD5 is published, but the subset cannot validate that checksum. Source fields and subset SHA-256 are recorded in `results/tables/catalog_provenance.json`.
- IGUANA is network **8G, 2018–2019**, verified at https://www.fdsn.org/networks/detail/8G_2018/; DOI 10.7914/SN/8G_2018. The main paper's generic 10.7914/SN is insufficient for acquisition. Metadata and waveform availability remain untested locally.
- Ecuador EC network: https://www.fdsn.org/networks/detail/EC/ and https://www.igepn.edu.ec/datos-mseed. Data may require provider access; do not assume the EarthScope query recovers these stations.
- GNSS archive cited by Song: https://www.unavco.org/data/doi/10.7283/3R4N-9775. Browser access failed. The Bell baseline is listed publicly but retrieval failed. It would not replace the paper's high-rate positions without verification.
- Original public Volpick weights verified at https://github.com/zhong-yy/volpick. SeisBench EQTransformer `from_pretrained('volpick')` accesses the model. The repository also provides another training variant; which exact weights/version Song used is not yet established. No weights were downloaded or inference executed.

## Methods traceability and independent implementations

| Step | Verified main-text definition | Remaining inputs or decisions | Current implementation/execution |
|---|---|---|---|
| Acquisition | June 26, 2018; broadband records | Actual channel coverage, station epoch metadata, EC access | Public catalog subset analyzed; download scripts provided, network attempts failed |
| Picking | Volpick EQTransformer | Thresholds, preprocessing, exact checkpoint | Dependency-bound adapter, not executed |
| Association | PyOcto | Velocity model, domain, phase count and tolerance settings | Not implemented with guessed settings; not executed |
| Location | HypoInverse then HypoDD | Input files, control settings, differential times, velocity model | Not executed; no fabricated template relocations |
| Matching | EQcorrscan; detections co-located with templates | Template criteria, preprocessing, threshold, duplicate control, time offsets | FFT normalized-correlation and detection kernels tested; no observational matching |
| Relative magnitudes | Scaling factor 0.7 | Exact amplitude estimator, stations and formula in supplement | Not inferred from 0.7 alone |
| Classification | Mean spectral-amplitude ratio; base-2 logarithm | Filter phase/order, taper, spectral estimator details, SNR definition | Tested FI implementation; five-second arrival windows; no event FI measured |
| Families | Positive network NCC >0.7; connected event pairs; minimum 10; template inheritance | Allowed lag, station/component aggregation, manual review | C++ signed NCC and components tested; input-window CLI provided, not executed on observations |
| Anti-repeaters | NCC <-0.7 plus manual inspection | Original pairs and waveforms | Candidate detection only; no confirmed observed pairs |
| Statistics | Piecewise magnitude conversion; moment intercept 9.105; mean/std recurrence periodicity; jackknife | Pair preceding/following interval, transform, std convention, samples/subsets | Implemented with explicit choices; tests only for family statistics |
| GNSS | 30-s PPP; GIPSY-OASIS II 6.3; ocean loading and mapping corrections | RINEX, orbits, PPP software and controls, original positions | One-hour displacement difference kernel tested; no PPP or observational GNSS execution |

The FI uses 9–15 Hz and 2–5 Hz mean **amplitudes**, not band energy sums. An FI of -2 implies a mean amplitude ratio 1/4, not an integrated energy ratio of 1/4. Retain this distinction when interpreting the paper's wording. The FI threshold is LP < -2, VT >= -2. Events lacking valid windows remain unclassified.

The independent event-pair kernel demeans overlapping windows at each lag, selects the largest absolute NCC, and preserves its sign. This is useful for polarity reversals but not established as the original lag procedure. Channels must represent common station/component/phase windows and pass the SNR criterion; missing stations do not contribute zero correlation. The current average weights common channel/phase keys equally, whereas the paper's precise station aggregation is unresolved. Alternative lag and station aggregation require sensitivity runs before membership agreement can be claimed.

## Published arithmetic inconsistencies

Results report 1,224 VT and 711 LP events, totaling 1,935. Methods report 1,214 VT and 711 LP, totaling 1,925. The stated 694 located events plus 1,241 new template events total 1,935. Neither VT value is silently corrected. The text also describes 47% of template signals as adequately recorded and 1,124 detections with measured FI; the unit of that percentage is unclear. Event-level coverage must be distinguished from station-signal coverage.

## Figure assessment

| Figure | Current product | Missing elements and comparison limits |
|---|---|---|
| Main 1 | Original-catalog epicenters, time color, latitude/depth projection | Stations, faults, terrain, sill geometry unavailable. All-event projection is not a selected cross-section. Source depth datum not verified. |
| Main 2 | Original cumulative counts and magnitude/time | Enhanced curve and GNSS missing. Event count is 219. Timeline annotations use published times. |
| Main 3 | Not reproduced | Requires measured/inherited FI, family memberships, caldera center and azimuth conventions. |
| Main 4 | Four original-catalog phase maps | Time color replaces unavailable FI and is labeled. GNSS/terrain absent. Out-of-zoom locations are counted. |
| Main 5 | Not reproduced | Requires family members, recurrence/moment sample choices and actual anticorrelated waveforms. Synthetic tests are not replacement panels. |
| Main 6 | Original four-stage schematic, PDF/PNG | Conceptual interpretation, geometry not to scale, no numerical stress/fluid simulation. Fluid pressurization is labeled as a hypothesis. |
| S1 | Not reproduced | Spectra, manual calibration labels, FI histogram required. |
| S2 | Not reproduced | Located LP/VT events and location errors required. |
| S3 | Not reproduced | Similarity and polarity-reversed waveform observations required. |
| S4 | Not reproduced | Family times and periodicity data required. |
| S5 | Not reproduced | Historical deformation and earthquake data required. |
| S6 | Not reproduced | Original relative-magnitude calibration required. |
| S7 | Not reproduced | Original/enhanced completeness analysis required. |
| S8 | Not reproduced | Measured/inherited FI comparison required. |
| S9 | Not reproduced | Original regression samples and resampling definition required. |

Supplement descriptions above come from main-text cross-references. The inaccessible supplement may include further panels, equations or tables. We cannot claim all supplementary assets have been inventoried.

## Previous-method review

The Volpick repository provides model loading and training provenance for Zhong and Tan (2024), doi:10.1029/2024GL108438. The public example uses P/S thresholds 0.2 and specific overlap/blinding settings; these are not verified Song settings. PyOcto documentation (https://pyocto.readthedocs.io/) explains that association requires station coordinates and a velocity model; no default model is adopted here. EQcorrscan documentation (https://eqcorrscan.readthedocs.io/en/latest/submodules/autogen/eqcorrscan.core.match_filter.matched_filter.match_filter.html) distinguishes absolute, network-mean and median-absolute thresholds; its MAD threshold uses `median(abs(cccsum))`, which differs from median absolute deviation about the median. The independent kernel names that convention explicitly. Waldhauser (2001), https://pubs.usgs.gov/publication/ofr01113, describes differential-time preprocessing and relocation. These references establish implementation dependencies; original controls are still needed. A full review of every cited detection/classification/multiplet paper has not been completed.

## Validation that was actually performed

Ten numerical test cases ran successfully on the installed Python environment and compiled C++ shared library. They compare FFT NCC with direct Pearson correlation and C++ lag results with NumPy, recover positive/negative injected signals, enforce the exact amplitude-based FI boundary, test connected components, moment conversion, pairing, regressions and missing-window handling. Tests use constructed mathematical signals only. Catalog validation requires unique IDs, finite quantities, valid coordinates and chronological sorting. No location-error cut is applied. Original magnitudes are never equated with the main earthquake's reported Mw 5.4.

Boundary sensitivity is computed from the same observed CSV: 19:35 gives 69/47 events in phases 3/4; 19:40 gives 72/44. The three-event reassignment is recorded in `results/tables/phase_boundary_sensitivity.csv` and regenerated by both catalog analysis routes.
