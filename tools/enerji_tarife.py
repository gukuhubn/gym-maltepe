# -*- coding: utf-8 -*-
"""2026 TÜRKİYE ELEKTRİK TARİFE VERİLERİ — araştırma çıktısı.

Bu dosya ARAŞTIRMA SONUCUDUR, kabul değildir. Her kalemde kaynak ve
güven derecesi vardır. Doğrulanamayan veriler açıkça işaretlidir.

  güven = "A"  birincil kaynak veya birden çok bağımsız kaynakta aynı
  güven = "B"  tek kaynak, makul, çapraz doğrulanmadı
  güven = "C"  kaynaklar çelişiyor veya türetilmiş

ÖNEMLİ SINIR: EPDK'nın kendi tarife tabloları (epdk.gov.tr) dinamik
sayfa yapısı nedeniyle doğrudan çekilemedi. Aktif enerji birim fiyatları
ikincil kaynaklardan derlendi ve aralarında %8'e varan fark var.
BİR GERÇEK FATURA GÖRÜLMEDEN HİÇBİR YATIRIM KARARI VERİLMEMELİDİR.
"""

ARASTIRMA_TARIH = "21 Eylül 2026"
BOLGE = "İstanbul · BEDAŞ bölgesi · görevli tedarikçi CK Enerji Boğaziçi"

# ───────────────────────── vergi ve fon yapısı ───────────────────────────────
VERGI = {
    "enerji_fonu": (0.01, "A", "Enerji bedeli üzerinden %1"),
    "trt_payi":    (0.00, "A", "25 Aralık 2021'den itibaren elektrik "
                               "faturalarından KALDIRILDI"),
    "btv":         (0.05, "A", "Belediye Tüketim Vergisi — ticarethane %5 "
                               "(sanayi %1)"),
    "kdv":         (0.20, "A", "Katma Değer Vergisi %20"),
}

# ───────────────────────── birim fiyatlar (TL/kWh) ───────────────────────────
# 4 Nisan 2026 tarifesi. 1 Ekim 2026 (Q4) tarifesi 21 Eylül itibarıyla
# HENÜZ AÇIKLANMAMIŞTIR.
DAGITIM_TICARETHANE = 2.081065   # TL/kWh · vergi/fon/pay hariç · güven A
DAGITIM_SANAYI      = 1.182457   # TL/kWh · güven A
AKTIF_TICARETHANE   = 3.27       # TL/kWh · vergi hariç · güven C (türetilmiş)

TARIFE_NOT = (
    "Vergi hariç toplam (aktif+dağıtım) 5,35 TL/kWh olarak yayımlanmıştır; "
    "dağıtım bedeli 2,081 TL/kWh EPDK tablosundan alındığı için aktif enerji "
    "bileşeni fark olarak 3,27 TL/kWh bulunmuştur. Vergiler dâhil nihai "
    "fiyat bağımsız kaynaklarda 6,42 – 7,33 TL/kWh bandındadır."
)

# Üç zamanlı ticarethane — VERGİLER DÂHİL (tek kaynak, güven B)
UC_ZAMANLI = {
    "T1": (7.39, "06:00–17:00", "gündüz"),
    "T2": (10.50, "17:00–22:00", "puant"),
    "T3": (4.91, "22:00–06:00", "gece"),
}
UC_ZAMANLI_GUVEN = "B"

# ───────────────────────── reaktif ────────────────────────────────────────────
REAKTIF_BEDEL = 3.493698     # TL/kVArh · vergi/fon/pay hariç · güven A
REAKTIF_ESIK  = {"enduktif": 0.20, "kapasitif": 0.15,
                 "kosul": "bağlantı gücü ≥ 50 kVA",
                 "alt_50kva": {"enduktif": 0.33, "kapasitif": 0.20}}
REAKTIF_NOT = ("Oran aşıldığında ölçülen reaktif enerjinin TAMAMI "
               "bedellendirilir (muhafazakâr kabul; kaynaklar çelişiyor).")

# ───────────────────────── piyasa ────────────────────────────────────────────
SERBEST_LIMIT_KWH   = 500      # kWh/yıl · 2026 · güven A · Kurul Kararı 14039
SKTT_LIMIT_TIC_KWH  = 15_000   # kWh/yıl · 2026 · güven A
SKTT_KBK            = 1.0938   # ticarethane/sanayi · güven A
PTF_2026 = {   # TL/MWh · aylık ortalama
    "Ocak-Mayıs (ort.)": (1644.71, "B"),
    "Haziran":           (1240.16, "B"),
    "Temmuz":            (2699.61, "A"),
    "Ağustos":           (None,    "—"),
    "Eylül (kısmi)":     (2444.19, "C"),
}
YEKDEM_2026 = {"Nisan": 574.54, "Mayıs": 602.51, "Haziran": 580.99,
               "Temmuz": 189.15, "Ağustos": 213.89, "Eylül": 330.66,
               "Ekim": 332.82, "Kasım": 302.57, "Aralık": 224.02}
TEDARIKCI_INDIRIM = (0.05, 0.15, "B",
                     "İndirim YALNIZCA aktif enerji bileşenine uygulanır; "
                     "dağıtım bedeli, BTV, fon ve KDV kapsam dışıdır.")

# ───────────────────────── GES ────────────────────────────────────────────────
GES = {
    "mahsuplasma": ("SAATLİK", "A",
        "2 Nisan 2026 / RG 33212 · yürürlük 1 Mayıs 2026. Aylık mahsuplaşma "
        "yalnız MESKEN abonelerinde sürüyor. Üretim fazlası artık bedelsiz "
        "olarak YEKDEM'e devredilir, ödeme yapılmaz."),
    "ticari_limit_kw": (100, "B", "EPDK Kurul Kararı 14353 · 26 Şubat 2026"),
    "uretim_tavani": ("yıllık tüketimin 2 katı", "A", ""),
    "ozgul_uretim_kwh_kwp": (1329, "A",
        "PVGIS v5.2 · SARAH2 · İstanbul 41,008°K 28,978°D · 30° güney · "
        "çatıya entegre · sistem kaybı %14. Serbest duran optimum: 1385."),
    "maliyet_tl_kwp": {50: 40500, 100: 31500, 250: 24000, 500: 25650,
                       1000: 22500},
    "maliyet_guven": "B",
    "maliyet_not": "Tek firmanın Nisan–Mayıs 2026 EPC listesi, KDV hariç.",
    "aylik_uretim": [61.7, 69.9, 104.6, 129.5, 143.6, 149.5,
                     162.0, 156.4, 125.5, 95.6, 72.8, 58.2],
}

# ───────────────────────── kıyaslama ─────────────────────────────────────────
BENCHMARK = [
 ("ENERGY STAR / CBECS · Restaurant", 1027, "kWh/m²/yıl", "toplam enerji", "A",
  "ABD ulusal medyan · Portfolio Manager Ağustos 2024 · site EUI 325,6 kBtu/ft²"),
 ("ENERGY STAR / CBECS · Fast Food", 1270, "kWh/m²/yıl", "toplam enerji", "A",
  "ABD ulusal medyan"),
 ("CBECS 2018 · Food service", 830, "kWh/m²/yıl", "toplam enerji", "A",
  "EIA · ticari bina ortalamasının ~4 katı"),
 ("CIBSE TM46 · Restaurant", 460, "kWh/m²/yıl", "toplam (90 elektrik + 370 fosil)",
  "A", "İngiltere · 2008 · Avrupa iklimine daha yakın"),
 ("CIBSE TM46 · Bar/pub", 480, "kWh/m²/yıl", "toplam (130 elektrik + 350 fosil)",
  "A", "İngiltere · 2008"),
 ("Türkiye · restoran", None, "kWh/m²/yıl", "—", "—",
  "BULUNAMADI · BEP-TR'de restoran kategorisi için yayımlanmış referans yok"),
]

SON_KULLANIM_PAY = [   # ENERGY STAR · full-service restaurant · Ocak 2014
 ("Mutfak / pişirme",            0.35),
 ("İklimlendirme (HVAC)",        0.28),
 ("Bulaşık, temizlik, sıcak su", 0.18),
 ("Aydınlatma",                  0.13),
 ("Soğutma",                     0.06),
]
SON_KULLANIM_KAYNAK = ("ENERGY STAR Guide for Cafés, Restaurants and "
                       "Institutional Kitchens · Ocak 2014 · güven A")
DCKV_TASARRUF = (0.30, 0.50, "A",
                 "Talep kontrollü mutfak havalandırması davlumbaz enerjisini "
                 "%30–50 azaltır — ENERGY STAR kılavuzu.")
CKV_HVAC_PAY = (0.75, "B",
                "Mutfak havalandırması HVAC yükünün %75'ine kadarını "
                "oluşturabilir.")

DOGRULANAMAYAN = [
 ("1 Ekim 2026 (Q4) tarifesi", "21 Eylül itibarıyla açıklanmamış"),
 ("1 Temmuz 2026 tarife değişikliği", "“%38 zam” iddiası teyit edilemedi; "
  "dağıtım tarafında değişiklik yok"),
 ("EPDK resmi tarife tablosu", "epdk.gov.tr dinamik sayfa — çekilemedi"),
 ("Kayıp-kaçak bedeli ayrı kalemi", "2016'dan beri dağıtım bedeline gömülü"),
 ("TEİAŞ iletim bedeli sayısal değerleri", "ekli PDF içinde"),
 ("Çift terimli güç bedeli birimi", "tablodaki değerin birimi belirsiz"),
 ("YEK-G sertifika piyasa fiyatı", "EPİAŞ uzlaştırma dosyası içinde"),
 ("Tedarikçi bazında somut indirim oranı", "yalnız %5–15 genel bant"),
 ("Aynı / farklı ölçüm noktası mahsuplaşması", "hiçbir kaynak ele almıyor"),
 ("Kapasitif reaktif için ayrı birim fiyat", "EPDK tek reaktif bedel veriyor"),
 ("Türkiye restoran kWh/m²/yıl kıyas değeri", "yayımlanmış veri yok"),
]


# ───────────────────────── senaryo kurucusu ──────────────────────────────────
def _kur(aktif, dagitim, ad, not_=""):
    fon = aktif*VERGI["enerji_fonu"][0]
    btv = aktif*VERGI["btv"][0]
    ara = aktif+dagitim+fon+btv
    kdv = ara*VERGI["kdv"][0]
    top = ara+kdv
    return {"ad": ad, "aktif": aktif, "dagitim": dagitim, "fon": fon,
            "btv": btv, "kdv": kdv, "birim": top, "not": not_,
            "bilesen": [("Aktif enerji", aktif), ("Dağıtım bedeli", dagitim),
                        ("Enerji fonu %1", fon), ("BTV %5", btv),
                        ("KDV %20", kdv)]}


SENARYO = {
 "MEVCUT": _kur(AKTIF_TICARETHANE, DAGITIM_TICARETHANE,
    "Ticarethane AG · tek terimli · tek zamanlı",
    "4 Nisan 2026 tarifesi. Bağımsız kaynaklar nihai fiyatı 6,42–7,33 TL/kWh "
    "bandında veriyor; model bandın ortasındadır."),
 "INDIRIMLI": _kur(AKTIF_TICARETHANE*(1-0.10), DAGITIM_TICARETHANE,
    "İkili anlaşma · aktif enerjide %10 indirim",
    "İndirim yalnız aktif enerjiye uygulanır."),
 "INDIRIMLI_15": _kur(AKTIF_TICARETHANE*(1-0.15), DAGITIM_TICARETHANE,
    "İkili anlaşma · aktif enerjide %15 indirim", ""),
}

# Üç zamanlı senaryo — restoranın akşam ağırlıklı profiliyle
def uc_zamanli_birim(pay):
    return sum(UC_ZAMANLI[k][0]*pay[k] for k in ("T1", "T2", "T3"))


# Yatırım maliyetleri — araştırma tamamlanınca doldurulur
YATIRIM = {}


# ═══════════════════════ YAKIT MALİYETİ KARŞILAŞTIRMASI ═════════════════════
# 1 kWh ISI üretmenin maliyeti — faturanın asıl kaldıracı buradadır.
DOGALGAZ = {
    "tl_sm3": (13.45, "B", "İstanbul perakende (konut referansı) · "
                           "akillitarife 4 Nisan 2026. İGDAŞ ticarethane/"
                           "serbest tüketici tarifesi BULUNAMADI — igdas.istanbul "
                           "21.09.2026'da HTTP 503 verdi."),
    "kwh_sm3": (10.64, "A", "1 Sm³ doğal gaz ≈ 10,64 kWh üst ısıl değer"),
    "botas_kademe1": (10.625, "B", "BOTAŞ toptan, 4 Nisan 2026, KDV hariç"),
}
DOGALGAZ_TL_KWH = DOGALGAZ["tl_sm3"][0]/DOGALGAZ["kwh_sm3"][0]   # ≈ 1,264

VERIM = {
    "elektrikli_direnc": (1.00, "A", "Tanım gereği 1 kWh elektrik = 1 kWh ısı; "
                                     "%100 aşılamaz."),
    "gazli_radyant":     (0.90, "B", "Seramik radyant ışınım verimi kabulü"),
    "isi_pompasi_wshp":  (4.50, "A", "Su kaynaklı ısı pompası COP 4,5–5,5 "
                                     "(Ekotec); Ankara saha verisi SCOP 5,68"),
    "isi_pompasi_hava":  (3.00, "B", "Hava kaynaklı, +5 °C'de COP ~3,0"),
    "vrf":               (7.00, "A", "VRF SEER 7,0–8,0 kısmi yükte; "
                                     "Gree GMV6 SEER 7,70 / SCOP 5,74"),
}


def isi_maliyeti(elektrik_tl_kwh):
    """1 kWh ISI üretmenin TL maliyeti, kaynağa göre."""
    return [
     ("Elektrikli direnç (teras ısıtıcı, hava perdesi, boiler)",
      elektrik_tl_kwh/VERIM["elektrikli_direnc"][0], "elektrik", "A"),
     ("Hava kaynaklı ısı pompası (COP 3,0)",
      elektrik_tl_kwh/VERIM["isi_pompasi_hava"][0], "elektrik", "B"),
     ("Su kaynaklı ısı pompası — WSHP (COP 4,5)",
      elektrik_tl_kwh/VERIM["isi_pompasi_wshp"][0], "elektrik", "A"),
     ("Doğalgazlı radyant (verim %90)",
      DOGALGAZ_TL_KWH/VERIM["gazli_radyant"][0], "doğal gaz", "B"),
    ]


# ═══════════════════════ YATIRIM MALİYETLERİ ═════════════════════════════════
# (alt TL, üst TL, kaynak, güven)  ·  hepsi 2026 Türkiye piyasası
YATIRIM_BANT = {
 "T-01": (0, 0, "Tedarikçi ihalesi — yatırım gerektirmez", "A"),
 "T-02": (150_000, 280_000,
   "Detuned (harmonik reaktörlü) otomatik kompanzasyon, ~150 kVAr. "
   "Taban pano 250–450 TL/kVAr; reaktör ek maliyeti 410–790 TL/kVAr "
   "(Ekon 20 kVAr reaktör 8.230 TL'den türetildi). 200–400 kVAr sınıfı "
   "Türkiye'de proje bazlı fiyatlanır, liste fiyatı yayımlanmaz.", "C"),
 "T-03": (0, 0, "Tarife tipi değişikliği — dilekçe, ücretsiz", "A"),
 "T-04": (0, 0, "Sözleşme gücü düzeltmesi — güvence bedeli iadesi doğabilir", "B"),
 "M-01": (390_000, 1_364_000,
   "Talep kontrollü mutfak havalandırması (DCKV). ENERGY STAR'ın beş saha "
   "retrofit'i 8.000–28.000 USD; 48,70 TL/USD ile çevrildi. Türkiye TL "
   "fiyatı (Halton MARVEL / Melink Intelli-Hood) yayımlanmıyor — teklif "
   "alınmalıdır. Sürücü tarafı ayrıca ~2.400–5.600 TL/kW.", "B"),
 "M-02": (230_000, 420_000,
   "Karşı akışlı plakalı ısı geri kazanım, 5.000 m³/h sınıfı. "
   "Point P-IGK 5000 ürün sayfası 227.460 TL; Vantila Reco 5000 316.779 TL. "
   "Montaj ve kanal tadilatı hariç. YALNIZ SALON egzozuna uygulanır.", "B"),
 "M-03": (12_000, 35_000,
   "Kapı kontağı, kontaktör, termostat ve devreye alma. Cihaz değişimi "
   "yok — mevcut perdenin ısıtıcı kademesi devre dışı bırakılır.", "C"),
 "M-04": (55_000, 120_000,
   "Bölge anahtarı, dış hava termostatı, zaman saati ve devreye alma. "
   "Gazlı radyanta dönüşüm ayrı kalemdir (M-08).", "C"),
 "M-05": (120_000, 260_000,
   "EC fan dönüşümü, elektronik genleşme valfi, PVC şerit kapı perdesi, "
   "kondenser temizlik programı. Türkiye'de doğrulanmış TL fiyatı ve "
   "doğrulanmış tasarruf yüzdesi BULUNAMADI — teklif alınmalıdır.", "C"),
 "M-06": (160_000, 300_000,
   "Isı pompalı sıcak su üreteci (9,9 kW boiler yerine). Türkiye TL "
   "fiyatı doğrulanamadı; tahmindir.", "C"),
 "M-07": (15_000, 45_000,
   "Servis bedeli: ayar noktası ve program düzenlemesi, filtre ve "
   "kondenser temizliği. Cihaz değişimi yok.", "C"),
 "E-01": (80_000, 400_000,
   "DALİ senaryolarının kurulumu ~80.000 TL. Armatür değişimi gerekirse "
   "üst banda çıkar: COB LED ray spot 30 W ≈ 698 TL, lineer LED 40 W ≈ "
   "3.018 TL, DALİ sürücü ≈ 2.566 TL (hepsi KDV dâhil). UYARI: mevcut "
   "armatürler metal halide ise LED dönüşümünden beklenen tasarruf "
   "belirgin düşer — önce envanter çıkarılmalıdır.", "B"),
 "E-02": (8_000, 18_000, "Astronomik/zaman rölesi ve devreye alma.", "C"),
 "E-03": (0, 0, "İşletme disiplini — eğitim ve kontrol listesi.", "A"),
 "E-04": (60_000, 180_000,
   "Enerji analizörü panoda ZATEN KURULU (-EA1 + 6 akım trafosu); "
   "haberleşme uçlaması, kaydedici ve alt sayaçlar eklenir. "
   "Schneider iEM3365 alt sayaç ≈ 9.993 TL/nokta; profesyonel analizör "
   "15.000–50.000 TL. Referans vaka: orta ölçekli tesis 150.000 TL.", "B"),
 "E-05": (0, 20_000, "UPS mod değişikliği ve yük gözden geçirmesi.", "C"),
 "G-01": (3_150_000, 3_150_000,
   "100 kWp çatı GES, 31.500 TL/kWp (Azimut Solar EPC listesi, Nisan–Mayıs "
   "2026, KDV hariç). AVM çatısında kiracı için noter muvafakati ve ≥5 yıl "
   "kira şartı vardır; depolamasız fizibilite artık geçersizdir.", "B"),
}

# ═══════════════════════ DESTEK VE YÜKÜMLÜLÜK ════════════════════════════════
TEP_KWH = 11_630     # 1 TEP karşılığı elektrik · güven A
YUKUMLULUK = {
 "enerji_yoneticisi_ticari": (500, 20_000,
   "Ticari ve hizmet binaları: ≥ 500 TEP/yıl VEYA ≥ 20.000 m² toplam "
   "inşaat alanı. 5627 sayılı Enerji Verimliliği Kanunu."),
 "iso50001_ticari": (500, 20_000,
   "Enerji yöneticisi görevlendirmekle yükümlü ticari binalar TS EN ISO "
   "50001 kurmak ve TÜRKAK akrediteli kuruluşa belgelendirmek zorundadır."),
 "etut_periyot_bina": 7,
 "etut_periyot_sanayi": 4,
}
DESTEK = [
 ("VAP · Verimlilik Artırıcı Proje (ETKB)", "%30 hibe (KDV hariç)",
  "Azami hibe 8.127.799 TL · azami proje bedeli 27.092.663 TL · "
  "ASGARİ PROJE BEDELİ 5.000.000 TL (1 Temmuz 2026'dan itibaren) · "
  "asgari tasarruf: diğer sektörler anlık 50 kW · geri ödeme ≤ 7 yıl · "
  "ÖN ŞART: enerji yöneticisi + TÜRKAK akrediteli ISO 50001 · "
  "başvuru EVDEŞ üzerinden",
  "Tek şube için asgari proje bedeli gerçekçi DEĞİL. Zincirin birden çok "
  "şubesi tek projede birleştirilirse veya AVM ile ortak proje yapılırsa "
  "uygulanabilir."),
 ("KOSGEB · Yeşil Dönüşüm", "Enerji etüdü %75 (30.000 TL) · "
  "verimlilik giderleri %40 (900.000 TL)",
  "100–500 TEP aralığındaki işletmeler · geri ödemesiz",
  "Program sanayi odaklıdır; ticaret/hizmet sektörü kapsamı KOSGEB'den "
  "teyit edilmelidir."),
 ("KOSGEB · Yeşil Sanayi", "%40–50 · üst limit 4.000.000 TL",
  "Makine-teçhizat, yazılım, hizmet alımı; enerji/su verimliliği",
  "Kaynaklar arasında üst limit tutarsızlığı var (4 M vs 14 M TL) — "
  "KOSGEB'den teyit edilmelidir."),
 ("TÜBİTAK 1832 · Yeşil Endüstriyel Dönüşüm",
  "KOBİ %80 · büyük işletme %70 · azami 48.000.000 TL",
  "%50 geri ödemeli + %50 hibe · süre en fazla 24 ay", ""),
]

REAKTIF_CELISKI = (
 "İki kaynak çelişiyor: birine göre ceza YALNIZ AŞAN KISMA, diğerine göre "
 "oran aşıldığında ÖLÇÜLEN REAKTİFİN TAMAMINA uygulanır. Rapor her iki "
 "hesabı da veriyor. Ayrıca reaktif birim fiyatta da çelişki var: EPDK "
 "Temmuz–Aralık 2026 tablosu 3,4937 TL/kVArh, bir ikincil kaynak 2,6455 "
 "TL/kVArh (5 Nisan 2025 kararı — muhtemelen eski) diyor. Model EPDK "
 "tablosundaki 2026 değerini kullanır.")
REAKTIF_BEDEL_ESKI = 2.645474

YATIRIM = {k: (v[0]+v[1])/2 for k, v in YATIRIM_BANT.items() if v[1]}
