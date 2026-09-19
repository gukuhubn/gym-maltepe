# -*- coding: utf-8 -*-
"""AUTOCAD UYGULAMA PROJESİ SETİ — DXF R2010 (mimari + mekanik + elektrik)

Üretilen dosyalar (cad/):
  GYM-MIM-Uygulama-R2010.dxf    mimari — 5 pafta (altlık · uygulama · zemin · tavan · yangın)
  GYM-MEK-Uygulama-R2010.dxf    mekanik — 4 pafta
  GYM-ELK-Uygulama-R2010.dxf    elektrik — 4 pafta
  GYM-BIRLESIK-R2010.dxf        tümü — 13 pafta

Birim: milimetre ($INSUNITS=4) · Paftalar: A1 (841×594, ISO 5457) · Ölçek: 1/50
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
# Ölçülmüş rölövede salon ile ıslak bloklar arasında 98 mm bölme boşluğu var;
# poligonlar DEĞMEZ. Bina iç kabuğu için boşluk kapat–aç ile kapatılır; aksi
# hâlde IC üç parçalı olur ve .exterior yoktur (build_dxf bu yüzden çöküyordu).
IC   = P.IC_KABUK
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
        b_ = g.bounds
        yazi(msp, ((b_[0]+b_[2])/2*K, b_[3]*K-120), kod, 150, "A-EKIPMAN", stil="GYM-B")
    for ad, g, tip in P.MOBILYA: sekil(msp, g, "A-MOBILYA")
    blok(msp, "G_KUZEY", (12.55, 12.10), "G-KUZEY")

def olculer(msp, olcek=50):
    ds = f"GYM-{olcek}"
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
    # aks sistemi zincir ölçüleri (yapının kendi doğrultusunda)
    import aks as AKS
    AKS.olculendir(msp, olcek)


def aks_ciz(msp, olcek=50):
    import aks as AKS
    return AKS.ciz(msp, olcek)


# ── kesit / detay işaretleri ─────────────────────────────────────────────────
def kesit_isareti(msp, a, b, ad, bakis=+1, pafta_ref="", olcek=50,
                  uc_boy=1.30, balon_r=0.44):
    """Profesyonel kesit işareti: hat boyunca yalnız UÇLARDA ağır çizgi,
    bakış yönünde ok ve pafta referanslı balon. Kesit hattı plan boyunca
    kesintisiz çizilmez."""
    import dxf_lib as X
    ax, ay = a; bx, by = b
    L = math.dist(a, b)
    ux, uy = (bx-ax)/L, (by-ay)/L
    nx, ny = -uy*bakis, ux*bakis           # bakış yönü normali
    for ucp, yon in (((ax, ay), +1), ((bx, by), -1)):
        p2 = (ucp[0]+ux*uc_boy*yon, ucp[1]+uy*uc_boy*yon)
        X.cizgi(msp, ucp, p2, "A-KESIT-HAT")
        # bakış oku
        ok0 = (p2[0], p2[1])
        ok1 = (p2[0]+nx*0.62, p2[1]+ny*0.62)
        X.cizgi(msp, ok0, ok1, "A-KESIT-HAT")
        for s_ in (+1, -1):
            X.cizgi(msp, ok1,
                    (ok1[0]-nx*0.20 + s_*ux*0.12, ok1[1]-ny*0.20 + s_*uy*0.12),
                    "A-KESIT-HAT")
        # balon: üstte kesit adı, altta pafta referansı
        cx = ucp[0]-ux*balon_r*yon*-1
        cx, cy = ucp[0]-ux*balon_r*yon, ucp[1]-uy*balon_r*yon
        msp.add_circle((cx*K, cy*K), balon_r*K,
                       dxfattribs={"layer": "A-KESIT-HAT"})
        if pafta_ref:
            X.cizgi(msp, (cx-balon_r, cy), (cx+balon_r, cy), "A-KESIT-HAT")
            X.yazi(msp, (cx*K, cy*K+balon_r*K*0.45), ad.split("-")[0],
                   balon_r*K*0.72, "A-KESIT-HAT", stil="GYM-B")
            X.yazi(msp, (cx*K, cy*K-balon_r*K*0.45), pafta_ref,
                   balon_r*K*0.52, "A-KESIT-HAT")
        else:
            X.yazi(msp, (cx*K, cy*K), ad.split("-")[0], balon_r*K*0.82,
                   "A-KESIT-HAT", stil="GYM-B")


# ── balon çakışma önleyici ───────────────────────────────────────────────────
_BALON_KONUM = []

def balon_sifirla():
    _BALON_KONUM.clear()

def _bos_balon(x, y, asgari=0.82):
    for qx, qy in _BALON_KONUM:
        if math.hypot(x-qx, y-qy) < asgari: return False
    return True


def _halkalar(baslangic=0.0, adim=0.55, halka=5, n=12):
    """Merkezden dışa doğru genişleyen aday konum halkaları."""
    yield (0.0, 0.0)
    r = baslangic
    for _ in range(halka):
        r += adim
        for i in range(n):
            a = 2*math.pi*i/n
            yield (math.cos(a)*r, math.sin(a)*r)


def balon_yerlestir(p, tercih=None, sinirla=None):
    """Çakışmayan balon konumu. `sinirla` verilirse (shapely poligon) balon
    yalnız o poligonun içinde/yakınında aranır."""
    adaylar = tercih if tercih else _halkalar()
    for dx, dy in adaylar:
        q = (p[0]+dx, p[1]+dy)
        if sinirla is not None and not sinirla.contains(Point(*q)):
            continue
        if _bos_balon(*q):
            _BALON_KONUM.append(q); return q
    q = (p[0], p[1]+0.9)
    _BALON_KONUM.append(q); return q

# ══════════════════════ MEKANİK ════════════════════════════════════════════════
def mekanik(msp):
    mekanik_havalandirma(msp)
    mekanik_iklimlendirme(msp)
    mekanik_sihhi(msp)

# ══════════════════════ ELEKTRİK ═══════════════════════════════════════════════
def elektrik(msp):
    elektrik_aydinlatma(msp)
    elektrik_kuvvet(msp)
    elektrik_zayif(msp)
    elektrik_toprak(msp)


# ══════════════════════ MİMARİ UYGULAMA PAFTALARI ══════════════════════════════
def _balon(msp, p, metin, r_mm=340, katman="A-MAHAL"):
    msp.add_circle(M(p), r_mm, dxfattribs={"layer": katman})
    yazi(msp, M(p), metin, r_mm*0.80, katman, stil="GYM-B")

def mimari_mahal(msp, olcek=50, pafta_ref="A-06"):
    """Mahal numaraları, kapı kodları, duvar tipi etiketleri, kesit işaretleri.

    Balonlar çakışma önleyiciden geçirilir; kesit hattı plan boyunca
    kesintisiz çizilmez, yalnız uçlarda işaretlenir."""
    balon_sifirla()
    # önce kesit işaretleri (sabit konumlu) — balon rezervasyonu yapar
    for ad, (a, b, _ack) in P.KESIT_HATLARI.items():
        kesit_isareti(msp, a, b, ad, P.KESIT_BAKIS.get(ad, 1), pafta_ref, olcek)
        for uc in (a, b): _BALON_KONUM.append(uc)
    # mahal adı / alan yazıları önce rezerve edilir ki balon üstlerine binmesin
    for z in P.ZONES:
        _BALON_KONUM.append(tuple(z[5]))
        _BALON_KONUM.append((z[5][0], z[5][1]-0.30))
    for ad, d in P.ISLAK.items():
        for n in ("soyunma", "dus", "wc"):
            q = d[n].representative_point()
            _BALON_KONUM.append((q.x, q.y)); _BALON_KONUM.append((q.x, q.y-0.23))
    for kod, ad_, g in P.ekipman_poligonlari():
        _BALON_KONUM.append((g.centroid.x, g.centroid.y))
    # mahal balonları — kendi mahalinin içinde ve yazıların altında kalır
    _mahal_geom = {mno: g for ad, mno, g in P._MAHAL_GEOM}
    for no, pt in P.MAHAL_NOKTA.items():
        g = _mahal_geom.get(no)
        sinir = g.buffer(-0.38) if g is not None and g.buffer(-0.38).area > 0.05 else None
        q = balon_yerlestir((pt[0], pt[1]-0.72), _halkalar(0.0, 0.40, 6),
                            sinirla=sinir)
        _balon(msp, q, no, 320)
        if math.dist(q, (pt[0], pt[1]-0.72)) > 0.45:
            cizgi(msp, pt, q, "A-MAHAL")
    # kapı balonları — konum KAPI_GEOM'dan (tek kaynak); K05–K08 önceden
    # elle yazılmıştı ve plandaki kapıyla ilişkisizdi
    for kod, (pt, gen, aci) in sorted(P.KAPI_GEOM.items()):
        q = balon_yerlestir(pt, _halkalar(0.30, 0.42, 5))
        _balon(msp, q, kod, 290)
        cizgi(msp, pt, q, "A-MAHAL")
    for kod, pt in (("K09", (2.55, 7.05)),):          # mobilya kapağı — mahal kapısı değil
        q = balon_yerlestir(pt, _halkalar(0.30, 0.42, 5))
        _balon(msp, q, kod, 290)
        cizgi(msp, pt, q, "A-MAHAL")
    # duvar tipi etiketleri — kutulu, çakışma kontrollü
    for tip, pt in (("D2",(8.35,6.30)), ("D3",(9.72,6.30)), ("D4",(7.35,0.42)),
                    ("D1",(5.90,11.30)), ("D6",(5.05,0.42)), ("D5",(10.30,2.30))):
        q = balon_yerlestir(pt, _halkalar(0.0, 0.42, 4))
        poli(msp, [(q[0]-0.24, q[1]-0.15), (q[0]+0.24, q[1]-0.15),
                   (q[0]+0.24, q[1]+0.15), (q[0]-0.24, q[1]+0.15)], "A-MAHAL")
        yazi(msp, M(q), tip, 200, "A-MAHAL", stil="GYM-B")

def mimari_zemin(msp):
    """Zemin kaplama planı: tip sınırı, kod, kot, kauçuk karo derzi, eğim."""
    Z = {m[0]: m[3] for m in P.MAHAL_LISTESI}
    for ad, mno, g in P._MAHAL_GEOM:
        sekil(msp, g, "A-ZEMIN-SINIR")
        pt = P.MAHAL_NOKTA[mno]
        kot = "−0,02" if P._MAHAL_BILGI[mno][9] else "±0,00"
        yazi(msp, (pt[0]*K, pt[1]*K-420), f"{Z[mno]}  {kot}", 220, "A-ZEMIN-YAZI", stil="GYM-B")
    sekil(msp, P.hex_poly(*P.EKIPMAN[0][5]), "A-ZEMIN-SINIR")
    yazi(msp, M(P.EKIPMAN[0][5]), "Z6  +0,30", 220, "A-ZEMIN-YAZI", stil="GYM-B")
    for zn in ("ARENA · SERBEST AĞIRLIK", "FONKSİYONEL · KARDİYO"):
        g = [z[1] for z in P.ZONES if z[0] == zn][0]; b = g.bounds
        for gx in range(int(b[0]), int(b[2])+2):
            seg = LineString([(gx, b[1]-1), (gx, b[3]+1)]).intersection(g)
            for s_ in (seg.geoms if seg.geom_type.startswith("Multi") else [seg]):
                if s_.geom_type == "LineString" and not s_.is_empty:
                    cizgi(msp, s_.coords[0], s_.coords[-1], "A-ZEMIN-DERZ")
        for gy in range(int(b[1]), int(b[3])+2):
            seg = LineString([(b[0]-1, gy), (b[2]+1, gy)]).intersection(g)
            for s_ in (seg.geoms if seg.geom_type.startswith("Multi") else [seg]):
                if s_.geom_type == "LineString" and not s_.is_empty:
                    cizgi(msp, s_.coords[0], s_.coords[-1], "A-ZEMIN-DERZ")
    for ad, d in P.ISLAK.items():
        for n in ("dus", "wc"):
            q = d[n].representative_point(); bb = d[n].bounds
            cizgi(msp, (bb[0]+0.12, bb[1]+0.12), (q.x, q.y), "A-ZEMIN-SINIR")
            yazi(msp, (q.x*K, q.y*K+260), "%1,5", 150, "A-ZEMIN-YAZI")

def mimari_tavan(msp):
    """Tavan planı: tip sınırı, kot, revizyon kapağı."""
    T = {m[0]: m[6] for m in P.MAHAL_LISTESI}
    for ad, mno, g in P._MAHAL_GEOM:
        sekil(msp, g, "A-TAVAN-SINIR")
        pt = P.MAHAL_NOKTA[mno]; tt = T[mno]
        yazi(msp, (pt[0]*K, pt[1]*K-420), f"{tt}  +{('%.2f' % P.TAVAN_KOT[tt]).replace('.', ',')}",
             220, "A-TAVAN-YAZI", stil="GYM-B")
    for ad, d in P.ISLAK.items():
        for n in ("dus", "wc"):
            bb = d[n].bounds; rx, ry = bb[0]+0.28, bb[3]-0.28
            poli(msp, [(rx-0.15, ry-0.15), (rx+0.15, ry-0.15),
                       (rx+0.15, ry+0.15), (rx-0.15, ry+0.15)], "A-TAVAN-KAPAK")
            cizgi(msp, (rx-0.15, ry-0.15), (rx+0.15, ry+0.15), "A-TAVAN-KAPAK")

def mimari_yangin(msp):
    """Yangın ve tahliye planı: kaçış yolu, çıkış, söndürücü."""
    for mno, yol, cik in P.TAHLIYE_YOL:
        poli(msp, yol, "A-YANGIN-KACIS", kapali=False)
        for i in range(1, len(yol)):
            ax, ay = yol[i-1]; bx, by = yol[i]
            ang = math.atan2(by-ay, bx-ax)
            mx, my = (ax+bx)/2, (ay+by)/2
            uc = (mx+math.cos(ang)*0.18, my+math.sin(ang)*0.18)
            for yn in (+1, -1):
                q = (mx+math.cos(ang+yn*2.5)*0.16, my+math.sin(ang+yn*2.5)*0.16)
                cizgi(msp, uc, q, "A-YANGIN-KACIS")
        yazi(msp, (yol[0][0]*K, yol[0][1]*K+420),
             f"{('%.1f' % P.tahliye_uzunluk(yol)).replace('.', ',')} m → {cik}",
             170, "A-YANGIN-KACIS", stil="GYM-B")
    for kod, pt, gen, ad in P.CIKISLAR:
        _balon(msp, pt, kod, 420, "A-YANGIN-KACIS")
        yazi(msp, (pt[0]*K, pt[1]*K+620), f"{ad} · {('%.2f' % gen).replace('.', ',')} m",
             160, "A-YANGIN-KACIS")
    for kod, pt, ad in P.YANGIN_EKIPMAN:
        if kod.startswith("YD"):
            poli(msp, [(pt[0]-0.22, pt[1]-0.22), (pt[0]+0.22, pt[1]-0.22),
                       (pt[0]+0.22, pt[1]+0.22), (pt[0]-0.22, pt[1]+0.22)], "A-YANGIN-EKIP")
        else:
            msp.add_circle(M(pt), 220, dxfattribs={"layer": "A-YANGIN-EKIP"})
        yazi(msp, M(pt), kod, 150, "A-YANGIN-EKIP", stil="GYM-B")

# ── LİNYE (ORTOGONAL TESİSAT HATTI) ──────────────────────────────────────────
def linye_ciz(msp, kodlar, katman, etiket=True):
    """data/yollar.json içindeki ortogonal güzergâhları çizer.

    Çapraz segment çizilmez — tesisat hatları yalnız yatay/düşey ilerler.
    """
    import linye_yollari as LY, draw_mep as DM
    d = LY.yukle()
    if not d: return 0
    n = 0
    for kod in kodlar:
        kayit = d["linye"].get(kod)
        if not kayit: continue
        en = (0.0, None, None)
        for g in kayit["segment"]:
            for a, b in zip(g, g[1:]):
                if abs(a[0]-b[0]) > 1e-6 and abs(a[1]-b[1]) > 1e-6: continue
                cizgi(msp, a, b, katman)
                dd = math.dist(a, b)
                if dd > en[0]: en = (dd, a, b)
        if etiket and en[1]:
            a, b = en[1], en[2]
            mx, my = (a[0]+b[0])/2, (a[1]+b[1])/2
            aci = 0 if abs(a[1]-b[1]) < 1e-6 else 90
            yazi(msp, (mx*K, my*K+120), DM.linye_etiketi(kod), 150, "E-YAZI", aci=aci)
        n += 1
    return n


def anahtar_sorti_ciz(msp, katman="E-AYD-SORTI"):
    import linye_yollari as LY
    d = LY.yukle()
    if not d: return
    for kayit in d.get("anahtar", []):
        for g in kayit["segment"]:
            for a, b in zip(g, g[1:]):
                if abs(a[0]-b[0]) > 1e-6 and abs(a[1]-b[1]) > 1e-6: continue
                cizgi(msp, a, b, katman)


# ── DİSİPLİN ALT ÇİZİMLERİ (her pafta yalnız kendi içeriğini alır) ───────────
def elektrik_aydinlatma(msp):
    import draw as D
    zon_linye = {"ARENA · SERBEST AĞIRLIK": "L1", "FONKSİYONEL · KARDİYO": "L2",
                 "DİNLENME SALONU": "L3", "GİRİŞ · BANKO · SİRKÜLASYON": "L4"}
    izgara = D.aydinlatma_izgara(); i = 0
    anahtar_sorti_ciz(msp)
    linye_ciz(msp, ["L1", "L2", "L3", "L4", "L5", "L6"], "E-AYD-LINYE")
    for z in P.ZONES:
        for _ in range(P.ZON_ARMATUR[z[0]]):
            if i >= len(izgara): break
            blok(msp, "E_ARMATUR_LINEER", izgara[i], "E-AYD-ARMATUR",
                 {"LINYE": zon_linye[z[0]]}); i += 1
    for ad, d in P.ISLAK.items():
        for n in ("soyunma", "dus", "wc"):
            q = d[n].representative_point()
            blok(msp, "E_DOWNLIGHT", (q.x, q.y), "E-AYD-DOWNLIGHT", {"LINYE": "L5"})
    for kod, x, y, t, a in P.ACIL:
        blok(msp, "E_ACIL" if "acil" in t else "E_YONLENDIRME", (x, y),
             "E-AYD-ACIL", {"KOD": kod}, aci=a)
    for kod, x, y, t, a in P.ANAHTAR:
        blok(msp, "E_ANAHTAR", (x, y), "E-AYD-ANAHTAR", {"KOD": kod}, aci=a)
    for kod, x, y, t, a in P.SENSOR:
        blok(msp, "E_SENSOR", (x, y), "E-AYD-ANAHTAR", {"KOD": kod})
    _pano(msp)


def elektrik_kuvvet(msp):
    linye_ciz(msp, ["P1", "P2", "P6", "P3", "P4", "P5", "K1", "K2", "K3", "K4",
                    "W1", "W2", "V1", "V2"], "E-KUVVET-LINYE")
    _priz_linye = {"P1": ("PR12","PR13","PR14","PR15","PR16","PR1"),
                   "P2": ("PR5","PR6","PR7","PR8","PR9"),
                   "P6": ("PR2","PR3","PR4","PR10","PR11")}
    for kod, x, y, t, a in P.PRIZ:
        ln = "P4" if kod.startswith("PK") else ("P3" if kod.startswith("PB") else
             next((k for k, v in _priz_linye.items() if kod in v), "P1"))
        blok(msp, "E_PRIZ", (x, y), "E-KUVVET-PRIZ", {"KOD": kod, "LINYE": ln}, aci=a)
    for kod, x, y, t, a in P.PRIZ_IP44:
        blok(msp, "E_PRIZ_IP44", (x, y), "E-KUVVET-PRIZ", {"KOD": kod, "LINYE": "P5"}, aci=a)
    for j, (kod, zon, btu, (x, y), a) in enumerate(P.KLIMA):
        blok(msp, "M_KLIMA_IC", (x, y), "E-KUVVET-CIHAZ",
             {"KOD": kod, "KAPASITE": "1×16 A"}, aci=a)
    for j, (kod, x, y, ad, a) in enumerate(P.ISITICI):
        blok(msp, "M_ISITICI", (x, y), "E-KUVVET-CIHAZ",
             {"KOD": kod, "GUC": "1×20 A"}, aci=a)
    for kod, x, y, ad, a in P.FAN:
        blok(msp, "M_FAN", (x, y), "E-KUVVET-CIHAZ", {"KOD": kod, "TANIM": "1×10 A"}, aci=a)
    _pano(msp)


def elektrik_zayif(msp):
    linye_ciz(msp, ["Z1"], "E-ZAYIF-TAVA")
    linye_ciz(msp, ["Z2"], "E-ZAYIF-LINYE")
    for kod, x, y, t, a in P.KAMERA: blok(msp, "E_KAMERA", (x, y), "E-ZAYIF-KAMERA", {"KOD": kod}, aci=a)
    for kod, x, y, t in P.HOPARLOR: blok(msp, "E_HOPARLOR", (x, y), "E-ZAYIF-SES", {"KOD": kod})
    for kod, x, y, t in P.VERI:     blok(msp, "E_VERI", (x, y), "E-ZAYIF-VERI", {"KOD": kod})
    for kod, x, y, t in P.DEDEKTOR: blok(msp, "E_DEDEKTOR", (x, y), "E-ZAYIF-YANGIN", {"KOD": kod})
    for kod, x, y, t, a in P.YANGIN:
        blok(msp, "E_YANGIN_BUTON", (x, y), "E-ZAYIF-YANGIN", {"KOD": kod}, aci=a)
    for ad, d in P.ISLAK.items():
        q = d["tum"].representative_point()
        yazi(msp, (q.x*K, q.y*K-520), "KAMERA YOK", 180, "E-YAZI", stil="GYM-B")
    _pano(msp)


def elektrik_toprak(msp):
    """Topraklama ve potansiyel dengeleme paftası."""
    import yol as Y
    serit = [(e[1], e[2]) for e in P.ELEKTROT]
    poli(msp, serit, "E-TOPRAK-SERIT", False)
    for kod, x, y in P.ELEKTROT:
        msp.add_circle((x*K, y*K), 200, dxfattribs={"layer": "E-TOPRAK-ELEKTROT"})
        cizgi(msp, (x, y-0.14), (x, y+0.14), "E-TOPRAK-ELEKTROT")
        cizgi(msp, (x-0.11, y-0.14), (x+0.11, y-0.14), "E-TOPRAK-ELEKTROT")
        cizgi(msp, (x-0.07, y-0.21), (x+0.07, y-0.21), "E-TOPRAK-ELEKTROT")
        yazi(msp, (x*K+300, y*K), kod, 170, "E-TOPRAK-YAZI", stil="GYM-B")
    ana = Y.guzergah((P.ELEKTROT[1][1]-0.55, P.ELEKTROT[1][2]), P.ATB)
    if ana:
        cizgi(msp, (P.ELEKTROT[1][1], P.ELEKTROT[1][2]), ana[0], "E-TOPRAK-ILETKEN")
        poli(msp, ana, "E-TOPRAK-ILETKEN", False)
    for kod, x, y, aciklama in P.EPDB:
        g = Y.guzergah(P.ATB, (x, y))
        if g: poli(msp, g, "E-TOPRAK-ILETKEN", False)
        poli(msp, [(x-0.28, y-0.13), (x+0.28, y-0.13),
                   (x+0.28, y+0.13), (x-0.28, y+0.13)], "E-TOPRAK-BARA")
        yazi(msp, (x*K, y*K), kod, 150, "E-TOPRAK-YAZI", stil="GYM-B")
    ax, ay = P.ATB
    poli(msp, [(ax-0.38, ay-0.16), (ax+0.38, ay-0.16),
               (ax+0.38, ay+0.16), (ax-0.38, ay+0.16)], "E-TOPRAK-BARA")
    yazi(msp, (ax*K, ay*K), "ATB", 180, "E-TOPRAK-YAZI", stil="GYM-B")
    yazi(msp, (ax*K, ay*K-400),
         f"Ra = {('%.1f' % P.TOPRAK_R_HESAP).replace('.', ',')} Ω ≤ "
         f"{int(P.TOPRAK_HEDEF)} Ω", 150, "E-TOPRAK-YAZI")
    _pano(msp)


def _pano(msp):
    blok(msp, "E_PANO", P.PANO, "E-PANO",
         {"KOD": "ADP", "TANIM": f"3×{P.ANA_KESICI//3} A · {len(P.LINYE)} linye"},
         aci=P.PANO_ACI)


def mekanik_havalandirma(msp):
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
        hat = P.KANAL["besleme" if tip == "besleme" else
                      ("egzoz" if tip == "egzoz" else "islak")]
        ls = LineString(hat["guzergah"]); q = ls.interpolate(ls.project(Point(x, y)))
        # branşman ortogonal: önce yatay, sonra düşey
        cizgi(msp, (q.x, q.y), (x, q.y), "M-HAVA-BRANSMAN")
        cizgi(msp, (x, q.y), (x, y), "M-HAVA-BRANSMAN")
        b = {"besleme": "M_MENFEZ_BESLEME", "egzoz": "M_MENFEZ_EGZOZ",
             "valf": "M_VALF"}[tip]
        blok(msp, b, (x, y), "M-HAVA-MENFEZ", {"KOD": kod, "DEBI": f"{debi} m³/h"})
    for kod, x, y, ad, a in P.FAN:
        blok(msp, "M_FAN", (x, y), "M-HAVA-CIHAZ",
             {"KOD": kod, "TANIM": ad.split("—")[-1].strip()}, aci=a)
    for kod, x, y, ad in P.PANJUR:
        blok(msp, "M_PANJUR", (x, y), "M-HAVA-CIHAZ", {"KOD": kod})


def mekanik_iklimlendirme(msp):
    for hat in P.BAKIR_HAT.values(): poli(msp, hat, "M-KLIMA-BAKIR", False)
    for hat in P.DRENAJ.values(): poli(msp, hat, "M-KLIMA-DRENAJ", False)
    for kod, zon, btu, (x, y), a in P.KLIMA:
        blok(msp, "M_KLIMA_IC", (x, y), "M-KLIMA-IC",
             {"KOD": kod, "KAPASITE": f"{btu} BTU"}, aci=a)
    blok(msp, "M_KLIMA_DIS", P.DIS_UNITE, "M-KLIMA-DIS",
         {"KOD": "DIŞ ÜNİTE PLATFORMU", "ADET": f"{P.ADET_KLIMA} adet"})


def mekanik_sihhi(msp):
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
    for kod, x, y, ad, a in P.ISITICI:
        blok(msp, "M_ISITICI", (x, y), "M-SIHHI-CIHAZ",
             {"KOD": kod, "GUC": "3 kW / 100 L"}, aci=a)
    blok(msp, "M_SAYAC", P.SU_GIRIS, "M-SIHHI-TEMIZ", {"KOD": "SAYAÇ + ANA KESME"})


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

PAFTA_BOYUT = (420, 297)          # A3 — TS EN ISO 216
PAFTA_KENAR = (20, 10, 10, 10)    # sol(cilt), üst, sağ, alt — TS EN ISO 5457
# Antette bulunması zorunlu alanlar (TMMOB MMO Proje Hazırlama ve Mesleki
# Denetim Esasları + Yapı Ruhsatı eki proje antet gereklilikleri)
ANTET_ALANLARI = [
 "İŞVEREN", "PROJE", "YAPI / MAHAL", "DİSİPLİN", "PAFTA ADI", "PAFTA NO",
 "ÖLÇEK", "TARİH", "REVİZYON", "ÇİZEN", "KONTROL", "ONAY",
 "PROJE MÜELLİFİ / ODA SİCİL NO",
]

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
 "E-05": ("TOPRAKLAMA VE POTANSİYEL DENGELEME PLANI", "ELEKTRİK",
          ["M-", "E-AYD-", "E-KUVVET-", "E-ZAYIF-"]),
 "A-01": ("MİMARİ ALTLIK", "MİMARİ",
          ["M-", "E-", "A-ZEMIN-", "A-TAVAN-", "A-YANGIN-"]),
 "A-02": ("MİMARİ UYGULAMA PLANI", "MİMARİ",
          ["M-", "E-", "A-ZEMIN-", "A-TAVAN-", "A-YANGIN-"]),
 "A-03": ("ZEMİN KAPLAMA PLANI", "MİMARİ",
          ["M-", "E-", "A-TAVAN-", "A-YANGIN-", "A-YAZI", "A-KESIT-HAT", "A-EKIPMAN", "A-MOBILYA"]),
 "A-04": ("TAVAN PLANI (RCP)", "MİMARİ",
          ["M-SIHHI-", "M-KLIMA-", "E-KUVVET-", "E-ZAYIF-", "A-ZEMIN-", "A-YANGIN-",
           "A-YAZI", "A-KESIT-HAT", "A-EKIPMAN"]),
 "A-05": ("YANGIN VE TAHLİYE PLANI", "MİMARİ",
          ["M-", "E-KUVVET-", "E-ZAYIF-KAMERA", "E-ZAYIF-SES", "E-ZAYIF-VERI",
           "E-ZAYIF-LINYE", "E-AYD-ARMATUR", "E-AYD-DOWNLIGHT", "E-AYD-ANAHTAR",
           "E-PANO", "E-YAZI", "A-ZEMIN-", "A-TAVAN-", "A-KESIT-HAT", "A-EKIPMAN"]),
}

# Pafta üst başlığı (supplementary title) ve sıradaki pafta (ISO 7200)
PAFTA_USTBASLIK = {
 "A-01": "Mevcut durum · ölçü ve aks sistemi",
 "A-02": "Bölme duvarlar · kapılar · mahal numaraları",
 "A-03": "Kaplama tipleri · kot · derz yönü",
 "A-04": "Asma tavan tipleri · kot · MEP koordinasyonu",
 "A-05": "Kaçış yolları · çıkışlar · söndürücü",
 "M-01": "Kanal güzergâhı · menfez debileri",
 "M-02": "Split küme · bakır hat · drenaj",
 "M-03": "Temiz su · sıcak su · pis su",
 "M-04": "Mekanik disiplin genel yerleşimi",
 "E-01": "Armatür · anahtar · aydınlatma linyeleri",
 "E-02": "Priz · kuvvet linyeleri · cihaz beslemeleri",
 "E-03": "Veri · CCTV · ses · yangın algılama",
 "E-04": "Elektrik disiplin genel yerleşimi",
 "E-05": "Elektrot grubu · ATB · EPDB",
 "E-06": "ADP tek hat şeması",
}
PAFTA_SONRAKI = {
 "A-01": "A-02", "A-02": "A-03", "A-03": "A-04", "A-04": "A-05", "A-05": "M-01",
 "M-01": "M-02", "M-02": "M-03", "M-03": "M-04", "M-04": "E-01",
 "E-01": "E-02", "E-02": "E-03", "E-03": "E-04", "E-04": "E-05", "E-05": "ADP-01",
}

PROJE_BILGI = {
 "isveren": "ÖZEL — MALTEPE / İDEALTEPE",
 "ad": "MOBİLYA MAĞAZASI → FONKSİYONEL ANTRENMAN STÜDYOSU",
 "yapi": "İdealtepe Mah. · zemin kat dükkân · 103,78 m² iç alan",
 "no": "GYM-25-001",
}
MUELLIF  = "—"                     # imza/onay aşamasında doldurulur
SICIL    = "Oda sicil no: —"
PAFTA_BOY = "A1"                   # tüm set tek kâğıt boyunda — TS EN ISO 216
PAFTA_BOYUT = KAGIT_A1 = (841, 594)
OLCEK_PLAN = 50                    # 1:50 uygulama ölçeği (MEB/MMO uygulama projesi)

REVIZYONLAR = [
 ("A", "17.09.2026", "İlk yayın — ön tasarım", "CC", "—", "—"),
 ("B", "18.09.2026", "Aks sistemi, zincir ölçü, ISO 5457/7200 pafta", "CC", "—", "—"),
 ("C", "18.09.2026", "A1 pafta, tekil DXF, ADP şeması CAD'de", "CC", "—", "—"),
 ("D", "18.09.2026", "ADP çok hatlı şema (faz ayrımı), B eğrisi, ana RCD",
  "CC", "—", "—"),
]


def _anahtar_plan_ciz(psp, x, y, w, h):
    """Antet üstündeki küçük anahtar plan — yapı çeperi + kuzey."""
    b = IC.bounds
    gw, gh = b[2]-b[0], b[3]-b[1]
    s_ = min((w-8)/gw, (h-8)/gh)
    ox, oy = x+(w-gw*s_)/2-b[0]*s_, y+(h-gh*s_)/2-b[1]*s_
    pts = [(ox+px*s_, oy+py*s_) for px, py in IC.exterior.coords]
    psp.add_lwpolyline(pts, close=True,
                       dxfattribs={"layer": "G-ANTET", "lineweight": 35})
    for g in (P.ERKEK, P.KADIN):
        psp.add_lwpolyline([(ox+px*s_, oy+py*s_) for px, py in g.exterior.coords],
                           close=True, dxfattribs={"layer": "G-ANTET",
                                                   "lineweight": 13})


SEMA_PAFTA = set()   # ölçeksiz şema paftaları artık ayrı sette (build_sema.py)


def pafta_ekle(doc, no, notlar=""):
    """ISO 5457 çerçeveli, ISO 7200 antetli pafta kurar."""
    import pafta as PF
    from pafta import Pafta, ANTET_H as ANTET_H_
    ad, disiplin, donan = PAFTALAR[no]
    ust = PAFTA_USTBASLIK.get(no, "")
    pf = Pafta(doc, no, ad, disiplin, boy=PAFTA_BOY, proje=PROJE_BILGI, ust_ad=ust)
    pf.cerceve()
    pf.antet(olcek="ÖLÇEKSİZ" if no in SEMA_PAFTA else f"1:{OLCEK_PLAN}",
             tarih=P.TARIH, rev=P.REV.split()[-1],
             durum="ÖN TASARIM", muellif=MUELLIF, sicil=SICIL,
             cizen="CC", kontrol="—", onay="—",
             birim="milimetre (mm)", revizyonlar=REVIZYONLAR,
             sonraki=PAFTA_SONRAKI.get(no, ""))
    if no in SEMA_PAFTA:
        import tekhat_dxf as TH
        alt = TH.ciz(pf)
        TH.alt_bloklar(pf, alt)
        pf.durum_damgasi(x=pf.ax-76, y=pf.ay+ANTET_H_+2)
        return pf.lay
    don = [l[0] for l in X.KATMANLAR if any(l[0].startswith(d) for d in donan)]
    pf.gorunum(merkez=(CX, CY), olcek=OLCEK_PLAN, donuk=don)
    pf.kuzey(); pf.olcek_cubugu(OLCEK_PLAN)
    pf.durum_damgasi()
    pf.dikkat_notu()
    # sağ sütun: anahtar plan → lejant → notlar
    sx, sy, sw = pf.sag()
    y = pf.anahtar_plan(_anahtar_plan_ciz, y=sy)
    kullanilan = {e.dxf.layer for e in doc.modelspace()}
    gorunur = [(l[0], l[4]) for l in X.KATMANLAR
               if l[0] in kullanilan
               and not any(l[0].startswith(d) for d in donan)
               and (l[0].startswith(("M-", "E-")) or l[0].startswith("A-"))]
    y = pf.lejant(gorunur[:30], y=y)
    if notlar:
        satirlar = [t.strip() for t in notlar.split("\n") if t.strip()]
        pf.notlar(satirlar, y=y-2)
    return pf.lay

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
 "E-05": "Topraklama ve potansiyel dengeleme.\nElektrot grubu yapi disinda, 4 adet 2 m Cu kapli\n"
         "celik cubuk, 3 m aralik. Ra hesap 15,5 ohm <= 20 ohm.\n"
         "ATB pano altinda; her islak blokta EPDB bulunur.",
 "A-01": "Mimari altlik — mevcut duvar korunur.\nKirmizi: yeni alcipan bolme.\n"
         "Olculer raster paftadan (+/-%3).",
 "A-02": "Mahal no, kapi kodu, duvar tipi ve\nkesit hatti gosterilmistir.\n"
         "Tum alcipan bolmeler yapisal doseme\naltina (+3,20) kadar yukselir.",
 "A-03": "Bitmis zemin kotu tum kuru hacimde\n+/-0,00; dus ve WC -0,02.\n"
         "Tesviye sapi kalinliklari farklidir\n(Z1:3 Z2:30 Z3:42 Z5:38 mm).\n"
         "Kaucuk karo derzi 1000x1000 mm.",
 "A-04": "T1 acik tavan +3,20 · T2 +2,75\nT4 +2,60 · T3 +2,40.\n"
         "Tesisat askisi alcipan karkasina\nasilmaz; ayri askilanir.\n"
         "Her islak hacimde 300x300 revizyon.",
 "A-05": "Iki bagimsiz cikis: C1 1,60 m, C2 1,00 m.\n"
         "En uzun kacis yolu 13,4 m.\n"
         "Kacis kapilari kacis yonunde acilir,\npanik donanimli, kilitsiz.",
}

def belge_uret(ad, mek=True, elk=True, paftalar=(), mim_detay=True):
    doc = X.yeni_belge(ad); X.bloklari_kur(doc); antet_blogu(doc)
    msp = doc.modelspace()
    mimari(msp); aks_ciz(msp, OLCEK_PLAN); olculer(msp, OLCEK_PLAN)
    if mim_detay:
        mimari_mahal(msp, OLCEK_PLAN); mimari_zemin(msp); mimari_tavan(msp)
        mimari_yangin(msp)
    if mek: mekanik(msp)
    if elk: elektrik(msp)
    for no in paftalar: pafta_ekle(doc, no, NOTLAR.get(no, ""))
    if "Layout1" in doc.layouts: doc.layouts.delete("Layout1")
    doc.set_modelspace_vport(height=16000, center=(CX, CY))
    return doc

# ── TEKİL PAFTA: her pafta kendi DXF dosyası, model uzayında YALNIZ o paftanın
#    geometrisi. (Tek model + katman dondurma yerine gerçek pafta ayrımı.)
#    (pafta no) -> (mimari altlık detayı, çizim fonksiyon adları)
TEKIL_PAFTA = {
 "A-01": (False, ["olculer"]),
 "A-02": (False, ["olculer", "mimari_mahal"]),
 "A-03": (False, ["mimari_zemin", "mimari_mahal"]),
 "A-04": (False, ["mimari_tavan", "mekanik_havalandirma", "elektrik_aydinlatma"]),
 "A-05": (False, ["mimari_yangin"]),
 "M-01": (False, ["mekanik_havalandirma"]),
 "M-02": (False, ["mekanik_iklimlendirme"]),
 "M-03": (False, ["mekanik_sihhi"]),
 "M-04": (False, ["mekanik_havalandirma", "mekanik_iklimlendirme", "mekanik_sihhi"]),
 "E-01": (False, ["elektrik_aydinlatma"]),
 "E-02": (False, ["elektrik_kuvvet"]),
 "E-03": (False, ["elektrik_zayif"]),
 "E-04": (False, ["elektrik_aydinlatma", "elektrik_kuvvet", "elektrik_zayif"]),
 "E-05": (False, ["elektrik_toprak"]),
}


def pafta_belgesi(no):
    """Tek paftalık bağımsız DXF: model uyazında yalnız bu paftanın içeriği."""
    ad, disiplin, _ = PAFTALAR[no]
    mim_detay, fnlar = TEKIL_PAFTA[no]
    doc = X.yeni_belge(f"{no}.dxf"); X.bloklari_kur(doc); antet_blogu(doc)
    msp = doc.modelspace()
    if mim_detay is not None:
        mimari(msp)                   # mimari altlık her plan paftasında bulunur
        aks_ciz(msp, OLCEK_PLAN)      # aks sistemi her plan paftasında ortaktır
    for fn in fnlar:
        if fn == "olculer": olculer(msp, OLCEK_PLAN)
        elif fn == "mimari_mahal": mimari_mahal(msp, OLCEK_PLAN)
        else: globals()[fn](msp)
    pafta_ekle(doc, no, NOTLAR.get(no, ""))
    if "Layout1" in doc.layouts: doc.layouts.delete("Layout1")
    doc.set_modelspace_vport(height=16000, center=(CX, CY))
    return doc


def tekil_paftalari_uret(klasor=None):
    hedef = (klasor or CAD/"paftalar"); hedef.mkdir(parents=True, exist_ok=True)
    uretilen = []
    for no in TEKIL_PAFTA:
        doc = pafta_belgesi(no)
        ad = PAFTALAR[no][0].replace(" ", "_").replace("/", "-")
        yol = hedef/f"{no}_{ad}.dxf"
        doc.saveas(yol)
        uretilen.append(yol)
        print(f"  → cad/paftalar/{yol.name:52s} "
              f"{len(list(doc.modelspace())):5d} nesne · {yol.stat().st_size/1e6:.2f} MB")
    return uretilen


def uret():
    setler = [
      ("GYM-MIM-Uygulama-R2010.dxf", False, False, ("A-01","A-02","A-03","A-04","A-05")),
      ("GYM-MEK-Uygulama-R2010.dxf", True,  False, ("M-01","M-02","M-03","M-04")),
      ("GYM-ELK-Uygulama-R2010.dxf", False, True,
       ("E-01","E-02","E-03","E-04","E-05")),
      ("GYM-BIRLESIK-R2010.dxf",     True,  True,
       ("A-01","A-02","A-03","A-04","A-05","M-01","M-02","M-03","M-04",
        "E-01","E-02","E-03","E-04","E-05")),
    ]
    uretilen = []
    for dosya, mek, elk, pf in setler:
        doc = belge_uret(dosya, mek, elk, pf)
        yol = CAD/dosya; doc.saveas(yol)
        n_ent = len(list(doc.modelspace()))
        print(f"  → cad/{dosya:32s} {n_ent:5d} nesne · {len(pf)} pafta · "
              f"{yol.stat().st_size/1e6:.2f} MB")
        uretilen.append(yol)
    uretilen += tekil_paftalari_uret()
    return uretilen


# ══════════════════════ PAFTA ÖNİZLEME PDF'İ ═══════════════════════════════════
def onizleme_pdf(cikti="output/Gym_CAD_Paftalar.pdf"):
    """Tüm paftaları tek PDF'e basar — CAD olmadan kontrol için."""
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.addons.drawing import config as _C
    import ezdxf.bbox as _bbox
    # Baskı ayarı. NOT: ABSOLUTE kalem politikası, model uzayı içeriği görüntü
    # penceresinden geçerken kalınlıkları ölçekle çarptığı için önizlemede
    # kullanılamaz (0,35 mm → 17 mm). Gerçek kalem kalınlıkları DXF içinde
    # katman ve varlık düzeyinde saklıdır; CAD'de doğru basılır. Önizleme için
    # ezdxf'in göreli politikası kullanılır.
    cfg = _C.Configuration(
        background_policy=_C.BackgroundPolicy.WHITE,
        color_policy=_C.ColorPolicy.COLOR,
        circle_approximation_count=160, hatching_timeout=90.0)
    # Her pafta KENDİ bağımsız DXF dosyasından basılır — tek model uzayı üzerinde
    # katman dondurma ile değil.
    sira = list(TEKIL_PAFTA)
    with PdfPages(cikti) as pdf:
        for no in sira:
            ad = PAFTALAR[no][0].replace(" ", "_").replace("/", "-")
            f = CAD/"paftalar"/f"{no}_{ad}.dxf"
            if not f.exists(): continue
            doc = ezdxf.readfile(f)
            lay = doc.layouts.get(f"{no} {PAFTALAR[no][0]}")
            fig = plt.figure(figsize=(PAFTA_BOYUT[0]/25.4, PAFTA_BOYUT[1]/25.4))
            ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
            Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg,
                     bbox_cache=_bbox.Cache()).draw_layout(lay, finalize=True)
            # finalize() figürü içeriğe göre yeniden boyutlar; kâğıdı geri koy
            ax.set_xlim(0, PAFTA_BOYUT[0]); ax.set_ylim(0, PAFTA_BOYUT[1])
            ax.set_aspect("equal", adjustable="box")
            fig.set_size_inches(PAFTA_BOYUT[0]/25.4, PAFTA_BOYUT[1]/25.4)
            pdf.savefig(fig, facecolor="white"); plt.close(fig)
    print(f"  → {cikti}  ·  {len(sira)} pafta (her biri ayrı DXF dosyasından)")

def paketle(cikti="output/Gym_CAD_Seti_DXF.zip"):
    n = 0
    with zipfile.ZipFile(cikti, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(CAD.rglob("*")):
            if f.is_file():
                z.write(f, f"Gym_CAD_Seti/{f.relative_to(CAD)}"); n += 1
    print(f"  → {cikti}  ·  {n} dosya · {Path(cikti).stat().st_size/1e6:.2f} MB")

# ══════════════════════ CAD OKUMA NOTU VE KATMAN LİSTESİ ═══════════════════════
def belgeler():
    import csv
    with open(CAD/"KATMAN-LISTESI.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Katman adı", "ACI renk", "Çizgi tipi", "Kalem (1/100 mm)", "Açıklama"])
        for r in X.KATMANLAR: w.writerow(r)
    bloklar = sorted(b.name for b in X.yeni_belge("x").blocks if not b.name.startswith("*")) \
              if False else None
    doc = ezdxf.readfile(CAD/"GYM-BIRLESIK-R2010.dxf")
    bl = sorted(b.name for b in doc.blocks if not b.name.startswith("*"))
    pafta_sat = "\n".join(
        f"  {no:6s} {PAFTALAR[no][0]:32s} ({PAFTALAR[no][1]})"
        for no in ["A-01","A-02","A-03","A-04","A-05","M-01","M-02","M-03","M-04",
                   "E-01","E-02","E-03","E-04"])
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
  GYM-MIM-Uygulama-R2010.dxf    Mimari — 5 pafta (altlık, uygulama, zemin kaplama,
                                tavan planı, yangın ve tahliye). Diğerlerine XREF bağlanabilir.
  GYM-MEK-Uygulama-R2010.dxf    Mekanik — 4 pafta
  GYM-ELK-Uygulama-R2010.dxf    Elektrik — 4 pafta
  GYM-BIRLESIK-R2010.dxf        Tümü — 13 pafta (tek dosyada çalışmak isteyenler için)
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
