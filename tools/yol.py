# -*- coding: utf-8 -*-
"""ORTOGONAL GÜZERGÂH MOTORU — tesisat hatları için.

Elektrik linyeleri, zayıf akım çevrimleri ve boru hatları ÇAPRAZ ÇİZİLMEZ.
Bu modül, yapı içinde yalnızca yatay/düşey adımlarla ilerleyen bir ızgara
grafiği üzerinde en kısa yolu bulur; duvar çeperine yakın güzergâhı
ödüllendirir (gerçek uygulamada tesisat duvar dibinden / asma tavan kenarından
gider, oda ortasından geçmez).

Kurallar
--------
1. Her adım 4 komşuludur → üretilen poligonun her segmenti ya yatay ya düşeydir.
2. Izgara yapı iç yüzünden `KENAR_PAY` kadar içeri alınır (duvara girmez).
3. Duvara yakınlık ödülü: çepere `CEPER_BANT` içinde kalan düğümlerin maliyeti
   düşüktür → hat, açık alanı kesmek yerine çeperden dolaşır.
4. Bölme duvarları engeldir; geçiş yalnızca kapı boşluklarından olur.
5. Aynı linyeye ait cihazlar, panodan başlayarak en yakın komşu sırasıyla
   zincirlenir; ortak segmentler birleştirilerek ana hat (trunk) oluşur.
"""
import sys, os, math, heapq
sys.path.insert(0, os.path.dirname(__file__))
from shapely.geometry import Point, LineString, Polygon, box
from shapely.ops import unary_union, nearest_points
import proj as P

ADIM       = 0.10      # m — ızgara çözünürlüğü
KENAR_PAY  = 0.10      # m — iç yüzden içeri çekme
CEPER_BANT = 0.55      # m — bu bant içinde güzergâh ucuz
CEPER_ODUL = 0.35      # bant içindeki adım maliyeti çarpanı
KAPI_GEN   = 0.95      # m — bölme duvarında açılan geçiş genişliği

# ── serbest alan: yapı içi eksi bölme duvarları artı kapı geçişleri ───────────
def _kapi_noktalari():
    """Kapı geçişleri — mimari kapı listesine karşılık gelen fiziksel boşluklar.

    Dış/ana kapılar P.KAPILAR'dan; iç kapılar (duş kapağı, WC kapısı) ilgili
    hacmin çeperi ile soyunma hacmi arasındaki en yakın nokta çiftinden
    türetilir — böylece kapı konumu geometriden gelir, elle girilmez.
    """
    pts = []
    for (x, y), gen, aci, lbl in P.KAPILAR:
        pts.append(((x, y), max(gen, KAPI_GEN)/2 + 0.14))
    for ad, d in P.ISLAK.items():
        soy = d["soyunma"]
        for n in ("dus", "wc"):
            a, b = nearest_points(d[n].exterior, soy.exterior)
            pts.append((((a.x+b.x)/2, (a.y+b.y)/2), 0.70/2 + 0.20))
        # soyunma kapısı: soyunma çeperinin salona en yakın noktası
        a, b = nearest_points(soy.exterior, P.SALON.difference(d["tum"]).buffer(-0.35))
        pts.append((((a.x+b.x)/2, (a.y+b.y)/2), 0.90/2 + 0.20))
    return pts

KAPI_GECIS = _kapi_noktalari()

def _serbest_alan():
    ic = unary_union([P.SALON, P.ERKEK, P.KADIN]).buffer(-KENAR_PAY)
    engel = []
    for g in (P.ERKEK, P.KADIN):
        engel.append(g.exterior.buffer(0.09, cap_style=2))
    for ad, d in P.ISLAK.items():
        for n in ("soyunma", "dus", "wc"):
            engel.append(d[n].exterior.buffer(0.09, cap_style=2))
    kapi = [Point(pt).buffer(r) for pt, r in KAPI_GECIS]
    engel_u = unary_union(engel).difference(unary_union(kapi))
    return ic.difference(engel_u)

SERBEST = _serbest_alan()
_CEPER  = unary_union([P.SALON.exterior, P.ERKEK.exterior, P.KADIN.exterior])

# ── ızgara ────────────────────────────────────────────────────────────────────
_b = SERBEST.bounds
NX = int((_b[2]-_b[0])/ADIM)+1
NY = int((_b[3]-_b[1])/ADIM)+1
def _xy(i, j): return (_b[0]+i*ADIM, _b[1]+j*ADIM)

_GECERLI = {}
_MALIYET = {}
for i in range(NX):
    for j in range(NY):
        p = Point(*_xy(i, j))
        if not SERBEST.contains(p): continue
        _GECERLI[(i, j)] = True
        d = _CEPER.distance(p)
        _MALIYET[(i, j)] = ADIM*(CEPER_ODUL if d <= CEPER_BANT else 1.0)

def _dugum(pt):
    """En yakın geçerli ızgara düğümü."""
    i0 = int(round((pt[0]-_b[0])/ADIM)); j0 = int(round((pt[1]-_b[1])/ADIM))
    if (i0, j0) in _GECERLI: return (i0, j0)
    en = None
    for r in range(1, 26):
        for di in range(-r, r+1):
            for dj in (-r, r):
                for a, b in ((i0+di, j0+dj), (i0+dj, j0+di)):
                    if (a, b) in _GECERLI:
                        d = (a-i0)**2 + (b-j0)**2
                        if en is None or d < en[0]: en = (d, (a, b))
        if en: return en[1]
    raise ValueError(f"ızgara dışı nokta: {pt}")

_KOMSU = ((1, 0), (-1, 0), (0, 1), (0, -1))     # YALNIZ ortogonal

def _astar(a, b):
    if a == b: return [a]
    h = lambda n: (abs(n[0]-b[0])+abs(n[1]-b[1]))*ADIM*CEPER_ODUL
    ac = [(h(a), 0.0, a)]; geldi = {a: None}; g = {a: 0.0}
    while ac:
        _, gc, n = heapq.heappop(ac)
        if n == b: break
        if gc > g.get(n, 1e18): continue
        for di, dj in _KOMSU:
            m = (n[0]+di, n[1]+dj)
            if m not in _GECERLI: continue
            # dönüş cezası: gereksiz zikzakı engeller
            ceza = 0.0
            p = geldi.get(n)
            if p is not None and (n[0]-p[0], n[1]-p[1]) != (di, dj): ceza = ADIM*0.9
            ng = gc + _MALIYET[m] + ceza
            if ng < g.get(m, 1e18):
                g[m] = ng; geldi[m] = n; heapq.heappush(ac, (ng+h(m), ng, m))
    if b not in geldi: return None
    yol = []; n = b
    while n is not None: yol.append(n); n = geldi[n]
    return yol[::-1]

def _sadelestir(dugumler):
    """Aynı yöndeki ardışık adımları tek segmente indirger."""
    if not dugumler: return []
    pts = [_xy(*d) for d in dugumler]
    out = [pts[0]]
    for k in range(1, len(pts)-1):
        ax, ay = out[-1]; bx, by = pts[k]; cx, cy = pts[k+1]
        if (abs(ax-bx) < 1e-9 and abs(bx-cx) < 1e-9) or \
           (abs(ay-by) < 1e-9 and abs(by-cy) < 1e-9):
            continue
        out.append((bx, by))
    out.append(pts[-1])
    return [(round(x, 3), round(y, 3)) for x, y in out]

def guzergah(a, b):
    """İki nokta arasında ortogonal güzergâh — [(x,y), ...]"""
    yol = _astar(_dugum(a), _dugum(b))
    if yol is None: return None
    return _sadelestir(yol)

def linye_guzergahi(baslangic, cihazlar):
    """Panodan başlayıp cihazları en yakın komşu sırasıyla dolaşan hat.
    Döner: (govde, [(cihaz, dallanma_noktasi)]) — govde ortogonal poligon listesi."""
    kalan = list(cihazlar); segmentler = []; sira = []
    cari = baslangic
    while kalan:
        en = min(kalan, key=lambda c: abs(c[0]-cari[0])+abs(c[1]-cari[1]))
        g = guzergah(cari, en)
        if g: segmentler.append(g); sira.append(en)
        kalan.remove(en); cari = en
    return segmentler, sira

def cevrim_guzergahi(baslangic, cihazlar):
    """Kapalı çevrim (yangın algılama A-B loop): panodan çıkar, tüm
    cihazları dolaşır, panoya döner."""
    seg, sira = linye_guzergahi(baslangic, cihazlar)
    if sira:
        d = guzergah(sira[-1], baslangic)
        if d: seg.append(d)
    return seg, sira

def capraz_var_mi(segmentler, tol=1e-6):
    """Denetim: herhangi bir segment çapraz mı?"""
    hatali = []
    for g in segmentler:
        for k in range(len(g)-1):
            (x1, y1), (x2, y2) = g[k], g[k+1]
            if abs(x1-x2) > tol and abs(y1-y2) > tol:
                hatali.append(((x1, y1), (x2, y2)))
    return hatali

def uzunluk(segmentler):
    return round(sum(LineString(g).length for g in segmentler if len(g) > 1), 2)

if __name__ == "__main__":
    print(f"ızgara: {len(_GECERLI)} düğüm · adım {ADIM} m · serbest alan "
          f"{SERBEST.area:.1f} m²")
    hedefler = [(x, y) for k, x, y, t, a in P.PRIZ_DUVAR[:6]]
    seg, sira = linye_guzergahi(P.PANO, hedefler)
    print(f"örnek linye: {len(seg)} segment · {uzunluk(seg)} m · "
          f"çapraz {len(capraz_var_mi(seg))}")
    for g in seg[:2]: print("   ", g)
