# -*- coding: utf-8 -*-
"""AKS SİSTEMİ VE ZİNCİR ÖLÇÜ — mimari uygulama paftasının omurgası.

Yapı kuzeye göre yaklaşık 8° dönüktür. Profesyonel uygulama projesinde aks
sistemi yapının KENDİ doğrultusuna kurulur (cepheye paralel), kuzeye değil.
Bu modül:

1. Çeper duvar segmentlerinden baskın iki doğrultuyu bulur,
2. Bu doğrultulara dik/paralel duvar hatlarını kümeleyerek aks hatlarını türetir,
3. Aksları balonlarıyla birlikte çizer,
4. Akslar arası ve toplam zincir ölçüleri gerçek DIMENSION varlığı olarak basar.

Ölçülendirme ISO 129-1'e göre: milimetre, ondalıksız, yazı ölçü çizgisinin
üstünde ve ona paralel, mimari çentik uçlu.
"""
import math
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import LineString, Point
from shapely.ops import unary_union
import proj as P

K = 1000.0
ASGARI_SEG   = 0.90      # m — aks üretiminde dikkate alınan en kısa duvar
KUME_TOLERANS= 0.40      # m — aynı aks sayılacak en büyük sapma
ASGARI_KUME  = 1.60      # m — bir aksı haklı kılan toplam duvar uzunluğu
TASMA        = 3.10      # m — aks çizgisinin yapıdan taşma payı
OLCU_BANT    = 1.10      # m — zincir ölçü şeridinin yapıdan uzaklığı
BALON_R      = 0.42      # m (model) — aks balonu yarıçapı @1:50 → 8,4 mm

HARF = "ABCDEFGHJKLMNPRSTUVYZ"


def _cevre():
    ic = unary_union([P.SALON, P.ERKEK, P.KADIN])
    return ic, list(ic.exterior.coords)


def baskin_aci():
    """Çeper duvarlarının uzunluk ağırlıklı baskın doğrultusu (radyan, 0–π/2)."""
    ic, r = _cevre()
    kova = {}
    for a, b in zip(r, r[1:]):
        L = math.dist(a, b)
        if L < ASGARI_SEG: continue
        ang = math.atan2(b[1]-a[1], b[0]-a[0]) % (math.pi/2)
        anahtar = round(math.degrees(ang)/2)*2
        kova[anahtar] = kova.get(anahtar, 0)+L
    if not kova: return 0.0
    return math.radians(max(kova, key=kova.get))


ACI = baskin_aci()
U = (math.cos(ACI), math.sin(ACI))              # cephe doğrultusu
V = (-math.sin(ACI), math.cos(ACI))             # cepheye dik


def _pu(p): return p[0]*U[0] + p[1]*U[1]
def _pv(p): return p[0]*V[0] + p[1]*V[1]
def _xy(u, v): return (u*U[0] + v*V[0], u*U[1] + v*V[1])


def _kumele(degerler):
    """(offset, agirlik) listesini kümeler → [(merkez, toplam_agirlik)]"""
    if not degerler: return []
    degerler = sorted(degerler)
    kume = [[degerler[0][0]*degerler[0][1], degerler[0][1], degerler[0][0]]]
    for d, w in degerler[1:]:
        if abs(d - kume[-1][2]) <= KUME_TOLERANS:
            kume[-1][0] += d*w; kume[-1][1] += w
            kume[-1][2] = kume[-1][0]/kume[-1][1]
        else:
            kume.append([d*w, w, d])
    return [(k[2], k[1]) for k in kume if k[1] >= ASGARI_KUME]


def akslar():
    """Döner: (rakam_akslari, harf_akslari)
    rakam_aksi = (kod, u_offset)  → cepheye DİK hat
    harf_aksi  = (kod, v_offset)  → cepheye PARALEL hat
    """
    ic, r = _cevre()
    dik, paralel = [], []
    for a, b in zip(r, r[1:]):
        L = math.dist(a, b)
        if L < ASGARI_SEG: continue
        ang = math.atan2(b[1]-a[1], b[0]-a[0])
        fark = abs(((ang - ACI + math.pi/2) % math.pi) - math.pi/2)
        orta = ((a[0]+b[0])/2, (a[1]+b[1])/2)
        if fark < math.radians(14):              # cepheye paralel → harf aksı
            paralel.append((_pv(orta), L))
        elif abs(fark - math.pi/2) < math.radians(14):   # dik → rakam aksı
            dik.append((_pu(orta), L))
    rakam = [(str(i+1), u) for i, (u, w) in enumerate(_kumele(dik))]
    harf  = [(HARF[i], v) for i, (v, w) in enumerate(_kumele(paralel))]
    return rakam, harf


RAKAM, HARF_AKS = akslar()


def sinirlar():
    """Yapının aks koordinat sistemindeki (umin, umax, vmin, vmax) sınırları."""
    ic, r = _cevre()
    us = [_pu(p) for p in r]; vs = [_pv(p) for p in r]
    return min(us), max(us), min(vs), max(vs)


UMIN, UMAX, VMIN, VMAX = sinirlar()


def aks_hatti(tip, offset):
    """Aks çizgisinin iki ucu (model metre)."""
    if tip == "rakam":
        return _xy(offset, VMIN-TASMA), _xy(offset, VMAX+TASMA)
    return _xy(UMIN-TASMA, offset), _xy(UMAX+TASMA, offset)


# ══════════════════════ ÇİZİM ═════════════════════════════════════════════════
def ciz(msp, olcek=50, balon=True):
    """Aks hatlarını ve balonlarını model uzayına çizer."""
    import dxf_lib as X
    r_balon = BALON_R*olcek/50.0
    n = 0
    for tip, liste in (("rakam", RAKAM), ("harf", HARF_AKS)):
        for kod, off in liste:
            a, b = aks_hatti(tip, off)
            X.cizgi(msp, a, b, "G-AKS-HAT")
            if not balon: continue
            for uc, yon in ((a, -1), (b, +1)):
                d = math.dist(a, b)
                ux, uy = (b[0]-a[0])/d, (b[1]-a[1])/d
                cx = uc[0] + yon*ux*r_balon
                cy = uc[1] + yon*uy*r_balon
                msp.add_circle((cx*K, cy*K), r_balon*K,
                               dxfattribs={"layer": "G-AKS-BALON"})
                X.yazi(msp, (cx*K, cy*K), kod, r_balon*K*0.95,
                       "G-AKS-BALON", stil="GYM-B")
            n += 1
    return n


def _dim_kenar(msp, tip, offsetler, taban, olcek, yon=-1):
    """Bir doğrultuda zincir ölçü + toplam ölçü basar (gerçek DIMENSION).

    `taban` ölçü çizgisinin oturduğu dik-offset (m); `yon` ölçü çizgisinin
    hangi tarafa kaydırılacağını verir. Zincir satır aralığı kâğıtta 9 mm.
    """
    stil = f"GYM-{olcek}"
    ofs = sorted(offsetler)
    if len(ofs) < 2: return 0
    satir = 9.0*olcek/1000.0      # m — kâğıtta 9 mm
    n = 0

    def _nokta(a, t):
        return _xy(a, t) if tip == "rakam" else _xy(t, a)

    for a, b in zip(ofs, ofs[1:]):
        p1 = _nokta(a, taban); p2 = _nokta(b, taban)
        d = msp.add_aligned_dim(
            p1=(p1[0]*K, p1[1]*K), p2=(p2[0]*K, p2[1]*K),
            distance=yon*satir*K,
            dxfattribs={"layer": "G-OLCU-ZINCIR"},
            override={"dimstyle": stil})
        d.render(); n += 1
    p1 = _nokta(ofs[0], taban); p2 = _nokta(ofs[-1], taban)
    d = msp.add_aligned_dim(
        p1=(p1[0]*K, p1[1]*K), p2=(p2[0]*K, p2[1]*K),
        distance=yon*2.0*satir*K,
        dxfattribs={"layer": "G-OLCU-ZINCIR"},
        override={"dimstyle": stil})
    d.render(); n += 1
    return n


def olculendir(msp, olcek=50):
    """Aks bazlı zincir ölçüleri iki kenara basar (sol ve alt)."""
    n = 0
    if len(RAKAM) >= 2:
        n += _dim_kenar(msp, "rakam", [o for _, o in RAKAM],
                        VMIN-OLCU_BANT, olcek, -1)
    if len(HARF_AKS) >= 2:
        n += _dim_kenar(msp, "harf", [o for _, o in HARF_AKS],
                        UMIN-OLCU_BANT, olcek, -1)
    return n


def ozet():
    return {"aci_derece": round(math.degrees(ACI), 2),
            "rakam_aks": [(k, round(o, 3)) for k, o in RAKAM],
            "harf_aks": [(k, round(o, 3)) for k, o in HARF_AKS],
            "u_araligi": round(UMAX-UMIN, 3), "v_araligi": round(VMAX-VMIN, 3)}


if __name__ == "__main__":
    import json
    print(json.dumps(ozet(), ensure_ascii=False, indent=1))
