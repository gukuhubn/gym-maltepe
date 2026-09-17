# -*- coding: utf-8 -*-
"""MİMARİ UYGULAMA PROJESİ — A3 yatay, 13 pafta."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union
import proj as P, helpers as h, draw as D, draw_mep as MP, draw_mim as M
import draw_duvar as DD

W, HH = 420*mm, 297*mm
TOP, BOT, L, R = HH-24.6*mm, 14*mm, 12*mm, W-12*mm
CW = R-L
N = 14
DISIPLIN = "MİMARİ UYGULAMA PROJESİ"

PAFTA_ADI = {
 1:("A-01","Kapak · genel notlar · pafta indeksi"),
 2:("A-02","Mevcut durum ve yıkım / söküm planı"),
 3:("A-03","Uygulama planı — bölme, kapı, mahal"),
 4:("A-04","Zemin kaplama planı"),
 5:("A-05","Tavan planı (RCP) ve tesisat koordinasyonu"),
 6:("A-06","Kesit A-A"),
 7:("A-07","Kesit B-B"),
 8:("A-08","İç görünüşler G-01 … G-04"),
 9:("A-09","Mahal listesi — kaplama ve bitiş"),
10:("A-10","Kapı ve pencere listesi · duvar tipleri"),
11:("A-11","İmalat detayları I — zemin ve kot geçişi"),
12:("A-12","İmalat detayları II — ıslak hacim, tavan, ayna"),
13:("A-13","Yangın ve tahliye planı"),
14:("A-14","Duvar tipleri — yatay kesit 1/10"),
}

def sayfa(c, no, baslik, ust=None):
    h.band(c, W, HH, no, baslik, ust or DISIPLIN)
    h.footer(c, W, no, N)

def kunye(c, x, y, w, pafta, olcek="1/75 (A3)", durum="Uygulama — yerinde doğrulanacak"):
    hgt = 26*mm
    h.kutu(c, x, y-hgt, w, hgt, h.PAPER, h.GREY_L)
    c.setFillColor(h.NAVY); c.rect(x, y-hgt, w, 5.4*mm, 0, 1)
    h.txt(c, x+3*mm, y-hgt+1.7*mm, h.TR_UP(DISIPLIN), h.FB, 5.6, HexColor("#FFFFFF"))
    h.txt(c, x+w-3*mm, y-hgt+1.7*mm, P.REV, h.FB, 5.6, h.COPPER, "r")
    yy = y-5*mm
    for k, v in [("Pafta", pafta), ("Ölçek", olcek), ("Tarih", P.TARIH), ("Durum", durum)]:
        h.txt(c, x+3*mm, yy, k, h.FB, 5.2, h.GREY)
        h.txt(c, x+w-3*mm, yy, v, h.F, 5.6, h.INK, "r")
        yy -= 4.6*mm
    return y-hgt

# ══ ORTAK PLAN ALTLIĞI ═════════════════════════════════════════════════════════
def plan_altlik(c, x, y, w, hgt, zemin=True):
    v = D.View(c, x, y, w, hgt)
    if zemin: MP.altlik(v)
    return v

def mahal_balonlari(c, v, sadece=None, ek=None):
    for no, pt in P.MAHAL_NOKTA.items():
        if sadece and no not in sadece: continue
        px, py = v.p(pt)
        M.balon(c, px, py+(ek or 0), no, r=2.7*mm)

# ══ 1 · KAPAK ══════════════════════════════════════════════════════════════════
def s1(c):
    sayfa(c, 1, "Mimari uygulama projesi", "Kapsam · genel notlar · pafta indeksi · mahal özeti")
    y = TOP
    y = h.para(c, L, y-2*mm,
      "Bu set, Maltepe / İdealtepe'deki mobilya mağazasının fonksiyonel antrenman stüdyosuna "
      f"dönüşümü için MİMARİ UYGULAMA PROJESİDİR. Net iç kullanım alanı {h.tl(P.A['ic_toplam'],2)} m², "
      f"{len(P.MAHAL_LISTESI)} mahal. Set; yıkım, uygulama planı, zemin kaplama, tavan planı, iki kesit, "
      "dört iç görünüş, mahal listesi, kapı-pencere listesi, duvar tipleri, sekiz imalat detayı ve "
      "yangın-tahliye planından oluşur. Mekanik (M-01…M-06) ve elektrik (E-01…E-06) paftaları ayrı "
      "dosyalardadır ve bu setle aynı geometrik altlığı kullanır. Bu set müteahhidin imalat yapabilmesi "
      "için gereken malzeme, katman ve kot bilgisini taşır; ruhsat başvurusu için proje müellifi mimar "
      "tarafından imzalanmış 1/50 takım ayrıca düzenlenecektir.", CW, h.F, 8.2, h.INK, 11.4)

    # KPI şeridi
    kw = (CW-3*5*mm)/4; ky = y-8*mm
    for i, (ust, dg, alt) in enumerate([
        ("NET İÇ ALAN", f"{h.tl(P.A['ic_toplam'],2)} m²", f"{len(P.MAHAL_LISTESI)} mahal · duvar payı {h.tl(P.MAHAL_DUVAR_PAYI,2)} m²"),
        ("ZEMİN KAPLAMA TİPİ", f"{len(P.ZEMIN_TIPLERI)} tip", "Z1–Z6 · bitmiş kot ±0,00 (ıslak −0,02)"),
        ("DUVAR / TAVAN TİPİ", f"{len(P.DUVAR_TIPLERI)} + {len(P.TAVAN_TIPLERI)}", "D1–D6 · T1–T4"),
        ("KAPI · PENCERE", f"{sum(k[1] for k in P.KAPI_LISTESI)} + {len(P.PENCERE_LISTESI)}", "K01–K09 · P01–P02")]):
        h.kpi(c, L+i*(kw+5*mm), ky-22*mm, kw, 22*mm, ust, dg, alt)
    y = ky-22*mm-9*mm

    # sol: genel notlar
    w1 = CW*0.545
    h.txt(c, L, y, h.TR_UP("Genel notlar — uygulamada bağlayıcıdır"), h.FB, 8.4, h.NAVY)
    yy = y-6*mm
    for i, nt in enumerate(P.MIMARI_NOTLAR):
        lines = h.wrap(c, nt, h.F, 6.3, w1-7*mm)
        h.txt(c, L+1*mm, yy, f"{i+1:02d}", h.FB, 6.3, h.COPPER)
        for ln in lines:
            h.txt(c, L+7*mm, yy, ln, h.F, 6.3, h.INK); yy -= 3.35*mm
        yy -= 1.5*mm

    # sağ: pafta indeksi + mahal özeti
    x2 = L+w1+8*mm; w2 = CW-w1-8*mm
    h.txt(c, x2, y, h.TR_UP("Pafta indeksi"), h.FB, 8.4, h.NAVY)
    rows = [[PAFTA_ADI[i][0], PAFTA_ADI[i][1],
             "1/75" if i in (2,3,4,5,13) else ("1/50" if i in (6,7,8) else ("1/10" if i in (11,12) else "—"))]
            for i in range(1, N+1)]
    y2 = h.tablo(c, x2, y-5*mm, [("Pafta",0.13),("İçerik",0.68),("Ölçek",0.19)], rows, w2,
                 satir_h=5.4*mm, bas_h=6.2*mm, fs=6.2, hfs=6.0, hizala=["l","l","c"])
    h.txt(c, x2, y2-6*mm, h.TR_UP("Mahal özeti"), h.FB, 8.4, h.NAVY)
    rows2 = [[m[0], m[1], f"{h.tl(m[2],2)}", m[3], m[6], ("%.2f" % m[7]).replace(".",",")]
             for m in P.MAHAL_LISTESI]
    rows2.append(["", h.TR_UP("TOPLAM (net)"), f"{h.tl(P.MAHAL_TOPLAM,2)}", "", "", ""])
    h.tablo(c, x2, y2-11*mm, [("No",0.09),("Mahal",0.40),("m²",0.13),("Zemin",0.12),
                              ("Tavan",0.12),("Kot",0.14)], rows2, w2,
            satir_h=5.2*mm, bas_h=6.2*mm, fs=6.1, hfs=6.0, hizala=["c","l","r","c","c","r"])

# ══ 2 · YIKIM / SÖKÜM ══════════════════════════════════════════════════════════
def s2(c):
    sayfa(c, 2, "Mevcut durum ve yıkım / söküm planı", "Sökülecek · korunacak · dokunulmayacak")
    pw = CW*0.575
    v = plan_altlik(c, L, BOT+8*mm, pw, TOP-BOT-10*mm)
    # sökülecek kaplama = tüm iç alan
    ic = unary_union([P.SALON, P.ERKEK, P.KADIN])
    D.poly(v, ic, fill=HexColor("#2F6FB3"), alpha=0.14)
    # şap kırımı = ıslak hacimler
    for ad, d in P.ISLAK.items():
        for n in ("dus", "wc"):
            D.poly(v, d[n], fill=HexColor("#C8322B"), alpha=0.30, stroke=HexColor("#C8322B"), lw=0.9)
    # korunacak kabuk
    D.poly(v, ic.buffer(D.DUVAR_T, join_style=2).difference(ic), fill=HexColor("#6B7078"))
    D.cephe(v)
    for (x_, y_), gen, aci, lbl in P.KAPILAR[:1]:
        pass
    # etiketler
    D.etiket(v, (4.6, 10.6), "MEVCUT KAPLAMA SÖKÜMÜ (Y03)", 6.0, HexColor("#1B4F86"), h.FB, "c")
    D.etiket(v, (4.6, 10.6), "tüm iç alan · 103,78 m²", 5.2, HexColor("#2F6FB3"), h.F, "c", dy=-3.4)
    D.etiket(v, (9.05, 7.80), "ŞAP KIRIMI (Y04)", 5.4, HexColor("#8F2019"), h.FB, "c", dy=7.5)
    D.etiket(v, (9.05, 7.80), "ort. 70 mm", 4.8, HexColor("#C8322B"), h.F, "c", dy=3.9)
    D.etiket(v, (2.1, 2.3), "KORUNACAK KABUK", 5.8, HexColor("#3A3F46"), h.FB, "c")
    D.etiket(v, (2.1, 2.3), "taşıyıcı sisteme dokunulmaz", 5.0, HexColor("#6B7078"), h.F, "c", dy=-3.4)
    D.kuzey_ok(v, L+pw-13*mm, TOP-13*mm); D.olcek_cubugu(v, L+5*mm, BOT+11*mm)
    h.lejant(c, L+5*mm, BOT+2*mm, [(HexColor("#BFD3E8"), "Kaplama sökümü"),
        (HexColor("#E6A9A4"), "Şap kırımı — tesisat"), (HexColor("#6B7078"), "Korunacak kabuk")], 6.0)

    x2 = L+pw+7*mm; w2 = R-x2
    yy = kunye(c, x2, TOP, w2, "A-02", "1/75 (A3)")
    h.txt(c, x2, yy-6*mm, h.TR_UP("Yıkım ve söküm iş kalemleri"), h.FB, 8.0, h.NAVY)
    rows = [[k[0], k[1], f"{h.tl(k[2],2) if isinstance(k[2],float) else k[2]} {k[3]}"] for k in P.YIKIM]
    yy = h.tablo(c, x2, yy-11*mm, [("Kod",0.10),("Tanım",0.68),("Metraj",0.22)], rows, w2,
                 satir_h=6.0*mm, bas_h=6.6*mm, fs=6.2, hfs=6.0, hizala=["c","l","r"])
    yy = h.notkutu(c, x2, yy-5*mm, w2, "Söküm öncesi zorunlu adımlar", P.YIKIM_NOT,
                   fs=6.3, acc=h.RED)
    h.notkutu(c, x2, yy-4*mm, w2, "Sıralama",
      "1) Enerji ve su kesilir, mevcut sayaç okuması tutanaklanır.  2) Mevcut durum rölövesi ve fotoğraf "
      "kaydı alınır.  3) Devralınacak mobilya ayrılır.  4) Asma tavan ve aydınlatma sökülür.  "
      "5) Zemin kaplaması sökülür, şap kotu ölçülür — bu ölçüm tüm tesviye şapı kalınlıklarının girdisidir.  "
      "6) Islak hacim şap kırımı ve pis su kotu tespiti yapılır; Seçenek A/B kararı burada verilir.  "
      "7) Moloz aynı gün tahliye edilir; kat sahanlığı ve asansör korunur.",
      fs=6.3, acc=h.NAVY2)

# ══ 3 · UYGULAMA PLANI ═════════════════════════════════════════════════════════
def s3(c):
    sayfa(c, 3, "Uygulama planı", "Bölme duvarları · kapılar · mahal numaraları · kotlar")
    pw = CW*0.615
    v = plan_altlik(c, L, BOT+8*mm, pw, TOP-BOT-10*mm)
    D.zeminler(v, alpha=0.35)
    DD.plan_bolme(v, dikme=True)          # gerçek C50 dikme @400 mm
    D.cephe(v); D.kapilar(v)
    D.mobilya(v, etiketli=True)
    # kapı kodları
    KP = {0:("K01",-5.2,0.0), 1:("K03",-5.8,2.6), 2:("K04",-5.8,-2.8), 3:("K02",0.0,-5.4)}
    for i, ((x_, y_), gen, aci, lbl) in enumerate(P.KAPILAR):
        kod, dx_, dy_ = KP[i]; px, py = v.p((x_, y_))
        c.saveState(); c.setStrokeColor(HexColor("#B87333")); c.setLineWidth(0.4)
        c.line(px, py, px+dx_*mm, py+dy_*mm); c.restoreState()
        M.balon(c, px+dx_*mm, py+dy_*mm, kod, r=2.5*mm, dolgu="#FFF3E3", kontur="#B87333")
    for kod, pt in (("K05",(10.30,8.55)), ("K06",(9.35,0.80)), ("K07",(8.30,6.62)),
                    ("K08",(11.30,1.55)), ("K09",(2.55,7.05))):
        px, py = v.p(pt); M.balon(c, px, py, kod, r=2.5*mm, dolgu="#FFF3E3", kontur="#B87333")
    mahal_balonlari(c, v)
    # duvar tipi etiketleri
    for tip, pt, aci in (("D2",(8.35,6.30),0), ("D3",(9.72,6.30),0), ("D4",(7.35,0.42),0),
                         ("D1",(5.90,11.30),0), ("D6",(5.05,0.42),0), ("D5",(10.30,2.30),0)):
        px, py = v.p(pt)
        c.saveState(); c.setFillColor(HexColor("#C8322B")); c.setStrokeColor(HexColor("#FFFFFF"))
        c.setLineWidth(0.7); c.roundRect(px-4.0*mm, py-1.9*mm, 8.0*mm, 3.8*mm, 0.9*mm, 1, 1)
        c.restoreState(); h.txt(c, px, py-1.15*mm, tip, h.FB, 5.4, HexColor("#FFFFFF"), "c")
    # kesit hatları
    for ad, (a, b, _) in P.KESIT_HATLARI.items():
        M.kesit_isareti(v, a, b, ad)
    # dış ölçüler
    D.olcu(v, (3.24, 0.0), (8.92, 0.0), off=0.68)
    D.olcu(v, (0.0, 6.84), (0.58, 1.25), off=0.62)
    D.kuzey_ok(v, L+pw-13*mm, TOP-13*mm); D.olcek_cubugu(v, L+5*mm, BOT+11*mm)
    h.lejant(c, L+5*mm, BOT+2*mm, [(HexColor("#C8322B"), "Yeni bölme (D2/D3)"),
        (HexColor("#6B7078"), "Mevcut duvar (D1)"), (HexColor("#B87333"), "Kapı kodu"),
        (HexColor("#16273D"), "Mahal no")], 6.0)

    x2 = L+pw+7*mm; w2 = R-x2
    yy = kunye(c, x2, TOP, w2, "A-03", "1/75 (A3)")
    h.txt(c, x2, yy-6*mm, h.TR_UP("Kot şeması"), h.FB, 8.0, h.NAVY)
    _mah = {t: " · ".join(sorted({m[0] for m in P.MAHAL_LISTESI if m[6] == t}))
            for t in ("T1","T2","T3","T4")}
    rows = [["±0,00","Bitmiş zemin kotu — tüm kuru hacimler","Referans"],
            ["−0,02","Duş ve WC bitmiş zemin kotu","Su taşkını kontrolü · eşik profili"],
            [("%+.3f" % P.KOT_MEVCUT_SAP).replace(".", ",").replace("-", "−"),
             "Mevcut şap üst kotu (VARSAYIM)","Tesviye şapı bu farkı kapatır"]]
    for t in ("T3","T4","T2","T1"):
        kot = ("+%.2f" % P.TAVAN_KOT[t]).replace(".", ",")
        ad = [x[1] for x in P.TAVAN_TIPLERI if x[0] == t][0]
        not_ = ("Yapısal döşeme altı (VARSAYIM)" if t == "T1"
                else f"{int(P.TAVAN_BOSLUK[t]*1000)} mm tesisat boşluğu · "
                     f"serbestlik {P.TAVAN_SERBESTLIK.get(t, '—')} mm")
        rows.append([kot, f"{t} {ad.split('—')[0].strip()} — mahal {_mah[t]}", not_])
    yy = h.tablo(c, x2, yy-11*mm, [("Kot",0.20),("Tanım",0.52),("Not",0.28)], rows, w2,
                 satir_h=5.6*mm, bas_h=6.4*mm, fs=6.2, hfs=6.0, hizala=["r","l","l"])
    h.txt(c, x2, yy-6*mm, h.TR_UP("Bölme duvar metrajı"), h.FB, 8.0, h.NAVY)
    rows2 = [["D2","Alçıpan bölme — kuru hacim","100 mm","≈ 14,6 m² (VARSAYIM)"],
             ["D3","Alçıpan bölme — ıslak yüz","100 mm","≈ 21,4 m² (VARSAYIM)"],
             ["D4","Akustik giydirme — arena güney çeperi","95 mm","≈ 18,2 m²"],
             ["D5","Seramik kaplı duvar — ıslak","216 mm","≈ 46,2 m²"],
             ["D6","Ayna duvarı — arena güney çeperi","212 mm","≈ 9,6 m² (4,80 m × 2,00 m)"]]
    yy = h.tablo(c, x2, yy-11*mm, [("Tip",0.10),("Tanım",0.46),("Kalınlık",0.16),("Metraj",0.28)],
                 rows2, w2, satir_h=5.6*mm, bas_h=6.4*mm, fs=6.2, hfs=6.0, hizala=["c","l","c","r"])
    h.notkutu(c, x2, yy-5*mm, w2, "Bölme yüksekliği",
      "Tüm alçıpan bölmeler asma tavan üstünden geçerek yapısal döşemeye kadar (+3,20) yükseltilecektir. "
      "Asma tavan hizasında kesilen bölme, ıslak hacim kokusunu ve soyunma mahremiyetini koruyamaz; "
      "akustik performans (Rw ≈ 51 dB) da yalnızca tam yükseklikte geçerlidir.",
      fs=6.3, acc=h.RED)

# ══ 4 · ZEMİN KAPLAMA PLANI ════════════════════════════════════════════════════
Z_RENK = {"Z1":"#3A3F46","Z2":"#6B7078","Z3":"#C9A063","Z4":"#9FB8C4","Z5":"#B7C7CF","Z6":"#B87333"}
def s4(c):
    sayfa(c, 4, "Zemin kaplama planı", "Kaplama tipleri · kot · derz ve eğim yönü · süpürgelik")
    pw = CW*0.605
    v = plan_altlik(c, L, BOT+8*mm, pw, TOP-BOT-10*mm, zemin=False)
    ic = unary_union([P.SALON, P.ERKEK, P.KADIN])
    Z_MAHAL = {m[0]: m[3] for m in P.MAHAL_LISTESI}
    for ad, mno, g in P._MAHAL_GEOM:
        D.poly(v, g, fill=HexColor(Z_RENK[Z_MAHAL[mno]]), alpha=0.82)
    D.poly(v, ic.buffer(D.DUVAR_T, join_style=2).difference(ic), fill=HexColor("#6B7078"))
    D.poly(v, ic, stroke=HexColor("#3A3F46"), lw=0.7)
    D.ic_bolme(v, col=HexColor("#FFFFFF"))
    # ring platformu
    D.poly(v, P.hex_poly(*P.EKIPMAN[0][5]), fill=HexColor("#B87333"), alpha=0.9,
           stroke=HexColor("#7A4A1E"), lw=1.1)
    D.etiket(v, P.EKIPMAN[0][5], "Z6 +0,30", 5.6, HexColor("#FFFFFF"), h.FB, "c", dy=-1.6)
    # kauçuk karo derz ızgarası (1×1 m) — arena ve fonksiyonel
    for zn in ("ARENA · SERBEST AĞIRLIK", "FONKSİYONEL · KARDİYO"):
        g = [z[1] for z in P.ZONES if z[0] == zn][0]
        b = g.bounds
        for gx in range(int(b[0]), int(b[2])+2):
            seg = LineString([(gx, b[1]-1), (gx, b[3]+1)]).intersection(g)
            for s_ in (seg.geoms if seg.geom_type.startswith("Multi") else [seg]):
                if s_.geom_type == "LineString" and not s_.is_empty:
                    D.line(v, s_.coords[0], s_.coords[-1], HexColor("#FFFFFF"), 0.3)
        for gy in range(int(b[1]), int(b[3])+2):
            seg = LineString([(b[0]-1, gy), (b[2]+1, gy)]).intersection(g)
            for s_ in (seg.geoms if seg.geom_type.startswith("Multi") else [seg]):
                if s_.geom_type == "LineString" and not s_.is_empty:
                    D.line(v, s_.coords[0], s_.coords[-1], HexColor("#FFFFFF"), 0.3)
    # eğim okları — ıslak hacimler
    for ad, d in P.ISLAK.items():
        for n in ("dus", "wc"):
            q = d[n].representative_point(); b = d[n].bounds
            D.line(v, (b[0]+0.12, b[1]+0.12), (q.x, q.y), HexColor("#16273D"), 0.7)
            px, py = v.p((q.x, q.y))
            c.setFillColor(HexColor("#16273D")); c.circle(px, py, 0.9*mm, 0, 1)
            h.txt(c, px, py+2.0*mm, "%1,5", h.FB, 4.6, HexColor("#16273D"), "c")
    # tip etiketleri
    for mno, pt in P.MAHAL_NOKTA.items():
        zt = Z_MAHAL[mno]
        px, py = v.p(pt)
        c.saveState(); c.setFillColor(HexColor("#FFFFFF")); c.setStrokeColor(HexColor("#16273D"))
        c.setLineWidth(0.7); c.roundRect(px-5.6*mm, py-2.1*mm, 11.2*mm, 4.2*mm, 1.0*mm, 1, 1)
        c.restoreState()
        kot = "−0,02" if zt == "Z4" else "±0,00"
        h.txt(c, px, py-1.25*mm, f"{zt}  {kot}", h.FB, 5.2, HexColor("#16273D"), "c")
    D.kuzey_ok(v, L+pw-13*mm, TOP-13*mm); D.olcek_cubugu(v, L+5*mm, BOT+11*mm)
    h.lejant(c, L+5*mm, BOT+2*mm, [(HexColor(Z_RENK["Z1"]), "Z1 kauçuk 40+10"),
        (HexColor(Z_RENK["Z2"]), "Z2 kauçuk 20"), (HexColor(Z_RENK["Z3"]), "Z3 SPC/LVT"),
        (HexColor(Z_RENK["Z4"]), "Z4 seramik R11"), (HexColor(Z_RENK["Z5"]), "Z5 seramik R10"),
        (HexColor(Z_RENK["Z6"]), "Z6 ring platformu")], 5.8)

    x2 = L+pw+7*mm; w2 = R-x2
    yy = kunye(c, x2, TOP, w2, "A-04", "1/75 (A3)")
    h.txt(c, x2, yy-6*mm, h.TR_UP("Zemin kaplama tipleri"), h.FB, 8.0, h.NAVY)
    rows = [[z[0], z[1].split(" — ")[0], f"{P.ZEMIN_KALINLIK[z[0]]} mm",
             ("±0,00" if abs(z[3]) < 0.005 else ("%+.2f" % z[3]).replace(".", ",").replace("-", "−"))]
            for z in P.ZEMIN_TIPLERI]
    yy = h.tablo(c, x2, yy-11*mm, [("Tip",0.10),("Mahal / kaplama",0.54),("Toplam",0.18),("Bitmiş kot",0.18)],
                 rows, w2, satir_h=5.6*mm, bas_h=6.4*mm, fs=6.2, hfs=6.0, hizala=["c","l","r","r"])
    h.txt(c, x2, yy-6*mm, h.TR_UP("Performans şartı"), h.FB, 8.0, h.NAVY)
    yyy = yy-11*mm
    for z in P.ZEMIN_TIPLERI[:5]:
        h.txt(c, x2, yyy, z[0], h.FB, 6.3, h.COPPER)
        for ln in h.wrap(c, z[4], h.F, 6.1, w2-8*mm):
            h.txt(c, x2+8*mm, yyy, ln, h.F, 6.1, h.INK); yyy -= 3.3*mm
        yyy -= 1.4*mm
    h.txt(c, x2, yyy-2*mm, h.TR_UP("Süpürgelik"), h.FB, 8.0, h.NAVY)
    yyy = h.tablo(c, x2, yyy-7*mm, [("Kod",0.10),("Tanım",0.68),("Mahal",0.22)],
                  [[sp[0], sp[1], {"S1":"102 · 103","S2":"101 · 104","S3":"106 · 107 · 109 · 110",
                                   "S4":"105 · 108"}[sp[0]]] for sp in P.SUPURGELIK], w2,
                  satir_h=5.4*mm, bas_h=6.2*mm, fs=6.0, hfs=5.9, hizala=["c","l","c"])
    h.notkutu(c, x2, yyy-5*mm, w2, "Kot sürekliliği — kontrol edildi",
      "Tüm kuru hacimlerde bitmiş zemin kotu ±0,00'dır; tesviye şapı kalınlıkları (Z1: 3 · Z2: 30 · "
      "Z3: 42 · Z5: 38 mm) farklı kaplama kalınlıklarını eşitler. Mahaller arasında eşik veya kot farkı "
      "oluşmaz. Yalnızca duş ve WC bitmiş kotu −0,02'dir; bu fark kapı altında 20 mm'lik eğimli "
      "alüminyum eşik profili ile karşılanır ve su taşkınını mahal içinde tutar.",
      fs=6.3, acc=h.GREEN)

# ══ 5 · TAVAN PLANI ════════════════════════════════════════════════════════════
T_RENK = {"T1":"#3A3F46","T2":"#EDE7DC","T3":"#CFE0EA","T4":"#E2E8EC"}
def s5(c):
    sayfa(c, 5, "Tavan planı (RCP)", "Tavan tipleri · kotlar · armatür, menfez ve dedektör koordinasyonu")
    pw = CW*0.605
    v = plan_altlik(c, L, BOT+8*mm, pw, TOP-BOT-10*mm, zemin=False)
    ic = unary_union([P.SALON, P.ERKEK, P.KADIN])
    T_MAHAL = {m[0]: m[6] for m in P.MAHAL_LISTESI}
    for ad, mno, g in P._MAHAL_GEOM:
        D.poly(v, g, fill=HexColor(T_RENK[T_MAHAL[mno]]), alpha=0.95)
    D.poly(v, ic.buffer(D.DUVAR_T, join_style=2).difference(ic), fill=HexColor("#6B7078"))
    D.poly(v, ic, stroke=HexColor("#3A3F46"), lw=0.7)
    D.ic_bolme(v, col=HexColor("#FFFFFF"))
    # armatürler
    for px_, py_ in D.aydinlatma_izgara(): MP.sembol(v, px_, py_, "armatur")
    for ad, d in P.ISLAK.items():
        for n in ("soyunma", "dus", "wc"):
            q = d[n].representative_point(); MP.sembol(v, q.x, q.y, "downlight")
    for kod, x_, y_, t in P.ACIL_TAVAN: MP.sembol(v, x_, y_, "acil", "E")
    for kod, x_, y_, t in P.HOPARLOR:  MP.sembol(v, x_, y_, "hoparlor")
    for kod, x_, y_, t in P.DEDEKTOR:  MP.sembol(v, x_, y_, "dedektor", kod)
    for kod, x_, y_, dbg, tip in P.MENFEZ: MP.menfez(v, x_, y_, tip, kod, dbg)
    # revizyon kapakları
    for ad, d in P.ISLAK.items():
        for n in ("dus", "wc"):
            b = d[n].bounds
            rx, ry = b[0]+0.28, b[3]-0.28
            px, py = v.p((rx, ry)); s_ = v.m(0.30)
            c.saveState(); c.setStrokeColor(HexColor("#16273D")); c.setLineWidth(0.7)
            c.setFillColor(HexColor("#FFFFFF")); c.rect(px-s_/2, py-s_/2, s_, s_, 1, 1)
            c.line(px-s_/2, py-s_/2, px+s_/2, py+s_/2); c.restoreState()
    # tip + kot etiketi
    for mno, pt in P.MAHAL_NOKTA.items():
        tt = T_MAHAL[mno]; px, py = v.p(pt)
        c.saveState(); c.setFillColor(HexColor("#FFFFFF")); c.setStrokeColor(HexColor("#16273D"))
        c.setLineWidth(0.7); c.roundRect(px-5.8*mm, py-2.1*mm, 11.6*mm, 4.2*mm, 1.0*mm, 1, 1)
        c.restoreState()
        h.txt(c, px, py-1.25*mm, f"{tt}  +{('%.2f'%P.TAVAN_KOT[tt]).replace('.',',')}",
              h.FB, 5.2, HexColor("#16273D"), "c")
    D.kuzey_ok(v, L+pw-13*mm, TOP-13*mm); D.olcek_cubugu(v, L+5*mm, BOT+11*mm)
    h.lejant(c, L+5*mm, BOT+2*mm, [(HexColor(T_RENK["T1"]), "T1 açık tavan +3,20"),
        (HexColor(T_RENK["T2"]), "T2 alçıpan +2,80"), (HexColor(T_RENK["T4"]), "T4 alçıpan +2,60"),
        (HexColor(T_RENK["T3"]), "T3 ıslak alçıpan +2,40"), (HexColor("#FFFFFF"), "Revizyon kapağı 30×30")], 5.8)

    x2 = L+pw+7*mm; w2 = R-x2
    yy = kunye(c, x2, TOP, w2, "A-05", "1/75 (A3)")
    h.txt(c, x2, yy-6*mm, h.TR_UP("Tavan tipleri"), h.FB, 8.0, h.NAVY)
    yyy = yy-11*mm
    for t in P.TAVAN_TIPLERI:
        h.txt(c, x2, yyy, f"{t[0]}  ·  {t[1]}", h.FB, 6.6, h.NAVY)
        h.txt(c, x2+w2, yyy, f"+{('%.2f'%t[2]).replace('.',',')}", h.FB, 6.6, h.COPPER, "r")
        yyy -= 3.9*mm
        for kk in t[3]:
            for ln in h.wrap(c, "– "+kk, h.F, 6.0, w2-4*mm):
                h.txt(c, x2+3*mm, yyy, ln, h.F, 6.0, h.INK); yyy -= 3.2*mm
        for ln in h.wrap(c, t[4], h.F, 5.9, w2-4*mm):
            h.txt(c, x2+3*mm, yyy, ln, h.F, 5.9, h.GREY); yyy -= 3.2*mm
        yyy -= 2.2*mm
    h.notkutu(c, x2, yyy-2*mm, w2, "Tavan koordinasyonu — kontrol edildi",
      "Armatür, menfez, hoparlör ve dedektör konumları elektrik (E-02, E-04) ve mekanik (M-02) "
      "paftalarıyla aynı kaynaktan üretilmiştir; otomatik çakışma kontrolü (tools/kontrol.py) "
      "yapılmıştır. Menfezler lineer armatür sıraları arasına yerleştirilmiş, aynı hizada üst üste "
      "gelmesi önlenmiştir. Askı çubukları kanal ve boru güzergâhlarından bağımsız planlanacaktır.",
      fs=6.3, acc=h.GREEN)

# ══ KESİT MOTORU ═══════════════════════════════════════════════════════════════
DUVAR_DIS = 0.20
def _kesit_yapisi(ad):
    a, b, _ = P.KESIT_HATLARI[ad]
    dizi = [d for d in P.kesit_dizisi(a, b) if d[0]]
    # ardışık aynı mahalleri birleştir
    birlesik = []
    for no, s0, s1 in dizi:
        if birlesik and birlesik[-1][0] == no and s0-birlesik[-1][2] < 0.05:
            birlesik[-1][2] = s1
        else: birlesik.append([no, s0, s1])
    duvarlar = []; sinirlar = []
    for i in range(len(birlesik)-1):
        orta = (birlesik[i][2]+birlesik[i+1][1])/2
        # 101–104 salon bölgeleri arasında fiziksel bölme yoktur: yalnızca kaplama sınırı
        if birlesik[i][0] in P.SALON_MAHAL and birlesik[i+1][0] in P.SALON_MAHAL:
            sinirlar.append(orta)
            birlesik[i][2] = orta; birlesik[i+1][1] = orta
            continue
        t = 0.10
        duvarlar.append((orta-t/2, orta+t/2, "ic"))
        birlesik[i][2] = orta-t/2; birlesik[i+1][1] = orta+t/2
    duvarlar.insert(0, (birlesik[0][1]-DUVAR_DIS, birlesik[0][1], "dis"))
    duvarlar.append((birlesik[-1][2], birlesik[-1][2]+DUVAR_DIS, "dis"))
    return birlesik, duvarlar, sinirlar, math.dist(a, b)

def _gorunen_ekipman(ad):
    """Kesit düzleminin arkasında kalan ekipmanın (s0,s1,yükseklik,kod) listesi."""
    a, b, _ = P.KESIT_HATLARI[ad]
    yatay = abs(b[1]-a[1]) < 1e-6
    yon = P.KESIT_BAKIS[ad]
    out = []
    for kod, adi, g in P.ekipman_poligonlari():
        bb = g.bounds; cen = g.centroid
        kk = kod[0]; yuk = P.EK_H[kk]
        if yatay:
            derinlik = (cen.y - a[1])*yon
            s0, s1 = bb[0]-a[0], bb[2]-a[0]
        else:
            derinlik = (cen.x - a[0])*yon
            s0, s1 = bb[1]-a[1], bb[3]-a[1]
        if -0.9 < derinlik < 4.2:
            out.append((s0, s1, yuk, kod, adi, abs(derinlik)))
    return sorted(out, key=lambda t: -t[5])

def _ring_ciz(v, s0, s1):
    """Altıgen ring — platform + direk + halat (kesitte görünüş)."""
    ph = P.RING["platform_h"]; dh = P.RING["direk_h"]
    M.gorunus_kutu(v, s0, 0.0, s1, ph, fill=HexColor("#E0C8A8"), kontur=HexColor("#8A5522"), lw=0.7)
    c = v.c
    for sx in (s0+0.10, s1-0.10):
        M.gorunus_kutu(v, sx-0.055, ph, sx+0.055, ph+dh,
                       fill=HexColor("#3A3F46"), kontur=HexColor("#1C1C1C"), lw=0.6)
    for k in P.RING["halat_kotlari"]:
        M.cizgi(v, (s0+0.10, ph+k), (s1-0.10, ph+k), HexColor("#1C1C1C"), 1.1)
    px, py = v.p((s0+s1)/2, ph/2)
    h.txt(c, px, py-1.0*mm, "Z6 RİNG PLATFORMU +0,30", h.FB, 4.8, HexColor("#5C3B14"), "c")

def kesit_ciz(c, ad, x, y, w, hgt):
    mahaller, duvarlar, sinirlar, Ltot = _kesit_yapisi(ad)
    v = M.KV(c, x, y, w, hgt, -0.2, Ltot+0.2, -0.75, 4.00, pad=13*mm)
    slab_alt = P.KOT_YAPISAL_TAVAN
    # zemin altı toprak/döşeme
    M.kutu(v, mahaller[0][1]-DUVAR_DIS, P.KOT_MEVCUT_SAP-0.22, mahaller[-1][2]+DUVAR_DIS,
           P.KOT_MEVCUT_SAP, "beton")
    # yapısal döşeme
    M.kutu(v, mahaller[0][1]-DUVAR_DIS, slab_alt, mahaller[-1][2]+DUVAR_DIS, slab_alt+0.22, "beton")
    # duvarlar
    for s0, s1, tip in duvarlar:
        M.kutu(v, s0, P.KOT_MEVCUT_SAP-0.22 if tip == "dis" else 0.0, s1, slab_alt,
               "beton" if tip == "dis" else "alcipan")
    # mahaller
    for no, s0, s1 in mahaller:
        m = P._MAHAL_BILGI[no]
        zt = m[3]; tt = m[6]; islak = m[9]
        kot_z = P.KOT_ISLAK if islak else 0.0
        zk = P.ZEMIN_KALINLIK[zt]/1000.0
        # zemin katmanı
        M.kutu(v, s0, kot_z-zk, s1, kot_z,
               "seramik" if zt in ("Z4","Z5") else ("lvt" if zt == "Z3" else "kaucuk"))
        # alt tesviye/şap
        M.kutu(v, s0, P.KOT_MEVCUT_SAP-(0.09 if islak else 0.0), s1, kot_z-zk, "sap")
        if islak: M.kot(v, s0+0.16, kot_z, "−0,02", 1)
        # asma tavan
        tk = P.TAVAN_KOT[tt]
        if tt != "T1":
            M.kutu(v, s0, tk, s1, tk+0.0125*2, "alcipan")
            M.kot(v, s0+0.18, tk, "+%s" % ("%.2f" % tk).replace(".", ","), 1)
        # mahal etiketi
        px, py = v.p((s0+s1)/2, tk-0.42 if tt != "T1" else 2.50)
        if v.m(s1-s0) > 16*mm:
            M.balon(c, px, py+4.6*mm, no, r=2.7*mm)
            for j, ln in enumerate(h.wrap(c, m[1], h.FB, 5.4, v.m(s1-s0)-2*mm)):
                h.txt(c, px, py-j*3.1*mm, ln, h.FB, 5.4, h.NAVY, "c")
            h.txt(c, px, py-3.3*mm-0.0, f"{zt} · {tt}", h.F, 5.0, h.COPPER, "c")
    # zemin kaplama sınırı (bölme değil)
    for sb in sinirlar:
        M.cizgi(v, (sb, -0.09), (sb, 0.30), HexColor("#B87333"), 0.7, (2.2, 1.8))
        px, py = v.p(sb, 0.34)
        h.txt(c, px, py, "kaplama sınırı", h.F, 4.4, HexColor("#8A5522"), "c")
    # görünen ekipman
    for s0, s1, yuk, kod, adi, dp in _gorunen_ekipman(ad):
        a0, a1 = max(s0, mahaller[0][1]), min(s1, mahaller[-1][2])
        if kod == "A":
            _ring_ciz(v, a0, a1); px, py = v.p((a0+a1)/2, P.RING["platform_h"]+P.RING["direk_h"])
            M.balon(c, px, py+4.2*mm, "A", r=2.4*mm, dolgu="#FFFFFF", kontur="#B87333", fs=5.0)
            continue
        M.gorunus_kutu(v, a0, 0.0, a1, yuk,
                       fill=HexColor("#E7EAEE"), kontur=HexColor("#98A0AA"), lw=0.5)
        px, py = v.p((a0+a1)/2, yuk)
        if v.m(a1-a0) > 8*mm:
            M.balon(c, px, py+3.2*mm, kod, r=2.2*mm, dolgu="#FFFFFF", kontur="#6B7078", fs=4.8)
    # kot referansları
    M.kot(v, mahaller[0][1]+0.10, 0.0, None, 1, uzun=0)
    M.kot(v, mahaller[-1][2]-0.10, slab_alt, "+3,20", -1)
    # düşey kot zinciri
    M.kot_zinciri(v, mahaller[-1][2]+DUVAR_DIS+0.42, [P.KOT_MEVCUT_SAP, 0.0, 2.40, 2.80, 3.20])
    # yatay ölçü zinciri
    noktalar = [mahaller[0][1]-DUVAR_DIS]
    for no, s0, s1 in mahaller: noktalar += [s0, s1]
    noktalar.append(mahaller[-1][2]+DUVAR_DIS)
    M.olcu_zinciri(v, -0.52, sorted(set(round(nn, 3) for nn in noktalar)))
    # zemin çizgisi
    M.cizgi(v, (mahaller[0][1]-DUVAR_DIS-0.25, P.KOT_MEVCUT_SAP-0.22),
            (mahaller[-1][2]+DUVAR_DIS+0.25, P.KOT_MEVCUT_SAP-0.22), h.INK, 1.4)
    return v, mahaller

def _kesit_sayfa(c, no, ad):
    pafta, bas = PAFTA_ADI[no]
    a, b, aciklama = P.KESIT_HATLARI[ad]
    sayfa(c, no, f"Kesit {ad}", aciklama)
    ch = (TOP-BOT)*0.60
    cy0 = TOP-ch
    h.kutu(c, L, cy0, CW, ch, HexColor("#FFFFFF"), h.GREY_L, 0.6)
    v, mahaller = kesit_ciz(c, ad, L, cy0, CW, ch)
    h.txt(c, L+4*mm, TOP-5.4*mm, f"KESİT {ad}   ·   {h.TR_UP(aciklama)}", h.FB, 7.0, h.NAVY)
    h.txt(c, R-4*mm, TOP-5.4*mm, "1/50 (A3)", h.FB, 6.6, h.COPPER, "r")

    # alt şerit: künye · anahtar plan · mahal tablosu · notlar
    ay = cy0-5*mm; ah = ay-BOT
    c1 = CW*0.185; c2 = CW*0.195; c3 = CW*0.315; c4 = CW-c1-c2-c3-3*5*mm
    kunye(c, L, ay, c1, pafta, "1/50 (A3)")
    x2 = L+c1+5*mm
    h.txt(c, x2, ay-3.4*mm, h.TR_UP("Anahtar plan"), h.FB, 7.0, h.NAVY)
    kv = D.View(c, x2, BOT, c2, ah-7*mm, pad=3*mm)
    MP.altlik(kv); M.kesit_isareti(kv, a, b, ad)
    x3 = x2+c2+5*mm
    h.txt(c, x3, ay-3.4*mm, h.TR_UP("Kesitte geçilen mahaller"), h.FB, 7.0, h.NAVY)
    rows = []
    for mno, s0, s1 in mahaller:
        m = P._MAHAL_BILGI[mno]
        rows.append([m[0], m[1], m[3], m[4], m[6], ("%.2f" % m[7]).replace(".", ","),
                     ("−0,02" if m[9] else "±0,00")])
    h.tablo(c, x3, ay-6*mm, [("No",0.09),("Mahal",0.35),("Zem.",0.10),("Süp.",0.09),
                             ("Tav.",0.10),("T.kot",0.13),("Z.kot",0.14)], rows, c3,
            satir_h=5.4*mm, bas_h=6.4*mm, fs=6.0, hfs=5.8, hizala=["c","l","c","c","c","r","r"])
    x4 = x3+c3+5*mm
    h.notkutu(c, x4, ay, c4, "Kesit notları",
      "Kesilen elemanlar kalın konturla ve malzeme taramasıyla, kesit düzleminin arkasında kalan ekipman "
      "silueti ince gri konturla gösterilmiştir. Tüm alçıpan bölmeler yapısal döşemeye kadar (+3,20) "
      "yükselir, asma tavan hizasında kesilmez. Yapısal döşeme kalınlığı ve tavan yüksekliği VARSAYIMDIR — "
      "söküm sonrası yerinde ölçülecek, kesitler ve tavan kotları buna göre revize edilecektir. Zemin "
      "katman kalınlıkları bu ölçekte okunmaz; A-11 ve A-12 detaylarına bakınız. Kesit hattı üzerinde "
      "kalmayan kapı ve pencereler gösterilmemiştir; doğrama bilgisi için A-10'a bakınız.",
      fs=6.0, acc=h.NAVY2)

def s6(c): _kesit_sayfa(c, 6, "A-A")
def s7(c): _kesit_sayfa(c, 7, "B-B")

# ══ 8 · İÇ GÖRÜNÜŞLER ══════════════════════════════════════════════════════════
GOR_STIL = {
 "cam":       ("#DCEBF5", "#3E8ACC", 0.9),
 "dolgu":     ("#EEF4F8", "#8FB4D2", 0.5),
 "kapi":      ("#FFF3E3", "#B87333", 1.0),
 "mobilya":   ("#F6F1E8", "#9A8E79", 0.8),
 "levha":     ("#FFFFFF", "#16273D", 0.7),
 "ayna":      ("#D6E6F2", "#5E8FB5", 0.9),
 "duvar":     ("#F7F6F3", "#B9B4A8", 0.5),
 "giydirme":  ("#F2EFE8", "#B9B4A8", 0.5),
 "ekipman":   ("#E7EAEE", "#98A0AA", 0.6),
 "supurgelik":("#3A3F46", "#1C1C1C", 0.5),
 "askilik":   ("#D8DCE1", "#8A8F98", 0.5),
}
def gorunus_ciz(c, g, x, y, w, hgt):
    kod, bas, gen, yuk, tkot, ogeler = g
    v = M.KV(c, x, y, w, hgt, -0.15, gen+0.15, -0.55, yuk+0.55, pad=8*mm)
    # zemin + tavan + yan duvarlar (kesilen)
    M.kutu(v, -0.15, -0.20, gen+0.15, 0.0, "sap")
    M.kutu(v, -0.15, yuk, gen+0.15, yuk+0.20, "beton")
    for tip, s0, s1, z0, z1, etk in ogeler:
        if tip == "tavan":
            M.cizgi(v, (s0, z0), (s1, z1), HexColor("#C8322B"), 0.9, (3, 2))
            M.kot(v, s1-0.25, z0, None, -1)
            continue
        fill, kon, lw = GOR_STIL.get(tip, GOR_STIL["duvar"])
        M.gorunus_kutu(v, s0, z0, s1, z1, fill=HexColor(fill), kontur=HexColor(kon), lw=lw)
        if tip == "ayna":
            for k in range(5):
                M.cizgi(v, (s0+(s1-s0)*k/5, z0), (s0+(s1-s0)*k/5+0.22, z1),
                        HexColor("#8FB4D2"), 0.35)
        if tip == "kapi":
            M.cizgi(v, (s0+(s1-s0)*0.5, z0), (s0+(s1-s0)*0.5, z1), HexColor("#B87333"), 0.5, (2, 2))
    # ölçü zinciri
    noktalar = sorted(set([0.0, gen] + [round(o[1], 2) for o in ogeler if o[0] in ("kapi","ayna","mobilya")]
                          + [round(o[2], 2) for o in ogeler if o[0] in ("kapi","ayna","mobilya")]))
    M.olcu_zinciri(v, -0.38, noktalar, s=4.4)
    M.kot(v, 0.10, 0.0, None, 1)
    M.kot_zinciri(v, gen+0.30, [0.0, tkot, yuk], fs=4.4)
    h.txt(c, x+w/2, y+hgt-4.4*mm, f"{kod}  ·  {bas}", h.FB, 6.6, h.NAVY, "c")
    h.txt(c, x+w/2, y+hgt-8.0*mm, f"{('%.2f'%gen).replace('.',',')} m açıklık  ·  tavan +{('%.2f'%tkot).replace('.',',')}",
          h.F, 5.4, h.GREY, "c")
    return v

def s8(c):
    sayfa(c, 8, "İç görünüşler",
          "G-01 giriş · G-02 arena güney · G-03 soyunma cephesi · G-04 soyunma içi — "
          "ölçüler mimari altlıktan türetilmiştir, imalat öncesi yerinde ölçü alınacaktır")
    gw = (CW-6*mm)/2; gh = (TOP-BOT-40*mm)/2
    for i, g in enumerate(P.IC_GORUNUS):
        gx = L + (i % 2)*(gw+6*mm)
        gy = TOP - gh - (i//2)*(gh+4*mm)
        h.kutu(c, gx, gy, gw, gh, HexColor("#FFFFFF"), h.GREY_L, 0.6)
        gorunus_ciz(c, g, gx, gy, gw, gh)
    # alt açıklama şeridi
    yy = TOP - 2*gh - 4*mm - 6*mm
    cols = (CW-3*4*mm)/4
    for i, g in enumerate(P.IC_GORUNUS):
        gx = L+i*(cols+4*mm)
        h.txt(c, gx, yy, g[0], h.FB, 6.4, h.COPPER)
        yyy = yy-4.0*mm
        for tip, s0, s1, z0, z1, etk in g[5]:
            if tip in ("duvar", "giydirme"): continue
            for ln in h.wrap(c, "• "+etk, h.F, 5.5, cols):
                h.txt(c, gx, yyy, ln, h.F, 5.5, h.INK); yyy -= 2.95*mm


# ══ 9 · MAHAL LİSTESİ ══════════════════════════════════════════════════════════
def s9(c):
    sayfa(c, 9, "Mahal listesi — kaplama ve bitiş şartnamesi", "Zemin · süpürgelik · duvar · tavan · kapı")
    y = TOP
    rows = [[m[0], m[1], f"{h.tl(m[2],2)}", m[3], m[4], m[5], m[6],
             ("%.2f" % m[7]).replace(".", ","), m[8], m[10]] for m in P.MAHAL_LISTESI]
    y = h.tablo(c, L, y, [("No",0.040),("Mahal",0.150),("m²",0.045),("Zemin",0.042),
                          ("Süp.",0.042),("Duvar",0.175),("Tavan",0.048),("Kot",0.048),
                          ("Kapı",0.070),("Açıklama",0.340)], rows, CW,
                satir_h=6.4*mm, bas_h=7.0*mm, fs=6.2, hfs=6.0,
                hizala=["c","l","r","c","c","l","c","r","c","l"])
    h.txt(c, L, y-2.8*mm, f"Net mahal alanları toplamı {h.tl(P.MAHAL_TOPLAM,2)} m² · iç bölme duvar payı "
          f"{h.tl(P.MAHAL_DUVAR_PAYI,2)} m² · net iç kullanım alanı {h.tl(P.A['ic_toplam'],2)} m².",
          h.F, 6.0, h.GREY)
    # süpürgelik + duvar tipi özeti
    y2 = y-9*mm
    w1 = CW*0.48
    h.txt(c, L, y2, h.TR_UP("Süpürgelik tipleri"), h.FB, 8.0, h.NAVY)
    h.tablo(c, L, y2-5*mm, [("Kod",0.10),("Tanım",0.90)],
            [[s[0], s[1]] for s in P.SUPURGELIK], w1,
            satir_h=6.0*mm, bas_h=6.4*mm, fs=6.2, hfs=6.0, hizala=["c","l"])
    x2 = L+w1+8*mm; w2 = CW-w1-8*mm
    h.txt(c, x2, y2, h.TR_UP("Malzeme onay ve numune şartı"), h.FB, 8.0, h.NAVY)
    yy = h.notkutu(c, x2, y2-5*mm, w2, "Numune onayı",
      "Kauçuk karo, SPC/LVT, porselen seramik, alçıpan boyası ve süpürgelik için imalat öncesi "
      "30×30 cm numune ve teknik föy (CE beyanı, kayma direnci ve yangın sınıfı belgesi) sunulacak; "
      "işveren yazılı onayı alınmadan sipariş verilmeyecektir.", fs=6.3, acc=h.COPPER)
    yy2 = h.notkutu(c, x2, yy-4*mm, w2, "Yönetmelik bağlantısı",
      "Özel Beden Eğitimi ve Spor Tesisleri Yönetmeliği; soyunma mahalleri için blok başına asgari 8 m², "
      "dinlenme alanı için asgari 15 m² aramaktadır. Mahal listesinde 105+106+107 = "
      f"{h.tl(sum(m[2] for m in P.MAHAL_LISTESI if m[0] in ('105','106','107')),2)} m² ve "
      f"108+109+110 = {h.tl(sum(m[2] for m in P.MAHAL_LISTESI if m[0] in ('108','109','110')),2)} m², "
      f"104 dinlenme salonu {h.tl(P.ZON_M2['DİNLENME SALONU'],2)} m² ile her iki şart sağlanmaktadır. "
      "Salon alanına ilişkin GSİM uygulaması için ana dosyanın uygunluk sayfasına bakınız.",
      fs=6.3, acc=h.GREEN)

    # ── imalat şartnamesi özeti: tip kodlarının katman karşılığı
    def _kat(liste, ad_i=0, kal_i=1):
        return " + ".join(
            f"{k[ad_i].split('—')[0].split('(')[0].strip()}"
            f"{'' if k[kal_i] == 0 else ' ' + ('%g' % k[kal_i]).replace('.', ',') + ' mm'}"
            for k in liste)
    ysar = min(y2 - 40*mm, yy2 - 6*mm)
    h.txt(c, L, ysar, h.TR_UP("İmalat şartnamesi özeti — tip kodlarının katman karşılığı"),
          h.FB, 8.4, h.NAVY)
    rows3 = [[z[0], z[1], _kat([k for k in z[2] if k[1] > 0]),
              f"{P.ZEMIN_KALINLIK[z[0]]} mm", z[4]] for z in P.ZEMIN_TIPLERI]
    rows3 += [[d[0], d[1], _kat(d[3]), f"{('%g' % d[2]).replace('.', ',')} mm", d[4]]
              for d in P.DUVAR_TIPLERI]
    rows3 += [[t[0], t[1], " + ".join(x.split("—")[0].split("(")[0].strip() for x in t[3]),
               f"+{('%.2f' % t[2]).replace('.', ',')}", t[4]] for t in P.TAVAN_TIPLERI]
    h.tablo(c, L, ysar-5*mm,
            [("Tip",0.030),("Tanım",0.145),("Katman dizilimi (alttan üste / içten dışa)",0.480),
             ("Toplam",0.060),("Performans · standart · mahal",0.285)], rows3, CW,
            satir_h=4.8*mm, bas_h=6.2*mm, fs=5.7, hfs=5.8, hizala=["c","l","l","r","l"])

# ══ 10 · KAPI / PENCERE + DUVAR TİPLERİ ════════════════════════════════════════
def s10(c):
    sayfa(c, 10, "Kapı ve pencere listesi · duvar tipleri", "Doğrama şartnamesi · bölme kesitleri")
    y = TOP
    h.txt(c, L, y, h.TR_UP("Kapı listesi"), h.FB, 8.4, h.NAVY)
    rows = [[k[0], str(k[1]), k[2], f"{k[3]}×{k[4]}", k[5], k[6], k[7], k[8]] for k in P.KAPI_LISTESI]
    y = h.tablo(c, L, y-5*mm, [("Kod",0.045),("Ad.",0.030),("Mahal",0.125),("En×Yük (mm)",0.090),
                               ("Tip",0.135),("Kanat / kasa",0.180),("Donanım",0.190),("Özel şart",0.205)],
                rows, CW, satir_h=6.2*mm, bas_h=6.8*mm, fs=6.1, hfs=6.0,
                hizala=["c","c","l","c","l","l","l","l"])
    h.txt(c, L, y-8*mm, h.TR_UP("Pencere / cephe doğraması"), h.FB, 8.4, h.NAVY)
    rows2 = [[p[0], str(p[1]), p[2], p[3], p[4], p[5]] for p in P.PENCERE_LISTESI]
    y = h.tablo(c, L, y-13*mm, [("Kod",0.045),("Ad.",0.030),("Mahal",0.230),("Doğrama",0.230),
                                ("Cam / kaplama",0.250),("Not",0.215)], rows2, CW,
                satir_h=6.2*mm, bas_h=6.8*mm, fs=6.1, hfs=6.0, hizala=["c","c","l","l","l","l"])
    # duvar tipleri — yatay kesit çizimleri
    h.txt(c, L, y-8*mm, h.TR_UP("Duvar tipleri — katman dizilimi"), h.FB, 8.4, h.NAVY)
    yy = y-13*mm
    cw_ = (CW-2*5*mm)/3
    for i, d in enumerate(P.DUVAR_TIPLERI):
        dx = L+(i % 3)*(cw_+5*mm); dy = yy-(i//3)*((yy-BOT-2*mm)/2)
        hgt = (yy-BOT-4*mm)/2
        h.kutu(c, dx, dy-hgt, cw_, hgt, HexColor("#FFFFFF"), h.GREY_L, 0.5)
        h.txt(c, dx+2.5*mm, dy-4.6*mm, f"{d[0]}  ·  {d[1]}", h.FB, 6.4, h.NAVY)
        h.txt(c, dx+cw_-2.5*mm, dy-4.6*mm, f"{('%g'%d[2]).replace('.',',')} mm", h.FB, 6.4, h.COPPER, "r")
        # katman metni
        ty = dy-9.6*mm
        for j, (ad_, kal) in enumerate(d[3]):
            t = ad_ if kal == 0 else f"{ad_} — {('%g'%kal).replace('.',',')} mm"
            for ln in h.wrap(c, f"{j+1}. {t}", h.F, 5.5, cw_-6*mm):
                h.txt(c, dx+3*mm, ty, ln, h.F, 5.5, h.INK); ty -= 2.9*mm
        # katman şeridi (yatay kesit, ölçekli)
        bx, by, bw, bh = dx+3*mm, ty-13*mm, cw_-6*mm, 8.5*mm
        tot = sum(max(k[1], 2) for k in d[3])
        cx = bx
        for ad_, kal in d[3]:
            ww = bw*max(kal, 2)/tot
            mat = ("alcipan" if "alçıpan" in ad_.lower() else
                   "profil" if "profil" in ad_.lower() else
                   "tasyunu" if "taşyünü" in ad_.lower() else
                   "seramik" if "seramik" in ad_.lower() else
                   "yalitim" if "yalıtım" in ad_.lower() else
                   "ayna" if "ayna" in ad_.lower() else
                   "ahsap" if "kontrapla" in ad_.lower() else
                   "beton" if "duvar" in ad_.lower() else "sap")
            fill, kon, tip = M.MAT.get(mat, M.MAT["sap"])
            c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor(kon)); c.setLineWidth(0.4)
            c.rect(cx, by, ww, bh, 1, 1); cx += ww
        c.setStrokeColor(h.INK); c.setLineWidth(0.8); c.rect(bx, by, cx-bx, bh, 0, 0)
        h.txt(c, bx, by-3.6*mm, "yatay kesit — katman genişlikleri orantılıdır", h.F, 5.2, h.GREY)
        ny = by-7.4*mm
        for ln in h.wrap(c, d[4], h.F, 5.4, cw_-6*mm):
            h.txt(c, dx+3*mm, ny, ln, h.F, 5.4, h.COPPER); ny -= 2.8*mm

# ══ 11 / 12 · İMALAT DETAYLARI ═════════════════════════════════════════════════
DETAY_REF = {"D-01":"Z1", "D-02":"Z4 · D5", "D-03":"Z1 · Z2 · Z3 · Z5", "D-04":"D2",
             "D-05":"D3 · Z4", "D-06":"T2 · T3", "D-07":"Z6", "D-08":"D6"}

def _detay_kutusu(c, d, x, y, w, hgt):
    kod, bas, tip, veri, notlar = d
    h.kutu(c, x, y-hgt, w, hgt, HexColor("#FFFFFF"), h.GREY_L, 0.6)
    c.setFillColor(h.NAVY); c.rect(x, y-6.4*mm, w, 6.4*mm, 0, 1)
    h.txt(c, x+3*mm, y-4.6*mm, f"{kod}   {h.TR_UP(bas)}", h.FB, 6.2, HexColor("#FFFFFF"))
    h.txt(c, x+w-3*mm, y-4.6*mm, DETAY_REF.get(kod, "detay"), h.FB, 6.0, h.COPPER, "r")
    cy = y-9.5*mm
    olcek_ad = "1/10"
    if tip == "katman":
        z = [zz for zz in P.ZEMIN_TIPLERI if zz[0] == veri][0]
        katmanlar = [(k[0], k[1], k[2]) for k in z[2] if k[1] > 0]
        cy, olcek_ad = M.katman_detay(c, x+9*mm, cy-3*mm, w-13*mm, katmanlar,
                                      yukseklik=hgt-16*mm-len(notlar)*9.5*mm, fs=5.2)
        h.txt(c, x+9*mm, cy-4.6*mm, f"Katman şeması · ölçek {olcek_ad} · "
              f"bitmiş kot {('±0,00' if abs(z[3])<0.005 else ('%+.2f'%z[3]).replace('.',',').replace('-','−'))}",
              h.FB, 5.4, h.NAVY)
        cy -= 8*mm
    elif tip == "duvar":
        dd = [xx for xx in P.DUVAR_TIPLERI if xx[0] == veri][0]
        bx, by, bw, bh = x+5*mm, cy-42*mm, w-10*mm, 26*mm
        tot = sum(max(k[1], 2) for k in dd[3]); cx = bx
        for ad_, kal in dd[3]:
            ww = bw*max(kal, 2)/tot
            mat = ("alcipan" if "alçıpan" in ad_.lower() else
                   "profil" if "profil" in ad_.lower() else
                   "tasyunu" if "taşyünü" in ad_.lower() else "sap")
            fill, kon, _t = M.MAT[mat]
            c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor(kon)); c.setLineWidth(0.45)
            c.rect(cx, by, ww, bh, 1, 1)
            _i = dd[3].index((ad_, kal))
            _up = by+bh+4*mm+(_i % 2)*9.5*mm
            M.kilavuz(c, cx+ww/2, by+bh, cx+ww/2, _up,
                      f"{ad_}" + ("" if kal == 0 else f" — {('%g'%kal).replace('.',',')} mm"),
                      fs=5.0, w=w*0.28, nokta=False,
                      al=("l" if cx+ww/2 < x+w*0.55 else "r"))
            cx += ww
        c.setStrokeColor(h.INK); c.setLineWidth(1.0); c.rect(bx, by, bw, bh, 0, 0)
        h.txt(c, bx+bw/2, by-4.2*mm, f"toplam {dd[2]} mm  ·  C profil @400 mm", h.FB, 5.4, h.NAVY, "c")
        cy = by-7*mm
    elif tip == "gecis":
        bx, by, bw = x+5*mm, cy-26*mm, w-10*mm
        # Z1 solda, Z3 sağda, bitmiş kot aynı
        oh = 0.20   # mm -> mm görsel ölçek
        for k, (zt, s0, s1) in enumerate((("Z1", 0.0, 0.46), ("Z3", 0.54, 1.0))):
            z = [zz for zz in P.ZEMIN_TIPLERI if zz[0] == zt][0]
            yy0 = by
            for ad_, kal, mat in z[2]:
                if kal == 0: continue
                hh = kal*oh*mm
                fill, kon, _t = M.MAT[mat]
                c.setFillColor(HexColor(fill)); c.setStrokeColor(HexColor(kon)); c.setLineWidth(0.4)
                c.rect(bx+bw*s0, yy0, bw*(s1-s0), hh, 1, 1); yy0 += hh
            h.txt(c, bx+bw*(s0+s1)/2, by-4.0*mm, f"{zt} — toplam {P.ZEMIN_KALINLIK[zt]} mm",
                  h.FB, 5.4, h.NAVY, "c")
            c.setStrokeColor(h.INK); c.setLineWidth(0.9)
            c.rect(bx+bw*s0, by, bw*(s1-s0), yy0-by, 0, 0)
        # geçiş profili
        c.setFillColor(HexColor("#B7BCC4")); c.setStrokeColor(h.INK); c.setLineWidth(0.6)
        c.rect(bx+bw*0.46, by+53*oh*mm-1.2*mm, bw*0.08, 1.2*mm, 1, 1)
        M.kilavuz(c, bx+bw*0.50, by+53*oh*mm, bx+bw*0.50, by+53*oh*mm+8*mm,
                  "40 mm alüminyum düz geçiş profili — bitmiş kot ±0,00, eşik yok",
                  fs=5.2, w=w*0.5, nokta=True)
        c.setStrokeColor(HexColor("#2E7D5B")); c.setLineWidth(0.8); c.setDash(3, 2)
        c.line(bx-2*mm, by+53*oh*mm, bx+bw+2*mm, by+53*oh*mm); c.setDash()
        h.txt(c, bx+bw+2.5*mm, by+53*oh*mm+0.6*mm, "±0,00", h.FB, 5.2, HexColor("#2E7D5B"))
        cy = by-7*mm
    elif tip == "islak":
        bx, by, bw = x+6*mm, cy-52*mm, w*0.44
        c.setFillColor(HexColor("#F2EFE8")); c.setStrokeColor(h.INK); c.setLineWidth(0.7)
        c.rect(bx, by, 9*mm, 52*mm, 1, 1)                      # D3 alçıpan bölme
        c.setFillColor(HexColor("#9FB8C4")); c.rect(bx+9*mm, by, 3.0*mm, 52*mm, 1, 1)  # duvar seramiği
        c.setStrokeColor(HexColor("#2F6FB3")); c.setLineWidth(1.6)
        p = c.beginPath(); p.moveTo(bx+9*mm, by+46*mm); p.lineTo(bx+9*mm, by+4*mm)
        p.lineTo(bx+bw, by+2.0*mm); c.drawPath(p, 0, 0)        # su yalıtımı dönüşü
        c.setFillColor(HexColor("#E2E0DA")); c.setStrokeColor(h.INK); c.setLineWidth(0.6)
        p = c.beginPath(); p.moveTo(bx+12*mm, by); p.lineTo(bx+bw, by)
        p.lineTo(bx+bw, by+3.0*mm); p.lineTo(bx+12*mm, by+6.0*mm); p.close()
        c.drawPath(p, 1, 1)                                     # eğim şapı
        c.setFillColor(HexColor("#9FB8C4"))
        p = c.beginPath(); p.moveTo(bx+12*mm, by+6.0*mm); p.lineTo(bx+bw, by+3.0*mm)
        p.lineTo(bx+bw, by+5.0*mm); p.lineTo(bx+12*mm, by+8.0*mm); p.close()
        c.drawPath(p, 1, 1)                                     # seramik
        c.setFillColor(HexColor("#B7BCC4")); c.setStrokeColor(h.INK)
        c.rect(bx+bw-8*mm, by-5*mm, 7*mm, 8.2*mm, 1, 1)         # süzgeç
        c.setStrokeColor(HexColor("#C8322B")); c.setLineWidth(0.9)
        c.line(bx+bw-13*mm, by+4.6*mm, bx+bw-1*mm, by+2.6*mm)   # eğim oku
        h.txt(c, bx+bw-7*mm, by+6.6*mm, "%1,5", h.FB, 4.8, HexColor("#C8322B"), "c")
        M.etiket_sutunu(c, x+w*0.56, cy-4*mm, by-3*mm, w*0.40, [
            (bx+4.5*mm, by+48*mm, "D3 — 12,5 mm H2 (yeşil) alçıpan çift kat, 50 mm C profil @400 mm"),
            (bx+10.5*mm, by+40*mm, "Çimento esaslı 2 bileşenli su yalıtımı, 2 kat — duş kabininde 2000 mm yukarı döner"),
            (bx+10.5*mm, by+26*mm, "Duvar seramiği 300×600 mm + C2TE S1 yapıştırıcı"),
            (bx+bw*0.55, by+7.0*mm, "Zemin seramiği R11 · eğim şapı süzgeğe doğru %1,5"),
            (bx+11*mm, by+2.4*mm, "120 mm elastik su yalıtım bandı — yalıtımın iki katı arasına gömülü"),
            (bx+bw-4.5*mm, by-1.5*mm, "100×100 mm paslanmaz süzgeç, kokulu sifon — flanş yalıtım katları arasında"),
        ], fs=5.1)
        h.txt(c, bx, by-9*mm, "U tabanlık butil bant üzerine · alçıpan alt kenarı bitmiş zeminden +10 mm",
              h.F, 5.2, h.COPPER)
        cy = by-13*mm
    elif tip == "tavan":
        bx, by, bw = x+6*mm, cy-46*mm, w*0.46
        c.setFillColor(HexColor("#C9CCD1")); c.setStrokeColor(h.INK); c.setLineWidth(0.7)
        c.rect(bx, by+40*mm, bw, 6*mm, 1, 1)                    # yapısal döşeme
        c.setFillColor(HexColor("#F2EFE8")); c.setStrokeColor(h.INK); c.setLineWidth(0.6)
        c.rect(bx, by+6*mm, 8*mm, 34*mm, 1, 1)                  # duvar
        c.setFillColor(HexColor("#B7BCC4")); c.setStrokeColor(HexColor("#6B7078"))
        c.rect(bx+9*mm, by+8.6*mm, bw-9*mm, 2.4*mm, 1, 1)       # taşıyıcı profil
        c.setFillColor(HexColor("#F2EFE8")); c.setStrokeColor(h.INK); c.setLineWidth(0.5)
        c.rect(bx+9*mm, by+5.6*mm, bw-9*mm, 3.0*mm, 1, 1)       # alçıpan
        c.setStrokeColor(HexColor("#6B7078")); c.setLineWidth(0.9)
        for k in range(3):
            xx = bx+14*mm+k*(bw-20*mm)/2
            c.line(xx, by+11*mm, xx, by+40*mm)                  # askı çubukları
            c.circle(xx, by+11.6*mm, 0.8*mm, 0, 0)
        c.setStrokeColor(HexColor("#C8322B")); c.setLineWidth(1.2)
        c.line(bx+8*mm, by+5.6*mm, bx+8*mm, by+8.6*mm)          # gölge derzi
        c.setFillColor(HexColor("#FFFFFF")); c.setStrokeColor(h.INK); c.setLineWidth(0.6)
        c.rect(bx+bw-16*mm, by+5.2*mm, 11*mm, 3.4*mm, 1, 1)     # revizyon kapağı
        M.etiket_sutunu(c, x+w*0.58, cy-4*mm, by+1*mm, w*0.38, [
            (bx+bw*0.55, by+43*mm, "Mevcut yapısal döşeme +3,20 — VARSAYIM, yerinde ölçülecek"),
            (bx+bw*0.42, by+26*mm, "Ayarlı askı çubuğu @900 mm — kanal, boru ve armatür askısı bağımsız"),
            (bx+bw*0.62, by+9.8*mm, "TC47 ana profil @900 / TU27 taşıyıcı @400 mm"),
            (bx+bw*0.62, by+7.1*mm, "12,5 mm alçıpan (ıslak hacimde H2 su itici)"),
            (bx+8.3*mm, by+7.1*mm, "10 mm gölge derzi — duvar birleşiminde çatlama önlemi"),
            (bx+bw-10.5*mm, by+6.9*mm, "300×300 mm revizyon kapağı — vana ve klima drenajı altında"),
        ], fs=5.1)
        cy = by-4*mm
    elif tip == "ayna":
        bx, by, bw = x+6*mm, cy-48*mm, w*0.40
        c.setFillColor(HexColor("#F2EFE8")); c.setStrokeColor(h.INK); c.setLineWidth(0.7)
        c.rect(bx, by, 10*mm, 48*mm, 1, 1)                      # mevcut duvar D1/D4
        c.setFillColor(HexColor("#D8B98C")); c.rect(bx+10*mm, by+6*mm, 3.0*mm, 38*mm, 1, 1)
        c.setFillColor(HexColor("#D6E6F2")); c.setStrokeColor(HexColor("#5E8FB5"))
        c.rect(bx+13.0*mm, by+6*mm, 2.2*mm, 38*mm, 1, 1)        # ayna
        c.setFillColor(HexColor("#B7BCC4")); c.setStrokeColor(h.INK); c.setLineWidth(0.5)
        c.rect(bx+12.4*mm, by+4.4*mm, 4.2*mm, 2.0*mm, 1, 1)
        c.rect(bx+12.4*mm, by+43.6*mm, 4.2*mm, 2.0*mm, 1, 1)    # emniyet profilleri
        c.setFillColor(HexColor("#3A3F46")); c.setStrokeColor(h.INK)
        c.rect(bx+10*mm, by, 6*mm, 4.0*mm, 1, 1)                # süpürgelik
        M.etiket_sutunu(c, x+w*0.52, cy-4*mm, by+2*mm, w*0.44, [
            (bx+14.1*mm, by+44.8*mm, "Üst alüminyum mekanik emniyet profili · ayna üst kotu +2,30"),
            (bx+14.1*mm, by+34*mm, "6 mm ayna — arka yüz güvenlik filmi (EN 12600 sınıf 2B2) ZORUNLU"),
            (bx+11.5*mm, by+22*mm, "18 mm su kontraplağı taşıyıcı altlık — D1/D4 üzerine dübelli"),
            (bx+5*mm, by+30*mm, "D1 mevcut duvar (arena güney çeperinde D4 akustik giydirme üzeri)"),
            (bx+14.1*mm, by+5.4*mm, "Alt emniyet profili · ayna alt kotu +0,30"),
            (bx+13*mm, by+2.0*mm, "S1 kauçuk süpürgelik 100 mm"),
        ], fs=5.1)
        cy = by-4*mm
    # notlar — çizimin hemen altında
    ny = max(cy-3*mm, y-hgt+len(notlar)*4.6*mm+5*mm)
    c.setStrokeColor(h.GREY_L); c.setLineWidth(0.5); c.line(x+4*mm, ny+3.4*mm, x+w-4*mm, ny+3.4*mm)
    for nt in notlar:
        for j, ln in enumerate(h.wrap(c, nt, h.F, 5.5, w-11*mm)):
            if j == 0: h.txt(c, x+4.5*mm, ny, "•", h.FB, 5.5, h.COPPER)
            h.txt(c, x+8*mm, ny, ln, h.F, 5.5, h.INK); ny -= 3.0*mm
        ny -= 1.2*mm

def _detay_sayfa(c, no, detaylar, baslik, ust):
    sayfa(c, no, baslik, ust)
    dw = (CW-5*mm)/2; dh = (TOP-BOT-5*mm)/2
    for i, d in enumerate(detaylar):
        dx = L+(i % 2)*(dw+5*mm); dy = TOP-(i//2)*(dh+5*mm)
        _detay_kutusu(c, d, dx, dy, dw, dh)

def s11(c): _detay_sayfa(c, 11, P.DETAYLAR[:4], "İmalat detayları I",
                         "Zemin katmanları · ıslak hacim birleşimi · kot geçişi · alçıpan bölme")
def s12(c): _detay_sayfa(c, 12, P.DETAYLAR[4:], "İmalat detayları II",
                         "Duş süzgeci · asma tavan kenarı · ring platformu · ayna montajı")

# ══ 13 · YANGIN VE TAHLİYE ═════════════════════════════════════════════════════
def s13(c):
    sayfa(c, 13, "Yangın ve tahliye planı", "Kaçış yolları · çıkışlar · söndürücü · acil aydınlatma")
    pw = CW*0.605
    v = plan_altlik(c, L, BOT+8*mm, pw, TOP-BOT-10*mm)
    MP.ekipman_soluk(v)
    # kaçış yolları
    for mno, yol, cik in P.TAHLIYE_YOL:
        for i in range(len(yol)-1):
            D.line(v, yol[i], yol[i+1], HexColor("#2E7D5B"), 2.0)
        # ok ucu
        for i in range(1, len(yol)):
            ax, ay = v.p(yol[i-1]); bx, by = v.p(yol[i])
            ang = math.degrees(math.atan2(by-ay, bx-ax))
            mx, my = (ax+bx)/2, (ay+by)/2
            c.saveState(); c.translate(mx, my); c.rotate(ang)
            c.setFillColor(HexColor("#2E7D5B"))
            p = c.beginPath(); p.moveTo(2.0*mm, 0); p.lineTo(-1.2*mm, 1.3*mm)
            p.lineTo(-1.2*mm, -1.3*mm); p.close(); c.drawPath(p, 0, 1); c.restoreState()
        u = P.tahliye_uzunluk(yol)
        px, py = v.p(yol[0])
        h.txt(c, px, py+5.0*mm, f"{('%.1f'%u).replace('.',',')} m", h.FB, 5.2, HexColor("#1E5C42"), "c")
    # çıkışlar
    for kod, pt, gen, ad in P.CIKISLAR:
        px, py = v.p(pt)
        c.saveState(); c.setFillColor(HexColor("#2E7D5B")); c.setStrokeColor(HexColor("#FFFFFF"))
        c.setLineWidth(0.8); c.circle(px, py, 3.4*mm, 1, 1); c.restoreState()
        h.txt(c, px, py-1.25*mm, kod, h.FB, 5.6, HexColor("#FFFFFF"), "c")
        h.txt(c, px, py+4.6*mm, f"{ad} · {('%.2f'%gen).replace('.',',')} m", h.FB, 5.0, HexColor("#1E5C42"), "c")
    # söndürücü / dolap
    for kod, pt, ad in P.YANGIN_EKIPMAN:
        px, py = v.p(pt)
        c.saveState(); c.setFillColor(HexColor("#C8322B")); c.setStrokeColor(HexColor("#FFFFFF"))
        c.setLineWidth(0.7)
        if kod.startswith("YD"): c.rect(px-2.6*mm, py-2.6*mm, 5.2*mm, 5.2*mm, 1, 1)
        else: c.circle(px, py, 2.4*mm, 1, 1)
        c.restoreState()
        h.txt(c, px, py-1.1*mm, kod[:2], h.FB, 4.6, HexColor("#FFFFFF"), "c")
    # acil aydınlatma / yönlendirme
    for kod, x_, y_, t, a in P.ACIL: MP.sembol(v, x_, y_, "acil", "E" if "acil" in t else "→", a)
    for kod, x_, y_, t, a in P.YANGIN: MP.sembol(v, x_, y_, "yangin", kod, a)
    mahal_balonlari(c, v)
    D.kuzey_ok(v, L+pw-13*mm, TOP-13*mm); D.olcek_cubugu(v, L+5*mm, BOT+11*mm)
    h.lejant(c, L+5*mm, BOT+2*mm, [(HexColor("#2E7D5B"), "Kaçış yolu · çıkış"),
        (HexColor("#C8322B"), "Söndürücü · dolap · ihbar"), (HexColor("#E8F5EC"), "Acil aydınlatma")], 6.0)

    x2 = L+pw+7*mm; w2 = R-x2
    yy = kunye(c, x2, TOP, w2, "A-13", "1/75 (A3)")
    h.txt(c, x2, yy-6*mm, h.TR_UP("Kaçış mesafeleri"), h.FB, 8.0, h.NAVY)
    rows = [[m, P._MAHAL_BILGI[m][1], f"{('%.1f'%P.tahliye_uzunluk(y_)).replace('.',',')} m", ck]
            for m, y_, ck in P.TAHLIYE_YOL]
    rows.append(["", h.TR_UP("EN UZUN KAÇIŞ"), f"{('%.1f'%P.TAHLIYE_MAX).replace('.',',')} m",
                 f"sınır {int(P.TAHLIYE_SINIR)} m"])
    yy = h.tablo(c, x2, yy-11*mm, [("No",0.10),("Mahal",0.44),("Mesafe",0.22),("Çıkış",0.24)],
                 rows, w2, satir_h=5.6*mm, bas_h=6.4*mm, fs=6.2, hfs=6.0, hizala=["c","l","r","c"])
    h.txt(c, x2, yy-6*mm, h.TR_UP("Yangın güvenlik donanımı"), h.FB, 8.0, h.NAVY)
    rows2 = [[k[0], k[2]] for k in P.YANGIN_EKIPMAN] + \
            [[y_[0], y_[3]] for y_ in P.YANGIN] + \
            [["AY1–3", "Çıkış yönlendirme armatürü — kendinden akülü, 60 dk"],
             ["AA1–5", "Acil aydınlatma armatürü — kendinden akülü, 60 dk"]]
    yy = h.tablo(c, x2, yy-11*mm, [("Kod",0.16),("Tanım",0.84)], rows2, w2,
                 satir_h=5.4*mm, bas_h=6.4*mm, fs=6.1, hfs=6.0, hizala=["c","l"])
    h.notkutu(c, x2, yy-5*mm, w2, "Tahliye değerlendirmesi",
      f"İki bağımsız çıkış (Ç1 ana giriş 1,60 m · Ç2 acil çıkış 1,00 m) mevcuttur; toplam çıkış genişliği "
      f"2,60 m, {P.KISI} kişilik tasarım kapasitesi için fazlasıyla yeterlidir. En uzun kaçış mesafesi "
      f"{('%.1f'%P.TAHLIYE_MAX).replace('.',',')} m olup Binaların Yangından Korunması Hakkında Yönetmelik'in "
      f"iki çıkışlı tesisler için öngördüğü sınırın çok altındadır. Kaçış kapıları kaçış yönünde açılacak, "
      "panik donanımlı olacak, üzerinde kilit bulunmayacaktır. Kaçış yolu genişliği hiçbir noktada 1,10 m'nin "
      "altına düşmeyecek; ekipman ve mobilya bu koridora taşırılmayacaktır.",
      fs=6.3, acc=h.GREEN)

# ══ 14 · DUVAR TİPLERİ — YATAY KESİT 1/10 ═════════════════════════════════════
def s14(c):
    sayfa(c, 14, "Duvar tipleri — yatay kesit 1/10",
          "Gerçek profil geometrisi · C50×50×0,6 dikme @400 mm · levha katmanları · taşyünü dolgu")
    w1 = CW*0.49; w2 = CW-w1-8*mm
    y = TOP-10*mm
    for i, tip in enumerate(("D2", "D3")):
        y, tot = DD.yatay_kesit(c, L, y, w1, tip, olcek=0.20, adet=2)
        y -= 14*mm
    y2 = TOP-10*mm
    for tip in ("D4", "D6"):
        y2, tot = DD.yatay_kesit(c, L+w1+8*mm, y2, w2, tip, olcek=0.20, adet=2)
        y2 -= 14*mm
    # karkas metrajı ve kurallar
    yy = min(y, y2)-4*mm
    h.txt(c, L, yy, h.TR_UP("Karkas metrajı — geometriden türetilmiştir"), h.FB, 8.0, h.NAVY)
    rows = []
    import math as _m
    for a, b, tip, t in DD.BOLME:
        rows.append([tip, f"({a[0]:.2f}, {a[1]:.2f}) → ({b[0]:.2f}, {b[1]:.2f})".replace(".", ","),
                     f"{_m.dist(a, b):.2f}".replace(".", ","),
                     str(len(DD.dikme_noktalari(a, b))),
                     f"{_m.dist(a, b)*P.KOT_YAPISAL_TAVAN:.2f}".replace(".", ",")])
    rows.append(["", h.TR_UP("TOPLAM"), f"{DD.BOLME_UZUNLUK:.2f}".replace(".", ","),
                 str(DD.DIKME_ADEDI),
                 f"{DD.BOLME_UZUNLUK*P.KOT_YAPISAL_TAVAN:.2f}".replace(".", ",")])
    yy = h.tablo(c, L, yy-5*mm, [("Tip",0.08),("Eksen (m)",0.40),("Uzunluk (m)",0.16),
                                 ("C50 dikme",0.16),("Alan (m²)",0.20)], rows, w1,
                 satir_h=5.2*mm, bas_h=6.2*mm, fs=6.0, hfs=6.0,
                 hizala=["c","l","r","c","r"])
    x2 = L+w1+8*mm
    h.txt(c, x2, min(y, y2)-2*mm, h.TR_UP("İmalat kuralları"), h.FB, 8.0, h.NAVY)
    yy2 = min(y, y2)-8*mm
    for n in [
      "Taban ve tavan kanalı U50×40×0,6; taban kanalı altına butil ses bandı serilir, "
      "dübel aralığı en fazla 600 mm.",
      "C50×50×0,6 dikmeler @400 mm; dikme boyu, kat yüksekliğinden 10 mm kısa kesilir "
      "(yapısal hareket payı). Dikme kanalın içine oturtulur, kanala vidalanmaz.",
      "Kapı kenarlarında ve 3,00 m'den uzun duvarlarda iki C profil sırt sırtta kutu profil "
      "olarak birleştirilir; kapı lentosu U profilden teşkil edilir.",
      "Alçıpan derzleri iki yüzde şaşırtmalı; ikinci kat, ilk kata göre 600 mm kaydırılır. "
      "Vida aralığı kenarda 200 mm, ortada 300 mm.",
      "Ağır asma yük (ayna, dolap, TV) için karkas içine 18 mm su kontraplağı takviye gömülür.",
      "Taşyünü dolgu 40 mm / 50 kg/m³, dikmeler arasına sıkıştırılarak yerleştirilir; "
      "boşluk bırakılmaz.",
      "Islak hacim yüzünde 12,5 mm H2 (yeşil) alçıpan kullanılır; alt kenarı bitmiş zeminden "
      "10 mm yukarıda bırakılır ve su yalıtımı levha üzerine uygulanır.",
      "Tüm bölmeler asma tavan üstünden geçerek yapısal döşemeye (+3,20) kadar yükselir.",
    ]:
        for ln in h.wrap(c, "— "+n, h.F, 6.2, w2):
            h.txt(c, x2, yy2, ln, h.F, 6.2, h.INK); yy2 -= 3.4*mm
        yy2 -= 1.4*mm

# ══ BUILD ══════════════════════════════════════════════════════════════════════
def build(path="output/Gym_Mimari_Proje_A3.pdf"):
    c = canvas.Canvas(path, pagesize=(W, HH))
    c.setTitle(f"Maltepe / İdealtepe — Mimari Uygulama Projesi ({P.REV})")
    for fn in (s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14):
        fn(c); c.showPage()
    c.save(); print("→", path)

if __name__ == "__main__":
    build()
