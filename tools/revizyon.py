# -*- coding: utf-8 -*-
"""REVİZYON DENEYİ — bir girdi değişince neyin kendiliğinden güncellendiğini ölçer.

Talimat §12: "Revizyon deneyi yap: örneğin kapı konumu değiştiğinde plan,
ölçü, liste ve ilgili görünüşün nasıl güncellendiğini göster."

Yöntem: proj.py'deki TEK girdiyi değiştirip modeli yeniden yükler ve
öncesi/sonrası farkını sayısal olarak karşılaştırır. Beklenen davranış,
değişikliğin elle hiçbir yere işlenmeden bütün türevlere yayılmasıdır.

    python3 tools/revizyon.py                # varsayılan deney: WC kapısı 700→800
    python3 tools/revizyon.py --kapi K05 800
"""
from __future__ import annotations
import importlib, json, os, sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
KOK = Path(__file__).resolve().parent.parent


def _durum():
    """Modelden türeyen bütün gözlenebilir büyüklükler.

    __pycache__ temizlenir: bayat .pyc, deneyin 'öncesi' durumunu bir önceki
    denemenin sonucuyla karıştırır ve sahte bir sonuç üretir (bu bilfiil oldu).
    """
    import shutil
    shutil.rmtree(KOK/"tools"/"__pycache__", ignore_errors=True)
    for m in list(sys.modules):
        if m in ("pilot", "proj") or m.startswith("agents"):
            del sys.modules[m]
    importlib.invalidate_caches()
    import proj as P
    import pilot as PL
    d = {
        "kapi_geom": {k: [round(v[0][0], 4), round(v[0][1], 4), v[1], v[2]]
                      for k, v in P.KAPI_GEOM.items()},
        "kapi_listesi": {k[0]: [k[3], k[4], k[5]] for k in P.KAPI_LISTESI},
        "mahal_m2": {n: round(g.area, 4) for n, g in
                     ((n, P.ISLAK["ERKEK"][n]) for n in ("soyunma", "dus", "wc"))},
        "mobilya": {ad: round(g.area, 4) for ad, g, t in P.MOBILYA},
        "mobilya_boy": {k: (v[0], v[2]) for k, v in P.MOBILYA_BOY.items()},
        "gorunus_en": round(PL.ALT_UV["dus"][3] - PL.ALT_UV["dus"][1], 4),
        "seramik_m2": round(P.M2_SERAMIK_D, 3) if hasattr(P, "M2_SERAMIK_D") else None,
        "kapi_yay_m2": {k: round(y.area, 4) for k, y in P.KAPI_YAY.items()
                        if y is not None},
        "islak_net_m2": P.ISLAK_NET_M2,
        "tavan_m2": round(P.M2_TAVAN, 3) if hasattr(P, "M2_TAVAN") else None,
        "kesif_islak": round(P.ISLAK_M2, 3),
    }
    return d


def _yaz(yol, kod, yeni_gen):
    """KAPI_EN_MM sözlüğündeki TEK sayıyı değiştirir."""
    import re
    s = yol.read_text()
    m = re.search(r'("' + kod + r'":\s*)(\d+)', s)
    if not m:
        raise RuntimeError(f"{kod} KAPI_EN_MM içinde bulunamadı")
    eski = int(m.group(2))
    s = s[:m.start(2)] + str(yeni_gen) + s[m.end(2):]
    yol.write_text(s)
    return eski


def _yaz_bolme(yol, yeni_mm):
    import re
    s = yol.read_text()
    m = re.search(r"(ISLAK_BOLME_T\s*=\s*)([\d.]+)", s)
    eski = float(m.group(2))
    s = s[:m.start(2)] + f"{yeni_mm/1000.0:.3f}" + s[m.end(2):]
    yol.write_text(s)
    return int(eski*1000)


def deney(kod="K05", yeni_gen=800, tur="kapi"):
    proj = KOK/"tools"/"proj.py"
    yedek = proj.read_text()
    once = _durum()
    eski_gen = (_yaz(proj, kod, yeni_gen) if tur == "kapi"
                else _yaz_bolme(proj, yeni_gen))
    try:
        sonra = _durum()
    finally:
        proj.write_text(yedek)
        for m in ("pilot", "proj"):
            if m in sys.modules: del sys.modules[m]
    return eski_gen, once, sonra


def _fark(a, b, yol=""):
    out = []
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            out += _fark(a.get(k), b.get(k), f"{yol}.{k}" if yol else str(k))
    elif isinstance(a, list):
        if a != b: out.append((yol, a, b))
    else:
        if a != b: out.append((yol, a, b))
    return out


def rapor(kod="K05", yeni_gen=800, tur="kapi"):
    eski_gen, once, sonra = deney(kod, yeni_gen, tur)
    f = _fark(once, sonra)
    if tur == "kapi":
        print(f"REVİZYON DENEYİ — {kod} kapı genişliği {eski_gen} → {yeni_gen} mm")
        print(f"  proj.py'de DEĞİŞEN TEK SAYI: KAPI_EN_MM['{kod}']\n")
    else:
        print(f"REVİZYON DENEYİ — ıslak iç bölme kalınlığı {eski_gen} → {yeni_gen} mm")
        print("  proj.py'de DEĞİŞEN TEK SAYI: ISLAK_BOLME_T\n")
    if not f:
        print("  ⚠ hiçbir türev güncellenmedi — ilişkilendirme YOK")
        return f
    grup = {}
    for yol, a, b in f:
        grup.setdefault(yol.split(".")[0], []).append((yol, a, b))
    baslik = {"kapi_geom": "PLAN — kapı geometrisi (konum · genişlik · açı)",
              "kapi_listesi": "LİSTE — kapı cetveli",
              "mahal_m2": "MAHAL ALANI",
              "mobilya": "SABİT MOBİLYA — yerleşim alanı",
              "mobilya_boy": "SABİT MOBİLYA — imalat boyu (metraja giren)",
              "gorunus_en": "İÇ GÖRÜNÜŞ — duvar genişliği",
              "seramik_m2": "METRAJ — duvar seramiği",
              "kapi_yay_m2": "ÇAKIŞMA KONTROLÜ — kapı açılım alanı",
              "islak_net_m2": "METRAJ — ıslak hacim net alanı",
              "tavan_m2": "METRAJ — asma tavan alanı",
              "kesif_islak": "KEŞİF — ıslak hacim brüt alanı"}
    for g, sat in grup.items():
        print(f"  ▸ {baslik.get(g, g)}")
        for yol, a, b in sat:
            print(f"      {yol:34s}  {a}  →  {b}")
    print(f"\n  {len(f)} türev büyüklük elle dokunulmadan güncellendi.")
    return f


if __name__ == "__main__":
    if "--bolme" in sys.argv:
        i = sys.argv.index("--bolme")
        rapor("", int(sys.argv[i+1]), tur="bolme")
    else:
        kod, gen = "K05", 800
        if "--kapi" in sys.argv:
            i = sys.argv.index("--kapi"); kod = sys.argv[i+1]; gen = int(sys.argv[i+2])
        rapor(kod, gen)
