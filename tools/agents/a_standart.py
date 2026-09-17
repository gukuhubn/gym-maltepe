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
        for no, (ad, dis, donan) in pf.items():
            disiplinler.setdefault(dis, []).append(no)
            if not donan:
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
