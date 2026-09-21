#!/usr/bin/env bash
# Aqua Florya elektrik maliyeti analizi — tam üretim zinciri.
set -euo pipefail
cd "$(dirname "$0")/.."
echo "── 1/4 grafikler"        && python3 tools/enerji_grafik.py
echo "── 2/4 rapor (1. geçiş)" && python3 tools/build_enerji_raporu.py
echo "── 3/4 denetim"          && python3 tools/denetim_enerji.py
echo "── 4/4 rapor (2. geçiş — denetim sonucu dahil)" \
                               && python3 tools/build_enerji_raporu.py
python3 tools/denetim_enerji.py
