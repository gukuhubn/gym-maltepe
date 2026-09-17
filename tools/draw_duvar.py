# -*- coding: utf-8 -*-
"""ALÇIPAN BÖLME DUVAR ÇİZİM MOTORU — gerçek profil geometrisiyle.

Metal karkas alçıpan bölme, plan ve yatay kesitte ÜÇ bileşenle çizilir:
  1. Levha katmanları  — her yüzde 2 × 12,5 mm, derzleri şaşırtmalı
  2. C dikme profilleri — @400 mm, gövde duvar kalınlığı boyunca, kanatlar
                          duvar ekseni yönünde (C ağzı sırayla ters çevrilir)
  3. Taşyünü dolgu      — dikmeler arasında

Profil ölçüleri (TS EN 14195 / DIN 18182):
  C50×50×0,6   gövde 50 · kanat 50 · et 0,6 mm   → 100 mm bölme
  C75×50×0,6   gövde 75 · kanat 50               → 125 mm bölme
  U50×40×0,6   taban/tavan kanalı (DU)
"""
import math
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
import proj as P, helpers as h

# ── profil kataloğu ───────────────────────────────────────────────────────────
PROFIL = {
 "C50":  dict(govde=50, kanat=50, et=0.6, ad="C50×50×0,6"),
 "C75":  dict(govde=75, kanat=50, et=0.6, ad="C75×50×0,6"),
 "C100": dict(govde=100, kanat=50, et=0.6, ad="C100×50×0,6"),
 "U50":  dict(govde=50, kanat=40, et=0.6, ad="U50×40×0,6"),
}
DIKME_ARA = 0.40        # m — C dikme aralığı
LEVHA     = 0.0125      # m — tek kat alçıpan

C_LEVHA   = HexColor("#F2EFE8")
C_LEVHA_K = HexColor("#B9B4A8")
C_PROFIL  = HexColor("#5A6470")
C_TASYUNU = HexColor("#FBE6A8")
C_TASYUNU_K = HexColor("#C9A227")
C_YENI    = HexColor("#C8322B")

# ═══════════════════════════════════════════════════════════════════════════════
#  BÖLME DUVAR EKSENLERİ — geometriden türetilir
# ═══════════════════════════════════════════════════════════════════════════════
def _duz_segmentler(geom, asgari=0.35):
    """LineString/MultiLineString → düz segment listesi."""
    out = []
    gs = list(geom.geoms) if geom.geom_type.startswith("Multi") else [geom]
    for g in gs:
        if g.geom_type != "LineString": continue
        cs = list(g.coords)
        for i in range(len(cs)-1):
            if math.dist(cs[i], cs[i+1]) >= asgari:
                out.append((cs[i], cs[i+1]))
    return out

def bolme_eksenleri():
    """[(p1, p2, tip, kalinlik_m)] — tüm yeni alçıpan bölmeler."""
    seg = []
    for blok in (P.ERKEK, P.KADIN):
        ort = blok.exterior.intersection(P.SALON.buffer(0.26))
        for a, b in _duz_segmentler(ort):
            seg.append((a, b, "D2", 0.10))
    def _snr(g):
        gs = g.geoms if g.geom_type.startswith("Multi") else [g]
        return unary_union([x.exterior for x in gs if x.geom_type == "Polygon"])
    for ad, d in P.ISLAK.items():
        i1 = _snr(d["soyunma"]).intersection(d["dus"].union(d["wc"]).buffer(0.02))
        i2 = _snr(d["dus"]).intersection(d["wc"].buffer(0.02))
        for g in (i1, i2):
            for a, b in _duz_segmentler(g):
                seg.append((a, b, "D3", 0.10))
    return seg

BOLME = bolme_eksenleri()
BOLME_UZUNLUK = round(sum(math.dist(a, b) for a, b, *_ in BOLME), 2)

def dikme_noktalari(a, b, ara=DIKME_ARA, kenar=0.05):
    """Bir bölme ekseni üzerindeki C dikme konumları (m cinsinden mesafe)."""
    L = math.dist(a, b)
    n = max(2, int(round((L-2*kenar)/ara))+1)
    if n < 2: return [kenar, L-kenar]
    step = (L-2*kenar)/(n-1)
    return [kenar + i*step for i in range(n)]

DIKME_ADEDI = sum(len(dikme_noktalari(a, b)) for a, b, *_ in BOLME)

# ═══════════════════════════════════════════════════════════════════════════════
#  PLAN ÇİZİMİ (1/75 – 1/50) — levha yüzleri + dikme işaretleri
# ═══════════════════════════════════════════════════════════════════════════════
def plan_bolme(v, dikme=True, profil_kodu="C50"):
    """draw.View üzerinde alçıpan bölmeleri gerçek katman kalınlığıyla çizer."""
    import draw as D
    c = v.c
    pr = PROFIL[profil_kodu]
    for a, b, tip, t in BOLME:
        ls = LineString([a, b])
        # levha yüzleri (dış kontur)
        D.poly(v, ls.buffer(t/2, cap_style=2, join_style=2),
               fill=C_LEVHA, stroke=HexColor("#3A3F46"), lw=0.7)
        # karkas boşluğu (gövde derinliği)
        gd = pr["govde"]/1000.0
        D.poly(v, ls.buffer(gd/2, cap_style=2, join_style=2),
               fill=C_TASYUNU, stroke=None, alpha=0.55)
        # levha derz çizgisi (çift kat ayrımı)
        for s in (+1, -1):
            off = ls.parallel_offset(t/2 - LEVHA, "left" if s > 0 else "right")
            if not off.is_empty and off.geom_type == "LineString":
                cs = list(off.coords)
                D.line(v, cs[0], cs[-1], HexColor("#C9C4B8"), 0.35)
        if not dikme: continue
        # ── C dikmeler @400 mm
        L = math.dist(a, b)
        ux, uy = (b[0]-a[0])/L, (b[1]-a[1])/L
        nx, ny = -uy, ux                      # duvar normali
        kanat = pr["kanat"]/1000.0
        for i, s in enumerate(dikme_noktalari(a, b)):
            px, py = a[0]+ux*s, a[1]+uy*s
            yon = 1 if i % 2 == 0 else -1     # C ağzı sırayla ters
            g1 = (px + nx*gd/2, py + ny*gd/2)
            g2 = (px - nx*gd/2, py - ny*gd/2)
            D.line(v, g1, g2, C_PROFIL, 0.75)                       # gövde
            for gg in (g1, g2):                                      # kanatlar
                D.line(v, gg, (gg[0]+ux*kanat*yon, gg[1]+uy*kanat*yon), C_PROFIL, 0.75)

def plan_bolme_etiket(v, fs=4.6):
    """Her bölme ekseninin ortasına tip + profil etiketi."""
    import draw as D
    for a, b, tip, t in BOLME:
        mx, my = (a[0]+b[0])/2, (a[1]+b[1])/2
        L = math.dist(a, b)
        n = len(dikme_noktalari(a, b))
        D.etiket(v, (mx, my), f"{tip} · C50 @400 · {n} dikme", fs, C_YENI, h.F, "c", dy=-1.2)

# ═══════════════════════════════════════════════════════════════════════════════
#  YATAY KESİT DETAYI (1/10 – 1/5) — gerçek profil geometrisi
# ═══════════════════════════════════════════════════════════════════════════════
def _tarama(c, x0, y0, x1, y1, tip, adim=1.4*mm):
    c.saveState()
    p = c.beginPath(); p.rect(x0, y0, x1-x0, y1-y0); c.clipPath(p, 0, 0)
    c.setLineWidth(0.3)
    if tip == "levha":
        c.setStrokeColor(C_LEVHA_K)
        n = int((y1-y0)/adim)+1
        for i in range(n):
            c.setFillColor(C_LEVHA_K)
            for j in range(int((x1-x0)/adim)+1):
                c.circle(x0+j*adim+(adim/2 if i % 2 else 0), y0+i*adim, 0.2*mm, 0, 1)
    elif tip == "tasyunu":
        c.setStrokeColor(C_TASYUNU_K)
        n = int((y1-y0)/(adim*1.1))+1
        for i in range(n):
            yy = y0+i*adim*1.1
            pth = c.beginPath(); pth.moveTo(x0, yy); k = 0
            while x0+k*adim < x1:
                pth.curveTo(x0+(k+0.3)*adim, yy+adim*0.4, x0+(k+0.7)*adim, yy-adim*0.4,
                            x0+(k+1)*adim, yy); k += 1
            c.drawPath(pth, 1, 0)
    c.restoreState()

def yatay_kesit(c, x, y, w, duvar_tipi, olcek=0.10, baslik=None, adet=3):
    """Alçıpan bölmenin YATAY KESİTİ — gerçek C profil geometrisi.
    olcek: 1 mm gerçek = olcek*mm çizim (0,10 → 1/10).
    Döner: (alt_y, toplam_kalinlik_mm)"""
    d = [x for x in P.DUVAR_TIPLERI if x[0] == duvar_tipi][0]
    kod, ad, toplam, katmanlar, perf = d
    birim = olcek*mm
    # katman dizilimi → (kalınlık, tip)
    diz = []
    for k_ad, kal in katmanlar:
        low = k_ad.lower()
        if "alçıpan" in low:
            n = 2 if "2 kat" in low else 1
            for _ in range(n): diz.append((12.5, "levha", k_ad))
        elif "profil" in low:
            diz.append((float(kal) if kal else 50.0, "karkas", k_ad))
        elif "taşyünü" in low: continue
        elif "hava boşluğu" in low: diz.append((float(kal), "bosluk", k_ad))
        elif "duvar" in low: diz.append((float(kal), "mevcut", k_ad))
        elif "seramik" in low: diz.append((float(kal), "seramik", k_ad))
        elif "yalıtım" in low: diz.append((float(kal), "yalitim", k_ad))
        elif "yapıştırıcı" in low: diz.append((float(kal), "sap", k_ad))
        elif "kontrapla" in low: diz.append((float(kal), "ahsap", k_ad))
        elif "ayna" in low: diz.append((float(kal), "ayna", k_ad))
        elif kal: diz.append((float(kal), "sap", k_ad))
    tot = sum(k for k, *_ in diz)
    # duvar boyunca çizilecek uzunluk: adet × 400 mm dikme aralığı
    boy = adet*DIKME_ARA*1000
    if boy*birim > w-26*mm: boy = (w-26*mm)/birim
    x0 = x+16*mm; y0 = y - tot*birim
    RENK = {"levha": ("#F2EFE8", "#B9B4A8"), "karkas": ("#FFFFFF", "#C9C4B8"),
            "bosluk": ("#FFFFFF", "#D5D8DC"), "mevcut": ("#C9CCD1", "#8A8F98"),
            "seramik": ("#9FB8C4", "#5E7B8B"), "yalitim": ("#7FB0D8", "#2F6FB3"),
            "sap": ("#E2E0DA", "#A9A69D"), "ahsap": ("#D8B98C", "#9A7845"),
            "ayna": ("#D6E6F2", "#5E8FB5")}
    yy = y
    karkas_y = None
    for kal, tip, k_ad in diz:
        hgt = kal*birim
        fill, kon = RENK[tip]
        c.saveState(); c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor(kon))
        c.setLineWidth(0.5); c.rect(x0, yy-hgt, boy*birim, hgt, 1, 1); c.restoreState()
        if tip == "levha":  _tarama(c, x0, yy-hgt, x0+boy*birim, yy, "levha")
        if tip == "karkas": karkas_y = (yy-hgt, yy, kal)
        yy -= hgt
    # ── C dikmeler + taşyünü (karkas katmanı içinde)
    if karkas_y:
        ky0, ky1, gov = karkas_y
        kanat = 50.0
        n = int(boy/(DIKME_ARA*1000))+1
        for i in range(n):
            px = x0 + i*DIKME_ARA*1000*birim
            if px > x0+boy*birim: break
            yon = 1 if i % 2 == 0 else -1
            c.saveState(); c.setStrokeColor(C_PROFIL); c.setLineWidth(1.0)
            c.line(px, ky0, px, ky1)                                  # gövde
            for yk in (ky0, ky1):
                c.line(px, yk, px+kanat*birim*yon, yk)                # kanatlar
                c.line(px+kanat*birim*yon, yk,
                       px+kanat*birim*yon, yk+(5*birim if yk == ky0 else -5*birim))  # dudak
            c.restoreState()
        # taşyünü dolgu
        _tarama(c, x0, ky0, x0+boy*birim, ky1, "tasyunu")
        for i in range(n):
            px = x0 + i*DIKME_ARA*1000*birim
            if px > x0+boy*birim: break
            c.saveState(); c.setStrokeColor(C_PROFIL); c.setLineWidth(1.0)
            c.line(px, ky0, px, ky1)
            yon = 1 if i % 2 == 0 else -1
            for yk in (ky0, ky1): c.line(px, yk, px+kanat*birim*yon, yk)
            c.restoreState()
    # ── ölçü zinciri (katman kalınlıkları — solda düşey)
    c.saveState(); c.setStrokeColor(h.NAVY); c.setLineWidth(0.45)
    dx = x0-4*mm
    c.line(dx, y0, dx, y)
    yy = y
    for kal, tip, k_ad in diz:
        hgt = kal*birim
        c.line(dx-1.4*mm, yy, dx+1.4*mm, yy)
        if hgt > 2.6*mm:
            c.saveState(); c.translate(dx-1.6*mm, yy-hgt/2); c.rotate(90)
            h.txt(c, 0, 0, ("%g" % kal).replace(".", ","), h.F, 4.4, h.NAVY, "c")
            c.restoreState()
        yy -= hgt
    c.line(dx-1.4*mm, y0, dx+1.4*mm, y0)
    c.restoreState()
    h.txt(c, dx-7*mm, (y+y0)/2, f"{('%g' % tot).replace('.', ',')}", h.FB, 5.2, h.NAVY, "c")
    # ── dikme aralığı ölçüsü (altta yatay)
    oy = y0-6*mm
    c.saveState(); c.setStrokeColor(h.NAVY); c.setLineWidth(0.45)
    c.line(x0, oy, x0+boy*birim, oy)
    for i in range(int(boy/(DIKME_ARA*1000))+1):
        px = x0+i*DIKME_ARA*1000*birim
        if px > x0+boy*birim+0.01: break
        c.line(px, oy-1.4*mm, px, oy+1.4*mm)
        if i:
            h.txt(c, px-DIKME_ARA*1000*birim/2, oy+1.2*mm, "400", h.F, 4.6, h.NAVY, "c")
    c.restoreState()
    h.txt(c, x0+boy*birim/2, oy-4.6*mm,
          f"C dikme aralığı 400 mm — kapı kenarlarında ve 3,0 m üzeri duvarlarda kutu profil takviye",
          h.F, 4.6, h.GREY, "c")
    # ── başlık ve etiketler
    h.txt(c, x, y+7*mm, f"{kod}  ·  {ad}", h.FB, 7.0, h.NAVY)
    h.txt(c, x+w, y+7*mm, f"toplam {('%g' % tot).replace('.', ',')} mm  ·  "
          f"ölçek 1/{int(1/olcek)}", h.FB, 6.2, h.COPPER, "r")
    # katman açıklamaları — kesitin ALTINDA, iki sütun
    ty = oy-9*mm
    kol = 2; kw = (w-4*mm)/kol
    yk = [ty]*kol
    for i, (kal, tip, k_ad) in enumerate(diz):
        k = 0 if i < (len(diz)+1)//2 else 1
        tx = x + k*kw
        h.txt(c, tx, yk[k], f"{i+1}.", h.FB, 4.8, h.COPPER)
        for ln in h.wrap(c, k_ad, h.F, 4.8, kw-6*mm)[:2]:
            h.txt(c, tx+4.2*mm, yk[k], ln, h.F, 4.8, h.INK); yk[k] -= 2.8*mm
        yk[k] -= 0.6*mm
    ty = min(yk)-1.5*mm
    for ln in h.wrap(c, perf, h.F, 4.8, w):
        h.txt(c, x, ty, ln, h.F, 4.8, h.COPPER); ty -= 2.8*mm
    return ty-3*mm, tot

if __name__ == "__main__":
    print(f"{len(BOLME)} bölme ekseni · toplam {BOLME_UZUNLUK} m · "
          f"{DIKME_ADEDI} adet C50 dikme @400 mm")
    for a, b, tip, t in BOLME:
        print(f"  {tip}  ({a[0]:.2f},{a[1]:.2f}) → ({b[0]:.2f},{b[1]:.2f})  "
              f"L={math.dist(a,b):.2f} m  {len(dikme_noktalari(a,b))} dikme")
