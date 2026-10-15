#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
git clone -b v1.2.0 --depth 1 --recurse-submodules https://github.com/dovecoteescapee/ByeDPIAndroid.git "$ROOT/upstream"
if [ "$(git -C "$ROOT/upstream" rev-parse HEAD)" != "9d289f096ed8373dd3734ab9966312c4c9e8d0aa" ]; then
  echo "Upstream revision mismatch" >&2
  exit 1
fi
git -C "$ROOT/upstream" submodule update --init --recursive
python3 "$ROOT/scripts/apply_port.py" --repo "$ROOT/upstream" --lists "$ROOT/profiles"
