# -*- coding: utf-8 -*-
"""Sayfa mobilyasi: fontlar, renkler, baslik bandi, tablo, kutucuk."""
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor, Color
from reportlab.lib.units import mm
import proj as P

FONTS = {"R":"/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
         "B":"/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "M":"/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"}
def register():
    pdfmetrics.registerFont(TTFont("DJ",  FONTS["R"]))
    pdfmetrics.registerFont(TTFont("DJB", FONTS["B"]))
    pdfmetrics.registerFont(TTFont("DJM", FONTS["M"]))
register()
F, FB, FM = "DJ", "DJB", "DJM"

NAVY   = HexColor("#16273D"); NAVY2 = HexColor("#24405F")
COPPER = HexColor("#B87333"); COPPER_L = HexColor("#E8CDAE")
INK    = HexColor("#1C1C1C"); GREY  = HexColor("#8A8F98")
GREY_L = HexColor("#E7E9EC"); PAPER = HexColor("#FBFAF8")
RED    = HexColor("#C8322B"); BLUE  = HexColor("#2F6FB3"); GREEN = HexColor("#2E7D5B")
AMBER  = HexColor("#D79A1E")
RISK   = {"K":RED, "S":AMBER, "Y":GREEN}       # Kırmızı / Sarı / Yeşil

def TR_UP(s):
    return s.replace("i","İ").replace("ı","I").upper()

def tint(c, f):
    return Color(c.red+(1-c.red)*f, c.green+(1-c.green)*f, c.blue+(1-c.blue)*f)

def tw(c, t, f, s):   # text width
    return c.stringWidth(t, f, s)

def txt(c, x, y, t, f=F, s=8, col=INK, al="l"):
    c.setFont(f, s); c.setFillColor(col)
    if   al=="l": c.drawString(x, y, t)
    elif al=="c": c.drawCentredString(x, y, t)
    else:         c.drawRightString(x, y, t)

def wrap(c, t, f, s, w):
    out, line = [], ""
    for word in t.split():
        trial = (line+" "+word).strip()
        if tw(c, trial, f, s) <= w: line = trial
        else: out.append(line); line = word
    if line: out.append(line)
    return out

def para(c, x, y, t, w, f=F, s=8, col=INK, lead=None):
    lead = lead or s*1.35
    for i, ln in enumerate(wrap(c, t, f, s, w)):
        txt(c, x, y-i*lead, ln, f, s, col)
    return y - len(wrap(c, t, f, s, w))*lead

def band(c, W, H, no, baslik, ustbaslik=None):
    """Navy üst bant + copper ince şerit."""
    hb = 17*mm
    c.setFillColor(NAVY);  c.rect(0, H-hb, W, hb, 0, 1)
    c.setFillColor(COPPER); c.rect(0, H-hb-1.6*mm, W, 1.6*mm, 0, 1)
    txt(c, 12*mm, H-9.4*mm, TR_UP(baslik), FB, 13, HexColor("#FFFFFF"))
    if ustbaslik:
        txt(c, 12*mm, H-14.2*mm, ustbaslik, F, 7, COPPER_L)
    txt(c, W-12*mm, H-9.4*mm, f"{no:02d}", FB, 15, COPPER, "r")
    txt(c, W-12*mm, H-14.2*mm, P.KISA+" · "+P.REV, F, 6.5, COPPER_L, "r")

def footer(c, W, no, toplam):
    c.setStrokeColor(GREY_L); c.setLineWidth(0.5)
    c.line(12*mm, 10.5*mm, W-12*mm, 10.5*mm)
    txt(c, 12*mm, 6.8*mm, P.ALTBILGI, F, 5.8, GREY)
    txt(c, W-12*mm, 6.8*mm, f"{P.TARIH}  ·  Sayfa {no} / {toplam}", F, 5.8, GREY, "r")

def kutu(c, x, y, w, h, fill=None, stroke=GREY_L, lw=0.6, r=1.6*mm):
    if fill: c.setFillColor(fill)
    c.setStrokeColor(stroke); c.setLineWidth(lw)
    c.roundRect(x, y, w, h, r, stroke=1 if stroke else 0, fill=1 if fill else 0)

def kpi(c, x, y, w, h, ust, deger, alt, acc=COPPER):
    kutu(c, x, y, w, h, PAPER, GREY_L)
    c.setFillColor(acc); c.rect(x, y, 2.2*mm, h, 0, 1)
    txt(c, x+6*mm, y+h-6.2*mm, TR_UP(ust), FB, 6.2, GREY)
    txt(c, x+6*mm, y+h-15*mm, deger, FB, 15, NAVY)
    for i, ln in enumerate(wrap(c, alt, F, 6.2, w-9*mm)[:2]):
        txt(c, x+6*mm, y+h-20.5*mm-i*3.1*mm, ln, F, 6.2, GREY)

def kart(c, x, y, w, h, no, baslik, govde, acc=COPPER):
    kutu(c, x, y, w, h, PAPER, GREY_L)
    c.setFillColor(acc); c.circle(x+7*mm, y+h-7*mm, 3.4*mm, 0, 1)
    txt(c, x+7*mm, y+h-8.6*mm, no, FB, 7.5, HexColor("#FFFFFF"), "c")
    txt(c, x+13.5*mm, y+h-8.6*mm, TR_UP(baslik), FB, 7.6, NAVY)
    para(c, x+5*mm, y+h-15.5*mm, govde, w-10*mm, F, 6.6, INK, 8.6)

def tablo(c, x, y, cols, rows, w, satir_h=6.2*mm, bas_h=7.4*mm,
          fs=6.6, hfs=6.4, zebra=True, renkli_sutun=None, hizala=None,
          bg=None, ink=None):
    """cols: [(baslik, oran)] ; rows: [[hucre,...]] ; renkli_sutun: {idx: fn(row)->color}"""
    tot = sum(o for _, o in cols); xs = []; cx = x
    for _, o in cols: xs.append(cx); cx += w*o/tot
    c.setFillColor(NAVY); c.rect(x, y-bas_h, w, bas_h, 0, 1)
    for i, (h_, o) in enumerate(cols):
        al = (hizala or ["l"]*len(cols))[i]
        px = xs[i]+1.8*mm if al=="l" else (xs[i]+w*o/tot-1.8*mm if al=="r" else xs[i]+w*o/tot/2)
        txt(c, px, y-bas_h+2.4*mm, TR_UP(h_), FB, hfs, HexColor("#FFFFFF"), al)
    yy = y-bas_h
    for r, row in enumerate(rows):
        n = max(1, max(len(wrap(c, str(cell), F, fs, w*cols[i][1]/tot-3.6*mm))
                       for i, cell in enumerate(row)))
        rh = max(satir_h, n*fs*1.28+2.6*mm)
        if bg is not None:
            c.setFillColor(bg); c.rect(x, yy-rh, w, rh, 0, 1)
        if zebra and r % 2 == 0:
            c.setFillColor(tint(bg, 0.10) if bg is not None else HexColor("#F4F5F7"))
            c.rect(x, yy-rh, w, rh, 0, 1)
        if renkli_sutun:
            for i, fn in renkli_sutun.items():
                col = fn(row)
                if col:
                    c.setFillColor(col); c.rect(xs[i], yy-rh, w*cols[i][1]/tot, rh, 0, 1)
        for i, cell in enumerate(row):
            al = (hizala or ["l"]*len(cols))[i]
            cw = w*cols[i][1]/tot
            lines = wrap(c, str(cell), F, fs, cw-3.6*mm)
            for j, ln in enumerate(lines):
                px = xs[i]+1.8*mm if al=="l" else (xs[i]+cw-1.8*mm if al=="r" else xs[i]+cw/2)
                col = ink or INK
                if renkli_sutun and i in renkli_sutun:
                    fc = renkli_sutun[i](row)
                    if fc is not None:
                        lum = 0.299*fc.red + 0.587*fc.green + 0.114*fc.blue
                        col = HexColor("#FFFFFF") if lum < 0.55 else INK
                txt(c, px, yy-rh+rh-fs*1.28-j*fs*1.28+0.6*mm, ln, F, fs, col, al)
        c.setStrokeColor(GREY_L); c.setLineWidth(0.4); c.line(x, yy-rh, x+w, yy-rh)
        yy -= rh
    c.setStrokeColor(GREY_L); c.setLineWidth(0.5); c.rect(x, yy, w, y-yy, 0, 0)
    return yy

def lejant(c, x, y, items, s=6.2, dx=None):
    cx = x
    for col, lbl in items:
        c.setFillColor(col); c.rect(cx, y, 3.2*mm, 3.2*mm, 0, 1)
        txt(c, cx+4.4*mm, y+0.7*mm, lbl, F, s, INK)
        cx += (dx or (tw(c, lbl, F, s)+11*mm))
    return cx

def tl(x, dec=0):
    return f"{x:,.{dec}f}".replace(",", "␣").replace(".", ",").replace("␣", ".")

def bant(x1, x2):
    return f"{tl(x1)} – {tl(x2)} TL"

def notkutu(c, x, y, w, baslik, metin, fs=6.4, acc=COPPER, bg=None, lead=None,
            baslik_fs=7.4, pad=5*mm, ink=None):
    """İçeriğe göre yüksekliği hesaplanan not kutusu. Üst kenarı y, alt kenarı döner."""
    lead = lead or fs*1.38
    lines = wrap(c, metin, F, fs, w-2*pad)
    hgt = pad + (baslik_fs*1.5 if baslik else 0) + len(lines)*lead + pad*0.7
    kutu(c, x, y-hgt, w, hgt, bg or tint(acc, 0.93), acc)
    yy = y-pad-(baslik_fs if baslik else 0)
    if baslik:
        txt(c, x+pad, yy, TR_UP(baslik), FB, baslik_fs, acc); yy -= baslik_fs*0.8
    for ln in lines:
        yy -= lead; txt(c, x+pad, yy, ln, F, fs, ink or INK)
    return y-hgt

def madde_listesi(c, x, y, w, maddeler, fs=6.3, lead=8.4, isaret="•", acc=COPPER):
    for m in maddeler:
        txt(c, x, y, isaret, FB, fs, acc)
        y = para(c, x+3.6*mm, y, m, w-3.6*mm, F, fs, INK, lead) - lead*0.35
    return y
