# -*- coding: utf-8 -*-
"""OFİS ÇİZİM STANDARDI — kod hâlinde tek kaynak.

Bu dosya docs/CIZIM_STANDARDI.md ile birebir aynı kuralları taşır; çizim
motorları ve denetim ajanı BURADAN okur, belge insan için aynı kuralları
anlatır. İkisi ayrışırsa denetim ajanı (a_standart) bunu hata olarak verir.

DAYANAKLAR (tools/kaynak.py kimlikleriyle)
  STD-01  Mimarlar Odası — Mimari Proje Çizim ve Sunuş Standartları (ana kaynak)
  STD-02  İTÜ ders notu (aynı standardın düzenlenmiş hâli)
  STD-03  İller Bankası mimari teknik şartnamesi
  CZM-01  MEGEP — Yapı Elemanları Ölçülendirme ve Tarama (gösterim)
  CZM-02  MEGEP — Alçı Levha ile Bölme Duvar (karkas gösterimi)
  ISO 5457 · ISO 7200 · ISO 128-2 · ISO 3098 (pafta, antet, çizgi, yazı)
"""

# ── 1 · PROJE AŞAMALARI VE ÖLÇEKLER (STD-01) ─────────────────────────────────
ASAMA = {
    "OP": ("Ön Proje",          (200, 100, 50)),
    "KP": ("Kesin Proje",       (100, 50)),
    "UP": ("Uygulama Projesi",  (100, 50)),
    "SD": ("Sistem Detayı",     (20, 10, 5)),
    "ID": ("İmalat Detayı",     (5, 2, 1)),
}
# Bu projede: uygulama planları 1/50 (A1), pilot büyütmeler 1/20 (A2 · SD),
# birleşim detayı 1/5 (A2 · ID)

# ── 2 · NUMARALANDIRMA (STD-01 §11–12) ───────────────────────────────────────
ELEMAN_ONEK = {"kapi": "K", "camli_kapi": "CK", "camekan": "CMK", "pencere": "P",
               "giris_kapisi": "GK", "gomme_dolap": "GD", "merdiven": "M"}
MAHAL_ONEK = {"bodrum": "B-", "zemin": "Z-", "kat": ""}      # Z-01, 101 …
MAHAL_BALON = "elips"            # mahal numarası elips içinde yazılır

# ── 3 · DOĞRAMA ETİKETİ (STD-01 kat planları maddesi; İTÜ §11) ──────────────
# "aksları gösteren çizgiler üzerinde en ve yükseklik (kaba yapı boşluğu
#  K7 90/220 gibi) gösterilir" · "çizgi üzerinde yükseklik, çizgi altında genişlik"
DOGRAMA_ETIKET = {"ust": "yukseklik_cm", "alt": "genislik_cm", "kod_solda": True}
DOGRAMA_BOSLUK = "kaba_yapi"     # etiketteki ölçü KABA YAPI boşluğudur, kanat değil

# ── 4 · ÖLÇÜLENDİRME (STD-01) ────────────────────────────────────────────────
DIS_OLCU_SIRASI = ("blok ölçüsü", "cephe hareketleri", "taşıyıcı akslar",
                   "doluluk ve boşluklar")            # dıştan cepheye doğru
IC_OLCU_SIRASI = ("net en ve boy", "kapı/pencere/kolon genişlikleri ve komşu "
                  "duvara uzaklıkları")                # her hacimde enine + boyuna
OLCU_SATIR_MM = 7.0              # kâğıtta ölçü çizgileri arası (ISO 129-1)
OLCU_YAZI_MM = 2.5

# ── 5 · KOTLAR (STD-01) ──────────────────────────────────────────────────────
KOT_REFERANS = "esas giriş önü tretuvar = ±0,00"
KOT_GOSTERIM = ("bitmis", "kaba")      # her ikisi AYRI AYRI yazılır
ASMA_TAVAN_KOT = "alt yüzü kotu yazılır"

# ── 6 · KESİT (STD-01) ───────────────────────────────────────────────────────
KESIT_ASGARI = 2
KESIT_OLCU_SIRASI = ("kaba kat yüksekliği — döşeme üstünden döşeme üstüne",
                     "kaplama kalınlığı · kapı/pencere/bölme yükseklikleri · "
                     "lento–tavan · taşıyıcı kalınlığı",
                     "asma tavan altı ile bitmiş döşeme arası NET yükseklik")
KESIT_MAHAL = "kod ve isim yazılır"

# ── 7 · ÇAPRAZ REFERANS (İTÜ §10) ────────────────────────────────────────────
# Plan/kesitte:  (Bak: SD-xx)   ·   Detay paftasında:  Bak pafta: UP-01 …
REFERANS_BICIM = {"planda": "(Bak: {detay})", "detayda": "Bak pafta: {paftalar}"}

# ── 8 · KALEM SERİSİ (ISO 128-2) — 1/100 mm ──────────────────────────────────
KALEM = {"kesilen": 70, "gorunus_sinir": 50, "gorunen": 35, "olcu": 25,
         "arkada": 18, "tarama": 13, "cerceve": 100}

# ── 9 · YAZI YÜKSEKLİĞİ (ISO 3098) — kâğıt mm ────────────────────────────────
YAZI = {"mikro": 1.8, "olcu": 2.5, "metin": 2.5, "etiket": 3.5,
        "altbaslik": 5.0, "baslik": 7.0}
YAZI_MIN = 1.8

# ── 10 · KATMAN ADLANDIRMA ───────────────────────────────────────────────────
# DİSİPLİN-NESNE[-NİTELİK]  ·  6–24 karakter  ·  A/M/E/G önekleri
KATMAN_ONEK = {"A": "mimari", "M": "mekanik", "E": "elektrik", "G": "genel"}
KATMAN_AD_MIN, KATMAN_AD_MAX = 6, 24

# ── 11 · ÖLÇEĞE GÖRE İFADE (MEGEP Tablo 2.1 / 2.7 / 2.8) ─────────────────────
IFADE = {
    100: "poché — duvar içi koyu, doğrama şematik, kapı yalnız açılım yayı",
    50:  "katman çizgileri; kasa/pervaz şematik; taşıyıcı içi koyu",
    20:  "gerçek katmanlar (levha · dikme · yalıtım · kaplama); kasa, pervaz, kanat kalınlığı",
    10:  "malzeme dokusu (tuğla sırası, derz); birleşim elemanları",
    5:   "imalat: vida, bant, profil et kalınlığı, silikon derzi",
}

# ── 12 · KAPI PLAN GÖSTERİMİ (MEGEP Şekil 2.51–2.55) ─────────────────────────
KAPI_PLAN = ("duvarda kapı genişliği kadar boşluk", "duvar kenarlarına kasa",
             "pervaz kasa–duvar birleşimini kapatır", "kanat boşluğu kapatır",
             "açılış yönü yayı")
KASA_KALINLIK_M = 0.045      # kasa profili (WPC/MDF) — plan kesitinde görünen
PERVAZ_GENISLIK_M = 0.060    # pervaz — duvar yüzünden dışa taşma
KANAT_KALINLIK_M = 0.040


def dograma_etiketi(kod, genislik_mm, yukseklik_mm):
    """K5  ·  üstte 200, altta 70 (cm) — çizgi üstü yükseklik, çizgi altı genişlik."""
    return kod, f"{round(yukseklik_mm/10):d}", f"{round(genislik_mm/10):d}"


def mahal_kodu(kat, sira):
    """Z-01, B-03, 101 …"""
    if kat == "zemin":  return f"Z-{sira:02d}"
    if kat == "bodrum": return f"B-{sira:02d}"
    return f"{kat}{sira:02d}"
