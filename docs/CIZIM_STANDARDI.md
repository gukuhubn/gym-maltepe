# GYM MALTEPE — OFİS ÇİZİM STANDARDI

Kod karşılığı: `tools/standart.py` (çizim motorları ve `a_standart` ajanı buradan okur).
Bu belge ile kod ayrışırsa denetim ajanı hata verir.

**Dayanaklar** (`tools/kaynak.py`): STD-01 Mimarlar Odası *Mimari Proje Çizim ve Sunuş
Standartları* (ana kaynak, verbatim: `docs/kaynak/`), STD-02 İTÜ notu, STD-03 İller Bankası
şartnamesi, CZM-01/02 MEGEP gösterim modülleri, ISO 5457 · 7200 · 128-2 · 3098.

## 1. Aşama ve ölçek
| Aşama | Kod | Ölçekler | Bu projede |
|---|---|---|---|
| Uygulama projesi | UP | 1/100 · 1/50 | A-, M-, E- paftaları 1/50, A1 |
| Sistem detayı | SD | 1/20 · 1/10 · 1/5 | P-01…P-04, 1/20, A2 |
| İmalat detayı | ID | 1/5 · 1/2 · 1/1 | P-05, 1/5, A2 |

## 2. Numaralandırma (STD-01 §11–12)
- Kapı **K1…Kn** · camlı kapı **CK** · camekan **CMK** · pencere **P** · giriş kapısı **GK** · gömme dolap **GD** · merdiven **M**
- Mahal: bodrum **B-01**, zemin **Z-01**, katlar **101**… — numara **elips** içinde.
- Bu proje zemin kattadır → **Z-01 … Z-10**.

## 3. Doğrama etiketi (STD-01; İTÜ §11)
Kapı/pencere eksenine dik kısa çizgi; **çizgi üstünde yükseklik, altında genişlik** (cm),
solunda kod. Ölçü **kaba yapı boşluğudur**, kanat değil. Örnek: `K5 · 200 / 70`.

## 4. Kapının planda gösterimi (MEGEP Şekil 2.51–2.55)
1. Duvarda kapı genişliği kadar boşluk açılır — **bütün katmanlar kesilir**, söve çizgisi kesilen kalemde.
2. Duvar kenarlarına **kasa** (45 mm profil).
3. **Pervaz** kasa–duvar birleşimini iki yüzde örter (60 mm).
4. **Kanat** boşluğu kapatacak uzunlukta, 40 mm kalınlıkta.
5. Açılış yayı, menteşe merkezli.

Ölçeğe göre: 1/100 yalnız yay + etiket · 1/50 kasa şematik, kanat tek çizgi · ≤1/20 tam.

## 5. Ölçülendirme (STD-01)
**Dış ölçüler**, dıştan cepheye doğru dört çizgi: 1 blok ölçüsü · 2 cephe hareketleri · 3 taşıyıcı akslar · 4 doluluk-boşluk.
**İç ölçüler**, her hacimde enine ve boyuna **ikişer** çizgi: 1 net en/boy · 2 kapı/pencere genişlikleri ve komşu duvara uzaklıkları.
Satır aralığı kâğıtta 7 mm; ölçü yazısı 2,5 mm; gerçek `DIMENSION` nesnesi, elle yazılmış ölçü metni yasak.

## 6. Kotlar (STD-01)
Esas giriş önü tretuvar **±0,00**. Her döşeme için **bitmiş ve kaba yapı kotu ayrı ayrı**. Asma tavan **alt yüzü kotu** yazılır.

## 7. Kesit (STD-01)
En az iki kesit. Mahal **kodu ve adı** yazılır. Üç ölçü çizgisi: (1) kaba kat yüksekliği döşeme üstünden döşeme üstüne; (2) kaplama kalınlığı, kapı/pencere/bölme yükseklikleri, lento–tavan; (3) asma tavan altı – bitmiş döşeme **net yükseklik**. Asma tavan içi tesisat **gerçek boyutlarıyla**.

## 8. Çapraz referans (İTÜ §10)
Plan/kesitte detay çağrısı **(Bak: SD-xx)**; detay paftasında **Bak pafta: UP-01, UP-08 …**

## 9. Sistem ve imalat detayı (STD-01 §14.6)
Plan + kesit + görünüş **aynı ölçek, aynı pafta**. Tüm malzeme isimleri ve açılımları; poz/referans no; ilgili mahal no ve UP pafta no; paftanın köşesine **imalatta dikkat edilecek hususlar**.

## 10. Kalem serisi (ISO 128-2) — 1/100 mm
kesilen 70 · görünüş sınırı 50 · görünen 35 · ölçü/anotasyon 25 · arkada kalan 18 · tarama/katman 13 · çerçeve 100.
Her paftada **ÇİZGİ HİYERARŞİSİ** lejantı gerçek kalınlıklarla basılır.

## 11. Yazı (ISO 3098) — kâğıt mm
1,8 mikro · 2,5 ölçü/metin · 3,5 etiket · 5 alt başlık · 7 başlık. Asgari 1,8 mm.

## 12. Katmanlar
`DİSİPLİN-NESNE[-NİTELİK]`, 6–24 karakter, A/M/E/G önekleri. Renk, çizgi tipi ve kalınlık **ByLayer**.

## 13. Ölçeğe göre ifade (MEGEP Tablo 2.1 · 2.7 · 2.8)
| Ölçek | Duvar | Doğrama |
|---|---|---|
| 1/100 | poché, içi koyu | yalnız yay |
| 1/50 | katman çizgileri; taşıyıcı içi koyu | kasa şematik, kanat çizgi |
| 1/20 | levha · dikme @400 · yalıtım · kaplama ayrı ayrı | kasa, pervaz, kanat kalınlığı |
| 1/10 | malzeme dokusu (tuğla sırası, derz) | birleşim elemanları |
| 1/5 | vida, bant, profil et kalınlığı, silikon derzi | imalat |

Kâğıtta 0,45 mm'den ince katman bant değil, **ekseninde tek çizgi** (su yalıtımı kendi kaleminde, 0,35).

## 14. Malzeme gösterimi (MEGEP Şekil 2.24–2.47)
Yalnız `acad.pat`'ta standart desenler. Tarama aralığı **kâğıtta sabit**, desenin taban aralığından hesaplanır.
Su yalıtımı: dolu/boş blok (2.44) · ısı/ses yalıtımı: zikzak (2.43) · beton: AR-CONC · tuğla: ANSI32, ≤1/10'da sıra dokusu · seramik: derz çizgisi.
Her paftada **MALZEME GÖSTERİMİ** tablosu.

## 15. Pafta (ISO 5457 · 7200)
A1 841×594 / A2 594×420; cilt payı 20; kenar 10; bölge ızgarası 50 mm; antet 180×92 (ISO 7200 alanları); durum damgası; "ÖLÇÜ ALINMAZ"; grafik ölçek; kuzey (döndürülmüş görüntü penceresinde ok da döner).
