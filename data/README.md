# Data and provenance

The full Bell catalog and archived GNSS baseline were downloaded from Zenodo 4389190 and match their published MD5 values. Zenodo metadata establish CC-BY-4.0. Derived date-specific original-catalog facts are in `results/catalogs/original_20180626.csv`; these are not Song's enhanced catalog. The full source confirms the earlier 219-row browser recovery.

Raw data stay under `data/raw`, outside Git. Acquired files include 21 complete 100-Hz channels from seven 8G stations for 26 June 2018, response metadata, all four PAYG BHZ days in S5, PAYG response epochs, supplementary methods and the Rezaeifar velocity-model manuscript. Source hashes are recorded in `results/tables/raw_file_checksums.json`, station/coverage tables in adjacent CSVs. Use `scripts/acquire.py --help` to retrieve named files; download endpoints may require retries. EC station acquisition and GNSS PPP have not run.

The GNSS baseline is a long-term scalar series, not the paper's 30-second GV03/GV09 positions. Its time/measurement conventions need source verification before physical analysis. Neither unknown velocity layers nor missing waveforms are synthesized.

Original catalog schema: event_id; UTC origin_time; latitude/longitude in decimal degrees; source depth_catalog_km (datum unresolved); magnitude (original scale, not substituted Mw); source error fields (units unverified); RMS seconds; azimuth gap degrees; phase-pick count; provenance; UTC hour; phase. Counts are not completeness-corrected. There are no event FI or family columns because these were not measured.

Candidate phase picks from any Volpick execution require association and relocation before becoming earthquakes. Their timestamps and model probabilities must not be interpreted as an enhanced event catalog.
