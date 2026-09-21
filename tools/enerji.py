# -*- coding: utf-8 -*-
"""AQUA FLORYA ELEKTRİK TÜKETİM VE TASARRUF MODELİ — tek veri kaynağı.

Bu dosya, elektrik faturası analizinin BÜTÜN sayısal girdilerini tutar.
Rapor, tablo ve grafiklerde elle yazılmış tek bir rakam yoktur; hepsi
buradan türer. Bir varsayım değişince bütün rapor kendiliğinden değişir.

BİRİNCİL VERİ (işverenin gönderdiği proje):
  input/referans/ADP_Yukleme_Cetveli_REF.xlsx
      "NUSRET SALTBAE AQUA FLORYA ADP ELEKTRİK PANO YÜKLEME CETVELİ R00"
      160 linye · toplam bağlı güç 373 650 W · talep gücü 333 230 W
      giriş şalteri 3×630 A TMŞ · cos φ 0,90 · kolon 8(1×95) mm² N2XH
  input/referans/ADP_REFERANS.pdf
      Proje no Y-24-003-001 · 34 sayfa · çizim 04.03.2025 · revizyon 10.03.2025
      IEC 61439-1&2 tip testli pano · TN-S · 36 kA · Form 4b

VARSAYIMLAR: her varsayım VARSAYIM sözlüğünde, gerekçesi ve doğrulama
yöntemiyle birlikte durur. Raporda "varsayım — yerinde doğrulanacak"
etiketiyle görünür.
"""
import csv, os, re, math
from pathlib import Path

KOK  = Path(__file__).resolve().parent.parent
HAM  = KOK/"work"/"enerji"/"adp_ham.csv"
XLSX = KOK/"input"/"referans"/"ADP_Yukleme_Cetveli_REF.xlsx"

REV        = "R00"
TARIH      = "21 Eylül 2026"
TESIS      = "Nusr-Et Saltbae · Aqua Florya"
PROJE_NO   = "Y-24-003-001"
PROJE_TAR  = "04.03.2025 (rev. 10.03.2025)"


# ═══════════════════════ 1 · PANO YÜKLEME CETVELİNİ OKU ══════════════════════
def _ham_satirlar():
    """Yükleme cetvelini oku. XLSX birincil; CSV önbellek."""
    if XLSX.exists():
        import openpyxl
        ws = openpyxl.load_workbook(XLSX, data_only=True).worksheets[0]
        return [[("" if c is None else str(c).replace("\n", " ").strip())
                 for c in r] for r in ws.iter_rows(values_only=True)]
    return list(csv.reader(open(HAM)))


S_KOD, S_L1, S_L3, S_TOP, S_ACIK = 3, 14, 16, 17, 18
S_ISIK, S_PRIZ, S_MOTOR = 9, 10, 11


def _sayi(v):
    v = str(v).replace(" ", "").replace(",", ".")
    try:    return float(v)
    except Exception: return None


# ═══════════════════════ 2 · İŞLEV SINIFLARI ═════════════════════════════════
# Tüketim, linyenin pano grubundan (P/K/M/L…) değil GERÇEK İŞLEVİNDEN türer:
# bir buzdolabı priz linyesinde de olsa 24 saat çalışır, bir fritöz mutfak
# linyesinde de olsa termostatik yüklenir.
SINIF_KURAL = [
    # (sınıf, açıklamada aranan kalıp)
    ("YEDEK",        r"\bYEDEK\b"),
    ("UPS_BT",       r"UPS"),
    ("PANO_SERVIS",  r"SİNYAL LAMBA|PANO AYDINLATMA|KOMPANZASYON"),
    ("TERAS_ISITMA", r"ELEKTRİKLİ ISITICI"),
    ("HAVA_PERDESI", r"HAVA PERDESİ"),
    ("AYDINLATMA",   r"DAVLUMBAZ AYDINLATMA"),
    ("HAVALANDIRMA", r"TAZE HAVA|MDP PANO"),
    ("HVAC",         r"WSHP|VRF|SPLİT KLİMA"),
    ("SOGUK_ODA",    r"SOĞUK ODA"),
    ("SOGUTMA",      r"BUZDOLABI|DONDURUCU|BUZ MAKİNASI"),
    ("SICAK_SU",     r"BOİLER|BOILER"),
    ("BODRUM",       r"BODRUM"),
    ("MUTFAK_PISIR", r"FRİTÖZ|İNDÜKSİYON|OCAK|SICAK TUTUCU|BAIN MAR|FIRIN|"
                     r"SICAK SERVİS ARABASI"),
    ("MUTFAK_YIKAMA",r"BULAŞIK YIKAMA|BARDAK YIKAMA"),
    ("BAR_KAHVE",    r"ESPRESSO|KAHVE|BLİNDER"),
    ("TABELA",       r"TABELA"),
    ("DOGRAMA",      r"GİYOTİN|KAYAR KAPI|TENTE"),
    ("AYDINLATMA",   r"AYDINLATMA|AYINLATMA|LED\s*BESLEME|EXIT|ACİL|"
                     r"KİT HATTI"),
    ("PRIZ",         r"PRİZ|SEBİL|FOTOSELLİ|SİNEK ÖLDÜRÜCÜ|SERVANT"),
]

SINIF_AD = {
    "AYDINLATMA":    "Aydınlatma (iç + dekoratif + acil)",
    "TABELA":        "Cephe tabelaları",
    "PRIZ":          "Genel priz ve küçük cihaz",
    "SOGUTMA":       "Ticari soğutma (dolap · dondurucu · buz)",
    "SOGUK_ODA":     "Soğuk oda (dış ünite + aydınlatma)",
    "MUTFAK_PISIR":  "Mutfak pişirme (fritöz · indüksiyon · fırın)",
    "MUTFAK_YIKAMA": "Bulaşık ve bardak yıkama",
    "BAR_KAHVE":     "Bar · espresso · kahve",
    "HVAC":          "İklimlendirme (VRF · WSHP · split)",
    "HAVALANDIRMA":  "Havalandırma (taze hava + davlumbaz egzoz)",
    "HAVA_PERDESI":  "Hava perdesi",
    "TERAS_ISITMA":  "Teras elektrikli ısıtıcı",
    "SICAK_SU":      "Elektrikli sıcak su (boiler)",
    "BODRUM":        "Bodrum depo alanı",
    "DOGRAMA":       "Motorlu doğrama (giyotin cam · kayar kapı · tente)",
    "UPS_BT":        "UPS besleme (kasa · sunucu · güvenlik)",
    "PANO_SERVIS":   "Pano servis yükleri",
    "YEDEK":         "Yedek linye (tüketim yok)",
}


def sinifla(aciklama):
    a = (aciklama or "").upper()
    for s, kalip in SINIF_KURAL:
        if re.search(kalip, a):
            return s
    return "PRIZ"


# ═══════════════════════ 3 · DEVRE LİSTESİ ═══════════════════════════════════
def _devreler():
    out, ham = [], _ham_satirlar()
    for r in ham:
        if len(r) <= S_ACIK:
            r = list(r) + [""]*(S_ACIK+1-len(r))
        kod = str(r[S_KOD]).strip()
        if kod.upper().startswith("TOPLAM"):
            break                      # TOPLAM satırından sonrası özet/not
        if "LİNYE" in kod.upper():
            continue
        if not kod:
            # Giriş şalteri altındaki kodsuz servis linyeleri (pano aydınlatma,
            # UPS beslemesi, şebeke sinyal lambaları) — cetvelde linye numarası
            # yoktur ama güçleri toplama girer.
            kod = "ANA"
        top = _sayi(r[S_TOP])
        if top is None:
            # tek fazlı linyelerde toplam boş kalmış olabilir → fazları topla
            faz = [_sayi(r[i]) for i in range(S_L1, S_L3+1)]
            faz = [f for f in faz if f]
            top = sum(faz) if faz else None
        if not top:
            continue
        acik = str(r[S_ACIK]).strip()
        if not acik:
            continue                   # açıklaması olmayan satır linye değildir
        faz  = 3 if sum(1 for i in range(S_L1, S_L3+1) if _sayi(r[i])) == 3 else 1
        out.append(dict(kod=kod, kw=top/1000.0, aciklama=acik,
                        sinif=sinifla(acik), faz=faz))
    return out


DEVRE = _devreler()

BAGLI_KW   = round(sum(d["kw"] for d in DEVRE), 2)
AKTIF_KW   = round(sum(d["kw"] for d in DEVRE if d["sinif"] != "YEDEK"), 2)
YEDEK_KW   = round(BAGLI_KW - AKTIF_KW, 2)

# Cetvelin kendi beyanı — modelin okuması bununla karşılaştırılır (regresyon)
CETVEL_BAGLI_KW  = 373.65
CETVEL_TALEP_KW  = 333.23
CETVEL_GIRIS_A   = 630
CETVEL_COSFI     = 0.90
CETVEL_TALEP_A   = 563.21
CETVEL_GRUP = {          # cetvel altındaki talep gücü dökümü (W) ve diversite
    "Priz":            (38840,  0.80),
    "Aydınlatma":      (9225,   0.90),
    "Mutfak ekipmanı": (88065,  0.90),
    "Mekanik cihaz":   (197100, 0.90),
}


def sinif_ozeti():
    d = {}
    for x in DEVRE:
        g = d.setdefault(x["sinif"], dict(kw=0.0, adet=0, devreler=[]))
        g["kw"] += x["kw"]; g["adet"] += 1; g["devreler"].append(x["kod"])
    for g in d.values():
        g["kw"] = round(g["kw"], 2)
    return dict(sorted(d.items(), key=lambda kv: -kv[1]["kw"]))


SINIF = sinif_ozeti()


# ═══════════════════════ 4 · VARSAYIMLAR ═════════════════════════════════════
# Her kayıt: (kod, konu, değer, gerekçe, nasıl doğrulanır)
VARSAYIM = [
 ("V-01", "İşletme takvimi", "365 gün/yıl · 30,4 gün/ay",
  "AVM içi restoran; yıl boyu kapanış yok.",
  "İşletmeden kapalı gün sayısı."),
 ("V-02", "Servis saati", "12:00–00:00 (12 saat)",
  "AVM restoran katı tipik servis penceresi.",
  "POS ilk/son fiş saatleri."),
 ("V-03", "Mutfak saati", "09:00–01:00 (16 saat)",
  "Hazırlık + servis + kapanış temizliği.",
  "Personel vardiya çizelgesi."),
 ("V-04", "Salon + teras alanı", "1 200 m² (kapalı 750 + teras 450)",
  "Cetvelde alan yok. Yük yoğunluğundan geri hesap: 373,65 kW / 1 200 m² "
  "= 311 W/m², tam donanımlı restoran için üst banttır.",
  "Mimari projeden net alan tablosu — RAPORUN EN KRİTİK EKSİK VERİSİ."),
 ("V-05", "Abone grubu ve tarife tipi",
  "AG · ticarethane · TARİFE TİPİ BİLİNMİYOR",
  "630 A giriş ve 333 kW talep gücüyle tesis alçak gerilim ticarethane "
  "abonesidir ve serbest tüketici sınırının çok üzerindedir. Tek zamanlı mı "
  "üç zamanlı mı olduğu BİLİNMİYOR; rapor her iki senaryoyu da hesaplar "
  "(§4.3). Ana senaryo tek zamanlıdır.",
  "Son faturanın üst bilgisi (abone grubu, tarife tipi, sayaç no). "
  "BU TEK SATIR yılda yüz binlerce TL'lik farkı belirler."),
 ("V-06", "Fatura aralığı", "350 000 – 450 000 TL/ay (işveren beyanı)",
  "İşverenin sözlü beyanı; fatura görülmedi.",
  "Son 12 ay faturası (PDF/e-arşiv)."),
 ("V-07", "Kompanzasyon", "Pano şemasında kompanzasyon beslemesi var, "
  "panonun kendisi pakette YOK",
  "ADP şeması -Q1 400 A üzerinden 'KOMPANZASYON BESLEME' ve 6 akım "
  "trafosundan 'KOMPANZASYON AKIM BİLGİSİ' çekiyor; kVAr kademe tablosu, "
  "reaktör/filtre bilgisi pakette yok.",
  "Kompanzasyon panosu projesi ve röle kayıtları."),
 ("V-08", "Hava perdesi", "21 kW elektrik ısıtmalı kabul edildi",
  "3×40 C kesici ve 5×6 N2XH kesit, 7 kW/faz — bu güç yoğunluğu ancak "
  "elektrikli ısıtıcılı hava perdesinde görülür; yalnız fanlı bir perde "
  "2–3 kW olurdu.",
  "Cihaz etiketi ve marka/model."),
 ("V-09", "Davlumbaz egzozu", "MDP panosu 21,9 kW · sabit debili",
  "M16 linyesi MDP'yi 3×50 C ile besliyor; ADP paketinde MDP'nin iç "
  "dağılımı ve sürücü (VFD) bilgisi yok. Zaman saati/kontaktör "
  "kullanılan diğer linyelerin aksine M16'da hız kontrolü görünmüyor.",
  "MDP pano yükleme cetveli ve davlumbaz otomasyon şeması."),
 ("V-10", "Mutfak pişirme", "Fritözler elektrikli (3×16,95 kW)",
  "MC5-MC7 'ELEKTRİKLİ FRİTÖZ', 3×40 C, 5×6 N2XH — cetvelde açık.",
  "Doğrulama gerekmez, cetvelde yazılı."),
 ("V-11", "Doğal gaz", "Yalnız kombi fırın doğalgazlı (MC10)",
  "Cetvelde tek doğalgazlı cihaz; mangal/ızgara kömür veya gaz olabilir, "
  "elektrik cetvelinde görünmez.",
  "Mekanik proje gaz akış şeması ve doğalgaz faturası."),
]
VARSAYIM_ETIKET = "varsayım — yerinde doğrulanacak"


# ═══════════════════════ 5 · İŞLETME PROFİLLERİ ══════════════════════════════
GUN_AY = 30.4167          # 365/12
AY_AD  = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran",
          "Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
AY_GUN = [31,28.25,31,30,31,30,31,31,30,31,30,31]

_D = [1.0]*12                                     # mevsimsiz
_SOGUK = [1.00,0.95,0.75,0.40,0.05,0.00,0.00,0.00,0.05,0.45,0.85,1.00]   # ısıtma
_SICAK = [0.35,0.30,0.32,0.40,0.65,0.90,1.00,1.00,0.88,0.58,0.38,0.35]   # soğutma
_SOG_TIC=[0.85,0.85,0.90,0.95,1.05,1.15,1.25,1.25,1.10,1.00,0.90,0.85]   # soğutma yükü
_TERAS = [0.30,0.30,0.50,0.80,1.00,1.00,1.00,1.00,1.00,0.85,0.45,0.30]   # teras kullanımı

# sinif: (saat/gün, yük faktörü, aylık katsayı, gerekçe)
PROFIL = {
 "AYDINLATMA":   (16.0, 0.92, _D,
   "Mutfak+salon aydınlatması hazırlıkla açılır, kapanış temizliğiyle kapanır. "
   "DALİ ve faz dim modülleri var ama linyeler sürekli enerjili."),
 "TABELA":       (11.0, 1.00, _D,
   "DTR-10 alacakaranlık rölesi + kontaktör; akşam–gece yanar."),
 "PRIZ":         (14.0, 0.28, _D,
   "Tezgâhüstü priz, kasa, su sebili, fotoselli batarya — düşük eşzamanlılık."),
 "SOGUTMA":      (24.0, 0.38, _SOG_TIC,
   "Buzdolabı/dondurucu 24 saat enerjili; kompresör çalışma oranı (duty) 0,38. "
   "Yaz aylarında mutfak sıcaklığıyla birlikte artar."),
 "SOGUK_ODA":    (24.0, 0.42, _SOG_TIC,
   "Soğuk oda dış üniteleri 24 saat; kapı açılma sıklığı ve yaz yükü etkili."),
 "MUTFAK_PISIR": (13.0, 0.33, _D,
   "Fritöz/indüksiyon/sıcak tutucu termostatiktir: bağlı gücün yaklaşık üçte "
   "biri kadar ortalama çeker. Boşta bekleme kaybı bu oranın içindedir."),
 "MUTFAK_YIKAMA":(11.0, 0.40, _D,
   "Bulaşık ve bardak makinesi çevrim başına ısıtır; servis yoğunluğuna bağlı."),
 "BAR_KAHVE":    (14.0, 0.25, _D,
   "Espresso ve kahve makineleri kazan sıcak tutar, çekiş anlıktır."),
 "HVAC":         (14.0, 0.55, _SICAK,
   "VRF + WSHP; yaz soğutma yükü baskın, kış WSHP ısıtma modunda kısmi çalışır. "
   "Aylık katsayı İstanbul derece-gün dağılımına göredir."),
 "HAVALANDIRMA": (15.0, 0.80, _D,
   "Taze hava şartlandırma + davlumbaz egzozu. Sabit debili kabul edildiği için "
   "yük faktörü yüksektir — bu varsayım tasarruf potansiyelinin merkezidir."),
 "HAVA_PERDESI": (13.0, 0.60, _SOGUK,
   "Kapı açıkken çalışır; elektrikli ısıtıcı kademesi kışın devrededir."),
 "TERAS_ISITMA": ( 6.0, 0.65, _SOGUK,
   "8 × 5 kW infrared ısıtıcı; akşam servisinde ve soğuk aylarda."),
 "SICAK_SU":     (24.0, 0.20, [1.05,1.05,1.00,0.95,0.90,0.85,0.80,0.80,0.90,1.00,1.05,1.05],
   "Depolu elektrikli boyler; kayıp + çekiş. Şebeke suyu sıcaklığı kışın düşük."),
 "BODRUM":       (16.0, 0.30, _D,
   "Bodrum depo alanı genel beslemesi (aydınlatma + priz + küçük cihaz)."),
 "DOGRAMA":      ( 1.5, 0.30, _TERAS,
   "Giyotin cam, kayar kapı, bioklimatik tente — yalnız hareket anında çeker."),
 "UPS_BT":       (24.0, 0.30, _D,
   "10 kVA UPS: kasa, sunucu, ağ, kamera + akü şarj ve çeviri kaybı."),
 "PANO_SERVIS":  (24.0, 0.50, _D, "Pano aydınlatma ve sinyal."),
 "YEDEK":        ( 0.0, 0.00, _D, "Yedek linye — tüketim yok."),
}


def aylik_kwh(sinif):
    """Bir sınıfın 12 aylık kWh dizisi."""
    kw = SINIF.get(sinif, {}).get("kw", 0.0)
    saat, lf, ay, _ = PROFIL[sinif]
    return [kw*saat*lf*k*g for k, g in zip(ay, AY_GUN)]


TUKETIM = {s: aylik_kwh(s) for s in SINIF}
YILLIK  = {s: round(sum(v)) for s, v in TUKETIM.items()}
YILLIK_TOPLAM = sum(YILLIK.values())
AYLIK_TOPLAM  = [round(sum(TUKETIM[s][i] for s in TUKETIM)) for i in range(12)]
ORT_AY_KWH    = round(YILLIK_TOPLAM/12)

# Talep (kW) — fatura güç bedeli ve trafo/abonelik için
ORT_GUC_KW    = round(YILLIK_TOPLAM/8760, 1)


# ═══════════════════════ 6 · TARİFE MODELİ ═══════════════════════════════════
# Türkiye AG ticarethane faturası bileşenleri. Bütün birim fiyatlar TL/kWh,
# KDV hariçtir. Değerler tools/enerji_tarife.py tarafından araştırma
# çıktısından doldurulur; burada modelin ŞEKLİ tanımlıdır.
TARIFE = {
    "ad":            "AG · Ticarethane · tek terimli (varsayılan senaryo)",
    "aktif":         None,   # TL/kWh — enerji bedeli
    "dagitim":       None,   # TL/kWh — dağıtım bedeli
    "enerji_fonu":   0.00,   # aktif bedelin oranı
    "trt_payi":      0.00,   # aktif bedelin oranı
    "btv":           0.05,   # elektrik tüketim vergisi — ticarethane %5
    "kdv":           0.20,   # katma değer vergisi
    "kaynak":        None,
}

# Üç zamanlı tarifede tüketimin zaman dilimlerine dağılımı.
# T1 gündüz 06–17 · T2 puant 17–22 · T3 gece 22–06
# Restoran servis penceresi akşam ağırlıklı olduğu için puant payı yüksektir.
ZAMAN_PAY = {"T1": 0.38, "T2": 0.34, "T3": 0.28}
ZAMAN_SAAT = {"T1": "06:00–17:00", "T2": "17:00–22:00", "T3": "22:00–06:00"}

REAKTIF = {
    "enduktif_esik": 0.20,   # aktifin %20'si — aşılırsa ceza
    "kapasitif_esik": 0.15,
    "not": "Elektrik Piyasası Tüketici Hizmetleri Yönetmeliği eşikleri.",
}


def fatura(kwh, tarife=None, reaktif_ceza=0.0, guc_asim=0.0):
    """Bir aylık faturanın bileşen dökümü (TL)."""
    t = dict(TARIFE); t.update(tarife or {})
    if t["aktif"] is None or t["dagitim"] is None:
        return None
    aktif   = kwh*t["aktif"]
    dagitim = kwh*t["dagitim"]
    fon     = aktif*t["enerji_fonu"]
    trt     = aktif*t["trt_payi"]
    btv     = aktif*t["btv"]
    ara     = aktif+dagitim+fon+trt+btv+reaktif_ceza+guc_asim
    kdv     = ara*t["kdv"]
    return {"Aktif enerji": aktif, "Dağıtım bedeli": dagitim,
            "Enerji fonu": fon, "TRT payı": trt,
            "Elektrik tüketim vergisi": btv,
            "Reaktif ceza": reaktif_ceza, "Güç aşım bedeli": guc_asim,
            "KDV": kdv, "TOPLAM": ara+kdv, "_kwh": kwh,
            "_birim": (ara+kdv)/kwh if kwh else 0.0}


# İşverenin beyan ettiği fatura aralığı (V-06)
BEYAN_TL = (350_000, 450_000)
BEYAN_ZINCIR_TL = (300_000, 650_000)   # bütün şubeler için beyan


def ima_edilen_birim(tl):
    """Beyan edilen fatura ÷ modelin tükettiği kWh → ima edilen TL/kWh."""
    return tl/ORT_AY_KWH


def ima_edilen_kwh(tl, birim):
    return tl/birim if birim else None


# ═══════════════════════ 7 · ÖNLEM KATALOĞU ══════════════════════════════════
# Her önlem: hangi tüketim sınıfına, ne oranda etki ettiğini söyler.
# Tasarruf kWh'i MODELDEN hesaplanır; elle yazılmaz.
#   kod · ad · etkilenen sınıflar {sinif: tasarruf oranı} · yatırım TL
#   · ömür yıl · güven (YÜKSEK/ORTA/DÜŞÜK) · kategori · gerekçe · kaynak
ONLEM = [
 dict(kod="T-01", ad="Serbest tüketici ikili anlaşması / tedarikçi ihalesi",
      kategori="TARİFE", etki={}, enerji_indirim=None, yatirim=0, omur=1,
      guven="YÜKSEK",
      gerekce="333 kW talep gücüyle tesis serbest tüketici sınırının çok "
              "üzerindedir. Son kaynak tedarik tarifesinden (SKTT) ikili "
              "anlaşmaya geçiş, aktif enerji bileşeninde indirim sağlar. "
              "Zincirin bütün şubeleri tek portföyde ihale edilirse "
              "pazarlık gücü artar.",
      kaynak="EPDK · serbest tüketici mevzuatı"),
 dict(kod="T-02", ad="Reaktif ceza sıfırlama (kompanzasyon bakımı/yenileme)",
      kategori="TARİFE", etki={}, yatirim=None, omur=10, guven="ORTA",
      gerekce="Pano şemasında kompanzasyon beslemesi ve 6 akım trafosu var; "
              "panonun projesi pakette yok. VRF/WSHP sürücüleri ve LED "
              "sürücüleri harmonik üretir, klasik kondansatör grubu bu yükte "
              "hızla bozulur. Ceza varsa faturanın görünmeyen kalemidir.",
      kaynak="ADP şeması s.5 · V-07"),
 dict(kod="T-03", ad="Tarife tipi kontrolü: üç zamanlıdan tek zamanlıya geçiş",
      kategori="TARİFE", etki={}, yatirim=0, omur=10, guven="ORTA",
      gerekce="Restoranın servis yükü 17:00–22:00 puant dilimine yığılır ve o "
              "dilimin birim fiyatı gündüzün 1,42 katıdır. Bu yük profilinde "
              "üç zamanlı tarife tek zamanlıdan PAHALIDIR. Tesis üç "
              "zamanlıdaysa dilekçeyle tek zamanlıya geçmek sıfır maliyetli "
              "en büyük tek kazançtır; tek zamanlıdaysa üç zamanlıya "
              "GEÇİLMEMELİDİR. Puant dilimine kaydırılabilen yükler "
              "(bulaşık, boyler ısıtma, buz üretimi, soğuk oda defrost) "
              "yine de gece dilimine alınmalıdır.",
      kaynak="§4.3 · üç zamanlı ticarethane birim fiyatları"),
 dict(kod="T-04", ad="Güç (talep) aşım kontrolü ve sözleşme gücü düzeltmesi",
      kategori="TARİFE", etki={}, yatirim=None, omur=10, guven="ORTA",
      gerekce="Cetvel talep gücünü 333 kW veriyor; modelin ortalama gücü "
              "bunun çok altında. Sözleşme gücü gereğinden yüksekse güç "
              "bedeli boşa ödenir, düşükse aşım cezası doğar.",
      kaynak="Cetvel · CETVEL_TALEP_KW"),

 dict(kod="M-01", ad="Davlumbaz değişken debili havalandırma (DCKV) + VFD",
      kategori="MEKANİK", etki={"HAVALANDIRMA": 0.40}, yatirim=None,
      omur=12, guven="ORTA",
      gerekce="Egzoz ve taze hava sabit debili çalışıyor (V-09). Sıcaklık ve "
              "optik duman sensörüyle debiyi pişirme yüküne bağlamak, fan "
              "gücünü küp yasasıyla düşürür: %70 debi = %34 güç. Ayrıca "
              "atılan şartlandırılmış havayı azaltarak iklimlendirme yükünü "
              "de düşürür (M-02 ile birlikte sayılmaz, çifte sayım yok).",
      kaynak="ASHRAE 90.1 mutfak havalandırma hükümleri"),
 dict(kod="M-02", ad="Taze hava ünitesine ısı geri kazanım eklenmesi",
      kategori="MEKANİK", etki={"HVAC": 0.12}, yatirim=None, omur=15,
      guven="ORTA",
      gerekce="Taze hava şartlandırma ünitesi var (M15/M17, 10,5 kW fan) "
              "ancak pakette ısı geri kazanım (rotor/plakalı) görünmüyor. "
              "Atık havadan duyulur ısı geri kazanımı taze hava "
              "şartlandırma yükünü belirgin azaltır. Mutfak egzozu yağlı "
              "olduğu için ısı geri kazanım yalnız SALON egzozuna uygulanır.",
      kaynak="V-09 · MMO havalandırma semineri"),
 dict(kod="M-03", ad="Hava perdesi elektrikli ısıtma kademesinin kapatılması "
                     "ve kapı ile kilitlenmesi",
      kategori="MEKANİK", etki={"HAVA_PERDESI": 0.55}, yatirim=None, omur=10,
      guven="ORTA",
      gerekce="21 kW'lık hava perdesi (V-08) elektrikli ısıtıcılıdır. "
              "Elektrikli direnç ısıtması 1 kWh elektrik = 1 kWh ısıdır; "
              "aynı ısıyı ısı pompası 3–4 kat verimle üretir. Perdenin "
              "ısıtıcısını devre dışı bırakıp yalnız fanla çalıştırmak, "
              "kapı kontağıyla kilitlemek ve kapı açık kalmasını önlemek.",
      kaynak="Cetvel M7 · V-08"),
 dict(kod="M-04", ad="Teras ısıtmasında bölgesel kontrol, termostat ve "
                     "zaman saati; gazlı radyant alternatifi",
      kategori="MEKANİK", etki={"TERAS_ISITMA": 0.45}, yatirim=None, omur=10,
      guven="ORTA",
      gerekce="8 × 5 kW = 40 kW elektrikli ısıtıcı, tesisin en pahalı ısı "
              "kaynağıdır. Masa bazlı bölgeleme, dış hava termostatı, "
              "hareket sensörü ve kapanış saati otomasyonu ile boşa yanma "
              "kesilir. Gazlı radyant ısıtıcı aynı ısıyı doğal gazın "
              "kWh fiyatından üretir.",
      kaynak="Cetvel M36-M43"),
 dict(kod="M-05", ad="Soğutma: EC fan · kondenser bakımı · kapı perdesi · "
                     "elektronik genleşme valfi",
      kategori="MEKANİK", etki={"SOGUTMA": 0.22, "SOGUK_ODA": 0.25},
      yatirim=None, omur=10, guven="ORTA",
      gerekce="Ticari soğutma 24 saat çalışır; küçük bir verim artışı bütün "
              "yıla yayılır. Kirli kondenser kompresör gücünü %10–30 artırır. "
              "Soğuk oda kapı perdesi ve otomatik kapı kapatıcı, kapı açık "
              "kalma kaybını keser.",
      kaynak="Cetvel P3-P5 · M20 · P48 · K6-K8"),
 dict(kod="M-06", ad="Elektrikli boylerin ısı pompalı su ısıtıcıya "
                     "veya gaza çevrilmesi",
      kategori="MEKANİK", etki={"SICAK_SU": 0.55}, yatirim=None, omur=12,
      guven="ORTA",
      gerekce="9,9 kW elektrikli boiler (M22) direnç ısıtmasıdır. Isı pompalı "
              "su ısıtıcı aynı sıcak suyu 3 kat verimle üretir; mutfak "
              "atık ısısından beslenirse verim daha da artar.",
      kaynak="Cetvel M22"),
 dict(kod="M-07", ad="VRF/WSHP işletme ayarı: ölü bant · gece geri çekme · "
                     "filtre ve kondenser bakımı",
      kategori="MEKANİK", etki={"HVAC": 0.10}, yatirim=None, omur=8,
      guven="ORTA",
      gerekce="Cihaz değişimi değil, işletme ayarı. Isıtma ve soğutma "
              "ayar noktaları arasında ölü bant bırakmak, boş saatlerde "
              "geri çekme, kirli filtre/kondenserin giderilmesi. "
              "Yatırımı en düşük, geri dönüşü en hızlı kalemdir.",
      kaynak="Cetvel M1-M5 · M8-M9 · M13-M14 · M18-M19"),

 dict(kod="E-01", ad="Aydınlatmada LED dönüşümü ve DALİ senaryolarının "
                     "gerçekten kullanılması",
      kategori="ELEKTRİK", etki={"AYDINLATMA": 0.30}, yatirim=None, omur=10,
      guven="ORTA",
      gerekce="Projede DALİ modülleri ve 4 kanal faz dim modülü var (DS1-DS7, "
              "FD1-FD4) — altyapı kurulu. Sorun genelde senaryoların "
              "kurulmaması ve her şeyin tam güçte yanmasıdır. Armatürler "
              "zaten LED ise kazanç senaryo ve takvimden gelir.",
      kaynak="Cetvel DS · FD · S · L linyeleri"),
 dict(kod="E-02", ad="Tabela ve cephe aydınlatmasında takvim/astronomik röle",
      kategori="ELEKTRİK", etki={"TABELA": 0.25}, yatirim=None, omur=10,
      guven="YÜKSEK",
      gerekce="DTR-10 alacakaranlık rölesi zaten var; kapanış sonrası "
              "söndürme saati eklenirse gece boyu yanma kesilir.",
      kaynak="Cetvel M30-M32"),
 dict(kod="E-03", ad="Mutfak ekipmanında açma/kapama disiplini ve "
                     "kademeli devreye alma",
      kategori="İŞLETME", etki={"MUTFAK_PISIR": 0.12,
                                "MUTFAK_YIKAMA": 0.10, "BAR_KAHVE": 0.15},
      yatirim=None, omur=5, guven="ORTA",
      gerekce="Fritöz ve sıcak tutucuların servis başlamadan saatler önce "
              "açılması, boşta bekleme kaybının ana kaynağıdır. Cihaz başına "
              "açılış saati, kapanışta kapatma kontrol listesi ve "
              "kontaktörlü zaman saati (projede M linyelerinde zaten var) "
              "ile sağlanır. Yatırımsız, davranışsal kalem.",
      kaynak="Cetvel MC · K linyeleri"),
 dict(kod="E-04", ad="Enerji izleme sistemi: alt sayaçlar + bulut raporlama",
      kategori="ELEKTRİK", etki={}, yatirim=None, omur=10, guven="YÜKSEK",
      gerekce="ADP'de enerji analizörü (-EA1, RS485) ve 6 akım trafosu ZATEN "
              "VAR. Sadece haberleşmenin uçlanması ve bir kaydediciye "
              "bağlanması gerekiyor. Ölçülmeyen tüketim yönetilemez: bu "
              "kalem kendi başına tasarruf üretmez ama diğer bütün "
              "kalemlerin doğrulanmasını sağlar. ÖNCE BU YAPILMALIDIR.",
      kaynak="ADP şeması s.5 · -EA1 enerji analizörü"),
 dict(kod="E-05", ad="UPS'in eko moda alınması ve yük gözden geçirmesi",
      kategori="ELEKTRİK", etki={"UPS_BT": 0.30}, yatirim=0, omur=8,
      guven="DÜŞÜK",
      gerekce="10 kVA UPS 24 saat çift dönüşümde çalışıyorsa çeviri kaybı "
              "sürekli gider yazar. Yalnız kritik yükler (kasa, sunucu, "
              "güvenlik) UPS'te kalmalı; eko/hat etkileşimli mod kaybı azaltır.",
      kaynak="Cetvel · 10 KVA UPS BESLEME"),
 dict(kod="G-01", ad="Çatı / teras fotovoltaik (öz tüketim)",
      kategori="ÜRETİM", etki={}, yatirim=None, omur=25, guven="DÜŞÜK",
      gerekce="Tesis AVM içindedir; çatı mülkiyeti ve kullanım hakkı "
              "kiracıda değildir. Uygulanabilirliği AVM yönetimiyle "
              "yapılacak anlaşmaya bağlıdır. Teknik olarak öğle saatlerinde "
              "soğutma yüküyle örtüşür, öz tüketim oranı yüksektir.",
      kaynak="Lisanssız üretim mevzuatı · V-04"),
]


def onlem_tasarruf(o):
    """Bir önlemin yıllık kWh tasarrufu — tüketim modelinden hesaplanır."""
    return round(sum(YILLIK.get(s, 0)*p for s, p in o.get("etki", {}).items()))


def teknik_toplam():
    """Etkisi modellenebilen önlemlerin toplam kWh tasarrufu.
    Aynı sınıfa birden fazla önlem varsa çarpımsal birleştirilir —
    yüzdeler toplanmaz, çifte sayım olmaz."""
    kalan = {s: 1.0 for s in YILLIK}
    for o in ONLEM:
        for s, p in o.get("etki", {}).items():
            kalan[s] *= (1.0 - p)
    return round(sum(YILLIK[s]*(1.0-kalan[s]) for s in YILLIK))


# ═══════════════════════ 8 · REAKTİF ENERJİ ANALİZİ ══════════════════════════
def reaktif_analiz(cosfi, kwh=None, birim=None):
    """Verilen güç katsayısında reaktif ceza riski.

    Eşik aşıldığında ölçülen reaktif enerjinin TAMAMI bedellendirilir
    (muhafazakâr kabul). Oran = kVArh / kWh = tan φ.
    """
    kwh = kwh if kwh is not None else ORT_AY_KWH
    tanfi = math.tan(math.acos(cosfi))
    kvarh = kwh*tanfi
    esik  = REAKTIF["enduktif_esik"]
    asim  = tanfi > esik
    ceza  = kvarh*birim if (asim and birim) else 0.0
    return {"cosfi": cosfi, "tanfi": tanfi, "kvarh": kvarh,
            "esik": esik, "asim": asim, "ceza": ceza,
            "gereken_cosfi": round(math.cos(math.atan(esik)), 4)}


def kompanzasyon_kvar(p_kw, cosfi_mevcut, cosfi_hedef):
    """cos φ'yi mevcuttan hedefe çıkarmak için gereken reaktif güç (kVAr)."""
    return p_kw*(math.tan(math.acos(cosfi_mevcut)) -
                 math.tan(math.acos(cosfi_hedef)))


# İşletme saatlerindeki ortalama güç (kW) — kompanzasyon boyutlandırması için
ISLETME_SAAT_GUN = 16.0
ISLETME_ORT_KW = round(YILLIK_TOPLAM/(365*ISLETME_SAAT_GUN), 1)


# ═══════════════════════ 9 · TARİFE ÖNLEMLERİNİN TL ETKİSİ ═══════════════════
def tarife_etkileri(T):
    """Fiyat tarafındaki önlemlerin yıllık TL etkisi. T = enerji_tarife modülü.
    Her kalem: (kod, TL/yıl, açıklama, güven)"""
    mev = T.SENARYO["MEVCUT"]["birim"]
    yil = YILLIK_TOPLAM
    out = {}

    # T-01 · tedarikçi indirimi (aktif enerjide %10 ve %15 senaryosu)
    d10 = (mev - T.SENARYO["INDIRIMLI"]["birim"])*yil
    d15 = (mev - T.SENARYO["INDIRIMLI_15"]["birim"])*yil
    out["T-01"] = (d10, d15,
        "Aktif enerjide %10–15 indirim. İndirim YALNIZCA aktif enerji "
        "bileşenine uygulanır; dağıtım bedeli, BTV, fon ve KDV kapsam "
        "dışıdır. Bu yüzden aktif enerjideki %10 indirim toplam faturada "
        f"%{100*d10/(mev*yil):.1f} tasarruf demektir.", "B")

    # T-02 · reaktif ceza — tasarım cos φ'si ile ceza senaryosu
    r = reaktif_analiz(CETVEL_COSFI, birim=T.REAKTIF_BEDEL)
    ceza_yil = r["ceza"]*12*(1+T.VERGI["kdv"][0])
    out["T-02"] = (0.0, ceza_yil,
        f"Cetvel cos φ'yi {CETVEL_COSFI} veriyor. Bu değerde reaktif oranı "
        f"%{100*r['tanfi']:.1f} olur ve %{100*r['esik']:.0f} eşiğini aşar. "
        f"Eşik aşıldığında ölçülen reaktif enerjinin TAMAMI bedellendirilir: "
        f"ayda {r['kvarh']:,.0f} kVArh × {T.REAKTIF_BEDEL:.3f} TL/kVArh = "
        f"{r['ceza']*1.2:,.0f} TL (KDV dâhil). Kompanzasyon çalışıyorsa bu "
        f"ceza SIFIRDIR; çalışmıyorsa faturanın "
        f"%{100*r['ceza']*1.2/(ORT_AY_KWH*mev):.0f}'ini oluşturur. "
        f"Eşiğin altında kalmak için cos φ ≥ {r['gereken_cosfi']} gerekir."
        .replace(",", "."), "A")

    # T-03 · tarife tipi (üç zamanlı ↔ tek zamanlı)
    uz = T.uc_zamanli_birim(ZAMAN_PAY)
    fark = (uz - mev)*yil
    out["T-03"] = (max(0.0, fark), max(0.0, fark),
        f"Restoranın servis yükü 17:00–22:00 puant dilimine denk gelir ve o "
        f"dilim gündüzün {T.UC_ZAMANLI['T2'][0]/T.UC_ZAMANLI['T1'][0]:.2f} "
        f"katıdır. Modelin zaman dağılımıyla (T1 %{100*ZAMAN_PAY['T1']:.0f} · "
        f"T2 %{100*ZAMAN_PAY['T2']:.0f} · T3 %{100*ZAMAN_PAY['T3']:.0f}) üç "
        f"zamanlı birim fiyat {uz:.2f} TL/kWh, tek zamanlı {mev:.2f} TL/kWh "
        f"çıkar — üç zamanlı %{100*(uz/mev-1):.0f} DAHA PAHALIDIR. Tesis üç "
        f"zamanlı tarifedeyse tek zamanlıya geçiş yılda "
        f"{fark:,.0f} TL kazandırır; tek zamanlıdaysa ÜÇ ZAMANLIYA GEÇİLMEMELİDİR."
        .replace(",", "."), "B")

    # T-04 · güç / abonelik
    out["T-04"] = (None, None,
        f"Cetvel talep gücünü {CETVEL_TALEP_KW:.0f} kW veriyor; modelin "
        f"işletme saatlerindeki ortalama gücü {ISLETME_ORT_KW:.0f} kW, yıllık "
        f"ortalaması {ORT_GUC_KW:.0f} kW. Yük faktörü çok düşüktür. Çift "
        f"terimli tarifedeyse güç bedeli kullanılmayan kapasiteye ödenir; "
        f"tek terimli tarifedeyse güç bedeli yoktur ve bu kalem geçersizdir. "
        f"Güvence bedeli 2026'da 746 TL/kW'dır — sözleşme gücü gereğinden "
        f"yüksekse bağlanan sermaye de büyür. TL etkisi fatura görülmeden "
        f"hesaplanamaz.", "B")
    return out


# ═══════════════════════ 10 · KIYASLAMA ══════════════════════════════════════
ALAN_M2      = 1200.0       # V-04 · varsayım — yerinde doğrulanacak
ALAN_KAPALI  = 750.0
ALAN_TERAS   = 450.0
ALAN_BANT    = (900.0, 1500.0)   # duyarlılık için makul aralık

def ozgul(alan=None):
    return YILLIK_TOPLAM/(alan or ALAN_M2)

def guc_yogunlugu(alan=None):
    return BAGLI_KW*1000.0/(alan or ALAN_M2)

# Elektrik dışı yakıt: cetvelde yalnız MC10 doğalgazlı kombi fırın var.
# Tesis pratikte TAMAMEN ELEKTRİKLİDİR — pişirme, ısıtma, teras ısıtması,
# sıcak su, hepsi elektrik. Kıyas tabloları ise fosil yakıtlı mutfak ve
# ısıtma varsayar. Bu fark raporun yapısal bulgusudur.
ELEKTRIK_PAYI = 1.00
ELEKTRIK_PAYI_NOT = (
    "Yük cetvelindeki 155 linyeden yalnız biri (MC10) doğalgazlı bir cihazı "
    "besler ve o da yalnız kumanda gücüdür. Mangal/ızgara kömür veya gaz "
    "olabilir; elektrik cetvelinde görünmez ve doğrulanmalıdır.")


# ═══════════════════════ 11 · YAKIT DÖNÜŞÜMÜ ÖNLEMLERİ ═══════════════════════
# Bu kalemler kWh'i azaltmaz; kWh'i DAHA UCUZ BİR YAKITTAN üretir.
# Tasarruf doğrudan TL cinsindendir ve kWh tasarrufuyla çakışmaz.
YAKIT_ONLEM = [
 dict(kod="Y-01", ad="Teras ısıtmasının gazlı radyanta çevrilmesi",
      sinif="TERAS_ISITMA", onceki="M-04", verim_kaynak="gazli_radyant",
      guven="ORTA",
      gerekce="8 × 5 kW elektrikli direnç ısıtıcı, bir kWh ısıyı üretmenin "
              "en pahalı yoludur. Gazlı seramik radyant ısıtıcı aynı ışınım "
              "ısısını doğal gazın kWh fiyatından üretir. Açık terasta ısı "
              "pompası KULLANILAMAZ — ısı pompası havayı ısıtır, açık alanda "
              "ısıtılan hava kaçar; açık teras zorunlu olarak IŞINIM "
              "(radyant) ısıtması gerektirir. ÖN ŞART: AVM'nin terasa doğal "
              "gaz hattı iznini vermesi. Çoğu AVM yangın yönetmeliği "
              "gerekçesiyle izin vermez — bu ilk sorulacak sorudur."),
 dict(kod="Y-02", ad="Hava perdesi ısıtmasının kaynağının değiştirilmesi",
      sinif="HAVA_PERDESI", onceki="M-03", verim_kaynak="isi_pompasi_wshp",
      pay=0.70, guven="DÜŞÜK",
      gerekce="Hava perdesinin elektrikli ısıtıcı kademesi yerine tesiste "
              "zaten bulunan WSHP devresinden sulu ısıtıcılı bir perde "
              "beslenebilirse, aynı ısı yaklaşık dörtte bir elektrikle "
              "üretilir. Cihaz değişimi ve tesisat gerektirir; M-03 "
              "(ısıtıcıyı tamamen kapatma) çok daha ucuz olduğu için önce "
              "o denenmelidir."),
 dict(kod="Y-03", ad="Elektrikli boylerin ısı pompalı üretece çevrilmesi",
      sinif="SICAK_SU", onceki=None, verim_kaynak="isi_pompasi_hava",
      guven="ORTA",
      gerekce="9,9 kW'lık depolu elektrikli boiler direnç ısıtmasıdır. "
              "Isı pompalı su ısıtıcı aynı sıcak suyu üçte bir elektrikle "
              "üretir; mutfak atık ısısından beslenirse verim daha da artar. "
              "M-06 ile aynı fiziksel işi tarif eder; burada TL etkisi "
              "yakıt/verim tarafından hesaplanır."),
]


def yakit_tasarruf(y, T):
    """Bir yakıt dönüşümü önleminin yıllık TL tasarrufu."""
    kwh = YILLIK.get(y["sinif"], 0)*y.get("pay", 1.0)
    # önceki bir kontrol önlemi varsa onun kalanı üzerinden çalışır
    if y.get("onceki"):
        o = next((x for x in ONLEM if x["kod"] == y["onceki"]), None)
        if o:
            kwh *= (1.0 - o["etki"].get(y["sinif"], 0.0))
    elektrik = T.SENARYO["MEVCUT"]["birim"]
    verim, _, _ = T.VERIM[y["verim_kaynak"]]
    if y["verim_kaynak"] == "gazli_radyant":
        yeni = T.DOGALGAZ_TL_KWH/verim
    else:
        yeni = elektrik/verim
    return {"kwh": kwh, "mevcut_tl": kwh*elektrik, "yeni_tl": kwh*yeni,
            "tasarruf": kwh*(elektrik-yeni), "yeni_birim": yeni}


# ═══════════════════════ 12 · TOPLAM POTANSİYEL ══════════════════════════════
def potansiyel(T):
    """Üç koldan gelen yıllık TL potansiyeli. Kollar birbirinden bağımsızdır:
    tüketim azaltma kWh'i düşürür, tarife kWh'i ucuzlatır, yakıt dönüşümü
    ısıyı başka kaynaktan üretir. Üçü toplanabilir; kendi içlerinde
    çakışmalar zaten giderilmiştir."""
    birim = T.SENARYO["MEVCUT"]["birim"]
    yil_tl = YILLIK_TOPLAM*birim
    te = tarife_etkileri(T)

    tuketim_tl = teknik_toplam()*birim
    yakit_tl   = sum(yakit_tasarruf(y, T)["tasarruf"] for y in YAKIT_ONLEM)
    tarife_alt = te["T-01"][0]
    tarife_ust = te["T-01"][1] + te["T-02"][1] + te["T-03"][1]

    return {
      "yillik_fatura": yil_tl,
      "tuketim": (tuketim_tl, tuketim_tl),
      "yakit":   (0.0, yakit_tl),
      "tarife":  (tarife_alt, tarife_ust),
      "toplam":  (tuketim_tl + tarife_alt,
                  tuketim_tl + yakit_tl + tarife_ust),
    }


def onlem_yatirim(kod, T):
    b = getattr(T, "YATIRIM_BANT", {}).get(kod)
    return b if b else None
