# -*- coding: utf-8 -*-
"""KOORDİNASYON DENETİM AJANI — disiplinler arası çakışma ve mantık denetimi.

kontrol.py'deki geometrik çakışma denetimini kapsar ve üzerine MEP
koordinasyon kurallarını ekler (servisler arası asgari açıklık, kablo tavası
erişim boşluğu, ıslak hacim koruma bölgeleri, ekipman–tesisat çakışması).
"""
import math
from shapely.geometry import Point, LineString
from .base import Ajan
import proj as P

ACIKLIK_MIN   = 0.025    # m — servis dış yüzeyleri arası asgari
ACIKLIK_IYI   = 0.050    # m — tercih edilen
TAVA_ERISIM   = 0.300    # m — kablo tavası üstü çekim boşluğu
ZAYIF_KUVVET  = 0.200    # m — zayıf akım ile kuvvet arası yatay ayrım
ARMATUR_MENFEZ= 0.300    # m — armatür ile menfez arası asgari
CIHAZ_CIHAZ   = 0.150    # m — duvar cihazları arası asgari
ISLAK_BOLGE_0 = 0.600    # m — duş süzgeci çevresi Bölge 1 yarıçapı (TS HD 60364-7-701)


class KoordinasyonAjani(Ajan):
    ad = "koordinasyon"
    baslik = "Disiplinler arası koordinasyon ve çakışma denetimi"

    def denetle(self, r):
        self._kontrol_py(r); self._tavan(r); self._cihaz(r); self._islak(r)
        self._ekipman(r)

    # 1 ── mevcut geometrik kontrol motorunu kapsa
    def _kontrol_py(self, r):
        try:
            import kontrol as K
            K.BULGU.clear()
            bulgular = K.calistir()
        except Exception as e:
            r.hata("kontrol", f"kontrol.py çalıştırılamadı: {type(e).__name__}: {e}")
            return
        n = {"HATA": 0, "UYARI": 0}
        for b in bulgular:
            sev, kat, msg = b[0], b[1], b[2]
            if sev == "HATA":
                r.hata(f"geo·{kat}", msg, dayanak="kontrol.py geometrik denetim")
            elif sev == "UYARI":
                r.uyari(f"geo·{kat}", msg, dayanak="kontrol.py geometrik denetim")
            n[sev] = n.get(sev, 0)+1
        r.bilgi("kontrol", f"kontrol.py: {len(bulgular)} bulgu "
                           f"({n.get('HATA',0)} hata, {n.get('UYARI',0)} uyarı)")

    # 2 ── asma tavan içi servis açıklıkları
    def _tavan(self, r):
        for tip, kat in P.TAVAN_KATMAN.items():
            serit = {}
            for k in kat: serit.setdefault(k[5], []).append(k)
            for srt, ks in serit.items():
                if srt == "*": continue
                s = sorted(ks, key=lambda k: -k[2])
                for a, b in zip(s, s[1:]):
                    ara = a[1]-b[2]
                    if ara < 0:
                        r.hata("açıklık", f"{tip}·{srt}: '{a[3]}' ile '{b[3]}' çakışıyor "
                                          f"({ara*1000:.0f} mm)")
                    elif ara < ACIKLIK_MIN:
                        r.hata("açıklık", f"{tip}·{srt}: '{a[3]}' ile '{b[3]}' arası "
                                          f"{ara*1000:.0f} mm — asgari {ACIKLIK_MIN*1000:.0f} mm",
                               dayanak="MEP koordinasyon — servis yüzeyleri arası asgari açıklık")
                    elif ara < ACIKLIK_IYI:
                        r.uyari("açıklık", f"{tip}·{srt}: '{a[3]}' ile '{b[3]}' arası "
                                           f"{ara*1000:.0f} mm — tercih edilen "
                                           f"{ACIKLIK_IYI*1000:.0f} mm")
            tava = [k for k in kat if k[4] == "kablo"]
            for t in tava:
                # erişim boşluğu yalnız AYNI yatay şeritte anlamlıdır
                ust = [k for k in kat if k[2] > t[2] and k[4] != "tavan"
                       and k[5] == t[5]]
                if ust:
                    bosluk = min(k[1] for k in ust) - t[2]
                    if bosluk < TAVA_ERISIM:
                        r.uyari("erişim", f"{tip}: kablo tavası üstünde {bosluk*1000:.0f} mm "
                                          f"boşluk — kablo çekimi için "
                                          f"{TAVA_ERISIM*1000:.0f} mm önerilir",
                                dayanak="MEP koordinasyon — tava çekim boşluğu")
        r.bilgi("açıklık", f"{sum(len(v) for v in P.TAVAN_KATMAN.values())} servis katmanı "
                           f"{len(P.TAVAN_KATMAN)} bölgede denetlendi")

    # 3 ── tavan cihazları arası mesafe (armatür / menfez / dedektör / hoparlör)
    def _cihaz(self, r):
        arm = []
        try:
            import helpers as h; h.register()
            import draw as D
            arm = [("AR", x, y) for x, y in D.aydinlatma_izgara()]
        except Exception as e:
            r.uyari("cihaz", f"armatür ızgarası okunamadı: {e}")
        menfez = [(m[0], m[1], m[2]) for m in P.MENFEZ]
        ded = [(d[0], d[1], d[2]) for d in P.DEDEKTOR]
        cakisma = 0
        for a in arm:
            for m in menfez:
                d = math.dist((a[1], a[2]), (m[1], m[2]))
                if d < ARMATUR_MENFEZ:
                    r.hata("cihaz", f"armatür ({a[1]:.2f}, {a[2]:.2f}) ile menfez {m[0]} "
                                    f"arası {d*100:.0f} cm — asgari "
                                    f"{ARMATUR_MENFEZ*100:.0f} cm")
                    cakisma += 1
        for d1 in ded:
            for m in menfez:
                if m[4:] and False: continue
                dd = math.dist((d1[1], d1[2]), (m[1], m[2]))
                if dd < 0.50:
                    r.hata("cihaz", f"duman dedektörü {d1[0]} menfez {m[0]}'e {dd*100:.0f} cm — "
                                    f"üfleme akımı dedektörü körleştirir (asgari 50 cm)",
                           dayanak="TS EN 54-14")
                    cakisma += 1
        if not cakisma:
            r.bilgi("cihaz", f"{len(arm)} armatür · {len(menfez)} menfez · {len(ded)} dedektör "
                             f"— tavan cihazları arası asgari mesafeler sağlanıyor")

    # 4 ── ıslak hacim bölge kuralları
    def _islak(self, r):
        sus = []
        for ad, d in P.ISLAK.items():
            sus.append(d["dus"].representative_point())
        priz44 = {p[0] for p in P.PRIZ_IP44}
        for kod, x, y, t, a in P.PRIZ_DUVAR:
            for s in sus:
                if math.dist((x, y), (s.x, s.y)) < ISLAK_BOLGE_0:
                    r.hata("ıslak", f"{kod} standart priz duş bölgesinde "
                                    f"({ISLAK_BOLGE_0*100:.0f} cm) — IP44 ve Bölge 2 dışı "
                                    f"zorunlu", dayanak="TS HD 60364-7-701")
        for kod, x, y, t, a in P.PRIZ_IP44:
            for s in sus:
                if math.dist((x, y), (s.x, s.y)) < 0.60:
                    r.uyari("ıslak", f"{kod} IP44 priz duş süzgecine "
                                     f"{math.dist((x,y),(s.x,s.y))*100:.0f} cm — Bölge 1 içinde "
                                     f"priz olamaz", dayanak="TS HD 60364-7-701")
        r.bilgi("ıslak", f"{len(priz44)} IP44 priz · {len(sus)} duş hacmi — bölge kuralları "
                         f"TS HD 60364-7-701'e göre denetlendi")

    # 5 ── ekipman ile tesisat/geçiş çakışması
    def _ekipman(self, r):
        try:
            import yol
        except Exception as e:
            r.uyari("ekipman", f"güzergâh motoru okunamadı: {e}"); return
        disarda = 0
        for e in P.EKIPMAN:
            konum = e[5]
            if isinstance(konum[0], (tuple, list)):   # çok adetli ekipman
                noktalar = list(konum)
            else:
                noktalar = [konum]
            disi = [p for p in noktalar if not P.SALON.buffer(0.05).contains(Point(*p))]
            if disi:
                x, y = disi[0]
                disarda += 1
                r.hata("ekipman", f"{e[0]} · {e[1][:46]} salon sınırı dışında "
                                  f"({x:.2f}, {y:.2f})")
        if not disarda:
            r.bilgi("ekipman", f"{len(P.EKIPMAN)} ekipman salon içinde · "
                               f"sirkülasyon serbest alanı {yol.SERBEST.area:.1f} m²")
