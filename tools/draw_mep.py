# -*- coding: utf-8 -*-
"""Mekanik ve elektrik pafta çizim primitifleri."""
import math
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from shapely.geometry import LineString
from shapely.ops import unary_union
import proj as P, helpers as h, draw as D

# ── renk paleti (disiplin standardı) ──────────────────────────────────────────
C_BESLEME = HexColor("#2E7D5B")   # taze hava
C_EGZOZ   = HexColor("#C8322B")   # egzoz
C_ISLAK   = HexColor("#8E3BB0")   # ıslak hacim egzozu
C_SOGUK   = HexColor("#2F6FB3")   # temiz su
C_SICAK   = HexColor("#D2691E")   # sıcak su
C_PIS     = HexColor("#5A6470")   # pis su
C_KLIMA   = HexColor("#1F8AA8")   # soğutucu akışkan
C_DRENAJ  = HexColor("#7FA8C4")
C_AYD     = HexColor("#D9A115")   # aydınlatma
C_PRIZ    = HexColor("#1F6FB2")   # priz / kuvvet
C_ZAYIF   = HexColor("#7B3FA0")   # zayıf akım
C_YANGIN  = HexColor("#C8322B")

def altlik(v, ton="acik"):
    """Tesisat paftası altlığı: mimari soluk, tesisat üstte okunur."""
    gri = HexColor("#F1F3F5") if ton == "acik" else HexColor("#E9ECEF")
    D.poly(v, P.SALON, fill=gri)
    for ad, d in P.ISLAK.items():
        D.poly(v, d["tum"], fill=HexColor("#E3E8EC"))
    ic = unary_union([P.SALON, P.ERKEK, P.KADIN])
    D.poly(v, ic.buffer(D.DUVAR_T, join_style=2).difference(ic), fill=HexColor("#B9BFC7"))
    D.poly(v, ic, stroke=HexColor("#949BA4"), lw=0.6)
    for b in (P.ERKEK, P.KADIN):
        D.poly(v, b, stroke=HexColor("#949BA4"), lw=0.5)
    for ad, d in P.ISLAK.items():
        for n in ("dus", "wc"):
            D.poly(v, d[n], stroke=HexColor("#A8AEB6"), lw=0.4)
    for a, b in P.CEPHE:
        D.poly(v, LineString([a, b]).buffer(0.09, cap_style=2),
               fill=HexColor("#FFFFFF"), stroke=HexColor("#8FB4D2"), lw=0.9)

def ekipman_soluk(v):
    for kod, ad, g in P.ekipman_poligonlari():
        D.poly(v, g, fill=HexColor("#DDE1E6"), stroke=HexColor("#C3C9D0"), lw=0.35)

def kanal(v, guzergah, genislik_m, renk, lw=0.6):
    ls = LineString(guzergah)
    D.poly(v, ls.buffer(genislik_m/2, cap_style=2, join_style=2),
           fill=h.tint(renk, 0.72), stroke=renk, lw=lw)
    for i in range(len(guzergah)-1):
        D.line(v, guzergah[i], guzergah[i+1], renk, 0.45, (1.6, 1.4))

def boru(v, guzergah, renk, lw=1.3, dash=None):
    for i in range(len(guzergah)-1):
        D.line(v, guzergah[i], guzergah[i+1], renk, lw, dash)

def _daire(v, x, y, r_mm, fill, stroke=None, lw=0.5):
    c = v.c; px, py = v.p((x, y))
    if fill:   c.setFillColor(fill)
    if stroke: c.setStrokeColor(stroke); c.setLineWidth(lw)
    c.circle(px, py, r_mm, stroke=1 if stroke else 0, fill=1 if fill else 0)
    return px, py

def _kare(v, x, y, a_mm, fill, stroke=None, lw=0.5):
    c = v.c; px, py = v.p((x, y))
    if fill:   c.setFillColor(fill)
    if stroke: c.setStrokeColor(stroke); c.setLineWidth(lw)
    c.rect(px-a_mm/2, py-a_mm/2, a_mm, a_mm, stroke=1 if stroke else 0, fill=1 if fill else 0)
    return px, py

def menfez(v, x, y, tip, kod, debi=None):
    renk = {"besleme": C_BESLEME, "egzoz": C_EGZOZ, "valf": C_ISLAK}[tip]
    c = v.c; px, py = v.p((x, y))
    a = 3.4*mm if tip != "valf" else 2.6*mm
    c.setFillColor(HexColor("#FFFFFF")); c.setStrokeColor(renk); c.setLineWidth(0.8)
    if tip == "valf":
        c.circle(px, py, a/2, 1, 1); c.setStrokeColor(renk); c.setLineWidth(0.5)
        c.line(px-a/3, py, px+a/3, py); c.line(px, py-a/3, px, py+a/3)
    else:
        c.rect(px-a/2, py-a/2*0.62, a, a*0.62, 1, 1)
        c.setLineWidth(0.4)
        for k in range(1, 3):
            c.line(px-a/2, py-a/2*0.62+k*a*0.62/3, px+a/2, py-a/2*0.62+k*a*0.62/3)
    h.txt(c, px, py+a/2+0.9*mm, kod, h.FB, 4.4, renk, "c")
    if debi: h.txt(c, px, py-a/2-3.0*mm, f"{debi} m³/h", h.F, 3.8, renk, "c")

def cihaz(v, x, y, kod, renk, w_mm=7.0, hh_mm=4.4, aci=0.0):
    c = v.c; px, py = v.p((x, y))
    if aci: c.saveState(); c.translate(px, py); c.rotate(aci); c.translate(-px, -py)
    c.setFillColor(renk); c.setStrokeColor(HexColor("#FFFFFF")); c.setLineWidth(0.7)
    c.roundRect(px-w_mm/2, py-hh_mm/2, w_mm, hh_mm, 0.8*mm, 1, 1)
    if aci: c.restoreState()
    h.txt(c, px, py-1.3*mm, kod, h.FB, 4.6, HexColor("#FFFFFF"), "c")

def sembol(v, x, y, tip, kod=None, aci=0.0):
    """aci: duvara göre dönme (derece). Sembolün 'yukarı'sı hacmin içine bakar."""
    c = v.c
    if aci:
        px0, py0 = v.p((x, y))
        c.saveState(); c.translate(px0, py0); c.rotate(aci); c.translate(-px0, -py0)
    _sembol_ciz(v, x, y, tip, None)          # sembol döner
    if aci: c.restoreState()
    if tip == "pano":                         # pano yazısı her zaman yatay okunur
        px, py = v.p((x, y))
        h.txt(c, px, py - 1.4*mm, "ADP", h.FB, 4.6, HexColor("#FFFFFF"), "c")
    if kod and tip in ("priz", "priz_ip44", "kamera", "hoparlor", "veri",
                       "dedektor", "yangin", "anahtar"):
        px, py = v.p((x, y))                  # etiket YATAY kalır
        h.txt(c, px, py + 2.6*mm, kod, h.F, 3.6, h.GREY, "c")

def _sembol_ciz(v, x, y, tip, kod=None):
    c = v.c
    if tip == "priz":
        px, py = _daire(v, x, y, 1.7*mm, HexColor("#FFFFFF"), C_PRIZ, 0.7)
        c.setStrokeColor(C_PRIZ); c.setLineWidth(0.7); c.line(px-1.7*mm, py, px+1.7*mm, py)
        c.setFillColor(C_PRIZ); c.rect(px-1.7*mm, py, 3.4*mm, 0.9*mm, 0, 1)
    elif tip == "priz_ip44":
        px, py = _daire(v, x, y, 1.9*mm, C_PRIZ, HexColor("#FFFFFF"), 0.6)
        h.txt(c, px, py-1.0*mm, "44", h.FB, 3.4, HexColor("#FFFFFF"), "c")
    elif tip == "anahtar":
        px, py = v.p((x, y))
        c.setStrokeColor(C_AYD); c.setLineWidth(0.8)
        c.circle(px, py, 1.2*mm, 1, 0); c.line(px, py, px+2.0*mm, py+1.8*mm)
    elif tip == "sensor":
        px, py = _daire(v, x, y, 1.8*mm, HexColor("#FFF6DC"), C_AYD, 0.7)
        h.txt(c, px, py-1.0*mm, "S", h.FB, 3.6, C_AYD, "c")
    elif tip == "armatur":
        px, py = v.p((x, y)); L = v.m(1.25)
        c.setFillColor(HexColor("#FFF3C4")); c.setStrokeColor(C_AYD); c.setLineWidth(0.6)
        c.rect(px-L/2, py-0.85*mm, L, 1.7*mm, 1, 1)
    elif tip == "downlight":
        px, py = _daire(v, x, y, 1.6*mm, HexColor("#FFF3C4"), C_AYD, 0.6)
        c.setStrokeColor(C_AYD); c.setLineWidth(0.5)
        c.line(px-1.1*mm, py-1.1*mm, px+1.1*mm, py+1.1*mm)
        c.line(px-1.1*mm, py+1.1*mm, px+1.1*mm, py-1.1*mm)
    elif tip == "acil":
        px, py = _kare(v, x, y, 3.2*mm, HexColor("#E8F5EC"), HexColor("#2E7D5B"), 0.7)
        h.txt(c, px, py-1.1*mm, kod or "E", h.FB, 3.6, HexColor("#2E7D5B"), "c")
    elif tip == "kamera":
        px, py = v.p((x, y))
        c.setFillColor(C_ZAYIF); c.setStrokeColor(HexColor("#FFFFFF")); c.setLineWidth(0.5)
        p = c.beginPath(); p.moveTo(px-2.0*mm, py-1.5*mm); p.lineTo(px+2.0*mm, py)
        p.lineTo(px-2.0*mm, py+1.5*mm); p.close(); c.drawPath(p, 1, 1)
    elif tip == "hoparlor":
        px, py = _daire(v, x, y, 1.8*mm, HexColor("#F3EAF8"), C_ZAYIF, 0.7)
        c.setStrokeColor(C_ZAYIF); c.setLineWidth(0.5)
        c.arc(px-0.4*mm, py-2.6*mm, px+3.2*mm, py+2.6*mm, -50, 100)
    elif tip == "veri":
        px, py = _kare(v, x, y, 3.2*mm, HexColor("#F3EAF8"), C_ZAYIF, 0.7)
        h.txt(c, px, py-1.1*mm, "D", h.FB, 3.6, C_ZAYIF, "c")
    elif tip == "dedektor":
        px, py = _daire(v, x, y, 2.0*mm, HexColor("#FFFFFF"), C_YANGIN, 0.8)
        _daire(v, x, y, 0.8*mm, C_YANGIN)
    elif tip == "yangin":
        px, py = _kare(v, x, y, 3.2*mm, C_YANGIN, HexColor("#FFFFFF"), 0.6)
        h.txt(c, px, py-1.1*mm, "Y", h.FB, 3.6, HexColor("#FFFFFF"), "c")
    elif tip == "pano":
        px, py = v.p((x, y))
        c.setFillColor(HexColor("#16273D")); c.setStrokeColor(HexColor("#FFFFFF")); c.setLineWidth(0.7)
        c.rect(px-4.2*mm, py-2.8*mm, 8.4*mm, 5.6*mm, 1, 1)


def lejant_dikey(v_c, x, y, satirlar, w, s=6.0, adim=5.6*mm):
    """satirlar: [(cizim_fn(c,x,y), metin)]"""
    c = v_c
    for fn, t in satirlar:
        fn(c, x+3.0*mm, y+1.0*mm)
        h.txt(c, x+8.5*mm, y, t, h.F, s, h.INK)
        y -= adim
    return y


# ══════════════════════ LİNYE (TESİSAT HATTI) ÇİZİMİ ══════════════════════════
# Uygulama projesi kuralı: tesisat hatları ortogonal döşenir; hat üzerine
# iletken sayısı çentiği, kablo cinsi/kesiti ve boru çapı yazılır.
_LINYE_RENK = {"L": C_AYD, "P": C_PRIZ, "K": C_KLIMA, "W": C_SICAK,
               "V": C_BESLEME, "Z": C_ZAYIF}
_BORU_CAP   = {2.5: "Ø20", 6.0: "Ø25", 1.5: "Ø16", 10.0: "Ø32"}


def linye_rengi(kod):
    return _LINYE_RENK.get(kod[0], C_PRIZ)


# Zayıf akım hatları güç linyesi değildir; kendi kablo cinsleriyle etiketlenir.
_ZAYIF_ETIKET = {
 "Z1": "Z1 · U/UTP Cat6 + RG6 · kablo kanalı 50×50",
 "Z2": "Z2 · JE-H(St)H 2×2×0,8 (FE180/E30) · yangın algılama çevrimi",
}


def linye_etiketi(kod):
    """'P3 · NHXMH 3×2,5 · Ø20' — pafta üzerine yazılan hat tanımı."""
    if kod in _ZAYIF_ETIKET: return _ZAYIF_ETIKET[kod]
    l = next((x for x in P.LINYE if x[0] == kod), None)
    if not l: return kod
    kes = l[3]
    try:
        mm2 = float(kes.split("×")[1].replace(",", "."))
    except Exception:
        mm2 = 2.5
    return f"{kod} · NHXMH {kes} · {_BORU_CAP.get(mm2, 'Ø20')}"


def _centik(v, a, b, adet, renk, boy_mm=1.7, ara_mm=1.1):
    """Hat üzerine iletken sayısı çentiği (kısa eğik çizgiler)."""
    c = v.c
    ax, ay = v.p(a); bx, by = v.p(b)
    L = math.hypot(bx-ax, by-ay)
    if L < (adet+1)*ara_mm + 6: return
    ux, uy = (bx-ax)/L, (by-ay)/L
    mx, my = (ax+bx)/2, (ay+by)/2
    c.saveState(); c.setStrokeColor(renk); c.setLineWidth(0.45)
    bas = -(adet-1)*ara_mm/2
    for i in range(adet):
        t = bas + i*ara_mm
        px, py = mx+ux*t, my+uy*t
        # 60° eğik çentik
        dx, dy = (-uy*0.5 + ux*0.866)*boy_mm/2, (ux*0.5 + uy*0.866)*boy_mm/2
        c.line(px-dx, py-dy, px+dx, py+dy)
    c.restoreState()


_ETIKET_KONUM = []      # çizim başına yerleştirilmiş etiket noktaları (pt)


def etiket_sifirla():
    _ETIKET_KONUM.clear()


def _bos_yer(px, py, asgari_mm=17.0):
    for qx, qy in _ETIKET_KONUM:
        if math.hypot(px-qx, py-qy) < asgari_mm*mm: return False
    return True


def linye(v, kod, segmentler, etiket=True, lw=0.85, centik=True):
    """Bir linyenin ortogonal güzergâhını çizer.

    `segmentler`: [[(x,y), ...], ...] — her biri ortogonal poligon.
    Çapraz segment bulunursa çizilmez; bu bir çizim hatasıdır ve denetim
    ajanı tarafından yakalanır.
    """
    renk = linye_rengi(kod)
    try:
        iletken = int(P.LINYE and next(x for x in P.LINYE if x[0] == kod)[3].split("×")[0])
    except Exception:
        iletken = 3
    adaylar = []
    for g in segmentler:
        for a, b in zip(g, g[1:]):
            if abs(a[0]-b[0]) > 1e-6 and abs(a[1]-b[1]) > 1e-6:
                continue                      # çapraz hat çizilmez
            D.line(v, a, b, renk, lw)
            adaylar.append((math.dist(a, b), a, b))
    adaylar.sort(key=lambda t: -t[0])
    en_uzun = (adaylar[0][1], adaylar[0][2]) if adaylar else None
    # etiket, çakışmayan en uzun segmentin ortasına konur
    yerlesim = None
    for d, a, b in adaylar:
        if d < 0.9: break
        for t in (0.5, 0.32, 0.68, 0.2, 0.8):
            px, py = v.p((a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t))
            if _bos_yer(px, py):
                yerlesim = (a, b, px, py); break
        if yerlesim: break
    if centik and en_uzun:
        _centik(v, en_uzun[0], en_uzun[1], iletken, renk)
    if etiket and yerlesim:
        a, b, _px, _py = yerlesim
        px, py = _px, _py
        _ETIKET_KONUM.append((px, py))
        yatay = abs(a[1]-b[1]) < 1e-6
        c = v.c; c.saveState()
        c.setFillColor(HexColor("#FFFFFF"))
        metin = linye_etiketi(kod)
        gen = len(metin)*2.15 + 4
        if yatay:
            c.rect(px-gen/2*0.5*mm, py+0.9*mm, gen*0.5*mm, 3.0*mm, 0, 1)
            h.txt(c, px, py+1.8*mm, metin, h.F, 4.6, renk, "c")
        else:
            c.translate(px-1.6*mm, py); c.rotate(90)
            c.rect(-gen/2*0.5*mm, -1.1*mm, gen*0.5*mm, 3.0*mm, 0, 1)
            h.txt(c, 0, 0, metin, h.F, 4.6, renk, "c")
        c.restoreState()


def linyeleri_ciz(v, kodlar, etiket=True, lw=0.85):
    """data/yollar.json içindeki hazır güzergâhları çizer."""
    import linye_yollari as LY
    d = LY.yukle()
    if not d: return 0
    etiket_sifirla()
    n = 0
    for kod in kodlar:
        kayit = d.get("linye", {}).get(kod)
        if not kayit: continue
        linye(v, kod, kayit["segment"], etiket=etiket, lw=lw); n += 1
    return n


def anahtar_hatlari_ciz(v, lw=0.6):
    """Anahtar → armatür kumanda hatları (ince, kesikli)."""
    import linye_yollari as LY
    d = LY.yukle()
    for kayit in (d.get("anahtar") or []):
        for g in kayit["segment"]:
            for a, b in zip(g, g[1:]):
                if abs(a[0]-b[0]) > 1e-6 and abs(a[1]-b[1]) > 1e-6: continue
                D.line(v, a, b, C_AYD, lw, (1.4, 1.2))
