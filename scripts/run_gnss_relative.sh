#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/env.sh
.venv/bin/python scripts/acquire_gnss.py
.venv/bin/python scripts/validate_gnss.py
.venv/bin/python scripts/acquire_gnss_navigation.py
if [ ! -d .cache/RTKLIB ]; then
    git clone https://github.com/tomojitakasu/RTKLIB.git .cache/RTKLIB
fi
git -C .cache/RTKLIB checkout 71db0ffa0d9735697c6adfd06fdf766d0e5ce807
make -C .cache/RTKLIB/app/rnx2rtkp/gcc -j8
.cache/RTKLIB/app/rnx2rtkp/gcc/rnx2rtkp -k config/gnss_relative.conf \
    -o results/catalogs/gv09_relative_gv03.pos \
    data/raw/gnss/gv091770.18o data/raw/gnss/gv031770.18o data/raw/gnss/gv031770.18n
.venv/bin/python scripts/analyze_gnss.py
