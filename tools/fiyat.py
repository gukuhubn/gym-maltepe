# -*- coding: utf-8 -*-
"""BİRİM FİYAT TABLOSU — malzeme / işçilik ayrık, min-maks aralıklı.

KALİBRASYON KAYNAĞI
-------------------
Fiyatlar, işverenin kendi referans projesi olan AQUA FLORYA / SALTBAE
(Vogelkopp İnşaat kesin hakedişi, 13.05.2025, KDV hariç gerçekleşen birim
fiyatlar) ile kalibre edilmiştir. Referanstan alınan gerçekleşmiş oranlar:

  Alçıpan tek karkas + çift yüz çift kat dıamant .......  2.450 TL/m²
  Alçıpan tek karkas + tek yüz çift kat ................  1.800 TL/m²
  Alçıpan tek karkas + tek yüz tek kat .................  1.450 TL/m²
  Alçıpan asma tavan (dıamant) .........................  1.450 TL/m²
  Taşyünü yerleştirilmesi ..............................    150 TL/m²
  Seramik işçiliği — zemin / duvar .....................  700 / 725 TL/m²
  Şap (malzeme + işçilik, h ≈ 10 cm) ...................    600 TL/m²
  Şap söküm ............................................    471 TL/m²
  Çimento esaslı çift komponentli su yalıtımı ..........    610 TL/m²
  Alüminyum/paslanmaz süpürgelik .......................  2.200 TL/mt
  Düz işçi / usta yevmiyesi ............................  3.500 / 4.500 TL
  Büyük kamyon moloz atımı .............................  12.000 TL/sefer

ESKALASYON: Mayıs 2025 → Eylül 2026 (16 ay) için 1,40 katsayısı uygulanmıştır
(yıllık ≈ %28 inşaat maliyet artışı kabulü). Katsayı tek yerden değiştirilebilir.

NOT — ÖNEMLİ BULGU: Rev C'deki mimari birim fiyatlar bu referansla
karşılaştırıldığında düşük kalmıştır (örn. alçıpan bölme ≈ 663 TL/m² idi;
referans karşılığı 3.430 TL/m²). Rev E fiyatları referansa göre yeniden
kurulmuştur. Mekanik ve elektrik kalemleri referans projede çok farklı bir
kapsama (restoran mutfağı, VRF, soğuk oda, 630 A abonelik) ait olduğu için
kalibrasyona dâhil edilmemiş, Rev C değerleriyle korunmuştur.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import metraj as MT

ESKALASYON = 1.40          # Mayıs 2025 → Eylül 2026
REF_TARIH  = "Mayıs 2025 (Vogelkopp kesin hakedişi) · Eylül 2026'ya eskale"

# poz: (malzeme_min, malzeme_maks, işçilik_min, işçilik_maks)   TL / birim, KDV hariç
F = {
# ── A · YIKIM VE SÖKÜM ────────────────────────────────────────────────────────
"A.1.1": (0, 0, 240, 380),
"A.1.2": (0, 0, 180, 300),
"A.1.3": (0, 0, 600, 850),
"A.1.4": (0, 0, 25000, 42000),
"A.1.5": (0, 0, 35000, 60000),
"A.1.6": (0, 0, 3600, 5200),
# ── B · BÖLME DUVAR ──────────────────────────────────────────────────────────
"B.1.1": (1900, 2350, 1300, 1700),
"B.1.2": (2250, 2800, 1300, 1700),
"B.1.3": (1900, 2450, 1150, 1500),
# ── C · ŞAP VE TESVİYE ───────────────────────────────────────────────────────
"C.1.1": (320, 480, 260, 380),
"C.1.2": (420, 580, 420, 600),
"C.1.3": (520, 720, 460, 650),
"C.1.4": (480, 680, 440, 620),
"C.1.5": (560, 780, 620, 880),
# ── D · ZEMİN KAPLAMA VE SÜPÜRGELİK ──────────────────────────────────────────
"D.1.1": (2400, 3400, 350, 520),
"D.1.2": (1350, 1950, 300, 450),
"D.1.3": (950, 1500, 420, 620),
"D.1.4": (750, 1150, 980, 1350),
"D.1.5": (850, 1350, 980, 1350),
"D.1.6": (650, 980, 180, 280),
"D.2.1": (210, 330, 140, 220),
"D.2.2": (240, 380, 160, 250),
"D.2.4": (180, 290, 200, 310),
# ── E · SERAMİK VE SU YALITIMI ───────────────────────────────────────────────
"E.1.1": (780, 1250, 1015, 1400),
"E.1.2": (780, 1250, 1015, 1400),
"E.1.3": (480, 700, 380, 560),
"E.1.4": (480, 700, 420, 620),
"E.1.5": (95, 160, 120, 190),
# ── F · ASMA TAVAN VE BOYA ───────────────────────────────────────────────────
"F.1.1": (1050, 1400, 950, 1300),
"F.1.2": (1050, 1400, 950, 1300),
"F.1.3": (1250, 1650, 980, 1350),
"F.1.4": (180, 280, 420, 650),
"F.1.5": (1400, 2200, 450, 700),
"F.1.6": (2800, 4500, 450, 700),
"F.2.1": (145, 230, 240, 380),
"F.2.2": (180, 290, 240, 380),
"F.2.3": (145, 230, 260, 400),
# ── G · DOĞRAMA, CAM VE AYNA ─────────────────────────────────────────────────
"G.1.1": (38000, 62000, 12000, 20000),
"G.1.2": (42000, 68000, 12000, 20000),
"G.1.3": (14000, 22000, 4500, 7000),
"G.1.4": (14000, 22000, 4500, 7000),
"G.1.5": (11000, 18000, 4000, 6500),
"G.1.6": (11000, 18000, 4000, 6500),
"G.1.7": (13000, 21000, 4500, 7000),
"G.1.8": (13000, 21000, 4500, 7000),
"G.1.9": (6500, 11000, 2500, 4000),
"G.2.1": (3200, 5200, 1400, 2200),
"G.2.2": (3800, 6200, 1200, 1900),
"G.2.3": (420, 700, 320, 520),
# ── H · SABİT MOBİLYA ────────────────────────────────────────────────────────
"H.1.1": (48000, 78000, 15000, 25000),
"H.1.2": (26000, 44000, 5000, 8500),
"H.1.3": (9500, 16000, 2800, 4500),
"H.1.4": (2200, 3800, 700, 1200),
"H.1.5": (14000, 24000, 4500, 7500),
# ── I · YANGIN GÜVENLİK ──────────────────────────────────────────────────────
"I.1.1": (2400, 3900, 600, 1000),
"I.1.2": (26000, 42000, 7000, 12000),
"I.1.3": (900, 1600, 350, 600),
# ── J · GENEL GİDERLER ───────────────────────────────────────────────────────
"J.1.1": (0, 0, 480, 760),
"J.1.2": (18000, 32000, 37000, 63000),
"J.1.3": (0, 0, 48000, 85000),
"J.1.4": (0, 0, 4900, 6800),
}

# ── grup tanımları (uygulama paketi = hakediş icmalindeki satırlar) ───────────
GRUP = [
 ("A", "YIKIM · SÖKÜM VE MOLOZ ATMA İŞLERİ",      "MMK / taşeron",   0.20),
 ("B", "BÖLME DUVAR VE ALÇIPAN İŞLERİ",           "Alçıpan taşeronu", 0.20),
 ("C", "ŞAP VE TESVİYE İŞLERİ",                   "Şap taşeronu",     0.20),
 ("D", "ZEMİN KAPLAMA VE SÜPÜRGELİK İŞLERİ",      "Kaplama taşeronu", 0.20),
 ("E", "SERAMİK VE SU YALITIMI İŞLERİ",           "Seramik taşeronu", 0.20),
 ("F", "ASMA TAVAN VE BOYA İŞLERİ",               "Tavan/boya taşeronu", 0.20),
 ("G", "DOĞRAMA, CAM VE AYNA İŞLERİ",             "Doğrama taşeronu", 0.20),
 ("H", "SABİT MOBİLYA İŞLERİ",                    "Marangoz",         0.20),
 ("I", "YANGIN GÜVENLİK VE İŞARETLEME",           "Yangın firması",   0.20),
 ("J", "ŞANTİYE GENEL GİDERLERİ",                 "Ana yüklenici",    0.20),
]
GRUP_AD = {g[0]: g[1] for g in GRUP}
KDV = {g[0]: g[3] for g in GRUP}

def satirlar():
    """[(poz, ad, birim, mahal, miktar, mlz_min, mlz_max, isc_min, isc_max,
         tut_min, tut_max)]"""
    out = []
    for c in MT.CETVEL:
        mm, mM, im, iM = F.get(c.poz, (0, 0, 0, 0))
        out.append((c.poz, c.ad, c.birim, c.mahal, c.miktar, mm, mM, im, iM,
                    round(c.miktar*(mm+im), 2), round(c.miktar*(mM+iM), 2)))
    return out

def grup_toplam():
    t = {}
    for r in satirlar():
        g = r[0][0]
        a = t.setdefault(g, [0.0, 0.0, 0])
        a[0] += r[9]; a[1] += r[10]; a[2] += 1
    return {k: (round(v[0], 2), round(v[1], 2), v[2]) for k, v in t.items()}

MIMARI_MIN = round(sum(r[9] for r in satirlar()), 2)
MIMARI_MAX = round(sum(r[10] for r in satirlar()), 2)

if __name__ == "__main__":
    print(f"BİRİM FİYAT KAYNAĞI: {REF_TARIH}  ·  eskalasyon ×{ESKALASYON}\n")
    for g, ad, firma, kdv in GRUP:
        lo, hi, n = grup_toplam().get(g, (0, 0, 0))
        print(f"  {g}  {ad:42s} {n:3d} poz  {lo:14,.0f} – {hi:14,.0f} TL")
    print(f"\n  MİMARİ TOPLAM (KDV hariç) : {MIMARI_MIN:,.0f} – {MIMARI_MAX:,.0f} TL")
    import proj as P
    mek = (sum(r[4]*r[5] for r in P.B_MEK), sum(r[4]*r[6] for r in P.B_MEK))
    elk = (sum(r[4]*r[5] for r in P.B_ELK), sum(r[4]*r[6] for r in P.B_ELK))
    print(f"  MEKANİK (Rev C korundu)   : {mek[0]:,.0f} – {mek[1]:,.0f} TL")
    print(f"  ELEKTRİK (Rev C korundu)  : {elk[0]:,.0f} – {elk[1]:,.0f} TL")
    print(f"  GENEL TOPLAM (KDV hariç)  : {MIMARI_MIN+mek[0]+elk[0]:,.0f} – "
          f"{MIMARI_MAX+mek[1]+elk[1]:,.0f} TL")
