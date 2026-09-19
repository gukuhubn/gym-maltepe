# -*- coding: utf-8 -*-
"""MALZEME GÖSTERİM KÜTÜPHANESİ — kesitte hangi malzeme nasıl çizilir.

NEDEN: Bu projenin duvarları bugüne kadar TEK bir bantla ve TEK bir taramayla
çiziliyordu. Yani duvarın içinde ne olduğu — levha, dikme, boşluk, yalıtım,
yalıtım bandı, seramik — çizimde hiç görünmüyordu. Teknik resimde duvar
"bir kalınlık" değil, katmanların toplamıdır ve her katman kendi malzeme
gösterimiyle çizilir.

ÖĞRENİLEN KAYNAKLAR (input/standart/ altında, indirme tarihi 18.09.2026)
  MEGEP — "Yapı Elemanları Ölçülendirme ve Tarama" (MEB, açık erişim)
      Tablo 2.1  : duvar ifadesi — KÜÇÜK ÖLÇEK (sıva çizgileri + poché/tarama)
                   ve BÜYÜK ÖLÇEK (gerçek malzeme dokusu: tuğla sırası, taş)
      Tablo 2.7/8: döşeme ve kiriş ifadesinin 1/100 · 1/50 · 1/20'de DEĞİŞMESİ
      Şekil 2.24–2.47: ahşap · beton · grobeton · donatılı beton · metal ·
                   seramik · ısı-ses yalıtımı · SU VE NEM YALITIMI · mantar ·
                   lastik · sünger taramaları
      Şekil 2.48 : 1/50 duvar ifadesi (10'luk ve 20'lik duvar)
  MEGEP — "Alçı Levha ile Bölme Duvar" (MEB, açık erişim)
      Şekil 1.3  : tek dikmeli / çift katlı kaplama YATAY KESİT — aks aralığı
                   ölçülü, C profil kesiti çizili, boşlukta yalıtım taraması
      Tablo 1.2  : DC50/DC75/DC100 aks aralığı ve azami duvar yüksekliği
  DALSAN — Alçı uygulama kılavuzu (üretici, açık erişim)

İKİ TEMEL KURAL BURADAN GELİR
  1) ÖLÇEĞE GÖRE İFADE. 1/100'de duvar poché'dir; 1/50'de katman çizgileri
     görünür; 1/20 ve büyüğünde gerçek malzeme dokusu ve dikme çizilir.
  2) HER KATMAN KENDİ GÖSTERİMİ. Katman ayrım çizgisi ince (0,13–0,18),
     kesilen eleman çeperi kalın (0,70). Tarama asla çeperden kalın olmaz.

AUTOCAD UYUMU
  Kullanılan desenler acad.pat içinde STANDART olarak bulunanlarla sınırlıdır
  (ACAD_DESEN kümesi). ezdxf'in genişletilmiş kütüphanesindeki CONCRETE1,
  WOOD1, BRICK_* gibi desenler AutoCAD'de "unable to retrieve pattern
  definition" verir; bu yüzden KULLANILMAZ. Deseni olmayan malzemeler
  (su yalıtımı, C dikme, seramik derzi) GERÇEK GEOMETRİ olarak çizilir —
  her CAD'de aynı görünür.
"""
from __future__ import annotations
import math

from shapely.geometry import Polygon, LineString

K = 1000.0            # m → model birimi (mm)

# AutoCAD acad.pat içinde standart olarak bulunan desenler (beyaz liste)
ACAD_DESEN = {
    "ANSI31", "ANSI32", "ANSI33", "ANSI34", "ANSI35", "ANSI36", "ANSI37", "ANSI38",
    "AR-B816", "AR-B816C", "AR-B88", "AR-BRELM", "AR-BRSTD", "AR-CONC", "AR-HBONE",
    "AR-PARQ1", "AR-RROOF", "AR-RSHKE", "AR-SAND", "BOX", "BRASS", "BRICK",
    "BRSTONE", "CLAY", "CORK", "CROSS", "DASH", "DOLMIT", "DOTS", "EARTH",
    "ESCHER", "FLEX", "GRASS", "GRATE", "GRAVEL", "HEX", "HONEY", "HOUND",
    "INSUL", "LINE", "MUDST", "NET", "NET3", "PLAST", "PLASTI", "SACNCR",
    "SAND", "SQUARE", "STARS", "STEEL", "SWAMP", "TRANS", "TRIANG", "ZIGZAG",
    "SOLID",
}

# Desenlerin TABAN ARALIĞI desen tanımından HESAPLANIR, elle yazılmaz.
# (Elle yazıldığında INSUL için 0,375 sanılmıştı; gerçek değer 9,525'tir —
# 25 kat hata, yalıtım taraması hiç görünmüyordu. AR-CONC'ta ters yönde aynı
# hata beton taramasını paftayı boydan boya kesen tek çizgiye çeviriyordu.)
_TABAN_ONBELLEK = {}


def desen_tabani(desen: str) -> float:
    """Desenin en küçük çizgi aralığı (desen birimi)."""
    if desen in _TABAN_ONBELLEK: return _TABAN_ONBELLEK[desen]
    taban = 0.125
    try:
        from ezdxf.tools import pattern as _pat
        tanim = _pat.load().get(desen)
        if tanim:
            araliklar = []
            for satir in tanim:
                ofs = satir[2]
                d = math.hypot(ofs[0], ofs[1])
                if d > 1e-9: araliklar.append(d)
            if araliklar: taban = min(araliklar)
    except Exception:
        pass
    _TABAN_ONBELLEK[desen] = taban
    return taban


def desen_olcek(desen: str, kagit_mm: float, olcek: float) -> float:
    """Kâğıtta istenen tarama aralığını (mm) desenin model ölçeğine çevirir."""
    return kagit_mm * olcek / desen_tabani(desen)


# ── MALZEME KAYDI ────────────────────────────────────────────────────────────
# yontem : "desen"  → hatch deseni
#          "dolu"   → solid dolgu (poché)
#          "bos"    → tarama yok, yalnız katman çizgisi
#          "ozel"   → gerçek geometriyle çizilir (aşağıdaki _ozel_* işlevleri)
# kagit  : kâğıtta istenen tarama aralığı (mm) — ölçek ne olursa olsun sabit
# asgari : bu ölçekten (payda) büyük paftalarda tarama BASTIRILIR; küçük
#          ölçekte doku okunmaz, çizimi kirletir (MEGEP Tablo 2.1/2.7 ilkesi)
MALZEME = {
    # yapısal
    "betonarme":  dict(ad="Betonarme",              yontem="desen", desen="AR-CONC", kagit=3.0, aci=0,  asgari=100),
    "beton":      dict(ad="Beton",                  yontem="desen", desen="AR-CONC", kagit=3.0, aci=0,  asgari=100),
    "grobeton":   dict(ad="Grobeton",               yontem="desen", desen="GRAVEL",  kagit=2.0, aci=0,  asgari=50),
    "tugla":      dict(ad="Tuğla dolgu duvar",      yontem="desen", desen="ANSI32",  kagit=3.0, aci=45, asgari=50),
    "tugla_buyuk":dict(ad="Tuğla — sıra dokusu",    yontem="ozel",  ozel="tugla_sira",                  asgari=25),
    # şap / harç
    "sap":        dict(ad="Şap / tesviye",          yontem="desen", desen="ANSI31",  kagit=2.2, aci=45, asgari=50),
    "harc":       dict(ad="Yapıştırma harcı",       yontem="desen", desen="ANSI31",  kagit=1.4, aci=45, asgari=25),
    "siva":       dict(ad="Sıva / saten alçı",      yontem="bos",                                       asgari=50),
    # kuru yapı
    "alcipan":    dict(ad="Alçı levha",             yontem="bos",                                       asgari=50),
    "alcipan_h2": dict(ad="H2 su itici alçı levha", yontem="bos",                                       asgari=50),
    "dikme":      dict(ad="Galvaniz C profil",      yontem="ozel",  ozel="c_profil",                    asgari=25),
    "bosluk":     dict(ad="Karkas boşluğu",         yontem="bos",                                       asgari=25),
    # yalıtım
    "yalitim_isi":dict(ad="Isı / ses yalıtımı (taşyünü)", yontem="ozel",  ozel="yalitim_isi",                 asgari=50),
    "yalitim_su": dict(ad="Su ve nem yalıtımı",     yontem="ozel",  ozel="su_yalitimi",                 asgari=200),
    "bant":       dict(ad="Elastik su yalıtım bandı", yontem="ozel", ozel="su_yalitimi",                asgari=200),
    # kaplama
    "seramik":    dict(ad="Porselen seramik",       yontem="ozel",  ozel="seramik",                     asgari=10),
    "kaucuk":     dict(ad="Kauçuk karo",            yontem="desen", desen="ANSI37",  kagit=2.0, aci=45, asgari=50),
    "ahsap":      dict(ad="Ahşap",                  yontem="desen", desen="ANSI33",  kagit=1.8, aci=0,  asgari=50),
    "metal":      dict(ad="Metal",                  yontem="desen", desen="ANSI32",  kagit=0.8, aci=45, asgari=50),
    "cam":        dict(ad="Cam",                    yontem="bos",                                       asgari=50),
    "toprak":     dict(ad="Doğal zemin",            yontem="desen", desen="EARTH",   kagit=2.4, aci=45, asgari=100),
    "bosalan":    dict(ad="—",                      yontem="bos",                                       asgari=1),
}

# çizgi katmanları
KAT_CEPER   = "A-KESIT-KESILEN"     # kesilen eleman çeperi   0,70
KAT_KATMAN  = "A-KATMAN-CIZGI"      # katman ayrım çizgisi    0,13
KAT_TARAMA  = "A-KESIT-TARAMA"      # tarama                  0,13
KAT_YALITIM = "A-KATMAN-YALITIM"    # su yalıtımı             0,35
KAT_DIKME   = "A-KESIT-GORUNEN"     # dikme / profil          0,35


def bilgi(m):
    return MALZEME.get(m, MALZEME["bosalan"])


# ── ÇİZİM ────────────────────────────────────────────────────────────────────
def _hatch(msp, g, kat, desen, kagit, aci, olcek, renk=None):
    n = 0
    for q in (g.geoms if hasattr(g, "geoms") else [g]):
        if q.is_empty or q.area < 1e-9: continue
        h = msp.add_hatch(dxfattribs={"layer": kat, **({"color": renk} if renk else {})})
        if desen == "SOLID":
            h.set_solid_fill(color=renk or 7)
        else:
            h.set_pattern_fill(desen, scale=desen_olcek(desen, kagit, olcek), angle=aci)
        h.paths.add_polyline_path([(x*K, y*K) for x, y in q.exterior.coords[:-1]],
                                  is_closed=True, flags=1)
        for r in q.interiors:
            h.paths.add_polyline_path([(x*K, y*K) for x, y in r.coords[:-1]],
                                      is_closed=True, flags=0)
        n += 1
    return n


def _pl(msp, pts, kat, kapali=True):
    return msp.add_lwpolyline([(x*K, y*K) for x, y in pts], close=kapali,
                              dxfattribs={"layer": kat})


def _ln(msp, a, b, kat):
    return msp.add_line((a[0]*K, a[1]*K), (b[0]*K, b[1]*K), dxfattribs={"layer": kat})


INCE_SINIR_MM = 0.45     # kâğıtta bundan ince katman bant çizilmez


def _kalinlik(dortgen, u_yon):
    o, du, dv, U, V = _uv_kutu(dortgen, u_yon)
    return V, o, du, dv, U


def katman_ciz(msp, dortgen, malzeme, olcek, u_yon=(1.0, 0.0), ceper=False):
    """Tek bir katmanı çizer: sınır çizgisi + malzemesine uygun gösterim.

    dortgen : shapely Polygon (metre)
    u_yon   : katmanın UZUNLUK yönü — dikme, seramik derzi, sıra dokusu bu
              yöne göre dizilir
    ceper   : True ise sınır KESİLEN ÇEPER kalınlığında çizilir

    İNCE KATMAN KURALI (teknik resim): kâğıt üzerinde 0,45 mm'den ince kalan
    katman iki çizgi arası bant olarak çizilemez — mürekkep birbirine girer.
    Böyle katmanlar EKSENİNDE TEK ÇİZGİ ile gösterilir; su yalıtımı gibi
    kritik olanlar kendi kaleminde (0,35) çizilir ki yok sayılmasın.
    """
    # ÖLÇEĞE GÖRE İFADE (MEGEP Tablo 2.1): küçük ölçekte duvar taramayla,
    # büyük ölçekte GERÇEK DOKUYLA (tuğla sırası) gösterilir.
    if malzeme == "tugla" and olcek <= 10:
        malzeme = "tugla_buyuk"
    m = bilgi(malzeme)
    V, o, du, dv, U = _kalinlik(dortgen, u_yon)
    if V*1000.0/olcek < INCE_SINIR_MM and V > 0:
        kat = KAT_YALITIM if malzeme in ("yalitim_su", "bant") else KAT_KATMAN
        _ln(msp, _xy(o, du, dv, 0, V/2), _xy(o, du, dv, U, V/2), kat)
        return 1
    kat = KAT_CEPER if ceper else KAT_KATMAN
    _pl(msp, list(dortgen.exterior.coords)[:-1], kat)
    if olcek > m["asgari"]:
        return 0                       # bu ölçekte doku okunmaz — bastırılır
    y = m["yontem"]
    if y == "desen":
        return _hatch(msp, dortgen, KAT_TARAMA, m["desen"], m["kagit"], m["aci"], olcek)
    if y == "dolu":
        return _hatch(msp, dortgen, KAT_TARAMA, "SOLID", 0, 0, olcek)
    if y == "ozel":
        return _OZEL[m["ozel"]](msp, dortgen, olcek, u_yon)
    return 0


# ── ÖZEL GÖSTERİMLER (gerçek geometri — her CAD'de aynı) ─────────────────────
def _uv_kutu(dortgen, u_yon):
    """Dörtgeni kendi (u,v) eksenine taşır: (o, du, dv, U, V)."""
    c = list(dortgen.exterior.coords)[:-1]
    ux, uy = u_yon
    n = math.hypot(ux, uy) or 1.0
    du = (ux/n, uy/n); dv = (-du[1], du[0])
    us = [(p[0]-c[0][0])*du[0] + (p[1]-c[0][1])*du[1] for p in c]
    vs = [(p[0]-c[0][0])*dv[0] + (p[1]-c[0][1])*dv[1] for p in c]
    u0, u1 = min(us), max(us); v0, v1 = min(vs), max(vs)
    o = (c[0][0] + du[0]*u0 + dv[0]*v0, c[0][1] + du[1]*u0 + dv[1]*v0)
    return o, du, dv, u1-u0, v1-v0


def _xy(o, du, dv, u, v):
    return (o[0] + du[0]*u + dv[0]*v, o[1] + du[1]*u + dv[1]*v)


def _ozel_su_yalitimi(msp, dortgen, olcek, u_yon):
    """MEGEP Şekil 2.44 — su ve neme karşı yalıtım: dolu/boş değişen bloklar.

    Blok boyu kâğıtta sabit 1,6 mm; ölçek değişse de aynı okunur.
    """
    o, du, dv, U, V = _uv_kutu(dortgen, u_yon)
    blok = 1.6*olcek/1000.0
    t = 0.0; n = 0; dolu = True
    while t < U - 1e-9:
        t2 = min(t + blok, U)
        if dolu:
            q = Polygon([_xy(o, du, dv, t, 0), _xy(o, du, dv, t2, 0),
                         _xy(o, du, dv, t2, V), _xy(o, du, dv, t, V)])
            _hatch(msp, q, KAT_YALITIM, "SOLID", 0, 0, olcek, renk=6)
            n += 1
        t = t2; dolu = not dolu
    _pl(msp, list(dortgen.exterior.coords)[:-1], KAT_YALITIM)
    return n


def _ozel_c_profil(msp, dortgen, olcek, u_yon, ara=0.40, et=0.006,
                   kenar_dikme=False):
    """MEGEP Alçı Levha Şekil 1.3 — yatay kesitte C dikme profilleri.

    Dikmeler GERÇEK aks aralığında (varsayılan 400 mm) dizilir; sayıları
    duvarın gerçek uzunluğundan çıkar, elle yazılmaz. `kenar_dikme` ile
    parçanın iki ucuna da dikme konur (kapı/pencere kenarı — Knauf W11
    "boşluk kenarında UA profil veya takviyeli C").
    """
    o, du, dv, U, V = _uv_kutu(dortgen, u_yon)
    n = 0
    f = V*0.62
    if kenar_dikme:
        for t in (0.004, U - f - 0.004):
            if 0 <= t <= U - f:
                pts = [(t, V), (t, 0.0), (t+f, 0.0), (t+f, et), (t+et, et),
                       (t+et, V-et), (t+f, V-et), (t+f, V), (t, V)]
                _pl(msp, [_xy(o, du, dv, a, b) for a, b in pts], KAT_DIKME, kapali=False)
                n += 1
    t = ara/2
    while t < U - 0.02:
        if kenar_dikme and (t < f + 0.02 or t > U - f - 0.02):
            t += ara; continue
        # C kesiti: sırt + iki flanş (flanş boyu gövdenin %62'si — DC profil oranı)
        f = V*0.62
        pts = [(t+et, f), (t, f), (t, 0.0), (t+et, 0.0)] if False else [
            (t, V), (t, 0.0), (t+f, 0.0), (t+f, et),
            (t+et, et), (t+et, V-et), (t+f, V-et), (t+f, V), (t, V)]
        _pl(msp, [_xy(o, du, dv, a, b) for a, b in pts], KAT_DIKME, kapali=False)
        n += 1
        t += ara
    return n


def _ozel_seramik(msp, dortgen, olcek, u_yon, karo=0.30):
    """Seramik: kesitte ince katman + GERÇEK karo boyunda derz çentiği."""
    o, du, dv, U, V = _uv_kutu(dortgen, u_yon)
    n = 0
    t = karo
    while t < U - 1e-6:
        _ln(msp, _xy(o, du, dv, t, 0), _xy(o, du, dv, t, V), KAT_KATMAN); n += 1
        t += karo
    return n


def _ozel_tugla_sira(msp, dortgen, olcek, u_yon, sira=0.085, derz=0.010):
    """MEGEP Tablo 2.1 büyük ölçek — tuğla sırası gerçek yüksekliğiyle.

    Sıralar duvarın UZUNLUK yönünde dizilir; her sıra arasında derz çizgisi,
    bir sırada bir şaşırtmalı düşey derz. Ölçek 1/10 ve büyüğünde devreye
    girer; küçük ölçekte yerine ANSI32 taraması kullanılır.
    """
    o, du, dv, U, V = _uv_kutu(dortgen, u_yon)
    n = 0; t = sira; i = 0
    while t < U - 1e-6:
        _ln(msp, _xy(o, du, dv, t, 0), _xy(o, du, dv, t, V), KAT_KATMAN); n += 1
        # şaşırtmalı düşey derz (sıra ortasında)
        if i % 2 == 0 and V > 0.04:
            _ln(msp, _xy(o, du, dv, t-sira/2, V*0.5), _xy(o, du, dv, t+sira/2, V*0.5),
                KAT_KATMAN)
        t += sira + derz; i += 1
    return n


def _ozel_yalitim_isi(msp, dortgen, olcek, u_yon):
    """MEGEP Şekil 2.43 — ısı/ses yalıtımı: sürekli zikzak (yorgan) dokusu.

    Hatch deseni yerine GERÇEK GEOMETRİ: 50 mm'lik bir karkas boşluğu 1:20'de
    kâğıtta 2,5 mm'dir; INSUL deseni bu genişlikte ya hiç görünmez ya da dolu
    siyah bant verir. Zikzak, dalga boyu kâğıtta sabit tutularak çizilir ve
    her ölçekte aynı okunur.
    """
    o, du, dv, U, V = _uv_kutu(dortgen, u_yon)
    if V < 1e-4 or U < 1e-4: return 0
    dalga = max(1.8*olcek/1000.0, V*0.55)      # kâğıtta ~1,8 mm
    pay = V*0.14
    ust, alt = V-pay, pay
    pts = []; t = 0.0; yukari = True
    while t < U - 1e-9:
        pts.append(_xy(o, du, dv, min(t, U), ust if yukari else alt))
        t += dalga/2; yukari = not yukari
    if len(pts) < 2: return 0
    msp.add_lwpolyline([(x*K, y*K) for x, y in pts],
                       dxfattribs={"layer": KAT_TARAMA})
    # dış yüzlerde ince kenar çizgisi (yalıtımın sınırı)
    _ln(msp, _xy(o, du, dv, 0, pay), _xy(o, du, dv, U, pay), KAT_TARAMA)
    _ln(msp, _xy(o, du, dv, 0, V-pay), _xy(o, du, dv, U, V-pay), KAT_TARAMA)
    return 1


_OZEL = {"su_yalitimi": _ozel_su_yalitimi, "c_profil": _ozel_c_profil,
         "yalitim_isi": _ozel_yalitim_isi,
         "seramik": _ozel_seramik, "tugla_sira": _ozel_tugla_sira}


# ── SERBEST METİNDEN MALZEME SINIFI ──────────────────────────────────────────
# proj.py'deki katman tabloları insan diliyle yazılmıştır ("12,5 mm H2 (su
# itici / yeşil) alçıpan, 2 kat"). Çizim motoru bunlara bakarak malzeme
# sınıfını çıkarır; tabloya ayrıca kod yazılmaz, tek kaynak bozulmaz.
_ANAHTAR = [
    ("su itici", "alcipan_h2"), ("h2", "alcipan_h2"),
    ("alçıpan", "alcipan"), ("alçı levha", "alcipan"),
    ("c profil", "dikme"), ("karkas", "dikme"), ("dikme", "dikme"),
    ("taşyünü", "yalitim_isi"), ("yalıtım, 2 kat", "yalitim_su"),
    ("su yalıtımı", "yalitim_su"), ("bant", "bant"),
    ("hava boşluğu", "bosluk"),
    ("seramik", "seramik"), ("porselen", "seramik"),
    ("yapıştırıcı", "harc"), ("c2te", "harc"),
    ("şap", "sap"), ("tesviye", "sap"),
    ("mevcut duvar", "tugla"), ("yığma", "tugla"),
    ("betonarme", "betonarme"), ("beton", "beton"),
    ("yığma", "tugla"), ("tuğla", "tugla"),
    ("saten", "siva"), ("sıva", "siva"), ("boya", "siva"), ("astar", "siva"),
    ("kauçuk", "kaucuk"), ("kontrplak", "ahsap"), ("kontraplak", "ahsap"),
    ("ahşap", "ahsap"), ("ayna", "cam"), ("cam", "cam"),
    ("galvaniz", "metal"), ("profil", "metal"),
]


def sinifla(ad: str) -> str:
    t = (ad or "").lower()
    for anahtar, m in _ANAHTAR:
        if anahtar in t: return m
    return "bosalan"


def katmanlari_coz(tablo):
    """proj.py katman listesini [(malzeme, kalinlik_m, ad)] hâline getirir.

    Kalınlığı 0 verilmiş katmanlar (ör. karkas içindeki taşyünü) ayrı bir
    katman değildir; bir ÖNCEKİ katmanın içine gömülüdür — dolgu olarak
    işaretlenir ki boşluk taraması doğru malzemeyle yapılsın.
    """
    out = []
    for ad, mm in [(t[0], t[1]) for t in tablo]:
        m = sinifla(ad)
        if mm and mm > 0:
            out.append({"malzeme": m, "m": mm/1000.0, "ad": ad, "dolgu": None})
        elif out:
            out[-1]["dolgu"] = m          # kalınlıksız katman = içteki dolgu
    return out


def _parcala(L, bosluklar):
    """[0,L] aralığını boşluklar dışında kalan dolu parçalara böler."""
    kes = sorted((max(0.0, a), min(L, b)) for a, b in (bosluklar or []) if b > a)
    dolu, t = [], 0.0
    for a, b in kes:
        if a > t + 1e-6: dolu.append((t, a))
        t = max(t, b)
    if L > t + 1e-6: dolu.append((t, L))
    return dolu


def duvar_kesiti(msp, a, b, katmanlar, olcek, taraf=1, dikme_ara=0.40,
                 ceper_dis=True, bosluklar=None, sove=True):
    """İki nokta arasında ÇOK KATMANLI duvarı çizer.

    a, b        : duvarın referans yüzü (metre)
    katmanlar   : katmanlari_coz() çıktısı — sırayla `taraf` yönünde dizilir
    taraf       : +1 sol normal, -1 sağ normal
    dikme_ara   : karkas aks aralığı (m) — C profiller bu aralıkla dizilir
    ceper_dis   : en dıştaki katmanın dış yüzü kesilen çeper kalınlığında
    bosluklar   : [(u0, u1)] — a'dan ölçülen KAPI/PENCERE boşlukları (m).
                  MEGEP Şekil 2.51: "duvar üzerinde kapı genişliği kadar
                  boşluk açılır" — bütün katmanlar boşlukta KESİLİR; duvar
                  kapının içinden geçmez. Boşluk kenarına söve (reveal)
                  çizgisi konur: kesilen çeper kalınlığında, tüm katmanları
                  bir uçtan öbür uca kapatır.
    sove        : boşluk kenarlarına söve çizgisi çizilsin mi

    Döner: (toplam_kalinlik, cizilen_katman_sayisi)
    """
    ax, ay = a; bx, by = b
    L = math.hypot(bx-ax, by-ay)
    if L < 1e-6: return (0.0, 0)
    ux, uy = (bx-ax)/L, (by-ay)/L
    nx, ny = -uy*taraf, ux*taraf
    toplam = sum(k["m"] for k in katmanlar)
    parcalar = _parcala(L, bosluklar)
    def P(u, t): return (ax + ux*u + nx*t, ay + uy*u + ny*t)
    n = 0
    for u0, u1 in parcalar:
        t0 = 0.0
        for i, k in enumerate(katmanlar):
            t1 = t0 + k["m"]
            q = Polygon([P(u0, t0), P(u1, t0), P(u1, t1), P(u0, t1)])
            son = (i == len(katmanlar)-1)
            ceper = (i == 0) or (son and ceper_dis)
            if k["malzeme"] == "dikme":
                if k.get("dolgu") and k["dolgu"] != "bosalan":
                    katman_ciz(msp, q, k["dolgu"], olcek, (ux, uy), ceper=False)
                    _pl(msp, list(q.exterior.coords)[:-1], KAT_KATMAN)
                else:
                    _pl(msp, list(q.exterior.coords)[:-1], KAT_KATMAN)
                if olcek <= bilgi("dikme")["asgari"]:
                    # Kapı kenarında takviyeli dikme (UA profil) — Knauf W11:
                    # boşluk kenarına her zaman bir dikme gelir.
                    _ozel_c_profil(msp, q, olcek, (ux, uy), ara=dikme_ara,
                                   kenar_dikme=bool(bosluklar))
            else:
                katman_ciz(msp, q, k["malzeme"], olcek, (ux, uy), ceper=ceper)
            t0 = t1; n += 1
    if sove and bosluklar:
        for u0, u1 in bosluklar:
            for u in (u0, u1):
                if 1e-6 < u < L - 1e-6:
                    _ln(msp, P(u, 0.0), P(u, toplam), KAT_CEPER)
    return (toplam, n)


def altlik_ayikla(kaplama):
    """Kaplama paketinin başındaki 'mevcut duvar / D3 ıslak yüzü' yer tutucusunu
    atar. D5 tablosu 216 mm der ama bunun 200 mm'si ALTLIKTIR; altlık D3 ise
    gerçek toplam 116 mm olur. Ayıklanmazsa duvar iki kez sayılır."""
    out = list(kaplama)
    while out and ("mevcut" in out[0]["ad"].lower() or
                   "yüzü" in out[0]["ad"].lower()):
        out.pop(0)
    return out


def birlestir(*paketler):
    """Birden çok katman paketini tek bir kesit dizisine bağlar (içten dışa)."""
    out = []
    for i, p in enumerate(paketler):
        out += (altlik_ayikla(p) if i else list(p))
    return out


def katman_etiketi(katmanlar):
    """Katman listesinin okunur özeti — antet ve lejant için."""
    return " + ".join(f"{bilgi(k['malzeme'])['ad']} {k['m']*1000:.0f}"
                      for k in katmanlar)
