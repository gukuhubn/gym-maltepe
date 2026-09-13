# BUILD NOTES — Maltepe / İdealtepe Gym Dönüşümü

**MALTEPE / İDEALTEPE — MOBİLYA MAĞAZASI → FONKSİYONEL ANTRENMAN STÜDYOSU**
Rev A · 13 Eylül 2026 · fiyat referansı **Eylül 2026 piyasa mertebesi**

---

## 1 · Teslimatlar

| Dosya | İçerik |
|---|---|
| `output/Gym_Donusum_Dosyasi_A3.pdf` | Ana dosya — A3 yatay, 12 sayfa |
| `output/Gym_Sunum_16x9.pdf` | Sunum — 16:9, 12 slayt, büyük punto |
| `output/Gym_Maliyet_BoQ.xlsx` | BoQ — 4 sayfa, 46 poz, birim fiyat sütunu boş, formüller canlı |
| `output/render/*.png` | 8 fotogerçekçi render (4 açı × 2 stil varyantı) |
| `output/Gym_Model.html` | Tek dosya offline 3B model + render galerisi |
| `output/Render_Promptlari.md` | Prompt seti — harici modelde yeniden üretim için |

Üretim zinciri: `tools/build_geometry.py` → `tools/proj.py` (tek kaynak) →
`build_a3.py` · `build_slides.py` · `build_boq.py` · `export_dimensions.py` →
`shoot.js` (Three.js → PNG) → `render_gemini.py` (image-to-image) →
`build_single_html.py` → `qa.py`.

**Tek kaynak ilkesi:** tüm m², metraj, TL ve hesap değerleri `tools/proj.py` içindedir.
Bir sayıyı değiştirmek için yalnızca o dosya düzenlenir; PDF, sunum, BoQ ve 3B model
kendiliğinden güncellenir. `tools/qa.py` bu tutarlılığı her derlemede doğrular.

---

## 2 · Girdilerle ilgili engeller ve nasıl aşıldı

**DWG okunamadı.** `ESAT-FINAL.dwg` AutoCAD 2018 (**AC1032**) formatındadır. Ortamda
LibreDWG / `dwg2dxf` / ODA File Converter bulunmamaktadır ve paket depolarından da
kurulamamıştır. *(İki DWG dosyası bit bazında aynıdır — md5 `a05b59e5…` — yani
`ESAT-FINAL (1).dwg` bir kopyadır.)*

**PDF paftaları vektör değil.** Her iki pafta da tek sayfalık A3 dosyalardır ve içerikleri
**JPEG raster** görüntüdür (PDF'te font nesnesi yok, `/DCTDecode` var; metin katmanı sıfır
karakter). Dolayısıyla ne metin ne de çizgi geometrisi doğrudan okunabilmiştir.

**Uygulanan yöntem.** Alan Dağılımı paftası 400 DPI'da raster'a çevrildi; gri / mavi / pembe
dolgu alanları renk maskesiyle ayrıştırıldı, kontur izleme ve Douglas–Peucker ile
sadeleştirildi, ardından **paftanın kendi m² etiketleriyle kalibre edildi**
(87,05 + 8,24 + 8,49 m²). Üç bölgede piksel/m² sapması **%3'ün altındadır**; ölçek
`data/geometry.json` içinde `olcek_m_per_px` olarak saklanır. Güney cephe kenarı yataya
döndürülerek ortak bir koordinat çerçevesi kuruldu.

> **Her metrajın yanında geçerli olan not:** *PDF'den ölçeklendirildi, ±%3 — yerinde
> doğrulanacak.* Uygulama projesi için işverenden **DXF (R2010) export** istenmelidir.

**Render hattı.** Gemini API bu ortamdan erişilebilirdi (`gemini-3-pro-image`).
Brief §7.B uygulandı: `site/` altındaki vendored Three.js kütle modelinden dört sabit
kamera açısı PNG olarak alındı (Playwright + Chromium), bu PNG'ler **image-to-image**
girdisi yapılarak fotogerçekçileştirildi. Böylece geometri plana sadık kaldı.
Brief §7.A (gerçek ÖNCE/SONRA çiftleri) **atlandı** — işverenden mevcut durum fotoğrafı
gelmedi. Fotoğraflar geldiğinde yöntem `output/Render_Promptlari.md` §5'te tariflidir.

---

## 3 · Çalışılan varsayımlar

Aşağıdaki değerler **ölçülmemiştir**. Hepsi `tools/proj.py` içinde tek bir sözlükte
(`V`) tutulur ve parametriktir; değeri değiştirmek tüm çıktıları günceller.

| # | Varsayım | Kabul edilen değer | Etkilediği hesap | Yanılırsa ne olur |
|---|---|---|---|---|
| V1 | Tavan yüksekliği | **3,20 m** | Duvar m², iç hacim, taze hava debisi, armatür adedi | 2,80 m → armatür artar; 2,50 m altı → tescil riski |
| V2 | Üst katta konut var | **Var (konservatif)** | Titreşim matı (poz 04.02) | Yoksa ~7.700–13.400 TL bütçeden düşer |
| V3 | Mevcut pis su kotu | **Bilinmiyor** | Seçenek A / B kararı | A yerine B → +57.780 / +104.578 TL |
| V4 | Elektrik pano gücü / trifaze | **Bilinmiyor** | Abonelik ve takvim | Yetersizse güç artırımı 3–8 hafta |
| V5 | Doğalgaz bağlantısı | **Yok varsayıldı** | Sıcak su elektrikli (poz 03.07) | Varsa kombi daha ekonomik |
| V6 | Eşzamanlı kapasite | **12 sporcu + 2 personel** | Taze hava, soğutma, dolap adedi, lux | Kapasite artarsa mekanik yeniden boyutlanır |
| V7 | Aylık kira | **28.000–52.000 TL** | Yalnızca açılış öncesi nakit tablosu | Sözleşme işverendedir, gerçek değerle değiştirilmeli |
| V8 | Kolon konumları | **Paftada okunamadı** | Ekipman yerleşimi, köşe kaplama metrajı | Yerinde tespitle revize edilir |
| V9 | Geometri doğruluğu | **±%3** | Tüm metrajlar | DXF gelince kesinleşir |
| V10 | Ana giriş batı cephede | Duvar planındaki mavi doğramadan | Sirkülasyon, banko konumu | Giriş farklıysa banko yeri değişir |

**Taze hava kriteri:** kişi başı 55 m³/h ile saatte 3 hava değişimi kriterlerinden büyüğü
alınmıştır → 1000 m³/h (71 m³/h·kişi; yasal asgari 30).

**Fiyatlar:** Eylül 2026 piyasa mertebesi. Tek m² fiyatı kullanılmamış, 46 poz kalem bazlı
kurulmuştur. Götürü kalemler (pano, yangın algılama, havalandırma seti, tabela, tesisat)
alandan büyük ölçüde bağımsızdır ve bu 103.78 m²'lik birimde imalat bedelinin
yaklaşık %40'ını oluşturur — TL/m² değerinin konut yenilemesi çıpalarının üzerinde
çıkmasının başlıca nedeni budur.

---

## 4 · Doğrulanacaklar listesi (ölçüm günü)

- [ ] Tavan yüksekliği — salon ve ıslak hacim ayrı ayrı
- [ ] Mevcut pis su bağlantısının kotu ve konumu (kroki + fotoğraf)
- [ ] Elektrik pano gücü, trifaze var mı, sayaç konumu
- [ ] Doğalgaz bağlantısı var mı
- [ ] Üst katta konut var mı; bina kaç bağımsız bölüm
- [ ] Kolon sayısı, kesiti ve konumu
- [ ] Cephe doğrama genişliği, kapı açıklıkları, giriş eşiği kot farkı
- [ ] Zemin yük kapasitesi (serbest ağırlık alanı için)
- [ ] Mevcut aydınlatma ve zayıf akım altyapısı

---

## 5 · İşverenden istenecekler

1. **DXF export (AutoCAD R2010)** — geometrinin ±%3 belirsizliğini sıfırlar
2. **Mevcut durum fotoğrafları** — ana salon, giriş/banko, soyunma koridoru
   (gerçek ÖNCE/SONRA render çiftleri için zorunlu)
3. **Ölçülmüş net m² ve tavan yüksekliği**
4. **Satın alınan ekipman listesi** — marka / model / ölçü / ağırlık
5. **Pis su bağlantısı fotoğrafı ve kotu**
6. **Elektrik pano gücü ve trifaze durumu**
7. **Tapu bağımsız bölüm niteliği ve yapı kullanma izni (iskân)**
8. **Bina bağımsız mı; değilse yönetim planı ve kat malikleri durumu**
9. **Hedeflenen açılış tarihi ve üye kapasitesi**
10. **Kira sözleşmesi** — ruhsat alınamaması hâlinde fesih/indirim maddesi var mı

---

## 6 · Özet rakamlar

| | |
|---|---|
| Net iç kullanım alanı | **103.78 m²** (salon 87.05 + ıslak hacim 16.73) |
| Bahçeler (açık) | 24.39 + 32.82 = 57.21 m² |
| Serbest sirkülasyon | 65,14 m² · ≈5,4 m²/kişi |
| Tadilat — minimum senaryo | 1,371,611 – 2,428,835 TL |
| Tadilat — önerilen senaryo | **1,621,845 – 2,917,468 TL** |
| Açılış öncesi toplam nakit | 2,229,845 – 4,109,468 TL |
| Ruhsat zinciri | 16–28 hafta |
| Şantiye süresi | 11 hafta · 14 adım |
| Uygunluk kontrolü | 28 madde: 5 kırmızı · 14 sarı · 9 yeşil |

---

## 7 · Mevzuat kaynakları (Eylül 2026'da erişildi)

- Özel Beden Eğitimi ve Spor Tesisleri Yönetmeliği — mevzuat.gov.tr (No. 4191)
- Özel Spor Salonları Talimatı — shgm.gsb.gov.tr
- İstanbul Gençlik ve Spor İl Müdürlüğü — bilgi formları
- Maltepe Belediyesi Ruhsat ve Denetim Müdürlüğü — işyeri açma ve çalışma ruhsatı
- İstanbul İtfaiyesi (İBB) — yangın güvenlik önlemleri açısından işyeri denetimi
- 2026 tarihli sektör kaynakları — birim fiyat ve açılış bütçesi çıpaları

> **Uyarı:** yerel uygulama farklılık gösterebilir. GSİM'in yaygın uygulamasında aranan
> 125 m² çalışma alanı / toplam 170 m² şartı **yönetmelik metninde yer almamaktadır**;
> talimat ve il müdürlüğü uygulamasından gelmektedir. Bu nedenle projenin ilk adımı
> İstanbul GSİM'den **yazılı ön görüş** almaktır (ana dosya s.3 ve s.9).

---

## 8 · Bilinen sınırlar

- Geometri raster paftadan türetilmiştir; kolon ve kapı konumları temsilîdir.
- Render'lar temsilîdir, imalat ölçüsü değildir; marka/model içermez.
- Maliyet bandı teklif değildir; BoQ'daki birim fiyat sütunu teklif alındıkça doldurulmalıdır.
- Harç, tescil ve rapor ücretleri her yıl güncellenir; başvuru öncesi kurumdan teyit alınmalıdır.
- Bu dosya ruhsat başvurusu yerine geçmez; mimar onaylı 1/100 vaziyet planı ayrıca üretilmelidir.


---

## 9 · QA protokolü sonucu

`python3 tools/qa.py` — **0 hata, 0 uyarı**. Kontrol edilenler:

1. Her iki PDF'in sayfa sayısı, sayfa boyutu (A3 yatay 1191×842 pt / 16:9 960×540 pt) ve
   tüm sayfaların hatasız render edilmesi.
2. Türkçe glif taraması (ş ğ ı İ ü ö ç Ş Ğ Ü Ö Ç) — her sayfada; bozuk kodlama izi (`�`, `Ã`)
   ve Python `.upper()` tuzağı (ISLAK/ISTANBUL/GIRIŞ gibi hatalı büyük harf) taraması.
3. Çapraz m² tutarlılığı: bölge toplamı = salon = 87,05 · salon + 2 blok = 103,78 ·
   soyunma+duş+WC ≈ blok · `geometry.json` ↔ `dimensions.json` ↔ `proj.py`.
4. Çapraz TL tutarlılığı: dört senaryonun (minimum/önerilen × Seçenek A/B) BoQ formül
   sonucu ile PDF maliyet modelinin birebir eşleşmesi; bütçe bandının her iki PDF'te de
   aynı yazılması.
5. XLSX: 211 canlı formül hücresi, birim fiyat sütununun tamamen boş olması, 4 sayfa.
6. Render'lar: 8 dosya, her birinde “temsilî görsel — imalat ölçüsü değildir” şeridi.
7. `Gym_Model.html`: tarayıcıda açılıp **dosya dışı her istek reddedilerek** test edildi —
   sıfır dış istek, sıfır konsol hatası, 8 render galeride, 3B görüntüleyici çalışıyor,
   390 px genişlikte yatay taşma yok.
8. Kırmızı takım denetimi (şüpheci ruhsat memuru + komisyon üyesi gözüyle): uygunluk
   listesine beş madde eklendi — soyunma/dinlenme odalarının kendi aydınlatma-havalandırma-ısı
   ve hijyen şartı, birimin bodrum katta olup olmadığı (bodrumda özel havalandırma zorunlu),
   İlçe Sağlık Müdürlüğü raporu ve personel hijyen eğitimi belgesi, çevresel gürültü
   değerlendirme raporu, kullanım değişikliğinden doğabilecek otopark/sığınak yükümlülüğü.
