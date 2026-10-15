#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/upstream"
git clone -b v.1.8.2 --depth 1 --recurse-submodules https://github.com/romanvht/ByeByeDPI.git "$DEST"
if [ "$(git -C "$DEST" rev-parse HEAD)" != "96a3c1ff555043d915af814aa4f0e9a572c89aba" ]; then
  echo "Incorrect pinned ByeByeDPI commit" >&2
  exit 1
fi
git -C "$DEST" submodule update --init --recursive
python3 "$ROOT/scripts/apply_port_v2.py" --repo "$DEST" --lists "$ROOT/profiles"
