# -*- coding: utf-8 -*-
"""Plan cizim motoru — metre koordinatlari -> sayfa koordinatlari."""
import math
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
import proj as P, helpers as h

DUVAR_T   = 0.20                      # mevcut duvar kalinligi (m)
C_DUVAR   = HexColor("#6B7078")       # mevcut = gri
C_YENI    = HexColor("#C8322B")       # yeni   = kirmizi
C_KALK    = HexColor("#2F6FB3")       # kaldirilan = mavi
C_CEPHE   = HexColor("#3E8ACC")
C_SERAMIK = HexColor("#9FB8C4")
C_EK      = HexColor("#2B2B2B")

class View:
    def __init__(self, c, x, y, w, hgt, pad=6*mm, geoms=None):
        self.c=c; self.x=x; self.y=y; self.w=w; self.h=hgt
        gs = geoms or [P.SALON, P.ERKEK, P.KADIN]
        b  = unary_union(gs).buffer(DUVAR_T).bounds
        gw, gh = b[2]-b[0], b[3]-b[1]
        self.s = min((w-2*pad)/gw, (hgt-2*pad)/gh)
        self.ox = x + (w - gw*self.s)/2 - b[0]*self.s
        self.oy = y + (hgt - gh*self.s)/2 - b[1]*self.s
    def p(self, pt):  return (self.ox+pt[0]*self.s, self.oy+pt[1]*self.s)
    def m(self, d):   return d*self.s

def poly(v, g, fill=None, stroke=None, lw=0.5, alpha=1.0, dash=None):
    if g.is_empty: return
    gs = list(g.geoms) if g.geom_type.startswith("Multi") else [g]
    c=v.c
    for gg in gs:
        if gg.geom_type!="Polygon" or gg.is_empty: continue
        c.saveState()
        if alpha<1: c.setFillAlpha(alpha); c.setStrokeAlpha(alpha)
        pth=c.beginPath(); ext=list(gg.exterior.coords)
        pth.moveTo(*v.p(ext[0]))
        for pt in ext[1:]: pth.lineTo(*v.p(pt))
        pth.close()
        for ring in gg.interiors:
            r=list(ring.coords); pth.moveTo(*v.p(r[0]))
            for pt in r[1:]: pth.lineTo(*v.p(pt))
            pth.close()
        if fill:   c.setFillColor(fill)
        if stroke: c.setStrokeColor(stroke); c.setLineWidth(lw)
        if dash:   c.setDash(dash)
        c.drawPath(pth, stroke=1 if stroke else 0, fill=1 if fill else 0)
        c.restoreState()

def line(v, a, b, col=h.INK, lw=0.6, dash=None):
    c=v.c; c.saveState(); c.setStrokeColor(col); c.setLineWidth(lw)
    if dash: c.setDash(dash)
    c.line(*v.p(a), *v.p(b)); c.restoreState()

def etiket(v, pt, t, s=6.0, col=h.INK, f=h.F, al="c", dy=0):
    x,y=v.p(pt); h.txt(v.c, x, y+dy, t, f, s, col, al)

# ── kabuk ────────────────────────────────────────────────────────────────────
def kabuk(v, duvar_col=C_DUVAR):
    ic  = unary_union([P.SALON, P.ERKEK, P.KADIN])
    dis = ic.buffer(DUVAR_T, join_style=2)
    poly(v, dis.difference(ic), fill=duvar_col)
    poly(v, ic, stroke=HexColor("#3A3F46"), lw=0.7)

def ic_bolme(v, col=C_YENI, lw=0.0):
    """salon / soyunma bloklari arasindaki bolme + blok ici bolmeler"""
    t=0.10
    seg=[]
    for blok in (P.ERKEK, P.KADIN):
        seg.append(blok.exterior.intersection(P.SALON.buffer(0.26)))
    def _bnd(g):
        return unary_union([gg.exterior for gg in (g.geoms if g.geom_type.startswith("Multi") else [g])
                            if gg.geom_type=="Polygon"])
    for ad,d in P.ISLAK.items():
        seg.append(_bnd(d["soyunma"]).intersection(d["dus"].union(d["wc"]).buffer(0.02)))
        seg.append(_bnd(d["dus"]).intersection(d["wc"].buffer(0.02)))
    for s in seg:
        if s.is_empty: continue
        poly(v, s.buffer(t/2, cap_style=2, join_style=2), fill=col)

def cephe(v):
    for a,b in P.CEPHE:
        ls=LineString([a,b]).buffer(0.11, cap_style=2)
        poly(v, ls, fill=HexColor("#FFFFFF"), stroke=C_CEPHE, lw=1.9)

def kapilar(v, göster=True):
    for (x,y), gen, aci, lbl in P.KAPILAR:
        a=math.radians(aci); dx,dy=math.cos(a)*gen/2, math.sin(a)*gen/2
        ls=LineString([(x-dx,y-dy),(x+dx,y+dy)]).buffer(0.14, cap_style=2)
        poly(v, ls, fill=HexColor("#FFFFFF"))
        line(v, (x-dx,y-dy), (x+dx,y+dy), h.GREY, 0.5)
        # acilim yayi
        c=v.c; c.saveState(); c.setStrokeColor(h.GREY); c.setLineWidth(0.45); c.setDash(1.2,1.2)
        px,py=v.p((x-dx,y-dy)); r=v.m(gen)
        c.arc(px-r,py-r,px+r,py+r, aci-90, 88); c.restoreState()

def zeminler(v, alpha=1.0):
    for z in P.ZONES:
        poly(v, z[1], fill=HexColor(z[4]), alpha=alpha)
    for ad,d in P.ISLAK.items():
        poly(v, d["tum"], fill=C_SERAMIK, alpha=alpha)

def ekipman(v, dolgu=True, etiketli=True):
    for kod, ad, g in P.ekipman_poligonlari():
        if kod=="A":
            poly(v, g, fill=HexColor("#B87333") if dolgu else None,
                 stroke=HexColor("#8A5522"), lw=1.0)
            for i in range(1,4):
                poly(v, P.hex_poly(*P.EKIPMAN[0][5], s=P.HEX_S*i/4.0),
                     stroke=HexColor("#EBD3B6"), lw=0.5)
            cx,cy=P.EKIPMAN[0][5]
            etiket(v,(cx,cy),"TRIMODE ARENA",5.6,HexColor("#FFFFFF"),h.FB,"c",dy=1.6)
            etiket(v,(cx,cy),"10,60 m² · 4 katman",4.8,HexColor("#F6E7D4"),h.F,"c",dy=-3.0)
        else:
            poly(v, g, fill=HexColor("#333940") if dolgu else None,
                 stroke=HexColor("#1C1C1C"), lw=0.6, alpha=0.92)
        if etiketli and kod!="A":
            c=v.c; px,py=v.p((g.centroid.x, g.centroid.y))
            c.setFillColor(HexColor("#FFFFFF")); c.circle(px,py,1.65*mm,0,1)
            h.txt(c, px, py-1.15*mm, kod, h.FB, 5.2, HexColor("#1C1C1C"), "c")

def mobilya(v, etiketli=True):
    for ad, g, tip in P.MOBILYA:
        col = HexColor("#FFF3E3") if tip=="banko" else HexColor("#FFFFFF")
        poly(v, g, fill=col, stroke=C_YENI, lw=0.8)
        if etiketli and tip=="banko":
            c=g.centroid; etiket(v,(c.x,c.y),"BANKO",4.8,C_YENI,h.FB,"c",dy=-1.4)

def mekan_adlari(v, s=6.2):
    for z in P.ZONES:
        ad, pt = z[0], z[5]
        parts = ad.split(" · ")
        etiket(v, pt, h.TR_UP(parts[0]), s, h.NAVY, h.FB, "c", dy=2.4)
        if len(parts)>1:
            etiket(v, pt, h.TR_UP(" · ".join(parts[1:])), s-1.4, h.NAVY2, h.F, "c", dy=-1.6)
            etiket(v, pt, f"{P.ZON_M2[ad]:.2f} m²".replace(".",","), s-0.6, h.COPPER, h.FB, "c", dy=-6.2)
        else:
            etiket(v, pt, f"{P.ZON_M2[ad]:.2f} m²".replace(".",","), s-0.6, h.COPPER, h.FB, "c", dy=-3.6)
    for ad,d in P.ISLAK.items():
        cpt=d["soyunma"].representative_point()
        etiket(v,(cpt.x,cpt.y), ad, s-0.6, h.NAVY, h.FB,"c",dy=2)
        etiket(v,(cpt.x,cpt.y), f"{P.ISLAK_M2_DETAY[ad]['soyunma']:.2f} m²".replace(".",","),
               s-1.6, h.NAVY, h.F,"c",dy=-3)
        for n,lbl in (("dus","DUŞ"),("wc","WC")):
            q=d[n].representative_point()
            etiket(v,(q.x,q.y), lbl, s-1.6, h.NAVY, h.FB,"c")

def olcu(v, a, b, t=None, off=0.45, s=5.2, col=h.NAVY):
    """olcu cizgisi — a,b metre"""
    dx,dy=b[0]-a[0], b[1]-a[1]; L=math.hypot(dx,dy)
    if L<1e-6: return
    nx,ny=-dy/L*off, dx/L*off
    A=(a[0]+nx,a[1]+ny); B=(b[0]+nx,b[1]+ny)
    line(v, A, B, col, 0.45); line(v, a, A, col, 0.3); line(v, b, B, col, 0.3)
    c=v.c
    for pt in (A,B):
        px,py=v.p(pt); c.saveState(); c.setStrokeColor(col); c.setLineWidth(0.8)
        ang=math.atan2(dy,dx); r=0.9*mm
        c.line(px-math.cos(ang)*r, py-math.sin(ang)*r, px+math.cos(ang)*r, py+math.sin(ang)*r)
        c.restoreState()
    mid=((A[0]+B[0])/2,(A[1]+B[1])/2); px,py=v.p(mid)
    lbl=t or f"{L:.2f}".replace(".",",")
    ang=math.degrees(math.atan2(dy,dx))
    if ang>90 or ang<-90: ang+=180
    c.saveState(); c.translate(px,py); c.rotate(ang)
    c.setFillColor(HexColor("#FFFFFF"))
    w=h.tw(c,lbl,h.F,s)+1.6*mm
    c.rect(-w/2,-0.8*mm,w,2.8*mm,0,1)
    h.txt(c,0,0,lbl,h.F,s,col,"c"); c.restoreState()

def kuzey_ok(v, x, y, r=5.5*mm):
    c=v.c; c.saveState(); c.setFillColor(h.NAVY); c.setStrokeColor(h.NAVY); c.setLineWidth(0.6)
    c.circle(x,y,r,0,1); c.setFillColor(HexColor("#FFFFFF"))
    p=c.beginPath(); p.moveTo(x,y+r*0.78); p.lineTo(x-r*0.36,y-r*0.42); p.lineTo(x,y-r*0.16)
    p.lineTo(x+r*0.36,y-r*0.42); p.close(); c.drawPath(p,0,1)
    h.txt(c,x,y-r-3.4*mm,"K",h.FB,6,h.NAVY,"c"); c.restoreState()

def olcek_cubugu(v, x, y, metre=5, w=None):
    c=v.c; L=v.m(metre); seg=L/metre
    for i in range(metre):
        c.setFillColor(h.NAVY if i%2==0 else HexColor("#FFFFFF"))
        c.setStrokeColor(h.NAVY); c.setLineWidth(0.4)
        c.rect(x+i*seg, y, seg, 1.5*mm, 1, 1)
    h.txt(c,x,y-3.6*mm,"0",h.F,5.2,h.NAVY,"c")
    h.txt(c,x+L,y-3.6*mm,f"{metre} m",h.F,5.2,h.NAVY,"c")

def bar_araligi(c, x, y, w, hgt, veriler, birim="TL", bar_h=4.6*mm, ara=2.4*mm,
                etiket_w=None, renk=None, renk2=None):
    """Yatay aralik (düşük–yüksek) çubuk grafiği — tek ölçü, tek hue.
    veriler: [(etiket, dusuk, yuksek)] — büyükten küçüğe sıralanmış gelmeli."""
    renk  = renk  or h.NAVY2
    renk2 = renk2 or h.COPPER
    etiket_w = etiket_w or w*0.30
    px = x+etiket_w; pw = w-etiket_w-w*0.20
    mx = max(v[2] for v in veriler) or 1
    # recessive izgara
    adim = 10**math.floor(math.log10(mx)); 
    while mx/adim > 6: adim *= 2
    c.saveState(); c.setStrokeColor(h.GREY_L); c.setLineWidth(0.4)
    g = 0
    while g <= mx:
        gx = px + pw*g/mx
        c.line(gx, y-hgt, gx, y+1.5*mm)
        h.txt(c, gx, y+2.6*mm, h.tl(g/1000)+"k" if g else "0", h.F, 5.0, h.GREY, "c")
        g += adim
    c.restoreState()
    cy = y
    for ad, lo, hi in veriler:
        cy -= bar_h + ara
        h.txt(c, x, cy+bar_h/2-1.5*mm, ad, h.F, 6.0, h.INK)
        x0 = px; x1 = px+pw*lo/mx; x2 = px+pw*hi/mx
        c.setFillColor(renk);  c.roundRect(x0, cy, max(x1-x0,0.9*mm), bar_h, 0.9*mm, 0, 1)
        c.setFillColor(h.PAPER); c.rect(x1, cy, 0.7*mm, bar_h, 0, 1)      # 2px yüzey boşluğu
        c.setFillColor(renk2); c.roundRect(x1+0.7*mm, cy, max(x2-x1-0.7*mm,0.9*mm), bar_h, 0.9*mm, 0, 1)
        h.txt(c, x2+2.2*mm, cy+bar_h/2-1.5*mm, f"{h.tl(lo/1000)}–{h.tl(hi/1000)} bin", h.F, 5.6, h.NAVY)
    h.lejant(c, x, cy-7*mm, [(renk,"Düşük tahmin"),(renk2,"Yüksek tahmine kadar olan bant")], 5.6)
    return cy-11*mm

def aydinlatma_izgara(v=None):
    """Yansıtılmış tavan planı: her bölgeye lux hesabının verdiği ADET kadar armatür."""
    from shapely.geometry import Point as _Pt
    out=[]
    for z in P.ZONES:
        n = P.ZON_ARMATUR[z[0]]
        g = z[1].buffer(-0.55)
        if g.is_empty: g = z[1].buffer(-0.25)
        b = z[1].bounds
        en = max(1e-6, b[2]-b[0]); boy = max(1e-6, b[3]-b[1])
        # bolgenin en-boy oranina gore satir/sutun
        cols = max(1, round(math.sqrt(n*en/boy))); rows = max(1, math.ceil(n/cols))
        aday=[]
        for i in range(cols):
            for j in range(rows):
                px=b[0]+en*(i+0.5)/cols; py=b[1]+boy*(j+0.5)/rows
                if g.contains(_Pt(px,py)): aday.append((px,py))
        if len(aday)<n:                      # ızgara yetmezse sıklaştır
            for k in range(2,7):
                aday=[]
                for i in range(cols*k):
                    for j in range(rows*k):
                        px=b[0]+en*(i+0.5)/(cols*k); py=b[1]+boy*(j+0.5)/(rows*k)
                        if g.contains(_Pt(px,py)): aday.append((px,py))
                if len(aday)>=n: break
        c0=z[1].centroid
        aday.sort(key=lambda p: math.dist(p,(c0.x,c0.y)))
        out += aday[:n]
    return out
