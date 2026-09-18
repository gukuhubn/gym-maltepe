# -*- coding: utf-8 -*-
"""MİMARİ DENETİM AJANI — mahal, kot, katman, doğrama, tahliye, karkas."""
from .base import Ajan
import proj as P

# — yönetmelik eşikleri ————————————————————————————————————————————————
NET_YUKSEKLIK_MIN = 2.40    # m — Planlı Alanlar İmar Yön. md.28 (ıslak hacim/koridor)
SALON_YUKSEKLIK_MIN = 2.60  # m — spor/çalışma hacmi için proje kabulü
KAPI_TAHLIYE_MIN = 800      # mm — BYKHY md.32 kaçış kapısı net genişliği
KAPI_WC_MIN = 700           # mm
TAHLIYE_SINIR = 45.0        # m — BYKHY md.33 tek yönlü kaçış mesafesi (sprinklersiz)
DIKME_ARA_MAX = 0.60        # m — TS EN 520 / üretici: 60 cm üstü kabul edilmez
LEVHA_MIN_MM = 12.5         # mm
ISLAK_LEVHA = ("su itici", "yeşil", "H2", "impregne")


class MimariAjani(Ajan):
    ad = "mimari"
    baslik = "Mimari proje — mahal, kot, katman ve imalat denetimi"

    def denetle(self, r):
        self._mahal(r); self._kot(r); self._tavan(r); self._dograma(r)
        self._tahliye(r); self._karkas(r); self._islak(r); self._pafta(r)

    # 1 ── mahal listesi ↔ geometri ↔ tip tabloları
    def _mahal(self, r):
        zt = {z[0] for z in P.ZEMIN_TIPLERI}
        dt = {d[0] for d in P.DUVAR_TIPLERI}
        tt = {t[0] for t in P.TAVAN_TIPLERI}
        st = {s[0] for s in P.SUPURGELIK}
        for m in P.MAHAL_LISTESI:
            no, ad, alan, z, s, d, t, h = m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7]
            for kod, kume, nm in ((z, zt, "zemin"), (s, st, "süpürgelik"),
                                  (t, tt, "tavan")):
                if kod not in kume:
                    r.hata("mahal", f"{no} {ad}: tanımsız {nm} tipi '{kod}'",
                           konum=f"mahal {no}",
                           oneri=f"{nm} tip tablosuna {kod} eklenmeli veya mahal düzeltilmeli.")
            import re as _re
            for kod in _re.findall(r"\bD\d+\b", str(d)):
                if kod not in dt:
                    r.hata("mahal", f"{no} {ad}: tanımsız duvar tipi '{kod}'",
                           konum=f"mahal {no}")
            sinir = SALON_YUKSEKLIK_MIN if alan >= 20 else NET_YUKSEKLIK_MIN
            if h < sinir:
                r.hata("yükseklik",
                       f"{no} {ad}: net yükseklik {h:.2f} m — asgari {sinir:.2f} m",
                       dayanak="Planlı Alanlar İmar Yönetmeliği md.28",
                       konum=f"mahal {no}")
        fark = abs(P.MAHAL_TOPLAM + P.MAHAL_DUVAR_PAYI - P.A["ic_toplam"])
        if fark > 0.6:
            r.hata("alan", f"mahal alanları toplamı {P.MAHAL_TOPLAM:.2f} + duvar payı "
                           f"{P.MAHAL_DUVAR_PAYI:.2f} ≠ iç alan {P.A['ic_toplam']:.2f} m² "
                           f"(fark {fark:.2f})")
        else:
            r.bilgi("alan", f"{len(P.MAHAL_LISTESI)} mahal · {P.MAHAL_TOPLAM:.2f} m² net "
                            f"+ {P.MAHAL_DUVAR_PAYI:.2f} m² duvar = {P.A['ic_toplam']:.2f} m² iç alan")

    # 2 ── kot dizgesi: bitmiş kot = mevcut şap + katman kalınlığı
    def _kot(self, r):
        for z in P.ZEMIN_TIPLERI:
            kod, ad, katman, kot = z[0], z[1], z[2], z[3]
            tk = sum(k[1] for k in katman)
            bekl = P.ZEMIN_KALINLIK.get(kod)
            if bekl is not None and abs(tk - bekl) > 1:
                r.hata("kot", f"{kod}: katman toplamı {tk} mm ≠ tablo {bekl} mm",
                       konum=f"detay {kod}")
            taban = P.ZEMIN_TABAN.get(kod, P.KOT_MEVCUT_SAP)
            hesap = round(taban + tk/1000, 3)
            if abs(hesap - kot) > 0.006:
                r.uyari("kot", f"{kod}: hesaplanan bitmiş kot {hesap:+.3f} ≠ "
                               f"tabloda {kot:+.3f} m", konum=f"detay {kod}")
        r.bilgi("kot", f"mevcut şap kotu {P.KOT_MEVCUT_SAP:+.3f} · ıslak hacim taban "
                       f"{P.KOT_ISLAK:+.3f} · yapısal tavan {P.KOT_YAPISAL_TAVAN:+.2f} m")

    # 3 ── asma tavan boşluğu tesisatı alıyor mu
    def _tavan(self, r):
        for tip, katman in P.TAVAN_KATMAN.items():
            serb = P.TAVAN_SERBESTLIK.get(tip)
            if serb is None: continue
            if serb < 0:
                r.hata("tavan", f"{tip}: asma tavan boşluğu {P.TAVAN_BOSLUK[tip]*1000:.0f} mm "
                                f"tesisat istifini almıyor — eksik {abs(serb):.0f} mm",
                       konum=f"tavan tipi {tip}",
                       oneri="Tavan kotunu düşürün veya kanal kesitini değiştirin.")
            elif serb < 25:
                r.uyari("tavan", f"{tip}: tesisat istifi üstünde yalnız {serb:.0f} mm "
                                 f"boşluk var — montaj toleransı 25 mm'nin altında",
                        dayanak="MEP koordinasyon pratiği: servisler arası asgari 25 mm")
            else:
                r.bilgi("tavan", f"{tip}: {P.TAVAN_BOSLUK[tip]*1000:.0f} mm boşluk · "
                                 f"{len(katman)} servis katmanı · {serb:.0f} mm serbestlik")
            # katmanlar çakışıyor mu
            # düşey çakışma yalnızca AYNI yatay şeritte anlamlıdır (MEP koordinasyonu:
            # önce yatay ayrıştırma, sonra düşey sınır)
            seritler = {}
            for k in katman: seritler.setdefault(k[5], []).append(k)
            for srt, kat in seritler.items():
                if srt == "*": continue
                sirali = sorted(kat, key=lambda k: -k[2])
                for a, b in zip(sirali, sirali[1:]):
                    if b[2] > a[1] + 1e-9:
                        r.hata("tavan", f"{tip} · şerit {srt}: '{a[3]}' ile '{b[3]}' "
                                        f"düşey olarak çakışıyor", konum=f"tavan tipi {tip}")
            kullanim = ", ".join(f"{k}:{len(v)}" for k, v in sorted(seritler.items()))
            r.bilgi("tavan", f"{tip} yatay şerit dağılımı — {kullanim}")

    # 4 ── doğrama: kaçış genişlikleri, ıslak hacim kapıları
    def _dograma(self, r):
        tahliye = {"K01", "K02"}
        for k in P.KAPI_LISTESI:
            kod, ad, gen, yuk = k[0], k[2], k[3], k[4]
            if kod in tahliye and gen < KAPI_TAHLIYE_MIN:
                r.hata("doğrama", f"{kod} {ad}: kaçış kapısı net {gen} mm — asgari "
                                  f"{KAPI_TAHLIYE_MIN} mm", dayanak="BYKHY md.32")
            if gen < KAPI_WC_MIN:
                r.hata("doğrama", f"{kod} {ad}: kapı genişliği {gen} mm — asgari "
                                  f"{KAPI_WC_MIN} mm")
            if yuk < 1900:
                r.uyari("doğrama", f"{kod} {ad}: kapı yüksekliği {yuk} mm — 1900 mm altı")
        # kapı listesi ↔ plan geometrisi eşleşmesi (talimat §11: "listeler
        # çizimle uyuşuyor mu"). Liste ile plan arasındaki sessiz kopukluk
        # K05–K08'de fiilen yaşandı: kapılar cetvelde vardı, planda yoktu.
        haric = getattr(P, "KAPI_GEOM_HARIC", {})
        geom = getattr(P, "KAPI_GEOM", {})
        for k in P.KAPI_LISTESI:
            kod = k[0]
            if kod in geom or kod in haric: continue
            r.hata("doğrama", f"{kod} {k[2]}: kapı cetvelinde var, planda geometrisi yok",
                   dayanak="liste ↔ çizim tutarlılığı")
        fazla = [g for g in geom if g not in {k[0] for k in P.KAPI_LISTESI}]
        for g in fazla:
            r.hata("doğrama", f"{g}: planda çizili, kapı cetvelinde yok")
        # planda çizilen kapı, bağlı olduğu mahallin çeperinde mi?
        from shapely.geometry import Point as _Pt
        for kod, (pt, gen, aci) in geom.items():
            if kod in ("K01", "K02"): continue
            q = _Pt(*pt)
            if all(g.exterior.distance(q) > 0.25 for _, _, g in P._MAHAL_GEOM):
                r.uyari("doğrama", f"{kod}: kapı hiçbir mahal çeperine oturmuyor "
                                   f"({pt[0]:.2f}, {pt[1]:.2f})")
        for kod, gerekce in haric.items():
            r.bilgi("doğrama", f"{kod}: plan geometrisi aranmaz — {gerekce}")
        r.bilgi("doğrama", f"{len(P.KAPI_LISTESI)} kapı ({len(geom)} planda çizili · "
                           f"{len(haric)} mobilya) · {len(P.PENCERE_LISTESI)} "
                           f"doğrama kalemi listelendi")

    # 5 ── tahliye
    def _tahliye(self, r):
        if P.TAHLIYE_MAX > TAHLIYE_SINIR:
            r.hata("tahliye", f"en uzun kaçış mesafesi {P.TAHLIYE_MAX:.1f} m — "
                              f"sınır {TAHLIYE_SINIR:.0f} m", dayanak="BYKHY md.33")
        else:
            r.bilgi("tahliye", f"{len(P.CIKISLAR)} çıkış · en uzun kaçış "
                               f"{P.TAHLIYE_MAX:.1f} m ≤ {TAHLIYE_SINIR:.0f} m")

    # 6 ── alçıpan karkas
    def _karkas(self, r):
        try:
            import draw_duvar as DD
        except Exception as e:
            r.hata("karkas", f"draw_duvar yüklenemedi: {e}"); return
        if DD.DIKME_ARA > DIKME_ARA_MAX:
            r.hata("karkas", f"dikme aralığı {DD.DIKME_ARA*100:.0f} cm — azami "
                             f"{DIKME_ARA_MAX*100:.0f} cm",
                   dayanak="TS EN 520 / üretici uygulama detayı")
        if DD.LEVHA*1000 < LEVHA_MIN_MM:
            r.hata("karkas", f"levha kalınlığı {DD.LEVHA*1000:.1f} mm — asgari "
                             f"{LEVHA_MIN_MM} mm")
        try:
            karkasli = set(b[2] for b in DD.BOLME)
        except Exception:
            karkasli = {"D2", "D3"}
        karkasli |= {d[0] for d in P.DUVAR_TIPLERI if "giydirme" in d[1].lower()
                     and "ayna" not in d[1].lower()}
        tipler = [d for d in P.DUVAR_TIPLERI if d[0] != "D1"]
        for d in tipler:
            kod, ad, kal, katman = d[0], d[1], d[2], d[3]
            tk = sum(k[1] for k in katman)
            if abs(tk - kal) > 1:
                r.hata("karkas", f"{kod}: katman toplamı {tk} mm ≠ tablo kalınlığı {kal} mm",
                       konum=f"duvar tipi {kod}")
            if kod in karkasli and not any(
                    "profil" in k[0].lower() or "dikme" in k[0].lower()
                    or "C50" in k[0] or "C75" in k[0] or "C100" in k[0]
                    for k in katman):
                r.hata("karkas", f"{kod}: katman listesinde taşıyıcı profil yok — "
                                 f"alçıpan duvar karkassız tarif edilemez",
                       konum=f"duvar tipi {kod}",
                       oneri="C profil + U ray katmanı tip tarifine eklenmeli.")
        r.bilgi("karkas", f"{len(DD.BOLME)} bölme ekseni · {DD.BOLME_UZUNLUK:.2f} m · "
                          f"{DD.DIKME_ADEDI} adet {DD.PROFIL['C50']['ad']} dikme "
                          f"@{DD.DIKME_ARA*1000:.0f} mm")

    # 7 ── ıslak hacim
    def _islak(self, r):
        islak_mahal = [m for m in P.MAHAL_LISTESI if m[3] == "Z4"]
        if not islak_mahal:
            r.hata("ıslak", "Z4 (su yalıtımlı) zemin tipine bağlı mahal yok")
        for m in islak_mahal:
            if m[6] != "T3":
                r.uyari("ıslak", f"{m[0]} {m[1]}: ıslak hacimde tavan tipi {m[6]} — "
                                 f"neme dayanıklı T3 bekleniyor", konum=f"mahal {m[0]}")
        z4 = next((z for z in P.ZEMIN_TIPLERI if z[0] == "Z4"), None)
        if z4 and not any("yalıtım" in k[0].lower() for k in z4[2]):
            r.hata("ıslak", "Z4 katman listesinde su yalıtımı yok",
                   dayanak="TS EN 14891 · Su Yalıtımı Yönetmeliği")
        d_islak = [d for d in P.DUVAR_TIPLERI
                   if "ıslak" in d[1].lower() or "duş" in d[1].lower() or "wc" in d[1].lower()]
        for d in d_islak:
            # giydirme tipleri altlığı üzerinden uygundur (ör. D5 altlığı D3 ıslak yüzü)
            altlik_ok = any("D3" in k[0] or "mevcut duvar" in k[0].lower() for k in d[3])
            if not altlik_ok and not any(any(t in k[0].lower() for t in ISLAK_LEVHA)
                                         for k in d[3]):
                r.uyari("ıslak", f"{d[0]} {d[1]}: su itici (H2/yeşil) levha belirtilmemiş",
                        konum=f"duvar tipi {d[0]}")
        r.bilgi("ıslak", f"{len(islak_mahal)} ıslak hacim · Z4 su yalıtımlı zemin · "
                         f"{len(d_islak)} ıslak duvar tipi")

    # 8 ── pafta bütünlüğü
    def _pafta(self, r):
        for ad, hat in P.KESIT_HATLARI.items():
            if ad not in P.KESIT_BAKIS:
                r.hata("pafta", f"{ad} kesitinin bakış yönü tanımlı değil")
        if len(P.KESIT_HATLARI) < 2:
            r.hata("pafta", "en az iki doğrultuda kesit gerekir (boyuna + enine)")
        if len(P.IC_GORUNUS) < 4:
            r.uyari("pafta", f"yalnız {len(P.IC_GORUNUS)} iç görünüş — ıslak hacim ve "
                             f"banko duvarları için en az 4 beklenir")
        if len(P.DETAYLAR) < 6:
            r.uyari("pafta", f"yalnız {len(P.DETAYLAR)} detay tanımlı")
        r.bilgi("pafta", f"{len(P.KESIT_HATLARI)} kesit · {len(P.IC_GORUNUS)} iç görünüş · "
                         f"{len(P.DETAYLAR)} detay · {len(P.YIKIM)} yıkım kalemi")


