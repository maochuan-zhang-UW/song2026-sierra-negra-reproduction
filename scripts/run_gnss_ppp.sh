#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/env.sh
# First execute run_gnss_relative.sh to acquire observations/nav and build RTKLIB.
.venv/bin/python scripts/acquire_gnss_products.py
for station in gv03 gv09; do
    .cache/RTKLIB/app/rnx2rtkp/gcc/rnx2rtkp -k config/gnss_ppp.conf \
        -o "results/catalogs/${station}_ppp.pos" "data/raw/gnss/${station}1770.18o" \
        "data/raw/gnss/${station}1770.18n" \
        data/raw/gnss/ESA0MGNFIN_20181770000_01D_05M_ORB.sp3 \
        data/raw/gnss/ESA0MGNFIN_20181770000_01D_30S_CLK.clk
done
.venv/bin/python scripts/analyze_gnss_ppp.py
