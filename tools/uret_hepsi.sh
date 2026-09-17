#!/usr/bin/env bash
# TÜM ÇIKTILARI SIFIRDAN ÜRET — tek kaynak (tools/proj.py) → tüm paftalar ve tablolar.
set -e
cd "$(dirname "$0")/.."
echo "── güzergâh motorları ──────────────────────────────────────────────"
python3 tools/kanal_yollari.py
python3 tools/linye_yollari.py | head -2
echo "── PDF paftalar ────────────────────────────────────────────────────"
for m in build_a3 build_slides build_mimari build_mekanik build_elektrik \
         build_tekhat build_insaat_seti; do
  python3 tools/$m.py
done
echo "── tablolar ────────────────────────────────────────────────────────"
for m in build_boq build_boq_mep build_kesif build_hakedis build_butce \
         build_pano_cetveli; do
  python3 tools/$m.py
done
echo "── CAD ─────────────────────────────────────────────────────────────"
python3 tools/build_dxf.py | tail -4
echo "── model ve paket ──────────────────────────────────────────────────"
python3 tools/build_single_html.py
python3 tools/build_paket.py | tail -3
echo "── denetim ─────────────────────────────────────────────────────────"
python3 tools/kontrol.py | tail -5 || true
python3 tools/qa.py | tail -8 || true
python3 tools/agents/denetim.py 2>&1 | tail -6
