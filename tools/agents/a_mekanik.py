# -*- coding: utf-8 -*-
"""MEKANİK DENETİM AJANI — havalandırma, iklimlendirme ve sıhhi tesisat.

Dayanak: TS 3419 (Havalandırma ve İklimlendirme Tesisleri — Projelendirme),
TS 2164 §1.13 (tesisat sembolleri), TS 825, BYKHY, TS EN 16798-1,
ÇŞB Mimari Proje Düzenleme Esasları (asma tavan içi tesisat hakiki boyut).
"""
import math
from shapely.geometry import LineString, Point
from .base import Ajan
import proj as P

# ── projelendirme sınırları ───────────────────────────────────────────────────
KANAL_EN_BOY_MAX = 4.0       # W/H ≤ 1:4  (TS 3419 / uygulama)
HIZ_ANA_MAX      = 6.0       # m/s — ana kanal, konfor tesisi
HIZ_KOL_MAX      = 4.5       # m/s — kol kanal
HIZ_MENFEZ_MAX   = 2.5       # m/s — menfez boyun hızı (gürültü)
TAZE_HAVA_KISI   = 30.0      # m³/h·kişi — TS EN 16798-1 Kategori II alt sınır
ISLAK_EGZOZ_WC   = 30.0      # m³/h·adet — WC
ISLAK_EGZOZ_DUS  = 60.0      # m³/h·adet — duş
ACH_MIN          = 2.0       # 1/h — spor salonu asgari hava değişimi
EGIM_KUCUK       = 2.0       # % — Ø ≤ 70 atık
EGIM_BUYUK       = 1.0       # % — Ø ≥ 100 atık
DRENAJ_EGIM      = 1.0       # % — klima kondens
IZOLASYON_MM     = 25        # mm — kanal yalıtımı asgari
SERVIS_BOSLUK    = 1.00      # m — dış ünite önü servis boşluğu


def _ortogonal_mu(guzergah, tol=1e-6):
    kirik = []
    for a, b in zip(guzergah, guzergah[1:]):
        if abs(a[0]-b[0]) > tol and abs(a[1]-b[1]) > tol:
            kirik.append((a, b))
    return kirik


class MekanikAjani(Ajan):
    ad = "mekanik"
    baslik = "Mekanik tesisat — havalandırma, iklimlendirme, sıhhi tesisat denetimi"

    def denetle(self, r):
        self._kanal(r); self._debi(r); self._menfez(r); self._iklim(r)
        self._sihhi(r); self._sicaksu(r); self._koordinasyon(r)

    # 1 ── kanal geometrisi: en/boy oranı, hız, ortogonallik, yalıtım
    def _kanal(self, r):
        for ad, k in P.KANAL.items():
            kes = k["kesit"].replace(",", ".")
            if kes.startswith("Ø"):                       # yuvarlak kanal
                cap = float(kes[1:]); w = h = cap
                alan = math.pi*(cap/2000)**2; oran = 1.0
            else:
                w, h = (float(t) for t in kes.split("×"))
                alan = (w/1000)*(h/1000); oran = max(w, h)/min(w, h)
            if oran > KANAL_EN_BOY_MAX:
                r.hata("kanal", f"{ad} kanalı {k['kesit']} — en/boy oranı 1:{oran:.1f}, "
                                f"sınır 1:{KANAL_EN_BOY_MAX:.0f}", dayanak="TS 3419",
                       konum=f"kanal {ad}",
                       oneri="Kesiti yeniden boyutlandırın (ör. daha kare bir en/boy).")
            debi = float(k["debi"])
            hiz = debi/3600/alan
            sinir = HIZ_ANA_MAX if ad == "besleme" else HIZ_KOL_MAX
            if hiz > sinir:
                r.hata("kanal", f"{ad} kanalında hava hızı {hiz:.1f} m/s — sınır "
                                f"{sinir:.1f} m/s (gürültü ve basınç kaybı)",
                       konum=f"kanal {ad}")
            elif abs(hiz - float(k["hiz"])) > 0.35:
                r.uyari("kanal", f"{ad}: tabloda {k['hiz']} m/s yazıyor, kesit ve debiden "
                                 f"hesaplanan {hiz:.1f} m/s", konum=f"kanal {ad}")
            kirik = _ortogonal_mu(k["guzergah"])
            if kirik:
                r.uyari("kanal", f"{ad} kanal güzergâhında {len(kirik)} çapraz segment — "
                                 f"kanallar ortogonal döşenir, yön değişimi dirsek parçasıyla olur",
                        dayanak="Uygulama projesi çizim kuralı", konum=f"kanal {ad}",
                        oneri="Güzergâhı yatay/düşey kollara ayırıp dirsek ekleyin.")
            else:
                r.bilgi("kanal", f"{ad}: {k['kesit']} · {debi:.0f} m³/h · {hiz:.1f} m/s · "
                                 f"güzergâh ortogonal")
        r.bilgi("kanal", f"besleme {P.L_KANAL_B:.1f} m · egzoz {P.L_KANAL_E:.1f} m · "
                         f"ıslak {P.L_KANAL_I:.1f} m ana hat + {P.L_BRANS:.1f} m branşman")

    # 2 ── debi dengesi
    def _debi(self, r):
        besleme = sum(m[3] for m in P.MENFEZ if m[4] == "besleme")
        egzoz   = sum(m[3] for m in P.MENFEZ if m[4] == "egzoz")
        valf    = sum(m[3] for m in P.MENFEZ if m[4] == "valf")
        fan = {f[0]: f for f in P.FAN}
        def _fan_debi(kod):
            return float(fan[kod][3].split("—")[1].split("m³/h")[0].strip()
                         .replace(".", "").replace(",", "."))
        try:
            th, eg, isl = _fan_debi("F-TH"), _fan_debi("F-EG"), _fan_debi("F-IS")
        except Exception as e:
            r.hata("debi", f"fan debisi okunamadı: {e}"); return
        for ad, menfez, f in (("taze hava", besleme, th), ("egzoz", egzoz, eg),
                              ("ıslak hacim egzozu", valf, isl)):
            if f <= 0: continue
            sap = 100*abs(menfez-f)/f
            if sap > 10:
                r.hata("debi", f"{ad}: menfez toplamı {menfez:.0f} m³/h, fan kapasitesi "
                               f"{f:.0f} m³/h — %{sap:.0f} sapma",
                       oneri="Menfez debilerini veya fan seçimini eşitleyin.")
            else:
                r.bilgi("debi", f"{ad}: menfez {menfez:.0f} m³/h ≈ fan {f:.0f} m³/h "
                                f"(%{sap:.0f} sapma)")
        kisi = P.V["kisi_kapasite"][0] + P.V["personel"][0]
        gerek = kisi*TAZE_HAVA_KISI
        if th < gerek:
            r.hata("debi", f"taze hava {th:.0f} m³/h — {kisi} kişi için asgari "
                           f"{gerek:.0f} m³/h ({TAZE_HAVA_KISI:.0f} m³/h·kişi)",
                   dayanak="TS EN 16798-1")
        else:
            r.bilgi("debi", f"taze hava {th:.0f} m³/h = {th/kisi:.0f} m³/h·kişi "
                            f"({kisi} kişi) — asgari {TAZE_HAVA_KISI:.0f}")
        if P.ACH < ACH_MIN:
            r.hata("debi", f"hava değişimi {P.ACH:.2f} 1/h — asgari {ACH_MIN:.1f} 1/h")
        else:
            r.bilgi("debi", f"salon hava değişimi {P.ACH:.2f} 1/h")
        wc = sum(1 for m in P.MAHAL_LISTESI if "WC" in m[1])
        dus = sum(1 for m in P.MAHAL_LISTESI if "DUŞ" in m[1])
        gerek_i = wc*ISLAK_EGZOZ_WC + dus*ISLAK_EGZOZ_DUS
        if P.EGZOZ_ISLAK < gerek_i:
            r.hata("debi", f"ıslak hacim egzozu {P.EGZOZ_ISLAK} m³/h — {wc} WC + {dus} duş "
                           f"için asgari {gerek_i:.0f} m³/h")
        else:
            r.bilgi("debi", f"ıslak hacim egzozu {P.EGZOZ_ISLAK} m³/h ≥ gerekli "
                            f"{gerek_i:.0f} m³/h ({wc} WC + {dus} duş)")

    # 3 ── menfez: boyun hızı, konum, tip ayrımı
    def _menfez(self, r):
        boyun = {"besleme": 0.30*0.30, "egzoz": 0.30*0.30, "valf": math.pi*0.08**2}
        for kod, x, y, debi, tip in P.MENFEZ:
            A = boyun[tip]
            v = debi/3600/A
            if v > HIZ_MENFEZ_MAX:
                r.uyari("menfez", f"{kod}: boyun hızı {v:.1f} m/s — {HIZ_MENFEZ_MAX} m/s "
                                  f"üstü gürültü yapar", konum=f"menfez {kod}")
        b = [m for m in P.MENFEZ if m[4] == "besleme"]
        e = [m for m in P.MENFEZ if m[4] == "egzoz"]
        if not b or not e:
            r.hata("menfez", "besleme veya egzoz menfezi tanımlı değil")
        # besleme–egzoz kısa devresi: aynı menfez çiftinin arası ≥ 2,0 m olmalı
        for mb in b:
            for me in e:
                d = math.dist((mb[1], mb[2]), (me[1], me[2]))
                if d < 2.0:
                    r.uyari("menfez", f"{mb[0]} ile {me[0]} arası {d:.2f} m — besleme/egzoz "
                                      f"kısa devresi riski (asgari 2,0 m)")
        r.bilgi("menfez", f"{len(b)} besleme · {len(e)} egzoz · "
                          f"{len([m for m in P.MENFEZ if m[4]=='valf'])} ıslak hacim valfi")

    # 4 ── iklimlendirme: kapasite, bakır hat, drenaj, dış ünite
    def _iklim(self, r):
        zon_alan = {z[0]: z[1].area for z in P.ZONES}
        for kod, zon, btu, pt, aci in P.KLIMA:
            alan = zon_alan.get(zon)
            if not alan: continue
            w_m2 = btu*0.293/alan
            if w_m2 < 90:
                r.uyari("iklim", f"{kod} ({zon}): {btu:,} BTU / {alan:.1f} m² = "
                                 f"{w_m2:.0f} W/m² — spor salonu için düşük"
                        .replace(",", "."), konum=f"klima {kod}")
            elif w_m2 > 300:
                r.uyari("iklim", f"{kod} ({zon}): {w_m2:.0f} W/m² — aşırı boyutlandırma "
                                 f"(kısa çevrim, nem alma zayıflar)", konum=f"klima {kod}")
            else:
                r.bilgi("iklim", f"{kod} {zon}: {btu} BTU → {w_m2:.0f} W/m² ({alan:.1f} m²)")
            if P.KLIMA_KOT + 0.32 > P.TAVAN_KOT.get("T1", 3.2):
                r.hata("iklim", f"{kod} iç ünite üst kotu tavanı aşıyor", konum=f"klima {kod}")
        for kod, hat in P.DRENAJ.items():
            if len(hat) < 2:
                r.hata("iklim", f"{kod} drenaj hattı tanımsız"); continue
            L = LineString(hat).length
            dusme = L*DRENAJ_EGIM/100
            if dusme > 0.35:
                r.uyari("iklim", f"{kod} drenaj hattı {L:.1f} m — %{DRENAJ_EGIM:.0f} eğimle "
                                 f"{dusme*1000:.0f} mm düşme gerekir; tavan boşluğunu zorlar",
                        konum=f"drenaj {kod}",
                        oneri="Kondens pompası kullanın veya hattı kısaltın.")
        for kod, hat in P.BAKIR_HAT.items():
            L = LineString(hat).length
            if L > 50:
                r.hata("iklim", f"{kod} bakır hat {L:.0f} m — split sistem sınırı 50 m",
                       konum=f"bakır hat {kod}")
            elif L > 30:
                r.uyari("iklim", f"{kod} bakır hat {L:.0f} m — 30 m üstünde ilave gaz şarjı "
                                 f"ve kapasite düzeltmesi gerekir", konum=f"bakır hat {kod}")
        dis = Point(*P.DIS_UNITE)
        ic = P.SALON.union(P.ERKEK).union(P.KADIN)
        if ic.contains(dis):
            r.hata("iklim", "dış ünite yapı içinde konumlanmış")
        else:
            r.bilgi("iklim", f"dış ünite {P.DIS_UNITE} — yapı dışında, "
                             f"{SERVIS_BOSLUK:.2f} m servis boşluğu paftada taranmalı")
        r.bilgi("iklim", f"{len(P.KLIMA)} iç ünite · toplam {P.KLIMA_BTU:,} BTU · "
                         f"bakır hat {P.L_BAKIR:.1f} m · drenaj {P.L_DRENAJ:.1f} m"
                .replace(",", "."))

    # 5 ── sıhhi tesisat: çap–eğim, ortogonallik, süzgeç
    def _sihhi(self, r):
        for cap, hatlar in P.PIS_SU.items():
            capmm = float(cap.replace("Ø", ""))
            gerek = EGIM_KUCUK if capmm <= 70 else EGIM_BUYUK
            hl = hatlar if isinstance(hatlar[0][0], (tuple, list)) else [hatlar]
            toplam = 0.0
            for h in hl:
                L = LineString(h).length; toplam += L
            r.bilgi("sıhhi", f"pis su {cap}: {toplam:.1f} m · gerekli eğim "
                             f"%{gerek:.0f} (Ø≤70 → %2, Ø≥100 → %1)")
            dus = toplam*gerek/100
            if capmm >= 100 and dus > 0.30:
                r.uyari("sıhhi", f"{cap} hattı {toplam:.1f} m — %{gerek:.0f} eğimle "
                                 f"{dus*1000:.0f} mm düşme; tesisat şapı kalınlığı kontrol edilmeli",
                        konum=f"pis su {cap}")
        r.bilgi("sıhhi", f"temiz su Ø20 {P.L_TEMIZ20:.1f} m · Ø25 {P.L_TEMIZ25:.1f} m · "
                         f"sıcak su {P.L_SICAK:.1f} m")
        if P.L_PIS100 <= 0:
            r.hata("sıhhi", "Ø100 ana atık hattı tanımlı değil")

    # 6 ── sıcak su kapasitesi
    def _sicaksu(self, r):
        dus = sum(1 for m in P.MAHAL_LISTESI if "DUŞ" in m[1])
        DUS_DEBI = 8.0      # l/dak · 40 °C karışık su — tasarruflu başlık
        DUS_SURE = 8.0      # dak — ardışık iki duş için tasarım kabulü
        for kod, x, y, ad, aci in P.ISITICI:
            kw = float(ad.split("kW")[0].split()[-1].replace(",", "."))
            depo = None
            if " L " in ad:
                depo = float(ad.split(" L ")[0].split()[-1].replace(",", "."))
            if depo is None:
                # ani ısıtıcı: ΔT 30 K'de sürekli debi
                debi = kw*860/(30*60)
                if debi < DUS_DEBI/2:
                    r.hata("sıcak su", f"{kod}: {kw:.0f} kW ani ısıtıcı ΔT 30 K'de yalnız "
                                       f"{debi:.1f} l/dak verir — duş için {DUS_DEBI:.0f} l/dak "
                                       f"gerekir", konum=f"ısıtıcı {kod}",
                           oneri="Depolu boyler seçin veya kapasiteyi artırın.")
                else:
                    r.bilgi("sıcak su", f"{kod}: {kw:.0f} kW → {debi:.1f} l/dak @ΔT 30 K")
                continue
            # depolu boyler: 60 °C depo, 40 °C kullanım, 10 °C şebeke
            kullanilabilir = depo*(60-10)/(40-10)          # l, 40 °C eşdeğeri
            gerek = DUS_DEBI*DUS_SURE*2                     # iki ardışık duş
            isinma = depo*(60-10)*1.163/1000/kw*60          # dak — sıfırdan ısınma
            if kullanilabilir < gerek:
                r.uyari("sıcak su", f"{kod}: {depo:.0f} L depo 40 °C'de {kullanilabilir:.0f} L "
                                    f"verir — iki ardışık duş için {gerek:.0f} L gerekir "
                                    f"(ısınma {isinma:.0f} dak)", konum=f"ısıtıcı {kod}")
            else:
                r.bilgi("sıcak su", f"{kod}: {depo:.0f} L / {kw:.0f} kW → 40 °C'de "
                                    f"{kullanilabilir:.0f} L kullanılabilir "
                                    f"(gerekli {gerek:.0f} L) · ısınma {isinma:.0f} dak")
        if len(P.ISITICI) < dus/2:
            r.uyari("sıcak su", f"{dus} duş için {len(P.ISITICI)} ısıtıcı")

    # 7 ── koordinasyon: asma tavan istifi ve kanal yalıtımı
    def _koordinasyon(self, r):
        for tip, kat in P.TAVAN_KATMAN.items():
            kanal = [k for k in kat if k[4] == "kanal"]
            for k in kanal:
                if "izolasyon" not in k[3].lower() and "izol" not in k[3].lower():
                    r.uyari("koordinasyon", f"{tip}: '{k[3]}' yalıtım belirtilmemiş — "
                                            f"asgari {IZOLASYON_MM} mm", konum=f"tavan {tip}")
            ust = max(k[2] for k in kat)
            if ust > P.KOT_YAPISAL_TAVAN:
                r.hata("koordinasyon", f"{tip}: tesisat üst kotu {ust:.2f} m yapısal tavanı "
                                       f"({P.KOT_YAPISAL_TAVAN:.2f} m) aşıyor")
            # öncelik sırası: eğimli hat > kanal > basınçlı boru > kablo (MEP koordinasyonu)
            sira = [k[4] for k in sorted(kat, key=lambda k: -k[2]) if k[4] != "tavan"]
            if sira and sira[0] != "kanal":
                r.uyari("koordinasyon", f"{tip}: en üstte '{sira[0]}' var — en büyük kesitli "
                                        f"ve eğimsiz eleman olan kanal döşemeye en yakın "
                                        f"yerleştirilir", konum=f"tavan {tip}")
        r.bilgi("koordinasyon", "tavan istifi şerit bazlı: A kanal · B mekanik boru · "
                                "C kuvvet · D zayıf akım")
