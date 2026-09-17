# -*- coding: utf-8 -*-
"""KANAL GÜZERGÂHLARI — hava kanalları ortogonal döşenir.

TS 3419 / uygulama kuralı: kanallar yapı akslarına paralel/dik ilerler; yön
değişimi ancak bir dirsek parçası ile olur. Bu modül her ana kanal hattını
(panjur → fan → menfezler) ızgara tabanlı ortogonal yol bulucu ile üretir ve
`data/kanallar.json` içine yazar. `proj.py` bu dosyayı okuyup KANAL
sözlüğündeki güzergâhları değiştirir.

Yeniden hesaplama:  python3 tools/kanal_yollari.py
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
from shapely.geometry import LineString

ROOT  = Path(__file__).resolve().parent.parent
DOSYA = ROOT/"data"/"kanallar.json"


def _islak_zincir(P, fan, panjur):
    v = [(m[1], m[2]) for m in P.MENFEZ if m[4] == "valf"]
    ust = sorted([p for p in v if p[1] > fan[1]], key=lambda p: -p[1])
    alt = sorted([p for p in v if p[1] <= fan[1]], key=lambda p: p[1])
    return ust + [fan] + alt + [panjur]


def hesapla():
    import proj as P, yol
    fan = {f[0]: (f[1], f[2]) for f in P.FAN}
    pan = {p[0]: (p[1], p[2]) for p in P.PANJUR}
    # (kanal, başlangıç zinciri) — panjurdan fana, oradan menfezlere sırayla
    zincir = {
        "besleme": [pan["TH"], fan["F-TH"]] +
                   [(m[1], m[2]) for m in P.MENFEZ if m[4] == "besleme"],
        "egzoz":   [pan["EG"], fan["F-EG"]] +
                   [(m[1], m[2]) for m in P.MENFEZ if m[4] == "egzoz"],
        # ıslak hacim egzozu: fanın iki yanındaki valfler uç noktadan fana doğru
        # toplanır, fandan sonra çıkış panjuruna gidilir
        "islak":   _islak_zincir(P, fan["F-IS"], pan["EI"]),
    }
    cikti = {}
    for ad, nokta in zincir.items():
        govde = []
        for a, b in zip(nokta, nokta[1:]):
            g = yol.guzergah(a, b)
            if not g:
                g = [tuple(a), (b[0], a[1]), tuple(b)]     # ortogonal yedek
            if govde and govde[-1] == g[0]: g = g[1:]
            govde.extend(g)
        # ardışık tekrarları ve aynı doğrultudaki kırılmaları sadeleştir
        sade = [govde[0]]
        for p in govde[1:]:
            if p != sade[-1]: sade.append(p)
        tek = [sade[0]]
        for k in range(1, len(sade)-1):
            ax, ay = tek[-1]; bx, by = sade[k]; cx, cy = sade[k+1]
            if (abs(ax-bx) < 1e-9 and abs(bx-cx) < 1e-9) or \
               (abs(ay-by) < 1e-9 and abs(by-cy) < 1e-9): continue
            tek.append((bx, by))
        tek.append(sade[-1])
        cikti[ad] = [[round(x, 3), round(y, 3)] for x, y in tek]
    return cikti


def yukle():
    if DOSYA.exists():
        return {k: [tuple(p) for p in v] for k, v in
                json.loads(DOSYA.read_text(encoding="utf-8")).items()}
    return {}


def kaydet(d=None):
    d = d or hesapla()
    DOSYA.parent.mkdir(parents=True, exist_ok=True)
    DOSYA.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return d


if __name__ == "__main__":
    d = kaydet()
    for ad, g in d.items():
        capraz = sum(1 for a, b in zip(g, g[1:])
                     if abs(a[0]-b[0]) > 1e-6 and abs(a[1]-b[1]) > 1e-6)
        print(f"{ad:9s} {LineString(g).length:6.1f} m · {len(g)-1} segment · "
              f"çapraz {capraz}")
