# -*- coding: utf-8 -*-
"""ADP ÇOK HATLI (MULTI-LINE) ŞEMA MOTORU — EPLAN düzeninde, A3, kâğıt alanı 1:1.

NEDEN ÇOK HATLI?
----------------
Türkiye'de pano dokümantasyonunun fiilî standardı, tek hat şeması değil
**çok hatlı şematik diyagramdır**: L1 · L2 · L3 · N potansiyel rayları sayfanın
üstünde AYRI AYRI çizilir, her linye kendi fazından bir bağlantı noktasıyla
(dolu nokta) ayrılır. Böylece hangi linyenin hangi fazda olduğu çizimden
doğrudan okunur — tek hat şemasında okunmaz.

Sayfa düzeni (referans pano projesiyle birebir):
    · üstte 0–7 sütun numaraları, iki yanda A–F satır harfleri
    · üstte L1/L2/L3/N potansiyel rayları, solda ve sağda sayfalar arası
      referans (`2.7 >` ... `> 5.0` biçiminde: sayfa.sütun)
    · altta PE rayı (noktalı-kesik çizgi)
    · her sütunda: koruma cihazı (terminal numaralı) → tel numarası →
      klemens -X1 → kablo etiketi → yük bloğu → cihaz etiketi ve Türkçe tanım
    · altta EPLAN antedi (çift dilli)

Dayanak: IEC 60617 (semboller), IEC 81346-2 (referans işaretleri),
IEC 61439-1&2 (pano), EN 60204-1 (tel numaralandırma).
"""
import math, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ezdxf.enums import TextEntityAlignment as TA
import proj as P

# ── sayfa geometrisi (A3 420×297, ISO 5457) ─────────────────────────────────
W, H      = 420.0, 297.0
FX0, FY0  = 20.0, 10.0          # çizim çerçevesi sol-alt
FX1, FY1  = 410.0, 287.0        # çizim çerçevesi sağ-üst
ZON       = 5.0                 # kenar ızgarası bant genişliği
ANTET_H   = 22.0                # antet yüksekliği (tam genişlik şerit)
SUTUN     = 8                   # sayfa başına sütun (EPLAN A3 standardı)

DX0 = FX0 + ZON                 # çizim alanı sol
DX1 = FX1 - ZON                 # çizim alanı sağ
DY0 = FY0 + ANTET_H             # çizim alanı alt
DY1 = FY1 - ZON                 # çizim alanı üst
SW  = (DX1 - DX0) / SUTUN       # sütun genişliği ≈ 47,5 mm

# düşey kotlar (mm)
Y_L1, Y_L2, Y_L3, Y_N = 272.0, 267.0, 262.0, 257.0
Y_RCD_UST  = 250.0
Y_RCD_ALT  = 234.0
Y_MCB_UST  = 218.0
Y_MCB_ALT  = 206.0
Y_ARA_UST  = 198.0              # ara cihaz (anahtar/kontaktör) üstü
Y_ARA_ALT  = 188.0
Y_PE       = 150.0
Y_KLEMENS  = 140.0
Y_KABLO    = 131.0
Y_YUK_UST  = 124.0
Y_YUK_ALT  = 110.0
Y_TAG      = 103.0
Y_TANIM    = 97.0

YZ = {"mikro": 1.5, "kucuk": 1.8, "orta": 2.2, "etiket": 2.8, "baslik": 4.0}

KAT = {"tel": "E-SEMA-TEL", "sembol": "E-SEMA-SEMBOL", "yazi": "E-SEMA-YAZI",
       "ray": "E-SEMA-RAY", "pe": "E-SEMA-PE", "antet": "E-SEMA-ANTET",
       "zon": "E-SEMA-ZON", "yuk": "E-SEMA-YUK", "klemens": "E-SEMA-KLEMENS"}

RAY = [("L1", Y_L1), ("L2", Y_L2), ("L3", Y_L3), ("N", Y_N)]


# ── ilkeller ────────────────────────────────────────────────────────────────
def _l(psp, a, b, kat="tel", lw=None, lt=None):
    d = {"layer": KAT[kat]}
    if lw is not None: d["lineweight"] = lw
    if lt: d["linetype"] = lt
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


def _dot(psp, x, y, r=0.55):
    try:
        h = psp.add_hatch(color=7, dxfattribs={"layer": KAT["sembol"]})
        h.paths.add_edge_path().add_arc(center=(x, y), radius=r)
    except Exception:
        _c(psp, x, y, r, "sembol")


def _t(psp, x, y, metin, h=YZ["kucuk"], kat="yazi", hiza=TA.MIDDLE_CENTER,
       aci=0, stil="GYM"):
    e = psp.add_text(str(metin), height=h, rotation=aci,
                     dxfattribs={"layer": KAT[kat], "style": stil})
    e.set_placement((x, y), align=hiza)
    return e


# ── IEC sembolleri (terminal numaralı — referans projedeki biçim) ───────────
def kesici_kutbu(psp, x, y_ust, y_alt, kapali=False):
    """Tek kutup kesici: üst terminal → pivot → eğik bıçak → alt terminal."""
    gov = (y_ust - y_alt)
    _l(psp, (x, y_ust), (x, y_ust-gov*0.22), "tel", 25)
    _dot(psp, x, y_ust-gov*0.22, 0.35)
    _l(psp, (x, y_ust-gov*0.22), (x+gov*0.30, y_alt+gov*0.20), "sembol", 35)
    _l(psp, (x, y_alt+gov*0.16), (x, y_alt), "tel", 25)
    # açtırma niteliği: termik-manyetik (dikdörtgen + çapraz)
    _pl(psp, [(x+0.9, y_alt+gov*0.16), (x+2.3, y_alt+gov*0.16),
              (x+2.3, y_alt+gov*0.46), (x+0.9, y_alt+gov*0.46)],
        "sembol", True, 25)


def mcb(psp, x, kutup=1, tag="", satir1="", satir2="", satir3=""):
    """Otomatik sigorta — referans yazım biçimi:
        -F1
        16A
        1P C
        6kA
    """
    for k in range(kutup):
        kesici_kutbu(psp, x+k*4.0, Y_MCB_UST, Y_MCB_ALT)
    if kutup > 1:
        _l(psp, (x, Y_MCB_UST-2.6), (x+(kutup-1)*4.0, Y_MCB_UST-2.6),
           "sembol", 18, "DASHED")
    _t(psp, x-1.2, Y_MCB_UST-0.6, "1", YZ["mikro"], "yazi", TA.MIDDLE_RIGHT)
    _t(psp, x+3.1, Y_MCB_ALT+2.0, "2", YZ["mikro"], "yazi", TA.MIDDLE_LEFT)
    yy = Y_MCB_UST - 0.4
    if tag:
        _t(psp, x-3.4, yy, tag, YZ["orta"], "yazi", TA.MIDDLE_RIGHT)
        yy -= 2.6
    for s in (satir1, satir2, satir3):
        if s:
            _t(psp, x-3.4, yy, s, YZ["mikro"], "yazi", TA.MIDDLE_RIGHT)
            yy -= 2.0


def rcd(psp, x, kutup=4, tag="-ID1", satir1="4×40 A", satir2="30 mA",
        gec=False):
    """Kaçak akım rölesi — referans biçim: üstte 1/3/5/N, altta 2/4/6/N
    terminalleri, altında toplam akım trafosu gövdesi ve toprak sembolü,
    solda test butonu."""
    n = kutup
    gen = (n-1)*4.0
    for k in range(n):
        kesici_kutbu(psp, x+k*4.0, Y_RCD_UST, Y_RCD_UST-8.0)
    _l(psp, (x, Y_RCD_UST-5.4), (x+gen, Y_RCD_UST-5.4), "sembol", 18, "DASHED")
    # terminal numaraları
    ust = ["1", "3", "5", "N"][:n] if n == 4 else ["1", "N"][:n]
    alt = ["2", "4", "6", "N"][:n] if n == 4 else ["2", "N"][:n]
    for k, (u, a) in enumerate(zip(ust, alt)):
        _t(psp, x+k*4.0-1.1, Y_RCD_UST-0.8, u, YZ["mikro"], "yazi",
           TA.MIDDLE_RIGHT)
        _t(psp, x+k*4.0-1.1, Y_RCD_ALT+1.2, a, YZ["mikro"], "yazi",
           TA.MIDDLE_RIGHT)
    # gövde
    _pl(psp, [(x-2.6, Y_RCD_ALT), (x+gen+2.6, Y_RCD_ALT),
              (x+gen+2.6, Y_RCD_ALT+5.0), (x-2.6, Y_RCD_ALT+5.0)],
        "sembol", True, 35)
    _t(psp, x+gen/2-1.6, Y_RCD_ALT+2.5, "I", YZ["orta"], "sembol")
    # toprak sembolü gövde içinde
    ex = x+gen/2+1.6
    _l(psp, (ex, Y_RCD_ALT+3.4), (ex, Y_RCD_ALT+2.4), "sembol", 25)
    for i, w in enumerate((1.1, 0.7, 0.35)):
        _l(psp, (ex-w, Y_RCD_ALT+2.4-i*0.45), (ex+w, Y_RCD_ALT+2.4-i*0.45),
           "sembol", 25)
    for k in range(n):
        _l(psp, (x+k*4.0, Y_RCD_ALT), (x+k*4.0, Y_RCD_ALT-1.6), "tel", 25)
    # test butonu
    _pl(psp, [(x-9.0, Y_RCD_UST-3.4), (x-6.0, Y_RCD_UST-3.4),
              (x-6.0, Y_RCD_UST-0.4), (x-9.0, Y_RCD_UST-0.4)],
        "sembol", True, 25)
    _l(psp, (x-9.0, Y_RCD_UST-3.4), (x-6.0, Y_RCD_UST-0.4), "sembol", 18)
    _l(psp, (x-11.0, Y_RCD_UST-1.9), (x-9.0, Y_RCD_UST-1.9), "tel", 25)
    _l(psp, (x-6.0, Y_RCD_UST-1.9), (x, Y_RCD_UST-1.9), "tel", 25)
    yy = Y_RCD_ALT + 3.4
    _t(psp, x-12.5, yy, tag, YZ["orta"], "yazi", TA.MIDDLE_RIGHT)
    for s in (satir1, satir2, "S tipi" if gec else ""):
        if s:
            yy -= 2.2
            _t(psp, x-12.5, yy, s, YZ["mikro"], "yazi", TA.MIDDLE_RIGHT)


def salter(psp, x, kutup=4, tag="-Q1", satir1="4×32 A"):
    """Ana şalter / yük ayırıcı — bıçaklı, niteliksiz."""
    for k in range(kutup):
        gov = Y_RCD_UST - (Y_RCD_UST-10.0)
        xx = x+k*4.0
        _l(psp, (xx, Y_L1+4.0), (xx, Y_L1+1.2), "tel", 25)
    return


def klemens(psp, x, no="", pot=""):
    _c(psp, x, Y_KLEMENS, 0.8, "klemens", 25)
    if no:  _t(psp, x-1.6, Y_KLEMENS+2.2, no, YZ["mikro"], "yazi", TA.MIDDLE_RIGHT)
    if pot: _t(psp, x+1.6, Y_KLEMENS+2.2, pot, YZ["mikro"], "yazi", TA.MIDDLE_LEFT)


def yuk_blogu(psp, x, damar=("L", "N", "PE"), etiket="", tanim=()):
    """Saha cihazı — kesikli kutu içinde damar klemensleri (referans biçim)."""
    gen = 3.4*len(damar) + 2.0
    x0 = x - gen/2
    _pl(psp, [(x0, Y_YUK_ALT), (x0+gen, Y_YUK_ALT), (x0+gen, Y_YUK_UST),
              (x0, Y_YUK_UST)], "yuk", True, 18, "DASHED")
    for i, d in enumerate(damar):
        cx = x0 + 1.0 + 3.4*i + 1.7
        _pl(psp, [(cx-0.8, Y_YUK_ALT+1.4), (cx+0.8, Y_YUK_ALT+1.4),
                  (cx+0.8, Y_YUK_UST-1.4), (cx-0.8, Y_YUK_UST-1.4)],
            "yuk", True, 18)
        _t(psp, cx, Y_YUK_UST-0.5, d, YZ["mikro"], "yuk")
    if etiket:
        _t(psp, x, Y_TAG, etiket, YZ["etiket"], "yazi", stil="GYM-B")
    y = Y_TANIM
    for t in tanim:
        _t(psp, x, y, t, YZ["kucuk"], "yazi"); y -= 2.6


def tel_no(psp, x, y1, y2, no):
    """Tel numarası — iletkenin soluna, 90° döndürülmüş (EN 60204-1)."""
    _t(psp, x-1.4, (y1+y2)/2, str(no), YZ["mikro"], "yazi",
       TA.MIDDLE_CENTER, 90)


def potansiyel_adi(psp, x, y, ad):
    _t(psp, x+1.4, y+1.4, ad, YZ["mikro"], "yazi", TA.MIDDLE_LEFT)


# ── sayfa çerçevesi ve antedi ───────────────────────────────────────────────
def sayfa_cercevesi(psp):
    _pl(psp, [(FX0, FY0), (FX1, FY0), (FX1, FY1), (FX0, FY1)],
        "antet", True, 70)
    _pl(psp, [(DX0, DY0), (DX1, DY0), (DX1, DY1), (DX0, DY1)],
        "zon", True, 18)
    # sütun numaraları (üstte ve altta)
    for i in range(SUTUN):
        xa = DX0 + i*SW
        if i:
            _l(psp, (xa, DY1), (xa, FY1), "zon", 18)
            _l(psp, (xa, FY0+ANTET_H), (xa, DY0), "zon", 18)
        _t(psp, xa+SW/2, FY1-ZON/2, i, YZ["orta"], "zon")
    # satır harfleri (solda ve sağda)
    harf = "ABCDEF"
    ny = len(harf)
    ady = (DY1-DY0)/ny
    for j, hf in enumerate(harf):
        ya = DY1 - (j+1)*ady
        if j:
            _l(psp, (FX0, ya+ady), (DX0, ya+ady), "zon", 18)
            _l(psp, (DX1, ya+ady), (FX1, ya+ady), "zon", 18)
        for xx in (FX0+ZON/2, FX1-ZON/2):
            _t(psp, xx, ya+ady/2, hf, YZ["orta"], "zon")


def antet(psp, sayfa, sonraki, toplam, aciklama, proje):
    """EPLAN tarzı çift dilli antet — tam genişlik alt şerit, 4 satır."""
    x0, y0, w, h = FX0, FY0, FX1-FX0, ANTET_H
    sh = h/4.0
    _pl(psp, [(x0, y0), (x0+w, y0), (x0+w, y0+h), (x0, y0+h)],
        "antet", True, 50)
    for i in range(1, 4):
        _l(psp, (x0, y0+i*sh), (x0+w, y0+i*sh), "antet", 18)
    kol = [0.0, 44.0, 76.0, 262.0, 296.0, 336.0, w]
    for k in kol[1:-1]:
        _l(psp, (x0+k, y0), (x0+k, y0+h), "antet", 18)

    def et(k_i, satir, tr, en):
        xa = x0 + kol[k_i] + 0.8
        ya = y0 + (5-satir)*sh
        _t(psp, xa, ya-1.8, tr, YZ["mikro"], "antet", TA.MIDDLE_LEFT)
        _t(psp, xa, ya-3.7, en, YZ["mikro"], "antet", TA.MIDDLE_LEFT)

    def dg(k_i, satir, v, dh=YZ["orta"], kalin=False):
        ya = y0 + (4.5-satir)*sh
        _t(psp, x0+kol[k_i]+1.2, ya, v, dh, "antet", TA.MIDDLE_LEFT,
           stil="GYM-B" if kalin else "GYM")

    # 1. sütun: çizen / kontrol / onay / tarih
    for i, (tr, en, key) in enumerate((
            ("Drawn By /", "Çizen", "cizen"),
            ("Checked By /", "Kontrol Eden", "kontrol"),
            ("Approved By /", "Onaylayan", "onay"),
            ("Project Date /", "Proje Tarihi", "tarih")), 1):
        et(0, i, tr, en)
        _t(psp, x0+kol[1]-1.6, y0+(4.5-i)*sh, proje.get(key, "—"),
           YZ["kucuk"], "antet", TA.MIDDLE_RIGHT)
    # 2. sütun etiketleri + 3. sütun değerleri
    for i, (tr, en, v) in enumerate((
            ("Customer Name /", "Müşteri Adı", proje.get("musteri", "")),
            ("Project Description /", "Proje Açıklaması",
             proje.get("aciklama", "")),
            ("Panel Name /", "Pano Adı", proje.get("pano", "ADP")),
            ("Page Description /", "Sayfa Açıklaması", aciklama)), 1):
        et(1, i, tr, en); dg(2, i, v)
    # 4. sütun: proje numarası (2 satır yüksekliğinde)
    et(3, 1, "Project Number /", "Proje Numarası")
    _t(psp, x0+kol[4]+1.2, y0+3.5*sh, proje.get("no", ""), YZ["etiket"],
       "antet", TA.MIDDLE_LEFT, stil="GYM-B")
    et(3, 3, "Revision /", "Revizyon")
    _t(psp, x0+kol[4]+1.2, y0+1.5*sh, proje.get("rev", ""), YZ["orta"],
       "antet", TA.MIDDLE_LEFT)
    et(3, 4, "Standards /", "Standartlar")
    _t(psp, x0+kol[4]+1.2, y0+0.5*sh, "IEC 61439-1&2 · IEC 60617",
       YZ["mikro"], "antet", TA.MIDDLE_LEFT)
    # 5. sütun: sayfa bilgisi
    for i, (tr, en, dv) in enumerate((("Sheet: /", "Sayfa", sayfa),
                                      ("Next sheet: /", "Sonraki", sonraki),
                                      ("Total sheets: /", "Toplam", toplam),
                                      ("Sheet size /", "Kâğıt", "A3")), 1):
        ya = y0 + (4.5-i)*sh
        _t(psp, x0+kol[5]+1.2, ya+1.0, tr, YZ["mikro"], "antet", TA.MIDDLE_LEFT)
        _t(psp, x0+kol[5]+1.2, ya-1.4, en, YZ["mikro"], "antet", TA.MIDDLE_LEFT)
        _t(psp, x0+w-2.0, ya, dv, YZ["etiket"], "antet", TA.MIDDLE_RIGHT,
           stil="GYM-B")


def raylar(psp, sayfa_no, onceki_ref, sonraki_ref, pe=True):
    """Potansiyel rayları + sayfalar arası referanslar."""
    for ad, y in RAY:
        _l(psp, (DX0, y), (DX1, y), "ray", 35)
        _t(psp, DX0-0.6, y+1.4, ad, YZ["kucuk"], "yazi", TA.MIDDLE_LEFT)
        _t(psp, DX1-0.6, y+1.4, ad, YZ["kucuk"], "yazi", TA.MIDDLE_RIGHT)
        # referans okları
        _pl(psp, [(DX0-6.0, y-1.3), (DX0-2.2, y-1.3), (DX0-0.6, y),
                  (DX0-2.2, y+1.3), (DX0-6.0, y+1.3)], "yazi", True, 18)
        _t(psp, DX0-7.0, y, onceki_ref, YZ["mikro"], "yazi", TA.MIDDLE_RIGHT)
        _pl(psp, [(DX1+0.6, y-1.3), (DX1+4.4, y-1.3), (DX1+6.0, y),
                  (DX1+4.4, y+1.3), (DX1+0.6, y+1.3)], "yazi", True, 18)
        _t(psp, DX1+7.0, y, sonraki_ref, YZ["mikro"], "yazi", TA.MIDDLE_LEFT)
    if pe:
        _l(psp, (DX0, Y_PE), (DX1, Y_PE), "pe", 35, "DASHDOT")
        _t(psp, DX0-0.6, Y_PE+1.4, "PE", YZ["kucuk"], "yazi", TA.MIDDLE_LEFT)
        _t(psp, DX1-0.6, Y_PE+1.4, "PE", YZ["kucuk"], "yazi", TA.MIDDLE_RIGHT)
        _t(psp, DX0-7.0, Y_PE, onceki_ref, YZ["mikro"], "yazi", TA.MIDDLE_RIGHT)
        _t(psp, DX1+7.0, Y_PE, sonraki_ref, YZ["mikro"], "yazi", TA.MIDDLE_LEFT)


def sutun_x(i):
    """i. sütunun cihaz ekseni."""
    return DX0 + i*SW + 14.0


# ══════════════════════ VERİ ════════════════════════════════════════════════
BORU = {1.5: "Ø16", 2.5: "Ø20", 4.0: "Ø25", 6.0: "Ø25", 10.0: "Ø32"}


def rcd_gruplari():
    """[(kod, özellik, [linye kodları], açıklama)] — yedekler dâhil."""
    out = []
    for kod, ozellik, kapsam in P.KACAK_AKIM:
        if kod == "—": continue
        govde = kapsam.split("—")[-1]
        kodlar = []
        for parca in govde.replace(",", " ").split():
            t = parca.strip(" ·()")
            if "–" in t:
                a, b = t.split("–")
                if a[:1] == b[:1] and a[1:].isdigit() and b[1:].isdigit():
                    kodlar += [f"{a[0]}{i}" for i in range(int(a[1:]), int(b[1:])+1)]
                    continue
            if t and t[0] in "LPKWVZY" and any(c.isdigit() for c in t):
                kodlar.append(t)
        out.append((kod, ozellik, kodlar, kapsam.split("—")[0].strip()))
    return out


def korumasiz_linyeler():
    for kod, ozellik, kapsam in P.KACAK_AKIM:
        if kod == "—":
            return [t.strip(" ·()") for t in kapsam.split()
                    if t and t[0] in "LPKWVZ" and any(c.isdigit() for c in t)]
    return []


def linye_kayitlari():
    """Şemanın her sütunu için tam kayıt — RCD grubuna göre sıralı."""
    hesap = {r[0]: r for r in P.PANO_HESAP}
    lin = {l[0]: l for l in P.LINYE}
    yedek_faz = ("L1", "L2", "L3", "L1")
    kayit, tel, klem = [], 11, 1
    fno, no = 1, 1
    for gi, (gkod, gozel, kodlar, gad) in enumerate(rcd_gruplari(), 1):
        for k in kodlar:
            if k in lin:
                kod, tanim, koruma, kesit, faz, bagli, es, talep = lin[k]
                h = hesap[kod]
                mm2 = float(kesit.split("×")[1].replace(",", "."))
                kutup = max(1, int(kesit.split("×")[0])-1)
                kayit.append(dict(
                    no=no, kod=kod, tag=f"-F{fno}", faz=faz, kutup=kutup,
                    amper=koruma.split("×")[1].split()[0],
                    egri=P.kesici_egrisi(kod), kesme=P.KESME_KAP,
                    kablo=("NHXMH" if kod[0] != "Z" else "JE-H(St)H"),
                    kesit=kesit, boru=BORU.get(mm2, "Ø20"),
                    kw=bagli, ib=h[6], L=h[10], du=h[12], cosfi=h[5],
                    tanim=tanim, rcd=gkod, rcd_ozel=gozel, rcd_ad=gad,
                    rcd_no=gi, yedek=False, tel=tel, klem=klem,
                    sonuc=h[14]))
                tel += 1; klem += 1; fno += 1; no += 1
            elif k.startswith("Y"):
                i = int(k[1:])-1
                kayit.append(dict(
                    no=no, kod=k, tag=f"-F{fno}", faz=yedek_faz[i % 4],
                    kutup=1, amper="16", egri="C", kesme=P.KESME_KAP,
                    kablo="—", kesit="—", boru="—", kw=0.0, ib=0.0, L=0,
                    du=0.0, cosfi=0.0, tanim="YEDEK — ileride yük bağlanacak",
                    rcd=gkod, rcd_ozel=gozel, rcd_ad=gad, rcd_no=gi,
                    yedek=True, tel=tel, klem=klem, sonuc="YEDEK"))
                tel += 1; klem += 1; fno += 1; no += 1
    # kaçak akım rölesi arkasına ALINMAYAN linyeler (yangın algılama paneli)
    for k in korumasiz_linyeler():
        if k not in lin: continue
        kod, tanim, koruma, kesit, faz, bagli, es, talep = lin[k]
        h = hesap[kod]
        mm2 = float(kesit.split("×")[1].replace(",", "."))
        kayit.append(dict(
            no=no, kod=kod, tag=f"-F{fno}", faz=faz,
            kutup=max(1, int(kesit.split("×")[0])-1),
            amper=koruma.split("×")[1].split()[0], egri=P.kesici_egrisi(kod),
            kesme=P.KESME_KAP, kablo="JE-H(St)H", kesit=kesit,
            boru=BORU.get(mm2, "Ø20"), kw=bagli, ib=h[6], L=h[10], du=h[12],
            cosfi=h[5], tanim=tanim, rcd="—",
            rcd_ozel="Kaçak akım rölesi arkasına alınmaz",
            rcd_ad="Kesintisiz besleme", rcd_no=0, yedek=False,
            tel=tel, klem=klem, sonuc=h[14]))
        tel += 1; klem += 1; fno += 1; no += 1
    return kayit


# ══════════════════════ SAYFALAR ════════════════════════════════════════════
def _ref(sayfa, sutun=0): return f"{sayfa}.{sutun}"


def sematik_sayfa(psp, kayitlar, sayfa, onceki, sonraki):
    """Bir şematik sayfa: en çok 8 linye.

    Kaçak akım rölesi grubun İLK sütununda çizilir; kutup sayısı röle
    özelliğinden gelir (4× → 4 kutup, 2× → 2 kutup). Rölenin altında grup
    alt rayları vardır: 4 kutuplu rölede L1/L2/L3/N, 2 kutuplu rölede
    faz + N. Her linye KENDİ fazından dallanır — böylece hangi linyenin
    hangi fazda olduğu çizimden okunur.
    """
    raylar(psp, sayfa, onceki, sonraki)
    ray_y = {"L1": Y_L1, "L2": Y_L2, "L3": Y_L3}
    grup_ilk, grup_alt = {}, {}
    for k in kayitlar:
        grup_ilk.setdefault(k["rcd"], k)

    # ── 1) grup röleleri ve alt rayları ─────────────────────────────────────
    for gkod, ilk in grup_ilk.items():
        if gkod == "—": continue
        i = kayitlar.index(ilk)
        x = sutun_x(i)
        dort = "4×" in ilk["rcd_ozel"]
        n = 4 if dort else 2
        # röle girişleri: 4 kutupluda L1,L2,L3,N — 2 kutupluda faz,N
        giris = [("L1", Y_L1), ("L2", Y_L2), ("L3", Y_L3), ("N", Y_N)] if dort \
            else [(ilk["faz"], ray_y[ilk["faz"]]), ("N", Y_N)]
        for k_i, (ad, ry) in enumerate(giris):
            xx = x + k_i*4.0
            _dot(psp, xx, ry)
            _l(psp, (xx, ry), (xx, Y_RCD_UST), "tel", 25)
        rcd(psp, x, n, f"-ID{ilk['rcd_no']}",
            ilk["rcd_ozel"].split(",")[0].replace(" ", ""),
            ilk["rcd_ozel"].split(",")[1].strip()
            if "," in ilk["rcd_ozel"] else "")
        _t(psp, x-12.5, Y_RCD_ALT-4.6, gkod, YZ["mikro"], "yazi",
           TA.MIDDLE_RIGHT)
        # grup alt rayları — grubun son sütununa kadar uzanır
        son = max(j for j, kk in enumerate(kayitlar) if kk["rcd"] == gkod)
        x_son = sutun_x(son) + 10.0
        alt = {}
        for k_i, (ad, ry) in enumerate(giris):
            ya = Y_RCD_ALT - 2.2 - k_i*2.6
            _l(psp, (x + k_i*4.0, Y_RCD_ALT), (x + k_i*4.0, ya), "tel", 25)
            _l(psp, (x + k_i*4.0, ya), (x_son, ya), "ray", 25)
            _t(psp, x_son+1.0, ya, ad if ad != "N" else f"N{ilk['rcd_no']}",
               YZ["mikro"], "yazi", TA.MIDDLE_LEFT)
            alt[ad] = ya
        grup_alt[gkod] = alt

    # ── 2) linyeler ─────────────────────────────────────────────────────────
    for i, k in enumerate(kayitlar):
        x = sutun_x(i)
        fy = ray_y[k["faz"]]
        uc_faz = uc_notr = None
        if k["rcd"] == "—":
            # kaçak akım rölesi arkasına ALINMAYAN linye — doğrudan baradan
            _dot(psp, x, fy); _l(psp, (x, fy), (x, Y_MCB_UST), "tel", 25)
            _dot(psp, x+4.0, Y_N)
            _l(psp, (x+4.0, Y_N), (x+4.0, Y_KLEMENS+0.8), "tel", 25)
            potansiyel_adi(psp, x+4.0, Y_MCB_UST-6, "N")
            for j, t in enumerate(("KAÇAK AKIM", "RÖLESİ YOK", "(kesintisiz)")):
                _t(psp, x-3.4, Y_RCD_ALT-1.0-j*2.0, t, YZ["mikro"], "yazi",
                   TA.MIDDLE_RIGHT)
        else:
            alt = grup_alt.get(k["rcd"])
            if alt is None:
                # grup rölesi başka sayfada
                _t(psp, x-3.0, Y_RCD_ALT-3.4,
                   f"-ID{k['rcd_no']} → s.{onceki.split('.')[0]}",
                   YZ["mikro"], "yazi", TA.MIDDLE_RIGHT)
                _pl(psp, [(x-2.6, Y_RCD_ALT-4.7), (x-0.6, Y_RCD_ALT-4.7),
                          (x, Y_RCD_ALT-3.4), (x-0.6, Y_RCD_ALT-2.1),
                          (x-2.6, Y_RCD_ALT-2.1)], "yazi", True, 18)
                uc_faz = uc_notr = Y_RCD_ALT-3.4
                _l(psp, (x, uc_faz), (x, Y_MCB_UST), "tel", 25)
                _dot(psp, x+4.0, Y_N)
                _l(psp, (x+4.0, Y_N), (x+4.0, Y_KLEMENS+0.8), "tel", 25)
                potansiyel_adi(psp, x+4.0, Y_MCB_UST-6, f"N{k['rcd_no']}")
            else:
                yf = alt.get(k["faz"], list(alt.values())[0])
                yn = alt.get("N", list(alt.values())[-1])
                _dot(psp, x, yf)
                _l(psp, (x, yf), (x, Y_MCB_UST), "tel", 25)
                _dot(psp, x+4.0, yn)
                _l(psp, (x+4.0, yn), (x+4.0, Y_KLEMENS+0.8), "tel", 25)
                potansiyel_adi(psp, x+4.0, Y_MCB_UST-6, f"N{k['rcd_no']}")
        # ── koruma cihazı ───────────────────────────────────────────────────
        korunan = 3 if k["kutup"] >= 3 else 1     # korunan kutup sayısı
        mcb(psp, x, korunan, k["tag"], f"{k['amper']} A",
            f"{korunan}P {k['egri']}", k["kesme"].replace(" ", ""))
        _l(psp, (x, Y_MCB_ALT), (x, Y_KLEMENS+0.8), "tel", 25)
        tel_no(psp, x, Y_MCB_ALT, Y_PE, k["tel"])
        # ── PE ──────────────────────────────────────────────────────────────
        pe_x = x + 8.0
        _dot(psp, pe_x, Y_PE)
        _l(psp, (pe_x, Y_PE), (pe_x, Y_KLEMENS+0.8), "pe", 25, "DASHDOT")
        # ── klemens ─────────────────────────────────────────────────────────
        klemens(psp, x, str(k["klem"]), "")
        klemens(psp, x+4.0, "", f"N{k['rcd_no']}" if k["rcd"] != "—" else "N")
        klemens(psp, pe_x, "", "PE")
        # ── kablo ve yük ────────────────────────────────────────────────────
        if not k["yedek"]:
            for xx, kt in ((x, "tel"), (x+4.0, "tel"), (pe_x, "pe")):
                _l(psp, (xx, Y_KLEMENS-0.8), (xx, Y_YUK_UST), kt, 25,
                   "DASHDOT" if kt == "pe" else None)
            _t(psp, x+4.0, Y_KABLO, f"{k['kesit']} {k['kablo']}",
               YZ["mikro"], "yazi")
            _l(psp, (x-3.0, Y_KABLO+1.6), (x+11.0, Y_KABLO+1.6), "yazi", 13)
            yuk_blogu(psp, x+4.0, ("L", "N", "PE"), k["kod"],
                      _sar(k["tanim"], 22)[:3])
        else:
            _l(psp, (x, Y_KLEMENS-0.8), (x, Y_KLEMENS-6.0), "tel", 25)
            _l(psp, (x-2.2, Y_KLEMENS-6.0), (x+2.2, Y_KLEMENS-6.0),
               "sembol", 25)
            _t(psp, x+4.0, Y_TAG, "YEDEK", YZ["etiket"], "yazi", stil="GYM-B")
            _t(psp, x+4.0, Y_TANIM, "ileride yük bağlanacak", YZ["kucuk"],
               "yazi")
            _t(psp, x+4.0, Y_TANIM-2.6, "kaçak akım koruması hazır",
               YZ["kucuk"], "yazi")
    _t(psp, DX0+1.0, Y_KLEMENS, "-X1", YZ["orta"], "yazi", TA.MIDDLE_LEFT,
       stil="GYM-B")


def _sar(metin, n):
    out, satir = [], ""
    for k in str(metin).replace("—", "·").split():
        if len(satir)+len(k)+1 > n:
            out.append(satir); satir = k
        else:
            satir = (satir+" "+k).strip()
    if satir: out.append(satir)
    return out or [""]


# ══════════════════════ BESLEME SAYFASI ═════════════════════════════════════
def besleme_sayfasi(psp, sayfa, onceki, sonraki):
    """Sayaç → ana şalter → ANA KAÇAK AKIM → parafudr → bara."""
    for ad, y in RAY:
        _l(psp, (DX0+120, y), (DX1, y), "ray", 35)
        _t(psp, DX1-0.6, y+1.4, ad, YZ["kucuk"], "yazi", TA.MIDDLE_RIGHT)
        _pl(psp, [(DX1+0.6, y-1.3), (DX1+4.4, y-1.3), (DX1+6.0, y),
                  (DX1+4.4, y+1.3), (DX1+0.6, y+1.3)], "yazi", True, 18)
        _t(psp, DX1+7.0, y, sonraki, YZ["mikro"], "yazi", TA.MIDDLE_LEFT)
    _l(psp, (DX0+120, Y_PE), (DX1, Y_PE), "pe", 35, "DASHDOT")
    _t(psp, DX1-0.6, Y_PE+1.4, "PE", YZ["kucuk"], "yazi", TA.MIDDLE_RIGHT)
    _t(psp, DX1+7.0, Y_PE, sonraki, YZ["mikro"], "yazi", TA.MIDDLE_LEFT)

    x = DX0 + 42
    ykat = [Y_L1+8, Y_L1+4, Y_L1, Y_L2, Y_L3, Y_N]
    # şebeke
    _t(psp, x, DY1-6, "ŞEBEKE / SAYAÇ PANOSU", YZ["etiket"], "yazi",
       stil="GYM-B")
    _t(psp, x, DY1-10, f"3F+N 400/230 V · 50 Hz · {P.ANA_KABLO} · "
       f"{P.ANA_L:.0f} m", YZ["kucuk"], "yazi")
    # sayaç
    ysay = DY1-26
    _c(psp, x, ysay, 4.2, "sembol", 35)
    _t(psp, x, ysay, "kWh", YZ["kucuk"], "sembol")
    _t(psp, x+6.0, ysay, "-P1   3F aktif enerji sayacı", YZ["kucuk"], "yazi",
       TA.MIDDLE_LEFT)
    for k in range(4):
        _l(psp, (x-6+k*4, ysay-4.2), (x-6+k*4, ysay-10), "tel", 25)
    # ana şalter
    ysal = ysay-14
    for k in range(4):
        kesici_kutbu(psp, x-6+k*4, ysal, ysal-10)
    _l(psp, (x-6, ysal-2.6), (x+6, ysal-2.6), "sembol", 18, "DASHED")
    _t(psp, x-10, ysal-2, "-Q1", YZ["orta"], "yazi", TA.MIDDLE_RIGHT)
    _t(psp, x+11, ysal-2, f"ANA ŞALTER  4×{P.ANA_KESICI//3} A  ·  Icu 6 kA",
       YZ["kucuk"], "yazi", TA.MIDDLE_LEFT)
    # ANA KAÇAK AKIM — ana şalterin hemen altında
    yrcd = ysal-22
    for k in range(4):
        kesici_kutbu(psp, x-6+k*4, yrcd, yrcd-8)
    _l(psp, (x-6, yrcd-2.2), (x+6, yrcd-2.2), "sembol", 18, "DASHED")
    for k, (u, a) in enumerate(zip(["1", "3", "5", "N"], ["2", "4", "6", "N"])):
        _t(psp, x-7.1+k*4, yrcd-0.8, u, YZ["mikro"], "yazi", TA.MIDDLE_RIGHT)
        _t(psp, x-7.1+k*4, yrcd-9.6, a, YZ["mikro"], "yazi", TA.MIDDLE_RIGHT)
    _pl(psp, [(x-8.6, yrcd-13), (x+8.6, yrcd-13), (x+8.6, yrcd-8),
              (x-8.6, yrcd-8)], "sembol", True, 35)
    _t(psp, x-2.0, yrcd-10.5, "I", YZ["orta"], "sembol")
    ex = x+2.0
    _l(psp, (ex, yrcd-9.6), (ex, yrcd-10.6), "sembol", 25)
    for i, w in enumerate((1.1, 0.7, 0.35)):
        _l(psp, (ex-w, yrcd-10.6-i*0.45), (ex+w, yrcd-10.6-i*0.45),
           "sembol", 25)
    _pl(psp, [(x-16, yrcd-4.4), (x-13, yrcd-4.4), (x-13, yrcd-1.4),
              (x-16, yrcd-1.4)], "sembol", True, 25)
    _l(psp, (x-16, yrcd-4.4), (x-13, yrcd-1.4), "sembol", 18)
    _t(psp, x-17.5, yrcd-2.9, "T", YZ["mikro"], "yazi", TA.MIDDLE_RIGHT)
    _t(psp, x-10, yrcd-15, "-ID0", YZ["orta"], "yazi", TA.MIDDLE_RIGHT)
    _t(psp, x+11, yrcd-3, f"ANA KAÇAK AKIM  4×{P.ANA_KACAK_A} A / "
       f"{P.ANA_KACAK_MA} mA", YZ["kucuk"], "yazi", TA.MIDDLE_LEFT)
    _t(psp, x+11, yrcd-6, "S tipi (zaman gecikmeli) — son devredeki 30 mA",
       YZ["mikro"], "yazi", TA.MIDDLE_LEFT)
    _t(psp, x+11, yrcd-8.6, f"röleler ile seçicilik sağlar. Ana şalter "
       f"{P.ANA_KESICI//3} A ile orantılıdır.", YZ["mikro"], "yazi",
       TA.MIDDLE_LEFT)
    for k in range(4):
        _l(psp, (x-6+k*4, yrcd-13), (x-6+k*4, ykat[2+k] if k < 3 else Y_N),
           "tel", 25)
    # baraya bağlanış
    for k, (ad, y) in enumerate(RAY):
        _l(psp, (x-6+k*4, yrcd-13), (x-6+k*4, y), "tel", 35)
        _l(psp, (x-6+k*4, y), (DX0+120, y), "ray", 35)
        _dot(psp, x-6+k*4, y)
        _t(psp, x-6+k*4+1.2, y+1.4, ad, YZ["mikro"], "yazi", TA.MIDDLE_LEFT)
    # parafudr
    xs = DX0+100
    _l(psp, (x-6, Y_L1), (xs, Y_L1), "tel", 25)
    for k in range(3):
        _pl(psp, [(xs+k*6-1.6, Y_PE+18), (xs+k*6+1.6, Y_PE+18),
                  (xs+k*6+1.6, Y_PE+26), (xs+k*6-1.6, Y_PE+26)],
            "sembol", True, 35)
        _l(psp, (xs+k*6-1.6, Y_PE+18), (xs+k*6+1.6, Y_PE+26), "sembol", 25)
        _l(psp, (xs+k*6, Y_PE+26), (xs+k*6, RAY[k][1]), "tel", 25)
        _dot(psp, xs+k*6, RAY[k][1])
        _l(psp, (xs+k*6, Y_PE+18), (xs+k*6, Y_PE), "tel", 25)
    _dot(psp, xs, Y_PE); _dot(psp, xs+6, Y_PE); _dot(psp, xs+12, Y_PE)
    _t(psp, xs-3.0, Y_PE+22, "-F0", YZ["orta"], "yazi", TA.MIDDLE_RIGHT)
    _t(psp, xs-3.0, Y_PE+18.5, "SPD T2", YZ["mikro"], "yazi", TA.MIDDLE_RIGHT)
    _t(psp, xs+16, Y_PE+22, "Tip 2 parafudr · Up 1,4 kV · In 20 kA · "
       "Imax 40 kA", YZ["mikro"], "yazi", TA.MIDDLE_LEFT)
    # topraklama
    _l(psp, (DX0+60, Y_PE), (DX0+60, Y_PE-8), "pe", 25)
    for i, w in enumerate((3.0, 2.0, 1.0)):
        _l(psp, (DX0+60-w, Y_PE-8-i*1.2), (DX0+60+w, Y_PE-8-i*1.2),
           "sembol", 35)
    _t(psp, DX0+64, Y_PE-9, f"ATB — ana topraklama barası · "
       f"Ra = {P.TOPRAK_R_HESAP:.1f} Ω ≤ {P.TOPRAK_HEDEF:.0f} Ω"
       .replace(".", ","), YZ["mikro"], "yazi", TA.MIDDLE_LEFT)
    # sistem notu
    _t(psp, DX0+4, DY0+20, "SİSTEM: TN-S — sayaç sonrası N ve PE ayrı çekilir, "
       "panoda hiçbir noktada birleştirilmez.", YZ["kucuk"], "yazi",
       TA.MIDDLE_LEFT)
    _t(psp, DX0+4, DY0+16, "SEÇİCİLİK: ana giriş 300 mA S tipi → son devre "
       "30 mA A tipi (Elektrik İç Tesisleri Yönetmeliği md.18).",
       YZ["kucuk"], "yazi", TA.MIDDLE_LEFT)
    _t(psp, DX0+4, DY0+12, "KESİCİ EĞRİSİ: aydınlatma linyelerinde B eğrisi, "
       "priz / klima / ısıtıcı linyelerinde C eğrisi. Tümü 6 kA.",
       YZ["kucuk"], "yazi", TA.MIDDLE_LEFT)
