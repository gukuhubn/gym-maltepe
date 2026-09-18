# -*- coding: utf-8 -*-
"""ADP TEK HAT ŞEMASI — CAD (DXF), kâğıt alanında 1:1.

Tek hat şeması ölçekli değildir; bu yüzden model uzayına değil, paftanın
KÂĞIT ALANINA doğrudan 1:1 milimetre olarak çizilir (ISO 5457 çerçevesi ve
antetle aynı uzayda).

Sembol geometrisi IEC 60617 modülü M = 2,5 mm üzerine kurulur. Her sembol
tek kutup anahtarı (SW_POLE) + niteleyici sembolden türer:
    ×  çarpı  → devre kesici (otomatik sigorta)
    —  çubuk  → ayırıcı (şalter)
    ⌐  kanca  → termik aşırı akım

Yerleşim kuralı (profesyonel şemayı profesyonel yapan tek kural):
    BİR ÇIKIŞ = BİR SÜTUN = BİR TABLO KOLONU.
    x_n = X0 + (n − 0,5) · ADIM   ·   ADIM = 26 mm
Bir linyeye ait her şey (sembol, dallanma, etiket, tüm tablo satırları) aynı
x ekseninde hizalıdır.

Dayanak: IEC 60617 (semboller, M = 2,5 mm), IEC 81346-2 (referans işaretleri
-Q, -F, -X, -P, -T), IEC 61439-1/-2, Elektrik İç Tesisleri Yönetmeliği md.18
(ana noktada 300 mA, son devrede 30 mA, seçicilik), TS HD 60364-5-52.
"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ezdxf.enums import TextEntityAlignment as TA
import proj as P

# ── IEC 60617 modülü ve türev sabitler ──────────────────────────────────────
M          = 2.5          # mm — IEC 60617 modülü
POLE_H     = 8*M          # 20,0 mm — tek kutup sembol yüksekliği
POLE_PITCH = 2*M          # 5,0 mm — çok kutuplu cihazda kutup aralığı
BLADE      = 4*M          # 10,0 mm — anahtar bıçağı
BLADE_ANG  = 30.0         # derece — bıçağın düşeyle açısı
DOT_R      = 0.2*M        # 0,5 mm — bağlantı noktası
TERM_R     = 0.4*M        # 1,0 mm — klemens dairesi

ADIM  = 26.0              # mm — bir çıkış sütununun genişliği
X0    = 78.0              # mm — ilk sütunun sol kenarı
BASLIK_W = 52.0           # mm — tablo satır başlığı sütunu

# düşey yerleşim (kâğıt mm, A1)
Y_BASLIK  = 566.0
Y_SAYAC   = 528.0
Y_QANA    = 494.0
Y_SPD     = 466.0
Y_BARA    = 446.0
Y_BARA_N  = 440.0
Y_BARA_PE = 434.0
Y_RCD     = 406.0
Y_ALTBARA = 386.0
Y_MCB     = 350.0
Y_SINIR   = 322.0
Y_KLEMENS = 312.0
Y_KABLO   = 302.0
Y_SUTUN_NO= 294.0
Y_MATRIS  = 288.0
TS        = 8.6           # tablo satır yüksekliği
Y_PARANTEZ_OFS = 7.0

YZ = {"mikro": 1.8, "kucuk": 2.0, "orta": 2.5, "etiket": 3.5, "baslik": 7.0}

KAT = {
 "tel":    "E-TEKHAT-TEL",
 "sembol": "E-TEKHAT-SEMBOL",
 "yazi":   "E-TEKHAT-YAZI",
 "bara":   "E-TEKHAT-BARA",
 "tablo":  "E-TEKHAT-TABLO",
 "sinir":  "E-TEKHAT-SINIR",
 "grup":   "E-TEKHAT-GRUP",
 "yedek":  "E-TEKHAT-YEDEK",
}

BORU = {1.5: "Ø16 PVC", 2.5: "Ø20 PVC", 4.0: "Ø25 PVC",
        6.0: "Ø25 PVC", 10.0: "Ø32 PVC", 16.0: "Ø40 PVC"}

# veri matrisi satırları: (başlık, veri anahtarı, çok satırlı mı)
MATRIS = [
 ("ÇIKIŞ NO",        "no"),
 ("LİNYE / TANIM",   "kod"),
 ("MAHAL · YÜK",     "tanim"),
 ("FAZ",             "faz"),
 ("KORUMA",          "koruma"),
 ("KESME KAP.",      "icn"),
 ("KAÇAK AKIM",      "rcd"),
 ("KABLO",           "kablo"),
 ("BORU / KANAL",    "boru"),
 ("UZUNLUK",         "L"),
 ("KURULU GÜÇ",      "kw"),
 ("cos φ",           "cosfi"),
 ("HESAP AKIMI Ib",  "ib"),
 ("GERİLİM DÜŞÜMÜ",  "du"),
]


# ── çizim ilkelleri (kâğıt alanı) ───────────────────────────────────────────
def _l(psp, a, b, kat="tel", lw=None):
    d = {"layer": KAT[kat]}
    if lw is not None: d["lineweight"] = lw
    return psp.add_line(a, b, dxfattribs=d)


def _pl(psp, pts, kat="sembol", kapali=False, lw=None, lt=None):
    d = {"layer": KAT[kat]}
    if lw is not None: d["lineweight"] = lw
    if lt: d["linetype"] = lt
    return psp.add_lwpolyline(pts, close=kapali, dxfattribs=d)


def _c(psp, x, y, r, kat="sembol", lw=None):
    d = {"layer": KAT[kat]}
    if lw is not None: d["lineweight"] = lw
    return psp.add_circle((x, y), r, dxfattribs=d)


def _dot(psp, x, y, r=DOT_R, kat="bara"):
    try:
        h = psp.add_hatch(color=7, dxfattribs={"layer": KAT[kat]})
        h.paths.add_edge_path().add_arc(center=(x, y), radius=r)
    except Exception:
        _c(psp, x, y, r, kat)


def _t(psp, x, y, metin, h=YZ["kucuk"], kat="yazi", hiza=TA.MIDDLE_CENTER,
       aci=0, stil="GYM"):
    e = psp.add_text(str(metin), height=h, rotation=aci,
                     dxfattribs={"layer": KAT[kat], "style": stil})
    e.set_placement((x, y), align=hiza)
    return e


# ── IEC 60617 temel eleman: tek kutup anahtarı ──────────────────────────────
def sw_pole(psp, x, y, nitelik="capraz", h=POLE_H):
    """Alt ucu (x, y)'de olan tek kutup anahtarı.

    nitelik: "capraz" devre kesici · "cubuk" ayırıcı · None sade anahtar
    """
    a = math.radians(BLADE_ANG)
    _l(psp, (x, y), (x, y+2*M), "sembol", 35)                    # alt uç
    _dot(psp, x, y+2*M, DOT_R, "sembol")                          # pivot
    _l(psp, (x, y+2*M), (x+BLADE*math.sin(a), y+2*M+BLADE*math.cos(a)),
       "sembol", 35)                                              # bıçak
    _l(psp, (x, y+6*M), (x, y+h), "sembol", 35)                   # üst uç
    if nitelik == "capraz":                                       # kesici
        _l(psp, (x-M, y+6*M-M), (x+M, y+6*M+M), "sembol", 35)
        _l(psp, (x-M, y+6*M+M), (x+M, y+6*M-M), "sembol", 35)
    elif nitelik == "cubuk":                                      # ayırıcı
        _l(psp, (x-1.2*M, y+6*M), (x+1.2*M, y+6*M), "sembol", 35)


def _mekanik_bag(psp, x, y, kutup):
    if kutup < 2: return
    _pl(psp, [(x, y+2*M), (x+(kutup-1)*POLE_PITCH, y+2*M)], "sembol",
        lw=25, lt="DASHED")


def mcb(psp, x, y, kutup=1, nitelik="capraz"):
    """Otomatik sigorta / şalter — kutuplar x ekseninde ortalanır."""
    x_sol = x - (kutup-1)*POLE_PITCH/2
    for k in range(kutup):
        sw_pole(psp, x_sol+k*POLE_PITCH, y, nitelik)
    _mekanik_bag(psp, x_sol, y, kutup)
    return x_sol


def rcd_sensor(psp, x, y, kutup, w):
    """Kaçak akım toplam akım trafosu — tüm kutupları saran elips + röle kutusu."""
    xm = x
    ry = 1.2*M
    rx = max(w/2, (kutup-1)*POLE_PITCH/2 + 1.5*M)
    try:
        psp.add_ellipse(center=(xm, y+4*M), major_axis=(rx, 0), ratio=ry/rx,
                        dxfattribs={"layer": KAT["sembol"], "lineweight": 35})
    except Exception:
        _c(psp, xm, y+4*M, rx, "sembol", 35)
    _l(psp, (xm+rx, y+4*M), (xm+rx+2.4*M, y+4*M), "sembol", 25)
    _pl(psp, [(xm+rx+2.4*M, y+4*M-1.2*M), (xm+rx+5.6*M, y+4*M-1.2*M),
              (xm+rx+5.6*M, y+4*M+1.2*M), (xm+rx+2.4*M, y+4*M+1.2*M)],
        "sembol", True, 35)
    _t(psp, xm+rx+4.0*M, y+4*M, "I∆n", YZ["kucuk"], "sembol")


def parafudr(psp, x, y):
    """Tip 2 aşırı gerilim koruma (SPD) — gövde + yön oku + PE inişi."""
    _pl(psp, [(x-1.6*M, y+1.6*M), (x+1.6*M, y+1.6*M),
              (x+1.6*M, y+4.4*M), (x-1.6*M, y+4.4*M)], "sembol", True, 35)
    _l(psp, (x, y+4.4*M), (x, y+6*M), "tel", 35)
    _l(psp, (x, y), (x, y+1.6*M), "tel", 35)
    _l(psp, (x-1.0*M, y+2.2*M), (x+1.0*M, y+3.8*M), "sembol", 35)
    _ok(psp, x+1.0*M, y+3.8*M, math.atan2(1.6*M, 2.0*M), 0.8*M)


def _ok(psp, x, y, aci, boy=2.0, ac=0.42):
    p = [(x, y),
         (x-boy*math.cos(aci-ac), y-boy*math.sin(aci-ac)),
         (x-boy*math.cos(aci+ac), y-boy*math.sin(aci+ac))]
    try:
        h = psp.add_hatch(color=7, dxfattribs={"layer": KAT["sembol"]})
        h.paths.add_polyline_path(p, is_closed=True)
    except Exception:
        _pl(psp, p, "sembol", True, 35)


def toprak(psp, x, y, koruma=False):
    _l(psp, (x, y), (x, y-2*M), "tel", 35)
    for i, w in enumerate((2*M, 1.2*M, 0.6*M)):
        _l(psp, (x-w, y-2*M-i*0.8*M), (x+w, y-2*M-i*0.8*M), "sembol", 35)
    if koruma: _c(psp, x, y-2.8*M, 2.6*M, "sembol", 25)


def sayac(psp, x, y):
    _c(psp, x, y+4*M, 2.4*M, "sembol", 35)
    _l(psp, (x, y), (x, y+1.6*M), "tel", 35)
    _l(psp, (x, y+6.4*M), (x, y+8*M), "tel", 35)
    _t(psp, x, y+4*M, "kWh", YZ["orta"], "sembol")


def klemens(psp, x, y):
    _c(psp, x, y, TERM_R, "sembol", 25)


def iletken_centik(psp, x, y, n=3, etiket=""):
    """İletken sayısı çentiği — 45°, 2M boy, 0,6M aralık."""
    for i in range(n):
        d = (i-(n-1)/2)*0.6*M
        _l(psp, (x-M+d, y-M+d), (x+M+d, y+M+d), "sembol", 25)
    if etiket:
        _t(psp, x+2.4*M, y, etiket, YZ["mikro"], "yazi", TA.MIDDLE_LEFT, 90)


def ok_ucu(psp, x, y):
    """Sahaya devam eden iletken sonu — açık ok ucu."""
    _l(psp, (x, y), (x-1.1*M, y+2.2*M), "sembol", 25)
    _l(psp, (x, y), (x+1.1*M, y+2.2*M), "sembol", 25)


# ── veri ────────────────────────────────────────────────────────────────────
def _rcd_gruplari():
    out = []
    for kod, ozellik, kapsam in P.KACAK_AKIM:
        if kod == "—": continue
        kodlar = []
        for parca in kapsam.split("—")[-1].replace(",", " ").split():
            t = parca.strip(" ·()")
            if "–" in t:
                a, b = t.split("–")
                if a[0] == b[0] and a[1:].isdigit() and b[1:].isdigit():
                    kodlar += [f"{a[0]}{i}" for i in range(int(a[1:]), int(b[1:])+1)]
                    continue
            if t and t[0] in "LPKWVZ" and any(c.isdigit() for c in t):
                kodlar.append(t)
        gecerli = [k for k in kodlar if any(l[0] == k for l in P.LINYE)]
        if gecerli: out.append((kod, ozellik, gecerli))
    return out


def _korumasiz():
    for kod, ozellik, kapsam in P.KACAK_AKIM:
        if kod == "—":
            return [t.strip(" ·()") for t in kapsam.split()
                    if t and t[0] in "LPKWVZ" and any(c.isdigit() for c in t)]
    return []


def linye_verisi():
    hesap = {r[0]: r for r in P.PANO_HESAP}
    sira, rcd_of = {}, {}
    for gi, (gkod, oz, kodlar) in enumerate(_rcd_gruplari()):
        for j, k in enumerate(kodlar):
            sira[k] = (gi, j); rcd_of[k] = (gkod, oz)
    sirali = sorted(P.LINYE, key=lambda l: sira.get(l[0], (98, 0)))
    out = []
    for i, l in enumerate(sirali):
        kod, tanim, koruma, kesit, faz, bagli, es, talep = l
        h = hesap[kod]
        mm2 = float(kesit.split("×")[1].replace(",", "."))
        g = rcd_of.get(kod)
        out.append({
            "no": str(i+1), "kod": kod,
            "tanim": tanim.split("—")[-1].strip()[:38],
            "koruma": ("MCB " if kod[0] != "W" else "MCB ") + koruma + " · C",
            "icn": "6 kA",
            "rcd": (g[1].split(",")[0] + " " + g[1].split(",")[1].strip()
                    if g else "—"),
            "rcd_kod": g[0] if g else "—",
            "kablo": ("NHXMH-J " if kod[0] != "Z" else "JE-H(St)H ") + kesit + " mm²",
            "boru": BORU.get(mm2, "Ø20 PVC"), "faz": faz,
            "ib": f"{h[6]:.1f} A".replace(".", ","),
            "L": f"{h[10]:.0f} m", "du": f"%{h[12]:.2f}".replace(".", ","),
            "kw": f"{bagli:.2f} kW".replace(".", ","),
            "cosfi": f"{h[5]:.2f}".replace(".", ","),
            "sonuc": h[14], "kutup": max(1, int(kesit.split("×")[0])-1),
            "tag": f"-Q{101+i}", "yedek": False,
        })
    n0 = len(out)
    for i in range(4):
        out.append({"no": str(n0+i+1), "kod": f"-Q{101+n0+i}", "tanim": "YEDEK",
                    "koruma": "MCB 1×16 A · C", "icn": "6 kA", "rcd": "—",
                    "rcd_kod": "—", "kablo": "YEDEK", "boru": "YEDEK",
                    "faz": "—", "ib": "—", "L": "—", "du": "—", "kw": "—",
                    "cosfi": "—", "sonuc": "YEDEK", "kutup": 1,
                    "tag": f"-Q{101+n0+i}", "yedek": True})
    return out


# ── ana çizim ───────────────────────────────────────────────────────────────
def ciz(pf):
    """Paftanın kâğıt alanına tam tek hat şemasını çizer. pf: pafta.Pafta"""
    psp = pf.psp
    veri = linye_verisi()
    n = len(veri)
    xs = [X0 + (i+0.5)*ADIM for i in range(n)]
    x_ilk, x_son = X0, X0 + n*ADIM
    idx = {d["kod"]: i for i, d in enumerate(veri)}

    _t(psp, X0, Y_BASLIK, "ADP — ANA DAĞITIM PANOSU · TEK HAT ŞEMASI",
       YZ["baslik"], "yazi", TA.MIDDLE_LEFT, stil="GYM-B")
    _t(psp, X0, Y_BASLIK-8, "IEC 60617 sembolleri · IEC 81346-2 referans işaretleri · "
       "ölçeksiz · TN-S sistem", YZ["orta"], "yazi", TA.MIDDLE_LEFT)

    # ── besleme kolu ────────────────────────────────────────────────────────
    xg = 64.0
    _t(psp, xg, Y_SAYAC+9*M+6, "ŞEBEKE / SAYAÇ PANOSU", YZ["orta"], "yazi",
       TA.MIDDLE_CENTER, stil="GYM-B")
    _l(psp, (xg, Y_SAYAC+9*M), (xg, Y_SAYAC+8*M), "tel", 35)
    sayac(psp, xg, Y_SAYAC)
    _t(psp, xg+3.2*M, Y_SAYAC+4*M, "-P1  3F kWh sayacı", YZ["kucuk"], "yazi",
       TA.MIDDLE_LEFT)
    _l(psp, (xg, Y_SAYAC), (xg, Y_QANA+POLE_H), "tel", 35)
    iletken_centik(psp, xg, (Y_SAYAC+Y_QANA+POLE_H)/2, 5,
                   f"{P.ANA_KABLO} · {P.ANA_L:.0f} m · ΔU %{P.ANA_DU_P:.2f}".replace(".", ","))
    mcb(psp, xg, Y_QANA, 4, "cubuk")
    _t(psp, xg-4.6*M, Y_QANA+4*M, "-Q1", YZ["orta"], "yazi", TA.MIDDLE_RIGHT,
       stil="GYM-B")
    _t(psp, xg+7.0*M, Y_QANA+5.2*M, f"ANA ŞALTER 4×{P.ANA_KESICI//3} A",
       YZ["kucuk"], "yazi", TA.MIDDLE_LEFT)
    _t(psp, xg+7.0*M, Y_QANA+2.6*M, P.ANA_KACAK, YZ["kucuk"], "yazi",
       TA.MIDDLE_LEFT)
    _l(psp, (xg, Y_QANA), (xg, Y_BARA), "tel", 50)
    # parafudr
    xs_spd = xg + 30
    _l(psp, (xg, Y_SPD), (xs_spd, Y_SPD), "tel", 35)
    _l(psp, (xs_spd, Y_SPD), (xs_spd, Y_SPD+6*M), "tel", 35)
    parafudr(psp, xs_spd, Y_SPD-6*M)
    toprak(psp, xs_spd, Y_SPD-6*M)
    _t(psp, xs_spd+2.4*M, Y_SPD-3*M, "-F0  SPD Tip 2", YZ["kucuk"], "yazi",
       TA.MIDDLE_LEFT)
    _t(psp, xs_spd+2.4*M, Y_SPD-5.0*M, "Up 1,4 kV · In 20 kA · Imax 40 kA",
       YZ["mikro"], "yazi", TA.MIDDLE_LEFT)
    _dot(psp, xg, Y_SPD)

    # ── bara sistemi ────────────────────────────────────────────────────────
    _pl(psp, [(x_ilk-18, Y_BARA), (x_son+10, Y_BARA)], "bara", lw=70)
    _pl(psp, [(x_ilk-18, Y_BARA_N), (x_son+10, Y_BARA_N)], "bara", lw=35)
    _pl(psp, [(x_ilk-18, Y_BARA_PE), (x_son+10, Y_BARA_PE)], "bara", lw=35)
    _t(psp, x_ilk-20, Y_BARA, "L1·L2·L3", YZ["kucuk"], "yazi", TA.MIDDLE_RIGHT,
       stil="GYM-B")
    _t(psp, x_ilk-20, Y_BARA_N, "N", YZ["kucuk"], "yazi", TA.MIDDLE_RIGHT,
       stil="GYM-B")
    _t(psp, x_ilk-20, Y_BARA_PE, "PE", YZ["kucuk"], "yazi", TA.MIDDLE_RIGHT,
       stil="GYM-B")
    toprak(psp, x_ilk-26, Y_BARA_PE, True)
    _t(psp, x_son+8, Y_BARA+7,
       f"ANA BARA  3L+N+PE  400/230 V  50 Hz  ·  Cu  ·  In {P.ANA_KESICI//3} A  ·  Icu 6 kA",
       YZ["orta"], "yazi", TA.MIDDLE_RIGHT, stil="GYM-B")

    # ── kaçak akım grupları ─────────────────────────────────────────────────
    for gi, (gkod, ozellik, kodlar) in enumerate(_rcd_gruplari()):
        sut = sorted(idx[k] for k in kodlar if k in idx)
        if not sut: continue
        xa, xb = xs[sut[0]], xs[sut[-1]]
        xm = (xa+xb)/2
        kutup = 4 if "4×" in ozellik else 2
        _l(psp, (xm, Y_BARA), (xm, Y_RCD+POLE_H), "tel", 35)
        _dot(psp, xm, Y_BARA)
        mcb(psp, xm, Y_RCD, kutup, None)
        rcd_sensor(psp, xm, Y_RCD, kutup, kutup*POLE_PITCH)
        _t(psp, xm-(kutup-1)*POLE_PITCH/2-3.0*M, Y_RCD+4*M, f"-F{gi+1}",
           YZ["orta"], "yazi", TA.MIDDLE_RIGHT, stil="GYM-B")
        _l(psp, (xm, Y_RCD), (xm, Y_ALTBARA), "tel", 35)
        # grup alt barası
        _pl(psp, [(xa-ADIM*0.36, Y_ALTBARA), (xb+ADIM*0.36, Y_ALTBARA)],
            "bara", lw=50)
        # grup parantezi — alt baranın hemen üstünde
        yb = Y_ALTBARA + 6.0
        _pl(psp, [(xa-ADIM*0.42, yb-3), (xa-ADIM*0.42, yb),
                  (xb+ADIM*0.42, yb), (xb+ADIM*0.42, yb-3)], "grup", lw=25)
        _t(psp, xm, yb+3.0, f"{gkod}  ·  {ozellik}", YZ["kucuk"], "grup")
    # kaçak akım rölesi arkasına alınmayan linyeler
    korumasiz = set(_korumasiz())
    grupta = {k for _, _, ks in _rcd_gruplari() for k in ks}
    for d in veri:
        if d["kod"] in grupta: continue
        i = idx.get(d["kod"])
        if i is None: continue
        _l(psp, (xs[i], Y_BARA), (xs[i], Y_ALTBARA), "tel", 35)
        _dot(psp, xs[i], Y_BARA)
        if d["kod"] in korumasiz:
            _t(psp, xs[i]+3.2, (Y_BARA+Y_ALTBARA)/2,
               "KAÇAK AKIM RÖLESİ ARKASINA ALINMAZ", YZ["mikro"], "yazi",
               TA.MIDDLE_LEFT, 90)

    # ── çıkış kesicileri ────────────────────────────────────────────────────
    for i, d in enumerate(veri):
        x = xs[i]
        _l(psp, (x, Y_ALTBARA), (x, Y_MCB+POLE_H), "tel", 35)
        _dot(psp, x, Y_ALTBARA)
        mcb(psp, x, Y_MCB, d["kutup"], "capraz")
        _t(psp, x+2.6*M, Y_MCB+6.6*M, d["tag"], YZ["kucuk"], "yazi",
           TA.MIDDLE_LEFT, stil="GYM-B")
        _t(psp, x+2.6*M, Y_MCB+3.4*M, d["koruma"].replace("MCB ", ""),
           YZ["mikro"], "yazi", TA.MIDDLE_LEFT)
        if d["yedek"]:
            _l(psp, (x, Y_MCB), (x, Y_MCB-8), "tel", 35)
            _l(psp, (x-2.5, Y_MCB-8), (x+2.5, Y_MCB-8), "sembol", 35)
            _t(psp, x, Y_MCB-13, "YEDEK", YZ["mikro"], "yazi")
            continue
        _l(psp, (x, Y_MCB), (x, Y_KLEMENS), "tel", 35)
        klemens(psp, x, Y_KLEMENS)
        _l(psp, (x, Y_KLEMENS-TERM_R), (x, Y_KABLO-6), "tel", 35)
        iletken_centik(psp, x, Y_KABLO, d["kutup"]+1, "")
        ok_ucu(psp, x, Y_KABLO-8)

    # ── pano sınırı ─────────────────────────────────────────────────────────
    _pl(psp, [(x_ilk-34, Y_SINIR), (x_ilk-34, Y_QANA+POLE_H+14),
              (x_son+16, Y_QANA+POLE_H+14), (x_son+16, Y_SINIR)],
        "sinir", False, 35, "DASHDOT")
    _pl(psp, [(x_ilk-34, Y_SINIR), (x_son+16, Y_SINIR)], "sinir", False, 35,
        "DASHDOT")
    _t(psp, x_ilk-32, Y_SINIR+4,
       "PANO: ADP · IP54 · Form 2b · sac gövde · Icw 6 kA 1 s  —  ÜSTÜ PANO İÇİ, "
       "ALTI SAHA KABLOLAMASI", YZ["kucuk"], "yazi", TA.MIDDLE_LEFT,
       stil="GYM-B")
    _t(psp, x_ilk-32, Y_KLEMENS, "-X1", YZ["orta"], "yazi", TA.MIDDLE_RIGHT,
       stil="GYM-B")
    _t(psp, x_ilk-30, Y_KLEMENS, "klemens sırası", YZ["mikro"], "yazi",
       TA.MIDDLE_LEFT)

    # ── sütun no şeridi + veri matrisi ──────────────────────────────────────
    ust = Y_SUTUN_NO
    alt = ust - len(MATRIS)*TS
    xl = X0 - BASLIK_W
    _pl(psp, [(xl, alt), (x_son, alt), (x_son, ust), (xl, ust)], "tablo",
        True, 50)
    for r in range(len(MATRIS)+1):
        y = ust - r*TS
        _pl(psp, [(xl, y), (x_son, y)], "tablo", lw=18)
    _pl(psp, [(X0, alt), (X0, ust)], "tablo", lw=50)
    for i in range(1, n):
        _pl(psp, [(X0+i*ADIM, alt), (X0+i*ADIM, ust)], "tablo", lw=18)
    for r, (baslik, anahtar) in enumerate(MATRIS):
        y = ust - (r+0.5)*TS
        _t(psp, xl+2, y, baslik, YZ["kucuk"], "tablo", TA.MIDDLE_LEFT,
           stil="GYM-B")
        for i, d in enumerate(veri):
            _hucre(psp, xs[i], y, str(d[anahtar]))
    return alt


def _hucre(psp, x, y, v, gen=ADIM-2.4):
    """Hücre metni: kısa ise tek satır, uzun ise iki satır yatay.
    Dikey yazı kullanılmaz — satır yüksekliğini aşıp komşu satıra taşar."""
    if len(v) <= 12:
        _t(psp, x, y, v, YZ["mikro"], "tablo"); return
    satirlar = _sar(v, max(10, int(gen/1.05)))[:2]
    if len(satirlar) == 1:
        _t(psp, x, y, satirlar[0], 1.5, "tablo"); return
    _t(psp, x, y+1.9, satirlar[0], 1.5, "tablo")
    _t(psp, x, y-1.9, satirlar[1], 1.5, "tablo")


def alt_bloklar(pf, alt_y):
    """Şemanın altına not, faz dengesi, güç özeti ve hesap tabloları."""
    psp = pf.psp
    y0 = alt_y - 12
    xl = X0 - BASLIK_W
    sag_sinir = pf.ax - 8
    gen = (sag_sinir - xl)/4 - 5

    def blok(x, baslik, satirlar, w):
        _t(psp, x, y0, baslik, YZ["orta"], "yazi", TA.MIDDLE_LEFT, stil="GYM-B")
        _pl(psp, [(x, y0-3), (x+w, y0-3)], "tablo", lw=35)
        y = y0-8
        for k, v in satirlar:
            _t(psp, x, y, k, YZ["kucuk"], "tablo", TA.MIDDLE_LEFT)
            _t(psp, x+w-1, y, v, YZ["kucuk"], "tablo", TA.MIDDLE_RIGHT)
            y -= 5.2
        return y

    _v = lambda x, n=2: f"{x:.{n}f}".replace(".", ",")
    blok(xl, "FAZ DENGESİ", [
        ("L1 bağlı güç", f"{_v(P.FAZ_YUK['L1'])} kW"),
        ("L2 bağlı güç", f"{_v(P.FAZ_YUK['L2'])} kW"),
        ("L3 bağlı güç", f"{_v(P.FAZ_YUK['L3'])} kW"),
        ("L1 / L2 / L3 akımı", " / ".join(f"{P.AKIM_FAZ[f]:.0f}" for f in
                                          ("L1", "L2", "L3")) + " A"),
        ("Dengesizlik", f"%{_v(P.FAZ_DENGE,1)}"),
        ("Sınır (pratik)", "%15"),
    ], gen)
    blok(xl+gen+5, "GÜÇ ÖZETİ", [
        ("Kurulu (bağlı) güç", f"{_v(P.BAGLI_KW)} kW"),
        ("Eşzamanlılık sonrası talep", f"{_v(P.TALEP_KW_E)} kW"),
        ("Tasarım talep gücü", f"{_v(P.TALEP_KW)} kW"),
        ("Ana besleme akımı Ib", f"{_v(P.ANA_IB,1)} A"),
        ("Ana kesici In", f"4×{P.ANA_KESICI//3} A"),
        ("Linye sayısı", f"{len(P.LINYE)} + 4 yedek"),
    ], gen)
    blok(xl+2*(gen+5), "HESAPLAR", [
        ("Ana besleme kesiti", P.ANA_KABLO),
        ("Ana besleme ΔU", f"%{_v(P.ANA_DU_P)}"),
        ("En yüksek son devre ΔU", f"%{_v(P.DU_MAX)} ({P.DU_MAX_LINYE})"),
        ("Toplam ΔU (en uzak tüketici)", f"%{_v(P.TOPLAM_DU_MAX)}"),
        ("Sınır — TS HD 60364-5-52", "%5"),
        ("Uygunsuz linye", f"{len(P.PANO_UYGUNSUZ)} adet"),
    ], gen)
    notlar = [
        "Sistem TN-S; sayaç sonrası N ve PE ayrı çekilir, panoda birleştirilmez.",
        "Ana girişte 300 mA S tipi seçici kaçak akım rölesi, son devrelerde "
        "30 mA A tipi koruma (Elektrik İç Tesisleri Yön. md.18).",
        "Kesici anma akımları kaynaktan yüke doğru azalır — seçicilik sağlanmıştır.",
        "Yangın algılama paneli (Z2) kaçak akım rölesi arkasına alınmaz; "
        "kendi aküsüyle 60 dakika beslenir.",
        "Tüm kesiciler C eğrili, Icn 6 kA. Pano IEC 61439-1/-2'ye göre "
        "tip testli tasarımdan türetilmiştir.",
        "Kablo kesitleri ısınma (Iz) ve gerilim düşümü koşullarının ikisini "
        "birden sağlar; hesap tablosu paftada verilmiştir.",
        "Pano üzerinde kalıcı tek hat şeması ve linye etiketleri bulunacaktır.",
    ]
    x = xl+3*(gen+5)
    _t(psp, x, y0, "GENEL NOTLAR", YZ["orta"], "yazi", TA.MIDDLE_LEFT,
       stil="GYM-B")
    _pl(psp, [(x, y0-3), (x+gen, y0-3)], "tablo", lw=35)
    y = y0-8
    for i, t in enumerate(notlar, 1):
        for j, par in enumerate(_sar(t, int(gen/1.15))):
            _t(psp, x, y, (f"{i}. " if j == 0 else "   ")+par, YZ["mikro"],
               "tablo", TA.MIDDLE_LEFT)
            y -= 3.6
        y -= 1.2


def _sar(metin, n):
    out, satir = [], ""
    for k in str(metin).split():
        if len(satir)+len(k)+1 > n:
            out.append(satir); satir = k
        else:
            satir = (satir+" "+k).strip()
    if satir: out.append(satir)
    return out or [""]
