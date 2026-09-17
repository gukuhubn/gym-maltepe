# Maltepe / İdealtepe — Mobilya Mağazası → Fonksiyonel Antrenman Stüdyosu

Ön tasarım, uygulama projesi ve bütçe paketi · **Rev E** · 17 Eylül 2026

## Teslimatlar (`output/`)

| Dosya | İçerik |
|---|---|
| `Gym_Insaat_Seti_A3.pdf` | **İnşaat uygulama seti** — kapak + indeks + mimari 13 + mekanik 7 + elektrik 7 = 29 pafta, PDF yer imli |
| `Gym_Mimari_Proje_A3.pdf` | Mimari uygulama projesi — A3 yatay, 13 pafta |
| `Gym_Mekanik_Proje_A3.pdf` | Mekanik tesisat projesi — A3 yatay, 7 pafta |
| `Gym_Elektrik_Proje_A3.pdf` | Elektrik projesi — A3 yatay, 7 pafta |
| `Gym_Donusum_Dosyasi_A3.pdf` | Yatırım / fizibilite dosyası — A3 yatay, 12 sayfa |
| `Gym_Sunum_16x9.pdf` | Sunum — 16:9, 12 slayt |
| `Gym_Proje_Paketi.zip` | **Teslim paketi** — disiplin klasörleri, referans dosya adı kodlaması, 21 dosya |
| `Gym_Kesif_Ozeti_BoQ.xlsx` | **Keşif özeti + metraj cetvelleri** — 61 mimari poz, malzeme/işçilik/genel gider/kâr ayrık, 160 metraj satırı (minha dâhil) |
| `Gym_Hakedis_Sablonu.xlsx` | **Hakediş şablonu** — kapak, icmal, poz bazlı gerçekleşme, kesinti ve avans, ödeme takibi |
| `Gym_Butce_Takip.xlsx` | **Bütçe takibi** — 22 iş kalemi, sözleşme/ödenen/kalan, sapma, nakit akışı |
| `Gym_Pano_Yukleme_Cetveli.xlsx` | **ADP pano yükleme cetveli** — çift dilli, faz bazlı, diversiteli; gerilim düşümü sayfası |
| `Gym_Maliyet_BoQ.xlsx` | Poz bazlı BoQ — 111 poz, senaryolu, birim fiyat sütunu boş, formüller canlı |
| `Gym_Mekanik_BoQ.xlsx` | Mekanik BoQ — 37 poz |
| `Gym_Elektrik_BoQ.xlsx` | Elektrik BoQ — 36 poz |
| `Gym_CAD_Seti_DXF.zip` | **CAD seti** — 4 × DXF R2010 (mimari 5 + mekanik 4 + elektrik 4 + birleşik 13 pafta), katman listesi, okuma notu |
| `Gym_CAD_Paftalar.pdf` | CAD paftalarının önizlemesi (13 pafta) |
| `Gym_Model.html` | Tek dosya offline 3B model + render galerisi |
| `Render_Promptlari.md` | Render prompt seti |
| `render/*.png` | 8 fotogerçekçi render (4 açı × 2 stil) |

Varsayımlar, doğrulanacaklar ve işverenden istenecekler: **`BUILD_NOTES.md`**

## Yeniden üretim

```bash
pip install reportlab openpyxl pillow pypdfium2 opencv-python-headless shapely numpy ezdxf matplotlib
python3 tools/build_geometry.py       # raster pafta → ölçekli geometri
python3 tools/build_a3.py             # ana dosya
python3 tools/build_slides.py         # sunum
python3 tools/build_boq.py            # ana BoQ
python3 tools/build_mimari.py         # mimari uygulama seti (13 pafta)
python3 tools/build_mekanik.py        # mekanik proje
python3 tools/build_elektrik.py       # elektrik projesi
python3 tools/build_boq_mep.py        # disiplin BoQ'ları
python3 tools/build_dxf.py            # DXF CAD seti + önizleme + zip
python3 tools/build_insaat_seti.py    # birleşik inşaat seti (yer imli tek PDF)
python3 tools/metraj.py               # metraj cetvelleri (geometriden türer)
python3 tools/fiyat.py                # birim fiyat tablosu — referansla kalibre
python3 tools/build_kesif.py          # keşif özeti + metraj .xlsx
python3 tools/build_hakedis.py        # hakediş şablonu .xlsx
python3 tools/build_butce.py          # bütçe takibi + nakit akışı .xlsx
python3 tools/build_pano_cetveli.py   # ADP pano yükleme cetveli .xlsx
python3 tools/build_paket.py          # disiplin klasörlü teslim paketi .zip
python3 tools/kontrol.py              # çizim kontrolü (çakışma, kot, yük, kaçış)
python3 tools/export_dimensions.py    # 3B model verisi
node     tools/shoot.js . work/model  # Three.js → PNG (Playwright)
python3 tools/render_gemini.py        # image-to-image render
python3 tools/render_altyazi.py       # zorunlu altyazı şeridi
python3 tools/build_promptlar.py
python3 tools/build_single_html.py
python3 tools/qa.py                   # QA protokolü
```

Tüm m², metraj ve TL değerleri **`tools/proj.py`** içindedir — tek kaynak.
Metraj cetvelleri `tools/metraj.py` ile geometriden türer; birim fiyatlar
`tools/fiyat.py` içinde ve işverenin Aqua Florya / Saltbae referans projesinin
gerçekleşen sözleşme fiyatlarıyla kalibre edilmiştir.
Bir sayıyı değiştirmek için yalnızca o dosya düzenlenir; tüm çıktılar yeniden üretilir.

> Ön tasarım — yerinde doğrulanmadan ve ruhsat alınmadan uygulama yapılamaz.
