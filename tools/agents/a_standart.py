# -*- coding: utf-8 -*-
"""ÇİZİM STANDARDI DENETİM AJANI — katman, kalem, yazı, pafta düzeni.

Dayanak: ISO 128 (çizgi kalınlığı serisi), ISO 3098 / TS 88 (yazı yüksekliği
serisi), TS EN ISO 216 (kâğıt), TS EN ISO 5457 (pafta kenar boşluğu),
ÇŞB CADD Usul ve Esasları (katman adlandırma), SMACNA/NCS katman yapısı,
Mimarlık ve Mühendislik Projelerinin Dijital Olarak Hazırlanması Hakkında
Yönetmelik (RG 05.08.2026/33331) EK-4.
"""
import re
from .base import Ajan
import proj as P

ISO_KALEM = [13, 18, 25, 35, 50, 70, 100, 140, 200]      # 1/100 mm
ISO_YAZI  = [1.8, 2.5, 3.5, 5.0, 7.0, 10.0, 14.0, 20.0]  # mm — plot
KAGIT     = {"A4": (297, 210), "A3": (420, 297), "A2": (594, 420),
             "A1": (841, 594), "A0": (1189, 841)}
DISIPLIN  = ("A-", "M-", "E-", "G-", "X-", "S-", "Y-")
AD_DESEN  = re.compile(r"^[A-Z]-[A-Z0-9ĞÜŞİÖÇ]+(-[A-Z0-9ĞÜŞİÖÇ]+)*$")


class StandartAjani(Ajan):
    ad = "standart"
    baslik = "Çizim standardı — katman, kalem, yazı ve pafta düzeni denetimi"

    def denetle(self, r):
        self._katman(r); self._pafta(r); self._yazi(r); self._antet(r)
        self._belge_kod_uyumu(r); self._kapi_boslugu(r); self._mahal_kodu(r)

    # 5 ── docs/CIZIM_STANDARDI.md ↔ tools/standart.py — ikisi ayrışamaz
    def _belge_kod_uyumu(self, r):
        from pathlib import Path
        import standart as ST
        md = Path(__file__).resolve().parents[2]/"docs"/"CIZIM_STANDARDI.md"
        if not md.exists():
            r.eksik("standart", "docs/CIZIM_STANDARDI.md yok — yazılı standart eksik"); return
        t = md.read_text(encoding="utf-8")
        eksik = []
        for k, v in ST.KALEM.items():
            if str(v) not in t: eksik.append(f"kalem {k}={v}")
        for k, v in ST.YAZI.items():
            if f"{v:g}".replace(".", ",") not in t and f"{v:g}" not in t:
                eksik.append(f"yazı {k}={v}")
        for n in ("Z-01", "K1", "elips", "kaba yapı"):
            if n not in t: eksik.append(n)
        if eksik:
            r.hata("standart", f"belge ile kod ayrışmış: {', '.join(eksik[:6])}",
                   dayanak="docs/CIZIM_STANDARDI.md ↔ tools/standart.py")
        else:
            r.bilgi("standart", "yazılı standart ile kod sabitleri uyumlu "
                                f"({len(ST.KALEM)} kalem · {len(ST.YAZI)} yazı boyu)")

    # 6 ── kapı boşluğunun içinden duvar geçmiyor (MEGEP 2.51; kullanıcı bulgusu)
    def _kapi_boslugu(self, r):
        from pathlib import Path
        import math, ezdxf
        from shapely.geometry import LineString, Polygon, Point
        yol = Path(__file__).resolve().parents[2]/"cad"/"pilot"
        dosya = next(iter(sorted(yol.glob("P-01_*.dxf"))), None)
        if dosya is None:
            r.eksik("kapı", "P-01 DXF yok — kapı boşluğu denetlenemedi"); return
        try:
            import pilot as PL
        except Exception as e:
            r.eksik("kapı", f"pilot modülü yüklenemedi: {e}"); return
        doc = ezdxf.readfile(dosya); msp = doc.modelspace()
        DUVAR_KAT = {"A-KATMAN-CIZGI", "A-KESIT-TARAMA", "A-KESIT-GORUNEN",
                     "A-KATMAN-YALITIM"}
        ihlal = []
        for kod, (pt, gen, aci) in P.KAPI_GEOM.items():
            if not P.ISLAK[PL.BLOK]["tum"].buffer(0.35).contains(Point(*pt)): continue
            kal = PL._kapi_duvar_kalinligi(pt)
            a = math.radians(aci); ux, uy = math.cos(a), math.sin(a); nx, ny = -uy, ux
            h = gen/2 - 0.02; t = kal/2 - 0.004
            bos = Polygon([(pt[0]-ux*h-nx*t, pt[1]-uy*h-ny*t), (pt[0]+ux*h-nx*t, pt[1]+uy*h-ny*t),
                           (pt[0]+ux*h+nx*t, pt[1]+uy*h+ny*t), (pt[0]-ux*h+nx*t, pt[1]-uy*h+ny*t)])
            n = 0
            for e in msp:
                if e.dxf.layer not in DUVAR_KAT: continue
                if e.dxftype() == "LINE":
                    g = LineString([(e.dxf.start.x/1000, e.dxf.start.y/1000),
                                    (e.dxf.end.x/1000, e.dxf.end.y/1000)])
                elif e.dxftype() == "LWPOLYLINE":
                    q = [(p[0]/1000, p[1]/1000) for p in e.get_points("xy")]
                    if len(q) < 2: continue
                    g = LineString(q)
                else: continue
                if g.intersection(bos).length > 0.01: n += 1
            if n: ihlal.append(f"{kod} ({n} parça)")
        if ihlal:
            r.hata("kapı", "kapı boşluğunun içinden duvar katmanı geçiyor: " + ", ".join(ihlal),
                   dayanak="MEGEP Şekil 2.51 — duvarda kapı genişliği kadar boşluk açılır")
        else:
            r.bilgi("kapı", "pilot bölgedeki kapı boşluklarının içinden duvar katmanı geçmiyor")

    # 7 ── mahal kodları Mimarlar Odası §12 biçiminde
    def _mahal_kodu(self, r):
        kotu = [no for no in P.MAHAL_NO.values()
                if not re.match(r"^(B-\d{2}|Z-\d{2}|\d{3,4})$", no)]
        if kotu:
            r.hata("mahal", f"mahal kodu standart dışı: {kotu}",
                   dayanak="Mimarlar Odası çizim standardı §12 (B-01 · Z-01 · 101)")
        else:
            r.bilgi("mahal", f"{len(P.MAHAL_NO)} mahal kodu §12 biçiminde (Z-01…)")

    # 1 ── katman tablosu
    def _katman(self, r):
        try:
            import dxf_lib as X
        except Exception as e:
            r.hata("katman", f"dxf_lib yüklenemedi: {e}"); return
        adlar = set()
        for k in X.KATMANLAR:
            ad, renk, ctip, kalem, aciklama = k[0], k[1], k[2], k[3], k[4]
            if ad in adlar:
                r.hata("katman", f"'{ad}' katmanı iki kez tanımlı")
            adlar.add(ad)
            if not ad.startswith(DISIPLIN):
                r.hata("katman", f"'{ad}' disiplin ön eki yok — "
                                 f"{' / '.join(DISIPLIN)} bekleniyor",
                       dayanak="ÇŞB CADD · SMACNA/NCS katman yapısı")
            if not AD_DESEN.match(ad):
                r.uyari("katman", f"'{ad}' adlandırma deseni dışında "
                                  f"(BÜYÜK HARF, tire ayraçlı)")
            if not (6 <= len(ad) <= 24):
                r.uyari("katman", f"'{ad}' uzunluğu {len(ad)} — 6–24 karakter beklenir")
            if kalem not in ISO_KALEM:
                r.hata("katman", f"'{ad}' kalem kalınlığı {kalem/100:.2f} mm — ISO 128 "
                                 f"serisi dışında", dayanak="ISO 128-20")
            if not aciklama:
                r.uyari("katman", f"'{ad}' açıklamasız")
        if "0" in adlar:
            r.hata("katman", "layer 0 kullanılmış — hiçbir geometri 0 katmanında olmaz")
        grup = {}
        for k in X.KATMANLAR: grup.setdefault(k[0].split("-")[0], []).append(k[0])
        r.bilgi("katman", f"{len(X.KATMANLAR)} katman · " +
                " · ".join(f"{g} {len(v)}" for g, v in sorted(grup.items())))
        kalemler = sorted({k[3] for k in X.KATMANLAR})
        r.bilgi("katman", "kullanılan kalem kalınlıkları: " +
                ", ".join(f"{k/100:.2f}" for k in kalemler) + " mm")

    # 2 ── pafta listesi: her çizim kendi paftasında mı
    def _pafta(self, r):
        try:
            import build_dxf as BD
        except Exception as e:
            r.hata("pafta", f"build_dxf yüklenemedi: {e}"); return
        pf = BD.PAFTALAR
        disiplinler = {}
        sema = getattr(BD, "SEMA_PAFTA", set())
        for no, (ad, dis, donan) in pf.items():
            disiplinler.setdefault(dis, []).append(no)
            if no in sema:
                r.bilgi("pafta", f"{no} {ad}: ölçeksiz şema paftası — "
                                 f"tümü kâğıt alanında, görüntü penceresi yok")
            elif not donan:
                r.uyari("pafta", f"{no} {ad}: donduruluan katman listesi boş — "
                                 f"pafta tüm disiplinleri üst üste gösteriyor",
                        konum=no)
        # her disiplinde tek bir toplayıcı pafta olmalı, geri kalanı ayrışmış
        for dis, nolar in sorted(disiplinler.items()):
            if len(nolar) < 2:
                r.hata("pafta", f"{dis} disiplininde yalnız {len(nolar)} pafta — her konu "
                                f"kendi paftasında verilmelidir",
                       dayanak="MEB İEGM Mekanik Proje Genel İlkeleri · MMO Proje Esasları")
            else:
                r.bilgi("pafta", f"{dis}: {len(nolar)} pafta — {', '.join(sorted(nolar))}")
        # her pafta ayrı DXF dosyası olarak da üretiliyor mu
        tekil = getattr(BD, "TEKIL_PAFTA", None)
        if not tekil:
            r.hata("pafta", "paftalar tek model uzayı üzerinde katman dondurularak "
                            "üretiliyor — her pafta ayrı DXF dosyası olarak da verilmeli",
                   oneri="build_dxf.TEKIL_PAFTA ile pafta başına bağımsız DXF üretin.")
        else:
            r.bilgi("pafta", f"{len(tekil)} pafta ayrı DXF dosyası olarak üretiliyor")

    # 3 ── yazı yüksekliği ve ölçek
    def _yazi(self, r):
        try:
            import dxf_lib as X
        except Exception:
            return
        yz = getattr(X, "YAZI_YUKSEKLIK", None)
        if yz is None:
            r.uyari("yazı", "dxf_lib içinde YAZI_YUKSEKLIK tablosu yok — yazı yükseklikleri "
                            "çizim içine gömülü", oneri="ISO 3098 serisini tek tabloda tanımlayın.")
            return
        for ad, (plot, olcek) in yz.items():
            if plot not in ISO_YAZI:
                r.hata("yazı", f"'{ad}': {plot} mm — ISO 3098 / TS 88 serisi dışında "
                               f"({', '.join(str(x) for x in ISO_YAZI)})", dayanak="ISO 3098")
        r.bilgi("yazı", f"{len(yz)} yazı sınıfı tanımlı: " +
                ", ".join(f"{a} {v[0]} mm" for a, v in yz.items()))

    # 4 ── antet ve pafta kenar düzeni
    def _antet(self, r):
        try:
            import build_dxf as BD
        except Exception:
            return
        boy = getattr(BD, "PAFTA_BOYUT", (420, 297))
        if tuple(boy) not in [KAGIT[k] for k in KAGIT]:
            r.hata("antet", f"pafta boyutu {boy[0]}×{boy[1]} mm — TS EN ISO 216 A serisi "
                            f"dışında", dayanak="TS EN ISO 216 · TS 5734 ISO 9961")
        else:
            ad = [k for k, v in KAGIT.items() if v == tuple(boy)][0]
            r.bilgi("antet", f"pafta boyutu {ad} ({boy[0]}×{boy[1]} mm)")
        zorunlu = ("İŞVEREN", "PROJE", "PAFTA ADI", "PAFTA NO", "ÖLÇEK", "TARİH",
                   "REVİZYON", "ÇİZEN", "KONTROL")
        alanlar = getattr(BD, "ANTET_ALANLARI", None)
        if alanlar is None:
            r.uyari("antet", "antet alanları programatik olarak listelenmiyor — "
                             "denetlenemedi")
        else:
            for z in zorunlu:
                if not any(z in a.upper() for a in alanlar):
                    r.hata("antet", f"antette '{z}' alanı yok",
                           dayanak="TMMOB MMO Proje Hazırlama ve Mesleki Denetim Esasları")
            r.bilgi("antet", f"antet {len(alanlar)} alan içeriyor")
