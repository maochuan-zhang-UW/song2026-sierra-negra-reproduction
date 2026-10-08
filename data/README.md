# Data

Derived original-catalog facts are in `results/catalogs/original_20180626.csv`, attributed to Bell et al. (2021) and Zenodo 4389190. This is not the enhanced Song catalog. The locally recovered raw subset is ignored; consecutive browser source rows 348–566 cover June 26. Complete file download/checksum verification awaits connectivity. Do not label the subset SHA-256 as the archive checksum.

`python3 scripts/acquire.py` retrieves the original event list, a GNSS baseline, paper, supplement, and response metadata when reachable. `scripts/acquire_waveforms.py` uses ObsPy and hour-long 8G requests. EC data need provider access. GNSS RINEX access/PPP are not implemented. Raw files live under `data/raw`, outside Git. The public archive license should be verified before raw redistribution.

Catalog schema: event_id; UTC origin_time; latitude/longitude in decimal degrees; source depth_catalog_km (datum unresolved); magnitude (original scale, not substituted Mw); source error fields (units unverified); RMS seconds; azimuth gap degrees; phase-pick count; provenance; UTC hour; phase. Phase durations and raw event counts are reported without completeness correction. There are no FI or family columns because those were not measured.
