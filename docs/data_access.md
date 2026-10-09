# Remaining data access

GitHub authentication is verified as maochuan-zhang-UW and the project is public at https://github.com/maochuan-zhang-UW/song2026-sierra-negra-reproduction. GitHub authentication does not authenticate either observation-data provider.

## Acquired and validated

The data drive holds the full Bell original catalog and GNSS baseline; all 219 located original events on June 26; the separate full VCH1 catalog (191 entries on the date); seven full-day three-component 8G station records; EC SN06 (complete) and SN02 (gapped); epoch response metadata; four PAYG days; the paper PDF, supplement, and cited velocity-model manuscript. Raw files remain outside Git. Checksums, coordinates, orientations, and common-component coverage are committed as small tables. SN02's common-component coverage is 79,636.67 seconds, or 92.172% of the day. The seven-station picker run has not been expanded to these EC records.

## GNSS observation files

The paper cites DOI 10.7283/3R4N-9775. GV03/GV09 DOI pages provide station coordinates and legacy download links, but the links redirect to a landing page rather than an observation file. Candidate daily RINEX paths for day 177 of 2018 are:

- https://data.earthscope.org/archive/gnss/rinex/obs/2018/177/gv031770.18d.Z
- https://data.earthscope.org/archive/gnss/rinex/obs/2018/177/gv091770.18d.Z

Historical unauthenticated requests returned login HTML. Authenticated retrieval now provides verified observations: GV09 has 2,880 epochs and GV03 has 1,431 at 30-second intervals. Detailed current validation is in `gnss_and_velocity.md`. A 200 response containing a login form is not a successful data download. These daily-file candidates are not established as the raw inputs to the paper's 30-second PPP time series.

EarthScope explicitly requires provider registration/login for this file server; see its [authentication documentation](https://www.earthscope.org/data/authentication/) and [GNSS file-server examples](https://www.unavco.org/data/gps-gnss/file-server/file-server-access-examples.html). Complete EarthScope authentication through its supported user or CLI/SDK workflow, then verify file listing and actual RINEX contents before processing. Keep tokens and cookies outside Git and do not put credentials into documentation or command logs. After acquisition, confirm the sample interval and epoch coverage and identify the required orbit/loading/tropospheric products. The archived scalar long-term baseline is not a substitute for high-rate positions.

## VCH1 and missing seismic stations

The public VCH1 original event catalog is acquired and checksum verified, but it contains neither waveform samples nor picks suitable for recreating the enhanced catalog. EarthScope all-network queries for VCH1 return no records. The [IGEPN waveform download portal](https://data.igepn.edu.ec/download/login2.php) presents a provider login form. VCH1 waveform access requires provider credentials or an independently located public deposit; no IGEPN account was created and no author/provider contact was sent.

All-channel June 26 requests return 404 for 8G SN01/SN03/SN08 and EC SN09/SN10. This is a query result, not evidence of permanent data loss. Fourteen station metadata entries are available, but only nine stations have acquired observation records. Distinguish metadata epochs from actual recording coverage.

Run `.venv/bin/python scripts/check_data_access.py` to repeat the public checks. It saves statuses and final host/path without authentication cookies or redirect parameters. `results/tables/access_recheck_20261009.json` records the latest checks. Broader network access is working; the remaining authentication requirements are provider-specific.

## Authenticated retry helper

The installed environment includes EarthScope CLI/SDK. `scripts/acquire_gnss.py --plan` lists the candidate daily files without logging in or downloading. The actual retry obtains an access token through the local CLI, never prints that token, rejects login HTML, and records download status separately from RINEX/PPP validation. EarthScope authentication is now available and successful downloads are decompressed, validated and independently processed.

```bash
source scripts/env.sh
.venv/bin/es login
.venv/bin/python scripts/acquire_gnss.py
```

The user completed this separate provider-account step. A compressed download, if obtained later, still requires decompression, RINEX-header checks, epoch/sample-interval validation, and scientifically specified PPP processing. The helper's status `downloaded_compressed_unparsed` explicitly means those checks remain outstanding.

VCH1 retrieval is skipped for the current analysis at the user's instruction. Independent PPP uses public ESA orbit/clock products and IGS20 antenna calibration; source hashes and URLs are in `results/tables/gnss_precise_products.json`.
