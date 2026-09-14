# BUILD NOTES — Maltepe / İdealtepe Gym Dönüşümü

**MALTEPE / İDEALTEPE — MOBİLYA MAĞAZASI → FONKSİYONEL ANTRENMAN STÜDYOSU**
Rev B · 13 Eylül 2026 · fiyat referansı **Eylül 2026 piyasa mertebesi**

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

---

## 10 · Rev B — işveren geri bildirimiyle yapılan üç düzeltme

**1 · Bahçeler gym'e katılmıyor.** Ön (24,39 m²) ve arka bahçe (32,82 m²) açık kullanımda kalır ve
hiçbir alan hesabına girmez — zaten 103,78 m²'lik net iç alana dâhil değildi. Değişen tek şey karar
ağacıdır: eski R2 rotası (arka bahçenin kapatılarak 136,60 m²'ye çıkılması) **kaldırıldı**. Yerine
gelen rotalar:

| | Rota | İçerik |
|---|---|---|
| R1 | Ön görüş olumlu | Dosya olduğu gibi uygulanır, ek maliyet yok |
| R2 | Kapsam revizyonu | Randevulu kişisel antrenman / özel ders stüdyosu; tescil kapsamı ve NACE kodu buna göre; hukuki görüş şart |
| R3 | Sözleşme yolu | Mesele mimari değil ticarî: kira sözleşmesindeki fesih/indirim imkânı avukatla değerlendirilir |

Uygunluk sayfasındaki iki kırmızı maddenin “gerekli aksiyon” metni ve risk kaydındaki ilk satır
buna göre güncellendi.

**2 · Ortadaki hacim gerçek bir RİNG.** Önceki modelde altıgen, yatay çubuklardan oluşan bakır
renkli bir “rig” olarak kurulmuştu ve render'larda ahşap bir yapı gibi okunuyordu. Yeniden
modellendi: 30 cm yüksekliğinde kanvas kaplı platform, koyu gri etek ve ince kırmızı şerit,
**altı adet koyu kırmızı vinil pedli çelik köşe direği** ve direkler arasında **dört sıra siyah ring
halatı** (kotlar 0,35 / 0,70 / 1,05 / 1,40 m). Ringde ahşap kullanılmamıştır; malzemeler çelik,
vinil ped, halat ve kanvastır. Teknik tanım `tools/proj.py` içindeki `RING` sözlüğündedir ve hem 3B
modeli hem render prompt'larını besler. Paftalardaki etiket de
“TRIMODE ARENA — altıgen ring, 4 sıra halat” olarak değişti.

**3 · Ekipmanlar render'da görünüyor.** Ekipman artık düz kutu değil; her biri tipine göre tanınır
kütle olarak modellendi (koşu bandı: bant + yan raylar + konsol · kondisyon bisikleti: volan, sele,
gidon · dambıl rafı: iki katlı raf + dambıllar · kablo çapraz: iki ağırlık takozlu kule + makara
kolları + barfiks · çok fonksiyonlu istasyon: takoz, oturma ve sırt pedi). Render prompt'ları da her
makineyi adıyla ve konumuyla sayıyor, “düz kutu bırakma, referansta olmayan makine uydurma”
talimatını içeriyor. Ekipman **bütçe dışıdır** — işverence temin edilmiştir; BoQ'nun 3. sayfasında
yalnızca bilgi olarak, artık yükseklik sütunuyla birlikte listelenir.

---

## 11 · Gym_Model.html — telefon / sohbet uygulaması davranışı

**Tespit edilen sorun.** Dosya WhatsApp'tan iPhone'a gönderildiğinde, ekteki `.html`'e
dokunulduğunda çoğu zaman **iOS Quick Look** önizleyicisinde açılır ve orada **JavaScript
kapalıdır**. Önceki sürümde gezinme sekmeleri, galeri ve tüm bölümler JavaScript ile
üretildiğinden bu durumda yalnızca ilk bölüm görünüyor, menüler ölü kalıyordu.
Playwright ile `javaScriptEnabled:false` altında doğrulandı: nav'da 0 buton, galeride 0 görsel.

**Uygulanan çözüm — ilerlemeli zenginleştirme.** Dosya yeniden kuruldu:

- Bütün içerik (metin, tablolar, sekiz render) doğrudan HTML işaretlemesinde; hiçbiri
  JavaScript ile üretilmiyor.
- Sekme mantığı kaldırıldı; tüm bölümler varsayılan olarak görünür, gezinme gerçek
  çapa bağlantısı (`<a href="#...">`) — JavaScript'siz de çalışır.
- 3B görüntüleyici artık sayfa açılışında değil, **“3B modeli başlat” düğmesine basılınca**
  yükleniyor. three.js ve model betiği `type="text/plain"` bloklarında bekliyor; böylece
  telefonda 600 KB'lık kütüphane boşuna ayrıştırılmıyor.
- 3B bölümünde, model çalışmazsa yerine geçen **sabit kütle modeli görseli** ve açıklayıcı
  not var. WebGL hatası `try/catch` ile yakalanıp kullanıcıya Türkçe mesajla bildiriliyor.

**Doğrulama (QA adım 6'ya eklendi).** `tools/qa_offline.js` artık iki senaryoyu birden
ölçüyor ve `tools/qa.py` sonucu raporluyor:

| Senaryo | Sonuç |
|---|---|
| JS açık, dosya dışı her istek reddedilmiş | 0 dış istek, 0 konsol hatası, 3B açılıyor (4 kamera düğmesi) |
| JS kapalı, iPhone 13 ekranı | 6 bölümün 6'sı görünür · 6 çapa bağlantısı · 8 render görseli · 11 tablo satırı · yatay taşma yok |

**Paylaşım önerisi.** Telefonda hızlı bakış için `Gym_Sunum_16x9.pdf` gönderilmelidir —
PDF her cihazda ve her önizleyicide aynı görünür. `Gym_Model.html` artık telefonda da
tamamen okunur; yalnızca döndürülebilir 3B model gerçek bir tarayıcı (Chrome/Safari'de
“tarayıcıda aç”) gerektirir.

---

## 12 · Rev C — mekanik ve elektrik projeleri

İşveren talebi üzerine mekanik ve elektrik, ayrı disiplin projeleri olarak çizildi ve her birine
kendi BoQ'su verildi.

### Yeni teslimatlar

| Dosya | İçerik |
|---|---|
| `Gym_Mekanik_Proje_A3.pdf` | 6 pafta: sistem özeti · havalandırma planı · iklimlendirme planı · sıhhi tesisat planı · prensip ve kolon şemaları · metraj özeti ve lejant |
| `Gym_Mekanik_BoQ.xlsx` | 4 sayfa · 37 poz · canlı formüllü · sistem verileri sayfası dâhil |
| `Gym_Elektrik_Proje_A3.pdf` | 6 pafta: sistem özeti · aydınlatma planı · priz ve kuvvet planı · zayıf akım planı · pano tek hat şeması · topraklama, metraj ve lejant |
| `Gym_Elektrik_BoQ.xlsx` | 4 sayfa · 36 poz · canlı formüllü · linye tablosu dâhil |

### Tek kaynak korundu

Disiplin pozları ayrı bir liste değildir: `tools/proj.py` içindeki `B_MEK` ve `B_ELK` listeleri
ana BoQ'nun `MEKANİK` ve `ELEKTRİK` gruplarını **oluşturur**. Disiplin BoQ'ları bu grupları
filtreleyerek üretilir, dolayısıyla üç dosya arasında sapma imkânsızdır. QA bunu her derlemede
poz poz karşılaştırır.

### Tasarım kararları

**Mekanik.** Dengeli havalandırma: 1.000 m³/h besleme, aynı debide egzoz (salon 760 + ıslak hacim
240). Besleme kuzey çeperden, egzoz güney çeperden — salon boyunca çapraz süpürme. Islak hacim
egzozu ayrı fan ve ayrı çıkışla doğrudan dışarı. İklimlendirme, tek büyük ünite yerine **bölge
bazlı dört split** olarak kuruldu (24.000 + 18.000 + 2 × 12.000 = 66.000 BTU, hesaplanan 57.000
BTU'nun %16 üzerinde): her mekân bağımsız çalışır, bir arıza tesisi durdurmaz. Sıhhi tesisatta
tek düşey şaft ve tek gider toplama hattı; sıcak su blok başına 6 kW ani ısıtıcı.

**Elektrik.** 21 linye, bağlı güç 26,59 kW, eşzamanlılık katsayıları uygulanmış talep gücü
17,03 kW. Faz dağıtımı elle değil algoritmayla yapıldı: linyeler talep gücüne göre büyükten
küçüğe sıralanıp her biri o an en az yüklü faza atandı; iki 6 kW'lık su ısıtıcısı farklı fazlara
düştü ve **dengesizlik %0,2**'ye indi (faz başına 26,8 A → 3×32 A abonelik). Islak hacim linyeleri
ikinci bir 30 mA kaçak akım rölesinden beslenir. Kardiyo ekipmanı ayrı linyededir.
**Soyunma odalarına ve WC'lere kamera konulmamıştır** — bu bir tasarım tercihi değil, kişisel
verilerin korunması mevzuatının sınırıdır; QA her derlemede kamera koordinatlarının ıslak hacim
poligonları içine düşmediğini kontrol eder.

### Bütçeye etkisi — açıkça

Detaylı tasarım, önceki götürü kalemlerin yerini aldı. Kaldırılan özet pozlar: 03.01 (pis su +
temiz su götürü), 03.07 (sıcak su götürü), 05.01–05.06 (elektrik götürü), 06.01–06.04 (mekanik
götürü), 09.02 (yangın algılama götürü — artık elektrikte). Sonuç:

| | Rev B | Rev C |
|---|---|---|
| MEKANİK | 204.000 – 353.000 TL (4 götürü poz) | **414.127 – 692.746 TL** (37 poz) |
| ELEKTRİK | ≈206.000 – 383.000 TL (6 götürü poz) | **401.420 – 680.700 TL** (36 poz) |
| ISLAK HACİM | 254.777 – 443.647 TL | 141.777 – 241.647 TL (tesisat mekaniğe taşındı) |
| YANGIN · GÜVENLİK | 114.100 – 223.600 TL | 82.100 – 158.600 TL (algılama elektriğe taşındı) |
| **GENEL TOPLAM (önerilen)** | 1.618.962 – 2.912.329 TL | **1.948.315 – 3.382.449 TL** |

Artış yaklaşık **330.000 – 470.000 TL**'dir ve gerçek bir maliyet artışı değil, **görünür hâle
gelmiş maliyettir**: götürü bir satır 37 poza açıldığında kanal askısı, damper, susturucu, balanslama,
potansiyel dengeleme, parafudr gibi kalemler ortaya çıkar. Bu kalemler önceki bütçede de yapılacaktı;
sadece yazılı değildi. Müteahhit teklifleri artık bu kalemler üzerinden karşılaştırılabilir.

Ayrıca **06.17 (ısı geri kazanımlı taze hava ünitesi, 95.000–165.000 TL)** alternatif kalem olarak
işaretlenmiştir ve toplamlara **dâhil değildir**; işletme gideri üzerinden geri ödemesi teklif
alındıktan sonra hesaplanmalıdır.

### Yeni doğrulanacak girdiler

- Mevcut abonelik gücü ve trifaze durumu — talep 17,03 kW, 3×32 A gerekiyor. Yetersizse dağıtım
  şirketine güç artırımı 3–8 hafta sürer ve kritik yola girer.
- Sıcak su çözümü boylere çevrilirse talep gücü ≈5 kW düşer ve 3×25 A yeterli olur (mekanik s.4).
- Pis su havalandırma bacası yüksekliği (9,5 m varsayım) ve binada mevcut baca olup olmadığı.
- Dış ünite montaj yüzeyinin taşıyıcılığı ve bina yönetimi onayı.
- Temel topraklamasının varlığı — varsa poz 05.45 iptal edilir.
