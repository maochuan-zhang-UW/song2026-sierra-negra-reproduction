#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/env.sh
g++ -O3 -std=c++17 -shared -fPIC src/template_matching/correlation.cpp -o .cache/libcorrelation.so
