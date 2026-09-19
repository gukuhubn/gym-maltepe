#!/usr/bin/env bash
# TÜM ÇIKTILARI SIFIRDAN ÜRET — tek kaynak (tools/proj.py) → tüm paftalar ve tablolar.
set -e
set -o pipefail   # borulu adımlarda gerçek hata gizlenmesin
cd "$(dirname "$0")/.."
echo "── ölçülmüş rölöve → geometri ──────────────────────────────────────"
python3 tools/roleve.py | tail -6
python3 -c "import sys;sys.path.insert(0,'tools');import roleve;d,y=roleve.geometri_dosyasi();print('  → data/geometry_roleve.json  uyum %'+str(d['kayit']['uyum_yuzde']))"
echo "── güzergâh motorları ──────────────────────────────────────────────"
python3 tools/kanal_yollari.py
python3 tools/linye_yollari.py | head -2
echo "── PDF paftalar ────────────────────────────────────────────────────"
for m in build_a3 build_slides build_mimari build_mekanik build_elektrik \
         build_insaat_seti; do
  python3 tools/$m.py
done
echo "── tablolar ────────────────────────────────────────────────────────"
for m in build_boq build_boq_mep build_kesif build_hakedis build_butce \
         build_pano_cetveli; do
  python3 tools/$m.py
done
echo "── CAD ─────────────────────────────────────────────────────────────"
python3 tools/build_dxf.py 2>&1 | tail -4
python3 tools/build_sema.py
echo "── PİLOT BÖLGE (ölçülü plan · tavan · kesit · görünüş · detay) ─────"
python3 tools/pilot.py
echo "── KAYNAK ENVANTERİ (talimat §3) ───────────────────────────────────"
python3 tools/kaynak.py | head -9
echo "── AUTOCAD DOĞRULAMA KİTİ ──────────────────────────────────────────"
python3 tools/autocad_kit.py | tail -3
echo "── PİLOT RAPORU (talimat §13) ──────────────────────────────────────"
python3 tools/build_pilot_raporu.py
echo "── REVİZYON DENEYİ ─────────────────────────────────────────────────"
python3 tools/revizyon.py --bolme 125 | tail -6
echo "── TEK DOSYA TESLİM ────────────────────────────────────────────────"
python3 tools/build_tek_dosya.py
echo "── model ve paket ──────────────────────────────────────────────────"
python3 tools/build_single_html.py
python3 tools/build_paket.py | tail -3
echo "── denetim ─────────────────────────────────────────────────────────"
python3 tools/kontrol.py | tail -5 || true
python3 tools/qa.py | tail -8 || true
python3 tools/agents/denetim.py 2>&1 | tail -6
