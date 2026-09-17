# -*- coding: utf-8 -*-
"""MEKANİK TESİSAT SEMBOL KÜTÜPHANESİ — TS 2164 §1.13 / ISO 14617 uyumlu.

Şematik çizim kuralları (prensip ve kolon şeması):
  · ölçekli DEĞİLDİR; hatlar YALNIZ yatay ve düşeydir (çapraz yok),
  · akış soldan sağa / alttan yukarı okunur,
  · her boruda akış yönü oku, servis kodu ve çap bulunur,
  · her sembolün anlamı aynı paftadaki lejantta verilir.

Tüm sembol boyutları `u` modülünün katlarıdır (u = 4 mm kâğıt üzerinde).
"""
import math
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
import helpers as h

U = 4*mm                       # temel modül
LW_BORU   = 0.35
LW_GOVDE  = 0.55
LW_IC     = 0.22

INK    = HexColor("#1A2530")
BEYAZ  = HexColor("#FFFFFF")
GRI    = HexColor("#8A939C")
# servis renkleri (TS uygulama pratiği)
C_TS   = HexColor("#2F6FB3")   # temiz su — soğuk
C_SS   = HexColor("#C8322B")   # sıcak su
C_SR   = HexColor("#A04BA0")   # sirkülasyon
C_PS   = HexColor("#4B7A52")   # pis su
C_HV   = HexColor("#8A939C")   # havalık
C_DR   = HexColor("#3C7A6B")   # drenaj / kondens
C_SAG  = HexColor("#A04BA0")   # soğutucu akışkan — gaz
C_SAS  = HexColor("#2F6FB3")   # soğutucu akışkan — sıvı
C_HAVA = HexColor("#2E7D5B")   # hava kanalı

CIZGI = {   # servis: (renk, kesik deseni)
 "TS": (C_TS, None), "SS": (C_SS, (2.6, 1.4)), "SR": (C_SR, (2.6, 1.4, 0.8, 1.4)),
 "PS": (C_PS, None), "HV": (C_HV, (1.4, 1.4)), "DR": (C_DR, (1.4, 1.4)),
 "SA-G": (C_SAG, None), "SA-S": (C_SAS, None), "HAVA": (C_HAVA, None),
}


# ── temel çizim ───────────────────────────────────────────────────────────────
def boru(c, pts, servis="TS", lw=LW_BORU, ok_ara=26*mm):
    """Ortogonal boru hattı. Çapraz segment çizilmez."""
    renk, dash = CIZGI.get(servis, (INK, None))
    c.saveState(); c.setStrokeColor(renk); c.setLineWidth(lw)
    if dash: c.setDash(list(dash), 0)
    for a, b in zip(pts, pts[1:]):
        if abs(a[0]-b[0]) > 1e-9 and abs(a[1]-b[1]) > 1e-9:
            continue                       # çapraz hat çizilmez
        c.line(a[0], a[1], b[0], b[1])
    c.restoreState()
    # akış okları
    c.saveState(); c.setFillColor(renk); c.setStrokeColor(renk)
    for a, b in zip(pts, pts[1:]):
        L = math.hypot(b[0]-a[0], b[1]-a[1])
        if L < 10*mm: continue
        n = max(1, int(L//ok_ara))
        for i in range(n):
            t = (i+0.5)/n
            _ok(c, a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t,
                math.atan2(b[1]-a[1], b[0]-a[0]), renk)
    c.restoreState()


def _ok(c, x, y, aci, renk, boy=2.6*mm, en=1.0*mm):
    p = c.beginPath(); p.moveTo(x+math.cos(aci)*boy/2, y+math.sin(aci)*boy/2)
    for s in (+1, -1):
        p.lineTo(x-math.cos(aci)*boy/2 - s*math.sin(aci)*en,
                 y-math.sin(aci)*boy/2 + s*math.cos(aci)*en)
    p.close(); c.setFillColor(renk); c.drawPath(p, 0, 1)


def etiket(c, x, y, metin, renk=INK, fs=4.8, hiza="c", dy=1.6*mm, kutu=True):
    if kutu:
        gen = len(metin)*fs*0.50
        c.setFillColor(BEYAZ)
        dx = {"c": -gen/2, "l": -1*mm, "r": -gen+1*mm}[hiza]
        c.rect(x+dx, y+dy-1.0*mm, gen, fs*0.95, 0, 1)
    h.txt(c, x, y+dy, metin, h.F, fs, renk, hiza)


# ── armatür sembolleri (TS 2164 / ISO 14617) ─────────────────────────────────
def _papyon(c, x, y, renk=INK, u=U, dikey=False):
    """Vana gövdesi — uç uca iki üçgen."""
    L, Hh = u*2, u*1.5
    c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE); c.setFillColor(BEYAZ)
    p = c.beginPath()
    if dikey:
        p.moveTo(x-Hh/2, y-L/2); p.lineTo(x+Hh/2, y-L/2); p.lineTo(x, y)
        p.lineTo(x-Hh/2, y+L/2); p.lineTo(x+Hh/2, y+L/2); p.lineTo(x, y)
    else:
        p.moveTo(x-L/2, y-Hh/2); p.lineTo(x-L/2, y+Hh/2); p.lineTo(x, y)
        p.lineTo(x+L/2, y+Hh/2); p.lineTo(x+L/2, y-Hh/2); p.lineTo(x, y)
    p.close(); c.drawPath(p, 1, 1)


def _sap(c, x, y, renk=INK, u=U):
    c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    c.line(x, y, x, y+u); c.line(x-u*0.4, y+u, x+u*0.4, y+u)


def kesme_vana(c, x, y, u=U, renk=INK, dikey=False, kod=None):
    _papyon(c, x, y, renk, u, dikey); _sap(c, x, y, renk, u)
    if kod: etiket(c, x, y+u*1.6, kod, renk, 4.2)


def kuresel_vana(c, x, y, u=U, renk=INK, dikey=False, kod=None):
    _papyon(c, x, y, renk, u, dikey)
    c.setFillColor(BEYAZ); c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    c.circle(x, y, u*0.40, 1, 1)
    _sap(c, x, y+u*0.40, renk, u*0.8)
    if kod: etiket(c, x, y+u*1.7, kod, renk, 4.2)


def kelebek_vana(c, x, y, u=U, renk=INK, kod=None):
    c.setFillColor(BEYAZ); c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    c.circle(x, y, u*0.75, 1, 1)
    a = math.radians(60)
    c.line(x-math.cos(a)*u*0.75, y-math.sin(a)*u*0.75,
           x+math.cos(a)*u*0.75, y+math.sin(a)*u*0.75)
    _sap(c, x, y+u*0.75, renk, u*0.8)
    if kod: etiket(c, x, y+u*2.0, kod, renk, 4.2)


def cekvalf(c, x, y, u=U, renk=INK, aci=0.0, kod=None):
    """Akış yönünde dolu üçgen + oturma çubuğu."""
    c.saveState(); c.translate(x, y); c.rotate(math.degrees(aci))
    c.setFillColor(renk); c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    p = c.beginPath(); p.moveTo(u*0.6, 0); p.lineTo(-u*0.6, u*0.6)
    p.lineTo(-u*0.6, -u*0.6); p.close(); c.drawPath(p, 0, 1)
    c.line(u*0.6, -u*0.7, u*0.6, u*0.7)
    c.restoreState()
    if kod: etiket(c, x, y+u*1.1, kod, renk, 4.2)


def balans_vana(c, x, y, u=U, renk=INK, kod="BV"):
    _papyon(c, x, y, renk, u)
    c.setStrokeColor(renk); c.setLineWidth(LW_IC)
    c.line(x-u*1.2, y-u*0.9, x+u*1.2, y+u*0.9)
    _ok(c, x+u*1.0, y+u*0.75, math.atan2(u*0.9*2, u*1.2*2), renk, 2.0*mm, 0.8*mm)
    c.setFillColor(BEYAZ)
    for s in (-1, 1):
        c.circle(x+s*u*1.5, y, u*0.18, 1, 1)
    _sap(c, x, y, renk, u)
    if kod: etiket(c, x, y+u*1.7, kod, renk, 4.2)


def emniyet_ventili(c, x, y, u=U, renk=INK, kod="EV"):
    _papyon(c, x, y, renk, u)
    c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    c.line(x, y, x, y+u*1.2)
    yy = y+u*1.2
    for i in range(5):                       # yay
        c.line(x+(-1)**i*u*0.25, yy+i*u*0.18, x+(-1)**(i+1)*u*0.25, yy+(i+1)*u*0.18)
    if kod: etiket(c, x, y+u*2.6, kod, renk, 4.2)


def pislik_tutucu(c, x, y, u=U, renk=INK, kod="PT"):
    c.setFillColor(BEYAZ); c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    c.rect(x-u*0.8, y-u*0.5, u*1.6, u*1.0, 1, 1)
    c.setLineWidth(LW_IC)
    c.line(x+u*0.8, y-u*0.5, x+u*1.6, y-u*1.3)
    c.line(x+u*1.35, y-u*1.55, x+u*1.85, y-u*1.05)
    if kod: etiket(c, x, y+u*0.8, kod, renk, 4.2)


def pompa(c, x, y, u=U, renk=INK, kod=None, tanim=None):
    c.setFillColor(BEYAZ); c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    c.circle(x, y, u*1.25, 1, 1)
    p = c.beginPath(); p.moveTo(x-u*0.9, y-u*0.7); p.lineTo(x-u*0.9, y+u*0.7)
    p.lineTo(x+u*1.1, y); p.close(); c.setFillColor(h.tint(renk, 0.75)); c.drawPath(p, 1, 1)
    if kod:   etiket(c, x, y-u*2.3, kod, renk, 4.6)
    if tanim: etiket(c, x, y-u*3.1, tanim, GRI, 4.0)


def fan_aksiyel(c, x, y, u=U, renk=INK, kod=None, tanim=None):
    """Aksiyel/kanal tipi fan — daire + göbek + 3 kanat (ISO 14617)."""
    c.setFillColor(BEYAZ); c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    c.circle(x, y, u*1.5, 1, 1)
    c.setLineWidth(LW_IC)
    for k in range(3):
        a0 = math.radians(90 + k*120)
        p = c.beginPath(); p.moveTo(x, y)
        p.lineTo(x+math.cos(a0-0.28)*u*1.35, y+math.sin(a0-0.28)*u*1.35)
        p.lineTo(x+math.cos(a0+0.28)*u*1.35, y+math.sin(a0+0.28)*u*1.35)
        p.close(); c.setFillColor(h.tint(renk, 0.55)); c.drawPath(p, 1, 1)
    c.setFillColor(renk); c.circle(x, y, u*0.28, 0, 1)
    if kod:   etiket(c, x, y-u*2.4, kod, renk, 4.6)
    if tanim: etiket(c, x, y-u*3.2, tanim, GRI, 4.0)


def susturucu(c, x, y, w, hh, renk=INK, kod="SUS"):
    c.setFillColor(BEYAZ); c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    c.rect(x-w/2, y-hh/2, w, hh, 1, 1)
    c.setLineWidth(LW_IC); c.setStrokeColor(h.tint(renk, 0.5))
    n = int(w/(1.6*mm))
    for i in range(n):
        xx = x-w/2+i*1.6*mm
        c.line(xx, y-hh/2, min(xx+hh, x+w/2), min(y+hh/2, y-hh/2+(x+w/2-xx)))
    etiket(c, x, y+hh/2+0.4*mm, kod, renk, 4.2)


def filtre(c, x, y, w, hh, renk=INK, kod="F7"):
    c.setFillColor(BEYAZ); c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    c.rect(x-w/2, y-hh/2, w, hh, 1, 1)
    c.setLineWidth(LW_IC); c.setDash([1.4, 1.2], 0)
    n = 6; adim = w/n
    for i in range(n):
        c.line(x-w/2+i*adim, y-hh/2, x-w/2+(i+0.5)*adim, y+hh/2)
        c.line(x-w/2+(i+0.5)*adim, y+hh/2, x-w/2+(i+1)*adim, y-hh/2)
    c.setDash()
    etiket(c, x, y+hh/2+0.4*mm, kod, renk, 4.2)


def damper(c, x, y, u=U, renk=INK, tip="HKD", dikey=False):
    c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    a = math.radians(45)
    if dikey: a = math.radians(-45)
    c.line(x-math.cos(a)*u, y-math.sin(a)*u, x+math.cos(a)*u, y+math.sin(a)*u)
    c.setFillColor(BEYAZ); c.circle(x, y, u*0.22, 1, 1)
    if tip == "MD":
        c.setFillColor(BEYAZ); c.setStrokeColor(renk); c.setLineWidth(LW_IC)
        c.rect(x-u*0.55, y+u*0.7, u*1.1, u*0.8, 1, 1)
        h.txt(c, x, y+u*0.95, "M", h.FB, 4.0, renk, "c")
    etiket(c, x, y-u*1.8, tip, renk, 4.0)


def yangin_damperi(c, x, y, w, hh, renk=C_SS, kod="YD-90"):
    c.setFillColor(BEYAZ); c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    c.rect(x-w/2, y-hh/2, w, hh, 1, 1)
    c.line(x-w/2, y-hh/2, x+w/2, y+hh/2)
    etiket(c, x, y+hh/2+0.4*mm, kod, renk, 4.0)


def termometre(c, x, y, u=U, renk=INK):
    c.setStrokeColor(renk); c.setLineWidth(LW_IC); c.line(x, y, x, y+u)
    c.setFillColor(BEYAZ); c.setLineWidth(LW_GOVDE); c.circle(x, y+u+u*0.6, u*0.6, 1, 1)
    h.txt(c, x, y+u+u*0.42, "T", h.FB, 4.0, renk, "c")


def manometre(c, x, y, u=U, renk=INK):
    c.setStrokeColor(renk); c.setLineWidth(LW_IC); c.line(x, y, x, y+u)
    c.setFillColor(BEYAZ); c.setLineWidth(LW_GOVDE); c.circle(x, y+u+u*0.6, u*0.6, 1, 1)
    h.txt(c, x, y+u+u*0.42, "P", h.FB, 4.0, renk, "c")


def boyler(c, x, y, w, hh, renk=C_SS, kod="BOYLER 100 L / 3 kW"):
    """Depolu elektrikli boyler — dikey kapsül, içinde rezistans."""
    c.setFillColor(BEYAZ); c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    r = w/2
    p = c.beginPath()
    p.moveTo(x-r, y+hh/2-r*0.55); p.lineTo(x-r, y-hh/2+r*0.55)
    p.curveTo(x-r, y-hh/2, x+r, y-hh/2, x+r, y-hh/2+r*0.55)
    p.lineTo(x+r, y+hh/2-r*0.55)
    p.curveTo(x+r, y+hh/2, x-r, y+hh/2, x-r, y+hh/2-r*0.55)
    p.close(); c.drawPath(p, 1, 1)
    c.setLineWidth(LW_IC); c.setStrokeColor(renk)
    for i in range(5):                       # rezistans
        yy = y-hh*0.28+i*hh*0.09
        c.line(x-r*0.55, yy, x+r*0.55, yy+hh*0.045)
        c.line(x+r*0.55, yy+hh*0.045, x-r*0.55, yy+hh*0.09)
    etiket(c, x, y-hh/2-3.0*mm, kod, renk, 4.4)


def yer_suzgeci(c, x, y, u=U, renk=C_PS, kod="YS Ø100"):
    c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE); c.setFillColor(BEYAZ)
    p = c.beginPath(); p.moveTo(x-u*0.75, y+u*0.4); p.lineTo(x+u*0.75, y+u*0.4)
    p.lineTo(x+u*0.25, y-u*0.4); p.lineTo(x-u*0.25, y-u*0.4); p.close()
    c.drawPath(p, 1, 1)
    c.setLineWidth(LW_IC)
    p = c.beginPath(); p.moveTo(x, y-u*0.4)
    p.curveTo(x-u*0.6, y-u*0.8, x+u*0.6, y-u*1.2, x, y-u*1.5)
    c.drawPath(p, 1, 0)
    if kod: etiket(c, x+u*1.0, y, kod, renk, 4.0, "l", 0)


def temizleme_kapagi(c, x, y, u=U, renk=C_PS, kod="TK"):
    c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    c.line(x, y, x+u*0.9, y+u*0.9)
    c.line(x+u*0.65, y+u*1.15, x+u*1.15, y+u*0.65)
    etiket(c, x+u*1.5, y+u*0.9, kod, renk, 4.0, "l", 0)


def havalik_bacasi(c, x, y, u=U, renk=C_HV):
    c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    c.line(x-u*0.8, y, x+u*0.8, y)
    c.line(x-u*0.5, y, x-u*0.5, y-u*0.35)
    c.line(x+u*0.5, y, x+u*0.5, y-u*0.35)


def klima_ic(c, x, y, w, hh, renk=C_SAG, kod="K1", tanim=None):
    c.setFillColor(BEYAZ); c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    c.rect(x-w/2, y-hh/2, w, hh, 1, 1)
    c.setLineWidth(LW_IC); c.line(x-w/2, y-hh/2, x+w/2, y+hh/2)
    _ok(c, x, y-hh/2-1.4*mm, -math.pi/2, renk)
    etiket(c, x, y+hh/2+0.6*mm, kod, renk, 4.4)
    if tanim: etiket(c, x, y+hh/2+4.2*mm, tanim, GRI, 3.9)


def klima_dis(c, x, y, w, hh, renk=C_SAG, kod="DIŞ ÜNİTE"):
    c.setFillColor(BEYAZ); c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    c.rect(x-w/2, y-hh/2, w, hh, 1, 1)
    for s in (-1, 1):
        c.setLineWidth(LW_IC); c.circle(x+s*w*0.22, y, min(hh, w)*0.26, 0, 0)
        for k in range(3):
            a = math.radians(k*120)
            c.line(x+s*w*0.22, y,
                   x+s*w*0.22+math.cos(a)*min(hh, w)*0.26,
                   y+math.sin(a)*min(hh, w)*0.26)
    etiket(c, x, y+hh/2+0.6*mm, kod, renk, 4.4)


def kolektor(c, x, y, w, hh, renk=INK, kod=None):
    c.setFillColor(BEYAZ); c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    c.roundRect(x-w/2, y-hh/2, w, hh, hh/2, 1, 1)
    if kod: etiket(c, x, y+hh/2+0.6*mm, kod, renk, 4.4)


def sayac(c, x, y, u=U, renk=C_TS, kod="SU SAYACI"):
    c.setFillColor(BEYAZ); c.setStrokeColor(renk); c.setLineWidth(LW_GOVDE)
    c.circle(x, y, u*0.75, 1, 1)
    h.txt(c, x, y-0.6*mm, "M", h.FB, 4.4, renk, "c")
    if kod: etiket(c, x, y+u*1.1, kod, renk, 4.0)


# ── lejant ────────────────────────────────────────────────────────────────────
def lejant(c, x, y, w, kalemler, baslik="LEJANT — TESİSAT SEMBOLLERİ", sut=2):
    """kalemler: [(çizim_fn(c, cx, cy), metin)]"""
    h.txt(c, x, y, baslik, h.FB, 7.5, h.NAVY)
    y -= 6*mm
    sw = w/sut; adim = 7.0*mm
    for i, (fn, metin) in enumerate(kalemler):
        cx = x + (i % sut)*sw + 5*mm
        cy = y - (i // sut)*adim
        try: fn(c, cx, cy)
        except Exception: pass
        h.txt(c, cx+9*mm, cy-1.0*mm, metin, h.F, 5.4, h.INK)
    return y - ((len(kalemler)+sut-1)//sut)*adim - 3*mm
