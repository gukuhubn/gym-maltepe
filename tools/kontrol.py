# -*- coding: utf-8 -*-
"""ÇİZİM KONTROLÜ — çakışma, taşma, konum ve mantık denetimi.
Model uzayında (metre) çalışır; bulguları liste hâlinde döner."""
import sys, os, math, itertools
sys.path.insert(0, os.path.dirname(__file__))
from shapely.geometry import Point, LineString, box
from shapely.ops import unary_union
import proj as P

IC = unary_union([P.SALON, P.ERKEK, P.KADIN])
BULGU = []
def ekle(sev, kategori, mesaj):
    BULGU.append((sev, kategori, mesaj))

KOT = {"priz": 0.40, "priz IP44": 1.20, "anahtar": 1.20, "kamera": 2.40, "yangın": 1.40,
       "acil": 2.30, "klima": 2.40, "ısıtıcı": 1.90, "pano": 1.70, "veri": 0.70,
       "sensör": 3.10, "hoparlör": 3.10, "dedektör": 3.10, "fan": 3.00, "menfez": 3.05,
       "vitrifiye": 0.0}

def _cihazlar():
    """(kod, nokta, tip, montaj) — montaj: duvar / tavan / zemin"""
    c = []
    for k, x, y, t, a in P.PRIZ_DUVAR: c.append((k, (x, y), "priz", "duvar"))
    for k, x, y, t, a in P.PRIZ_ZEMIN: c.append((k, (x, y), "priz", "zemin-kutu"))
    for k, x, y, t, a in P.PRIZ_IP44: c.append((k, (x, y), "priz IP44", "duvar"))
    for k, x, y, t, a in P.ANAHTAR:   c.append((k, (x, y), "anahtar", "duvar"))
    for k, x, y, t, a in P.SENSOR:    c.append((k, (x, y), "sensör", "tavan"))
    for k, x, y, t, a in P.KAMERA:    c.append((k, (x, y), "kamera", "duvar"))
    for k, x, y, t in P.HOPARLOR:     c.append((k, (x, y), "hoparlör", "tavan"))
    for k, x, y, t in P.VERI:
        c.append((k, (x, y), "veri", "tavan" if k.startswith("AP") else "banko"))
    for k, x, y, t in P.DEDEKTOR:     c.append((k, (x, y), "dedektör", "tavan"))
    for k, x, y, t, a in P.YANGIN:    c.append((k, (x, y), "yangın", "duvar"))
    for k, x, y, t, a in P.ACIL:
        c.append((k, (x, y), "acil", "duvar" if k.startswith("AY") else "tavan"))
    for k, z, b, pt, a in P.KLIMA:    c.append((k, pt, "klima", "duvar"))
    for k, x, y, t, a in P.ISITICI:   c.append((k, (x, y), "ısıtıcı", "duvar"))
    for k, x, y, t, a in P.FAN:       c.append((k, (x, y), "fan", "tavan"))
    for k, x, y, d, t in P.MENFEZ:    c.append((k, (x, y), "menfez", "tavan"))
    for k, x, y, t in P.VITRIFIYE:    c.append((k, (x, y), "vitrifiye", "zemin"))
    c.append(("AP", P.PANO, "pano", "duvar"))
    return c

def calistir():
    BULGU.clear()
    C = _cihazlar()
    # 1 · bina dışına taşan cihaz
    for k, p, t, m in C:
        if not IC.buffer(0.30).contains(Point(p)):
            ekle("HATA", "konum", f"{t} {k} bina dışında ({p[0]:.2f}, {p[1]:.2f})")
    # 2 · aynı montaj düzleminde çakışan cihazlar
    for (k1, p1, t1, m1), (k2, p2, t2, m2) in itertools.combinations(C, 2):
        if m1 != m2: continue                       # tavan ile duvar çakışmaz
        dk = abs(KOT.get(t1, 0) - KOT.get(t2, 0))   # montaj kotu farkı
        d = math.dist(p1, p2)
        if d < 0.22 and dk < 0.45:
            ekle("HATA", "çakışma", f"{t1} {k1} ile {t2} {k2} çakışıyor "
                                    f"({d*100:.0f} cm, kot farkı {dk*100:.0f} cm)")
        elif d < 0.35 and t1 != t2 and dk < 0.45:
            ekle("UYARI", "çakışma", f"{t1} {k1} ile {t2} {k2} çok yakın ({d*100:.0f} cm)")
        elif d < 0.22 and dk >= 0.45:
            ekle("BİLGİ", "çakışma", f"{t1} {k1} ({KOT.get(t1,0):.2f} m) ile {t2} {k2} "
                                     f"({KOT.get(t2,0):.2f} m) planda üst üste — farklı kotta, "
                                     f"imalat çakışması yok")
    # 3 · duvara monte cihaz gerçekten duvarda mı
    for k, p, t, m in C:
        if m != "duvar" or t in ("vitrifiye",): continue
        _, _, mes = P.duvar_yonu(p)
        if mes > 0.45:
            ekle("UYARI", "montaj", f"{t} {k} duvardan {mes*100:.0f} cm uzakta — "
                                    f"duvara monte sembol serbest alanda")
    # 4 · tavan cihazı ekipmanın üstünde mi (çakışma değil ama kontrol)
    ek = [(kod, g) for kod, ad, g in P.ekipman_poligonlari()]
    for k, p, t, m in C:
        if m != "zemin": continue
        for kod, g in ek:
            if g.contains(Point(p)):
                ekle("HATA", "çakışma", f"{t} {k} ekipman {kod} ile aynı yerde")
    # 5 · kanal / boru bina dışına taşıyor mu
    for ad, d in P.KANAL.items():
        ls = LineString(d["guzergah"])
        dis = ls.difference(IC.buffer(0.35))
        if dis.length > 0.20:
            ekle("UYARI", "güzergâh", f"{ad} kanalı bina dışında {dis.length:.2f} m ilerliyor "
                                      f"(dış ünite/panjur bağlantısı ise normal)")
    # 6 · armatür ızgarası ekipmanla dikey çakışıyor mu (tavan vs 2,15 m ekipman)
    import draw as D
    yuksek = [(kod, g) for kod, ad, g in P.ekipman_poligonlari()
              if P.EK_H.get(kod[0], 0) >= 2.0]
    for px, py in D.aydinlatma_izgara():
        for kod, g in yuksek:
            if g.contains(Point((px, py))):
                ekle("UYARI", "koordinasyon",
                     f"armatür {kod} ekipmanının ({P.EK_H[kod[0]]:.2f} m) tam üstünde — "
                     f"tavan yüksekliği 3,20 m, açıklık yeterli ama aydınlatma gölgelenir")
    # 7 · menfez ile armatür tavan çakışması
    arm = D.aydinlatma_izgara()
    for k, x, y, deb, t in P.MENFEZ:
        for ax, ay in arm:
            if math.dist((x, y), (ax, ay)) < 0.70:
                ekle("UYARI", "koordinasyon",
                     f"menfez {k} ile lineer armatür {math.dist((x,y),(ax,ay))*100:.0f} cm "
                     f"mesafede — tavan koordinasyonu gerekir")
    # 8 · linye yük kontrolü
    for l in P.LINYE:
        anma = int(l[2].split("×")[1].replace(" A", ""))
        akim = l[5]*1000/230
        if akim > anma*0.85:
            ekle("UYARI", "elektrik", f"linye {l[0]}: bağlı güç {l[5]:.2f} kW → {akim:.1f} A, "
                                      f"koruma {anma} A (>%80 yüklenme)")
    # 9 · kaçış mesafesi
    cikis = [(k[0][0], k[0][1]) for k in P.KAPILAR if "ÇIKIŞ" in k[3] or "GİRİŞ" in k[3]]
    enuzak = 0; nokta = None
    for g in (P.SALON,):
        for x in [i*0.5 for i in range(int(g.bounds[2]/0.5)+1)]:
            for y in [i*0.5 for i in range(int(g.bounds[3]/0.5)+1)]:
                if not g.contains(Point(x, y)): continue
                d = min(math.dist((x, y), c) for c in cikis)
                if d > enuzak: enuzak, nokta = d, (x, y)
    if enuzak > 25:
        ekle("HATA", "yangın", f"en uzak noktadan çıkışa {enuzak:.1f} m (>25 m)")
    else:
        ekle("BİLGİ", "yangın", f"en uzak noktadan çıkışa kuş uçuşu {enuzak:.1f} m — sınır içinde")
    # ── 10 · MİMARİ DENETİMLER ────────────────────────────────────────────────
    # 10a mahal alanı kapanışı
    fark = abs(P.A["ic_toplam"] - P.MAHAL_TOPLAM - P.MAHAL_DUVAR_PAYI)
    if fark > 0.01:
        ekle("HATA", "mimari", f"mahal listesi kapanmıyor: net toplam {P.MAHAL_TOPLAM} + duvar payı "
                               f"{P.MAHAL_DUVAR_PAYI} ≠ {P.A['ic_toplam']} m²")
    # 10b bitmiş zemin kotu sürekliliği (kuru hacimler eşit olmalı)
    kuru = {m[3] for m in P.MAHAL_LISTESI if not m[9]}
    kotlar = {z[0]: z[3] for z in P.ZEMIN_TIPLERI}
    farkli = {k for k in kuru if abs(kotlar[k]) > 0.005}
    if farkli:
        ekle("HATA", "mimari", f"kuru hacim zemin kotu ±0,00 değil: {', '.join(sorted(farkli))}")
    else:
        ekle("BİLGİ", "mimari", "tüm kuru hacimlerde bitmiş zemin kotu ±0,00 — eşik/tökezleme yok")
    # 10c kapı yüksekliği ile tavan kotu
    _kapi_h = {k[0]: k[4]/1000.0 for k in P.KAPI_LISTESI}
    for m in P.MAHAL_LISTESI:
        for kod in [x.strip() for x in m[8].split("·") if x.strip().startswith("K")]:
            if kod in _kapi_h and _kapi_h[kod] > m[7]-0.10:
                ekle("HATA", "mimari", f"{kod} kapı yüksekliği {_kapi_h[kod]:.2f} m, "
                                       f"{m[0]} tavan kotu {m[7]:.2f} m — lento sığmıyor")
    # 10d duvara monte cihaz kotu ile tavan kotu
    _mahal_tavan = []
    for ad, mno, g in P._MAHAL_GEOM:
        _mahal_tavan.append((g, mno, P._MAHAL_BILGI[mno][7]))
    for kod, p_, tip, montaj in _cihazlar():
        if montaj != "duvar" or tip not in KOT: continue
        for g, mno, tk in _mahal_tavan:
            if g.contains(Point(*p_)) and KOT[tip] > tk-0.15:
                ekle("HATA", "mimari", f"{tip} {kod} kotu {KOT[tip]:.2f} m, {mno} tavan kotu "
                                       f"{tk:.2f} m — cihaz asma tavana giriyor")
    # 10e klima iç ünitesi (kot + gövde) asma tavan altında kalmalı
    for kod, zon, btu, (x_, y_), a_ in P.KLIMA:
        for g, mno, tk in _mahal_tavan:
            if g.contains(Point(x_, y_)) and P.KLIMA_KOT+0.32 > tk:
                ekle("HATA", "mimari", f"klima {kod} üst kotu {P.KLIMA_KOT+0.32:.2f} m, "
                                       f"{mno} tavan kotu {tk:.2f} m")
    # 10f tavan içi tesisat katmanları asma tavan boşluğuna sığmalı (bölge bazlı)
    for tip, kat in P.TAVAN_KATMAN.items():
        tk = P.TAVAN_KOT[tip]
        tes = min(k[1] for k in kat if k[4] != "tavan")
        tas = max(k[2] for k in kat if k[4] == "tavan")
        ust = max(k[2] for k in kat)
        serb = round((tes-tas)*1000)
        if tes < tas:
            ekle("HATA", "mimari", f"{tip} bölgesinde tesisat en alt kotu {tes:.4f} m, asma tavan "
                                   f"taşıyıcı üstü {tas:.4f} m — çakışma")
        elif serb < 20:
            ekle("UYARI", "mimari", f"{tip} bölgesinde tesisat ile asma tavan taşıyıcısı arası "
                                    f"yalnızca {serb} mm")
        if ust > P.KOT_YAPISAL_TAVAN:
            ekle("HATA", "mimari", f"{tip} bölgesinde tesisat üst kotu {ust:.2f} m > yapısal "
                                   f"döşeme altı {P.KOT_YAPISAL_TAVAN:.2f} m")
    ekle("BİLGİ", "mimari", "tavan içi serbestlik (mm): " +
         " · ".join(f"{t} {v}" for t, v in P.TAVAN_SERBESTLIK.items()))
    # 10g kaçış yolu genişliği / mahal kapsamı
    _kapsanan = {y_[0] for y_ in P.TAHLIYE_YOL}
    _gereken = {m[0] for m in P.MAHAL_LISTESI if not m[9] and m[0] != "101"}
    if _gereken - _kapsanan:
        ekle("UYARI", "yangın", f"tahliye yolu tanımlanmamış mahal: {', '.join(sorted(_gereken-_kapsanan))}")
    if P.TAHLIYE_MAX > P.TAHLIYE_SINIR:
        ekle("HATA", "yangın", f"en uzun kaçış {P.TAHLIYE_MAX} m > sınır {P.TAHLIYE_SINIR} m")
    else:
        ekle("BİLGİ", "yangın", f"en uzun kaçış yolu {P.TAHLIYE_MAX} m — sınır {P.TAHLIYE_SINIR:.0f} m")
    # 10h pano hesabı
    if P.PANO_UYGUNSUZ:
        for r in P.PANO_UYGUNSUZ:
            ekle("HATA", "elektrik", f"linye {r[0]}: Ib={r[6]} A · In={r[7]} A · Iz={r[9]} A · "
                                     f"ΔU=%{r[12]} (sınır %{r[13]:.0f})")
    else:
        ekle("BİLGİ", "elektrik", f"pano hesabı: {len(P.PANO_HESAP)} linyenin tamamı uygun; "
                                  f"maks ΔU %{P.DU_MAX} ({P.DU_MAX_LINYE}), toplam %{P.TOPLAM_DU_MAX}")
    return BULGU

if __name__ == "__main__":
    b = calistir()
    hata = sum(1 for s, _, _ in b if s == "HATA")
    uyari = sum(1 for s, _, _ in b if s == "UYARI")
    for s, k, m in b:
        print(f"  {s:5s} [{k:13s}] {m}")
    print(f"\nÇİZİM KONTROLÜ: {hata} hata, {uyari} uyarı, {len(b)-hata-uyari} bilgi")
