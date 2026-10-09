# Song (2026) Sierra Negra reproduction

**Status: partial, with original-catalog analysis, approximate association and independent GNSS calculations.** The full Bell catalog passes its published checksum and contains 219 events on 26 June 2018. Nine three-component stations across 8G and EC and all four PAYG days in Supplementary Figure 5 are acquired. Eight stations are complete; SN02 has gaps. The VCH1 archive checksum is verified, with 191 events on the date retained in a separate catalog. The supplement is reviewed. No enhanced located catalog, event-associated LP/VT population, observed families or published regressions are reproduced yet.

The project generates partial main Figures 1, 2 and 4, a station map, an original conceptual Figure 6 and an independent raw-waveform reproduction of S5. Fifteen numerical tests pass in the installed modern environment. Raw waveforms and checkpoint weights stay on the data drive and out of Git. The public [GitHub repository](https://github.com/maochuan-zhang-UW/song2026-sierra-negra-reproduction) is published and its remote commit verified.

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

Approximate PyOcto locations use [Tepp et al. (2014) Table 1 Model F](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1002/2013JB010227), with published P/S values, piecewise-linear interpolation and documented elevation correction. They are candidate associations; no HypoInverse/HypoDD relocation or magnitudes are claimed. Configuration and differences from Song's model are described in `docs/gnss_and_velocity.md`.

Approximate association now yields **536 candidates**, with 2,730 P and 2,408 S assigned arrivals. All satisfy four P, one S and the 0.5-s tolerance. Time-only matching finds 199 original entries within two seconds, without establishing event identity or completeness. See [candidate catalog](results/catalogs/approximate_associated_events.csv), [validation](results/tables/approximate_association_validation.json) and [figure](results/figures/approximate_association.png). About 53.9% occupy the shallowest 0.46875-km grid node; depth interpretation requires finer relocation.
