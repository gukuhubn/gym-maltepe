# -*- coding: utf-8 -*-
"""PİLOT ÇİZİM — ERKEK ISLAK BLOK (105 soyunma · 106 duş · 107 WC)

Talimat §12'nin istediği pilot teslim: sınırlı bir bölge için ölçülü plan,
tavan planı, koordinasyon kesiti, iç görünüş ve GERÇEK bir birleşim detayı.
Beşi de aynı veri modelinden (tools/proj.py) türetilir; hiçbiri elle
koordinat dizisi değildir. Geometri ölçülmüş rölöveden gelir
(data/geometry_roleve.json ← input/ESAT-FINAL.dwg).

Paftalar (A2, ISO 5457 çerçeve · ISO 7200 antet)
  P-01  ÖLÇÜLÜ PLAN                        1:20
  P-02  TAVAN PLANI (RCP)                  1:20
  P-03  KOORDİNASYON KESİTİ K1-K1          1:20
  P-04  İÇ GÖRÜNÜŞ G-05 — DUŞ BATI DUVARI  1:20
  P-05  BİRLEŞİM DETAYI D-02               1:5

Yerel eksen takımı: blok bir paralelkenar değil, 8,8° dönük bir dikdörtgendir.
Kesit ve görünüşler bloğun KENDİ eksenlerinde (u,v) kurulur; böylece ölçüler
gerçek imalat ölçüleridir, dünya eksenine izdüşüm değil.

    u : kısa kenar yönü  (0 → 2,200 m)   — soyunma/duş genişliği
    v : uzun kenar yönü  (0 → 3,750 m)   — soyunma(0–2,109) · duş·WC(2,109–3,729)
"""
from __future__ import annotations
import math, sys, os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ezdxf
from ezdxf.enums import TextEntityAlignment as TA
from shapely.geometry import Polygon, Point, LineString

import proj as P
import dxf_lib as X
import malzeme as MZ
from dxf_lib import M, ML, yazi, poli, cizgi, tarama, sekil, K
import pafta as PF
from pafta import Pafta

KOK = Path(__file__).resolve().parent.parent
CIK = KOK/"cad"/"pilot"; CIK.mkdir(parents=True, exist_ok=True)

BLOK   = "ERKEK"
OLCEK  = 20
OLCEK_DETAY = 5
BOY    = "A2"
MAHAL  = {"soyunma": "105", "dus": "106", "wc": "107"}

PROJE_BILGI = {
    "isveren": "ÖZEL — MALTEPE / İDEALTEPE",
    "proje": P.PROJE,
    "yapi": "Mevcut mağaza → fonksiyonel antrenman stüdyosu (fit-out)",
    "ada_parsel": "yerinde doğrulanacak",
}
MUELLIF = "—  (proje müellifi imzası için ayrılmıştır)"
SICIL   = "—"

PAFTALAR = {
 "P-01": ("ÖLÇÜLÜ PLAN — ERKEK ISLAK BLOK", "MİMARİ", OLCEK),
 "P-02": ("TAVAN PLANI (RCP) — ERKEK ISLAK BLOK", "MİMARİ", OLCEK),
 "P-03": ("KOORDİNASYON KESİTİ K1-K1", "KOORDİNASYON", OLCEK),
 "P-04": ("İÇ GÖRÜNÜŞ G-05 — 106 DUŞ, BATI DUVARI", "İÇ MİMARİ", OLCEK),
 "P-05": ("BİRLEŞİM DETAYI D-02 — Z4 ZEMİN / D5 DUVAR SU YALITIMI", "DETAY", OLCEK_DETAY),
}
SIRA = list(PAFTALAR)


# ══════════════════════════ YEREL EKSEN TAKIMI ════════════════════════════════
def eksen():
    """Bloğun kendi (u,v) eksen takımı — köşelerden türetilir, elle yazılmaz."""
    c = list(P.ISLAK[BLOK]["tum"].exterior.coords)[:-1]
    # en kısa kenardan başlayan köşeyi orijin al
    kenar = [(math.dist(c[i], c[(i+1) % len(c)]), i) for i in range(len(c))]
    Lk, i0 = min(kenar)
    o = c[i0]
    a = c[(i0+1) % len(c)]
    b = c[(i0-1) % len(c)]
    du = ((a[0]-o[0])/Lk, (a[1]-o[1])/Lk)
    Lv = math.dist(o, b)
    dv = ((b[0]-o[0])/Lv, (b[1]-o[1])/Lv)
    # v yönü soyunmadan duşa doğru baksın
    s = P.ISLAK[BLOK]["soyunma"].centroid
    d = P.ISLAK[BLOK]["dus"].centroid
    if (d.x-s.x)*dv[0] + (d.y-s.y)*dv[1] < 0:
        o = b; dv = (-dv[0], -dv[1])
    return o, du, dv, Lk, Lv


ORG, DU, DV, W_BLOK, L_BLOK = eksen()


def uv(p):
    """dünya (x,y) → yerel (u,v), metre."""
    dx, dy = p[0]-ORG[0], p[1]-ORG[1]
    return (dx*DU[0] + dy*DU[1], dx*DV[0] + dy*DV[1])


def xy(u, v):
    """yerel (u,v) → dünya (x,y), metre."""
    return (ORG[0] + u*DU[0] + v*DV[0], ORG[1] + u*DU[1] + v*DV[1])


def uv_kutu(g):
    q = [uv(p) for p in g.exterior.coords[:-1]]
    return (min(a for a, _ in q), min(b for _, b in q),
            max(a for a, _ in q), max(b for _, b in q))


ALT_UV = {n: uv_kutu(P.ISLAK[BLOK][n]) for n in ("soyunma", "dus", "wc")}
ACI_DER = math.degrees(math.atan2(DU[1], DU[0]))


# ══════════════════════════ ORTAK ÇİZİM YARDIMCILARI ══════════════════════════
def _ln(msp, a, b, kat, lw=None):
    d = {"layer": kat}
    if lw: d["lineweight"] = lw
    return msp.add_line((a[0]*K, a[1]*K), (b[0]*K, b[1]*K), dxfattribs=d)


def _pl(msp, pts, kat, kapali=True, lw=None):
    d = {"layer": kat}
    if lw: d["lineweight"] = lw
    return msp.add_lwpolyline([(x*K, y*K) for x, y in pts], close=kapali, dxfattribs=d)


_DONME = 0.0   # derece — sheet builder tarafından ayarlanır


def _tx(msp, p, t, h_mm, kat, hiza="ORTA", aci=0, stil="GYM", olcek=OLCEK,
        telafi=True):
    """h_mm: KÂĞITTAKİ yazı yüksekliği (ISO 3098) — model boyu ölçekle çarpılır.

    telafi: görüntü penceresi döndürülmüşse yazı ters yönde döndürülür; böylece
    kâğıtta yatay okunur. Döndürülmüş büyütme paftasında bu yapılmazsa bütün
    etiketler eğik çıkar.
    """
    return yazi(msp, (p[0]*K, p[1]*K), t, h_mm*olcek, kat,
                hiza=hiza, aci=aci + (_DONME if telafi else 0.0), stil=stil)


def _tara_olcek(kagit_mm, olcek=OLCEK):
    """Geriye dönük sarmalayıcı — gerçek hesap malzeme kütüphanesindedir."""
    return MZ.desen_olcek("ANSI31", kagit_mm, olcek)


def _tara(msp, pts, kat, desen="ANSI31", olc=1.0, aci=45):
    h = msp.add_hatch(dxfattribs={"layer": kat})
    h.set_pattern_fill(desen, scale=olc*K/40, angle=aci)
    h.paths.add_polyline_path([(x*K, y*K) for x, y in pts], is_closed=True)
    return h


def _dim(msp, p1, p2, mesafe, olcek=OLCEK, kat="G-OLCU", aci=None):
    """Gerçek DIMENSION nesnesi — elle yazılmış ölçü metni kullanılmaz."""
    d = msp.add_aligned_dim(p1=(p1[0]*K, p1[1]*K), p2=(p2[0]*K, p2[1]*K),
                            distance=mesafe*K, dimstyle=f"GYM-{olcek}",
                            dxfattribs={"layer": kat})
    d.render()
    return d


def _zincir(msp, noktalar, mesafe, olcek=OLCEK, toplam=True, kat="G-OLCU-ZINCIR"):
    n = 0
    for a, b in zip(noktalar, noktalar[1:]):
        if math.dist(a, b) < 0.02: continue
        _dim(msp, a, b, mesafe, olcek, kat); n += 1
    if toplam and len(noktalar) > 2:
        _dim(msp, noktalar[0], noktalar[-1], mesafe*1.6, olcek, kat); n += 1
    return n


def _kot_isareti(msp, p, kot, olcek=OLCEK, kat="A-KOT-ISARET", ust=True):
    """Üçgen kot işareti + değer (ISO 129-1 / mimari uygulama)."""
    s = 1.6*olcek/1000.0            # kâğıtta 1,6 mm
    x, y = p
    yon = 1 if ust else -1
    ca, sa = math.cos(math.radians(_DONME)), math.sin(math.radians(_DONME))
    def _d(dx, dy): return (x + dx*ca - dy*sa, y + dx*sa + dy*ca)
    _pl(msp, [_d(0, 0), _d(-s, yon*1.7*s), _d(s, yon*1.7*s)], kat, True)
    _tx(msp, _d(2.2*s, yon*1.9*s), f"{kot:+.3f}".replace(".", ","),
        2.5, kat, hiza="SOL", olcek=olcek)


def _etiket(msp, p, satirlar, olcek=OLCEK, kat="A-YAZI", hiza="SOL", h=2.5):
    ca, sa = math.cos(math.radians(_DONME)), math.sin(math.radians(_DONME))
    for i, t in enumerate(satirlar):
        d = -i*h*1.45*olcek/1000.0
        _tx(msp, (p[0] - d*sa, p[1] + d*ca), t, h, kat, hiza=hiza, olcek=olcek)


def _lider(msp, uc, kirilma, metin, olcek=OLCEK, kat="A-YAZI", sag=True, h=2.5):
    """Kılavuz çizgi + yazı — nokta gösterimi ISO 128-22."""
    msp.add_line((uc[0]*K, uc[1]*K), (kirilma[0]*K, kirilma[1]*K),
                 dxfattribs={"layer": kat})
    yat = (0.5 if sag else -0.5)*olcek/1000.0*8
    son = (kirilma[0]+yat, kirilma[1])
    msp.add_line((kirilma[0]*K, kirilma[1]*K), (son[0]*K, son[1]*K),
                 dxfattribs={"layer": kat})
    msp.add_circle((uc[0]*K, uc[1]*K), 0.5*olcek/1000.0*K/2,
                   dxfattribs={"layer": kat})
    if isinstance(metin, str): metin = [metin]
    _etiket(msp, (son[0] + (0.4 if sag else -0.4)*olcek/1000.0*4,
                  son[1] + 0.3*olcek/1000.0*4),
            metin, olcek, kat, "SOL" if sag else "SAG", h)


# ══════════════════════════ DUVAR GÖVDELERİ ═══════════════════════════════════
# Alt mekân poligonları bloğu TAM olarak döşer (2,109 + 1,620 = 3,729 ≈ 3,747);
# yani bunlar bölme DUVAR EKSENLERİdir, bitmiş yüz değil. Bitmiş mahal =
# poligondan, komşu alt mekânla PAYLAŞILAN kenarlarda yarım bölme kadar
# aşındırılmış hâli. Bu ayrım yazılmazsa mahal alanı 47 dm² fazla çıkar.
# ══════════════════════ DUVAR KURGUSU ═════════════════════════════════════════
# proj.py'deki ISLAK poligonları KABA YAPI (karkas) yüzleridir: ölçülmüş
# rölövede salon ile ıslak blok arası 98 mm ölçüldü — bu, mimarın çizdiği
# D3 bölme karkasıdır, bitmiş yüz değil. Bitmiş mahal, karkas yüzünden
# KAPLAMA KALINLIĞI kadar içeridedir. İki alan ayrı ayrı raporlanır:
# kaba yapı (imalat/karkas metrajı) ve bitmiş (mahal listesi, seramik metrajı).
BOLME_T = P.ISLAK_BOLME_T
CEPER_T = P.V["duvar_kalinlik"][0]

from shapely.ops import unary_union
_IC = unary_union([P.SALON, P.ERKEK, P.KADIN])


def _tip(kod):
    return next(d for d in P.DUVAR_TIPLERI if d[0] == kod)


def _kat(kod):
    return MZ.katmanlari_coz(_tip(kod)[3])


# D5 kaplama paketi = seramik + yapıştırıcı + su yalıtımı (altlık ayıklanmış),
# mahal yüzünden DIŞA doğru sıralı.
KAPLAMA_ISLAK = list(reversed(MZ.altlik_ayikla(_kat("D5"))))
# Kuru yüz kaplaması: saten + boya (D1'in ince katmanları)
KAPLAMA_KURU = [k for k in _kat("D1") if k["malzeme"] == "siva"]
# Karkaslar
KARKAS_BOLME = _kat("D3")                      # H2 alçıpan · C dikme · alçıpan
KARKAS_MEVCUT = [k for k in _kat("D1") if k["malzeme"] in ("betonarme", "tugla")]

KAPLAMA_T = {"islak": sum(k["m"] for k in KAPLAMA_ISLAK),   # 0,016 m
             "kuru":  sum(k["m"] for k in KAPLAMA_KURU)}    # 0,006 m

# Hangi mahal ıslak? (kaplama kalınlığı ve seramik bundan çıkar)
ISLAK_MAHAL = {"soyunma": False, "dus": True, "wc": True}


def duvar_kurgusu(mevcut: bool, islak: bool):
    """Bir duvarın, MAHAL YÜZÜNDEN DIŞA doğru tam katman dizisi."""
    kaplama = KAPLAMA_ISLAK if islak else KAPLAMA_KURU
    karkas = KARKAS_MEVCUT if mevcut else KARKAS_BOLME
    return kaplama + karkas


def kaplama_t(ad):
    return KAPLAMA_T["islak" if ISLAK_MAHAL.get(ad) else "kuru"]


# Bitmiş mahal = karkas poligonu eksi kaplama kalınlığı
BITMIS = {n: P.ISLAK[BLOK][n].buffer(-kaplama_t(n), join_style=2)
          for n in MAHAL}
BITMIS = {n: (max(g.geoms, key=lambda q: q.area) if hasattr(g, "geoms") else g)
          for n, g in BITMIS.items()}
NET = BITMIS                                   # çizim ve etiketler bitmiş yüzü kullanır
NET_M2 = {n: round(g.area, 3) for n, g in BITMIS.items()}
KABA_M2 = {n: round(P.ISLAK[BLOK][n].area, 3) for n in MAHAL}
BOLME = P.ISLAK[BLOK].get("bolme")


def ceper_govdesi():
    """Bloğun çeper duvarları — her kenar için (kenar, mevcut mu, katmanlar).

    Mevcut bina çeperine oturan kenar ile salona bakan bölme, kenarın binanın
    DIŞ kabuğuna uzaklığından ayrılır; elle işaretlenmez.
    """
    tum = P.ISLAK[BLOK]["tum"]
    kab = _IC.buffer(0.06, join_style=2).buffer(-0.06, join_style=2)
    dis_kabuk = unary_union([g.exterior for g in
                             (kab.geoms if hasattr(kab, "geoms") else [kab])])
    parcalar = []
    c = list(tum.exterior.coords)
    for a, b in zip(c, c[1:]):
        L = math.dist(a, b)
        if L < 0.05: continue
        ux, uy = (b[0]-a[0])/L, (b[1]-a[1])/L
        nx, ny = -uy, ux
        if tum.contains(Point((a[0]+b[0])/2 + nx*0.02, (a[1]+b[1])/2 + ny*0.02)):
            nx, ny = -nx, -ny
        seg = LineString([a, b])
        mevcut = seg.interpolate(0.5, normalized=True).distance(dis_kabuk) < 0.06
        parcalar.append({"a": a, "b": b, "L": L, "mevcut": mevcut,
                         "n": (nx, ny), "seg": seg})
    return parcalar


CEPER = ceper_govdesi()


# ══════════════════════════ P-01  ÖLÇÜLÜ PLAN ═════════════════════════════════
KESIT_U = 0.55          # m — K1-K1 kesit düzleminin yerel u koordinatı
DETAY_UV = (0.08, 2.40)  # m — D-02 detay çağrısı: duşun zemin/duvar köşesi


def _kutu_uv(msp, u0, v0, w, d, kat, kapali=True):
    c = [(u0, v0), (u0+w, v0), (u0+w, v0+d), (u0, v0+d)]
    return _pl(msp, [xy(*q) for q in c], kat, kapali)


def _vitrifiye(msp):
    """Vitrifiye mahallin KENDİ çeperinden yerleşir; dünya koordinatı elle
    yazılmaz. Ölçüler gerçek ürün ölçüleridir (asma klozet 370×650,
    lavabo 500×420, duş teknesi 900×900)."""
    yer = {}
    # 107 WC — klozet arka duvarda, lavabo yan duvarda
    u0, v0, u1, v1 = ALT_UV["wc"]
    kw, kd = 0.37, 0.65
    ku = (u0+u1)/2 - kw/2
    kv = v1 - kd - 0.02
    _kutu_uv(msp, ku, kv, kw, kd, "M-SIHHI-CIHAZ")
    _kutu_uv(msp, ku+0.06, kv+0.06, kw-0.12, 0.20, "M-SIHHI-CIHAZ")   # rezervuar önü
    yer["WC-1"] = (ku+kw/2, kv+kd/2)
    lw, ld = 0.50, 0.42
    lu, lv = u0+0.04, v0+0.10
    _kutu_uv(msp, lu, lv, lw, ld, "M-SIHHI-CIHAZ")
    ce = xy(lu+lw/2, lv+ld/2)
    msp.add_ellipse((ce[0]*K, ce[1]*K),
                    major_axis=(0.17*K*DU[0], 0.17*K*DU[1]), ratio=0.70,
                    dxfattribs={"layer": "M-SIHHI-CIHAZ"})
    yer["LV-1"] = (lu+lw/2, lv+ld/2)
    # WC yer süzgeci
    su = (u0+u1)/2 + 0.30; sv = v0+0.30
    _suzgec(msp, su, sv); yer["SZ-WC"] = (su, sv)

    # 106 DUŞ — tekne mahalli dolduruyor, süzgeç merkezde
    u0, v0, u1, v1 = ALT_UV["dus"]
    _kutu_uv(msp, u0+0.03, v0+0.03, (u1-u0)-0.06, (v1-v0)-0.06, "M-SIHHI-CIHAZ")
    du, dv = (u0+u1)/2, v0 + (v1-v0)*0.40
    _suzgec(msp, du, dv); yer["SZ-DUS"] = (du, dv)
    # duş başlığı ve batarya izdüşümü (duvarda, +u yüzünde)
    yer["DU-1"] = (u1-0.14, (v0+v1)/2)
    bp = xy(*yer["DU-1"])
    msp.add_circle((bp[0]*K, bp[1]*K), 0.075*K, dxfattribs={"layer": "M-SIHHI-CIHAZ"})
    return yer


def _suzgec(msp, u, v, r=0.05):
    c = xy(u, v)
    msp.add_circle((c[0]*K, c[1]*K), r*K, dxfattribs={"layer": "M-SIHHI-PIS"})
    msp.add_circle((c[0]*K, c[1]*K), r*1.5*K, dxfattribs={"layer": "M-SIHHI-PIS"})
    for a in (0, 90):
        d = r*1.5
        _ln(msp, xy(u-d*math.cos(math.radians(a)), v-d*math.sin(math.radians(a))),
            xy(u+d*math.cos(math.radians(a)), v+d*math.sin(math.radians(a))),
            "M-SIHHI-PIS")


def _egim_oku(msp, u0, v0, u1, v1, metin="%1,5"):
    a = xy(u0, v0); b = xy(u1, v1)
    _ln(msp, a, b, "A-ZEMIN-YAZI")
    ang = math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))
    for s in (+1, -1):
        d = 0.10
        _ln(msp, b, (b[0]-d*math.cos(math.radians(ang+s*22)),
                     b[1]-d*math.sin(math.radians(ang+s*22))), "A-ZEMIN-YAZI")
    m = ((a[0]+b[0])/2, (a[1]+b[1])/2)
    _tx(msp, (m[0], m[1]+0.06), metin, 2.5, "A-ZEMIN-YAZI", hiza="ORTA", aci=ang)


DIKME_ARA = 0.40      # m — C profil aks aralığı (Knauf DC50 · MEGEP Tablo 1.2)


def _ic_bolme_eksenleri():
    """Alt mekânlar arasındaki bölme duvarlarının EKSEN doğruları.

    Her bölme BİR KEZ çizilmeli: iki komşu mahal de kendi yüzünü bildirirse
    karkas iki kez çizilir ve çizgiler üst üste biner.
    """
    adlar = list(MAHAL)
    out = []
    for i in range(len(adlar)):
        for j in range(i+1, len(adlar)):
            a, b = P.ISLAK[BLOK][adlar[i]], P.ISLAK[BLOK][adlar[j]]
            if a.distance(b) > BOLME_T*1.6: continue
            ort = a.exterior.intersection(b.buffer(BOLME_T*1.2))
            for g in (ort.geoms if hasattr(ort, "geoms") else [ort]):
                if getattr(g, "length", 0) < 0.15: continue
                c = list(g.coords)
                out.append({"a": c[0], "b": c[-1], "ic": adlar[i], "dis": adlar[j]})
    return out


IC_BOLME = _ic_bolme_eksenleri()


def _taraf(a, b, disa_normal):
    """duvar_kesiti'nin `taraf` işareti: +1 sol normal (-uy, ux)."""
    ux, uy = b[0]-a[0], b[1]-a[1]
    L = math.hypot(ux, uy) or 1.0
    return 1 if (-uy/L*disa_normal[0] + ux/L*disa_normal[1]) > 0 else -1


def duvarlari_ciz(msp, olcek):
    """Bütün duvarları KATMAN KATMAN çizer — üç aşama:

      1) çeper karkası — blok çeperinden DIŞA (mevcut 200 mm ya da D3 100 mm)
      2) iç bölme karkası — iki mahal arasında, bir kez
      3) her mahalin KAPLAMASI — mahal yüzünden İÇERİ

    Böylece planda duvarın içindeki levha, C dikme, karkas boşluğu ve taşyünü
    görünür; su yalıtımı ince katman kuralı gereği kendi kaleminde sürekli tek
    çizgi olarak okunur. Önceki hâlinde duvar tek bant + tek taramaydı.
    """
    nd = ndk = 0
    govde = []
    for c in CEPER:
        karkas = KARKAS_MEVCUT if c["mevcut"] else KARKAS_BOLME
        kal = sum(x["m"] for x in karkas)
        tr = _taraf(c["a"], c["b"], c["n"])
        # Köşelerin kapanması için kenar iki uçtan duvar kalınlığı kadar uzatılır;
        # uzatma yalnız GÖVDE sınırını kapatmak içindir, katman çizgileri
        # kendi kenarında kalır.
        t, k = MZ.duvar_kesiti(msp, c["a"], c["b"], karkas, olcek,
                               taraf=tr, dikme_ara=DIKME_ARA)
        nd += k
        govde.append(_bant(c["a"], c["b"], kal, tr, uzat=kal))
        if not c["mevcut"] and olcek <= 25: ndk += 1
    for b in IC_BOLME:
        ic = P.ISLAK[BLOK][b["ic"]]
        ux, uy = b["b"][0]-b["a"][0], b["b"][1]-b["a"][1]
        L = math.hypot(ux, uy) or 1.0
        nx, ny = -uy/L, ux/L
        m = ((b["a"][0]+b["b"][0])/2, (b["a"][1]+b["b"][1])/2)
        disa = -1 if ic.contains(Point(m[0]+nx*0.02, m[1]+ny*0.02)) else 1
        t, k = MZ.duvar_kesiti(msp, b["a"], b["b"], KARKAS_BOLME, olcek,
                               taraf=disa, dikme_ara=DIKME_ARA)
        nd += k
        govde.append(_bant(b["a"], b["b"], sum(x["m"] for x in KARKAS_BOLME),
                           disa, uzat=0.0))
        if olcek <= 25: ndk += 1
    for ad in MAHAL:
        g = P.ISLAK[BLOK][ad]
        kap = list(reversed(KAPLAMA_ISLAK if ISLAK_MAHAL[ad] else KAPLAMA_KURU))
        c = list(g.exterior.coords)
        for a, b in zip(c, c[1:]):
            L = math.dist(a, b)
            if L < 0.05: continue
            nx, ny = -(b[1]-a[1])/L, (b[0]-a[0])/L
            ice = 1 if g.contains(Point((a[0]+b[0])/2 + nx*0.02,
                                        (a[1]+b[1])/2 + ny*0.02)) else -1
            MZ.duvar_kesiti(msp, a, b, kap, olcek, taraf=ice)
            nd += len(kap)
    # DIŞ ÇEPER: bütün duvar gövdelerinin birleşimi, kesilen eleman kaleminde
    # tek sürekli çizgi. Kenarlar tek tek çizildiği için köşeler aksi hâlde
    # açık kalır ve duvar "bitmemiş" görünür.
    if govde:
        # köşe kapatma uzatması bloğun dışına taşmasın
        sinir = P.ISLAK[BLOK]["tum"].buffer(
            max(sum(x["m"] for x in KARKAS_MEVCUT),
                sum(x["m"] for x in KARKAS_BOLME)) + 0.004, join_style=2)
        u = unary_union(govde).intersection(sinir)
        for g in (u.geoms if hasattr(u, "geoms") else [u]):
            # Birleşim köşelerde 0,1 mm'lik kırıntı düğümler bırakır; çizime
            # girmeden önce temizlenir (sıfır uzunluklu parça kalmaz).
            _pl(msp, _sadelestir(list(g.exterior.coords)[:-1]), MZ.KAT_CEPER)
            for r in g.interiors:
                _pl(msp, _sadelestir(list(r.coords)[:-1]), MZ.KAT_CEPER)
    return nd, ndk


def _sadelestir(pts, esik=0.0015):
    """Ardışık iki düğüm `esik`ten yakınsa birini atar (m)."""
    out = []
    for q in pts:
        if not out or math.dist(q, out[-1]) > esik: out.append(q)
    while len(out) > 3 and math.dist(out[0], out[-1]) <= esik: out.pop()
    return out


def _bant(a, b, kal, taraf, uzat=0.0):
    """a→b kenarının `taraf` yönünde `kal` kalınlığında bandı (gövde sınırı)."""
    L = math.dist(a, b) or 1.0
    ux, uy = (b[0]-a[0])/L, (b[1]-a[1])/L
    nx, ny = -uy*taraf, ux*taraf
    a2 = (a[0]-ux*uzat, a[1]-uy*uzat); b2 = (b[0]+ux*uzat, b[1]+uy*uzat)
    return Polygon([a2, b2, (b2[0]+nx*kal, b2[1]+ny*kal), (a2[0]+nx*kal, a2[1]+ny*kal)])


def plan(msp):
    n = {"duvar": 0, "kapi": 0, "olcu": 0, "dikme": 0}
    # 1) DUVARLAR — tek bant değil, KATMAN KATMAN (levha · dikme · boşluk ·
    #    yalıtım · kaplama); ayrıntı için duvarlari_ciz()
    n["duvar"], n["dikme"] = duvarlari_ciz(msp, OLCEK)
    # 2) bitmiş mahal yüzü
    for ad, g in BITMIS.items():
        sekil(msp, g, "A-ZEMIN-SINIR")
    # 3) kapılar — kod, kanat ve açılım
    for kod, (pt, gen, aci) in P.KAPI_GEOM.items():
        if not P.ISLAK[BLOK]["tum"].buffer(0.35).contains(Point(*pt)): continue
        a = math.radians(aci) + (math.pi if kod in P.KAPI_DISA else 0.0)
        dx, dy = math.cos(a)*gen/2, math.sin(a)*gen/2
        p1 = (pt[0]-dx, pt[1]-dy); p2 = (pt[0]+dx, pt[1]+dy)
        nx, ny = math.cos(a-math.pi/2), math.sin(a-math.pi/2)
        t = BOLME_T/2 + 0.02
        # söve (kapı boşluğunun iki kenarı) — boşluğun karşıdan karşıya çizgisi YOK
        for q in (p1, p2):
            _ln(msp, (q[0]-nx*t, q[1]-ny*t), (q[0]+nx*t, q[1]+ny*t), "A-KAPI")
        # kanat (40 mm) ve açılım yayı — menteşe p1'de
        uc = (p1[0]+nx*gen, p1[1]+ny*gen)
        _pl(msp, [p1, uc, (uc[0]-math.cos(a)*0.04, uc[1]-math.sin(a)*0.04),
                  (p1[0]-math.cos(a)*0.04, p1[1]-math.sin(a)*0.04)], "A-KAPI")
        msp.add_arc((p1[0]*K, p1[1]*K), gen*K,
                    math.degrees(math.atan2(ny, nx)),
                    math.degrees(math.atan2(p2[1]-p1[1], p2[0]-p1[0])),
                    dxfattribs={"layer": "A-KAPI"})
        # kapı kodu balonu
        bu, bv = uv(pt)
        bp = xy(bu, bv)
        msp.add_circle((bp[0]*K, bp[1]*K), 0.115*OLCEK/1000.0*K*2.4,
                       dxfattribs={"layer": "A-MAHAL"})
        _tx(msp, bp, kod, 2.5, "A-MAHAL", hiza="ORTA")
        n["kapi"] += 1
    # 4) vitrifiye + süzgeç + eğim
    yer = _vitrifiye(msp)
    du = ALT_UV["dus"]; szd = yer["SZ-DUS"]
    _egim_oku(msp, du[0]+0.18, du[3]-0.18, szd[0]-0.10, szd[1]+0.12)
    wc = ALT_UV["wc"]; szw = yer["SZ-WC"]
    _egim_oku(msp, wc[2]-0.20, wc[3]-0.20, szw[0]+0.10, szw[1]+0.12)
    # 5) sabit mobilya
    for ad, g, tip in P.MOBILYA:
        if not P.ISLAK[BLOK]["tum"].buffer(0.05).intersects(g): continue
        sekil(msp, g, "A-MOBILYA")
        q = g.representative_point()
        _tx(msp, (q.x, q.y), ad, 2.0, "A-MOBILYA", hiza="ORTA")
    # 6) mahal etiketleri — no · ad · net alan · zemin/tavan kodu · kot
    for ad in ("soyunma", "dus", "wc"):
        no = MAHAL[ad]
        bilgi = P._MAHAL_BILGI[no]
        u0, v0, u1, v1 = ALT_UV[ad]
        etk = xy(u0+0.09, v1-0.12)
        # mahal numarası balonu
        bc = xy(u0+0.20, v1-0.20)
        msp.add_circle((bc[0]*K, bc[1]*K), 0.17*K, dxfattribs={"layer": "A-MAHAL"})
        _tx(msp, bc, no, 2.5, "A-MAHAL", hiza="ORTA")
        _etiket(msp, xy(u0+0.44, v1-0.13), [
            bilgi[1].upper(),
            f"{NET_M2[ad]:.2f} m²".replace(".", ",") + f"   {bilgi[3]} / {bilgi[6]}",
        ], OLCEK, "A-YAZI", "SOL", 2.2)
        kot = (P.ZEMIN_TABAN.get(bilgi[3], 0.0)
               + sum(k[1] for k in
                     next(z for z in P.ZEMIN_TIPLERI if z[0] == bilgi[3])[2])/1000.0)
        _kot_isareti(msp, xy(u0+0.50, v0+0.22), kot, OLCEK)
    # 7) ölçü zincirleri — bloğun KENDİ eksenlerinde
    off = 0.62
    # v ekseni (uzun): soyunma / duş sınırları
    v_nok = [0.0, ALT_UV["soyunma"][3], ALT_UV["dus"][1], L_BLOK]
    v_nok = sorted(set(round(t, 3) for t in v_nok))
    n["olcu"] += _zincir(msp, [xy(-off, t) for t in v_nok], -off*0.55)
    # u ekseni (kısa): duş / WC bölmesi
    u_nok = sorted(set(round(t, 3) for t in
                       [0.0, ALT_UV["dus"][2], ALT_UV["wc"][0], W_BLOK]))
    n["olcu"] += _zincir(msp, [xy(t, L_BLOK+off) for t in u_nok], off*0.55)
    # kapı boşlukları (soyunma/duş duvarı)
    kapi_u = []
    for kod in ("K07", "K05"):
        if kod not in P.KAPI_GEOM: continue
        pt, gen, aci = P.KAPI_GEOM[kod]
        cu, cv = uv(pt)
        kapi_u += [round(cu-gen/2, 3), round(cu+gen/2, 3)]
    if kapi_u:
        nok = sorted(set([0.0] + kapi_u + [W_BLOK]))
        n["olcu"] += _zincir(msp, [xy(t, ALT_UV["dus"][1]-off*0.5) for t in nok],
                             -off*0.30, toplam=False)
    # 8) kesit işareti K1-K1
    _kesit_isareti(msp)
    # 9) detay çağrısı D-02
    _detay_cagri(msp, DETAY_UV, "D-02", "P-05")
    return n


def _kesit_isareti(msp):
    """K1-K1 kesit düzlemi. Kesit çizgisi uçlarda gösterilir (tam boy çizilmez),
    bakış oku kesit düzlemine DİK ve +u yönündedir (ISO 128-40)."""
    u = KESIT_U
    pay = 0.55
    for yon, v0 in ((-1, -0.10), (+1, L_BLOK+0.10)):
        a = xy(u, v0)
        b = xy(u, v0 + yon*pay)
        _ln(msp, a, b, "A-KESIT-HAT")                     # kesit düzlemi ucu
        # bakış oku: +u yönünde, kesit çizgisinin ucundan
        o0 = b
        o1 = xy(u+0.38, uv(b)[1])
        _ln(msp, o0, o1, "G-KESIT-ISARET")
        ang = math.degrees(math.atan2(o1[1]-o0[1], o1[0]-o0[0]))
        for sgn in (+1, -1):
            _ln(msp, o1, (o1[0]-0.14*math.cos(math.radians(ang+sgn*18)),
                          o1[1]-0.14*math.sin(math.radians(ang+sgn*18))),
                "G-KESIT-ISARET")
        # pafta referanslı balon
        bal = xy(u, v0 + yon*(pay+0.42))
        msp.add_circle((bal[0]*K, bal[1]*K), 0.30*K,
                       dxfattribs={"layer": "G-KESIT-ISARET"})
        _ln(msp, xy(u-0.30, uv(bal)[1]), xy(u+0.30, uv(bal)[1]), "G-KESIT-ISARET")
        _tx(msp, xy(u, uv(bal)[1]+0.13), "K1", 2.5, "G-KESIT-ISARET", hiza="ORTA")
        _tx(msp, xy(u, uv(bal)[1]-0.19), "P-03", 2.0, "G-KESIT-ISARET", hiza="ORTA")


_BALON_YER = []


def _balon(msp, p, metin, r=0.14, kat="M-YAZI", olcek=OLCEK, ayir=True):
    """Numaralı balon. `ayir` ile daha önce konmuş balonlarla çakışma çözülür —
    kesitte tavan içi tesisat kotları birbirine çok yakın olduğu için şart."""
    x, y = p
    if ayir:
        for _ in range(60):
            if all(math.hypot(x-bx, y-by) > r+br+0.03 for bx, by, br in _BALON_YER):
                break
            x += r*2.1
    msp.add_circle((x*K, y*K), r*K, dxfattribs={"layer": kat})
    _tx(msp, (x, y), metin, 2.2, kat, hiza="ORTA", olcek=olcek, telafi=False)
    _BALON_YER.append((x, y, r))
    return (x, y)


def _detay_cagri(msp, uv_p, detay, pafta_no, r=0.26):
    c = xy(*uv_p)
    msp.add_circle((c[0]*K, c[1]*K), r*K,
                   dxfattribs={"layer": "A-DETAY-CAGRI", "linetype": "DASHED"})
    # kılavuz SOLA (bloğun dışına) çıkar; mahal balonlarıyla çakışmaz
    uc = xy(uv_p[0]-r*0.71, uv_p[1]+r*0.71)
    kir = xy(uv_p[0]-r*0.71-0.55, uv_p[1]+r*0.71+0.55)
    _ln(msp, uc, kir, "A-DETAY-CAGRI")
    bal = xy(uv_p[0]-r*0.71-0.55-0.32, uv_p[1]+r*0.71+0.55)
    msp.add_circle((bal[0]*K, bal[1]*K), 0.30*K, dxfattribs={"layer": "A-DETAY-CAGRI"})
    _ln(msp, (bal[0]-0.30, bal[1]), (bal[0]+0.30, bal[1]), "A-DETAY-CAGRI")
    _tx(msp, (bal[0], bal[1]+0.12), detay, 2.5, "A-DETAY-CAGRI", hiza="ORTA")
    _tx(msp, (bal[0], bal[1]-0.20), pafta_no, 2.0, "A-DETAY-CAGRI", hiza="ORTA")


# ══════════════════════════ PAFTA KURULUMU ════════════════════════════════════
REVIZYONLAR = (
 ("A", "13.09.2026", "İlk yayın — ön tasarım"),
 ("B", "17.09.2026", "Mühendis geri bildirimi işlendi"),
 ("C", "18.09.2026", "Geometri ölçülmüş rölöveye taşındı (ESAT-FINAL.dwg)"),
 ("D", "18.09.2026", "Pilot bölge: ölçülü plan · tavan · kesit · görünüş · detay"),
)

PAFTA_SONRAKI = {a: b for a, b in zip(SIRA, SIRA[1:])}

# Paftada fiilen kullanılan malzemelerin gösterim anahtarı — okuyucu hangi
# dokunun ne olduğunu paftadan öğrenir, tahmin etmez.
def _malzeme_lejanti(*anahtarlar):
    return [[MZ.bilgi(a)["ad"], _gosterim_metni(a)] for a in anahtarlar]


def _gosterim_metni(a):
    m = MZ.bilgi(a)
    if m["yontem"] == "desen":
        return f"{m['desen']} taraması · kâğıtta {m['kagit']:.1f} mm aralık".replace(".", ",")
    if m["yontem"] == "ozel":
        return {"su_yalitimi": "dolu/boş değişen blok (MEGEP Şekil 2.44)",
                "c_profil": "gerçek C kesiti, aks aralığı 400 mm",
                "seramik": "gerçek karo boyunda derz çizgisi",
                "yalitim_isi": "sürekli zikzak (MEGEP Şekil 2.43)",
                "tugla_sira": "gerçek sıra yüksekliği 85 mm + derz"}.get(m["ozel"], "özel")
    return "tarama yok — yalnız katman çizgisi"


MALZEME_LEJANTI = {
 "P-01": _malzeme_lejanti("tugla", "alcipan", "dikme", "yalitim_isi",
                          "yalitim_su", "seramik"),
 "P-02": [],
 "P-03": _malzeme_lejanti("betonarme", "sap", "yalitim_su", "seramik"),
 "P-04": _malzeme_lejanti("seramik", "yalitim_su"),
 "P-05": _malzeme_lejanti("tugla", "sap", "yalitim_su", "bant", "seramik", "harc"),
}

NOTLAR = {
 "P-01": [
  "Geometri ölçülmüş rölöveden alınmıştır (ESAT-FINAL.dwg, TRIMODE).",
  "Mahal alanları BİTMİŞ YÜZ net alanıdır: karkas yüzünden kaplama\n  kalınlığı (ıslakta 16 mm, kuruda 6 mm) düşülmüştür. Kaba yapı\n  (karkas) alanları malzeme listesindedir.",
  "Ölçüler bloğun kendi doğrultusundadır (dünya eksenine izdüşüm değil).",
  "Duş ve WC zemininde süzgeğe doğru %1,5 eğim verilecektir.",
  "Duvarlar KATMAN KATMAN çizilmiştir: alçı levha · C dikme @400 mm ·\n"
  "  karkas boşluğu + taşyünü · su yalıtımı · yapıştırıcı · seramik.",
  "Kapı kodları kapı cetveliyle (K03·K05·K07) aynı kaynaktan üretilir.",
 ],
 "P-02": [
  "Tavan kotları bitmiş zemin kotundan ölçülür.",
  "Duş ve WC üzerinde T3 (H2 su itici alçıpan), soyunmada T4 kullanılır.",
  "Her ıslak hacimde 300×300 mm menteşeli revizyon kapağı bulunur.",
  "Armatür ve valf konumları koordinasyon kesiti P-03 ile çakışma kontrolünden geçmiştir.",
 ],
 "P-03": [
  "Kesit düzlemi K1-K1; bakış yönü plan üzerinde gösterilmiştir.",
  "Tavan içi tesisat kotları tek kaynaktan (TAVAN_KATMAN) türetilir.",
  "Kesilen eleman 0,70 mm · görünen 0,35 mm · arkada kalan 0,18 mm (ISO 128-2).",
  "Mevcut döşeme kotu ve kalınlığı VARSAYIMDIR — söküm sonrası ölçülecektir.",
 ],
 "P-04": [
  "Seramik 300×600 mm rektifiye, düşey derz şaşırtmalı (yarım kaydırma).",
  "Su yalıtımı duş kabininde +2,00 m'ye kadar döner (D-02 detayına bakınız).",
  "Batarya ve duş başlığı kotları bitmiş zeminden ölçülür.",
  "Derz ızgarası gerçek karo boyutundan üretilmiştir; dekoratif değildir.",
 ],
 "P-05": [
  "Katman kalınlıkları Z4 zemin ve D5 duvar tip tablosundan gelir.",
  "Su yalıtımı zemin-duvar köşesinde 120 mm elastik bantla sürekliliği sağlar.",
  "Detay 1:5 ölçeğindedir; ölçü alınmaz, yazılı ölçüler geçerlidir.",
 ],
}


DONEN_PAFTA = ("P-01", "P-02")      # görüntü penceresi bloğa hizalanan paftalar
VP_GEN = 232.0                      # mm — görüntü penceresi genişliği (A2)


def _pafta(doc, no, olcek, merkez, tablo_fn=None):
    ad, disiplin, olc = PAFTALAR[no]
    pf = Pafta(doc, no, ad, disiplin, boy=BOY, proje=PROJE_BILGI,
               ust_ad=f"PİLOT BÖLGE — {BLOK} ISLAK BLOK (105·106·107)")
    pf.cerceve()
    pf.antet(olcek=f"1:{olcek}", tarih=P.TARIH, rev="D", durum="ÖN TASARIM",
             muellif=MUELLIF, sicil=SICIL, cizen="CC", kontrol="—", onay="—",
             birim="milimetre (mm)", revizyonlar=REVIZYONLAR,
             sonraki=PAFTA_SONRAKI.get(no, ""))
    x = pf.x0 + PF.ZON_BANT + 4
    pf.gorunum(merkez=(merkez[0]*K, merkez[1]*K), olcek=olcek,
               x=x, w=VP_GEN, donme=-ACI_DER if no in DONEN_PAFTA else 0.0)
    pf.olcek_cubugu(olcek, uzunluk_m=0.5 if olcek <= 5 else 2, bolum=4)
    if no in DONEN_PAFTA:
        pf.kuzey(aci=-ACI_DER)
    pf.durum_damgasi()
    pf.dikkat_notu()
    # ORTA SÜTUN — malzeme / ekipman listesi ve lejant
    mx = x + VP_GEN + 8
    mg = pf.ax - 6 - mx
    y = pf.baslik(mx, pf._ic[3]-6 if hasattr(pf, "_ic") else pf.y1-6,
                  "MALZEME VE EKİPMAN LİSTESİ") if tablo_fn else \
        (pf._ic[3]-6 if hasattr(pf, "_ic") else pf.y1-6)
    if tablo_fn:
        y = tablo_fn(pf, mx, y, mg)
    # SAĞ SÜTUN — lejant + notlar
    sx, sy, sw = pf.sag()
    kullanilan = {e.dxf.layer for e in doc.modelspace()}
    gorunur = [(l[0], l[4]) for l in X.KATMANLAR if l[0] in kullanilan
               and not l[0].startswith(("G-CERCEVE", "G-ANTET", "G-PAFTA", "G-VIEWPORT"))]
    sy2 = pf.kalem_lejanti(y=sy)
    sy2 = pf.lejant(gorunur[:18], y=sy2-2)
    if MALZEME_LEJANTI.get(no):
        sy2 = pf.tablo(["MALZEME", "GÖSTERİM"], MALZEME_LEJANTI[no],
                       [52, 74], x=sx, y=sy2-4, baslik="MALZEME GÖSTERİMİ")
    pf.notlar(NOTLAR[no], y=sy2-2)
    return pf


def _tablo(pf, x, y, gen, basliklar, satirlar, sutunlar, baslik=None):
    return pf.tablo(basliklar, satirlar, sutunlar, x=x, y=y, baslik=baslik)


# ── pafta bazlı malzeme listeleri (hepsi veri modelinden) ────────────────────
def _liste_plan(pf, x, y, gen):
    sat = []
    for ad in ("soyunma", "dus", "wc"):
        no = MAHAL[ad]; b = P._MAHAL_BILGI[no]
        sat.append([no, b[1], f"{NET_M2[ad]:.2f}".replace(".", ","),
                    f"{KABA_M2[ad]:.2f}".replace(".", ","), b[3], b[6]])
    y = pf.tablo(["NO", "MAHAL", "BİTMİŞ m²", "KABA m²", "ZEMİN", "TAVAN"], sat,
                 [11, 41, 22, 20, 16, 16], x=x, y=y, baslik="MAHAL LİSTESİ")
    kap = []
    for kod in ("K03", "K05", "K07"):
        k = next(t for t in P.KAPI_LISTESI if t[0] == kod)
        kap.append([kod, k[2], f"{k[3]}×{k[4]}", k[5]])
    y = pf.tablo(["KOD", "MAHAL", "mm", "TİP"], kap, [14, 44, 26, 56],
                 x=x, y=y-6, baslik="KAPI LİSTESİ (bu bölge)")
    vit = [["WC-1", "Asma klozet + gömme rezervuar", "370×650"],
           ["LV-1", "Lavabo + batarya", "500×420"],
           ["DU-1", "Duş bataryası + tepe duşu", "—"],
           ["SZ-1", "Sifonlu yer süzgeci Ø100, paslanmaz", "150×150"]]
    y = pf.tablo(["KOD", "TANIM", "mm"], vit, [18, 84, 30], x=x, y=y-6,
                 baslik="VİTRİFİYE VE ARMATÜR")
    return y
# ══════════════════════════ ÖNİZLEME ══════════════════════════════════════════
def onizleme(dosyalar, cikti=None, dpi=170):
    """Her paftayı kendi DXF'inden PDF'e basar ve PNG önizleme üretir.

    §11: "Her çıktı turunda dosyayı YENİDEN AÇ, paftaları PDF/PNG üret ve
    görsel olarak incele." Bu yüzden diskteki dosya tekrar okunur, bellekteki
    belge kullanılmaz.
    """
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.addons.drawing import config as _C
    import ezdxf.bbox as _bbox
    cikti = Path(cikti or KOK/"output"/"Gym_Pilot_Paftalar.pdf")
    W, H = PF.KAGIT[BOY]
    cfg = _C.Configuration(background_policy=_C.BackgroundPolicy.WHITE,
                           color_policy=_C.ColorPolicy.COLOR,
                           circle_approximation_count=160, hatching_timeout=90.0)
    png = []
    with PdfPages(cikti) as pdf:
        for no, yol in dosyalar:
            doc = ezdxf.readfile(yol)           # diskten YENİDEN oku
            lay = next(l for l in doc.layouts if l.name != "Model")
            fig = plt.figure(figsize=(W/25.4, H/25.4))
            ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
            Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg,
                     bbox_cache=_bbox.Cache()).draw_layout(lay, finalize=True)
            ax.set_xlim(0, W); ax.set_ylim(0, H)
            ax.set_aspect("equal", adjustable="box")
            fig.set_size_inches(W/25.4, H/25.4)
            pdf.savefig(fig, facecolor="white")
            pp = KOK/"work"/"pilot"/f"{no}.png"
            pp.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(pp, dpi=dpi, facecolor="white")
            png.append(pp)
            plt.close(fig)
    return cikti, png


# ══════════════════════════ ÜRETİM ════════════════════════════════════════════
def _belge(no):
    doc = X.yeni_belge(f"{no}.dxf")
    X.bloklari_kur(doc)
    return doc


def uret_pafta(no):
    """Tek paftayı bağımsız bir DXF olarak üretir."""
    global _DONME
    _DONME = ACI_DER if no in DONEN_PAFTA else 0.0
    _BALON_YER.clear()
    doc = _belge(no)
    msp = doc.modelspace()
    olcek = PAFTALAR[no][2]
    if no == "P-01":
        plan(msp); merkez = _merkez_blok(); tablo = _liste_plan
    elif no == "P-02":
        tavan(msp); merkez = _merkez_blok(); tablo = _liste_tavan
    elif no == "P-03":
        merkez = kesit(msp); tablo = _liste_kesit
    elif no == "P-04":
        merkez = gorunus(msp); tablo = _liste_gorunus
    else:
        merkez = detay(msp); tablo = _liste_detay
    _pafta(doc, no, olcek, merkez, tablo)
    if "Layout1" in doc.layouts: doc.layouts.delete("Layout1")
    doc.set_modelspace_vport(height=6000, center=(merkez[0]*K, merkez[1]*K))
    yol = CIK/f"{no}_{PAFTALAR[no][0].split(' — ')[0].replace(' ', '_').replace('/', '-')}.dxf"
    doc.saveas(yol)
    return yol


def _merkez_blok():
    c = P.ISLAK[BLOK]["tum"].centroid
    return (c.x, c.y)


def uret(paftalar=None):
    dosya = []
    for no in (paftalar or SIRA):
        y = uret_pafta(no)
        doc = ezdxf.readfile(y)          # §11: yazdıktan sonra YENİDEN aç
        n = len(list(doc.modelspace()))
        print(f"  → cad/pilot/{y.name:54s} {n:4d} nesne · {y.stat().st_size/1024:6.0f} KB")
        dosya.append((no, y))
    return dosya


# ══════════════════════════ P-02  TAVAN PLANI (RCP) ═══════════════════════════
TAVAN_MAHAL = {"soyunma": "T4", "dus": "T3", "wc": "T3"}
TASIYICI_ARA = 0.40      # m — TU27 taşıyıcı profil aralığı
ANA_ARA = 0.90           # m — TC47 ana profil / askı aralığı


def _armatur(msp, u, v, tip="downlight", d=0.16):
    c = xy(u, v)
    if tip == "downlight":
        msp.add_circle((c[0]*K, c[1]*K), d/2*K, dxfattribs={"layer": "E-AYD-DOWNLIGHT"})
        msp.add_circle((c[0]*K, c[1]*K), d/2*0.55*K, dxfattribs={"layer": "E-AYD-DOWNLIGHT"})
    else:
        _kutu_uv(msp, u-d/2, v-d/2, d, d, "E-AYD-ACIL")
        _ln(msp, xy(u-d/2, v-d/2), xy(u+d/2, v+d/2), "E-AYD-ACIL")


def _valf(msp, u, v, cap_mm, kod):
    c = xy(u, v); r = max(cap_mm, 100)/2000.0
    msp.add_circle((c[0]*K, c[1]*K), r*K, dxfattribs={"layer": "M-HAVA-MENFEZ"})
    for a in (45, 135):
        _ln(msp, xy(u-r*math.cos(math.radians(a)), v-r*math.sin(math.radians(a))),
            xy(u+r*math.cos(math.radians(a)), v+r*math.sin(math.radians(a))),
            "M-HAVA-MENFEZ")
    _tx(msp, xy(u, v-r-0.10), f"{kod} Ø{cap_mm}", 2.0, "M-YAZI", hiza="ORTA")


def tavan(msp):
    n = {"tasiyici": 0, "armatur": 0, "kapak": 0}
    # Tavan planında duvarlar ARKADA KALAN elemandır: doku ve dikme çizilmez,
    # yalnız gövde sınırı ince çizgiyle gösterilir (ISO 128-2 çizgi hiyerarşisi).
    for c in CEPER:
        karkas = KARKAS_MEVCUT if c["mevcut"] else KARKAS_BOLME
        kal = sum(x["m"] for x in karkas)
        sekil(msp, _bant(c["a"], c["b"], kal,
                         _taraf(c["a"], c["b"], c["n"]), uzat=kal),
              "A-KESIT-ARKA")
    for b in IC_BOLME:
        ic = P.ISLAK[BLOK][b["ic"]]
        L = math.dist(b["a"], b["b"]) or 1.0
        nx, ny = -(b["b"][1]-b["a"][1])/L, (b["b"][0]-b["a"][0])/L
        m = ((b["a"][0]+b["b"][0])/2, (b["a"][1]+b["b"][1])/2)
        disa = -1 if ic.contains(Point(m[0]+nx*0.02, m[1]+ny*0.02)) else 1
        sekil(msp, _bant(b["a"], b["b"], sum(x["m"] for x in KARKAS_BOLME), disa),
              "A-KESIT-ARKA")
    for ad in ("soyunma", "dus", "wc"):
        g = NET[ad]
        sekil(msp, g, "A-TAVAN-SINIR")
        u0, v0, u1, v1 = ALT_UV[ad]
        tip = TAVAN_MAHAL[ad]
        kot = P.TAVAN_KOT[tip]
        # taşıyıcı profil ızgarası — gerçek aralıkla, dekoratif değil
        t = u0 + TASIYICI_ARA
        while t < u1 - 0.02:
            a, b = xy(t, v0+0.02), xy(t, v1-0.02)
            if g.buffer(-0.01).intersects(LineString([a, b])):
                seg = g.buffer(-0.01).intersection(LineString([a, b]))
                for q in (seg.geoms if hasattr(seg, "geoms") else [seg]):
                    if getattr(q, "length", 0) > 0.05:
                        _ln(msp, q.coords[0], q.coords[-1], "A-TAVAN-SINIR")
                        n["tasiyici"] += 1
            t += TASIYICI_ARA
        # armatür + valf + revizyon kapağı
        cu, cv = (u0+u1)/2, (v0+v1)/2
        _armatur(msp, cu, cv); n["armatur"] += 1
        if ad in ("dus", "wc"):
            kod, cap = ("V1", 80) if ad == "dus" else ("V2", 40)
            _valf(msp, cu, v1-0.32, cap, kod)
            _kutu_uv(msp, u1-0.44, v0+0.12, 0.30, 0.30, "A-TAVAN-KAPAK")
            _tx(msp, xy(u1-0.29, v0+0.05), "R", 2.0, "A-TAVAN-KAPAK", hiza="ORTA")
            n["kapak"] += 1
        else:
            _armatur(msp, cu, v0+0.40, "acil"); n["armatur"] += 1
            _kutu_uv(msp, u1-0.44, v0+0.12, 0.30, 0.30, "A-TAVAN-KAPAK")
            n["kapak"] += 1
        # tavan tipi ve kotu
        _etiket(msp, xy(u0+0.09, v1-0.13),
                [f"{tip}   {kot:+.3f}".replace(".", ","),
                 f"{P._MAHAL_BILGI[MAHAL[ad]][1]}"],
                OLCEK, "A-TAVAN-YAZI", "SOL", 2.2)
    # ölçü: armatür eksenleri (v) ve taşıyıcı ilk aks (u)
    off = 0.62
    v_nok = sorted(set(round(t, 3) for t in
                       [0.0, (ALT_UV['soyunma'][1]+ALT_UV['soyunma'][3])/2,
                        ALT_UV['soyunma'][3], (ALT_UV['dus'][1]+ALT_UV['dus'][3])/2,
                        L_BLOK]))
    n["olcu"] = _zincir(msp, [xy(-off, t) for t in v_nok], -off*0.55)
    u_nok = sorted(set(round(t, 3) for t in
                       [0.0, (ALT_UV['dus'][0]+ALT_UV['dus'][2])/2, ALT_UV['dus'][2],
                        (ALT_UV['wc'][0]+ALT_UV['wc'][2])/2, W_BLOK]))
    n["olcu"] += _zincir(msp, [xy(t, L_BLOK+off) for t in u_nok], off*0.55)
    return n


def _liste_tavan(pf, x, y, gen):
    sat = []
    for ad in ("soyunma", "dus", "wc"):
        tip = TAVAN_MAHAL[ad]
        t = next(q for q in P.TAVAN_TIPLERI if q[0] == tip)
        bos = P.KOT_YAPISAL_TAVAN - t[2]
        sat.append([MAHAL[ad], P._MAHAL_BILGI[MAHAL[ad]][1], tip,
                    f"{t[2]:.2f}".replace(".", ","), f"{bos*1000:.0f}"])
    y = pf.tablo(["NO", "MAHAL", "TİP", "KOT m", "BOŞLUK mm"], sat,
                 [12, 46, 14, 20, 26], x=x, y=y, baslik="ASMA TAVAN")
    kat = []
    for tip in ("T4", "T3"):
        t = next(q for q in P.TAVAN_TIPLERI if q[0] == tip)
        for i, k in enumerate(t[3]):
            kat.append([tip if i == 0 else "", k])
    y = pf.tablo(["TİP", "KATMAN VE İMALAT"], kat, [14, 104], x=x, y=y-6,
                 baslik="TAVAN KATMANLARI")
    cih = [["L-1", "IP44 downlight 18 W / 1800 lm", "1 / mahal"],
           ["V1", "Egzoz valfi Ø80 — duş", "80 m³/h"],
           ["V2", "Egzoz valfi Ø40 — WC", "40 m³/h"],
           ["R", "Revizyon kapağı 300×300 menteşeli", "1 / mahal"],
           ["S1", "Hareket sensörü — ıslak blok", "1"]]
    y = pf.tablo(["KOD", "CİHAZ", "ADET/DEBİ"], cih, [16, 72, 30], x=x, y=y-6,
                 baslik="TAVAN CİHAZLARI")
    return y


# ══════════════════════════ P-03  KOORDİNASYON KESİTİ ═════════════════════════
# Kesit yerel (v, z) düzleminde kurulur: v = bloğun uzun ekseni, z = kot.
# Bütün kotlar ve katman kalınlıkları proj.py'deki tip tablolarından gelir.
ZEMIN_MAHAL = {"soyunma": "Z5", "dus": "Z4", "wc": "Z4"}
DOSEME_KALINLIK = 0.18          # m — VARSAYIM: mevcut betonarme döşeme
KOT_YAPISAL = P.KOT_YAPISAL_TAVAN


def _zemin_katmanlari(zt):
    """(taban_kot, [(ad, z_alt, z_ust, tur)]) — Z tipi tablosundan."""
    z = next(q for q in P.ZEMIN_TIPLERI if q[0] == zt)
    taban = P.ZEMIN_TABAN[zt]
    kat, alt = [], taban
    for ad, mm, tur in z[2]:
        if mm <= 0: continue
        kat.append((ad, alt, alt+mm/1000.0, tur))
        alt += mm/1000.0
    return taban, kat, alt


# Zemin tip tablosundaki tür kodları → malzeme kütüphanesi sınıfı
TUR_MALZEME = {"beton": "betonarme", "sap": "sap", "yalitim": "yalitim_su",
               "seramik": "seramik"}
TUR_KATMAN = {"beton": "A-KESIT-YAPISAL", "sap": "A-KATMAN-CIZGI",
              "yalitim": "A-KATMAN-YALITIM", "seramik": "A-KESIT-KESILEN"}
# ANSI serisi 0,125 birim aralıklıdır; AR-CONC çok daha geniş adımlıdır
# (yaklaşık 12 birim). Ortak ölçek kullanılırsa beton taraması tek bir uzun
# çizgiye dönüşüp paftayı boydan boya keser — bu yüzden desen başına katsayı.
TUR_DESEN = {"beton": ("AR-CONC", 2.4), "sap": ("ANSI31", 1.0),
             "yalitim": ("SOLID", 0), "seramik": ("ANSI37", 0.8)}


def _katman_bandi(msp, v0, v1, z0, z1, tur, kat=None, olcek=OLCEK, malzeme=None):
    """Kesitte yatay bir katman bandı — gösterimi malzeme kütüphanesi seçer.

    Kalınlığı kâğıtta 0,45 mm'nin altında kalan katman (su yalıtımı gibi)
    ekseninde tek çizgiye iner; tarama sıklığı desen tanımından hesaplanır.
    """
    m = malzeme or TUR_MALZEME.get(tur, "bosalan")
    q = Polygon([(v0, z0), (v1, z0), (v1, z1), (v0, z1)])
    return MZ.katman_ciz(msp, q, m, olcek, u_yon=(1.0, 0.0),
                         ceper=(kat == "A-KESIT-KESILEN"))


def kesit(msp):
    n = {"katman": 0, "tesisat": 0}
    sv, dv = ALT_UV["soyunma"], ALT_UV["dus"]
    v_b = 0.0                          # blok başı
    v_p = sv[3]                        # soyunma / duş bölme ekseni
    v_s = L_BLOK                       # blok sonu
    yb = BOLME_T/2
    # 1) mevcut betonarme döşeme
    _katman_bandi(msp, -0.35, v_s+0.35, min(P.ZEMIN_TABAN.values())-DOSEME_KALINLIK,
                  min(P.ZEMIN_TABAN.values()), "beton")
    # 2) zemin katmanları — her mahal kendi Z tipiyle
    for ad, (a, b) in (("soyunma", (v_b, v_p-yb)), ("dus", (v_p+yb, v_s))):
        taban, kat, ust = _zemin_katmanlari(ZEMIN_MAHAL[ad])
        for k_ad, z0, z1, tur in kat:
            _katman_bandi(msp, a, b, z0, z1, tur); n["katman"] += 1
        _kot_isareti(msp, (b-0.18, ust), ust, OLCEK)
    # 3) kesilen duvarlar: blok başı, bölme (kapı boşluklu), blok sonu
    d5 = next(q for q in P.DUVAR_TIPLERI if q[0] == "D5")[2]/1000.0
    for v0, v1, ust, etiket in ((v_b-CEPER_T, v_b, KOT_YAPISAL, "D5"),
                                (v_s, v_s+CEPER_T, KOT_YAPISAL, "D5")):
        _katman_bandi(msp, v0, v1, P.ZEMIN_TABAN["Z4"]-0.02, ust, "beton",
                      "A-KESIT-KESILEN")
        n["katman"] += 1
    # bölme duvarı — K07 kapı boşluğu kesitte görünür
    kapi_h = next(t for t in P.KAPI_LISTESI if t[0] == "K07")[4]/1000.0
    _katman_bandi(msp, v_p-yb, v_p+yb, P.ZEMIN_TABAN["Z5"], kapi_h, "sap",
                  "A-KESIT-KESILEN")
    _katman_bandi(msp, v_p-yb, v_p+yb, kapi_h, P.TAVAN_KOT["T3"], "sap",
                  "A-KESIT-KESILEN")
    _tx(msp, (v_p, kapi_h/2), "K07", 2.5, "A-KAPI", hiza="ORTA", aci=90)
    n["katman"] += 2
    # 4) asma tavanlar + tavan içi tesisat (gerçek kotlarıyla)
    for ad, (a, b), tip in (("soyunma", (v_b, v_p-yb), "T4"),
                            ("dus", (v_p+yb, v_s), "T3")):
        kot = P.TAVAN_KOT[tip]
        _katman_bandi(msp, a, b, kot, kot+0.0125, "sap", "A-KESIT-KESILEN")
        _kot_isareti(msp, (a+0.20, kot), kot, OLCEK, ust=False)
        _tx(msp, ((a+b)/2, kot-0.13), tip, 2.5, "A-TAVAN-YAZI", hiza="ORTA")
        for no, z0, z1, tanim, tur, bant in P.TAVAN_KATMAN[tip]:
            if tur == "tavan":
                # askı çubukları
                t = a + 0.25
                while t < b:
                    _ln(msp, (t, z1), (t, kot+0.0125), "A-KESIT-ARKA"); t += ANA_ARA
                continue
            w = (b-a)
            xa = a + w*{"A": 0.08, "B": 0.36, "C": 0.58, "D": 0.78}.get(bant, 0.2)
            xb = xa + min(0.30, w*0.20)
            _pl(msp, [(xa, z0), (xb, z0), (xb, z1), (xa, z1)], "A-TESISAT-KESIT")
            # uzun lider yerine numaralı balon; numara TAVAN İÇİ KOORDİNASYON
            # tablosundaki sıra numarasıdır — pafta kalabalıklaşmaz
            bp = _balon(msp, (xb + 0.15, (z0+z1)/2), str(no), 0.115)
            _ln(msp, (xb, (z0+z1)/2), (bp[0]-0.115, bp[1]), "M-YAZI")
            n["tesisat"] += 1
    # 5) yapısal tavan
    _katman_bandi(msp, -0.35, v_s+0.35, KOT_YAPISAL, KOT_YAPISAL+DOSEME_KALINLIK, "beton")
    _kot_isareti(msp, (v_b+0.30, KOT_YAPISAL), KOT_YAPISAL, OLCEK, ust=False)
    # 6) kesit düzlemi ARKASINDA görünen donatı
    _gorunen_donati(msp, v_b, v_p, v_s, yb)
    # 7) düşey kot zinciri (sol kenar) + yatay ölçü (alt)
    zn = sorted({round(t, 3) for t in
                 [min(P.ZEMIN_TABAN.values())-DOSEME_KALINLIK,
                  P.ZEMIN_TABAN["Z4"], 0.0, 1.10, 2.10,
                  P.TAVAN_KOT["T3"], P.TAVAN_KOT["T4"], KOT_YAPISAL]})
    n["olcu"] = _zincir(msp, [(-0.62, t) for t in zn], -0.34)
    n["olcu"] += _zincir(msp, [(t, min(P.ZEMIN_TABAN.values())-DOSEME_KALINLIK-0.30)
                               for t in (v_b, v_p, v_s)], -0.34)
    return ((v_b+v_s)/2 + 0.35, (KOT_YAPISAL+DOSEME_KALINLIK)/2 - 0.10)


def _gorunen_donati(msp, v_b, v_p, v_s, yb):
    """Kesit düzleminin arkasında kalan donatı — 0,35 mm görünen çizgi."""
    # soyunma: dolap 1600×450×1800 + bank
    _pl(msp, [(v_b+0.10, 0.0), (v_b+0.10+1.60, 0.0),
              (v_b+0.10+1.60, 1.80), (v_b+0.10, 1.80)], "A-KESIT-GORUNEN")
    _tx(msp, (v_b+0.90, 1.90), "8 gözlü soyunma dolabı 1600×450×1800", 2.0,
        "A-MOBILYA", hiza="ORTA")
    _pl(msp, [(v_p-0.60, 0.0), (v_p-0.18, 0.0), (v_p-0.18, 0.45), (v_p-0.60, 0.45)],
        "A-KESIT-GORUNEN")
    _tx(msp, (v_p-0.39, 0.55), "Bank h=450", 2.0, "A-MOBILYA", hiza="ORTA")
    # duş: tepe duşu ve batarya kotları (proje kabulü)
    dz = P.ZEMIN_TABAN["Z4"] + 0.050
    for z, ad in ((2.10, "Tepe duşu / duş başlığı — kot +2,10"),
                  (1.10, "Duş bataryası — kot +1,10")):
        _ln(msp, (v_s-0.02, z), (v_s-0.30, z), "A-KESIT-GORUNEN")
        msp.add_circle(((v_s-0.30)*K, z*K), 0.035*K, dxfattribs={"layer": "A-KESIT-GORUNEN"})
        _tx(msp, (v_s-0.36, z+0.09), ad, 2.0, "M-YAZI", hiza="SAG")
    # süzgeç
    _pl(msp, [(v_s-0.95, dz-0.02), (v_s-0.80, dz-0.02), (v_s-0.80, dz+0.005),
              (v_s-0.95, dz+0.005)], "A-KESIT-GORUNEN")
    _etiket(msp, (v_s-1.05, dz+0.42),
            ["Sifonlu yer süzgeci Ø100", "eğim %1,5 süzgeğe doğru"],
            OLCEK, "M-YAZI", "SAG", 2.0)


def _liste_kesit(pf, x, y, gen):
    sat = []
    for ad in ("soyunma", "dus"):
        zt = ZEMIN_MAHAL[ad]
        z = next(q for q in P.ZEMIN_TIPLERI if q[0] == zt)
        for i, (k, mm, tur) in enumerate(z[2]):
            sat.append([zt if i == 0 else "", k[:56], f"{mm}" if mm else "mevcut"])
    y = pf.tablo(["TİP", "ZEMİN KATMANI (alttan üste)", "mm"], sat, [12, 92, 16],
                 x=x, y=y, baslik="ZEMİN KATMANLARI")
    tes = []
    for tip in ("T4", "T3"):
        for no, z0, z1, tanim, tur, bant in P.TAVAN_KATMAN[tip]:
            tes.append([no, tip, tanim[:48], f"{z0:.3f}".replace(".", ","),
                        f"{z1:.3f}".replace(".", ",")])
    y = pf.tablo(["№", "TAVAN", "TAVAN İÇİ TESİSAT", "ALT m", "ÜST m"], tes,
                 [8, 14, 62, 18, 18], x=x, y=y-6,
                 baslik="TAVAN İÇİ KOORDİNASYON (№ kesitteki balon)")
    return y


# ══════════════════════════ P-04  İÇ GÖRÜNÜŞ ══════════════════════════════════
# 106 DUŞ — WC ile ortak bölme duvarına (u1 yüzü) içeriden bakış.
# Yerel düzlem: x = duşun v ekseni boyunca genişlik, z = kot.
KARO_D = (0.300, 0.600)          # m — D5 duvar seramiği 300×600 rektifiye
DERZ = 0.002
SU_YALITIM_H = 2.00              # m — duş kabininde yalıtımın dönüş kotu
BATARYA_H, DUS_BASI_H = 1.10, 2.10
NIS = (0.30, 0.60, 1.00)         # genişlik, yükseklik, alt kot


def gorunus(msp):
    u0, v0, u1, v1 = ALT_UV["dus"]
    W = round(v1 - v0, 3)
    _, _, zust = _zemin_katmanlari("Z4")
    H = P.TAVAN_KOT["T3"]
    n = {"karo": 0}
    # 1) duvar yüzü sınırı
    _pl(msp, [(0, zust), (W, zust), (W, H), (0, H)], "A-GORUNUS-SINIR")
    # 2) seramik derz ızgarası — GERÇEK karo ölçüsünden, şaşırtmalı
    z = zust; sira = 0
    while z < H - 1e-6:
        h = min(KARO_D[1], H - z)
        _ln(msp, (0, z), (W, z), "A-GORUNUS-DERZ")
        kay = 0.0 if sira % 2 == 0 else KARO_D[0]/2
        t = kay
        if kay: _ln(msp, (0, z), (0, z+h), "A-GORUNUS-DERZ")
        while t < W - 1e-6:
            _ln(msp, (t, z), (t, z+h), "A-GORUNUS-DERZ"); n["karo"] += 1
            t += KARO_D[0]
        z += h; sira += 1
    _ln(msp, (0, H), (W, H), "A-GORUNUS-SINIR")
    # 3) su yalıtımı dönüş kotu
    _ln(msp, (0, zust+SU_YALITIM_H), (W, zust+SU_YALITIM_H), "A-KATMAN-YALITIM")
    _lider(msp, (W*0.62, zust+SU_YALITIM_H), (W+0.30, zust+SU_YALITIM_H+0.34),
           ["Su yalıtımı dönüş kotu +2,00", "(D-02 detayına bakınız)"],
           OLCEK, "A-KATMAN-YALITIM", h=2.0)
    # 4) armatürler
    bx = W*0.30
    for z, ad, r in ((BATARYA_H, "Duş bataryası (termostatik)", 0.045),
                     (DUS_BASI_H, "Tepe duşu Ø200", 0.10)):
        msp.add_circle((bx*K, (zust+z)*K), r*K, dxfattribs={"layer": "A-GORUNUS-IC"})
        _lider(msp, (bx, zust+z), (W+0.30, zust+z+(-0.16 if r > 0.05 else -0.06)),
               [ad], OLCEK, "M-YAZI", h=2.0)
    _ln(msp, (bx, zust+BATARYA_H), (bx, zust+DUS_BASI_H), "A-GORUNUS-IC")
    # 5) niş (şampuanlık) — karo modülüne oturur
    nx = W - NIS[0] - KARO_D[0]
    _pl(msp, [(nx, zust+NIS[2]), (nx+NIS[0], zust+NIS[2]),
              (nx+NIS[0], zust+NIS[2]+NIS[1]), (nx, zust+NIS[2]+NIS[1])],
        "A-GORUNUS-IC")
    _ln(msp, (nx, zust+NIS[2]+NIS[1]/2), (nx+NIS[0], zust+NIS[2]+NIS[1]/2),
        "A-GORUNUS-IC")
    _lider(msp, (nx+NIS[0]/2, zust+NIS[2]+NIS[1]/2), (W+0.30, zust+NIS[2]+NIS[1]+0.12),
           ["Gömme niş 300×600×120 mm", "karo modülüne oturur, tabanı %2 eğimli"],
           OLCEK, "A-YAZI", h=2.0)
    # 6) tavan ve zemin çizgileri, kotlar
    _kot_isareti(msp, (W*0.80, zust), zust, OLCEK)
    _kot_isareti(msp, (W*0.80, H), H, OLCEK, ust=False)
    _tx(msp, (W/2, H+0.12), f"T3 ASMA TAVAN {H:+.3f}".replace(".", ","),
        2.5, "A-TAVAN-YAZI", hiza="ORTA")
    # 7) süzgeç izdüşümü ve eğim
    _ln(msp, (0, zust), (W, zust), "A-GORUNUS-SINIR")
    # 8) ölçüler
    zn = sorted({round(t, 3) for t in
                 [zust, zust+NIS[2], zust+BATARYA_H, zust+NIS[2]+NIS[1],
                  zust+SU_YALITIM_H, zust+DUS_BASI_H, H]})
    n["olcu"] = _zincir(msp, [(-0.40, t) for t in zn], -0.26)
    xn = sorted({round(t, 3) for t in [0.0, bx, nx, nx+NIS[0], W]})
    n["olcu"] += _zincir(msp, [(t, zust-0.34) for t in xn], -0.26)
    # 9) detay çağrısı — zemin/duvar birleşimi
    c = (0.18, zust)
    msp.add_circle((c[0]*K, c[1]*K), 0.18*K,
                   dxfattribs={"layer": "A-DETAY-CAGRI", "linetype": "DASHED"})
    _ln(msp, (c[0]-0.13, c[1]+0.13), (c[0]-0.52, c[1]+0.52), "A-DETAY-CAGRI")
    bal = (c[0]-0.52-0.28, c[1]+0.52)
    msp.add_circle((bal[0]*K, bal[1]*K), 0.26*K, dxfattribs={"layer": "A-DETAY-CAGRI"})
    _ln(msp, (bal[0]-0.26, bal[1]), (bal[0]+0.26, bal[1]), "A-DETAY-CAGRI")
    _tx(msp, (bal[0], bal[1]+0.10), "D-02", 2.5, "A-DETAY-CAGRI", hiza="ORTA")
    _tx(msp, (bal[0], bal[1]-0.16), "P-05", 2.0, "A-DETAY-CAGRI", hiza="ORTA")
    return (W/2, (zust+H)/2)


def _liste_gorunus(pf, x, y, gen):
    d5 = next(q for q in P.DUVAR_TIPLERI if q[0] == "D5")
    sat = [[k, f"{mm}"] for k, mm in d5[3]]
    y = pf.tablo(["D5 DUVAR KATMANI (içten dışa)", "mm"], sat, [104, 16],
                 x=x, y=y, baslik="DUVAR YAPISI")
    kar = [["Karo", "Porselen 300×600 mm rektifiye, düşey şaşırtmalı"],
           ["Derz", "CG2 WA çimento esaslı, 2 mm — köşelerde 25LM silikon"],
           ["Yapıştırıcı", "C2TE S1, çift taraflı sıvama (tam yapışma)"],
           ["Yalıtım", "EN 14891 çimento esaslı 2 bileşenli, 2 kat, +2,00 m"],
           ["Süpürgelik", "S3 — süpürgelik yok; karo zemine iner, kaveto profil"]]
    y = pf.tablo(["KALEM", "TANIM"], kar, [26, 94], x=x, y=y-6,
                 baslik="KAPLAMA VE BİRLEŞİM")
    arm = [["Duş bataryası", "termostatik, krom", "+1,10"],
           ["Tepe duşu", "Ø200 paslanmaz", "+2,10"],
           ["Gömme niş", "300×600×120 mm", "+1,00"],
           ["Duş kapağı K07", "6 mm temperli cam 700×1950", "+0,015"]]
    y = pf.tablo(["ELEMAN", "TANIM", "KOT m"], arm, [34, 66, 20], x=x, y=y-6,
                 baslik="ARMATÜR VE DONATI KOTLARI")
    return y


# ══════════════════════════ P-05  BİRLEŞİM DETAYI D-02 ════════════════════════
# Z4 ıslak hacim zemini ile D5 seramik kaplı duvarın birleşimi, 1:5.
# Bütün kalınlıklar Z4 ve D5 tip tablolarından okunur; hiçbiri elle yazılmaz.
DETAY_ANAHTAR = []          # (no, grup, katman, mm) — balonlarla eşleşen liste
DETAY_ANAHTAR_EK = []       # (harf, açıklama)
DETAY_ZEMIN_BOY = 0.46      # m — detayda gösterilen zemin uzunluğu
DETAY_DUVAR_BOY = 0.52      # m — detayda gösterilen duvar yüksekliği
BANT_G = 0.120              # m — köşe su yalıtım bandı (Z4 notu)


def _kopus(msp, a, b, kat="A-DETAY-CAGRI", genlik=0.018, adim=0.045):
    """Kopuş (break) çizgisi — detayın sınırlandığı yer."""
    L = math.dist(a, b)
    ux, uy = (b[0]-a[0])/L, (b[1]-a[1])/L
    nx, ny = -uy, ux
    pts, t, s = [a], 0.0, 1
    while t < L:
        t2 = min(t+adim, L)
        m = ((a[0]+ux*(t+t2)/2) + nx*genlik*s, (a[1]+uy*(t+t2)/2) + ny*genlik*s)
        pts.append(m); pts.append((a[0]+ux*t2, a[1]+uy*t2))
        t = t2; s = -s
    msp.add_lwpolyline([(x*K, y*K) for x, y in pts], dxfattribs={"layer": kat})


def detay(msp):
    O = OLCEK_DETAY
    n = {"katman": 0}
    taban, kat, zust = _zemin_katmanlari("Z4")
    d5 = next(q for q in P.DUVAR_TIPLERI if q[0] == "D5")
    duvar_t = sum(mm for _, mm in d5[3])/1000.0      # 216 mm
    x_ic = 0.0                                        # duvarın bitmiş iç yüzü
    x_duv = -duvar_t                                  # duvar arka yüzü
    # 1) duvar katmanları (içten dışa, sağdan sola)
    x = x_ic
    duvar_kat = []
    for ad, mm in reversed(d5[3]):
        t = mm/1000.0
        duvar_kat.append((ad, x-t, x, t))
        x -= t
    # Malzeme sınıfı serbest metinden ÇIKARILIR (MZ.sinifla); detayda her
    # katman kendi gösterimiyle çizilir — 1:5'te seramik derzi, dikme kesiti
    # ve tuğla sırası da görünür hâle gelir.
    for ad, xa, xb, t in duvar_kat:
        q = Polygon([(xa, taban-0.06), (xb, taban-0.06),
                     (xb, taban+DETAY_DUVAR_BOY), (xa, taban+DETAY_DUVAR_BOY)])
        MZ.katman_ciz(msp, q, MZ.sinifla(ad), O, u_yon=(0.0, 1.0))
        n["katman"] += 1
    # 2) zemin katmanları
    for ad, z0, z1, tur in kat:
        q = Polygon([(x_ic, z0), (DETAY_ZEMIN_BOY, z0),
                     (DETAY_ZEMIN_BOY, z1), (x_ic, z1)])
        MZ.katman_ciz(msp, q, MZ.sinifla(ad), O, u_yon=(1.0, 0.0))
        n["katman"] += 1
    # 3) mevcut döşeme
    q = Polygon([(x_duv, taban-DOSEME_KALINLIK),
                 (DETAY_ZEMIN_BOY, taban-DOSEME_KALINLIK),
                 (DETAY_ZEMIN_BOY, taban), (x_duv, taban)])
    MZ.katman_ciz(msp, q, "betonarme", O, u_yon=(1.0, 0.0), ceper=True)
    # 4) KÖŞE SU YALITIM BANDI — detayın asıl konusu
    yal_z = next(z for ad, z, _, t in kat if t == "yalitim")
    yal_ust = next(z1 for ad, z0, z1, t in kat if t == "yalitim")
    # duvardaki yalıtım katmanının x aralığı
    yx = next((xa, xb) for ad, xa, xb, t in duvar_kat if "yalıtım" in ad.lower())
    bant = [(DETAY_ZEMIN_BOY*0.0 + BANT_G, yal_z),
            (yx[1], yal_z), (yx[1], yal_z + BANT_G),
            (yx[1]-0.0015, yal_z + BANT_G), (yx[1]-0.0015, yal_z+0.0015),
            (BANT_G, yal_z+0.0015)]
    _pl(msp, bant, "A-KATMAN-YALITIM")
    MZ._hatch(msp, Polygon(bant), MZ.KAT_YALITIM, "SOLID", 0, 0, O, renk=6)
    bp = _balon(msp, (BANT_G*1.9, yal_z+0.10), "A", 0.026, "A-KATMAN-YALITIM", O)
    _ln(msp, (BANT_G*0.6, yal_z), (bp[0], bp[1]-0.026), "A-KATMAN-YALITIM")
    DETAY_ANAHTAR_EK.clear()
    DETAY_ANAHTAR_EK.append(("A", f"Elastik su yalıtım bandı {BANT_G*1000:.0f} mm — "
                                  "yalıtımın iki katı arasına gömülür"))
    # 5) kaveto (içbükey) profil — S3 süpürgelik kararı
    kv = 0.030
    msp.add_arc((x_ic*K, zust*K), kv*K, 0, 90, dxfattribs={"layer": "A-KESIT-KESILEN"})
    bp = _balon(msp, (x_ic+0.14, zust+0.16), "B", 0.026, "A-YAZI", O)
    _ln(msp, (x_ic+kv*0.7, zust+kv*0.7), (bp[0]-0.026, bp[1]), "A-YAZI")
    DETAY_ANAHTAR_EK.append(("B", "S3 — süpürgelik yok; duvar karosu zemine iner, "
                                  "birleşimde içbükey (kaveto) porselen profil"))
    # 6) katman numaraları — balonlar DETAY KATMAN LİSTESİ tablosuyla eşleşir
    DETAY_ANAHTAR.clear()
    i = 1
    yy = taban + DETAY_DUVAR_BOY - 0.04
    for ad, xa, xb, t in duvar_kat:
        bp = _balon(msp, (DETAY_ZEMIN_BOY*0.30, yy), str(i), 0.026, "A-YAZI", O)
        _ln(msp, ((xa+xb)/2, yy), (bp[0]-0.026, bp[1]), "A-YAZI")
        DETAY_ANAHTAR.append((i, "D5 duvar", ad, f"{t*1000:.0f}" if t else "mevcut"))
        yy -= 0.062; i += 1
    # zemin katmanları için balonlar SAĞDA, katman kotuna yakın dizilir
    yz = zust + 0.20
    for ad, z0, z1, tur in kat:
        bp = _balon(msp, (DETAY_ZEMIN_BOY+0.075, yz), str(i), 0.026, "A-YAZI", O,
                    ayir=False)
        _ln(msp, (DETAY_ZEMIN_BOY*0.62, (z0+z1)/2), (bp[0]-0.026, bp[1]), "A-YAZI")
        DETAY_ANAHTAR.append((i, "Z4 zemin", ad, f"{(z1-z0)*1000:.0f}"))
        yz -= 0.062; i += 1
    # 7) kopuş çizgileri
    _kopus(msp, (DETAY_ZEMIN_BOY, taban-DOSEME_KALINLIK), (DETAY_ZEMIN_BOY, zust))
    _kopus(msp, (x_duv, taban+DETAY_DUVAR_BOY), (x_ic, taban+DETAY_DUVAR_BOY))
    # 8) kotlar ve ölçüler
    _kot_isareti(msp, (DETAY_ZEMIN_BOY*0.55, zust), zust, O)
    _kot_isareti(msp, (DETAY_ZEMIN_BOY*0.55, taban), taban, O, ust=False)
    zn = sorted({round(t, 4) for t in
                 [taban-DOSEME_KALINLIK, taban] + [z1 for _, _, z1, _ in kat]})
    n["olcu"] = _zincir(msp, [(-duvar_t-0.12, t) for t in zn], -0.06, O)
    xn = sorted({round(t, 4) for t in [x_duv] + [xa for _, xa, _, _ in duvar_kat]
                 + [x_ic]})
    n["olcu"] += _zincir(msp, [(t, taban+DETAY_DUVAR_BOY+0.10) for t in xn], 0.06, O)
    return ((x_duv+DETAY_ZEMIN_BOY)/2, (taban-DOSEME_KALINLIK+DETAY_DUVAR_BOY)/2)


def _liste_detay(pf, x, y, gen):
    y = pf.tablo(["№", "GRUP", "KATMAN", "mm"],
                 [[n, g, a[:52], mm] for n, g, a, mm in DETAY_ANAHTAR],
                 [8, 20, 78, 14], x=x, y=y, baslik="DETAY KATMAN LİSTESİ")
    if DETAY_ANAHTAR_EK:
        y = pf.tablo(["№", "BİRLEŞİM ELEMANI"],
                     [[k, v[:96]] for k, v in DETAY_ANAHTAR_EK], [8, 112],
                     x=x, y=y-6, baslik="BİRLEŞİM NOTLARI")
    d = next(q for q in P.DETAYLAR if q[0] == "D-02")
    y = pf.tablo(["D-02 — UYGULAMA KURALI"], [[t] for t in d[4]], [120],
                 x=x, y=y, baslik="DETAY NOTLARI")
    kay = [["EN 14891", "Çimento esaslı su yalıtımı — sıvı uygulanan"],
           ["EN 16165 Ek B", "R11 kaymazlık — duş ve WC zemini"],
           ["EN 12004 / C2TE S1", "Seramik yapıştırıcısı, deforme olabilir"],
           ["EN 13888 / CG2 WA", "Derz dolgusu — su emmesi azaltılmış"],
           ["ISO 11600 / 25LM", "Köşe silikonu — küf önleyici"]]
    y = pf.tablo(["KAYNAK", "KONU"], kay, [40, 80], x=x, y=y-6,
                 baslik="UYGULANAN STANDARTLAR (aday — proje bazında doğrulanacak)")
    return y


if __name__ == "__main__":
    print("PİLOT BÖLGE — " + BLOK + " ISLAK BLOK (105 · 106 · 107)")
    print(f"  yerel eksen: u={W_BLOK:.3f} m · v={L_BLOK:.3f} m · doğrultu {ACI_DER:.2f}°")
    print(f"  net mahal alanları: " +
          " · ".join(f"{MAHAL[k]} {v:.2f} m²".replace(".", ",")
                     for k, v in NET_M2.items()))
    d = uret()
    pdf, png = onizleme(d)
    print(f"  → {pdf.relative_to(KOK)}  ·  {len(d)} pafta A2")
    print(f"  → work/pilot/  ·  {len(png)} PNG önizleme")
