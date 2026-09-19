# -*- coding: utf-8 -*-
"""DOĞRAMA BLOK KÜTÜPHANESİ — kapı ve pencere, plan / kesit / görünüş, ölçeğe göre.

Dayanak: MEGEP Şekil 2.51–2.55 (kapı plan sırası), Tablo 2.4–2.6 (1/200 ·
1/100 · 1/50 kapı-pencere ifadesi), Mimarlar Odası standardı (doğrama etiketi
"K7 90/220", açılan kanatların işaretlenmesi), tools/standart.py sabitleri.

Her sembol GERÇEK ölçüyle çizilir (kasa 45, pervaz 60, kanat 40 mm) ve ölçeğe
göre sadeleşir:
    1/100 : yalnız açılış yayı + etiket
    1/50  : kasa şematik, kanat tek çizgi, yay, etiket
    ≤1/20 : kasa profili, pervaz (iki yüz), kanat kalınlığı, yay, etiket

Yerel eksen: kapı merkezi `pt`, boşluk doğrultusu `aci` (derece). Kanat,
boşluk doğrultusunun SOL normali yönüne açılır; ters açılım için `aci+180`.
"""
from __future__ import annotations
import math

import standart as ST

K = 1000.0


def _ln(msp, a, b, kat):
    return msp.add_line((a[0]*K, a[1]*K), (b[0]*K, b[1]*K), dxfattribs={"layer": kat})


def _pl(msp, pts, kat, kapali=True):
    return msp.add_lwpolyline([(x*K, y*K) for x, y in pts], close=kapali,
                              dxfattribs={"layer": kat})


def _tx(msp, p, t, h_mm, kat, olcek, aci=0.0):
    """h_mm kâğıtta; olcek = PAFTANIN ölçeği (yazı boyu buna göre)."""
    e = msp.add_text(t, height=h_mm*olcek, rotation=aci,
                     dxfattribs={"layer": kat, "style": "GYM"})
    from ezdxf.enums import TextEntityAlignment as TA
    e.set_placement((p[0]*K, p[1]*K), align=TA.MIDDLE_CENTER)
    return e


# ── KAPI — PLAN ──────────────────────────────────────────────────────────────
def kapi_plan(msp, pt, gen, aci, kal, olcek, tip="panel", mentese="sol",
              etiket=None, kat="A-KAPI", kat_etiket="A-MAHAL",
              etiket_taraf=-1, f=1.0, pafta_olcek=None):
    """f: geometri çarpanı (sembol paftasında 1/100 satırı için 20/100 gibi);
    pafta_olcek: yazı boyu için paftanın ölçeği (None → olcek).
    etiket_taraf: -1 açılmayan taraf (varsayılan), +1 açılış tarafı."""
    po = pafta_olcek or olcek
    """Tek kanatlı kapı planı.

    pt, gen, aci : merkez (m), kaba yapı boşluğu (m), boşluk doğrultusu (°)
    kal          : duvar karkas kalınlığı (m) — kasa derinliği ve pervaz yeri
    tip          : "panel" (kasa+pervaz) · "cam" (duş kapağı: profil + cam çizgisi)
    mentese      : "sol" → menteşe boşluğun -u ucunda; "sag" → +u ucunda
    etiket       : (kod, yükseklik_cm, genişlik_cm) — Mimarlar Odası biçimi
    """
    a = math.radians(aci)
    ux, uy = math.cos(a), math.sin(a)          # boşluk doğrultusu
    nx, ny = -uy, ux                           # açılış yönü
    if mentese == "sag":
        ux, uy = -ux, -uy                      # menteşe +u ucuna alınır
    gen, kal = gen*f, kal*f
    h = gen/2
    p1 = (pt[0]-ux*h, pt[1]-uy*h)              # menteşe sövesi
    p2 = (pt[0]+ux*h, pt[1]+uy*h)              # kilit sövesi
    kasa = (ST.KASA_KALINLIK_M if tip == "panel" else 0.025)*f
    perv = ST.PERVAZ_GENISLIK_M*f
    kan = (ST.KANAT_KALINLIK_M if tip == "panel" else 0.008)*f
    def dik(p, t): return (p[0]+nx*t, p[1]+ny*t)
    n = 0
    if olcek <= 50:
        for q, yon in ((p1, +1), (p2, -1)):
            k0 = dik(q, -kal/2); k1 = dik(q, +kal/2)
            kx = (q[0]+ux*yon*kasa, q[1]+uy*yon*kasa)
            _pl(msp, [k0, k1, dik(kx, +kal/2), dik(kx, -kal/2)], kat); n += 1
            if olcek <= 20 and tip == "panel":
                for t, s_ in ((+kal/2, +1), (-kal/2, -1)):
                    pv0 = dik(q, t); pv1 = dik(q, t + s_*0.012*f)
                    _pl(msp, [pv0, (pv0[0]+ux*yon*perv, pv0[1]+uy*yon*perv),
                              (pv1[0]+ux*yon*perv, pv1[1]+uy*yon*perv), pv1], kat)
                    n += 1
    # kanat — menteşeden açılış yönüne; yay AYNI merkezden AYNI yöne
    net = gen - 2*kasa if olcek <= 50 else gen
    m1 = (p1[0]+ux*kasa, p1[1]+uy*kasa) if olcek <= 50 else p1
    uc = dik(m1, net)
    if olcek <= 50:
        _pl(msp, [m1, uc, (uc[0]+ux*kan, uc[1]+uy*kan), (m1[0]+ux*kan, m1[1]+uy*kan)], kat)
    else:
        _ln(msp, m1, uc, kat)
    # yay: kanat ucu açısından (n yönü) kapalı konuma (u yönü) — kısa yönde
    a_n = math.degrees(math.atan2(ny, nx)); a_u = math.degrees(math.atan2(uy, ux))
    fark = (a_u - a_n + 540) % 360 - 180        # -180..180
    bas, son = (a_n, a_n + fark) if fark > 0 else (a_n + fark, a_n)
    msp.add_arc((m1[0]*K, m1[1]*K), net*K, bas, son, dxfattribs={"layer": kat}); n += 1
    if tip == "cam" and olcek <= 20:
        # cam kanat: kanadın ortasından cam çizgisi
        _ln(msp, (m1[0]+ux*kan/2, m1[1]+uy*kan/2), (uc[0]+ux*kan/2, uc[1]+uy*kan/2), kat)
    # etiket — açılmayan tarafta, eksene dik çizgi; üst yükseklik, alt genişlik
    if etiket:
        kod, yuk, gcm = etiket
        st = etiket_taraf
        d0 = kal/2 + 0.04*po/20; d1 = d0 + 0.40*po/20
        e0 = dik(pt, st*d0); e1 = dik(pt, st*d1)
        _ln(msp, e0, e1, kat_etiket)
        em = ((e0[0]+e1[0])/2, (e0[1]+e1[1])/2)
        ta = (math.degrees(math.atan2(ny, nx)) + 360) % 360
        if 90 < ta <= 270: ta -= 180
        o = 0.05*po/20
        _tx(msp, (em[0]+ux*o, em[1]+uy*o), yuk, ST.YAZI["olcu"], kat_etiket, po, ta)
        _tx(msp, (em[0]-ux*o, em[1]-uy*o), gcm, ST.YAZI["olcu"], kat_etiket, po, ta)
        _tx(msp, (e1[0]+nx*st*0.07*po/20, e1[1]+ny*st*0.07*po/20), kod,
            ST.YAZI["olcu"], kat_etiket, po, ta)
    return n


# ── KAPI — GÖRÜNÜŞ (duvar düzleminde, x: boşluk boyu, z: kot) ───────────────
def kapi_gorunus(msp, x0, z0, gen, yuk, olcek, tip="panel", mentese="sol",
                 kat="A-GORUNUS-IC", f=1.0):
    """Kapı görünüşü: kasa + kanat + açılış işareti (kesik çizgi 'V' — Mimarlar
    Odası: açılan kanatlar işaretlenir; V'nin tepesi menteşe kenarını gösterir)."""
    gen, yuk = gen*f, yuk*f
    kasa = ST.KASA_KALINLIK_M*f
    _pl(msp, [(x0, z0), (x0+gen, z0), (x0+gen, z0+yuk), (x0, z0+yuk)], kat, False)
    if olcek <= 50:
        _pl(msp, [(x0+kasa, z0), (x0+gen-kasa, z0), (x0+gen-kasa, z0+yuk-kasa),
                  (x0+kasa, z0+yuk-kasa)], kat, False)
    # açılış işareti: menteşe kenarından karşı kenarın orta yüksekliğine
    mx = x0 if mentese == "sol" else x0+gen
    kx = x0+gen if mentese == "sol" else x0
    for zz in (z0+kasa, z0+yuk-kasa):
        msp.add_line((mx*K, zz*K), (kx*K, (z0+yuk/2)*K),
                     dxfattribs={"layer": kat, "linetype": "DASHED"})
    if tip == "panel" and olcek <= 20:
        # kol — kilit kenarında, +1,05 m
        hx = kx + (0.06 if mentese == "sol" else -0.06) * (-1 if mentese == "sol" else 1)
        msp.add_circle((hx*K, (z0+1.05*f)*K), 0.02*f*K, dxfattribs={"layer": kat})
    return 1


# ── PENCERE — PLAN / KESİT / GÖRÜNÜŞ (MEGEP Tablo 2.6) ──────────────────────
def pencere_plan(msp, pt, gen, aci, kal, olcek, kanat=2, kat="A-CEPHE", f=1.0):
    """Pencere planı: kasa iki söve, cam çizgisi, kanat bölüntüsü."""
    gen, kal = gen*f, kal*f
    a = math.radians(aci); ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
    h = gen/2
    p1 = (pt[0]-ux*h, pt[1]-uy*h); p2 = (pt[0]+ux*h, pt[1]+uy*h)
    def dik(p, t): return (p[0]+nx*t, p[1]+ny*t)
    n = 0
    for q, yon in ((p1, +1), (p2, -1)):
        k0 = dik(q, -kal/2); k1 = dik(q, +kal/2)
        kx = (q[0]+ux*yon*0.06*f, q[1]+uy*yon*0.06*f)
        _pl(msp, [k0, k1, dik(kx, +kal/2), dik(kx, -kal/2)], kat); n += 1
    # cam çizgisi (duvar ekseninde; 1/50 ve büyüğünde çift çizgi)
    for t in ((0.0,) if olcek > 50 else (-0.006*f, 0.006*f)):
        _ln(msp, dik((p1[0]+ux*0.06*f, p1[1]+uy*0.06*f), t),
            dik((p2[0]-ux*0.06*f, p2[1]-uy*0.06*f), t), kat); n += 1
    if kanat > 1 and olcek <= 50:
        for i in range(1, kanat):
            q = (p1[0]+ux*gen*i/kanat, p1[1]+uy*gen*i/kanat)
            _ln(msp, dik(q, -kal/2), dik(q, kal/2), kat)
    return n


def pencere_gorunus(msp, x0, z0, gen, yuk, olcek, kanat=2, acilan=(0,),
                    kat="A-GORUNUS-IC", f=1.0):
    """Pencere görünüşü: kasa, kanat bölüntüleri, açılan kanatta 'V' işareti."""
    gen, yuk = gen*f, yuk*f
    _pl(msp, [(x0, z0), (x0+gen, z0), (x0+gen, z0+yuk), (x0, z0+yuk)], kat)
    kw = gen/kanat
    for i in range(kanat):
        xa = x0 + i*kw
        c = 0.04*f
        if olcek <= 50:
            _pl(msp, [(xa+c, z0+c), (xa+kw-c, z0+c),
                      (xa+kw-c, z0+yuk-c), (xa+c, z0+yuk-c)], kat)
        if i in acilan:
            for zz in (z0+c, z0+yuk-c):
                msp.add_line(((xa+c)*K, zz*K), ((xa+kw-c)*K, (z0+yuk/2)*K),
                             dxfattribs={"layer": kat, "linetype": "DASHED"})
    return kanat


# ── SEMBOL PAFTASI — kütüphanenin üç ölçekte doğrulanması ───────────────────
def sembol_paftasi(msp, x0=0.0, y0=0.0, pafta_olcek=20):
    """Her sembolü 1/100 · 1/50 · 1/20'de alt alta çizer. Pafta 1:20'dir; her
    satırın geometrisi f = pafta/ölçek ile küçültülür — böylece kâğıtta her
    satır KENDİ ölçeğinde nasıl görüneceğini gösterir (MEGEP Tablo 2.4–2.6
    mantığı). Yazılar pafta ölçeğinde sabit kalır. Döner: (genişlik, yükseklik) m."""
    po = pafta_olcek
    satir = 0.0
    en = 0.0
    for olc, ad in ((100, "1/100"), (50, "1/50"), (20, "1/20")):
        f = po/olc
        x = x0
        _tx(msp, (x-0.25, y0+satir+0.55), ad, ST.YAZI["etiket"], "A-YAZI", po)
        kapi_plan(msp, (x+0.55, y0+satir), 0.90, 0, 0.10, olc, "panel", "sol",
                  ("K1", "210", "90"), f=f, pafta_olcek=po); x += 1.35
        kapi_plan(msp, (x+0.45, y0+satir), 0.70, 0, 0.10, olc, "cam", "sag",
                  ("K7", "195", "70"), f=f, pafta_olcek=po); x += 1.15
        pencere_plan(msp, (x+0.65, y0+satir), 1.20, 0, 0.20, olc, kanat=2, f=f); x += 1.45
        kapi_gorunus(msp, x, y0+satir-0.55*f-0.35, 0.90, 2.10, olc, "panel", "sol", f=f); x += 1.05
        pencere_gorunus(msp, x, y0+satir-0.25, 1.20, 1.20, olc, 2, (0,), f=f); x += 1.35
        en = max(en, x - x0)
        satir += 2.45
    return (en + 0.3, satir)
