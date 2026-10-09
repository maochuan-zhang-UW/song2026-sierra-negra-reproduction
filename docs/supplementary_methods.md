# Verified supplementary methods

Reviewed the downloaded 13-page supplement on 9 October 2026. Source: https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41467-026-68645-4/MediaObjects/41467_2026_68645_MOESM1_ESM.pdf. File checksum is recorded in `results/tables/raw_file_checksums.json`. Equations and settings below are transcriptions, not computed results.

## Detection and association (pages 2–3)

Volpick inputs are 100 Hz waveforms filtered at 2–12 Hz, detrended and normalized. Windows last 60 s and overlap by 50%. P and S probabilities use a 0.2 threshold. The supplement reports 13,144 P and 12,196 S candidate picks, reduced through association to 6,261 P and 5,159 S arrivals in 994 events. Main-text arrival counts therefore refer to associated picks, not all picker outputs.

Association requires four P and one S picks, with 0.5 s residual tolerance. The location search spans 0.14 degrees horizontally and 30 km in depth at 1 km spacing, using Rezaeifar et al. (2024)'s 1-D model. Events within 2 s are duplicates; the event with fewer assigned picks is removed. The exact caldera center and numerical velocity layers are not given here.

HypoInverse precedes HypoDD. The authors retain 785 events with azimuthal gaps below 300 degrees and location errors below 5 km, then relocate 694. Event-pair distance is at most 5 km; pairs require four common observations. Differential-time P windows are 1.5 s on vertical components, starting 0.5 s before P; S windows are 3 s on horizontal components, starting 1 s before S. SNR must exceed 2 and NCC must exceed 0.7. These are relocation windows, distinct from five-second classification and template windows. HypoInverse/HypoDD control files, weights and iteration settings remain unavailable.

## Magnitudes (page 3)

The supplement gives

`ML = log10(APeak) + log10(R/100) + 0.00301*(R-100) + 3.0`.

It measures average horizontal peak-to-peak amplitude in five-second S windows beginning one second before arrival after response removal and Wood–Anderson simulation; network magnitudes are station medians. The text calls R epicentral distance. Units for APeak and R must be established from the cited calibration rather than assumed. No local magnitudes have been independently estimated here.

## Template matching (pages 3–4)

Templates and continuous data use 50 Hz sampling and 2–20 Hz filtering. P windows use vertical components; S windows use horizontal components. Both last five seconds and start one second before arrivals. Templates require SNR at least 2 at four stations; 669 are retained. Continuous chunks last one hour with 30 s overlap. The authors discard chunks with excessive gaps/spikes without numerical rejection criteria.

Network summed NCC must exceed nine times the stated median absolute deviation. The EQcorrscan implementation's `MAD` convention requires verification against source controls. Average station NCC below 0.4 is rejected. Detections within two seconds of templates are removed, and detections within two seconds of each other are reduced to the highest NCC. The authors report 1,241 additional events, co-located with templates.

Relative magnitude is `MDetection = MTemplate + 0.7*log(alpha)`. Alpha is measured using PCA on five-second preprocessed vertical P windows, starting one second before P; the network median is retained. The logarithm base and PCA details require source-method verification.

## Figures and statistics (pages 5–11)

The supplement contains exactly S1–S9. S1 uses five largest manually labeled events of each class, all magnitudes below 3, to calibrate FI. S2 compares LP locations with typical VT events having FI above zero. S3 shows aligned SN12 waveforms. S4 classifies families by average member FI and plots periodicity and its relation to mean recurrence time.

S5 contains PAYG BHZ day plots for 26 June 2018, 22 October 2005, 16 April 2005 and 22 December 1999. It concerns ground velocity, not GNSS. All four raw records and epoch response metadata are now acquired.

S6 calibrates the relative-magnitude factor with a principal-component fit. S7 uses maximum curvature for magnitude completeness, comparing catalogs before/after template matching separately before/after intrusion. Histogram binning is unspecified. S8 compares directly measured and template-inherited FI.

S9 uses **RANSAC on log10 moment versus log10 recurrence time**, not ordinary least squares on dimensional values. Its displayed fits are slope/intercept 0.58/11.27 for VT and -0.05/11.2 for LP, with reported R² 0.7 and 0.07. Jackknife distribution peaks differ slightly from full-sample fits. RANSAC thresholds, random state, inlier selection, exact R² sample and recurrence pairing remain unspecified. The existing ordinary-least-squares routine is an independently tested numerical option; it does not reproduce S9.

## Additional velocity-model source

The accepted Rezaeifar et al. (2024) manuscript was obtained from https://www.pure.ed.ac.uk/ws/portalfiles/portal/444614081/Main_text-4_D_imaging_V3.0.pdf (doi:10.1016/j.jvolgeores.2024.108112). Its text describes a VELEST-derived average P-velocity model and displays it in Figure 2. The accessible text provides no numerical layer table or S-velocity prescription, and its data statement links the same Bell catalog and waveform archives. A plotted model is insufficient for an exact numerical association/relocation reproduction. No layers or Vp/Vs ratio are invented.
