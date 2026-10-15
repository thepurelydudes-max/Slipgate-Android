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
git clone https://github.com/crim50n/tg-ws-proxy-android.git "$ROOT/telegram-upstream"
git -C "$ROOT/telegram-upstream" checkout --detach 41f4d4ff9a5f14c5ffbc5b9a4662099cd11c7738
test "$(git -C "$ROOT/telegram-upstream" rev-parse HEAD)" = "41f4d4ff9a5f14c5ffbc5b9a4662099cd11c7738"
python3 "$ROOT/scripts/integrate_telegram.py" --android "$DEST" --telegram "$ROOT/telegram-upstream"
python3 "$ROOT/scripts/add_dpi_modes.py" --android "$DEST"
python3 "$ROOT/scripts/fix_quick_tile.py" --android "$DEST" --telegram "$ROOT/telegram-upstream"
python3 "$ROOT/scripts/add_hybrid.py" --android "$DEST" --root "$ROOT"
