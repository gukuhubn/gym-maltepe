# Aqua Florya elektrik maliyeti analizi

Bu klasördeki çalışma, **Nusr-Et Saltbae · Aqua Florya** şubesinin elektrik
faturasını analiz eder ve azaltma programı üretir. Gym Maltepe projesinden
bağımsızdır; yalnız aynı depoda ve aynı mühendislik disiplininde durur.

## Soru

İşveren şunu sordu: şubelerin elektrik faturası ayda 300.000 – 650.000 TL;
Aqua Florya 350.000 – 450.000 TL. Bu normal mi, değilse nasıl düşürülür?

## Cevap (özet)

Fatura, tesisin kurulu yüküne ve 2026 İstanbul ticarethane tarifesine göre
**açıklanabilir durumdadır**. Model ayda 58.033 kWh veriyor; 2026 tarifesiyle
386.309 TL ediyor ve beyan edilen bandın ortasına düşüyor (sapma %3,5).

Anormal olan tüketimin miktarı değil, **yakıt seçimi**dir: tesis normalde
doğal gazla yapılan ısıtma işlerini (40 kW teras ısıtıcı, 21 kW hava perdesi,
9,9 kW boiler) elektrikli dirençle yapıyor. Elektrikli direnç ısıtması, gazlı
radyanta göre ~4,7 kat pahalıdır. İkinci büyük kalem, havalandırmanın pişirme
olsun olmasın tam debide çalışmasıdır.

## Veri kaynağı

| Dosya | İçerik |
|---|---|
| `input/referans/ADP_Yukleme_Cetveli_REF.xlsx` | ADP yükleme cetveli R00 · 155 linye · 373,75 kW bağlı güç |
| `input/referans/ADP_REFERANS.pdf` | Proje Y-24-003-001 · 34 sayfa pano şeması |

## Üretim zinciri

```
bash tools/uret_enerji.sh
```

| Dosya | Ne yapar |
|---|---|
| `tools/enerji.py` | Yükleme cetvelini okur, 155 linyeyi 18 işlev sınıfına ayırır, işletme profillerini uygular, tüketimi, reaktif riskini ve önlem tasarruflarını hesaplar. **Bütün varsayımlar burada.** |
| `tools/enerji_tarife.py` | 2026 tarife, vergi, reaktif, yakıt, GES ve kıyaslama verisi. Her kalemde kaynak ve güven derecesi (A/B/C). |
| `tools/enerji_grafik.py` | Rapordaki dört grafiği modelden üretir. |
| `tools/build_enerji_raporu.py` | `output/Nusret_Elektrik_Maliyet_Raporu.pdf` — 19 sayfa. |
| `tools/agents/a_enerji.py` | Denetim ajanı; dört sonuçlu (geçti · kaldı · VERİ EKSİK · UYGULANMAZ). |
| `tools/denetim_enerji.py` | Ajanı çalıştırır, `data/denetim_enerji.json` yazar. |

Raporda **elle yazılmış rakam yoktur**; hepsi koddan okunur. Bir varsayım
değişince tek satır düzeltilir ve rapor yeniden üretilir.

## Denetim durumu

`ŞARTLI` — geçti 20 · kaldı 0 · şartlı 1 · VERİ EKSİK 15 · UYGULANMAZ 2

Tek şartlı bulgu: üç zamanlı ticarethane birim fiyatları tek kaynaktan
alındı, çapraz doğrulanmadı. 15 "VERİ EKSİK" kalemi, elimizde olmayan
veriyle yapılamayan kontrollerdir; geçmiş gibi gösterilmemiştir.

## En kritik eksik veri

1. **Tek bir elektrik faturası.** Tarife tipini, reaktif cezayı, gerçek
   kWh'i, birim fiyatı ve sözleşme gücünü aynı anda cevaplar.
2. **Net alan tablosu.** kWh/m² kıyası 1.200 m² varsayımına dayanıyor (V-04).
3. **Dört haftalık yük kaydı.** ADP'de enerji analizörü (-EA1) ve altı akım
   trafosu zaten kurulu; yalnız haberleşmenin uçlanması gerekiyor.
