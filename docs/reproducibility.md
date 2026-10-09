# Reproducibility assessment

Status: **partial reproduction using an archived catalog and acquired raw waveforms**. The project does not yet reproduce the enhanced event catalog, LP/VT populations, family memberships or moment–recurrence regressions. Numerical tests and phase picks must not be equated with a located earthquake catalog.

## Verified data and methods

Song et al. (2026), https://doi.org/10.1038/s41467-026-68645-4, provides waveform and GNSS archive pointers but no separate source-code or enhanced-catalog deposit identified in the accessible article. Absence of an identified deposit is not evidence that none exists. No authors were contacted.

The supplementary PDF was downloaded and reviewed on 9 October 2026. It contains supplementary methods, figures S1–S9 and references. [The methods audit](supplementary_methods.md) records verified settings, figure content and remaining decisions. In particular, S9 uses log–log RANSAC, whereas the earlier ordinary-least-squares implementation is an independent numerical option.

Bell et al.'s archive, https://doi.org/10.5281/zenodo.4389190, provides the original catalog, VCH1 catalog, GNSS baseline and interferometric products. It is not the enhanced Song catalog. The complete original catalog now matches published MD5 `8935d6cc8189ff1991ba966666aacd66`. Its date-specific subset confirms all 219 previously recovered events. Metadata establish CC-BY-4.0 licensing. The GNSS baseline also matches published MD5 `217c1c1e3582ef9fb8e88b659d9a4c32`; its long-term scalar series does not replace the paper's 30-second GV03/GV09 positions.

EarthScope 8G requests yielded seven complete three-component, 100 Hz stations on 26 June 2018: SN04, SN05, SN07, SN11, SN12, SN13 and SN14. Metadata contain ten stations for the date; metadata presence does not establish waveform availability. The 21 acquired channels contain complete daily records. Counts exclude the inclusive endpoint at next midnight. Coverage and station tables accompany raw-file hashes. Additional retrieval now supplies EC SN02 and SN06, bringing the acquired total to nine stations and 27 channels. SN06 is complete; SN02 has 79,636.67 s of common three-component data (92.172%). VCH1 waveforms still require provider access. Combined coverage and orientation tables preserve gaps; no EC picking has run.

All four IU.PAYG.00.BHZ records shown in S5 were downloaded, with instrument-response epochs. Dates are 26 June 2018, 22 October 2005, 16 April 2005 and 22 December 1999. Response-corrected ground-velocity day plots were generated from those records. They are computational reproductions, not digitized traces. Stabilization and graphical settings differ from the unspecified original settings.

The public Volpick EQTransformer checkpoint v1 is cached on the data drive. Its equivalence to the authors' exact checkpoint is unverified. The modern environment includes ObsPy, PyTorch, SeisBench and PyOcto; versions are recorded in `environment/waveforms-lock.txt`. GPU operation is unavailable; inference uses CPU. The public model's batch pre/forward/post methods run directly because asynchronous stream inference stalled. Valid overlapping predictions are averaged; five-second blind edges remain uncovered at the full-day boundaries. SeisBench's probability trigger-to-pick routine extracts candidate arrivals. Explicit implementation choices are recorded with executed picks. An overlap test verifies averaging and missing-component rejection.

## Implementation and remaining scientific inputs

| Component | Implemented/executed | Remaining requirement |
|---|---|---|
| Catalog acquisition | Full source checksum verified; date subset analyzed | Enhanced source catalog and picks |
| Waveforms | Nine stations across 8G/EC; four PAYG historical records; coverage inventoried | VCH1 access; SN02 gaps; EC inputs not yet picked |
| Picking | Public checkpoint executed on actual acquired waveforms | Exact checkpoint and unspecified filtering/normalization details |
| Association | 536 approximate candidates, 5,138 assigned picks, constraints validated | Published alternative Model F supplied; exact original model/domain and location controls differ |
| Locations | Published relocation selection/windows reviewed | HypoInverse/HypoDD source controls, differential observations; no relocation run |
| Template matching | FFT kernels tested; nine-MAD and 0.4 quality thresholds recorded | Real relocated templates and picks; original gap/spike controls |
| FI classification | Amplitude-based FI tested, LP < -2 | Event-associated arrival windows and SNR definition |
| Multiplets | C++ signed NCC and connected components tested | Observed event windows, lag/station aggregation and manual inspection |
| Recurrence/moment | Conversion, pairing, OLS and jackknife tested | Real families, RANSAC controls and interval pairing |
| GNSS | Validated RINEX, independent float PPP and relative baseline computed | Original GIPSY/VMF1/FES2004 controls; GV03 outage |

The velocity-model manuscript (Rezaeifar et al., 2024) is locally reviewed. It describes a VELEST-derived 1-D P model and plots it, without a numerical layer table identified in accessible text. Authorized approximate association uses published Tepp et al. (2014) Table 1 Model F P/S values with explicit interpolation and elevation correction; differential relocation remains unexecuted.

FI is the base-2 logarithm of mean spectral amplitude at 9–15 Hz divided by mean spectral amplitude at 2–5 Hz. FI -2 implies amplitude ratio 1/4, not integrated energy ratio 1/4. Unmeasured events remain unclassified.

The independent NCC implementation selects the largest absolute correlation at explicitly allowed lags, preserving sign. Its common-channel average and lag search are not established as the authors' exact network aggregation. Candidates with negative correlation require manual review; they are not confirmed polarity reversals.

## Figure inventory

| Figure | Current status | Comparison limits |
|---|---|---|
| Main 1 | Original event map/depth projection; additional actual-station map | Terrain, faults and reservoir missing; GNSS DOI coordinates now mapped; source depth datum unresolved |
| Main 2 | Original cumulative count and magnitude/time | Enhanced curve and high-rate GNSS missing |
| Main 3 | Unreproduced | Event FI and observed family memberships missing |
| Main 4 | Four original-catalog phase maps | FI, terrain and normalized GNSS missing |
| Main 5 | Unreproduced | Real families and anticorrelated waveform pairs missing |
| Main 6 | Original conceptual schematic | Not a numerical simulation; fluid mechanism labeled as hypothesis |
| S1 | Unreproduced | Manual calibration event identities and event FI |
| S2 | Unreproduced | Located classified LP and typical VT populations |
| S3 | Unreproduced | Identified family waveforms |
| S4 | Unreproduced | Family membership and recurrence intervals |
| S5 | All four real-waveform day plots generated, PDF/PNG | Response stabilization, gain and rendering differ; original settings unspecified |
| S6 | Unreproduced | Original PCA amplitude/magnitude calibration samples |
| S7 | Unreproduced | Before/after matching catalogs; original binning |
| S8 | Unreproduced | Measured and inherited event FI |
| S9 | Unreproduced | Log–log RANSAC samples, controls and jackknife details |

S5 uses per-day display gain based on the 99th percentile of absolute velocity, with no clipping of physical amplitudes. One-second min/max envelopes retain short peaks. Deconvolution uses output VEL, prefilter (0.01, 0.02, 8, 9) Hz and no water level; each contiguous segment is processed independently. Those are documented independent choices, not published values. Major wave packets occur in the corresponding published half-hour rows, but amplitude agreement cannot be claimed without identical preprocessing and gain.

## Published inconsistencies and validation

Results report 1,224 VT and 711 LP events (1,935 total); Methods report 1,214 VT and 711 LP (1,925). The stated 694 located plus 1,241 matched events give 1,935. Both VT values are preserved. The associated arrival counts in the main text must not be compared with all candidate picks in the supplement.

Eleven numerical tests pass under the modern environment. They compare FFT and C++ correlation to direct calculations, recover injected signs, verify amplitude-based FI, transitive families, moment conversion, recurrence pairing, regressions and window handling. These use constructed signals, excluded from volcanic results. Archived catalog count and checksum validation use actual observations.

The observed original phase counts are 29/74/72/44 using a 19:40 eruption boundary. A 19:35 boundary gives 29/74/69/47. These are catalog observations, not completeness-corrected physical rates. The mainshock's original time is 09:15:32.299; its original magnitude 4.73 is distinct from reported Mw 5.4.

Completed actual-waveform Volpick execution processed all 168 acquired station-hours: **6,908 P and 6,379 S candidate picks** (13,287 total). The supplement reports 13,144 P and 12,196 S candidates before association across the study network. Differences are -6,236 P and -5,817 S, with station coverage and processing/checkpoint choices differing; these are not earthquake-count differences or evidence of detection completeness. The [execution record](../results/tables/volpick_execution.json) and checkpoint hashes document the run. No false-pick rate or event completeness has been estimated.

The public repository is published at https://github.com/maochuan-zhang-UW/song2026-sierra-negra-reproduction. The full VCH1 original catalog also passes its published MD5; its separate date subset contains 191 events. It lacks locations and event identities for reliable merging with the 219-event located catalog. A new consolidated station map includes 14 seismic metadata stations (nine acquired) and GV03/GV09 DOI coordinates. GNSS observations and navigation files are now authenticated, decompressed and validated; independent PPP positions are calculated. See `gnss_and_velocity.md` for coverage, processing settings and departures from source methods. See `docs/data_access.md` and `results/tables/remaining_data_access.json`.

Independent PPP gives a one-hour GV09 vertical difference of 1.86707 m, consistent with the published lower bound of 1.83 m. This is not an exact scalar agreement test. GV03 has no coseismic estimate owing to its outage. New GNSS figures supplement the original-catalog main Figure 2 comparison; LP/VT and family results remain incomplete.

The nominal published-model approximation produces 536 candidates (2,730 P and 2,408 S assigned arrivals). Median absolute residual is 0.0982 s. There are 199 time-only matches to distinct original events within two seconds; unmatched candidates are not automatically new earthquakes. No false-detection or completeness estimate follows from this comparison.
