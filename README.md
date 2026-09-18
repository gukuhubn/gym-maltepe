# Maltepe / İdealtepe — Mobilya Mağazası → Fonksiyonel Antrenman Stüdyosu

Ön tasarım, uygulama projesi ve bütçe paketi · **Rev H** · 18 Eylül 2026

## Teslimatlar (`output/`)

> **Tek dosya teslim:** `GYM_MALTEPE_UYGULAMA_PROJESI.pdf` — 27 pafta.
> Mimari (A-01…05) · mekanik (M-01…04) · elektrik (E-01…05) A1 1:50 planlar
> + ADP çok hatlı şema seti (ADP-01…12) A3. Diğer dosyalar bu setin
> parçaları ve yardımcı tablolarıdır.

| Dosya | İçerik |
|---|---|
| `Gym_Insaat_Seti_A3.pdf` | **İnşaat uygulama seti** — kapak + indeks + mimari 14 + mekanik 9 + elektrik 8 = 33 pafta, PDF yer imli |
| `Gym_Mimari_Proje_A3.pdf` | Mimari uygulama projesi — A3 yatay, 14 pafta (A-14 duvar tipleri 1/5 yatay kesit) |
| `Gym_Mekanik_Proje_A3.pdf` | Mekanik tesisat projesi — A3 yatay, 9 pafta (havalandırma prensip, sıhhi kolon şeması ve iklimlendirme prensip şemaları **ayrı paftalarda**) |
| `Gym_Elektrik_Proje_A3.pdf` | Elektrik projesi — A3 yatay, 8 pafta (E-08 topraklama ve potansiyel dengeleme planı dâhil) |
| `Gym_ADP_Sema_A3.pdf` | **ADP çok hatlı şema seti** — 12 pafta A3: kapak, pano karakteristiği (IEC 61439), sembol listesi, ana besleme, 4 şematik diyagram, klemens planı, pano önden görünüş, yükleme cetveli, malzeme listesi |
| `Gym_Denetim_Raporu.pdf` | **Otomatik denetim raporu** — 6 kontrol ajanının bulguları, dayanak standartlarıyla |
| `Gym_Donusum_Dosyasi_A3.pdf` | Yatırım / fizibilite dosyası — A3 yatay, 12 sayfa |
| `Gym_Sunum_16x9.pdf` | Sunum — 16:9, 12 slayt |
| `Gym_Proje_Paketi.zip` | **TEK TESLİM DOSYASI** — 7 klasör, 39 dosya, 24,4 MB. Tüm paftalar, CAD seti, tablolar, model, renderlar ve denetim raporu içindedir. |
| `Gym_Kesif_Ozeti_BoQ.xlsx` | **Keşif özeti + metraj cetvelleri** — 61 mimari poz, malzeme/işçilik/genel gider/kâr ayrık, 160 metraj satırı (minha dâhil) |
| `Gym_Hakedis_Sablonu.xlsx` | **Hakediş şablonu** — kapak, icmal, poz bazlı gerçekleşme, kesinti ve avans, ödeme takibi |
| `Gym_Butce_Takip.xlsx` | **Bütçe takibi** — 22 iş kalemi, sözleşme/ödenen/kalan, sapma, nakit akışı |
| `Gym_Pano_Yukleme_Cetveli.xlsx` | **ADP pano yükleme cetveli** — çift dilli, faz bazlı, diversiteli; gerilim düşümü sayfası |
| `Gym_Maliyet_BoQ.xlsx` | Poz bazlı BoQ — 111 poz, senaryolu, birim fiyat sütunu boş, formüller canlı |
| `Gym_Mekanik_BoQ.xlsx` | Mekanik BoQ — 37 poz |
| `Gym_Elektrik_BoQ.xlsx` | Elektrik BoQ — 36 poz |
| `Gym_CAD_Seti_DXF.zip` | **CAD seti** — 4 birleşik DXF R2010 **+ 15 tekil pafta dosyası** (`paftalar/`), A1 · ISO 5457 çerçeve · ISO 7200 antet, 70 katman, katman listesi, okuma notu |
| `Gym_CAD_Paftalar.pdf` | CAD paftalarının önizlemesi — **15 pafta, A1**, her biri kendi bağımsız DXF dosyasından basılır |
| `Gym_Model.html` | Tek dosya offline 3B model + render galerisi |
| `Render_Promptlari.md` | Render prompt seti |
| `render/*.png` | 8 fotogerçekçi render (4 açı × 2 stil) |

Varsayımlar, doğrulanacaklar ve işverenden istenecekler: **`BUILD_NOTES.md`**

## Yeniden üretim

```bash
pip install reportlab openpyxl pillow pypdfium2 opencv-python-headless shapely numpy ezdxf matplotlib
bash tools/uret_hepsi.sh              # TÜM çıktıları sıfırdan üretir (aşağıdaki sıra)

python3 tools/build_geometry.py       # raster pafta → ölçekli geometri
python3 tools/kanal_yollari.py        # hava kanalı ortogonal güzergâhları → data/kanallar.json
python3 tools/linye_yollari.py        # elektrik linye ortogonal güzergâhları → data/yollar.json
python3 tools/build_a3.py             # ana dosya
python3 tools/build_slides.py         # sunum
python3 tools/build_boq.py            # ana BoQ
python3 tools/build_mimari.py         # mimari uygulama seti (14 pafta)
python3 tools/build_mekanik.py        # mekanik proje
python3 tools/build_elektrik.py       # elektrik projesi (8 pafta, topraklama dâhil)
python3 tools/build_tekhat.py         # ADP tek hat şeması PDF (8 pafta, IEC 60617 / 61439)
#                                       CAD karşılığı: build_dxf.py içinde pafta E-06
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
python3 tools/agents/denetim.py       # DENETİM AJANLARI — 6 ajan, konsol + JSON + PDF rapor
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


## Denetim ajanları

Proje, altı bağımsız kontrol ajanı tarafından otomatik denetlenir. Her ajan
kendi mevzuat/standart kümesine göre çalışır ve `HATA / UYARI / BİLGİ`
seviyesinde bulgu üretir; bir tek hata bile genel sonucu **RED** yapar.

| Ajan | Kapsam | Başlıca dayanaklar |
|---|---|---|
| `mimari` | mahal–tip tutarlılığı, kot dizgesi, katman toplamları, asma tavan istifi, doğrama genişlikleri, kaçış mesafesi, alçıpan karkas (dikme aralığı, profil varlığı), ıslak hacim | Planlı Alanlar İmar Yön. md.28 · BYKHY md.32–33 · TS EN 520 / TS EN 14195 · TS EN 14891 |
| `mekanik` | kanal en/boy oranı ve hız, debi dengesi, kişi başı taze hava, ıslak hacim egzozu, menfez boyun hızı, klima yükü, bakır hat ve drenaj uzunluğu, atık su eğimi, sıcak su kapasitesi, kanal ortogonalliği | TS 3419 · TS 2164 · TS EN 16798-1 · BYKHY |
| `elektrik` | iletken kesitleri, linye başına sorti sayısı, Ib ≤ In ≤ Iz, gerilim düşümü, faz dengesi, **çapraz güzergâh denetimi**, tek hat ↔ yükleme cetveli tutarlılığı, ıslak hacim RCD kuralları | Elektrik İç Tesisleri Yönetmeliği · TS HD 60364-4-41/-5-52/-7-701 |
| `standart` | katman adlandırma ve disiplin ön eki, ISO 128 kalem serisi, ISO 3098 yazı serisi, pafta boyutu (TS EN ISO 216), antet zorunlu alanları, **her paftanın ayrı dosya olması** | ISO 128 · ISO 3098 / TS 88 · TS EN ISO 216 / 5457 · ÇŞB CADD · TMMOB MMO |
| `koordinasyon` | `kontrol.py` geometrik denetimini kapsar; servisler arası asgari açıklık, kablo tavası erişim boşluğu, armatür–menfez–dedektör mesafeleri, ıslak hacim bölge kuralları, ekipman sınırı | MEP koordinasyon pratiği · TS EN 54-14 · TS HD 60364-7-701 |
| `teslim` | beklenen 19 çıktının varlığı, pafta/sayfa sayısı, tekil DXF pafta sayısı, render sayısı, sürüm | teslim şartnamesi |

```bash
python3 tools/agents/denetim.py             # tümü + PDF rapor
python3 tools/agents/denetim.py elektrik    # tek ajan
```

Çıktılar: konsol özeti, `data/denetim.json`, `output/Gym_Denetim_Raporu.pdf`.

## Tesisat güzergâhı kuralı — çapraz hat yoktur

Elektrik linyeleri, zayıf akım hatları ve hava kanalları elle çizilmez.
`tools/yol.py` içindeki 10 cm çözünürlüklü ızgara üzerinde, **yalnız dört komşulu**
(yatay/düşey) A\* algoritmasıyla üretilir — çapraz segment üretmek geometrik
olarak imkânsızdır. Bölme duvarları engel, kapı boşlukları geçittir; duvar
çeperine yakın güzergâh ödüllendirilir, böylece hat oda ortasından geçmez.

* `tools/linye_yollari.py` → 22 linye + 7 anahtar sortisi, 450,8 m, **0 çapraz segment**
* `tools/kanal_yollari.py` → 3 ana kanal hattı, 42,3 m, **0 çapraz segment**

Sonuçlar `data/yollar.json` ve `data/kanallar.json` içinde saklanır; hem PDF
paftalar hem DXF aynı veriyi okur. `elektrik` ajanı her derlemede bu dosyaları
yeniden tarar ve tek bir çapraz segment bulursa **HATA** verir.


## Pafta motoru — `tools/pafta.py`

Her pafta tek bir motordan çıkar; set içi tutarlılık böyle sağlanır.

* **TS EN ISO 5457** — A1 (841×594), çizim alanı 811×574, sol cilt payı 20 mm,
  diğer kenarlar 10 mm, çerçeve 0,70 mm; kenar ızgarası (bölge referansı,
  16×12), merkezleme ve yön işaretleri, 100 mm metrik referans cetveli,
  alt kenarda kâğıt boyutu tanımı.
* **TS EN ISO 7200** — 180×92 mm antet: işveren, proje, yapı/mahal, disiplin,
  pafta adı ve üst başlığı, proje müellifi + oda sicil no, çizen/kontrol/onay,
  tarih, ölçek, birim, durum, pafta no, revizyon, sonraki pafta.
* Revizyon tablosu, anahtar plan, kuzey oku, grafik ölçek çubuğu, durum damgası
  ve "ölçü alınmaz" notu otomatik yerleşir.
* Görüntü penceresi **tam ölçeklidir**: `view_height = pencere_yüksekliği × ölçek`.
  Pencereler `plot = 0` olan `G-VIEWPORT` katmanındadır, çerçeveleri basılmaz.

## Aks sistemi — `tools/aks.py`

Yapı kuzeye göre **8,0° dönüktür**; aks sistemi kuzeye değil **yapının kendi
doğrultusuna** kurulur. Motor çeper duvarlarının baskın doğrultusunu uzunluk
ağırlıklı bulur, paralel/dik hatları 0,40 m toleransla kümeler ve 1,60 m'yi
aşan kümeleri aks kabul eder → **4 rakam aksı (1–4) + 5 harf aksı (A–E)**.
Akslar arası ve toplam zincir ölçüler gerçek `DIMENSION` varlığı olarak basılır.

## Çok hatlı şema CAD'de — `tools/sema.py` + `tools/build_sema.py`

Türkiye'de pano dokümantasyonunun fiilî standardı tek hat şeması değil,
**çok hatlı şematik diyagramdır**: **L1 · L2 · L3 · N** potansiyel rayları
sayfanın üstünde ayrı ayrı çizilir ve her linye kendi fazından bir bağlantı
noktasıyla ayrılır — hangi linyenin hangi fazda olduğu çizimden okunur.

* A3 sayfa, 0–7 sütun / A–F satır ızgarası, sayfalar arası `sayfa.sütun`
  referansı
* Kaçak akım rölesi grubun ilk sütununda, altında **grup alt rayları**
  (4 kutuplu rölede L1/L2/L3/N)
* Terminal numaralı koruma cihazı + `-F1 / 10 A / 1P B / 6kA` yazımı
* Tel numarası (EN 60204-1), `-X1` klemens sırası, kablo etiketi,
  kesikli saha cihazı bloğu, Türkçe yük tanımı
* EPLAN düzeninde çift dilli antet
* **Kesici eğrisi:** aydınlatmada B, priz/klima/ısıtıcıda C — tümü 6 kA
* **Ana kaçak akım** ana şalterle orantılıdır: 4×32 A → **4×40 A / 300 mA
  S tipi**, ana şalterin hemen altında
* **Yedek linyeler dâhil** tüm son devreler 30 mA röle arkasındadır

### Eski tek hat şeması (kaldırıldı)

Şema ölçeksiz olduğu için **kâğıt alanına 1:1 milimetre** çizilir. Semboller
**IEC 60617 modülü M = 2,5 mm** üzerine kurulur; her güç sembolü tek kutup
anahtarından türer (× devre kesici, — ayırıcı). Yerleşim kuralı:
**bir çıkış = bir sütun = bir tablo kolonu**, `x_n = X0 + (n−0,5)×26 mm`.
Üç hatlı bara (L1·L2·L3 / N / PE), kaçak akım grupları için alt bara + köşeli
parantez, kesik-nokta pano sınırı, klemens sırası `-X1`, 14 satırlık veri
matrisi ve faz dengesi / güç özeti / hesaplar / notlar blokları.
Cihaz etiketleri **IEC 81346-2**'ye göredir (`-Q1`, `-F0`, `-F1…-F5`,
`-Q101…-Q126`, `-X1`, `-P1`).
