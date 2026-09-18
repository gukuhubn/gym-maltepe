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

---

## 13 · CAD seti (DXF R2010)

### Neden DWG değil — ve neden fark etmiyor

DWG kapalı (tescilli) bir formattır; açık kaynaklı hiçbir kütüphane onu güvenilir biçimde
**yazamaz**. Bu ortamda ODA File Converter veya LibreDWG da yoktur. Bu nedenle set,
AutoCAD'in kendi değişim formatı olan **DXF R2010 (AC1024)** ile üretilmiştir.

Pratikte engel değildir: AutoCAD, BricsCAD, ZWCAD, GstarCAD ve DraftSight bu dosyaları
doğrudan açar; **Farklı Kaydet → AutoCAD 2018 Çizim (*.dwg)** ile tek adımda DWG olur.
Toplu dönüşüm için AutoCAD'in DWG Convert aracı veya ücretsiz ODA File Converter kullanılır.

### Set

| Dosya | İçerik |
|---|---|
| `GYM-MIM-Uygulama-R2010.dxf` | Mimari · 5 pafta (A-01 altlık, A-02 uygulama, A-03 zemin kaplama, A-04 tavan planı, A-05 yangın ve tahliye) — diğerlerine XREF bağlanabilir |
| `GYM-MEK-Uygulama-R2010.dxf` | Mekanik · 4 pafta (M-01…M-04) |
| `GYM-ELK-Uygulama-R2010.dxf` | Elektrik · 4 pafta (E-01…E-04) |
| `GYM-BIRLESIK-R2010.dxf` | Tümü · 13 pafta |
| `KATMAN-LISTESI.csv` | 52 katmanın standardı (Excel) |
| `OKUBENI-CAD.txt` | Format, birim, ölçek, DWG dönüşümü, kapsam sınırı |

### Teknik kurulum

- **Birim:** milimetre (`$INSUNITS = 4`), model uzayı 1:1 gerçek boyut
- **Pafta:** A3 (420 × 297), **ölçek 1/75**, ölçülendirme stili `GYM-75` (DIMSCALE 75)
- **Katman:** 52 katman, `A-` mimari / `M-` mekanik / `E-` elektrik / `G-` genel öneki ile;
  her katmanda ACI renk, çizgi tipi ve kalem kalınlığı tanımlı
- **Blok:** 32 sembol bloğu, **öznitelikli** — menfezlerde `KOD`/`DEBI`, prizlerde
  `KOD`/`LINYE`, klimalarda `KOD`/`KAPASITE`. `DATAEXTRACTION` ile doğrudan metraj çekilebilir
- **Pafta düzeni:** tek model uzayı, paftalar aynı modeli farklı katman durumlarıyla gösterir;
  her görüntü penceresinde disiplin dışı katmanlar **VP Freeze** ile dondurulmuştur
- **Yazı:** Arial tabanlı `GYM` / `GYM-B` stilleri — Türkçe karakterler sorunsuz

### Ölçek neden 1/75

İlk denemede 1/50 seçilmişti; bina 11,96 × 13,39 m olduğundan A3'te lejant sütunuyla
birlikte **sığmadı** — doğu kenarı ve ölçü çizgileri kırpıldı. 1/75'te tüm bina, ölçüler,
kuzey oku, lejant ve antet aynı paftaya rahatça giriyor. A2'de 1/50 de mümkündür;
istenirse `build_dxf.py` içinde tek satır değişir.

### Üretim sırasında düzeltilen iki gerçek çizim hatası

1. **Tarama adası.** Duvar bandı delikli (island) tarama ile kuruluyordu; hem ezdxf'in
   görüntüleyicisi hem de bazı CAD'ler deliği doldurup tüm paftayı kapatıyordu. Duvar bandı
   kenar bazlı deliksiz dörtgenlere ayrıldı — her CAD'de aynı görünür.
2. **Bakır ve drenaj güzergâhı.** Hatlar salonun ortasından çapraz geçiyordu. Tavan altında
   duvar boyunca ortogonal güzergâhlara çevrildi; her iç ünitenin kendi hattı `proj.py`
   içinde açıkça tanımlı. Metraj 33,5 → 35,8 m (bakır) ve 31,6 → 34,2 m (drenaj) oldu,
   bütçeye yansıdı.

### Bu set ne değildir

Ön tasarım seviyesindeki bir CAD setidir; uygulama projesi **formatında** düzenlenmiştir
ama uygulama projesi **değildir**. Dönüşmesi için: ölçülmüş mimari altlık (DXF veya rölöve),
tavan ve kiriş altı kotları, kolon konumları, mevcut pis su bağlantı kotu, mevcut abonelik
gücü — ve **yetkili mühendis imzası**. Türkiye'de mekanik ve elektrik uygulama projeleri
ilgili meslek odasına kayıtlı mühendis tarafından imzalanır; bu set o imzanın yerine geçmez,
ona girdi oluşturur.


---

## 14 · Rev D — mimari uygulama seti, inşaat seti ve çizim denetimi

İşveren geri bildirimi: *"plan, kesit görünüş, detay vs, pano hesabı vs, yani kısacası tüm
inşaat setini ver, belediye teslimi gibi düşün ya da müteahhit, oradan her şey anlaşılmalı…
ayrıca çizimleri kontrol et… mimari proje yok misal alçıpan, seramik, yer kauçuk karo vs."*

### 14.1 · Yeni teslimatlar

| Dosya | İçerik |
|---|---|
| `Gym_Mimari_Proje_A3.pdf` | **Mimari uygulama projesi — 13 pafta** |
| `Gym_Insaat_Seti_A3.pdf` | **Birleşik inşaat seti — 29 pafta**, kapak + indeks + mimari 13 + mekanik 7 + elektrik 7, PDF yer imli |
| `Gym_CAD_Seti_DXF.zip` | CAD seti **13 paftaya** çıktı (mimari 5 pafta eklendi) |
| `Gym_CAD_Paftalar.pdf` | 13 pafta önizleme |

Mimari set paftaları: A-01 kapak/genel notlar/indeks · A-02 yıkım-söküm · A-03 uygulama planı ·
A-04 zemin kaplama planı · A-05 tavan planı (RCP) · A-06 kesit A-A · A-07 kesit B-B ·
A-08 iç görünüşler (G-01…G-04) · A-09 mahal listesi · A-10 kapı-pencere listesi ve duvar tipleri ·
A-11/A-12 imalat detayları (D-01…D-08) · A-13 yangın ve tahliye planı.

Mekanik sete **M-07 tavan içi tesisat koordinasyon kesiti**, elektrik sete
**E-07 pano yük ve gerilim düşümü hesabı** eklendi.

### 14.2 · Malzeme kararları (mahal listesi — A-09)

| Kod | Mahal | Kaplama |
|---|---|---|
| Z1 | Arena · serbest ağırlık | 10 mm SBR titreşim matı + **40 mm granül kauçuk karo** 1000×1000, Shore A 55, EN 14041 Bfl-s1 |
| Z2 | Fonksiyonel · kardiyo | tesviye şapı 30 mm + **20 mm kauçuk karo**, Shore A 60 |
| Z3 | Giriş · banko · dinlenme | tesviye şapı 42 mm + IXPE şilte + **5 mm SPC klik LVT**, AC5 / sınıf 33 |
| Z4 | Duş · WC | eğim şapı %1,5 + EN 14891 su yalıtımı 2 kat + **8 mm porselen 300×300, R11 / B** |
| Z5 | Soyunma | tesviye şapı 38 mm + **9 mm porselen 600×600, R10** |
| Z6 | Ring platformu | ahşap kadron + 2×18 mm su kontraplağı + EVA + kanvas, **+0,30** |

| Kod | Duvar / tavan |
|---|---|
| D1 | Mevcut duvar — saten alçı + su bazlı silikonlu mat boya (sınıf 1 yıkanabilir) |
| D2 | **Alçıpan bölme 100 mm** — 50 mm C profil @400 + 40 mm taşyünü + her yüz 2×12,5 mm A tipi, Rw ≈ 51 dB |
| D3 | Islak bölme 100 mm — ıslak yüz 2×12,5 mm **H2 (yeşil) alçıpan** |
| D4 | Akustik giydirme 95 mm — bağımsız karkas + 50 mm taşyünü, ΔRw ≈ +10 dB |
| D5 | Islak duvar — su yalıtımı + **9 mm seramik 300×600** (duşta tavana, WC'de h=1,60) |
| D6 | Ayna duvarı — 18 mm kontraplak + 6 mm güvenlik filmli ayna (+0,30 / +2,30) |
| T1 | Açık endüstriyel tavan **+3,20** — siyah boya + 12 adet akustik baffle |
| T2 | Alçıpan asma tavan **+2,75** (giriş · dinlenme) |
| T4 | Alçıpan asma tavan **+2,60** (soyunma) |
| T3 | H2 alçıpan asma tavan **+2,40** (duş · WC) + revizyon kapağı |

**Kot sürekliliği:** bitmiş zemin kotu tüm kuru hacimlerde ±0,00. Farklı kaplama kalınlıkları
tesviye şapı ile eşitlenir (Z1: 3 · Z2: 30 · Z3: 42 · Z5: 38 mm) — mahaller arasında eşik veya
tökezleme oluşmaz. Yalnızca duş ve WC −0,02'dir; fark kapı altında eğimli eşik profili ile karşılanır.

### 14.3 · Denetlenen ve düzeltilen gerçek hatalar

`tools/kontrol.py` 10 kategoride denetler. Bu turda bulunup düzeltilenler:

1. **Priz ve anahtar yönleri duvara göre değildi** — tüm duvar cihazları en yakın duvar
   segmentine dik izdüşürülüp içe bakan normale döndürüldü; sembol döner, etiket yatay kalır.
2. **Klima K2 komşu hacme kaydı** — `duvara_yapistir()` tüm hacimlerin çeperinde arama
   yapıyordu ve iç ünite erkek duşun (106) içine düşmüştü. Fonksiyona hacim filtresi eklendi;
   iç üniteler artık yalnızca salon çeperine yapışır.
3. **Su ısıtıcı devresi yanlış korumadaydı** — 6 kW / 26,1 A yük için `1×40 A + 3×6 mm²`
   yazılmıştı; 6 mm²'nin B2 akım kapasitesi 40 A olduğundan In ≤ Iz koşulu sınırda kalıyordu.
   **`1×32 A + 3×6 mm²`** olarak düzeltildi (BoQ poz 05.24 ile birlikte).
4. **Asma tavan boşluğu tesisata yetmiyordu** — T2 kotu +2,80 iken 400 mm boşluğa kanal,
   bakır hat, kablo tavası ve taşıyıcı profil sığmıyordu (10 mm açık). **T2 kotu +2,75'e
   indirildi** (boşluk 450 mm, serbestlik 30 mm) ve tavan içi kot dizilimi bölge bazında
   (T2 / T4 / T3) ayrı tanımlandı. Pis su hattı tavana değil zemine alındı.
5. **Menfez–armatür tavan çakışması** — M1 ve M2 lineer armatüre 59 ve 47 cm mesafedeydi;
   armatür sıraları arasına kaydırıldı (≥ 70 cm).
6. **Sensör–valf çakışması** — S1 ile V1 arası 22 cm; sensör erkek WC içinde yeniden konumlandı.
7. **Armatür yüksek ekipmanın üstünde** — 2,00 m'den yüksek ekipmanın tam üstüne denk gelen
   armatür, bölge içinde kalacak şekilde otomatik kaydırılıyor (`_ekipman_ustunden_kaydir`).
8. **Kesitte olmayan duvar çiziliyordu** — 101–104 salon bölgeleri arasında fiziksel bölme
   yoktur; kesit motoru bunları artık duvar değil **zemin kaplama sınırı** olarak çiziyor.
9. **Kaçış yolları duvardan geçiyordu** — soyunma mahallerinin tahliye güzergâhları kapılardan
   geçecek ve ring çevresinden dolaşacak şekilde yeniden çizildi.

Son durum: **0 hata, 0 uyarı, 6 bilgi.**

### 14.4 · Pano hesabı (E-07)

21 linyenin tamamı için hesap akımı, kesici anma akımı, kablo kesiti, akım taşıma kapasitesi
(TS HD 60364-5-52, B2, 30 °C), hat uzunluğu ve gerilim düşümü tablolandı. Sonuç:
**Ib ≤ In ≤ Iz ve ΔU ≤ sınır koşulları 21 linyede de sağlanıyor.**
En yüksek son devre gerilim düşümü %1,64 (W2 — kadın bloğu su ısıtıcısı);
ana besleme (NYY 5×10 mm², 25 m) %0,60 ile birlikte en uzak tüketicide **toplam %2,24** —
%5 sınırının altında. Kaçak akım koruması 5 grup hâlinde 30 mA A tipi, ana girişte 300 mA
S tipi seçici; yangın algılama paneli kaçak akım rölesi arkasına alınmaz.

### 14.5 · Setin sınırı

Bu set **mimari + mekanik + elektrik uygulama setidir**. Ruhsat başvurusu için proje müellifi
mimar ve tesisat mühendislerince imzalanmış 1/50 onaylı takım ayrıca düzenlenecektir.
Statik proje kapsam dışıdır; taşıyıcı sistemde hiçbir müdahale öngörülmemektedir.
Yapısal döşeme altı kotu (+3,20), mevcut duvar kalınlığı (200 mm), mevcut şap üst kotu (−0,053)
ve mevcut asma tavan varlığı **VARSAYIMDIR** — söküm sonrası rölöve ile doğrulanıp tüm set
tek yerden (`tools/proj.py`) güncellenecektir.


---

## 15 · Rev E — referans projeyle kalibrasyon, keşif özeti ve bütçe paketi

İşveren, kendi Aqua Florya / Saltbae projesinin as-built ve hakediş dosyalarını
paylaşarak "buna benzet" dedi. Paylaşılan referans:

| Dosya | İçerik |
|---|---|
| `R1_AQUA FLORYA SALTBAE - VOGELKOPP - KESİN HAKEDİŞİ 13.05.2025.xlsx` | Kesin hakediş — kapak, icmal, taşeron bazlı hakedişler, metraj cetvelleri, ödeme tabloları |
| `2025'0520_Saltbae_AquaFlorya_Butce.xlsx` | Yüklenici/firma bazlı bütçe takibi, çok para birimli |
| `ADP / UDP Yükleme Cetveli R00.xlsx` | Çift dilli elektrik pano yükleme cetveli |
| `AS BUILT PROJESİ-*` (mimari · mekanik · elektrik) | DWG setleri, ADP/UDP tek hat şemaları, as-built raporu |

### 15.1 · Benimsenen formatlar

- **Keşif özeti:** ŞARTNAME NO · POZ NO · YAPILACAK İŞİN CİNSİ · MAHAL / PROJE REFERANSI ·
  AÇIKLAMA/MARKA · BİRİM · MİKTAR · MALZEME BF/TF · İŞÇİLİK BF/TF · GENEL GİDER · KÂR+RİSK ·
  TOPLAM BF/TF. Hiyerarşik poz numarası (A · A.1 · A.1.1) ve MasterFormat benzeri şartname no.
- **Metraj cetveli:** S.NO · YAPILACAK İMALAT AÇIKLAMASI · Birim · Adet · En · Boy · Yükseklik ·
  TOPLANAN (+) · ÇIKARILAN (−) · KISMİ YEKÜN · SAYFA YEKÜNÜ. Kapı ve pencere boşlukları
  **minha** olarak eksi satırla düşülür.
- **Hakediş:** kapak (KDV, tevkifat, avans mahsubu, ödenecek net tutar) · imalat icmali
  (uygulama paketi bazında, koordinasyon bedeliyle) · poz bazlı gerçekleşme · kesintiler ·
  ödeme takibi.
- **Bütçe takibi:** iş kalemi · yüklenici/firma · para birimi · sözleşme bedeli · revize bütçe ·
  kur · ödenen · kalan · açıklama.
- **Pano yükleme cetveli:** çift dilli başlıklar, kaçak akım rölesi gruplamalı, L1/L2/L3 faz
  dağılımlı, diversite katsayılı altbilgi, yedek linyeli.
- **Dosya adı kodlaması:** `A_00_00_GF_00_1_01 (Pafta Adı)` — disiplin_yapı_blok_kat_tip_ölçek_sıra.
- **Klasör yapısı:** disiplin bazlı (01_MİMARİ · 02_MEKANİK · 03_ELEKTRİK · 04_BÜTÇE VE HAKEDİŞ).

### 15.2 · BİRİM FİYAT KALİBRASYONU — en önemli bulgu

Referans hakedişteki **gerçekleşmiş** birim fiyatlar (Mayıs 2025, KDV hariç) ile Rev C'deki
tahminler karşılaştırıldığında, mimari kalemlerde ciddi bir sapma çıktı:

| İmalat | Referans (05/2025) | Eylül 2026 karşılığı (×1,40) | Rev C tahmini | Sapma |
|---|---|---|---|---|
| Alçıpan bölme — çift yüz çift kat | 2.450 TL/m² | 3.430 TL/m² | 600–950 TL/m² | **≈ 4,4×** |
| Alçıpan asma tavan (dıamant) | 1.450 TL/m² | 2.030 TL/m² | — (kalem yoktu) | — |
| Seramik işçiliği (zemin / duvar) | 700 / 725 TL/m² | 980 / 1.015 TL/m² | 750–1.200 (mlz+işç) | ≈ 2,0× |
| Şap (malzeme + işçilik) | 600 TL/m² | 840 TL/m² | — | — |
| Çimento esaslı su yalıtımı | 610 TL/m² | 854 TL/m² | 480–780 TL/m² | ≈ 1,4× |
| Şap söküm | 471 TL/m² | 660 TL/m² | 260–450 TL/m² | ≈ 1,9× |
| Düz işçi / usta yevmiyesi | 3.500 / 4.500 TL | 4.900 / 6.300 TL | — | — |

**Eskalasyon kabulü:** Mayıs 2025 → Eylül 2026 (16 ay) için **×1,40** (yıllık ≈ %28 inşaat
maliyet artışı). Katsayı `tools/fiyat.py` içinde tek yerdedir.

Rev E'de mimari kalemlerin tamamı bu referansa göre yeniden fiyatlandırılmış; ayrıca Rev C'de
hiç yer almayan **iç doğrama grubu** (K02–K09 kapıları, 165–266 bin TL) eklenmiştir. Şantiye
genel gideri oranı, referans projedeki gerçekleşmeye uyacak şekilde %9'dan **%12**'ye çıkarılmıştır.

**Mekanik ve elektrik kalemleri kalibrasyona dâhil edilmemiştir:** referans proje bir restoran
(mutfak egzozu, VRF, soğuk oda, 630 A abonelik) olduğundan birim fiyatları bu 104 m²'lik
stüdyoyla karşılaştırılabilir değildir. Bu kalemler Rev C değerleriyle korunmuştur.

### 15.3 · Bütçenin değişimi

| | Rev C | Rev E | Değişim |
|---|---|---|---|
| Mimari imalat | 811 bin – 1,45 milyon TL | 1,72 – 2,80 milyon TL | ≈ 2,1× |
| Mekanik | 514 – 867 bin TL | değişmedi | — |
| Elektrik | 403 – 683 bin TL | değişmedi | — |
| **Önerilen senaryo — genel toplam** | **1,95 – 3,38 milyon TL** | **3,15 – 5,18 milyon TL** | **≈ 1,6×** |
| TL/m² | 18.775 – 32.593 | 30.394 – 49.877 | — |

### 15.4 · İki bütçe modelinin mutabakatı

Artık iki bağımsız model var ve QA bunların ayrışmasını denetliyor:

1. **Poz bazlı model** (`proj.B`, 111 poz) — senaryolu (MİNİMUM / ÖNERİLEN, Seçenek A/B),
   A3 dosyası ve sunumu besler.
2. **Metraj bazlı model** (`metraj.py` + `fiyat.py`, 61 poz · 160 metraj satırı) — keşif özeti,
   hakediş ve bütçe takibi dosyalarını besler.

Genel gider farklı ele alındığı için karşılaştırma J paketi hariç yapılır:
**1.721.992 vs 1.770.879 TL (%+3)** ve **2.804.540 vs 2.649.731 TL (%−6)**.
QA, sapma %15'i aşarsa hata verir.

### 15.5 · Yeni teslimatlar

| Dosya | İçerik |
|---|---|
| `Gym_Kesif_Ozeti_BoQ.xlsx` | 7 sayfa — kapak, icmal, keşif özeti (61 poz), bütçe tahmini, mekanik/elektrik keşif, 160 satırlık metraj cetvelleri |
| `Gym_Hakedis_Sablonu.xlsx` | 5 sayfa — kapak, icmal, poz bazlı hakediş detayı, kesintiler/avans, ödeme takibi |
| `Gym_Butce_Takip.xlsx` | 2 sayfa — 22 iş kalemi bütçe takibi, 8 aylık nakit akışı |
| `Gym_Pano_Yukleme_Cetveli.xlsx` | 2 sayfa — ADP yükleme cetveli (referans formatında), gerilim düşümü kontrol cetveli |
| `Gym_Proje_Paketi.zip` | 6 klasör, 21 dosya — referans klasör yapısı ve dosya adı kodlamasıyla |

### 15.6 · Metraj motorunun kurduğu ilişkiler

`tools/metraj.py` her miktarı geometriden türetir; elle girilen tek şey birim fiyattır:

- Bölme duvar alanı = mahal çeperi × 3,20 m (yapısal döşemeye kadar) − kapı boşlukları
- Süpürgelik = mahal çevresi − kapı genişlikleri − salon bölge sınırları (fiziksel duvar yok)
- Duvar seramiği = ıslak hacim çevresi × (duşta 2,40 · WC'de 1,60 m) − kapı boşlukları
- Boya = mahal çevresi × tavan kotu − kapı − vitrin − ayna duvarı
- Moloz hacmi = kaplama sökümü + asma tavan sökümü + ıslak hacim şap kırımı kalınlıklarından

Bu sayede bir mahal ölçüsü değiştiğinde metraj, keşif özeti, hakediş ve bütçe birlikte güncellenir.

---

## 16 · Rev F — teknik çizim tekniği, denetim ajanları ve pafta ayrıştırması

İşveren geri bildirimi aynen: *"projeleri mimari, elektrik, mekanik teknik çizim
teknikleri ile çizmen gerekiyor. projeleri kontrol eden sistem agentları kur.
bunlar kabul edilebilir imalat çizimleri değil. alçıpan duvarda profil yok.
çapraz elektrik kablosu gitmemeli hiç bir yerde. tek hat şeması çizimi yok...
her biri ayrı pafta da olmalı ki anlayabilelim."*

Sekiz maddeye ayrıştırıldı ve sekizi de kapatıldı.

### 16.1 · Çapraz tesisat hattı — geometrik olarak imkânsız hâle getirildi

Önceki sürümlerde linyeler ve yangın algılama çevrimi cihazdan cihaza düz
(çapraz) çizgilerle bağlanıyordu. Bu bir çizim hatası değil, **uygulanamaz bir
proje** demektir: gerçekte kablo duvar dibinden veya asma tavan kenarından,
yalnız yatay ve düşey kollarla gider.

Çözüm elle düzeltme değil, motor değişimi oldu:

- `tools/yol.py` — yapı içini 10 cm ızgaraya böler (9.672 düğüm, 96,9 m² serbest
  alan), **yalnız dört komşulu** (yatay/düşey) A\* ile yol bulur. Çapraz adım
  komşu kümesinde yoktur; dolayısıyla çapraz segment üretilemez.
  Duvar çeperine 55 cm bandında kalan düğümlerin maliyeti 0,35 katsayılıdır →
  hat açık alanı kesmek yerine çeperden dolaşır. Dönüş cezası zikzakı engeller.
- Kapı geçişleri artık elle girilmiyor: `_kapi_noktalari()` her ıslak hacmin
  çeperi ile soyunma hacmi arasındaki **en yakın nokta çiftinden** kapı boşluğunu
  türetir. Bu düzeltmeyle daha önce yol bulunamayan P5 / W1 / W2 linyeleri de
  bağlandı.
- `tools/linye_yollari.py` → 22 linye + 7 anahtar sortisi · **450,8 m · 0 çapraz segment**
- `tools/kanal_yollari.py` → hava kanalları da aynı motora alındı:
  besleme 16,8 m · egzoz 10,5 m · ıslak 15,0 m · **0 çapraz segment**.
  `proj.KANAL` güzergâhları artık `data/kanallar.json`'dan okunur.

Hatlar paftaya `draw_mep.linye()` ile basılır: iletken sayısı çentiği, kablo
cinsi/kesiti ve boru çapı (`P3 · NHXMH 3×2,5 · Ø20`), etiket çakışmasını önleyen
yerleştirme. DXF tarafında `build_dxf.linye_ciz()` aynı veriyi
`E-AYD-LINYE` / `E-KUVVET-LINYE` / `E-ZAYIF-TAVA` / `E-ZAYIF-LINYE`
katmanlarına yazar.

### 16.2 · Alçıpan duvarda profil

`tools/draw_duvar.py` gerçek C/U profil geometrisi üretir (TS EN 14195 /
DIN 18182): C50×50×0,6 gövdesi boşluğu enine geçer, 50 mm kanatlar duvar
doğrultusunda uzanır, açılış yönü şaşırtmalı, aralık 400 mm.

- Uygulama planında (1/50) dikmeler basitleştirilmiş çizgi olarak görünür.
- **A-14 paftası** D2 / D3 / D4 / D6 tiplerini **1/5 yatay kesitte** verir:
  katman dolguları ve taramaları, C dikme kesiti, düşey katman ölçü zinciri,
  yatay 400 mm dikme aralığı zinciri, iki sütunlu katman lejantı, karkas
  metrajı (17,14 m · 49 dikme · 54,85 m²) ve 8 imalat kuralı.
- `mimari` ajanı, bölme olarak kullanılan her duvar tipinin katman listesinde
  taşıyıcı profil bulunmasını **zorunlu** kılar; bulunmazsa HATA verir.

### 16.3 · Tek hat şeması

`tools/build_tekhat.py` → `output/Gym_ADP_Tek_Hat_Semasi.pdf`, 8 pafta:
kapak · pano karakteristik tablosu (IEC 61439-1/-2, 8 grup) · sembol listesi
(IEC 60617, 13 sembol) · pano önden görünüş (3 sıra × 18 modül, 32 cihaz /
46 modül) · EPLAN tarzı şematik diyagram (potansiyel rayları L1-L2-L3-N-PE,
sayfalar arası referans, cihaz etiketleri −1F1 / −F1 / −ID1 / −X1, tel
numaraları, klemens sırası, YEDEK linyeler).

### 16.4 · Her çizim kendi paftasında

Önceki CAD seti tek model uzayı üzerinde katman dondurarak (VP Freeze) pafta
üretiyordu. İşveren bunu haklı olarak yetersiz buldu.

`build_dxf.TEKIL_PAFTA` artık **pafta başına bağımsız DXF belgesi** üretir;
model uzayında yalnız o paftanın geometrisi bulunur:

```
cad/paftalar/A-01 … A-05   (5 mimari)
cad/paftalar/M-01 … M-04   (4 mekanik)
cad/paftalar/E-01 … E-05   (5 elektrik, E-05 topraklama)
```

`Gym_CAD_Paftalar.pdf` önizlemesi de bu tekil dosyalardan basılır. Lejant,
yalnız o paftada **fiilen kullanılan** katmanları listeler. Birleşik dosyalar
(disiplin ve tüm proje) koordinasyon için korunmuştur.

Aynı ilke PDF setlerinde de uygulandı:

- Mekanik set 7 → **9 pafta**: havalandırma prensip şeması, sıhhi tesisat kolon
  şeması ve iklimlendirme prensip şeması artık **ayrı paftalarda**.
- Elektrik set 7 → **8 pafta**: topraklama ve potansiyel dengeleme planı eklendi.
- Mimari set 13 → **14 pafta**: duvar tipleri yatay kesit paftası eklendi.
- İnşaat seti 29 → **33 pafta**.

### 16.5 · Teknik çizim tekniği — mekanik sembol kütüphanesi

`tools/draw_tesisat.py`, TS 2164 §1.13 / ISO 14617 uyumlu sembol kütüphanesidir;
tüm boyutlar `u = 4 mm` modülünün katıdır. Kesme/küresel/kelebek vana, çekvalf,
balans vanası, emniyet ventili, pislik tutucu, pompa, aksiyel fan, susturucu,
filtre, hacim kontrol damperi (HKD), motorlu damper (MD), yangın damperi (YD-90),
termometre, manometre, boyler, yer süzgeci, temizleme kapağı (TK), havalık
bacası, klima iç/dış ünite, kolektör, su sayacı.

Şema kuralları koda gömüldü: ölçeksiz, **yalnız ortogonal**, akış soldan sağa,
her hatta akış yönü oku + servis kodu + çap, aynı paftada zorunlu lejant.

**Kolon şeması** gerçek bir düşey kesittir: düşey ölçüler ölçekli (1 m = 38 mm),
yatay ölçüler ölçeksiz; döşeme iki paralel çizgiyle gösterilir; armatürler
gerçek montaj kotlarındadır (lavabo 85, klozet çıkışı 20, duş başlığı 210,
boyler 190 cm); kolon numarası her kolonun en üst noktasındadır; havalık çatı
üstü +2,00 m'de şapkayla biter; her kolon dibinde temizleme kapağı vardır.

### 16.6 · Denetim ajanları

`tools/agents/` altında altı bağımsız ajan (`base.py` ortak altyapı,
`denetim.py` koşucu). Her ajan kendi mevzuatına göre `HATA / UYARI / BİLGİ`
üretir; bir hata genel sonucu **RED** yapar. Çıktılar: konsol,
`data/denetim.json`, `output/Gym_Denetim_Raporu.pdf`.

Ajanların ilk koşusunda bulup düzelttikleri **gerçek** tasarım hataları:

| Bulgu | Düzeltme |
|---|---|
| Aydınlatma linyelerinde 3×1,5 mm² — yönetmelik linye için ≥ 2,5 mm² ister | L1–L6, V1, V2, Z2 → 3×2,5 mm² |
| P1 ve P2 priz linyelerinde 8'er sorti — sınır 7 | 16 duvar prizi üç linyeye bölündü (P1/P2/**P6**), RCD-2 güncellendi |
| Priz etiketleri P1…P16, linye kodlarıyla çakışıyordu | Duvar prizleri **PR1…PR16** olarak yeniden kodlandı |
| 6 kW ani su ısıtıcı ΔT 30 K'de yalnız 2,9 l/dak verir — bir duş 8 l/dak ister | **100 L / 3 kW depolu boyler**; W1/W2 linyesi 1×32 A / 3×6 → 1×20 A / 3×2,5; poz 06.40 ve 05.24 güncellendi |
| Hava kanalı güzergâhlarında 11 çapraz segment | Kanallar ortogonal yol bulucuya alındı |
| Yangın algılama çevrimi çapraz çiziliyordu | Z2 ortogonal çevrim güzergâhına alındı |
| D6 ayna duvarı katman toplamı 24 mm, tabloda 212 mm | D6, D1/D4 üzerine **24 mm giydirme** olarak tanımlandı |
| Z4 / Z6 bitmiş kotları katman toplamıyla tutmuyordu | `ZEMIN_TABAN` sözlüğü eklendi; ıslak hacim tabanı −0,075 (şap traşı), ring platformu bitmiş Z1 üzerine |
| A-BOLGE ve A-ZEMIN-DERZ katmanlarında 0,09 mm kalem — ISO 128 serisi dışında | 0,13 mm |
| Yazı yüksekliği ve antet alanları programatik değildi | `dxf_lib.YAZI_YUKSEKLIK` (ISO 3098) ve `build_dxf.ANTET_ALANLARI` eklendi |
| Tavan içi servisler düşey çakışıyor görünüyordu | `TAVAN_KATMAN` kayıtlarına **yatay şerit** alanı eklendi (A kanal · B mekanik boru · C kuvvet · D zayıf akım); çakışma yalnız aynı şeritte aranır |

### 16.7 · Topraklama ve potansiyel dengeleme

Araştırma, setin zorunlu bir parçasının eksik olduğunu gösterdi. Eklendi:

- Sistem TN-S; sayaç sonrası N ve PE ayrık.
- 4 adet Ø16 Cu kaplı çelik çubuk elektrot (2 m, 3 m aralık), 30×3,5 mm
  galvanizli şeritle bağlı. Hesap: tek elektrot R = ρ/(2πL)·ln(4L/d) = 49,5 Ω;
  4 paralel + %25 karşılıklı etki payı → **15,5 Ω ≤ 20 Ω**.
- Ana topraklama barası (ATB) pano altında; her ıslak blokta ek potansiyel
  dengeleme barası (EPDB).
- 10 kalemlik yabancı iletken parça bağlantı listesi (su borusu, kanal gövdesi,
  kablo tavası, klima şasisi, ring karkası, alçıpan profilleri…).
- PDF pafta E-08 ve tekil DXF paftası E-05; `E-TOPRAK-*` katmanları.

### 16.8 · Rev F sayısal özet

| | Rev E | Rev F |
|---|---|---|
| Linye sayısı | 21 | **22** (+P6) |
| Tesisat hattı | çapraz çizgiler | **450,8 m ortogonal · 0 çapraz** |
| Hava kanalı | 11 çapraz segment | **42,3 m ortogonal · 0 çapraz** |
| DXF katman | 50 | **61** |
| DXF dosya | 4 birleşik | 4 birleşik + **14 tekil pafta** |
| Mimari pafta | 13 | **14** |
| Mekanik pafta | 7 | **9** |
| Elektrik pafta | 7 | **8** |
| İnşaat seti | 29 | **33** |
| Denetim | `kontrol.py` + `qa.py` | + **6 denetim ajanı**, PDF rapor |

---

## 17 · Rev G — pafta motoru, aks sistemi ve tek hat şemasının CAD'e taşınması

İşveren geri bildirimi: *"çizim kalitesi hâlâ istediğim gibi değil… tek hat
şeması örneğin neden cad değil… elli tane dosya verme ziple düzgün teslim et…
genel olarak çizim üreten sistemi kurmamız lazım."*

İki derin araştırma ajanı çalıştırıldı (dünya ölçeğinde pafta/antet standartları
ve CAD'de tek hat şeması üretimi). Bulgular doğrudan koda uygulandı. Araştırma
notu: bu ortamda WebFetch/curl egress proxy tarafından engellidir; kaynaklar
WebSearch özetlerinden gelmiştir ve raporlarda [S] (kaynaklı) / [P] (meslek
pratiği) olarak işaretlenmiştir. ezdxf bulguları ise **çalıştırılarak**
doğrulanmıştır.

### 17.1 · Pafta motoru — `tools/pafta.py`

Artık her pafta tek bir motordan çıkıyor; set içi tutarlılık böyle sağlanıyor.

| Öğe | Dayanak | Uygulama |
|---|---|---|
| Kâğıt ve çizim alanı | TS EN ISO 5457 | A1 841×594, çizim alanı 811×574 (sol cilt payı 20 mm, diğer kenarlar 10 mm) |
| Çerçeve | ISO 5457 | sürekli çizgi 0,70 mm |
| Kenar ızgarası (bölge referansı) | ISO 5457 | 50 mm nominal, rakamlar soldan sağa, harfler aşağıdan yukarı, karakter 3,5 mm; "C4'teki detaya bakınız" gösterimi mümkün |
| Merkezleme ve yön işaretleri | ISO 5457 | dört kenar ortasında, 0,70 mm, çerçeveyi 10 mm aşar |
| Metrik referans cetveli | ISO 5457 | 100 mm / 10 mm bölmeli — baskı ölçek sapması denetlenebilir |
| Kâğıt boyutu tanımı | ISO 5457 | alt kenarın sağ köşesinde "A1" |
| Antet | TS EN ISO 7200 + TMMOB MMO | 180×92 mm, sağ altta: işveren, proje, yapı/mahal, disiplin, pafta adı ve üst başlığı, **proje müellifi + oda sicil no**, çizen/kontrol/onay, tarih, ölçek, birim, durum, pafta no, revizyon, sonraki pafta |
| Revizyon tablosu | ISO 7200 | antetin üstünde, REV · TARİH · AÇIKLAMA · ÇZ · KT · ON |
| Görüntü penceresi | — | **tam ölçekli**: `view_height = pencere_yüksekliği × ölçek` → 1:50 |
| Anahtar plan · kuzey oku · grafik ölçek · durum damgası · "ölçü alınmaz" notu | meslek pratiği | motor tarafından otomatik |

Görüntü pencereleri `plot = 0` olan `G-VIEWPORT` katmanındadır; çerçeveleri
basılmaz.

### 17.2 · Aks sistemi — `tools/aks.py`

Yapı kuzeye göre **8,0°** dönüktür. Aks sistemi kuzeye değil, **yapının kendi
doğrultusuna** kurulur — profesyonel uygulamada doğru olan budur.

Motor, çeper duvar segmentlerinin uzunluk ağırlıklı baskın doğrultusunu bulur,
bu doğrultuya paralel/dik duvar hatlarını 0,40 m toleransla kümeler ve toplam
uzunluğu 1,60 m'yi aşan kümeleri aks kabul eder. Sonuç: **4 rakam aksı (1–4) +
5 harf aksı (A–E)**. Akslar balonlarıyla birlikte çizilir; akslar arası ve
toplam **zincir ölçüler gerçek DIMENSION varlığı** olarak basılır
(ISO 129-1: milimetre, ondalıksız, yazı ölçü çizgisine paralel ve üstünde,
mimari çentik uçlu).

Ölçülendirme stilleri artık ölçek başına ayrıdır (`GYM-5 … GYM-100`);
`dimscale = ölçek` olduğu için yazı kâğıtta her ölçekte 2,5 mm çıkar.

### 17.3 · Kesit işaretleri ve balon çakışması

- Kesit hattı artık plan boyunca **kesintisiz kırmızı çizgi olarak çizilmiyor**.
  Yalnız uçlarda ağır çizgi + bakış oku + pafta referanslı balon (`A` üstte,
  `A-06` altta) var — uygulama projelerinin standardı budur.
- Mahal adı, alan yazısı ve ekipman kodu konumları **önce rezerve edilir**;
  balonlar bu noktalardan kaçarak halka halka dışa doğru boş yer arar ve
  taşındıklarında kılavuz çizgi çizilir. Önceki sürümdeki üst üste binen
  balon yığılması bu şekilde çözülmüştür.

### 17.4 · Tek hat şeması artık CAD'de — `tools/tekhat_dxf.py` · pafta E-06

Şema **ölçeksiz** olduğu için model uzayına değil, paftanın **kâğıt alanına
1:1 milimetre** olarak çizilir; çerçeve ve antetle aynı uzayı paylaşır.

- **Sembol geometrisi IEC 60617 modülü M = 2,5 mm üzerine kurulur.** Her güç
  sembolü tek kutup anahtarından (`SW_POLE`) türer; niteleyici sembol cihazı
  belirler: **×** devre kesici, **—** ayırıcı. Çok kutuplu cihazlarda kutuplar
  2M aralıkla dizilir ve pivotlardan geçen **kesikli mekanik bağ** çizilir.
- Kaçak akım rölesi: tüm kutupları saran **toplam akım trafosu elipsi** + `I∆n`
  röle kutusu.
- Parafudr (SPD Tip 2): gövde + yön oku + PE inişi ve toprak sembolü.
- **Yerleşim kuralı:** bir çıkış = bir sütun = bir tablo kolonu,
  `x_n = X0 + (n − 0,5) × 26 mm`. Sembol, dallanma, etiket ve 14 tablo satırının
  tamamı aynı x ekseninde hizalıdır. Şemayı profesyonel yapan tek kural budur.
- Bara sistemi üç hatlı: **L1·L2·L3 (0,70 mm) · N · PE**, PE ucunda koruma
  toprağı sembolü. Her dallanmada dolu bağlantı noktası.
- Kaçak akım grupları üç grafik araçla birlikte gösterilir: **grup alt barası**,
  **köşeli parantez + grup etiketi**, ve sütun sırasının gruba göre dizilmesi.
  Sütunlar RCD grubuna göre sıralanır; bir grubun linyeleri **yan yanadır**.
- **Pano sınırı** kesik-nokta çizgiyle çizilir; üstü pano içi, altı saha
  kablolamasıdır. Sınırın altında klemens sırası `-X1`, iletken sayısı çentiği
  ve sahaya devam eden açık ok ucu bulunur.
- **14 satırlık veri matrisi**: çıkış no, linye, mahal·yük, faz, koruma, kesme
  kapasitesi, kaçak akım, kablo, boru, uzunluk, kurulu güç, cos φ, hesap akımı,
  gerilim düşümü. Uzun değerler iki satıra sarılır (dikey yazı kullanılmaz —
  satır yüksekliğini aşıp komşu satıra taşıyordu).
- Altta dört blok: **faz dengesi · güç özeti · hesaplar · genel notlar**.
- Cihaz etiketleri **IEC 81346-2**'ye göre: `-Q1` ana şalter, `-F0` parafudr,
  `-F1…-F5` kaçak akım röleleri, `-Q101…-Q126` linye kesicileri, `-X1` klemens,
  `-P1` sayaç.
- **4 yedek çıkış** teçhizatlı olarak çizilir (kesici var, kablo yok).

`ezdxf` **ACAD_TABLE yazamaz**; bu nedenle tüm tablolar çizgi + yazı olarak
kurulur — bu aynı zamanda her CAD'de taşınabilir olandır.

### 17.5 · Baskı ve kalem kalınlığı — dürüst not

`ezdxf`'in `LineweightPolicy.ABSOLUTE` politikası denendi ve **önizleme PDF'i
için kullanılamadı**: model uzayı içeriği görüntü penceresinden geçerken
kalınlıklar çizim ölçeğiyle çarpılıyor (0,35 mm → 17 mm). Bu yüzden önizleme
ezdxf'in göreli politikasıyla basılır.

**Gerçek kalem kalınlıkları DXF içinde katman ve varlık düzeyinde saklıdır**
(ISO 128 serisi: 0,13 / 0,18 / 0,25 / 0,35 / 0,50 / 0,70 / 1,00 mm) ve CAD'de
doğru basılır. Denetim ajanı, serinin dışında bir kalem kalınlığı bulursa hata
verir — bu turda `E-TEKHAT-BARA` 0,60 → 0,70 mm ve iki katmanın 0,09 mm kalemi
0,13 mm olarak düzeltildi. CTB dosyası taşınabilir değildir; hiçbir anlam CTB'ye
bırakılmamıştır.

### 17.6 · Teslim: TEK DOSYA

`output/Gym_Proje_Paketi.zip` artık **tek teslim dosyasıdır** — 7 klasör,
39 dosya, 24,4 MB:

```
00_OKUMA              proje notları (varsayımlar, doğrulanacaklar), depo rehberi
01_MİMARİ             mimari uygulama seti (14 pafta) · DXF · mahal listesi · rapor
02_MEKANİK            mekanik proje (9 pafta) · DXF · BoQ
03_ELEKTRİK           elektrik projesi (8 pafta) · ADP tek hat şeması (PDF + DXF)
                      · topraklama DXF · yükleme cetveli · BoQ
04_BÜTÇE VE HAKEDİŞ   keşif özeti + metraj · hakediş şablonu · bütçe takibi
05_BİRLEŞİK SET       33 paftalık tek PDF · birleşik DXF · 15 tekil pafta DXF
                      · katman listesi · otomatik denetim raporu
06_YATIRIM DOSYASI    fizibilite dosyası · sunum · 3B model · ana BoQ · renderlar
```

### 17.7 · Rev G sayısal özet

| | Rev F | Rev G |
|---|---|---|
| Pafta boyutu | A3, 1:75 | **A1 (ISO 5457), 1:50** |
| Antet | 9 alan | **ISO 7200 · 17 alan + revizyon tablosu** |
| Kenar ızgarası / bölge referansı | yok | **var (16 × 12 bölge)** |
| Aks sistemi | yok | **4 rakam + 5 harf aksı, yapı doğrultusunda (8,0°)** |
| Zincir ölçü | 5 kopuk ölçü | **5 + 9 aks zincir ölçüsü (gerçek DIMENSION)** |
| Kesit işareti | plan boyu kırmızı çizgi | **uçta işaret + bakış oku + pafta referansı** |
| Tek hat şeması | yalnız PDF | **PDF + CAD (pafta E-06, kâğıt alanında 1:1)** |
| DXF katman | 61 | **70** |
| CAD pafta | 14 | **15** |
| Teslim | 10 ayrı dosya | **tek zip · 7 klasör · 39 dosya** |
