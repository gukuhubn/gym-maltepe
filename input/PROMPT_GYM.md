# MALTEPE / İDEALTEPE — MOBİLYA MAĞAZASI → SPOR SALONU DÖNÜŞÜMÜ
### Claude Code Brief · Rev A

---

## 0 · ROL VE GÖREV

Kıdemli mimar + müteahhit + yatırım analisti olarak, **mimar olmayan bir işletmeciye** teslim edilecek bir dönüşüm dosyası üret. Teslimatlar Türkçe. Üç çıktı:

- **A** — Ana dosya: A3 yatay, ~12 sayfa tasarım + yol haritası + maliyet paketi (§6)
- **B** — 3D model + render prompt seti (§7)
- **C** — BoQ / keşif-metraj çalışma dosyası (.xlsx, fiyat sütunları boş) (§8)

Otonom çalış, soru sorma — her açık nokta için bu brief'te varsayılan var. Teslimden önce §11 QA protokolünü uygula.

---

## 1 · GİRDİLER (`./input/` klasöründe)

| Dosya | İçerik |
|---|---|
| `TRIMODE-Yerlesim_Plani.pdf` | Mevcut konsept yerleşim: ortada altıgen "TRIMODE ARENA 4 LAYER 10.60 m²", çevresinde ekipman footprint'leri (244×62, 175×232, 155×39 ×2, 84×150, 245×74 ×2 — cm), KADIN/ERKEK soyunma + DUŞ ×2 + WC, BANKO resepsiyon, ÖN BAHÇE ve ARKA BAHÇE |
| `TRIMODE-Duvar_Plani.pdf` | Duvar planı — mevcut/kalacak/yeni duvar ayrımı |
| `TRIMODE-Yikim_Sokum.pdf` | Yıkım-söküm paftası (mobilyacıdan kalan imalatların sökümü) |
| `TRIMODE-Alan_Dagilimi.pdf` | **Alan dağılımı — net m² değerlerini BURADAN çıkar, tüm hesapların temeli budur** |
| `ESAT-FINAL.dwg`, `ESAT-FINAL (1).dwg` | AutoCAD dosyaları |

**DWG uyarısı:** ezdxf DWG okumaz. Sırasıyla dene: (1) ortamda `dwg2dxf` / LibreDWG var mı, (2) yoksa PDF'lerden ölçeklendirerek çalış ve her metrajın yanına "PDF'den ölçeklendirildi, ±%5" notu düş, (3) BUILD_NOTES'a "işverenden DXF (R2010) export istenmeli" maddesini yaz. Bu, projeyi durduran bir engel değil.

---

## 2 · PROJE TANIMI VE VARSAYIMLAR

Maltepe / İdealtepe'de **kirası imzalanmış**, hâlen mobilya mağazası olarak kullanılan ticari bir birim, butik fonksiyonel antrenman stüdyosuna dönüştürülüyor. **Ekipman zaten satın alınmış** — yerleşim mevcut ekipmana göre çözülecek, ekipman maliyeti bütçe dışı (ayrı bilgi satırı olarak gösterilir).

Bütçe hedefi: **mütevazı / maliyet-etkin**. Prensip: mevcut TRIMODE yerleşimini koru, duvar hareketini minimumda tut, parayı üç yere harca — ıslak hacim, zemin, aydınlatma/havalandırma.

**Doğrulanacak varsayımlar** (her çizim ve tabloya "yerinde doğrulanacak" notu düş):
- Net kullanım alanı, tavan yüksekliği (**Alan Dağılımı PDF'inden çek; yoksa TBD bırak ve hesapları parametrik kur**)
- Mevcut pis su bağlantısının kotu ve konumu
- Zemin yük kapasitesi, üst katta konut olup olmadığı
- Mevcut elektrik pano gücü (kW) ve trifaze var mı
- Doğalgaz / sıcak su kaynağı

---

## 3 · TASARIM YAKLAŞIMI — KİLİTLİ KARARLAR

1. **Yerleşim korunur.** Altıgen arena merkez, ekipman çevrede, soyunma-duş-WC güney blokta, banko girişte. Duvar değişikliği yalnızca mevzuat veya sirkülasyon gerektiriyorsa.
2. **Islak hacim = maliyetin kalbi.** Yönetmelik gereği soyunma odalarının **içinde** en az 2 duş + 2 tuvalet, sürekli sıcak su. Gider kotu yerçekimiyle çözülmüyorsa iki seçenek üret ve karşılaştır: (A) ıslak hacim zeminini 15-20 cm yükselt (ucuz, basamak getirir), (B) foseptik/gri su pompası (kot serbest, bakım ve arıza riski). Her ikisinin maliyetini ayrı göster.
3. **Zemin stratejisi — 3 bölge:** ağırlık/arena alanı 20-40 mm kauçuk kaplama (düşürme ve akustik), kardiyo/serbest alan sporcu vinil veya kauçuk, ıslak hacim seramik R11. Yönetmelik zemin kaplamasını şart koşuyor; çıplak beton kabul edilmez.
4. **Akustik ve titreşim** üst katta konut varsa ayrı kalem: ağırlık alanında çift kat kauçuk / kauçuk altı titreşim matı. Aksi hâlde şikâyet → ruhsat riski.
5. **Havalandırma:** yönetmelik "sporcu sayısına göre yeterli havalandırma" ve salon ısısı ≥18 °C istiyor. Mütevazı çözüm: mekanik taze hava + egzoz fanı + ıslak hacim egzozu; ısıtma/soğutma için VRF yerine split klima kümesi. Kapasiteyi kişi başı hava debisi üzerinden kabaca hesapla ve göster.
6. **Güvenlik detayları (yönetmelik maddeleri):** keskin köşe ve kolonların yumuşak malzemeyle kaplanması, yangın söndürücüler, engelli erişimi tedbirleri, acil çıkış genişlikleri — hepsi BoQ'da satır olarak yer alacak.
7. **Aydınlatma:** lineer LED armatür, arena üzerinde daha yüksek lux; mütevazı ama fotojenik (render ve sosyal medya için kritik).
8. **Dinlenme alanı:** yönetmelik en az 15 m² dinlenme salonu istiyor — mevcut planda karşılığını bul (banko/bekleme bölgesi) ve m² olarak göster; yetmiyorsa çözüm öner.

---

## 4 · DOĞRULANMIŞ MEVZUAT (araştırıldı — yeniden araştırma, yalnız çelişki varsa teyit et)

**Sıra kritik: önce GSB, sonra belediye.**

- **Gençlik ve Spor İl Müdürlüğü — Tesis Açılış İzni.** Özel Beden Eğitimi ve Spor Tesisleri Yönetmeliği kapsamında; başvuru sonrası **komisyon tesisi yerinde tetkik ediyor** ve tutanak düzenliyor, uygunsa yeterlilik belgesi + il başkanı onayı, ardından bir defaya mahsus **tescil ücreti**.
- **Belediye (Maltepe) — İşyeri Açma ve Çalışma Ruhsatı.** Belediye, GSİM uygunluk yazısını talep ediyor. Süreç tipik 15-30 iş günü. Gerekli tipik evrak: kimlik/şirket evrakı, vergi levhası, kira sözleşmesi/tapu, yapı kullanma izni, itfaiye raporu, sağlık müdürlüğü raporu, **bina bağımsız değilse kat malikleri muvafakatnamesi**, mimar onaylı vaziyet/yerleşim planı.
- **Yönetmeliğin aradığı fiziki şartlar** (tasarımın karşılaması gereken kontrol listesi): soyunma odalarında sporcu sayısı kadar dolap/askılık, aydınlatma ve havalandırma, oda ısısı 18 °C, hijyen; **kadın-erkek birlikte kullanılan tesislerde soyunma odalarının içinde en az 2 duş + 2 tuvalet**; çalışma boyunca sıcak su; salon ısısı ≥18 °C ve sporcu sayısına göre havalandırma; zeminin spor dalına uygun malzemeyle kaplanması; yangın söndürme ekipmanı; keskin kenar/kolonların darbe hafifletici malzemeyle kaplanması; engellilere ve can güvenliğine yönelik tedbirler; **kullanım alanı en az 15 m² dinlenme salonu**.
- **Antrenörlük:** salonda bizzat ders verecekse SGM onaylı antrenörlük belgesi; yalnız işletmeciyse lisanslı antrenör istihdamı yeterli olabiliyor.
- **Diğer:** vergi dairesi kaydı, SGK, hijyen belgesi, anlaşmalı doktor/klinik sözleşmesi istenebiliyor.
- **En sık hata** (kaynaklarda bizzat böyle geçiyor): mekânın fiziki uygunluğu — tavan yüksekliği, havalandırma, m² — kontrol edilmeden kiralanması. **Bu projede kira imzalanmış durumda; bu yüzden ilk teslimat uygunluk kontrolü olacak (§6 sayfa 3).**

Tüm mevzuat sayfalarına şu notu koy: "Yerel uygulama farklılık gösterebilir; Maltepe Belediyesi Ruhsat Müdürlüğü ve İstanbul GSİM'den güncel liste teyit edilmelidir."

---

## 5 · MALİYET ÇERÇEVESİ

Para birimi **TL**, tarih damgası zorunlu ("Ağustos 2026 piyasa mertebesi"). Referans çıpa: 2026 İstanbul orta segment komple yenileme ≈ **5.500-8.500 TL/m²**; ticari dönüşümde açık salon alanı bu bandın altında, ıslak hacim üstünde kalır — bu yüzden **tek m² fiyatı kullanma, kalem bazlı kur.**

Maliyeti üç kolonlu göster: **Miktar × Birim fiyat (düşük-yüksek) = Tutar bandı.**

Ana başlıklar: yıkım-söküm + moloz nakli · duvar/alçıpan imalatları · ıslak hacim (tesisat + seramik + vitrifiye + kabin) · zemin kaplama (3 bölge ayrı) · elektrik (pano, priz, aydınlatma, zayıf akım) · mekanik (havalandırma, klima, sıcak su) · boya-dekorasyon · banko/soyunma dolapları (marangoz) · yangın-güvenlik-engelli kalemleri · tabela/dış görünüş · şantiye genel giderleri (%8-10) · **beklenmedik giderler %15** (ıslak hacim belirsizliği yüksek).

**Ekipman bütçe dışı** — ayrı bilgi satırı: "ekipman işverence temin edilmiştir".

Ayrıca tek sayfalık **açılış öncesi nakit ihtiyacı** özeti: tadilat + ruhsat/harç/tescil + ilk 3 ay kira + personel + pazarlama. Referans: 2026 kaynaklarında butik salon başlangıç bütçesi 500.000-1.000.000 TL, orta ölçekli 1.500.000-3.000.000 TL (ekipman dahil) — bu çıpayı "karşılaştırma" olarak göster, kendi hesabının yerine koyma.

---

## 6 · TESLİMAT A — ANA DOSYA (A3 yatay, Türkçe, ~12 sayfa)

1. **Kapak** — proje adı, konum (Maltepe/İdealtepe), Rev A, tarih, "ön tasarım — yerinde doğrulanacak".
2. **Projeye bakış** — tek paragraf kapsam, 4 karar kartı (mevzuat sırası · ıslak hacim çözümü · zemin stratejisi · bütçe), 6 rakam kutucuğu (m², kişi kapasitesi, tadilat bütçe bandı, ruhsat süresi, takvim, beklenmedik pay).
3. **UYGUNLUK KONTROL SAYFASI (kritik — kira imzalandı)** — yönetmelik şartları tablo hâlinde: her madde × mevcut durum × gerekli aksiyon × risk rengi. Muvafakatname, bağımsız bölüm niteliği, gider kotu, tavan yüksekliği, dinlenme salonu 15 m², 2 duş + 2 WC burada tek tek işaretlenir. **Kırmızı çıkan her madde için çözüm ve maliyet etkisi yaz.**
4. **Mevcut durum** — yerleşim/duvar/yıkım paftalarından üretilmiş özet + alan dağılımı tablosu + söküm kapsamı.
5. **Öneri planı** (renk kodlu: kırmızı yeni, gri mevcut, mavi kaldırılan) + sirkülasyon ve acil çıkış analizi + ekipman yerleşimi (mevcut ekipman ölçüleriyle).
6. **Zemin ve akustik paftası** — 3 bölgeli zemin planı, kesit detayları (kauçuk kalınlıkları, titreşim matı), lejant.
7. **Islak hacim çözümü** — plan + kesit + A/B seçenek karşılaştırması (yükseltme vs pompa), tesisat şeması basit seviyede.
8. **Elektrik + mekanik şema** — aydınlatma yerleşimi (lux hedefleriyle), priz/zayıf akım, havalandırma debisi ve klima yerleşimi.
9. **Yol haritası — ruhsat ve başvurular** — GSB → belediye sıralı akış, evrak kontrol listesi, kurum-kişi-ne zaman tablosu, süre takvimi, harç/tescil kalemleri.
10. **Maliyet planı** — §5 yapısına göre kalem bazlı tablo, alt toplamlar, senaryo karşılaştırması (minimum / önerilen), açılış öncesi nakit ihtiyacı.
11. **İş programı ve şantiye sırası** — 10-14 adımlık uygulama sırası (söküm → tesisat → duvar → sıva/alçı → zemin → elektrik-mekanik montaj → boya → marangoz → temizlik-kabul), süre tahmini, kritik yol.
12. **Risk kaydı + sonraki 5 adım** — olasılık/etki/önlem tablosu (muvafakatname, gider kotu, komisyon tetkiki, bütçe sapması, gecikme), ve render prompt setine referans.

## 7 · TESLİMAT B — FOTOGERÇEKÇİ RENDER'LAR (GEMINI API ile, CC üretecek)

**Bu işi sen yapacaksın — harici modele prompt devretme.** Orange/Aykut-Ardit projesinde kurulan image-to-image hattının aynısı: ortamda tanımlı **Gemini API** anahtarıyla (`gemini-3-pro-image` veya ortamda geçerli güncel görsel modeli) render üret. Ağ politikası Google API'lerini engelliyorsa bunu net bir engel olarak raporla ve §7.C'ye düş.

**A · Gerçek ÖNCE/SONRA çiftleri (öncelik 1 — en ikna edici çıktı)**
İşverenin gönderdiği mevcut durum fotoğraflarını (mobilya mağazası hâli) image-to-image girdisi olarak kullan; her fotoğraf için aynı kamera açısında "sonra" görselini üret. Perspektif, pencere/kolon konumları ve tavan yüksekliği korunsun. En az 3 çift: ① ana salon ② giriş/banko bölgesi ③ soyunma koridoru. Fotoğraf gelmediyse bu bloğu atla, BUILD_NOTES'a yaz.

**B · Tasarım render'ları (öncelik 2)**
`site/` altında Three.js kütle modeli kur (vendored, build adımı yok): mekân kabuğu, altıgen arena, ekipman kütleleri, soyunma bloğu, banko, aydınlatma; ölçüler `data/dimensions.json`'dan. 4 sabit kamera açısından PNG al (① girişten arenaya ② arenadan soyunmaya ③ ağırlık alanı ④ banko/karşılama) ve bu PNG'leri image-to-image girdisi yaparak fotogerçekçi hâle getir — böylece geometri plana sadık kalır, model halüsinasyon yapmaz.
Her açı için **2 stil varyantı** üret: (i) ham endüstriyel — açık tavan, siyah metal, beton dokusu, (ii) sıcak minimal — ahşap aksan, yumuşak ışık, açık renk duvar. İşletmeci seçsin.

**C · Yedek plan (yalnız API erişimi yoksa)**
`Render_Promptlari.md` üret: her açı için hazır İngilizce prompt (malzeme paleti, aydınlatma, lens, mekân ölçüsü, ekipman tanımı) + Three.js PNG'leri, işveren harici bir modele yapıştırsın.

**Ortak kurallar:** Üretilen her görselin altına "temsilî görsel — imalat ölçüsü değildir" notu. Görselleri `output/render/` altına, açı ve varyant adıyla kaydet (`01_giris_arena_endustriyel.png`). Ekipman görsellerde işverenin **gerçekten satın aldığı** ekipmana benzesin (liste geldiyse ona göre tarif et). Model isimleri/marka logoları üretme.

**Ayrıca tek dosya offline HTML** (`Gym_Model.html`) derle — ES module ve fetch kullanma, inline et; WhatsApp'tan paylaşılabilsin, render galerisi de içine gömülsün.

## 8 · TESLİMAT C — BoQ (.xlsx)

`xlsx` skill'ini oku, sonra üret. Sayfalar: ① Özet (başlık bazlı toplamlar, senaryo seçimi) ② Detay metraj (Poz No · Tanım · Birim · Miktar · Birim Fiyat [BOŞ] · Tutar [formül]) ③ Ekipman bilgi sayfası (işverence temin) ④ Varsayımlar ve metraj dayanağı. Formüller canlı olsun — işletmeci teklif geldikçe birim fiyat girsin, toplam kendiliğinden dönsün.

---

## 9 · ÇİZİM VE SUNUM STANDARTLARI

Orange projesindeki dil: navy başlık bandı, copper vurgu, kırmızı=yeni / gri=mevcut / mavi=kaldırılan, ölçü çizgileri, lejant, her sayfada altbilgi ("Ön tasarım — yerinde doğrulanmadan ve ruhsat alınmadan uygulama yapılamaz") ve sayfa numarası. **Türkçe için Unicode TTF (DejaVu) gömülmesi zorunlu** — core Helvetica ş/ğ/ı/İ içermez. Python `.upper()` Türkçe i→İ hatasına dikkat (Orange'da yakalandı).

## 10 · TEKNİK YIĞIN

Python + ReportLab (vektör kontrolü), Pillow, openpyxl (xlsx), Three.js (vendored). Modüler: `helpers.py` + sayfa modülleri + `build.py`.

## 11 · QA PROTOKOLÜ (zorunlu)

1. PDF'i üret → her sayfayı PNG'ye render et (pdftoppm yoksa pypdfium2).
2. Her sayfayı gözle incele: taşma, çakışma, kırpılma, okunmayan ölçü.
3. Türkçe glif taraması (ş ğ ı İ ü ö ç) her sayfada.
4. Çapraz tutarlılık: m² değerleri = alan dağılımı = BoQ metrajı = maliyet tablosu; TL rakamları her yerde aynı.
5. Kırmızı takım: "şüpheci Maltepe ruhsat memuru + GSİM komisyon üyesi" gözüyle uygunluk sayfasını denetle — atlanan yönetmelik maddesi var mı?
6. xlsx: formülleri test et, toplamlar doğru mu.
7. Teslim: `output/` + `BUILD_NOTES.md` (varsayımlar, doğrulanacaklar listesi, işverenden istenecek bilgiler).

## 12 · İŞVERENDEN İSTENECEKLER (BUILD_NOTES'a yaz, dosyada da bir kutuda göster)

DXF export (R2010) · mevcut durum fotoğrafları · net m² ve tavan yüksekliği · satın alınan ekipman listesi (marka/model/ölçü/ağırlık) · mevcut pis su bağlantısı fotoğrafı ve kotu · elektrik pano gücü · tapu bağımsız bölüm niteliği · bina bağımsız mı, değilse yönetim/kat malikleri durumu · hedeflenen açılış tarihi ve üye kapasitesi.

---
*Brief sonu. Sonuca kadar çalıştır.*
