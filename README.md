# Maltepe / İdealtepe — Mobilya Mağazası → Fonksiyonel Antrenman Stüdyosu

Ön tasarım ve yatırım dosyası · **Rev C** · 13 Eylül 2026

## Teslimatlar (`output/`)

| Dosya | İçerik |
|---|---|
| `Gym_Donusum_Dosyasi_A3.pdf` | Ana dosya — A3 yatay, 12 sayfa |
| `Gym_Sunum_16x9.pdf` | Sunum — 16:9, 12 slayt |
| `Gym_Maliyet_BoQ.xlsx` | Ana BoQ — 106 poz, birim fiyat sütunu boş, formüller canlı |
| `Gym_Mekanik_Proje_A3.pdf` | Mekanik tesisat projesi — A3 yatay, 6 pafta |
| `Gym_Mekanik_BoQ.xlsx` | Mekanik BoQ — 37 poz |
| `Gym_Elektrik_Proje_A3.pdf` | Elektrik projesi — A3 yatay, 6 pafta |
| `Gym_Elektrik_BoQ.xlsx` | Elektrik BoQ — 36 poz |
| `Gym_Model.html` | Tek dosya offline 3B model + render galerisi |
| `Render_Promptlari.md` | Render prompt seti |
| `render/*.png` | 8 fotogerçekçi render (4 açı × 2 stil) |

Varsayımlar, doğrulanacaklar ve işverenden istenecekler: **`BUILD_NOTES.md`**

## Yeniden üretim

```bash
pip install reportlab openpyxl pillow pypdfium2 opencv-python-headless shapely numpy
python3 tools/build_geometry.py       # raster pafta → ölçekli geometri
python3 tools/build_a3.py             # ana dosya
python3 tools/build_slides.py         # sunum
python3 tools/build_boq.py            # ana BoQ
python3 tools/build_mekanik.py        # mekanik proje
python3 tools/build_elektrik.py       # elektrik projesi
python3 tools/build_boq_mep.py        # disiplin BoQ'ları
python3 tools/export_dimensions.py    # 3B model verisi
node     tools/shoot.js . work/model  # Three.js → PNG (Playwright)
python3 tools/render_gemini.py        # image-to-image render
python3 tools/render_altyazi.py       # zorunlu altyazı şeridi
python3 tools/build_promptlar.py
python3 tools/build_single_html.py
python3 tools/qa.py                   # QA protokolü
```

Tüm m², metraj ve TL değerleri **`tools/proj.py`** içindedir — tek kaynak.
Bir sayıyı değiştirmek için yalnızca o dosya düzenlenir; tüm çıktılar yeniden üretilir.

> Ön tasarım — yerinde doğrulanmadan ve ruhsat alınmadan uygulama yapılamaz.
