#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/env.sh
revision=fb40407fb768cbdc23a11e27bc841f5d4a98abb7
if [ ! -d .cache/HypoDD/.git ]; then
  git init .cache/HypoDD
  git -C .cache/HypoDD remote add origin https://github.com/fwaldhauser/HypoDD.git
  git -C .cache/HypoDD fetch --depth 1 origin "$revision"
  git -C .cache/HypoDD checkout --detach FETCH_HEAD
fi
[ "$(git -C .cache/HypoDD rev-parse HEAD)" = "$revision" ]
make -C .cache/HypoDD/src/hypoDD FFLAGS='-O2 -I../../include -std=legacy -ffixed-line-length-none -mcmodel=medium' LDFLAGS='-mcmodel=medium'
