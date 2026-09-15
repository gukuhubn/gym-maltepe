# -*- coding: utf-8 -*-
"""DXF uygulama projesi — ortak altyapı: birim, katman standardı, blok kütüphanesi, antet.

BİRİM: milimetre ($INSUNITS = 4). Plan koordinatları metre cinsindendir, 1000 ile çarpılır.
SÜRÜM: DXF R2010 (AC1024, UTF-8) — AutoCAD 2010 ve üzeri, BricsCAD, ZWCAD, DraftSight açar.
"""
import math, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import ezdxf
from ezdxf.enums import TextEntityAlignment
import proj as P

K = 1000.0                      # metre → milimetre
def M(p):  return (p[0]*K, p[1]*K)
def ML(pts): return [M(p) for p in pts]

# ── KATMAN STANDARDI ──────────────────────────────────────────────────────────
# (ad, ACI renk, çizgi tipi, kalem kalınlığı 1/100 mm, açıklama)
KATMANLAR = [
 ("A-DUVAR-MEVCUT",  8, "Continuous", 35, "Mimari — mevcut duvar (korunuyor)"),
 ("A-DUVAR-YENI",    1, "Continuous", 35, "Mimari — yeni alçıpan bölme"),
 ("A-CEPHE",         5, "Continuous", 25, "Mimari — cephe doğraması"),
 ("A-KAPI",          8, "Continuous", 18, "Mimari — kapı ve açılım"),
 ("A-EKIPMAN",       9, "Continuous", 18, "Mimari — spor ekipmanı (işverence temin)"),
 ("A-MOBILYA",       9, "Continuous", 18, "Mimari — sabit mobilya"),
 ("A-BOLGE",       254, "Continuous",  9, "Mimari — zemin bölge taraması"),
 ("A-YAZI",          8, "Continuous", 13, "Mimari — mahal adı ve alan"),
 ("A-MAHAL",         6, "Continuous", 18, "Mimari — mahal numarası ve kapı kodu balonu"),
 ("A-KESIT-HAT",     1, "DASHDOT",    35, "Mimari — kesit ve görünüş hattı"),
 ("A-ZEMIN-SINIR",  30, "Continuous", 25, "Mimari — zemin kaplama tipi sınırı"),
 ("A-ZEMIN-YAZI",   30, "Continuous", 13, "Mimari — zemin kaplama tipi ve kotu"),
 ("A-ZEMIN-DERZ",  253, "Continuous",  9, "Mimari — kauçuk karo derz ızgarası"),
 ("A-TAVAN-SINIR", 150, "Continuous", 25, "Mimari — asma tavan tipi sınırı"),
 ("A-TAVAN-YAZI",  150, "Continuous", 13, "Mimari — asma tavan tipi ve kotu"),
 ("A-TAVAN-KAPAK", 150, "Continuous", 18, "Mimari — revizyon kapağı 300×300"),
 ("A-YANGIN-KACIS", 3, "Continuous", 50, "Mimari — kaçış yolu ve çıkış"),
 ("A-YANGIN-EKIP",  1, "Continuous", 35, "Mimari — söndürücü, dolap, ihbar"),
 ("M-HAVA-BESLEME",  3, "Continuous", 35, "Mekanik — taze hava kanalı"),
 ("M-HAVA-EGZOZ",    1, "Continuous", 35, "Mekanik — egzoz kanalı"),
 ("M-HAVA-ISLAK",    6, "Continuous", 25, "Mekanik — ıslak hacim egzoz kanalı"),
 ("M-HAVA-MENFEZ",   3, "Continuous", 25, "Mekanik — menfez ve valf"),
 ("M-HAVA-BRANSMAN", 3, "DASHED",     18, "Mekanik — menfez branşmanı"),
 ("M-HAVA-CIHAZ",    2, "Continuous", 35, "Mekanik — fan ve panjur"),
 ("M-KLIMA-IC",      4, "Continuous", 35, "Mekanik — klima iç ünite"),
 ("M-KLIMA-DIS",     4, "Continuous", 35, "Mekanik — klima dış ünite platformu"),
 ("M-KLIMA-BAKIR",   4, "Continuous", 25, "Mekanik — soğutucu akışkan bakır hattı"),
 ("M-KLIMA-DRENAJ",  4, "DASHED",     18, "Mekanik — klima drenaj hattı"),
 ("M-SIHHI-TEMIZ",   5, "Continuous", 25, "Mekanik — temiz su PPRC"),
 ("M-SIHHI-SICAK",  30, "DASHED",     25, "Mekanik — sıcak su PPRC izoleli"),
 ("M-SIHHI-PIS",     8, "Continuous", 35, "Mekanik — pis su PVC"),
 ("M-SIHHI-CIHAZ",   8, "Continuous", 25, "Mekanik — vitrifiye ve su ısıtıcı"),
 ("M-YAZI",          7, "Continuous", 13, "Mekanik — etiket ve not"),
 ("E-AYD-ARMATUR",   2, "Continuous", 25, "Elektrik — lineer LED armatür"),
 ("E-AYD-DOWNLIGHT", 2, "Continuous", 25, "Elektrik — IP44 downlight"),
 ("E-AYD-ACIL",      3, "Continuous", 25, "Elektrik — acil aydınlatma / yönlendirme"),
 ("E-AYD-ANAHTAR",   2, "Continuous", 18, "Elektrik — anahtar ve sensör"),
 ("E-KUVVET-PRIZ",   5, "Continuous", 25, "Elektrik — priz"),
 ("E-KUVVET-CIHAZ",  5, "Continuous", 25, "Elektrik — klima/ısıtıcı/fan beslemesi"),
 ("E-ZAYIF-KAMERA",  6, "Continuous", 25, "Elektrik — IP kamera"),
 ("E-ZAYIF-SES",     6, "Continuous", 25, "Elektrik — tavan hoparlörü"),
 ("E-ZAYIF-VERI",    6, "Continuous", 25, "Elektrik — veri prizi ve rack"),
 ("E-ZAYIF-YANGIN",  1, "Continuous", 25, "Elektrik — dedektör, buton, siren"),
 ("E-ZAYIF-LINYE",   6, "DASHED",     13, "Elektrik — yangın algılama çevrimi"),
 ("E-PANO",          7, "Continuous", 50, "Elektrik — ana dağıtım panosu"),
 ("E-YAZI",          7, "Continuous", 13, "Elektrik — etiket ve not"),
 ("G-OLCU",          7, "Continuous", 13, "Genel — ölçülendirme"),
 ("G-YAZI",          7, "Continuous", 18, "Genel — başlık ve açıklama"),
 ("G-ANTET",         7, "Continuous", 25, "Genel — antet ve pafta çerçevesi"),
 ("G-KUZEY",         7, "Continuous", 25, "Genel — kuzey oku ve ölçek"),
]

def yeni_belge(aciklama):
    doc = ezdxf.new("R2010", setup=True)
    doc.header["$INSUNITS"]  = 4        # milimetre
    doc.header["$MEASUREMENT"] = 1      # metrik
    doc.header["$LUNITS"]    = 2
    doc.header["$LUPREC"]    = 2
    doc.header["$DIMSCALE"]  = 75.0
    for ad, renk, lt, lw, ack in KATMANLAR:
        ly = doc.layers.add(ad, color=renk, linetype=lt)
        ly.dxf.lineweight = lw
        ly.description = ack
    # Türkçe karakter için gerçek TTF
    for st, font, h in (("GYM", "arial.ttf", 0), ("GYM-B", "arialbd.ttf", 0)):
        if st not in doc.styles:
            doc.styles.add(st, font=font)
    ds = doc.dimstyles.add("GYM-75")
    ds.dxf.dimscale = 75.0; ds.dxf.dimtxt = 2.5; ds.dxf.dimasz = 2.0
    ds.dxf.dimexe = 1.25;   ds.dxf.dimexo = 2.0; ds.dxf.dimgap = 0.8
    ds.dxf.dimtxsty = "GYM"; ds.dxf.dimclrt = 7; ds.dxf.dimdec = 0
    ds.dxf.dimlunit = 2;    ds.dxf.dimtad = 1;  ds.dxf.dimblk = "ARCHTICK"
    doc.header["$DIMSTYLE"] = "GYM-75"
    return doc

# ── YAZI YARDIMCILARI ─────────────────────────────────────────────────────────
def yazi(msp, p, t, h_=175, katman="G-YAZI", hiza="ORTA", aci=0, stil="GYM", renk=None):
    e = msp.add_text(t, height=h_, rotation=aci,
                     dxfattribs={"layer": katman, "style": stil,
                                 **({"color": renk} if renk else {})})
    al = {"ORTA": TextEntityAlignment.MIDDLE_CENTER, "SOL": TextEntityAlignment.MIDDLE_LEFT,
          "SAG": TextEntityAlignment.MIDDLE_RIGHT, "ALT": TextEntityAlignment.BOTTOM_LEFT}[hiza]
    e.set_placement(p, align=al)
    return e

def poli(msp, pts, katman, kapali=True, renk=None):
    return msp.add_lwpolyline(ML(pts), close=kapali,
                              dxfattribs={"layer": katman, **({"color": renk} if renk else {})})

def cizgi(msp, a, b, katman, renk=None):
    return msp.add_line(M(a), M(b), dxfattribs={"layer": katman,
                                                **({"color": renk} if renk else {})})

def tarama(msp, poligonlar, katman, desen="SOLID", olcek=1.0, aci=0, renk=None):
    """Delikli (island) taramayı doğru kurar: dış halka EXTERNAL, iç halkalar DEFAULT,
    tarama stili NESTED — aksi hâlde delik dolar ve pafta kapanır."""
    hs = msp.add_hatch(dxfattribs={"layer": katman, **({"color": renk} if renk else {})})
    hs.dxf.hatch_style = ezdxf.const.HATCH_STYLE_NESTED
    if desen != "SOLID":
        hs.set_pattern_fill(desen, scale=olcek, angle=aci)
    for g in poligonlar:
        if g.is_empty: continue
        gs = list(g.geoms) if g.geom_type.startswith("Multi") else [g]
        for gg in gs:
            if gg.geom_type != "Polygon": continue
            hs.paths.add_polyline_path(ML(list(gg.exterior.coords)[:-1]), is_closed=True,
                                       flags=ezdxf.const.BOUNDARY_PATH_EXTERNAL)
            for r in gg.interiors:
                hs.paths.add_polyline_path(ML(list(r.coords)[:-1]), is_closed=True,
                                           flags=ezdxf.const.BOUNDARY_PATH_DEFAULT)
    return hs

def sekil(msp, g, katman, renk=None):
    """shapely poligonunu LWPOLYLINE olarak yaz."""
    if g.is_empty: return
    gs = list(g.geoms) if g.geom_type.startswith("Multi") else [g]
    for gg in gs:
        if gg.geom_type == "Polygon":
            poli(msp, list(gg.exterior.coords)[:-1], katman, True, renk)
            for r in gg.interiors:
                poli(msp, list(r.coords)[:-1], katman, True, renk)
        elif gg.geom_type in ("LineString", "LinearRing"):
            poli(msp, list(gg.coords), katman, False, renk)

# ── BLOK KÜTÜPHANESİ ──────────────────────────────────────────────────────────
# Semboller mm cinsinden, 1:75 ölçekte okunur boyutta.
def _attdef(blk, etiket, istem, p, h_=120, varsayilan=""):
    a = blk.add_attdef(etiket, dxfattribs={"height": h_, "style": "GYM", "layer": "0",
                                           "prompt": istem, "invisible": 0})
    a.dxf.insert = p
    a.dxf.text = varsayilan
    return a

def bloklari_kur(doc):
    B = doc.blocks
    # ---- MEKANİK ----
    b = B.new("M_MENFEZ_BESLEME")
    b.add_lwpolyline([(-150,-75),(150,-75),(150,75),(-150,75)], close=True, dxfattribs={"layer":"0"})
    for i in (-1,0,1):
        b.add_line((-150, i*40), (150, i*40), dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Menfez kodu", (0, 140))
    _attdef(b, "DEBI", "Debi (m3/h)", (0, -200), 105)

    b = B.new("M_MENFEZ_EGZOZ")
    b.add_lwpolyline([(-150,-75),(150,-75),(150,75),(-150,75)], close=True, dxfattribs={"layer":"0"})
    b.add_line((-150,-75),(150,75), dxfattribs={"layer":"0"})
    b.add_line((-150,75),(150,-75), dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Menfez kodu", (0, 140))
    _attdef(b, "DEBI", "Debi (m3/h)", (0, -200), 105)

    b = B.new("M_VALF")
    b.add_circle((0,0), 90, dxfattribs={"layer":"0"})
    b.add_line((-90,0),(90,0), dxfattribs={"layer":"0"})
    b.add_line((0,-90),(0,90), dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Valf kodu", (0, 150))
    _attdef(b, "DEBI", "Debi (m3/h)", (0, -200), 105)

    b = B.new("M_FAN")
    b.add_lwpolyline([(-250,-140),(250,-140),(250,140),(-250,140)], close=True, dxfattribs={"layer":"0"})
    b.add_circle((0,0), 105, dxfattribs={"layer":"0"})
    for a_ in (0, 90, 180, 270):
        r = math.radians(a_)
        b.add_line((0,0), (105*math.cos(r), 105*math.sin(r)), dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Fan kodu", (0, 210))
    _attdef(b, "TANIM", "Fan tanimi", (0, -270), 105)

    b = B.new("M_PANJUR")
    b.add_lwpolyline([(-140,-90),(140,-90),(140,90),(-140,90)], close=True, dxfattribs={"layer":"0"})
    for i in (-2,-1,0,1,2):
        b.add_line((-140, i*32), (140, i*32), dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Panjur kodu", (0, 150))

    b = B.new("M_KLIMA_IC")
    b.add_lwpolyline([(-450,-140),(450,-140),(450,140),(-450,140)], close=True, dxfattribs={"layer":"0"})
    b.add_line((-450,-60),(450,-60), dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Unite kodu", (0, 215))
    _attdef(b, "KAPASITE", "Kapasite (BTU)", (0, -270), 105)

    b = B.new("M_KLIMA_DIS")
    b.add_lwpolyline([(-500,-350),(500,-350),(500,350),(-500,350)], close=True, dxfattribs={"layer":"0"})
    b.add_circle((0,0), 230, dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Platform", (0, 430))
    _attdef(b, "ADET", "Unite adedi", (0, -530), 105)

    b = B.new("M_ISITICI")
    b.add_lwpolyline([(-200,-150),(200,-150),(200,150),(-200,150)], close=True, dxfattribs={"layer":"0"})
    for i in (-1,0,1):
        b.add_line((i*90,-150),(i*90,150), dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Isitici kodu", (0, 225))
    _attdef(b, "GUC", "Guc (kW)", (0, -285), 105)

    b = B.new("M_KLOZET")
    b.add_ellipse((0,-40), major_axis=(160,0), ratio=0.78, dxfattribs={"layer":"0"})
    b.add_lwpolyline([(-170,150),(170,150),(170,260),(-170,260)], close=True, dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Vitrifiye", (0, 330))

    b = B.new("M_LAVABO")
    b.add_lwpolyline([(-230,-140),(230,-140),(230,140),(-230,140)], close=True, dxfattribs={"layer":"0"})
    b.add_ellipse((0,0), major_axis=(170,0), ratio=0.62, dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Vitrifiye", (0, 210))

    b = B.new("M_DUS")
    b.add_lwpolyline([(-450,-450),(450,-450),(450,450),(-450,450)], close=True, dxfattribs={"layer":"0"})
    b.add_circle((0,0), 80, dxfattribs={"layer":"0"})
    b.add_line((-450,-450),(450,450), dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Dus teknesi", (0, 530))

    b = B.new("M_SUZGEC")
    b.add_lwpolyline([(-75,-75),(75,-75),(75,75),(-75,75)], close=True, dxfattribs={"layer":"0"})
    b.add_circle((0,0), 42, dxfattribs={"layer":"0"})

    b = B.new("M_SAYAC")
    b.add_circle((0,0), 130, dxfattribs={"layer":"0"})
    b.add_line((-130,0),(130,0), dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Sayac / ana kesme", (0, 200))

    # ---- ELEKTRİK ----
    b = B.new("E_ARMATUR_LINEER")
    b.add_lwpolyline([(-600,-55),(600,-55),(600,55),(-600,55)], close=True, dxfattribs={"layer":"0"})
    b.add_line((-600,0),(600,0), dxfattribs={"layer":"0"})
    _attdef(b, "LINYE", "Linye kodu", (0, 185), 105)

    b = B.new("E_DOWNLIGHT")
    b.add_circle((0,0), 90, dxfattribs={"layer":"0"})
    b.add_line((-64,-64),(64,64), dxfattribs={"layer":"0"})
    b.add_line((-64,64),(64,-64), dxfattribs={"layer":"0"})
    _attdef(b, "LINYE", "Linye kodu", (0, 210), 105)

    b = B.new("E_ACIL")
    b.add_lwpolyline([(-100,-100),(100,-100),(100,100),(-100,100)], close=True, dxfattribs={"layer":"0"})
    b.add_text("E", height=110, dxfattribs={"layer":"0","style":"GYM-B"}).set_placement(
        (0,0), align=TextEntityAlignment.MIDDLE_CENTER)
    _attdef(b, "KOD", "Armatur kodu", (0, 230), 105)

    b = B.new("E_YONLENDIRME")
    b.add_lwpolyline([(-130,-80),(130,-80),(130,80),(-130,80)], close=True, dxfattribs={"layer":"0"})
    b.add_lwpolyline([(-70,0),(30,0)], dxfattribs={"layer":"0"})
    b.add_lwpolyline([(30,45),(80,0),(30,-45)], close=True, dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Armatur kodu", (0, 205), 105)

    b = B.new("E_PRIZ")
    b.add_arc((0,0), 95, 0, 180, dxfattribs={"layer":"0"})
    b.add_line((-95,0),(95,0), dxfattribs={"layer":"0"})
    b.add_line((0,0),(0,150), dxfattribs={"layer":"0"})
    b.add_line((-60,150),(60,150), dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Priz kodu", (195, 80), 105)
    _attdef(b, "LINYE", "Linye", (195, -80), 105)

    b = B.new("E_PRIZ_IP44")
    b.add_arc((0,0), 95, 0, 180, dxfattribs={"layer":"0"})
    b.add_line((-95,0),(95,0), dxfattribs={"layer":"0"})
    b.add_line((0,0),(0,150), dxfattribs={"layer":"0"})
    b.add_line((-60,150),(60,150), dxfattribs={"layer":"0"})
    b.add_text("IP44", height=70, dxfattribs={"layer":"0","style":"GYM"}).set_placement(
        (0,-120), align=TextEntityAlignment.MIDDLE_CENTER)
    _attdef(b, "KOD", "Priz kodu", (205, 80), 105)

    b = B.new("E_ANAHTAR")
    b.add_circle((0,0), 60, dxfattribs={"layer":"0"})
    b.add_line((0,0),(130,110), dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Anahtar kodu", (0, 240), 105)

    b = B.new("E_SENSOR")
    b.add_circle((0,0), 95, dxfattribs={"layer":"0"})
    b.add_text("S", height=100, dxfattribs={"layer":"0","style":"GYM-B"}).set_placement(
        (0,0), align=TextEntityAlignment.MIDDLE_CENTER)
    _attdef(b, "KOD", "Sensor kodu", (0, 230), 105)

    b = B.new("E_KAMERA")
    b.add_lwpolyline([(-110,-85),(110,0),(-110,85)], close=True, dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Kamera kodu", (0, 210), 105)

    b = B.new("E_HOPARLOR")
    b.add_circle((0,0), 95, dxfattribs={"layer":"0"})
    b.add_arc((0,0), 150, -45, 45, dxfattribs={"layer":"0"})
    b.add_arc((0,0), 200, -35, 35, dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Hoparlor kodu", (0, 330), 105)

    b = B.new("E_VERI")
    b.add_lwpolyline([(-95,-95),(95,-95),(95,95),(-95,95)], close=True, dxfattribs={"layer":"0"})
    b.add_text("D", height=105, dxfattribs={"layer":"0","style":"GYM-B"}).set_placement(
        (0,0), align=TextEntityAlignment.MIDDLE_CENTER)
    _attdef(b, "KOD", "Veri kodu", (0, 230), 105)

    b = B.new("E_DEDEKTOR")
    b.add_circle((0,0), 110, dxfattribs={"layer":"0"})
    b.add_circle((0,0), 40, dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Dedektor kodu", (0, 240), 105)

    b = B.new("E_YANGIN_BUTON")
    b.add_lwpolyline([(-95,-95),(95,-95),(95,95),(-95,95)], close=True, dxfattribs={"layer":"0"})
    b.add_text("Y", height=105, dxfattribs={"layer":"0","style":"GYM-B"}).set_placement(
        (0,0), align=TextEntityAlignment.MIDDLE_CENTER)
    _attdef(b, "KOD", "Buton kodu", (0, 230), 105)

    b = B.new("E_PANO")
    b.add_lwpolyline([(-420,-280),(420,-280),(420,280),(-420,280)], close=True, dxfattribs={"layer":"0"})
    for i in range(-3, 4):
        b.add_line((i*110,-280),(i*110,280), dxfattribs={"layer":"0"})
    _attdef(b, "KOD", "Pano kodu", (0, 380))
    _attdef(b, "TANIM", "Pano tanimi", (0, -470), 105)

    b = B.new("G_KUZEY")
    b.add_circle((0,0), 700, dxfattribs={"layer":"0"})
    b.add_lwpolyline([(0,560),(-230,-330),(0,-140),(230,-330)], close=True, dxfattribs={"layer":"0"})
    b.add_text("K", height=260, dxfattribs={"layer":"0","style":"GYM-B"}).set_placement(
        (0,-960), align=TextEntityAlignment.MIDDLE_CENTER)
    return doc

def blok(msp, ad, p, katman, oznitelik=None, aci=0, olcek=1.0, yazi_yatay=True):
    """Sembol duvara göre döner; öznitelik yazıları YATAY kalır (okunabilirlik)."""
    ref = msp.add_blockref(ad, M(p), dxfattribs={
        "layer": katman, "rotation": aci, "xscale": olcek, "yscale": olcek})
    if oznitelik:
        ref.add_auto_attribs({k: str(v) for k, v in oznitelik.items()})
        if yazi_yatay and aci:
            for at in ref.attribs:
                at.dxf.rotation = 0.0
    return ref


def duvar_taramasi(msp, ic_poly, kalinlik, katman, desen="ANSI31", olcek=40, aci=45):
    """Duvar bandını DELİKSİZ dörtgenlere ayırarak tarar.
    Ada (island) taramasına güvenilmez: bazı görüntüleyiciler deliği doldurup paftayı kapatır.
    Bu yöntem her CAD'de aynı sonucu verir."""
    from shapely.geometry import Polygon as _Poly, Point as _Pt
    ring = list(ic_poly.exterior.coords)[:-1]
    n = len(ring)
    # dışa doğru normal yönünü deneyerek bul
    a, b = ring[0], ring[1]
    dx, dy = b[0]-a[0], b[1]-a[1]; L = math.hypot(dx, dy) or 1
    deneme = ((a[0]+b[0])/2 + dy/L*0.01, (a[1]+b[1])/2 - dx/L*0.01)
    sgn = 1 if not ic_poly.contains(_Pt(deneme)) else -1
    parcalar = []
    for i in range(n):
        a, b = ring[i], ring[(i+1) % n]
        dx, dy = b[0]-a[0], b[1]-a[1]; L = math.hypot(dx, dy)
        if L < 1e-9: continue
        nx, ny = sgn*dy/L*kalinlik, -sgn*dx/L*kalinlik
        parcalar.append(_Poly([a, b, (b[0]+nx, b[1]+ny), (a[0]+nx, a[1]+ny)]))
        # köşe boşluğunu kapat
        k = kalinlik*1.05
        parcalar.append(_Poly([(b[0]-k, b[1]-k), (b[0]+k, b[1]-k),
                               (b[0]+k, b[1]+k), (b[0]-k, b[1]+k)]
                              ).intersection(ic_poly.buffer(kalinlik, join_style=2)
                                             ).difference(ic_poly))
    hs = msp.add_hatch(dxfattribs={"layer": katman})
    hs.dxf.hatch_style = ezdxf.const.HATCH_STYLE_NESTED
    if desen != "SOLID":
        hs.set_pattern_fill(desen, scale=olcek, angle=aci)
    for g in parcalar:
        if g.is_empty or g.area < 1e-6: continue
        gs = list(g.geoms) if g.geom_type.startswith("Multi") else [g]
        for gg in gs:
            if gg.geom_type != "Polygon" or gg.is_empty: continue
            hs.paths.add_polyline_path(ML(list(gg.exterior.coords)[:-1]), is_closed=True,
                                       flags=ezdxf.const.BOUNDARY_PATH_EXTERNAL)
    return hs
