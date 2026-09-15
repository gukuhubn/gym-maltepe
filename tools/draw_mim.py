# -*- coding: utf-8 -*-
"""Mimari çizim ilkelleri — kesit / görünüş / detay motoru."""
import math
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
import helpers as h

# ── malzeme paleti (katman taraması) ───────────────────────────────────────────
MAT = {
 "beton":   ("#C9CCD1", "#8A8F98", "beton"),
 "sap":     ("#E2E0DA", "#A9A69D", "nokta"),
 "kaucuk":  ("#3A3F46", "#1C1C1C", "yok"),
 "sunger":  ("#F0D9C2", "#C9A27E", "dalga"),
 "lvt":     ("#C9A063", "#8C6A3A", "yok"),
 "yalitim": ("#7FB0D8", "#2F6FB3", "yok"),
 "seramik": ("#9FB8C4", "#5E7B8B", "cizgi"),
 "ahsap":   ("#D8B98C", "#9A7845", "egik"),
 "alcipan": ("#F2EFE8", "#B9B4A8", "nokta"),
 "tasyunu": ("#FBE6A8", "#C9A227", "dalga"),
 "profil":  ("#B7BCC4", "#6B7078", "yok"),
 "ayna":    ("#D6E6F2", "#5E8FB5", "yok"),
 "cam":     ("#DCEBF5", "#3E8ACC", "yok"),
 "toprak":  ("#D8CDBC", "#9A8E79", "egik"),
}
C_KESIT   = HexColor("#1C1C1C")     # kesilen eleman konturu
C_GORUNUS = HexColor("#8A8F98")     # arkada görünen
C_KOT     = HexColor("#16273D")

# ══ KESİT / GÖRÜNÜŞ GÖRÜNTÜSÜ ══════════════════════════════════════════════════
class KV:
    """s = hat boyunca yatay mesafe (m) · z = kot (m)"""
    def __init__(self, c, x, y, w, hgt, s0, s1, z0, z1, pad=9*mm):
        self.c = c; self.s0 = s0; self.z0 = z0
        gw, gh = (s1-s0), (z1-z0)
        self.s = min((w-2*pad)/gw, (hgt-2*pad)/gh)
        self.ox = x + (w-gw*self.s)/2 - s0*self.s
        self.oy = y + pad*0.9 - z0*self.s
        self.x, self.y, self.w, self.h = x, y, w, hgt
    def p(self, s, z): return (self.ox+s*self.s, self.oy+z*self.s)
    def m(self, d):    return d*self.s

def kutu(v, s0, z0, s1, z1, mat="beton", kontur=C_KESIT, lw=0.8):
    """Kesilen dikdörtgen eleman — malzeme taramalı."""
    c = v.c; x0, y0 = v.p(s0, z0); x1, y1 = v.p(s1, z1)
    if x1 < x0: x0, x1 = x1, x0
    if y1 < y0: y0, y1 = y1, y0
    fill, cizgi, tip = MAT.get(mat, MAT["beton"])
    c.saveState()
    c.setFillColor(HexColor(fill)); c.rect(x0, y0, x1-x0, y1-y0, 0, 1)
    c.rect(x0, y0, x1-x0, y1-y0, 0, 0)
    p = c.beginPath(); p.rect(x0, y0, x1-x0, y1-y0); c.clipPath(p, 0, 0)
    c.setStrokeColor(HexColor(cizgi)); c.setLineWidth(0.35)
    w_, hh = x1-x0, y1-y0
    if tip == "egik":
        d = 1.5*mm
        for i in range(int((w_+hh)/d)+1):
            c.line(x0+i*d, y0, x0+i*d-hh, y0+hh)
    elif tip == "beton":
        d = 2.4*mm
        for i in range(int((w_+hh)/d)+1):
            c.line(x0+i*d, y0, x0+i*d-hh, y0+hh)
        c.setFillColor(HexColor(cizgi))
        for i in range(int(w_/(3.2*mm))+1):
            for j in range(int(hh/(3.2*mm))+1):
                c.circle(x0+1.4*mm+i*3.2*mm, y0+1.0*mm+j*3.2*mm, 0.28*mm, 0, 1)
    elif tip == "nokta":
        c.setFillColor(HexColor(cizgi))
        d = 1.5*mm
        for i in range(int(w_/d)+1):
            for j in range(int(hh/d)+1):
                c.circle(x0+0.7*mm+i*d+(0.75*mm if j % 2 else 0), y0+0.7*mm+j*d, 0.22*mm, 0, 1)
    elif tip == "cizgi":
        d = 1.2*mm
        for j in range(int(hh/d)+1): c.line(x0, y0+j*d, x1, y0+j*d)
    elif tip == "dalga":
        d = 1.6*mm
        for j in range(int(hh/d)+1):
            yy = y0+j*d; pth = c.beginPath(); pth.moveTo(x0, yy); k = 0
            while x0+k*1.2*mm < x1:
                pth.curveTo(x0+(k+0.3)*1.2*mm, yy+0.55*mm, x0+(k+0.7)*1.2*mm, yy-0.55*mm,
                            x0+(k+1)*1.2*mm, yy); k += 1
            c.drawPath(pth, 1, 0)
    c.restoreState()
    if kontur:
        c.saveState(); c.setStrokeColor(kontur); c.setLineWidth(lw)
        c.rect(x0, y0, x1-x0, y1-y0, 1, 0); c.restoreState()

def cizgi(v, a, b, col=C_KESIT, lw=0.7, dash=None):
    c = v.c; c.saveState(); c.setStrokeColor(col); c.setLineWidth(lw)
    if dash: c.setDash(dash)
    c.line(*v.p(*a), *v.p(*b)); c.restoreState()

def gorunus_kutu(v, s0, z0, s1, z1, fill=None, kontur=C_GORUNUS, lw=0.55, dash=None):
    """Kesit düzleminin arkasında görünen eleman."""
    c = v.c; x0, y0 = v.p(s0, z0); x1, y1 = v.p(s1, z1)
    c.saveState(); c.setLineWidth(lw)
    if dash: c.setDash(dash)
    if fill: c.setFillColor(fill)
    c.setStrokeColor(kontur)
    c.rect(min(x0,x1), min(y0,y1), abs(x1-x0), abs(y1-y0), 1, 1 if fill else 0)
    c.restoreState()

# ── kot işareti ────────────────────────────────────────────────────────────────
def kot(v, s, z, etiket=None, yon=1, uzun=0.0):
    """Üçgen kot işareti + ±0,00 biçiminde etiket."""
    c = v.c; x, y = v.p(s, z); r = 1.5*mm
    if uzun:
        c.saveState(); c.setStrokeColor(HexColor("#B9BEC6")); c.setLineWidth(0.4)
        c.setDash(3, 2); c.line(x, y, *v.p(s+uzun*yon, z)); c.restoreState()
    c.saveState(); c.setFillColor(C_KOT); c.setStrokeColor(C_KOT); c.setLineWidth(0.5)
    p = c.beginPath(); p.moveTo(x, y); p.lineTo(x-r, y+r*1.7); p.lineTo(x+r, y+r*1.7); p.close()
    c.drawPath(p, 1, 1); c.restoreState()
    if etiket is None:
        etiket = "±0,00" if abs(z) < 0.005 else ("%+.2f" % z).replace(".", ",")
    h.txt(c, x+r+1.2*mm if yon > 0 else x-r-1.2*mm, y+r*1.9+0.4*mm, etiket,
          h.FB, 5.4, C_KOT, "l" if yon > 0 else "r")

# ── yatay ölçü zinciri ─────────────────────────────────────────────────────────
def olcu_zinciri(v, z, noktalar, s=4.9, col=C_KOT, etiketler=None):
    c = v.c; c.saveState(); c.setStrokeColor(col); c.setLineWidth(0.45)
    y = v.p(0, z)[1]
    for i, sv in enumerate(noktalar):
        x = v.p(sv, z)[0]
        c.line(x, y-1.6*mm, x, y+1.6*mm)
    c.line(v.p(noktalar[0], z)[0], y, v.p(noktalar[-1], z)[0], y)
    for i in range(len(noktalar)-1):
        a, b = noktalar[i], noktalar[i+1]
        t = etiketler[i] if etiketler else ("%.2f" % (b-a)).replace(".", ",")
        if v.m(b-a) > 6*mm:
            h.txt(c, (v.p(a, z)[0]+v.p(b, z)[0])/2, y+1.0*mm, t, h.F, s, col, "c")
    c.restoreState()

def kot_zinciri(v, s, kotlar, yon=1, fs=4.9, col=C_KOT):
    """Düşey kot zinciri (kesitin kenarında)."""
    c = v.c; c.saveState(); c.setStrokeColor(col); c.setLineWidth(0.45)
    x = v.p(s, 0)[0]
    ks = sorted(kotlar)
    c.line(x, v.p(s, ks[0])[1], x, v.p(s, ks[-1])[1])
    for z in ks:
        y = v.p(s, z)[1]; c.line(x-1.6*mm, y, x+1.6*mm, y)
    for i in range(len(ks)-1):
        a, b = ks[i], ks[i+1]
        if v.m(b-a) > 5*mm:
            c.saveState(); c.translate(x-1.0*mm, (v.p(s, a)[1]+v.p(s, b)[1])/2); c.rotate(90)
            h.txt(c, 0, 0, ("%.2f" % (b-a)).replace(".", ","), h.F, fs, col, "c"); c.restoreState()
    c.restoreState()

# ── kılavuz çizgili etiket (leader) ────────────────────────────────────────────
def kilavuz(c, x0, y0, x1, y1, metin, fs=5.6, col=h.INK, al="l", kalin=False,
            nokta=True, w=None):
    c.saveState(); c.setStrokeColor(HexColor("#6B7078")); c.setLineWidth(0.4)
    c.line(x0, y0, x1, y1)
    if nokta:
        c.setFillColor(HexColor("#6B7078")); c.circle(x0, y0, 0.55*mm, 0, 1)
    c.restoreState()
    dx = 1.4*mm if al == "l" else -1.4*mm
    if w:
        lines = h.wrap(c, metin, h.FB if kalin else h.F, fs, w)
        yy = y1 + (len(lines)-1)*(fs*0.36*mm)/1 * 0.0 + (len(lines)-1)*1.55*mm/1 * 0.0
        yy = y1 + (len(lines)-1)*1.9*mm/2
        for ln in lines:
            h.txt(c, x1+dx, yy-0.7*mm, ln, h.FB if kalin else h.F, fs, col, al); yy -= 3.0*mm
    else:
        h.txt(c, x1+dx, y1-0.7*mm, metin, h.FB if kalin else h.F, fs, col, al)

# ── kesit / görünüş baloncuğu (plan üzerinde) ──────────────────────────────────
def kesit_isareti(v, a, b, ad, yon=1):
    """Plan üzerinde kesit hattı ve yön okları (draw.View ile kullanılır)."""
    c = v.c; ax, ay = v.p(a); bx, by = v.p(b)
    c.saveState(); c.setStrokeColor(HexColor("#C8322B")); c.setLineWidth(1.0)
    c.setDash([6, 2.5, 1.5, 2.5], 0); c.line(ax, ay, bx, by); c.restoreState()
    ang = math.degrees(math.atan2(by-ay, bx-ax))
    for (px, py), sgn in (((ax, ay), 1), ((bx, by), -1)):
        c.saveState(); c.translate(px, py); c.rotate(ang)
        c.setFillColor(HexColor("#C8322B")); c.setStrokeColor(HexColor("#C8322B"))
        c.circle(0, 0, 3.0*mm, 0, 1)
        p = c.beginPath(); p.moveTo(sgn*3.0*mm, 0); p.lineTo(sgn*6.6*mm, 2.0*mm)
        p.lineTo(sgn*6.6*mm, -2.0*mm); p.close(); c.drawPath(p, 0, 1)
        c.restoreState()
        h.txt(c, px, py-1.15*mm, ad.split("-")[0], h.FB, 5.6, HexColor("#FFFFFF"), "c")

def balon(c, x, y, metin, r=2.6*mm, dolgu="#FFFFFF", kontur="#16273D", fs=5.2):
    c.saveState(); c.setFillColor(HexColor(dolgu)); c.setStrokeColor(HexColor(kontur))
    c.setLineWidth(0.7); c.circle(x, y, r, 1, 1); c.restoreState()
    h.txt(c, x, y-fs*0.36, metin, h.FB, fs, HexColor(kontur), "c")

# ══ KATMAN ŞEMASI (düşey ölçek büyütülmüş) ════════════════════════════════════
def katman_detay(c, x, y, w, katmanlar, yukseklik, baslik=None, fs=5.2, min_ara=3.35):
    """katmanlar: [(ad, mm, mat)] alttan üste. Şeridi verilen yüksekliğe sığdırır,
    etiketleri üst üste binmeyecek şekilde açar ve kılavuz çizgisi ile bağlar.
    Döner: (en_alt_y, olcek_metni)"""
    katmanlar = [k for k in katmanlar if k[1] > 0]
    toplam = sum(k[1] for k in katmanlar)
    gerekli = max(len(katmanlar)*min_ara, 12*mm)
    hgt = min(yukseklik, max(gerekli, yukseklik*0.92))
    px_per_mm = hgt/(toplam*mm) if toplam else 1.0
    # okunur bir ölçek seç (1/1, 1/2, 1/5, 1/10)
    for bol, ad in ((1, "1/1"), (2, "1/2"), (5, "1/5"), (10, "1/10")):
        if toplam/bol*mm <= hgt: px_per_mm = (1.0/bol); olcek_ad = ad; break
    else:
        px_per_mm = hgt/(toplam*mm); olcek_ad = "şematik"
    kul = toplam*px_per_mm*mm
    genislik = w*0.30
    # ── şerit
    yy = y
    dilim = []
    for ad, kal, mat in reversed(katmanlar):
        dh = max(kal*px_per_mm*mm, 0.9*mm)
        fill, cz, tip = MAT.get(mat, MAT["beton"])
        c.saveState(); c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor(cz))
        c.setLineWidth(0.5); c.rect(x, yy-dh, genislik, dh, 1, 1)
        if tip in ("egik", "beton"):
            p_ = c.beginPath(); p_.rect(x, yy-dh, genislik, dh); c.clipPath(p_, 0, 0)
            c.setLineWidth(0.3); d = 1.5*mm
            for i in range(int((genislik+dh)/d)+1):
                c.line(x+i*d, yy-dh, x+i*d-dh, yy)
        c.restoreState()
        dilim.append((ad, kal, yy-dh/2, yy, yy-dh)); yy -= dh
    alt = yy
    c.saveState(); c.setStrokeColor(HexColor("#1C1C1C")); c.setLineWidth(1.1)
    c.line(x-2.5*mm, alt, x+genislik+2.5*mm, alt)
    c.setLineWidth(0.8); c.rect(x, alt, genislik, y-alt, 0, 0); c.restoreState()
    # ── etiket konumlarını aç (üstten aşağı, en az min_ara)
    hedef = [d[2] for d in dilim]
    for i in range(1, len(hedef)):
        if hedef[i-1]-hedef[i] < min_ara: hedef[i] = hedef[i-1]-min_ara
    kaydir = 0
    if hedef and hedef[0] > y: kaydir = y-hedef[0]
    hedef = [t+kaydir for t in hedef]
    tx = x+genislik+9*mm
    for (ad, kal, cy_, ust, altk), ty in zip(dilim, hedef):
        c.saveState(); c.setStrokeColor(HexColor("#6B7078")); c.setLineWidth(0.4)
        p_ = c.beginPath(); p_.moveTo(x+genislik, cy_); p_.lineTo(x+genislik+5*mm, ty)
        p_.lineTo(tx-1.2*mm, ty); c.drawPath(p_, 1, 0)
        c.setFillColor(HexColor("#6B7078")); c.circle(x+genislik, cy_, 0.5*mm, 0, 1)
        c.restoreState()
        t = ad if kal == 0 else f"{ad} — {('%g' % kal).replace('.', ',')} mm"
        ln = h.wrap(c, t, h.F, fs, w-(tx-x)-1*mm)
        h.txt(c, tx, ty-fs*0.34, ln[0], h.F, fs, h.INK)
        if len(ln) > 1:
            h.txt(c, tx, ty-fs*0.34-2.7*mm, " ".join(ln[1:]), h.F, fs, h.INK)
    # ── toplam ölçüsü (solda)
    c.saveState(); c.setStrokeColor(C_KOT); c.setLineWidth(0.5)
    dx = x-4.5*mm
    c.line(dx, alt, dx, y); c.line(dx-1.4*mm, alt, dx+1.4*mm, alt)
    c.line(dx-1.4*mm, y, dx+1.4*mm, y)
    c.translate(dx-1.2*mm, (alt+y)/2); c.rotate(90)
    h.txt(c, 0, 0, f"toplam {('%g' % toplam).replace('.', ',')} mm", h.FB, 5.0, C_KOT, "c")
    c.restoreState()
    return alt, olcek_ad


def etiket_sutunu(c, tx, ust, alt, genislik, ogeler, fs=5.1, ara=None):
    """ogeler: [(ankraj_x, ankraj_y, metin)] — etiketleri tx sütununda eşit aralıkla
    dağıtır ve kırık kılavuz çizgisiyle ankraja bağlar."""
    n = len(ogeler)
    if not n: return alt
    ogeler = sorted(ogeler, key=lambda o: -o[1])
    ara = ara or min(7.0*mm, max(3.6*mm, (ust-alt)/max(n-1, 1)))
    ys = [ust - i*ara for i in range(n)]
    for (ax, ay, metin), ty in zip(ogeler, ys):
        c.saveState(); c.setStrokeColor(HexColor("#6B7078")); c.setLineWidth(0.4)
        p = c.beginPath(); p.moveTo(ax, ay)
        p.lineTo(ax+(tx-ax)*0.40, ay); p.lineTo(tx-1.6*mm, ty); c.drawPath(p, 1, 0)
        c.setFillColor(HexColor("#6B7078")); c.circle(ax, ay, 0.5*mm, 0, 1); c.restoreState()
        lns = h.wrap(c, metin, h.F, fs, genislik)
        yy = ty
        for ln in lns[:2]:
            h.txt(c, tx, yy-fs*0.34, ln, h.F, fs, h.INK); yy -= 2.8*mm
    return ys[-1]
