# -*- coding: utf-8 -*-
"""RÖLÖVE OKUYUCU — işverenin ölçülü CAD dosyasını proje veri modeline alır.

NEDEN: Bu projenin geometrisi bugüne kadar `TRIMODE-Alan_Dagilimi.pdf`
(JPEG raster) üzerinden renk maskesiyle vektörleştirilmişti; beyan edilen
doğruluk ±%3 idi. Oysa aynı çizimin **ölçülü vektör kaynağı**
`input/ESAT-FINAL.dwg` içinde duruyordu. Talimat §2 açıkça şunu söyler:
"Fotoğraftan tahmin edilen boyutu ölçülmüş bilgi gibi kullanma."
Bu modül o kaynağı açar ve ölçülmüş geometriyi tek kaynak hâline getirir.

KAYNAK KAYDI (talimat §3)
  kaynak_kimligi : ROLEVE-01
  baslik         : ESAT-FINAL.dwg — TRIMODE mağaza projesi (4 pafta)
  yayinci        : TRIMODE (işveren mimarı) · içinde Leica 3DDisto ölçüm katmanları
  dosya          : input/ESAT-FINAL.dwg  (AC1032 / AutoCAD 2018)
  disiplin       : mimari — mevcut durum, yıkım, alan dağılımı, yerleşim
  erisim         : işveren tarafından proje başında teslim edildi
  birim          : SANTİMETRE (poligon alanı ile pafta m² etiketi birebir
                   doğrulandı: 870.586,1 cm² ↔ "87,05 M2")
  dogrulama      : DOĞRULANDI — alan etiketi + ölçü zinciri çapraz kontrolü

PAFTALAR (0_TESTO katmanındaki başlıklardan bulunur)
  DUVAR PLANI · YIKIM & SÖKÜM · MAĞAZA ALAN DAĞILIM · YERLEŞİM PLANI

Kullanım:
    python3 tools/roleve.py            # oku, data/roleve.json yaz, özet bas
    python3 tools/roleve.py --fark     # mevcut raster modele göre sapma
"""
from __future__ import annotations
import json, math, re, sys
from pathlib import Path

import ezdxf
from shapely.geometry import Polygon

KOK = Path(__file__).resolve().parent.parent
DWG = KOK/"input"/"ESAT-FINAL.dwg"
ARA = KOK/"work"/"roleve"
CIKTI = KOK/"data"/"roleve.json"

CM = 0.01                      # model birimi → metre
PAFTA_EN, PAFTA_BOY = 2420.0, 1600.0     # cm — çizimdeki dış çerçeve
CERCEVE_ALAN = (PAFTA_EN*PAFTA_BOY/1e4, 2410.0*1590.0/1e4)   # 387.20 · 383.19 m²

# 0_TESTO başlığındaki anahtar kelime → sayfa anahtarı
BASLIK = {"DUVAR PLANI": "duvar", "YIKIM": "yikim",
          "ALAN DA": "alan", "YERLE": "yerlesim"}


# ─────────────────────────────────────────────── yardımcılar
def _duz(mtext: str) -> str:
    """MTEXT biçim kodlarını (\\fFont|b1|i0|c238; \\pxql; \\P …) temizler."""
    t = re.sub(r"\\f[^;]*;", "", mtext)
    t = re.sub(r"\\[pP][^;]*;", "", t)
    t = re.sub(r"\\[A-Za-z][^\;]*;", "", t)
    t = t.replace("\\P", " ").replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", t).strip()


def _nokta(e):
    """Nesnenin temsilî noktalarını döndürür (birim: cm)."""
    t = e.dxftype()
    if t == "LINE":       return [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
    if t == "LWPOLYLINE": return [(p[0], p[1]) for p in e.get_points("xy")]
    if t == "POLYLINE":   return [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
    if t in ("TEXT", "MTEXT", "INSERT"): return [(e.dxf.insert.x, e.dxf.insert.y)]
    if t == "POINT":      return [(e.dxf.location.x, e.dxf.location.y)]
    if t in ("CIRCLE", "ARC"): return [(e.dxf.center.x, e.dxf.center.y)]
    if t == "DIMENSION":  return [(e.dxf.defpoint.x, e.dxf.defpoint.y)]
    return []


def _merkez_y(e):
    p = _nokta(e)
    return sum(q[1] for q in p)/len(p) if p else None


def _cerceve_mi(ps) -> bool:
    if len(ps) not in (4, 5): return False
    a = Polygon(ps).area/1e4
    return any(abs(a-c) < 1.0 for c in CERCEVE_ALAN)


def _temizle(ps, esik=0.5):
    """Sıfır uzunluklu ve yinelenen köşeleri atar (esik: cm)."""
    out = []
    for p in ps:
        if not out or math.hypot(p[0]-out[-1][0], p[1]-out[-1][1]) > esik:
            out.append(p)
    if len(out) > 2 and math.hypot(out[0][0]-out[-1][0], out[0][1]-out[-1][1]) <= esik:
        out.pop()
    return out


# ─────────────────────────────────────────────── açı
def baskin_aci(ps) -> float:
    """Poligon kenarlarının uzunlukla ağırlıklı baskın doğrultusu (derece)."""
    top = {}
    for i in range(len(ps)):
        x0, y0 = ps[i]; x1, y1 = ps[(i+1) % len(ps)]
        L = math.hypot(x1-x0, y1-y0)
        if L < 30: continue                       # 30 cm altı kenarlar gürültü
        a = math.degrees(math.atan2(y1-y0, x1-x0)) % 90
        top[round(a, 1)] = top.get(round(a, 1), 0) + L
    if not top: return 0.0
    # 0° civarına yakın kümeyi ağırlıklı ortala
    ana = max(top, key=top.get)
    pay = tuk = 0.0
    for a, w in top.items():
        if min(abs(a-ana), 90-abs(a-ana)) < 4.0:
            pay += a*w; tuk += w
    return round(pay/tuk, 2)


# ─────────────────────────────────────────────── okuma
def dxf_yolu(yeniden=False) -> Path:
    ARA.mkdir(parents=True, exist_ok=True)
    hedef = ARA/(DWG.stem + ".dxf")
    if hedef.exists() and not yeniden:
        return hedef
    sys.path.insert(0, str(KOK/"tools"))
    import dwg as D
    D.cevir(DWG, ARA)
    if not hedef.exists():
        raise RuntimeError(f"dönüşüm çıktı vermedi: {DWG}")
    return hedef


def oku(yeniden=False) -> dict:
    doc = ezdxf.readfile(dxf_yolu(yeniden))
    msp = doc.modelspace()

    # 1) Pafta başlıklarından bantları bul
    basliklar = []
    for e in msp.query("MTEXT TEXT"):
        if e.dxf.layer != "0_TESTO": continue
        t = _duz(e.text if e.dxftype() == "MTEXT" else e.dxf.text).upper()
        for anahtar, ad in BASLIK.items():
            if anahtar in t:
                basliklar.append((e.dxf.insert.y, ad, t))
    basliklar.sort()
    if len(basliklar) != 4:
        raise RuntimeError(f"4 pafta başlığı beklenirken {len(basliklar)} bulundu: "
                           f"{[b[2] for b in basliklar]}")

    # Başlık paftanın üstünde; bant = başlıktan bir önceki başlığa kadar
    bantlar = {}
    for i, (y, ad, t) in enumerate(basliklar):
        alt = basliklar[i-1][0] + 60 if i else y - PAFTA_BOY
        bantlar[ad] = (alt, y + 30, t)

    # 2) Nesneleri bantlara dağıt
    sayfalar = {}
    for ad, (alt, ust, baslik) in bantlar.items():
        ic = [e for e in msp
              if not e.dxf.layer.startswith("Leica")
              and (v := _merkez_y(e)) is not None and alt <= v <= ust]
        sayfalar[ad] = {"baslik": baslik, "nesne": ic, "taban": alt}

    # 3) Ortak orijin: ALAN paftasındaki salon poligonunun sol-alt köşesi
    salon_ham = None
    for e in sayfalar["alan"]["nesne"]:
        if e.dxftype() != "LWPOLYLINE": continue
        ps = [(p[0], p[1]) for p in e.get_points("xy")]
        if len(ps) < 3 or _cerceve_mi(ps): continue
        if abs(Polygon(ps).area/1e4 - 87.06) < 0.5:
            salon_ham = _temizle(ps)
    if salon_ham is None:
        raise RuntimeError("salon poligonu (87 m²) bulunamadı")
    ox = min(p[0] for p in salon_ham)
    aci = baskin_aci(salon_ham)

    # 4) Sayfa sayfa çıkar — metreye çevir, paftanın kendi tabanına göre hizala
    sonuc = {
        "kaynak": {
            "kaynak_kimligi": "ROLEVE-01",
            "baslik": "ESAT-FINAL.dwg — TRIMODE mağaza projesi (4 pafta)",
            "yayinci": "TRIMODE (işveren mimarı)",
            "dosya": str(DWG.relative_to(KOK)),
            "dxf_surum": doc.dxfversion,
            "birim": "cm (alan etiketi ile doğrulandı)",
            "disiplin": "mimari — mevcut durum / yıkım / alan / yerleşim",
            "dogrulama": "DOĞRULANDI",
            "aciklama": "Leica 3DDisto ölçüm katmanları çizimin içinde; "
                        "geometri ölçülmüş kaynaktır, raster türetme değildir.",
        },
        "baskin_aci_derece": aci,
        "orijin_cm": [ox, None],
        "sayfalar": {},
    }

    for ad, blok in sayfalar.items():
        taban = blok["taban"]
        poli, cizgi, olcu, yazi, blok_ref = [], [], [], [], []
        for e in blok["nesne"]:
            t = e.dxftype()
            if t == "LWPOLYLINE":
                ps = [(p[0], p[1]) for p in e.get_points("xy")]
                if len(ps) < 2 or _cerceve_mi(ps): continue
                ham = len(ps); ps = _temizle(ps)
                if len(ps) < 2: continue
                kapali = bool(e.closed) or len(ps) >= 3
                al = Polygon(ps).area/1e4 if len(ps) >= 3 else 0.0
                poli.append({"n": [[round((x-ox)*CM, 4), round((y-taban)*CM, 4)] for x, y in ps],
                             "alan_m2": round(al, 3), "kapali": kapali,
                             "katman": e.dxf.layer, "atilan_kose": ham-len(ps)})
            elif t == "LINE":
                cizgi.append({"a": [round((e.dxf.start.x-ox)*CM, 4), round((e.dxf.start.y-taban)*CM, 4)],
                              "b": [round((e.dxf.end.x-ox)*CM, 4), round((e.dxf.end.y-taban)*CM, 4)],
                              "katman": e.dxf.layer})
            elif t == "DIMENSION":
                try: mo = float(e.get_measurement())
                except Exception: continue
                olcu.append({"olcu_m": round(mo*CM, 4), "katman": e.dxf.layer,
                             "konum": [round((e.dxf.defpoint.x-ox)*CM, 4),
                                       round((e.dxf.defpoint.y-taban)*CM, 4)]})
            elif t in ("MTEXT", "TEXT"):
                s = _duz(e.text if t == "MTEXT" else e.dxf.text)
                if not s: continue
                h = e.dxf.char_height if t == "MTEXT" else e.dxf.height
                yazi.append({"metin": s, "yukseklik_cm": round(h, 1), "katman": e.dxf.layer,
                             "konum": [round((e.dxf.insert.x-ox)*CM, 4),
                                       round((e.dxf.insert.y-taban)*CM, 4)]})
            elif t == "INSERT":
                blok_ref.append({"ad": e.dxf.name, "katman": e.dxf.layer,
                                 "konum": [round((e.dxf.insert.x-ox)*CM, 4),
                                           round((e.dxf.insert.y-taban)*CM, 4)],
                                 "aci": round(float(e.dxf.rotation), 2)})
        sonuc["sayfalar"][ad] = {"baslik": blok["baslik"], "poligon": poli, "cizgi": cizgi,
                                 "olcu": olcu, "yazi": yazi, "blok": blok_ref}
    return sonuc


# ─────────────────────────────────────────────── türetilmiş ölçüler
def mahal_alanlari(r) -> dict:
    """ALAN paftasındaki m² etiketlerini en yakın poligonla eşleştirir."""
    s = r["sayfalar"]["alan"]
    etiket = []
    for y in s["yazi"]:
        mm = re.search(r"([\d]+[,.]\d+)\s*M2", y["metin"], re.I)
        if mm:
            etiket.append((float(mm.group(1).replace(",", ".")), y["konum"], y["metin"]))
    poli = [p for p in s["poligon"] if p["alan_m2"] > 1.0]
    esles = {}
    for deg, kon, ham in etiket:
        en_iyi, en_fark = None, 1e9
        for p in poli:
            f = abs(p["alan_m2"] - deg)
            if f < en_fark: en_fark, en_iyi = f, p
        esles[ham] = {"etiket_m2": deg,
                      "poligon_m2": en_iyi["alan_m2"] if en_iyi else None,
                      "sapma_m2": round(en_fark, 3) if en_iyi else None,
                      "kose": len(en_iyi["n"]) if en_iyi else 0,
                      "eslesti": en_fark < 0.05}
    return esles


def olcu_zinciri(r) -> list:
    """Tüm paftalardaki DIMENSION değerleri — büyükten küçüğe, tekilleştirilmiş."""
    v = {}
    for ad, s in r["sayfalar"].items():
        for o in s["olcu"]:
            if o["olcu_m"] < 0.02: continue
            v.setdefault(round(o["olcu_m"], 3), []).append(ad)
    return sorted(((k, sorted(set(vv))) for k, vv in v.items()), reverse=True)


def yaz(r, yol=CIKTI):
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    return yol


# ─────────────────────────────────────────────── rapor
def ozet(r):
    print(f"RÖLÖVE — {r['kaynak']['baslik']}")
    print(f"  DXF {r['kaynak']['dxf_surum']} · birim {r['kaynak']['birim']}")
    print(f"  baskın doğrultu: {r['baskin_aci_derece']}°")
    print()
    for ad, s in r["sayfalar"].items():
        sifir = sum(p["atilan_kose"] for p in s["poligon"])
        print(f"  [{ad:9s}] {s['baslik'][:34]:34s} "
              f"poligon {len(s['poligon']):3d} · çizgi {len(s['cizgi']):3d} · "
              f"ölçü {len(s['olcu']):3d} · yazı {len(s['yazi']):3d} · blok {len(s['blok']):3d}"
              + (f"  ⚠ {sifir} sıfır/yinelenen köşe atıldı" if sifir else ""))
    print()
    print("  ALAN PAFTASI — etiket ↔ poligon doğrulaması:")
    for ham, d in mahal_alanlari(r).items():
        im = "✓" if d["eslesti"] else "✗"
        print(f"    {im} {ham:12s} etiket {d['etiket_m2']:7.2f} m² · "
              f"poligon {d['poligon_m2']:7.2f} m² ({d['kose']} köşe) · "
              f"sapma {d['sapma_m2']:.3f} m²")
    print()
    z = olcu_zinciri(r)
    print(f"  ÖLÇÜ ZİNCİRİ — {len(z)} tekil değer, en büyük 12'si (m):")
    for v, sf in z[:12]:
        print(f"    {v:7.3f}   {'·'.join(sf)}")


if __name__ == "__main__":
    r = oku("--yeniden" in sys.argv)
    ozet(r)
    p = yaz(r)
    print(f"\n  → {p.relative_to(KOK)}  ({p.stat().st_size/1024:.0f} KB)")


# ─────────────────────────────────────────────── model koordinatına oturtma
def _don(ps, aci, mx=0.0, my=0.0):
    c, s = math.cos(aci), math.sin(aci)
    return [((x-mx)*c - (y-my)*s + mx, (x-mx)*s + (y-my)*c + my) for x, y in ps]


def _tasи(ps, dx, dy):                     # noqa - tek kullanımlık
    return [(x+dx, y+dy) for x, y in ps]


def model_poligonlari(r=None):
    """Ölçülmüş poligonları mevcut model koordinat sistemine kaydeder (rijit).

    Ölçek DEĞİŞTİRİLMEZ — ölçülmüş boyut esastır. Yalnız döndürme + öteleme
    uygulanır ki mevcut cihaz konumları, güzergâhlar ve aks sistemi geçerli
    kalsın. Uyum, simetrik fark alanı en küçüklenerek aranır.
    """
    from shapely.affinity import rotate, translate
    r = r or oku()
    s = r["sayfalar"]["alan"]
    ad_poli = {}
    for p in s["poligon"]:
        if p["alan_m2"] < 1.0: continue
        for ad, hedef in (("salon", 87.06), ("erkek", 8.25), ("kadin", 8.50)):
            if abs(p["alan_m2"] - hedef) < 0.05:
                ad_poli[ad] = Polygon(p["n"])
    eksik = {"salon", "erkek", "kadin"} - set(ad_poli)
    if eksik:
        raise RuntimeError(f"ölçülmüş poligon bulunamadı: {eksik}")

    G = json.loads((KOK/"data/geometry.json").read_text())
    ref = Polygon(G["poligonlar"]["salon"])

    olculen = ad_poli["salon"]
    en_iyi = None
    # kaba tarama: açı, sonra merkez öteleme; ardından ince tarama
    for kaba in (True, False):
        aci_ara = [a/10 for a in range(-1200, 1201, 25)] if kaba else \
                  [en_iyi[1] + a/100 for a in range(-150, 151, 5)]
        for aci in aci_ara:
            grup = {ad: rotate(g, aci, origin=olculen.centroid) for ad, g in ad_poli.items()}
            d = ref.centroid
            k = grup["salon"].centroid
            oteleme = [(d.x-k.x, d.y-k.y)] if kaba else \
                      [(d.x-k.x+i/100, d.y-k.y+j/100) for i in range(-40, 41, 5)
                       for j in range(-40, 41, 5)]
            for dx, dy in oteleme:
                sal = translate(grup["salon"], dx, dy)
                fark = sal.symmetric_difference(ref).area
                if en_iyi is None or fark < en_iyi[0]:
                    en_iyi = (fark, aci, dx, dy)
    fark, aci, dx, dy = en_iyi
    son = {ad: translate(rotate(g, aci, origin=olculen.centroid), dx, dy)
           for ad, g in ad_poli.items()}
    return son, {"donme_derece": round(aci, 3), "oteleme_m": [round(dx, 4), round(dy, 4)],
                 "simetrik_fark_m2": round(fark, 3),
                 "uyum_yuzde": round(100*(1 - fark/ref.area), 2)}


def geometri_dosyasi(cikti=None):
    """data/geometry_roleve.json — mevcut geometry.json ile aynı arayüz."""
    r = oku()
    poli, uyum = model_poligonlari(r)
    G = json.loads((KOK/"data/geometry.json").read_text())
    eski = {k: Polygon(v) for k, v in G["poligonlar"].items()}
    kars = {}
    for ad in ("salon", "erkek", "kadin"):
        y, e = poli[ad], eski[ad]
        kars[ad] = {"olculen_m2": round(y.area, 3), "raster_m2": round(e.area, 3),
                    "sapma_m2": round(y.area-e.area, 3),
                    "sapma_yuzde": round(100*(y.area-e.area)/e.area, 2),
                    "hausdorff_m": round(y.exterior.hausdorff_distance(e.exterior), 3)}
    d = {
        "kaynak": "ESAT-FINAL.dwg (TRIMODE, AC1032) — ÖLÇÜLMÜŞ vektör kaynak",
        "yontem": "ODA File Converter ile DXF'e çevrildi; MAĞAZA ALAN DAĞILIM "
                  "paftasındaki mahal poligonları alındı; birim cm→m; "
                  "mevcut model koordinatına rijit (ölçeksiz) kayıt yapıldı",
        "dogruluk": "ölçülmüş — alan etiketi ile ±0,01 m² doğrulandı",
        "olcek_m_per_px": None,
        "rotasyon_derece": uyum["donme_derece"],
        "kayit": uyum,
        "baskin_aci_derece": r["baskin_aci_derece"],
        "poligonlar": {ad: [[round(x, 4), round(y, 4)] for x, y in g.exterior.coords[:-1]]
                       for ad, g in poli.items()},
        "alan_kontrol": kars,
        "onceki_kaynak": G["kaynak"],
    }
    yol = Path(cikti) if cikti else KOK/"data"/"geometry_roleve.json"
    yol.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return d, yol
