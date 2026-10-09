# Data and provenance

The full Bell catalog and archived GNSS baseline were downloaded from Zenodo 4389190 and match their published MD5 values. Zenodo metadata establish CC-BY-4.0. Derived date-specific original-catalog facts are in `results/catalogs/original_20180626.csv`; these are not Song's enhanced catalog. The full source confirms the earlier 219-row browser recovery.

Raw data stay under `data/raw`, outside Git. Acquired files include 21 complete 100-Hz channels from seven 8G stations for 26 June 2018, response metadata, all four PAYG BHZ days in S5, PAYG response epochs, supplementary methods and the Rezaeifar velocity-model manuscript. Source hashes are recorded in `results/tables/raw_file_checksums.json`, station/coverage tables in adjacent CSVs. Use `scripts/acquire.py --help` to retrieve named files; download endpoints may require retries. EC SN02/SN06 records and responses are now acquired; SN02 gaps are recorded in combined coverage tables. VCH1 original catalog checksum is verified and 191 date-specific rows are kept separately. GNSS PPP has not run; raw RINEX requires separate EarthScope authentication.

The GNSS baseline is a long-term scalar series, not the paper's 30-second GV03/GV09 positions. Its time/measurement conventions need source verification before physical analysis. Neither unknown velocity layers nor missing waveforms are synthesized.

Original catalog schema: event_id; UTC origin_time; latitude/longitude in decimal degrees; source depth_catalog_km (datum unresolved); magnitude (original scale, not substituted Mw); source error fields (units unverified); RMS seconds; azimuth gap degrees; phase-pick count; provenance; UTC hour; phase. Counts are not completeness-corrected. There are no event FI or family columns because these were not measured.

Candidate phase picks from any Volpick execution require association and relocation before becoming earthquakes. Their timestamps and model probabilities must not be interpreted as an enhanced event catalog.

GNSS raw observations (CRINEX and decompressed RINEX), station-specific navigation, ESA precise orbit/clock products and IGS20 antenna calibration are stored under `data/raw/gnss` and excluded from Git. Acquisition scripts record source URLs and hashes. Derived RTKLIB position solutions, validation summaries and observation-coverage tables are under `results`; they are independent processing products, not the authors' GIPSY time series. See `docs/gnss_and_velocity.md`.


Copernicus surface elevation is retrieved by `scripts/plot_topographic_catalog.py` from the public GLO-30 bucket. The raw GeoTIFF remains ignored. Derived map attribution:

produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018
provided under COPERNICUS by the European Union and ESA; all rights reserved

The organisations in charge of the Copernicus programme by law or by delegation do not incur any liability for any use of the Copernicus WorldDEM-30. See the source licence linked in `results/tables/topographic_map_execution.json`. Subsequent redistribution of this surface-elevation map must preserve these notices.
