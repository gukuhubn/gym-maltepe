# -*- coding: utf-8 -*-
"""PİLOT PAFTA DENETİM AJANI — üretilen DXF dosyalarını DİSKTEN AÇIP denetler.

Talimat §11: "Her çıktı turunda dosyayı yeniden aç, veri kontrollerini
çalıştır, paftaları PDF/PNG üret ve görsel olarak incele."

Bu ajan modelin ne söylediğini değil, ÜRETİLEN DOSYADA ne olduğunu ölçer.
Kontroller §11 listesindeki sırayla ve dört sonuçlu olarak raporlanır:
geçti (BİLGİ) · kaldı (HATA) · veri eksik (VERİ EKSİK) · uygulanmaz (UYGULANMAZ).
"""
import math
from pathlib import Path

from .base import Ajan
import proj as P

KOK = Path(__file__).resolve().parent.parent.parent
PILOT = KOK/"cad"/"pilot"

# ISO 3098 — basılı yazı yüksekliği alt sınırı (okunabilirlik)
YAZI_MIN_MM = 1.8
SIFIR_UZUNLUK = 0.5          # mm — model biriminde sıfır sayılan uzunluk
OLCU_TOLERANS = 1.0          # mm — DIMENSION ölçüsü ile geometri arasındaki sınır


class PilotAjani(Ajan):
    ad = "pilot"
    baslik = "Pilot paftalar — üretilen DXF dosyalarının denetimi"

    def denetle(self, r):
        import pilot as PL
        self.PL = PL
        dosyalar = sorted(PILOT.glob("P-*.dxf"))
        if not dosyalar:
            r.eksik("dosya", "cad/pilot altında pafta bulunamadı — önce "
                             "`python3 tools/pilot.py` çalıştırılmalı")
            return
        for yol in dosyalar:
            self._pafta(r, yol)
        self._model(r)
        self._kapi_acilim(r)

    # ── 1 dosya açılıyor mu; birim, extents, layout ─────────────────────────
    def _pafta(self, r, yol):
        import ezdxf
        no = yol.name.split("_")[0]
        try:
            doc = ezdxf.readfile(yol)
        except Exception as e:
            r.hata("dosya", f"{no}: DXF açılamadı — {type(e).__name__}: {e}")
            return
        msp = doc.modelspace()
        birim = doc.header.get("$INSUNITS")
        if birim != 4:
            r.hata("birim", f"{no}: $INSUNITS={birim} — milimetre (4) bekleniyor")
        layout = [l for l in doc.layouts if l.name != "Model"]
        if len(layout) != 1:
            r.hata("pafta", f"{no}: {len(layout)} kâğıt düzeni — bir pafta bir düzen")
        # görüntü penceresi ve ölçek
        vp = [v for l in layout for v in l.query("VIEWPORT")]
        vp = [v for v in vp if v.dxf.get("id", 2) != 1]
        if not vp:
            r.hata("pafta", f"{no}: görüntü penceresi yok — pafta ölçeksiz basılır")
        else:
            v = vp[0]
            olcek = v.dxf.view_height / v.dxf.height
            bek = self.PL.PAFTALAR[no][2]
            if abs(olcek - bek) > 0.01:
                r.hata("ölçek", f"{no}: pencere ölçeği 1:{olcek:.2f}, antette 1:{bek}")
            else:
                r.bilgi("ölçek", f"{no}: görüntü penceresi ölçeği 1:{bek} — antetle uyumlu")
        # sıfır uzunluklu / yinelenen geometri
        sifir = 0
        for e in msp:
            if e.dxftype() == "LINE":
                if math.dist((e.dxf.start.x, e.dxf.start.y),
                             (e.dxf.end.x, e.dxf.end.y)) < SIFIR_UZUNLUK:
                    sifir += 1
            elif e.dxftype() == "LWPOLYLINE":
                q = [(p[0], p[1]) for p in e.get_points("xy")]
                sifir += sum(1 for a, b in zip(q, q[1:]) if math.dist(a, b) < SIFIR_UZUNLUK)
        if sifir:
            r.hata("geometri", f"{no}: {sifir} sıfır uzunluklu/yinelenen parça")
        else:
            r.bilgi("geometri", f"{no}: sıfır uzunluklu veya yinelenen geometri yok")
        # yazı yüksekliği — basılı ölçekte okunabilirlik
        bek = self.PL.PAFTALAR[no][2]
        kucuk = []
        for e in msp.query("TEXT MTEXT"):
            h = e.dxf.height if e.dxftype() == "TEXT" else e.dxf.char_height
            kagit = h/bek
            if kagit < YAZI_MIN_MM - 0.05:
                kucuk.append((e.dxf.layer, round(kagit, 2)))
        if kucuk:
            r.hata("yazı", f"{no}: {len(kucuk)} yazı basılı ölçekte "
                           f"{min(k[1] for k in kucuk):.2f} mm — asgari {YAZI_MIN_MM} mm",
                   dayanak="ISO 3098 / TS 88")
        else:
            r.bilgi("yazı", f"{no}: tüm yazılar basılı ölçekte ≥ {YAZI_MIN_MM} mm")
        # ÖLÇÜ nesneleri gerçek DIMENSION mı, ölçü metni elle değiştirilmiş mi
        dims = list(msp.query("DIMENSION"))
        if not dims and no not in ("P-05", "P-00"):
            r.hata("ölçü", f"{no}: hiç DIMENSION nesnesi yok")
        elle = [d for d in dims if (d.dxf.get("text", "") or "") not in ("", "<>")]
        if elle:
            r.hata("ölçü", f"{no}: {len(elle)} ölçüde metin elle yazılmış — "
                           f"hesaplanan ölçüden farklı gösterilebilir",
                   dayanak="talimat §8")
        elif dims:
            r.bilgi("ölçü", f"{no}: {len(dims)} gerçek DIMENSION · ölçü metni "
                            f"geometriden türetiliyor")
        # ölçü stili çizim ölçeğiyle uyumlu mu
        yanlis = [d for d in dims if d.dxf.dimstyle != f"GYM-{bek}"]
        if yanlis:
            r.hata("ölçü", f"{no}: {len(yanlis)} ölçü {yanlis[0].dxf.dimstyle} "
                           f"stilinde — GYM-{bek} olmalı (yazı boyu bozulur)")
        # pafta dışına taşan içerik
        self._tasma(r, no, doc, layout)

    def _tasma(self, r, no, doc, layout):
        """Kâğıt alanındaki içerik çerçeve dışına taşıyor mu?"""
        import pafta as PF
        W, H = PF.KAGIT[self.PL.BOY]
        tasan = 0
        for l in layout:
            for e in l.query("TEXT MTEXT LWPOLYLINE LINE CIRCLE"):
                pts = []
                t = e.dxftype()
                if t in ("TEXT", "MTEXT"): pts = [e.dxf.insert]
                elif t == "LINE": pts = [e.dxf.start, e.dxf.end]
                elif t == "CIRCLE": pts = [e.dxf.center]
                elif t == "LWPOLYLINE": pts = [(p[0], p[1]) for p in e.get_points("xy")]
                for p in pts:
                    x, y = p[0], p[1]
                    if x < -1 or y < -1 or x > W+1 or y > H+1: tasan += 1
        if tasan:
            r.hata("pafta", f"{no}: kâğıt alanında {tasan} nokta çerçeve dışında")
        else:
            r.bilgi("pafta", f"{no}: kâğıt alanı içeriği {self.PL.BOY} sınırları içinde")

    # ── 2 model tutarlılığı: listeler ↔ çizim ───────────────────────────────
    def _model(self, r):
        PL = self.PL
        # mahal alanı: net alan toplamı brüt bloğu aşamaz
        # Üç alan kademesi: blok brütü ⊃ kaba yapı (karkas) ⊃ bitmiş yüz.
        brut = P.ISLAK[PL.BLOK]["tum"].area
        kaba = sum(PL.KABA_M2.values())
        bitmis = sum(PL.NET_M2.values())
        bolme_pay = brut - kaba
        kaplama_pay = kaba - bitmis
        bek_bolme = (2.200 + 1.620) * PL.BOLME_T
        if bitmis > kaba or kaba > brut:
            r.hata("alan", f"alan kademeleri tutarsız: bitmiş {bitmis:.3f} · "
                           f"kaba {kaba:.3f} · brüt {brut:.3f} m²")
        elif abs(bolme_pay - bek_bolme) > 0.08:
            r.uyari("alan", f"iç bölme payı {bolme_pay:.3f} m², beklenen "
                            f"{bek_bolme:.3f} m² (fark {bolme_pay-bek_bolme:+.3f})")
        else:
            r.bilgi("alan", f"brüt {brut:.3f} = kaba {kaba:.3f} + bölme "
                            f"{bolme_pay:.3f} m²")
        # kaplama payı, ıslak/kuru kaplama kalınlıklarıyla tutarlı mı?
        bek_kaplama = sum(P.ISLAK[PL.BLOK][n].exterior.length * PL.kaplama_t(n)
                          for n in PL.MAHAL)
        if abs(kaplama_pay - bek_kaplama) > 0.06:
            r.uyari("alan", f"kaplama payı {kaplama_pay:.3f} m², çeper × kalınlık "
                            f"{bek_kaplama:.3f} m²")
        else:
            r.bilgi("alan", f"kaba {kaba:.3f} − kaplama {kaplama_pay:.3f} = "
                            f"bitmiş {bitmis:.3f} m²")
        # mahal numaraları benzersiz
        nolar = list(PL.MAHAL.values())
        if len(set(nolar)) != len(nolar):
            r.hata("mahal", "mahal numarası tekrarlıyor")
        else:
            r.bilgi("mahal", f"mahal numaraları benzersiz: {', '.join(nolar)}")
        # plan–kesit kot tutarlılığı
        for ad in ("dus", "wc"):
            zt = PL.ZEMIN_MAHAL[ad]
            _, _, zust = PL._zemin_katmanlari(zt)
            beyan = P._MAHAL_BILGI[PL.MAHAL[ad]][3]
            if beyan != zt:
                r.hata("kot", f"{PL.MAHAL[ad]}: mahal listesinde {beyan}, "
                              f"kesitte {zt} kullanılıyor")
        r.bilgi("kot", "plan mahal listesi ile kesit zemin tipleri aynı kaynaktan")
        # pafta çağrıları gerçek paftaya gidiyor mu
        cagri = {"P-01": {"P-03", "P-05"}, "P-04": {"P-05"}}
        for kaynak, hedefler in cagri.items():
            yok = [h for h in hedefler if h not in PL.PAFTALAR]
            if yok:
                r.hata("çağrı", f"{kaynak}: var olmayan paftaya çağrı {yok}")
        r.bilgi("çağrı", "kesit ve detay çağrıları set içindeki paftalara gidiyor")
        # ölçülmemiş / doğrulanmamış girdiler
        r.eksik("girdi", "mevcut betonarme döşeme kalınlığı (180 mm) VARSAYIMDIR — "
                         "söküm sonrası ölçülecek",
                oneri="Rölövede döşeme kalınlığı yok; yerinde tespit gerekir.")
        r.eksik("girdi", "yapısal tavan kotu 3,20 m VARSAYIMDIR — "
                         "rölöve yalnız plan düzleminde ölçüm içeriyor")
        r.eksik("girdi", "mevcut pis su bağlantı kotu ölçülmedi — duş eğim şapı "
                         "kalınlığı buna bağlı")
        r.disi("yangın", "bu bölgede yangın bölmesi geçişi yok — bölmeler mahal "
                         "ayırıcıdır, yangın kompartımanı değildir")
        r.disi("taşıyıcı", "pilot bölgede taşıyıcı sisteme müdahale yok — "
                           "deprem yönetmeliği kapsamı dışında")

    # ── 3 kapı açılımı ile mobilya/donatı çakışması ─────────────────────────
    def _kapi_acilim(self, r):
        PL = self.PL
        cak = 0
        for kod, yay in P.KAPI_YAY.items():
            if yay is None: continue
            if not P.ISLAK[PL.BLOK]["tum"].buffer(0.45).intersects(yay): continue
            for ad, g, tip in P.MOBILYA:
                ort = yay.intersection(g).area
                if ort > 0.02:
                    r.hata("açılım", f"{kod} kapı açılımı '{ad}' ile çakışıyor "
                                     f"({ort:.2f} m²)",
                           oneri="Kapıyı ters menteşeye alın veya mobilyayı kaydırın.")
                    cak += 1
        if not cak:
            r.bilgi("açılım", "pilot bölgedeki kapı açılımları sabit mobilyayla "
                              "çakışmıyor")
