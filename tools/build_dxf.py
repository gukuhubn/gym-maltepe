# -*- coding: utf-8 -*-
"""AUTOCAD UYGULAMA PROJESİ SETİ — DXF R2010 (MEP)

Üretilen dosyalar (cad/):
  GYM-MIM-Altlik-R2010.dxf      mimari altlık (xref olarak kullanılabilir)
  GYM-MEK-Uygulama-R2010.dxf    mekanik — 4 pafta
  GYM-ELK-Uygulama-R2010.dxf    elektrik — 4 pafta
  GYM-MEP-Birlesik-R2010.dxf    tümü — 8 pafta

Birim: milimetre ($INSUNITS=4) · Paftalar: A3 (420×297) · Ölçek: 1/75
"""
import sys, os, math, zipfile
sys.path.insert(0, os.path.dirname(__file__))
from pathlib import Path
from shapely.ops import unary_union
from shapely.geometry import LineString, Point, box
import ezdxf
from ezdxf.enums import TextEntityAlignment
import proj as P, dxf_lib as X
from dxf_lib import M, ML, yazi, poli, cizgi, tarama, sekil, blok, K

ROOT = Path(__file__).resolve().parent.parent
CAD  = ROOT/"cad"; CAD.mkdir(exist_ok=True)
IC   = unary_union([P.SALON, P.ERKEK, P.KADIN])
BB   = IC.buffer(P.V["duvar_kalinlik"][0]).bounds
CX, CY = (BB[0]+BB[2])/2*K, (BB[1]+BB[3])/2*K

# ══════════════════════ MİMARİ ALTLIK ══════════════════════════════════════════
def mimari(msp, bolge_tarama=True):
    t = P.V["duvar_kalinlik"][0]
    dis = IC.buffer(t, join_style=2)
    X.duvar_taramasi(msp, IC, t, "A-DUVAR-MEVCUT", "ANSI31", 40, 0)
    sekil(msp, dis, "A-DUVAR-MEVCUT"); sekil(msp, IC, "A-DUVAR-MEVCUT")
    # yeni bölmeler (ıslak hacim içi)
    for ad, d in P.ISLAK.items():
        for n in ("dus", "wc"):
            sekil(msp, d[n], "A-DUVAR-YENI")
    for b in (P.ERKEK, P.KADIN): sekil(msp, b, "A-DUVAR-YENI")
    # cephe doğraması
    for a, b in P.CEPHE:
        sekil(msp, LineString([a, b]).buffer(0.045, cap_style=2), "A-CEPHE")
    # kapılar
    for (x, y), gen, aci, lbl in P.KAPILAR:
        a = math.radians(aci); dx, dy = math.cos(a)*gen/2, math.sin(a)*gen/2
        cizgi(msp, (x-dx, y-dy), (x+dx, y+dy), "A-KAPI")
        msp.add_arc(M((x-dx, y-dy)), gen*K, aci-90, aci-2, dxfattribs={"layer": "A-KAPI"})
    # mahal etiketleri (MEP paftasında zemin bölge taraması kullanılmaz)
    for z in P.ZONES:
        yazi(msp, M(z[5]), z[0].split(" · ")[0], 260, "A-YAZI", stil="GYM-B")
        yazi(msp, (M(z[5])[0], M(z[5])[1]-300), f"{P.ZON_M2[z[0]]:.2f} m²".replace(".", ","),
             195, "A-YAZI")
    for ad, d in P.ISLAK.items():
        for n, lbl in (("soyunma", ad), ("dus", "DUŞ"), ("wc", "WC")):
            q = d[n].representative_point()
            yazi(msp, M((q.x, q.y)), lbl, 190, "A-YAZI", stil="GYM-B")
            yazi(msp, (q.x*K, q.y*K-230), f"{P.ISLAK_M2_DETAY[ad][n]:.2f} m²".replace(".", ","),
                 145, "A-YAZI")
    # ekipman ve mobilya
    for kod, ad, g in P.ekipman_poligonlari():
        sekil(msp, g, "A-EKIPMAN")
        yazi(msp, M((g.centroid.x, g.centroid.y)), kod, 170, "A-EKIPMAN", stil="GYM-B")
    for ad, g, tip in P.MOBILYA: sekil(msp, g, "A-MOBILYA")
    blok(msp, "G_KUZEY", (12.55, 12.10), "G-KUZEY")

def olculer(msp):
    ds = "GYM-75"
    ol = [((3.24, 0.0), (8.92, 0.0), -1.1, 0),      # güney cephe
          ((0.0, 6.84), (0.58, 1.25), -1.1, 90),    # batı cephe
          ((11.56, 1.10), (11.01, 4.96), 1.1, 90),  # doğu — kadın blok
          ((10.47, 8.75), (11.00, 5.08), 1.1, 90),  # doğu — erkek blok
          ((5.84, 12.50), (9.89, 12.99), 1.1, 0)]   # kuzey kol
    for p1, p2, off, aci in ol:
        d = msp.add_linear_dim(base=M(((p1[0]+p2[0])/2 + (off if aci else 0),
                                       (p1[1]+p2[1])/2 + (0 if aci else off))),
                               p1=M(p1), p2=M(p2), angle=aci, dimstyle=ds,
                               dxfattribs={"layer": "G-OLCU"})
        d.render()

# ══════════════════════ MEKANİK ════════════════════════════════════════════════
def mekanik(msp):
    for ad, k in (("besleme", "M-HAVA-BESLEME"), ("egzoz", "M-HAVA-EGZOZ"),
                  ("islak", "M-HAVA-ISLAK")):
        d = P.KANAL[ad]
        g = 0.50 if ad == "besleme" else (0.40 if ad == "egzoz" else 0.16)
        sekil(msp, LineString(d["guzergah"]).buffer(g/2, cap_style=2, join_style=2), k)
        poli(msp, d["guzergah"], k, False)
        mid = LineString(d["guzergah"]).interpolate(0.30, normalized=True)
        yazi(msp, (mid.x*K, mid.y*K+g*K/2+330),
             f"{d['kesit']} · {d['debi']} m³/h", 160, "M-YAZI")
    for kod, x, y, debi, tip in P.MENFEZ:
        hat = P.KANAL["besleme" if tip == "besleme" else ("egzoz" if tip == "egzoz" else "islak")]
        ls = LineString(hat["guzergah"]); q = ls.interpolate(ls.project(Point(x, y)))
        cizgi(msp, (q.x, q.y), (x, y), "M-HAVA-BRANSMAN")
        b = {"besleme": "M_MENFEZ_BESLEME", "egzoz": "M_MENFEZ_EGZOZ", "valf": "M_VALF"}[tip]
        blok(msp, b, (x, y), "M-HAVA-MENFEZ", {"KOD": kod, "DEBI": f"{debi} m³/h"})
    for kod, x, y, ad in P.FAN:
        blok(msp, "M_FAN", (x, y), "M-HAVA-CIHAZ", {"KOD": kod, "TANIM": ad.split("—")[-1].strip()})
    for kod, x, y, ad in P.PANJUR:
        blok(msp, "M_PANJUR", (x, y), "M-HAVA-CIHAZ", {"KOD": kod})
    # iklimlendirme
    for hat in P.BAKIR_HAT.values(): poli(msp, hat, "M-KLIMA-BAKIR", False)
    for hat in P.DRENAJ.values(): poli(msp, hat, "M-KLIMA-DRENAJ", False)
    for kod, zon, btu, (x, y) in P.KLIMA:
        blok(msp, "M_KLIMA_IC", (x, y), "M-KLIMA-IC", {"KOD": kod, "KAPASITE": f"{btu} BTU"})
    blok(msp, "M_KLIMA_DIS", P.DIS_UNITE, "M-KLIMA-DIS",
         {"KOD": "DIŞ ÜNİTE PLATFORMU", "ADET": f"{P.ADET_KLIMA} adet"})
    # sıhhi tesisat
    poli(msp, P.TEMIZ_SU["Ø25"], "M-SIHHI-TEMIZ", False)
    for br in P.TEMIZ_SU["Ø20"]:
        poli(msp, br, "M-SIHHI-TEMIZ", False)
        poli(msp, [(p[0]+0.09, p[1]+0.09) for p in br], "M-SIHHI-SICAK", False)
    poli(msp, P.PIS_SU["Ø100"], "M-SIHHI-PIS", False)
    for br in P.PIS_SU["Ø70"] + P.PIS_SU["Ø50"]: poli(msp, br, "M-SIHHI-PIS", False)
    for kod, x, y, ad in P.VITRIFIYE:
        if kod.startswith("WC"):
            blok(msp, "M_KLOZET", (x, y), "M-SIHHI-CIHAZ", {"KOD": kod})
            blok(msp, "M_LAVABO", (x+0.55, y), "M-SIHHI-CIHAZ", {"KOD": "LV"})
        else:
            blok(msp, "M_DUS", (x, y), "M-SIHHI-CIHAZ", {"KOD": kod})
            blok(msp, "M_SUZGEC", (x, y), "M-SIHHI-CIHAZ")
    for kod, x, y, ad in P.ISITICI:
        blok(msp, "M_ISITICI", (x, y), "M-SIHHI-CIHAZ", {"KOD": kod, "GUC": "6 kW"})
    blok(msp, "M_SAYAC", P.SU_GIRIS, "M-SIHHI-TEMIZ", {"KOD": "SAYAÇ + ANA KESME"})

# ══════════════════════ ELEKTRİK ═══════════════════════════════════════════════
def elektrik(msp):
    import draw as D
    zon_linye = {"ARENA · SERBEST AĞIRLIK": "L1", "FONKSİYONEL · KARDİYO": "L2",
                 "DİNLENME SALONU": "L3", "GİRİŞ · BANKO · SİRKÜLASYON": "L4"}
    izgara = D.aydinlatma_izgara()
    i = 0
    for z in P.ZONES:
        n = P.ZON_ARMATUR[z[0]]
        for _ in range(n):
            if i >= len(izgara): break
            blok(msp, "E_ARMATUR_LINEER", izgara[i], "E-AYD-ARMATUR",
                 {"LINYE": zon_linye[z[0]]}); i += 1
    for ad, d in P.ISLAK.items():
        for n in ("soyunma", "dus", "wc"):
            q = d[n].representative_point()
            blok(msp, "E_DOWNLIGHT", (q.x, q.y), "E-AYD-DOWNLIGHT", {"LINYE": "L5"})
    for kod, x, y, t in P.ACIL:
        b = "E_ACIL" if "acil" in t else "E_YONLENDIRME"
        blok(msp, b, (x, y), "E-AYD-ACIL", {"KOD": kod})
    for kod, x, y, t in P.ANAHTAR: blok(msp, "E_ANAHTAR", (x, y), "E-AYD-ANAHTAR", {"KOD": kod})
    for kod, x, y, t in P.SENSOR:  blok(msp, "E_SENSOR",  (x, y), "E-AYD-ANAHTAR", {"KOD": kod})
    linye_priz = {}
    for j, (kod, x, y, t) in enumerate(P.PRIZ):
        ln = "P4" if kod.startswith("PK") else ("P3" if kod.startswith("PB") else
             ("P1" if j % 2 == 0 else "P2"))
        blok(msp, "E_PRIZ", (x, y), "E-KUVVET-PRIZ", {"KOD": kod, "LINYE": ln})
    for kod, x, y, t in P.PRIZ_IP44:
        blok(msp, "E_PRIZ_IP44", (x, y), "E-KUVVET-PRIZ", {"KOD": kod})
    for kod, zon, btu, (x, y) in P.KLIMA:
        blok(msp, "M_KLIMA_IC", (x, y), "E-KUVVET-CIHAZ", {"KOD": kod, "KAPASITE": "1×16 A"})
    for kod, x, y, ad in P.ISITICI:
        blok(msp, "M_ISITICI", (x, y), "E-KUVVET-CIHAZ", {"KOD": kod, "GUC": "1×32 A"})
    for kod, x, y, ad in P.FAN:
        blok(msp, "M_FAN", (x, y), "E-KUVVET-CIHAZ", {"KOD": kod, "TANIM": "1×10 A"})
    for kod, x, y, t in P.KAMERA:   blok(msp, "E_KAMERA",  (x, y), "E-ZAYIF-KAMERA", {"KOD": kod})
    for kod, x, y, t in P.HOPARLOR: blok(msp, "E_HOPARLOR",(x, y), "E-ZAYIF-SES",    {"KOD": kod})
    for kod, x, y, t in P.VERI:     blok(msp, "E_VERI",    (x, y), "E-ZAYIF-VERI",   {"KOD": kod})
    for kod, x, y, t in P.DEDEKTOR: blok(msp, "E_DEDEKTOR",(x, y), "E-ZAYIF-YANGIN", {"KOD": kod})
    for kod, x, y, t in P.YANGIN:   blok(msp, "E_YANGIN_BUTON", (x, y), "E-ZAYIF-YANGIN", {"KOD": kod})
    cevrim = [P.PANO] + [(d[1], d[2]) for d in P.DEDEKTOR] + [(P.YANGIN[2][1], P.YANGIN[2][2])]
    poli(msp, cevrim, "E-ZAYIF-LINYE", False)
    blok(msp, "E_PANO", P.PANO, "E-PANO",
         {"KOD": "AP", "TANIM": f"3×{P.ANA_KESICI//3} A · {len(P.LINYE)} linye"})
    for ad, d in P.ISLAK.items():
        q = d["tum"].representative_point()
        yazi(msp, (q.x*K, q.y*K-780), "KAMERA YOK", 190, "E-YAZI", stil="GYM-B", renk=1)

# ══════════════════════ ANTET VE PAFTALAR ══════════════════════════════════════
def antet_blogu(doc):
    """A3 antedi — kâğıt alanında 1:1, mm."""
    if "ANTET_A3" in doc.blocks: return
    b = doc.blocks.new("ANTET_A3")
    W_, H_ = 170.0, 92.0
    b.add_lwpolyline([(0,0),(W_,0),(W_,H_),(0,H_)], close=True, dxfattribs={"layer":"0"})
    for y in (12, 24, 36, 48, 62, 74):
        b.add_line((0,y),(W_,y), dxfattribs={"layer":"0"})
    b.add_line((52,0),(52,62), dxfattribs={"layer":"0"})
    def t(txt, p, h_=3.0, stil="GYM", hiza=TextEntityAlignment.MIDDLE_LEFT):
        e = b.add_text(txt, height=h_, dxfattribs={"layer":"0","style":stil})
        e.set_placement(p, align=hiza); return e
    t("PROJE", (2, 87.5), 2.2); t("DİSİPLİN", (2, 70.5), 2.2)
    t("PAFTA ADI", (2, 58.5), 2.2); t("PAFTA NO", (2, 46.5), 2.2)
    t("ÖLÇEK", (54, 46.5), 2.2);  t("TARİH", (2, 34.5), 2.2)
    t("REVİZYON", (54, 34.5), 2.2); t("BİRİM", (2, 22.5), 2.2); t("DURUM", (54, 22.5), 2.2)
    def a(etiket, istem, p, h_=3.4, stil="GYM-B"):
        ad = b.add_attdef(etiket, dxfattribs={"height": h_, "style": stil, "layer": "0",
                                              "prompt": istem})
        ad.dxf.insert = p; ad.dxf.text = ""
        return ad
    a("PROJE", "Proje adi", (2, 79), 3.2)
    a("DISIPLIN", "Disiplin", (2, 65.5), 3.4)
    a("PAFTA_ADI", "Pafta adi", (2, 53.5), 3.4)
    a("PAFTA_NO", "Pafta no", (2, 41.0), 3.6)
    a("OLCEK", "Olcek", (54, 41.5), 3.4)
    a("TARIH", "Tarih", (2, 29.5), 3.0, "GYM")
    a("REV", "Revizyon", (54, 29.5), 3.0, "GYM")
    a("BIRIM", "Birim", (2, 17.5), 3.0, "GYM")
    a("DURUM", "Durum", (54, 17.5), 3.0, "GYM")
    ad = b.add_attdef("NOT", dxfattribs={"height": 2.2, "style": "GYM", "layer": "0",
                                         "prompt": "Alt not"})
    ad.dxf.insert = (2, 6); ad.dxf.text = ""

PAFTALAR = {
 "M-01": ("HAVALANDIRMA PLANI", "MEKANİK TESİSAT",
          ["M-KLIMA-", "M-SIHHI-", "E-"]),
 "M-02": ("İKLİMLENDİRME PLANI", "MEKANİK TESİSAT",
          ["M-HAVA-", "M-SIHHI-", "E-"]),
 "M-03": ("SIHHİ TESİSAT PLANI", "MEKANİK TESİSAT",
          ["M-HAVA-", "M-KLIMA-", "E-"]),
 "M-04": ("MEKANİK GENEL YERLEŞİM", "MEKANİK TESİSAT", ["E-"]),
 "E-01": ("AYDINLATMA PLANI", "ELEKTRİK",
          ["M-", "E-KUVVET-", "E-ZAYIF-"]),
 "E-02": ("PRİZ VE KUVVET PLANI", "ELEKTRİK",
          ["M-", "E-AYD-", "E-ZAYIF-"]),
 "E-03": ("ZAYIF AKIM PLANI", "ELEKTRİK",
          ["M-", "E-AYD-", "E-KUVVET-"]),
 "E-04": ("ELEKTRİK GENEL YERLEŞİM", "ELEKTRİK", ["M-"]),
 "A-01": ("MİMARİ ALTLIK", "MİMARİ", ["M-", "E-"]),
}

def pafta_ekle(doc, no, notlar=""):
    ad, disiplin, donan = PAFTALAR[no]
    lay = doc.layouts.new(f"{no} {ad}")
    lay.page_setup(size=(420, 297), margins=(0, 0, 0, 0), units="mm")
    psp = lay
    psp.add_lwpolyline([(10,10),(410,10),(410,287),(10,287)], close=True,
                       dxfattribs={"layer": "G-ANTET"})
    ref = psp.add_blockref("ANTET_A3", (236, 12), dxfattribs={"layer": "G-ANTET"})
    ref.add_auto_attribs({
        "PROJE": "MALTEPE / İDEALTEPE — GYM DÖNÜŞÜMÜ",
        "DISIPLIN": disiplin, "PAFTA_ADI": ad, "PAFTA_NO": no,
        "OLCEK": "1 / 75", "TARIH": P.TARIH, "REV": P.REV,
        "BIRIM": "milimetre (mm)", "DURUM": "ÖN TASARIM",
        "NOT": "Yerinde doğrulanmadan ve ruhsat alınmadan uygulama yapılamaz."})
    vp = psp.add_viewport(center=(122, 150), size=(216, 268),
                          view_center_point=(CX, CY), view_height=20100)
    vp.dxf.layer = "G-ANTET"
    don = [l[0] for l in X.KATMANLAR if any(l[0].startswith(d) for d in donan)]
    if don: vp.frozen_layers = don
    # sağ sütun: lejant ve notlar
    y = 280
    psp.add_text("LEJANT", height=4.0, dxfattribs={"layer": "G-ANTET", "style": "GYM-B"}
                 ).set_placement((236, y), align=TextEntityAlignment.MIDDLE_LEFT)
    y -= 8
    gorunur = [l for l in X.KATMANLAR
               if not any(l[0].startswith(d) for d in donan)
               and (l[0].startswith(("M-", "E-")) or l[0].startswith("A-DUVAR"))]
    for kat, renk, lt, lw, ack in gorunur[:26]:
        psp.add_line((236, y), (246, y), dxfattribs={"layer": "G-ANTET", "color": renk,
                                                     "linetype": lt})
        psp.add_text(ack, height=2.4, dxfattribs={"layer": "G-ANTET", "style": "GYM"}
                     ).set_placement((249, y), align=TextEntityAlignment.MIDDLE_LEFT)
        y -= 5.2
    if notlar:
        y -= 4
        psp.add_text("NOTLAR", height=3.4, dxfattribs={"layer": "G-ANTET", "style": "GYM-B"}
                     ).set_placement((236, y), align=TextEntityAlignment.MIDDLE_LEFT)
        y -= 6
        for satir in notlar.split("\n"):
            psp.add_text(satir, height=2.4, dxfattribs={"layer": "G-ANTET", "style": "GYM"}
                         ).set_placement((236, y), align=TextEntityAlignment.MIDDLE_LEFT)
            y -= 4.6
    return lay

NOTLAR = {
 "M-01": "Kanallar galvaniz sac, TS EN 1507 sinif B.\nBesleme ve egzoz hatti 19 mm izoleli.\n"
         "Her bransman basi debi ayar damperi.\nDevreye almada balanslama ve olcum raporu.",
 "M-02": "Ic unite montaj kotu 2,40 m (alt kot).\nBakir hat izoleli, dis unite konsolu\n"
         "titresim takozlu.\nDrenaj %1 egimli.",
 "M-03": "Pis su %2 egimli.\nTum islak hacimde sifonlu yer suzgeci.\n"
         "SOKUM SONRASI ILK IS: mevcut pis su\nbaglanti kotunun olculmesi.",
 "M-04": "Mekanik disiplin genel yerlesimi.\nAyrinti icin M-01, M-02, M-03 paftalari.",
 "E-01": "Tesisat siva alti spiral boru icinde,\nNHXMH halojensiz kablo.\n"
         "Acil aydinlatma 3 saat bataryali.",
 "E-02": "Islak hacim linyeleri ayri 30 mA\nkacak akim rolesinden beslenir.\n"
         "Kardiyo ekipmani ayri linyede (P4).",
 "E-03": "SOYUNMA VE WC ICINE KAMERA KONULMAZ.\nYangin algilama panosu kesintisiz beslenir.\n"
         "Topraklama direnci <= 10 ohm.",
 "E-04": "Elektrik disiplin genel yerlesimi.\nAyrinti icin E-01, E-02, E-03 paftalari.",
 "A-01": "Mimari altlik — mevcut duvar korunur.\nKirmizi: yeni alcipan bolme.\n"
         "Olculer raster paftadan (+/-%3).",
}

def belge_uret(ad, mek=True, elk=True, paftalar=()):
    doc = X.yeni_belge(ad); X.bloklari_kur(doc); antet_blogu(doc)
    msp = doc.modelspace()
    mimari(msp); olculer(msp)
    if mek: mekanik(msp)
    if elk: elektrik(msp)
    for no in paftalar: pafta_ekle(doc, no, NOTLAR.get(no, ""))
    if "Layout1" in doc.layouts: doc.layouts.delete("Layout1")
    doc.set_modelspace_vport(height=14000, center=(CX, CY))
    return doc

def uret():
    setler = [
      ("GYM-MIM-Altlik-R2010.dxf",   False, False, ("A-01",)),
      ("GYM-MEK-Uygulama-R2010.dxf", True,  False, ("M-01","M-02","M-03","M-04")),
      ("GYM-ELK-Uygulama-R2010.dxf", False, True,  ("E-01","E-02","E-03","E-04")),
      ("GYM-MEP-Birlesik-R2010.dxf", True,  True,
       ("A-01","M-01","M-02","M-03","M-04","E-01","E-02","E-03","E-04")),
    ]
    uretilen = []
    for dosya, mek, elk, pf in setler:
        doc = belge_uret(dosya, mek, elk, pf)
        yol = CAD/dosya; doc.saveas(yol)
        n_ent = len(list(doc.modelspace()))
        print(f"  → cad/{dosya:32s} {n_ent:5d} nesne · {len(pf)} pafta · "
              f"{yol.stat().st_size/1e6:.2f} MB")
        uretilen.append(yol)
    return uretilen


# ══════════════════════ PAFTA ÖNİZLEME PDF'İ ═══════════════════════════════════
def onizleme_pdf(cikti="output/Gym_MEP_CAD_Paftalar.pdf"):
    """Tüm paftaları tek PDF'e basar — CAD olmadan kontrol için."""
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    doc = ezdxf.readfile(CAD/"GYM-MEP-Birlesik-R2010.dxf")
    sira = ["A-01", "M-01", "M-02", "M-03", "M-04", "E-01", "E-02", "E-03", "E-04"]
    adlar = {n: f"{n} {PAFTALAR[n][0]}" for n in sira}
    with PdfPages(cikti) as pdf:
        for no in sira:
            lay = doc.layouts.get(adlar[no])
            # Önizleme motoru görünüm penceresi bazlı katman dondurmayı uygulamaz;
            # aynı sonucu vermek için o paftanın donmuş katmanları geçici olarak kapatılır.
            donmus = []
            for vp in lay.query("VIEWPORT"):
                donmus += list(vp.frozen_layers)
            for k in set(donmus):
                if k in doc.layers: doc.layers.get(k).off()
            fig = plt.figure(figsize=(16.54, 11.69))
            ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
            Frontend(RenderContext(doc), MatplotlibBackend(ax)).draw_layout(lay, finalize=True)
            pdf.savefig(fig, facecolor="white"); plt.close(fig)
            for k in set(donmus):
                if k in doc.layers: doc.layers.get(k).on()
    print(f"  → {cikti}  ·  {len(sira)} pafta")

def paketle(cikti="output/Gym_MEP_CAD_Seti_DXF.zip"):
    with zipfile.ZipFile(cikti, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(CAD.iterdir()):
            if f.is_file(): z.write(f, f"Gym_MEP_CAD_Seti/{f.name}")
    print(f"  → {cikti}  ·  {sum(1 for f in CAD.iterdir() if f.is_file())} dosya · "
          f"{Path(cikti).stat().st_size/1e6:.2f} MB")

# ══════════════════════ CAD OKUMA NOTU VE KATMAN LİSTESİ ═══════════════════════
def belgeler():
    import csv
    with open(CAD/"KATMAN-LISTESI.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Katman adı", "ACI renk", "Çizgi tipi", "Kalem (1/100 mm)", "Açıklama"])
        for r in X.KATMANLAR: w.writerow(r)
    bloklar = sorted(b.name for b in X.yeni_belge("x").blocks if not b.name.startswith("*")) \
              if False else None
    doc = ezdxf.readfile(CAD/"GYM-MEP-Birlesik-R2010.dxf")
    bl = sorted(b.name for b in doc.blocks if not b.name.startswith("*"))
    pafta_sat = "\n".join(
        f"  {no:6s} {PAFTALAR[no][0]:32s} ({PAFTALAR[no][1]})"
        for no in ["A-01","M-01","M-02","M-03","M-04","E-01","E-02","E-03","E-04"])
    kat_sat = "\n".join(f"  {a:18s} renk {r:3d}  {lt:11s} {lw:3d}  {ack}"
                        for a, r, lt, lw, ack in X.KATMANLAR)
    metin = f"""GYM DÖNÜŞÜMÜ — MEP CAD SETİ
{P.PROJE}
{P.REV} · {P.TARIH}
================================================================================

1 · FORMAT VE ÖNEMLİ UYARI
--------------------------------------------------------------------------------
Bu set DXF R2010 (AC1024) formatındadır. .dwg DEĞİLDİR.

DWG kapalı (tescilli) bir formattır ve açık kaynaklı hiçbir kütüphane onu güvenilir
biçimde YAZAMAZ. Bu nedenle set, AutoCAD'in kendi değişim formatı olan DXF ile
üretilmiştir. Pratikte fark yoktur:

  AutoCAD / BricsCAD / ZWCAD / GstarCAD / DraftSight bu dosyaları doğrudan açar.
  DWG'ye çevirmek için:  dosyayı açın  →  Farklı Kaydet  →  AutoCAD 2018 Çizim (*.dwg)
  Toplu çevirme için:    AutoCAD "DWG Convert" veya ODA File Converter (ücretsiz)

2 · BİRİM VE ÖLÇEK
--------------------------------------------------------------------------------
  Model uzayı birimi : MİLİMETRE  ($INSUNITS = 4)
  Çizim ölçeği       : 1 / 1 (model uzayında gerçek boyut)
  Pafta ölçeği       : 1 / 75  (A3 · 420 × 297 mm)
  Ölçülendirme stili : GYM-75  (DIMSCALE = 75)
  Yazı stili         : GYM / GYM-B  (Arial — Türkçe karakter destekli)

  Not: cm ile çalışan bir ofise verilecekse model uzayını 0,1 ile ölçekleyin
  (SCALE komutu, referans nokta 0,0) ve DIMSCALE'i 7,5 yapın.

3 · DOSYALAR
--------------------------------------------------------------------------------
  GYM-MIM-Altlik-R2010.dxf      Mimari altlık — diğerlerine XREF olarak bağlanabilir
  GYM-MEK-Uygulama-R2010.dxf    Mekanik — 4 pafta
  GYM-ELK-Uygulama-R2010.dxf    Elektrik — 4 pafta
  GYM-MEP-Birlesik-R2010.dxf    Tümü — 9 pafta (tek dosyada çalışmak isteyenler için)
  KATMAN-LISTESI.csv            Katman standardı (Excel ile açılır)

4 · PAFTALAR (kâğıt alanı sekmeleri)
--------------------------------------------------------------------------------
{pafta_sat}

  Her paftanın görüntü penceresinde o disipline ait olmayan katmanlar DONDURULMUŞTUR
  (VP Freeze). Model uzayı tek ve ortaktır; paftalar aynı modeli farklı katman
  durumlarıyla gösterir. Bir katmanı bir paftada görmek isterseniz o paftanın
  görüntü penceresini seçip katmanı çözün — diğer paftalar etkilenmez.

5 · KATMAN STANDARDI ({len(X.KATMANLAR)} katman)
--------------------------------------------------------------------------------
  Önek:  A- mimari · M- mekanik · E- elektrik · G- genel (ölçü, antet, yazı)

{kat_sat}

6 · BLOK KÜTÜPHANESİ ({len(bl)} blok)
--------------------------------------------------------------------------------
  {", ".join(bl)}

  Sembol blokları ÖZNİTELİKLİDİR. Örneğin menfez bloklarında KOD ve DEBI,
  priz bloklarında KOD ve LINYE öznitelikleri vardır. ATTEXT veya DATAEXTRACTION
  komutuyla bu öznitelikler doğrudan metraj tablosuna aktarılabilir.

7 · BU SET NE DEĞİLDİR — DÜRÜST SINIR
--------------------------------------------------------------------------------
  Bu bir ÖN TASARIM (avan) seviyesindeki CAD setidir; uygulama projesi formatında
  düzenlenmiştir ama henüz uygulama projesi DEĞİLDİR. Uygulama projesine
  dönüşmesi için gerekenler:

  a) Ölçülmüş mimari altlık. Mevcut geometri, raster pafta izlenerek üretilmiştir
     (±%3). İşverenden DXF (R2010) export veya yerinde rölöve alınmalıdır.
  b) Tavan yüksekliği, kiriş altı kotları ve kolon konumları. Kanal güzergâhları
     bu veriler olmadan kesinleşemez.
  c) Mevcut pis su bağlantısının kotu. Sıhhi tesisatın tamamı buna bağlıdır.
  d) Mevcut elektrik abonelik gücü ve pano kapasitesi.
  e) Yetkili mühendis onayı. Türkiye'de mekanik ve elektrik uygulama projeleri
     ilgili meslek odasına kayıtlı mühendis tarafından imzalanır ve onaylanır;
     bu set o imzanın yerine geçmez, ona girdi oluşturur.

8 · SORUMLULUK
--------------------------------------------------------------------------------
  Ön tasarım — yerinde doğrulanmadan ve ruhsat alınmadan uygulama yapılamaz.
  Tüm ölçüler kontrol edilmelidir. Yerel uygulama farklılık gösterebilir.
"""
    (CAD/"OKUBENI-CAD.txt").write_text(metin, encoding="utf-8")
    print(f"  → cad/OKUBENI-CAD.txt · cad/KATMAN-LISTESI.csv")

if __name__ == "__main__":
    uret(); belgeler(); onizleme_pdf(); paketle()
