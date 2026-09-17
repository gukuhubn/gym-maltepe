# -*- coding: utf-8 -*-
"""LİNYE GÜZERGÂHLARI — panodan cihazlara ortogonal tesisat hatları.

Her linye için güzergâh bir kez hesaplanır ve data/yollar.json içine yazılır;
çizim betikleri bu dosyayı okur. Yeniden hesaplamak için:  python3 tools/linye_yollari.py --yenile
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
from pathlib import Path
import proj as P

ROOT = Path(__file__).resolve().parent.parent
DOSYA = ROOT/"data"/"yollar.json"

# ── linye → cihaz eşlemesi ────────────────────────────────────────────────────
def _armatur():
    import helpers as h; h.register()
    import draw as D
    return D.aydinlatma_izgara()

def linye_cihazlari():
    """{linye_kodu: [(x, y), ...]}"""
    import helpers as h; h.register()
    import draw as D
    arm = D.aydinlatma_izgara()
    zon = {z[0]: z[1] for z in P.ZONES}
    from shapely.geometry import Point
    def _zon(ad): return [p for p in arm if zon[ad].contains(Point(*p))]
    c = {}
    c["L1"] = _zon("ARENA · SERBEST AĞIRLIK")
    c["L2"] = _zon("FONKSİYONEL · KARDİYO")
    c["L3"] = _zon("DİNLENME SALONU")
    c["L4"] = _zon("GİRİŞ · BANKO · SİRKÜLASYON")
    c["L5"] = [(d[n].representative_point().x, d[n].representative_point().y)
               for ad, d in P.ISLAK.items() for n in ("soyunma", "dus", "wc")]
    c["L6"] = [(x, y) for k, x, y, t, a in P.ACIL]
    # prizler — linye atamaları elektrik projesindeki gruplamayla aynı
    pr = [(k, x, y) for k, x, y, t, a in P.PRIZ_DUVAR]
    # yönetmelik: bir priz linyesine en çok 7 sorti → 16 duvar prizi 3 linyeye bölünür
    _g = {"P1": ("PR12","PR13","PR14","PR15","PR16","PR1"),
          "P2": ("PR5","PR6","PR7","PR8","PR9"),
          "P6": ("PR2","PR3","PR4","PR10","PR11")}
    for _lin, _kodlar in _g.items():
        c[_lin] = [(x, y) for k, x, y in pr if k in _kodlar]
    c["P3"] = [(x, y) for k, x, y, t, a in P.PRIZ_ZEMIN if k.startswith("PB")] + \
              [(x, y) for k, x, y, t in P.VERI]
    c["P4"] = [(x, y) for k, x, y, t, a in P.PRIZ_ZEMIN if k.startswith("PK")]
    c["P5"] = [(x, y) for k, x, y, t, a in P.PRIZ_IP44]
    for i, (kod, zon_ad, btu, pt, aci) in enumerate(P.KLIMA):
        c[f"K{i+1}"] = [pt]
    c["W1"] = [(P.ISITICI[0][1], P.ISITICI[0][2])]
    c["W2"] = [(P.ISITICI[1][1], P.ISITICI[1][2])]
    c["V1"] = [(x, y) for k, x, y, ad, a in P.FAN][:2]
    c["V2"] = [(x, y) for k, x, y, ad, a in P.FAN][2:]
    c["Z1"] = [(x, y) for k, x, y, t in P.VERI] + \
              [(x, y) for k, x, y, t, a in P.KAMERA] + \
              [(x, y) for k, x, y, t in P.HOPARLOR]
    c["Z2"] = [(x, y) for k, x, y, t in P.DEDEKTOR] + \
              [(x, y) for k, x, y, t, a in P.YANGIN]
    return {k: v for k, v in c.items() if v}

# ── anahtar → armatür bağlantıları (aydınlatma kumanda hattı) ────────────────
def anahtar_baglantilari():
    """Her anahtardan, kumanda ettiği bölgenin en yakın armatürüne giden hat."""
    import helpers as h; h.register()
    import draw as D
    from shapely.geometry import Point
    arm = D.aydinlatma_izgara()
    out = []
    for kod, x, y, tanim, aci in P.ANAHTAR:
        if not arm: continue
        hedef = min(arm, key=lambda p: math.dist(p, (x, y)))
        out.append((kod, (x, y), hedef))
    return out

def hesapla():
    import yol as Y
    cih = linye_cihazlari()
    veri = {"linye": {}, "anahtar": [], "cevrim": None}
    for kod, hedefler in cih.items():
        if kod == "Z2":
            seg, sira = Y.cevrim_guzergahi(P.PANO, hedefler)
        else:
            seg, sira = Y.linye_guzergahi(P.PANO, hedefler)
        veri["linye"][kod] = {"segment": seg, "uzunluk": Y.uzunluk(seg),
                              "cihaz": len(hedefler)}
    for kod, a, b in anahtar_baglantilari():
        g = Y.guzergah(a, b)
        if g: veri["anahtar"].append({"kod": kod, "segment": [g],
                                      "uzunluk": Y.uzunluk([g])})
    return veri

def yukle():
    if not DOSYA.exists(): return None
    return json.loads(DOSYA.read_text(encoding="utf-8"))

def kaydet(veri):
    DOSYA.parent.mkdir(exist_ok=True)
    DOSYA.write_text(json.dumps(veri, ensure_ascii=False), encoding="utf-8")

def segmentler(kod=None):
    """Çizim için: [(kod, [[(x,y),...], ...])]"""
    v = yukle()
    if v is None: return []
    if kod: return v["linye"].get(kod, {}).get("segment", [])
    return [(k, d["segment"]) for k, d in v["linye"].items()]

if __name__ == "__main__":
    import time, yol as Y
    t0 = time.time()
    veri = hesapla()
    kaydet(veri)
    tl = sum(d["uzunluk"] for d in veri["linye"].values())
    ta = sum(d["uzunluk"] for d in veri["anahtar"])
    capraz = 0
    for d in veri["linye"].values(): capraz += len(Y.capraz_var_mi(d["segment"]))
    for d in veri["anahtar"]: capraz += len(Y.capraz_var_mi(d["segment"]))
    print(f"{len(veri['linye'])} linye + {len(veri['anahtar'])} anahtar hattı · "
          f"{tl:.1f} + {ta:.1f} = {tl+ta:.1f} m · ÇAPRAZ SEGMENT: {capraz} · "
          f"{time.time()-t0:.1f} s")
    for k, d in sorted(veri["linye"].items()):
        print(f"  {k:4s} {d['cihaz']:2d} cihaz  {d['uzunluk']:7.2f} m  "
              f"{len(d['segment'])} segment")
