# -*- coding: utf-8 -*-
"""PAFTA MOTORU — ISO 5457 çerçeve + ISO 7200 antet + ölçekli görüntü penceresi.

Bu modül, DXF kâğıt alanında (paper space) profesyonel bir teknik resim paftası
kurar. Her pafta aynı motordan çıkar; bu yüzden set içinde tutarlıdır.

Dayanaklar
----------
TS EN ISO 5457  — kâğıt boyutu, çizim çerçevesi, cilt payı, merkezleme işaretleri,
                  kenar ızgarası (zone/bölge referans sistemi), kesme işaretleri
TS EN ISO 7200  — antet veri alanları (zorunlu ve isteğe bağlı)
ISO 128         — çizgi tipleri ve kalem kalınlığı serisi
ISO 3098 / TS 88— yazı yüksekliği serisi
TMMOB MMO/EMO   — proje müellifi, oda sicil no, mesleki denetim alanları

Koordinat sistemi: kâğıt alanı, milimetre, sol-alt köşe (0,0).
"""
import math
from ezdxf.enums import TextEntityAlignment as TA

# ── kâğıt ─────────────────────────────────────────────────────────────────────
KAGIT = {"A0": (1189, 841), "A1": (841, 594), "A2": (594, 420),
         "A3": (420, 297),  "A4": (297, 210)}
CILT_PAYI = 20.0          # mm — sol kenar (ISO 5457)
KENAR     = 10.0          # mm — üst/sağ/alt (A0–A3)
ZON_ADIM  = 50.0          # mm — kenar ızgarası bölge adımı
ZON_BANT  = 5.0           # mm — kenar ızgarası bant genişliği
ANTET_W   = 180.0         # mm — antet genişliği (ISO 7200 önerisi)
ANTET_H   = 92.0          # mm

# ISO 3098 yazı yüksekliği serisi (kâğıt üzerinde mm)
YZ = {"mikro": 1.8, "olcu": 2.5, "metin": 2.5, "etiket": 3.5,
      "altbaslik": 5.0, "baslik": 7.0, "buyuk": 10.0}

# katmanlar (dxf_lib.KATMANLAR içinde tanımlı olmalı)
KAT_CERCEVE = "G-CERCEVE"
KAT_ANTET   = "G-ANTET"
KAT_ZON     = "G-PAFTA-ZON"
KAT_YAZI    = "G-YAZI"


def _t(psp, txt, p, h=2.5, kat=KAT_ANTET, stil="GYM", hiza=TA.MIDDLE_LEFT,
       renk=None, aci=0):
    e = psp.add_text(str(txt), height=h, rotation=aci,
                     dxfattribs={"layer": kat, "style": stil,
                                 **({"color": renk} if renk else {})})
    e.set_placement(p, align=hiza)
    return e


def _l(psp, a, b, kat=KAT_ANTET, lw=None, renk=None):
    d = {"layer": kat}
    if lw is not None: d["lineweight"] = lw
    if renk: d["color"] = renk
    return psp.add_line(a, b, dxfattribs=d)


def _r(psp, x, y, w, h, kat=KAT_ANTET, lw=None, renk=None):
    d = {"layer": kat}
    if lw is not None: d["lineweight"] = lw
    if renk: d["color"] = renk
    return psp.add_lwpolyline([(x, y), (x+w, y), (x+w, y+h), (x, y+h)],
                              close=True, dxfattribs=d)


class Pafta:
    """Tek bir paftayı kâğıt alanında kurar.

    Kullanım:
        pf = Pafta(doc, "A-02", "MİMARİ UYGULAMA PLANI", "MİMARİ", boy="A1")
        pf.cerceve(); pf.antet(olcek="1:50", ...)
        pf.gorunum(merkez=(cx, cy), olcek=50)
        pf.lejant([...]); pf.notlar([...]); pf.kuzey(); pf.olcek_cubugu(50)
    """

    def __init__(self, doc, no, ad, disiplin, boy="A1", proje=None, ust_ad=None):
        self.doc = doc
        self.no, self.ad, self.disiplin, self.boy = no, ad, disiplin, boy
        self.W, self.H = KAGIT[boy]
        # Layout adında /, \, <, >, ", :, ;, ?, *, |, ', ` kullanılamaz
        _ad = f"{no} {ad}"[:60]
        for _c in '/\\<>":;?*|\'`,=': _ad = _ad.replace(_c, "-")
        self.lay = doc.layouts.new(_ad)
        self.lay.page_setup(size=(self.W, self.H), margins=(0, 0, 0, 0), units="mm")
        self.psp = self.lay
        self.proje = proje or {}
        self.ust_ad = ust_ad or ""
        # çizim alanı (çerçeve içi)
        self.x0 = CILT_PAYI
        self.y0 = KENAR
        self.x1 = self.W - KENAR
        self.y1 = self.H - KENAR
        # antet sol-alt köşesi
        self.ax = self.x1 - ANTET_W
        self.ay = self.y0
        # serbest çizim alanı (antet ve sağ sütun hariç) — gorunum() doldurur
        self.sag_sutun = 0.0

    # ── ISO 5457 çerçeve, kenar ızgarası, merkezleme işaretleri ──────────────
    def cerceve(self, zon=True, kesme=True):
        p = self.psp
        # kesme işaretleri (trimming marks) — kâğıt köşelerinde 10×10 mm
        if kesme:
            for cx, cy in ((0, 0), (self.W, 0), (self.W, self.H), (0, self.H)):
                sx = 1 if cx == 0 else -1
                sy = 1 if cy == 0 else -1
                _r(p, min(cx, cx+sx*10), min(cy, cy+sy*10), 10, 10,
                   KAT_CERCEVE, lw=13)
        # çizim çerçevesi
        _r(p, self.x0, self.y0, self.x1-self.x0, self.y1-self.y0,
           KAT_CERCEVE, lw=70)
        if not zon:
            return
        # kenar ızgarası bandı
        _r(p, self.x0+ZON_BANT, self.y0+ZON_BANT,
           self.x1-self.x0-2*ZON_BANT, self.y1-self.y0-2*ZON_BANT,
           KAT_ZON, lw=13)
        ic_x0, ic_y0 = self.x0+ZON_BANT, self.y0+ZON_BANT
        ic_x1, ic_y1 = self.x1-ZON_BANT, self.y1-ZON_BANT
        # yatay bölgeler: rakam, SOLDAN sağa
        nx = max(1, int(round((ic_x1-ic_x0)/ZON_ADIM)))
        adx = (ic_x1-ic_x0)/nx
        for i in range(nx):
            xa = ic_x0+i*adx
            if i:
                _l(p, (xa, self.y0), (xa, ic_y0), KAT_ZON, 13)
                _l(p, (xa, ic_y1), (xa, self.y1), KAT_ZON, 13)
            for yy, hz in ((self.y0+ZON_BANT/2, TA.MIDDLE_CENTER),
                           (self.y1-ZON_BANT/2, TA.MIDDLE_CENTER)):
                _t(p, i+1, (xa+adx/2, yy), YZ["etiket"], KAT_ZON, hiza=hz)
        # düşey bölgeler: harf, AŞAĞIDAN yukarı
        ny = max(1, int(round((ic_y1-ic_y0)/ZON_ADIM)))
        ady = (ic_y1-ic_y0)/ny
        harf = "ABCDEFGHJKLMNPRSTUVYZ"
        for j in range(ny):
            ya = ic_y0+j*ady
            if j:
                _l(p, (self.x0, ya), (ic_x0, ya), KAT_ZON, 13)
                _l(p, (ic_x1, ya), (self.x1, ya), KAT_ZON, 13)
            for xx in (self.x0+ZON_BANT/2, self.x1-ZON_BANT/2):
                _t(p, harf[j % len(harf)], (xx, ya+ady/2), YZ["etiket"], KAT_ZON,
                   hiza=TA.MIDDLE_CENTER)
        # merkezleme işaretleri (ISO 5457): kenar ızgarasından başlar, çizim
        # çerçevesini 10 mm aşar; sürekli çizgi 0,7 mm
        for eksen in ("yatay", "dusey"):
            if eksen == "yatay":
                mx = self.W/2
                _l(p, (mx, self.y0-KENAR), (mx, self.y0+10), KAT_CERCEVE, 70)
                _l(p, (mx, self.y1-10), (mx, self.y1+KENAR), KAT_CERCEVE, 70)
                # yön işareti (orientation mark) — üst kenarda okuyucuya bakan ok
                p.add_lwpolyline([(mx, self.y1+KENAR-1), (mx-2.6, self.y1+KENAR-8),
                                  (mx+2.6, self.y1+KENAR-8)], close=True,
                                 dxfattribs={"layer": KAT_CERCEVE, "lineweight": 70})
            else:
                my = self.H/2
                _l(p, (self.x0-CILT_PAYI, my), (self.x0+10, my), KAT_CERCEVE, 70)
                _l(p, (self.x1-10, my), (self.x1+KENAR, my), KAT_CERCEVE, 70)
                p.add_lwpolyline([(self.x0-CILT_PAYI+1, my), (self.x0-CILT_PAYI+8, my-2.6),
                                  (self.x0-CILT_PAYI+8, my+2.6)], close=True,
                                 dxfattribs={"layer": KAT_CERCEVE, "lineweight": 70})
        # kâğıt boyutu tanımı — alt kenarın sağ köşesi (ISO 5457)
        _t(p, self.boy, (self.x1-2, self.y0-KENAR/2), YZ["olcu"], KAT_CERCEVE,
           hiza=TA.MIDDLE_RIGHT)
        # metrik referans cetveli — 100 mm, 10 mm bölmeli (ISO 5457, isteğe bağlı)
        rx = self.W/2 + 30
        _r(p, rx, self.y0-KENAR+2, 100, 4, KAT_CERCEVE, lw=35)
        for i in range(11):
            _l(p, (rx+i*10, self.y0-KENAR+2), (rx+i*10, self.y0-KENAR+6),
               KAT_CERCEVE, 35)
        _t(p, "100 mm", (rx+104, self.y0-KENAR+4), YZ["mikro"], KAT_CERCEVE)
        self._ic = (ic_x0, ic_y0, ic_x1, ic_y1)
        return self._ic

    # ── ISO 7200 antet + revizyon tablosu ────────────────────────────────────
    def antet(self, olcek="1:50", tarih="", rev="A", durum="ÖN TASARIM",
              muellif="", sicil="", cizen="", kontrol="", onay="",
              sonraki="", birim="mm", revizyonlar=()):
        p = self.psp
        ax, ay, w, h = self.ax, self.ay+ZON_BANT, ANTET_W, ANTET_H
        self.ay = ay
        _r(p, ax, ay, w, h, KAT_ANTET, lw=100)
        # satır yükseklikleri (alttan yukarı)
        satir = [10, 10, 10, 12, 12, 14, 24]          # toplam 92
        yc = ay
        cizgiler = []
        for s in satir[:-1]:
            yc += s; cizgiler.append(yc)
            _l(p, (ax, yc), (ax+w, yc), KAT_ANTET, 35)
        s0, s1, s2, s3, s4, s5 = cizgiler
        # dikey ayraçlar
        _l(p, (ax+60, ay), (ax+60, s2), KAT_ANTET, 35)
        _l(p, (ax+120, ay), (ax+120, s2), KAT_ANTET, 35)
        _l(p, (ax+118, s2), (ax+118, s4), KAT_ANTET, 35)

        def alan(etiket, deger, x, y, gen, hh=None, dh=None):
            _t(p, etiket, (x+1.6, y+hh-3.0 if hh else y+7.2), YZ["mikro"],
               KAT_ANTET)
            _t(p, deger, (x+1.6, y+2.8), dh or YZ["etiket"], KAT_ANTET)

        # üst blok: proje sahibi / proje adı
        _t(p, "İŞVEREN", (ax+1.6, s5+20.0), YZ["mikro"], KAT_ANTET)
        _t(p, self.proje.get("isveren", ""), (ax+1.6, s5+15.0), YZ["metin"], KAT_ANTET)
        _t(p, "PROJE", (ax+1.6, s5+10.0), YZ["mikro"], KAT_ANTET)
        _t(p, self.proje.get("ad", ""), (ax+1.6, s5+4.2), YZ["etiket"], KAT_ANTET)
        # yapı / mahal
        _t(p, "YAPI / MAHAL", (ax+1.6, s4+9.0), YZ["mikro"], KAT_ANTET)
        _t(p, self.proje.get("yapi", ""), (ax+1.6, s4+3.0), YZ["metin"], KAT_ANTET)
        _t(p, "DİSİPLİN", (ax+120.4, s4+9.0), YZ["mikro"], KAT_ANTET)
        _t(p, self.disiplin, (ax+120.4, s4+3.0), YZ["metin"], KAT_ANTET)
        _l(p, (ax+118, s4), (ax+118, s5), KAT_ANTET, 35)
        # pafta adı
        _t(p, "PAFTA ADI", (ax+1.6, s3+8.0), YZ["mikro"], KAT_ANTET)
        # Ad 118 mm'lik alana sığmalı; ISO 3098 3,5 mm yazıda ~0,62 mm/karakter.
        # Sığmıyorsa yazı bir seri küçültülür, hâlâ sığmıyorsa iki satıra kırılır.
        _ad_t, _h = self.ad, YZ["etiket"]
        if len(_ad_t)*0.62*_h/3.5 > 116:
            _h = YZ["metin"]
        if len(_ad_t)*0.62*_h/3.5 > 116:
            _p = _sar(_ad_t, int(116/(0.62*_h/3.5)))
            _t(p, _p[0], (ax+1.6, s3+5.2), _h, KAT_ANTET)
            if len(_p) > 1:
                _t(p, " ".join(_p[1:]), (ax+1.6, s3+1.4), _h, KAT_ANTET)
        else:
            _t(p, _ad_t, (ax+1.6, s3+2.8), _h, KAT_ANTET)
        if self.ust_ad:
            _t(p, self.ust_ad, (ax+120.4, s3+2.8), YZ["mikro"], KAT_ANTET)
        # müellif / sicil
        _t(p, "PROJE MÜELLİFİ · ODA SİCİL NO", (ax+1.6, s2+8.0), YZ["mikro"], KAT_ANTET)
        _t(p, f"{muellif}   {sicil}".strip(), (ax+1.6, s2+2.8), YZ["metin"], KAT_ANTET)
        # alt üç sütun × üç satır
        def hucre(etiket, deger, x, y, dh=YZ["metin"]):
            _t(p, etiket, (x+1.6, y+7.0), YZ["mikro"], KAT_ANTET)
            _t(p, deger, (x+1.6, y+2.6), dh, KAT_ANTET)
        hucre("ÇİZEN", cizen, ax, s1)
        hucre("KONTROL", kontrol, ax+60, s1)
        hucre("ONAY", onay, ax+120, s1)
        hucre("TARİH", tarih, ax, s0)
        hucre("ÖLÇEK", olcek, ax+60, s0, YZ["etiket"])
        hucre("BİRİM", birim, ax+120, s0)
        hucre("DURUM", durum, ax, ay)
        hucre("PAFTA NO", self.no, ax+60, ay, YZ["altbaslik"])
        hucre("REV", rev, ax+120, ay, YZ["altbaslik"])
        if sonraki:
            _t(p, f"SONRAKİ: {sonraki}", (ax+150, ay+3.0), YZ["mikro"], KAT_ANTET)
        # revizyon tablosu — antetin hemen üstünde
        self.revizyon_tablosu(revizyonlar)
        return ay+h

    def revizyon_tablosu(self, revizyonlar=(), satir=5):
        """Antetin üstünde, sağa yaslı revizyon tablosu (en yeni üstte)."""
        p = self.psp
        w, sh = ANTET_W, 6.0
        x, y = self.ax, self.ay+ANTET_H
        sut = [12, 24, 90, 18, 18, 18]        # REV · TARİH · AÇIKLAMA · ÇZ · KT · ON
        bas = ["REV", "TARİH", "AÇIKLAMA", "ÇZ", "KT", "ON"]
        n = max(satir, len(revizyonlar))
        _r(p, x, y, w, sh*(n+1), KAT_ANTET, lw=50)
        for i in range(n+1):
            _l(p, (x, y+i*sh), (x+w, y+i*sh), KAT_ANTET, 18)
        cx = x
        for s in sut[:-1]:
            cx += s; _l(p, (cx, y), (cx, y+sh*(n+1)), KAT_ANTET, 18)
        cx = x
        for b, s in zip(bas, sut):
            _t(p, b, (cx+1.2, y+n*sh+sh/2), YZ["mikro"], KAT_ANTET,
               hiza=TA.MIDDLE_LEFT)
            cx += s
        for i, r in enumerate(revizyonlar[:n]):
            yy = y+(n-1-i)*sh+sh/2
            cx = x
            for v, s in zip(r, sut):
                _t(p, v, (cx+1.2, yy), YZ["mikro"], KAT_ANTET, hiza=TA.MIDDLE_LEFT)
                cx += s
        self.rev_ust = y+sh*(n+1)
        return self.rev_ust

    # ── ölçekli görüntü penceresi ────────────────────────────────────────────
    def gorunum(self, merkez, olcek=50, x=None, y=None, w=None, h=None,
                donuk=(), cerceve=True, donme=0.0):
        """Model uzayını TAM ÖLÇEKTE kâğıda basar.

        merkez : model uzayı merkezi (mm)
        olcek  : 50 → 1:50.  view_height = kâğıt yüksekliği × ölçek
        donuk  : bu görüntü penceresinde dondurulacak katman adları
        """
        ic = getattr(self, "_ic", (self.x0, self.y0, self.x1, self.y1))
        x = self.x0+ZON_BANT+4 if x is None else x
        y = self.y0+ZON_BANT+4 if y is None else y
        w = (self.ax-6) - x if w is None else w
        h = (ic[3]-4) - y if h is None else h
        vp = self.psp.add_viewport(
            center=(x+w/2, y+h/2), size=(w, h),
            view_center_point=merkez, view_height=h*olcek)
        if donme:
            vp.dxf.view_twist_angle = float(donme)
        vp.dxf.status = 1
        vp.dxf.layer = "G-VIEWPORT"   # plot=0 — çerçevesi basılmaz
        if donuk:
            vp.frozen_layers = list(donuk)
        if cerceve:
            _r(self.psp, x, y, w, h, KAT_CERCEVE, lw=18)
        self.vp = vp
        self.vp_kutu = (x, y, w, h)
        return vp

    # ── sağ sütun blokları ───────────────────────────────────────────────────
    def sag(self, genislik=None):
        """Sağ sütun: antet ve revizyon tablosunun ÜSTÜNDE kalan boş şerit.
        Döner: (x, ust_y, genişlik). Bloklar ust_y'den AŞAĞI doğru yığılır ve
        rev_ust sınırına kadar iner."""
        g = genislik or ANTET_W
        ic = getattr(self, "_ic", (self.x0, self.y0, self.x1, self.y1))
        return self.ax, ic[3]-6, g

    @property
    def sag_alt_sinir(self):
        return getattr(self, "rev_ust", self.ay+ANTET_H)+4

    def baslik(self, x, y, metin):
        _t(self.psp, metin, (x, y), YZ["etiket"], KAT_YAZI)
        _l(self.psp, (x, y-2.4), (x+ANTET_W, y-2.4), KAT_YAZI, 35)
        return y-7.0

    def lejant(self, kalemler, x=None, y=None, baslik="LEJANT"):
        """kalemler: [(katman_adi, aciklama)] — çizgi örneği + açıklama."""
        p = self.psp
        sx, sy, w = self.sag()
        x = sx if x is None else x
        y = y if y is not None else sy
        y = self.baslik(x, y, baslik)
        for kat, ack in kalemler:
            if y < self.sag_alt_sinir: break
            ly = self.doc.layers.get(kat) if kat in self.doc.layers else None
            d = {"layer": KAT_ANTET}
            if ly is not None:
                d["color"] = ly.color
                d["linetype"] = ly.dxf.linetype
                d["lineweight"] = ly.dxf.lineweight
            p.add_line((x, y), (x+12, y), dxfattribs=d)
            _t(p, ack, (x+15, y), YZ["mikro"], KAT_YAZI)
            y -= 4.6
        return y-3

    def sembol_lejanti(self, kalemler, x=None, y=None, baslik="SEMBOL LİSTESİ",
                       olcek=1.0):
        """kalemler: [(blok_adi, aciklama)] — blok örneği + açıklama."""
        p = self.psp
        sx, sy, w = self.sag()
        x = sx if x is None else x
        y = y if y is not None else sy
        y = self.baslik(x, y, baslik)
        for blk, ack in kalemler:
            if y < self.sag_alt_sinir: break
            if blk in self.doc.blocks:
                try:
                    r = p.add_blockref(blk, (x+6, y),
                                       dxfattribs={"layer": KAT_ANTET,
                                                   "xscale": olcek,
                                                   "yscale": olcek})
                    r.dxf.rotation = 0
                except Exception:
                    pass
            _t(p, ack, (x+15, y), YZ["mikro"], KAT_YAZI)
            y -= 6.0
        return y-3

    def notlar(self, satirlar, x=None, y=None, baslik="GENEL NOTLAR", gen=None):
        p = self.psp
        sx, sy, w = self.sag()
        x = sx if x is None else x
        y = y if y is not None else sy
        gen = gen or w
        y = self.baslik(x, y, baslik)
        for i, s in enumerate(satirlar, 1):
            if y < self.sag_alt_sinir: break
            for j, par in enumerate(_sar(s, int(gen/1.45))):
                _t(p, (f"{i}. " if j == 0 else "   ")+par, (x, y),
                   YZ["mikro"], KAT_YAZI)
                y -= 3.8
            y -= 1.0
        return y-2

    def tablo(self, basliklar, satirlar, sutunlar, x=None, y=None, baslik=None,
              sh=5.0, fs=None):
        """Basit çizgi+yazı tablosu (ACAD_TABLE taşınabilir değildir)."""
        p = self.psp
        sx, sy, w = self.sag()
        x = sx if x is None else x
        y = y if y is not None else sy
        fs = fs or YZ["mikro"]
        if baslik: y = self.baslik(x, y, baslik)
        toplam = sum(sutunlar)
        n = len(satirlar)+1
        ust = y
        alt = y-n*sh
        _r(p, x, alt, toplam, n*sh, KAT_ANTET, lw=35)
        for i in range(1, n):
            _l(p, (x, ust-i*sh), (x+toplam, ust-i*sh), KAT_ANTET, 13)
        cx = x
        for s in sutunlar[:-1]:
            cx += s; _l(p, (cx, alt), (cx, ust), KAT_ANTET, 13)
        cx = x
        for b, s in zip(basliklar, sutunlar):
            _t(p, b, (cx+1.2, ust-sh/2), fs, KAT_ANTET, hiza=TA.MIDDLE_LEFT)
            cx += s
        for r_i, r in enumerate(satirlar):
            cx = x
            for v, s in zip(r, sutunlar):
                _t(p, str(v), (cx+1.2, ust-(r_i+1.5)*sh), fs, KAT_YAZI,
                   hiza=TA.MIDDLE_LEFT)
                cx += s
        return alt-3

    # ── grafik elemanlar ─────────────────────────────────────────────────────
    def kalem_lejanti(self, x=None, y=None, baslik="ÇİZGİ HİYERARŞİSİ",
                      kalemler=None, uzunluk=22.0):
        """ISO 128-2 kalem serisi — hangi kalınlık neyi anlatıyor.

        Paftanın "ifade" anahtarıdır: kesilen · görünen · arkada kalan ·
        tarama ayrımı burada gösterilmezse okuyucu çizgi kalınlığını yorumlamaz.
        Çizgiler GERÇEK kalınlıklarıyla basılır; lejant baskıda doğrulanabilir.
        """
        p = self.psp
        kalemler = kalemler or [
            (70, "Kesilen eleman çeperi"),
            (50, "Bakılan yüzey sınırı (görünüş)"),
            (35, "Kesit düzlemi arkasında görünen"),
            (25, "Ölçü · kot · anotasyon"),
            (18, "Arkada kalan / ikincil eleman"),
            (13, "Tarama · katman ayrım çizgisi"),
        ]
        sx, sy, sw = self.sag()
        x = sx if x is None else x
        y = sy if y is None else y
        y = self.baslik(x, y, baslik)
        for lw, aciklama in kalemler:
            _l(p, (x, y), (x+uzunluk, y), KAT_ANTET, lw)
            _t(p, f"{lw/100:.2f} mm".replace(".", ","), (x+uzunluk+3, y),
               YZ["mikro"], KAT_ANTET)
            _t(p, aciklama, (x+uzunluk+19, y), YZ["mikro"], KAT_ANTET)
            y -= 4.6
        return y-2

    def kuzey(self, x=None, y=None, r=9.0, aci=0.0):
        """aci: kuzey okunun saat yönünün TERSİNE dönme açısı (derece).
        Görüntü penceresi döndürülmüşse (enlarged plan), ok da aynı kadar döner;
        aksi hâlde pafta kuzeyi yalan söyler."""
        p = self.psp
        vx, vy, vw, vh = getattr(self, "vp_kutu", (self.x0, self.y0, 100, 100))
        x = vx+vw-r-8 if x is None else x
        y = vy+vh-r-8 if y is None else y
        ca, sa = math.cos(math.radians(aci)), math.sin(math.radians(aci))
        def d(dx, dy): return (x + dx*ca - dy*sa, y + dx*sa + dy*ca)
        p.add_circle((x, y), r, dxfattribs={"layer": KAT_ANTET, "lineweight": 35})
        ok = [d(0, r*0.86), d(-r*0.34, -r*0.52), d(0, -r*0.18), d(r*0.34, -r*0.52)]
        pl = p.add_lwpolyline(ok, close=True,
                              dxfattribs={"layer": KAT_ANTET, "lineweight": 50})
        try:
            h = p.add_hatch(color=7, dxfattribs={"layer": KAT_ANTET})
            h.paths.add_polyline_path(ok[:3], is_closed=True)
        except Exception:
            pass
        kx, ky = d(0, -r-4)
        _t(p, "K", (kx, ky), YZ["etiket"], KAT_ANTET, hiza=TA.MIDDLE_CENTER)
        return pl

    def olcek_cubugu(self, olcek=50, x=None, y=None, uzunluk_m=5, bolum=5):
        """Grafik ölçek — ölçek değişse de doğru kalır."""
        p = self.psp
        vx, vy, vw, vh = getattr(self, "vp_kutu", (self.x0, self.y0, 100, 100))
        x = vx+8 if x is None else x
        y = vy+8 if y is None else y
        boy = uzunluk_m*1000.0/olcek        # kâğıt mm
        db = boy/bolum
        for i in range(bolum):
            col = 7 if i % 2 else 250
            try:
                hh = p.add_hatch(color=(0 if i % 2 else 7),
                                 dxfattribs={"layer": KAT_ANTET})
                hh.paths.add_polyline_path(
                    [(x+i*db, y), (x+(i+1)*db, y), (x+(i+1)*db, y+2.2),
                     (x+i*db, y+2.2)], is_closed=True)
            except Exception:
                pass
            _r(p, x+i*db, y, db, 2.2, KAT_ANTET, lw=18)
        for i in range(bolum+1):
            v = i*uzunluk_m/bolum
            et = f"{v:.0f}" if abs(v - round(v)) < 1e-9 else f"{v:.2f}".replace(".", ",")
            _t(p, et, (x+i*db, y-3.2), YZ["mikro"], KAT_ANTET, hiza=TA.MIDDLE_CENTER)
        _t(p, "m", (x+boy+3, y+1.1), YZ["mikro"], KAT_ANTET)
        _t(p, f"ÖLÇEK 1:{olcek}", (x, y+4.0), YZ["mikro"], KAT_ANTET)
        return x+boy

    def durum_damgasi(self, metin="ÖN TASARIM — UYGULAMA İÇİN DEĞİLDİR",
                      x=None, y=None):
        p = self.psp
        vx, vy, vw, vh = getattr(self, "vp_kutu", (self.x0, self.y0, 100, 100))
        x = vx+vw-72 if x is None else x
        y = vy+8 if y is None else y
        _r(p, x, y, 70, 9, KAT_ANTET, lw=50, renk=1)
        _t(p, metin, (x+35, y+4.5), YZ["mikro"], KAT_ANTET, hiza=TA.MIDDLE_CENTER,
           renk=1)

    def dikkat_notu(self, metin="ÖLÇÜ ALINMAZ — YAZILI ÖLÇÜLER GEÇERLİDİR",
                    x=None, y=None):
        vx, vy, vw, vh = getattr(self, "vp_kutu", (self.x0, self.y0, 100, 100))
        x = vx+2 if x is None else x
        y = vy+vh+2.2 if y is None else y
        _t(self.psp, metin, (x, y), YZ["mikro"], KAT_YAZI)

    def anahtar_plan(self, ciz_fn, x=None, y=None, w=None, h=48,
                     baslik="ANAHTAR PLAN"):
        """ciz_fn(psp, x, y, w, h) — küçük konum/anahtar planı çizer."""
        p = self.psp
        sx, sy, gw = self.sag()
        w = w or gw
        x = sx if x is None else x
        y = y if y is not None else sy
        y = self.baslik(x, y, baslik)
        _r(p, x, y-h, w, h, KAT_ANTET, lw=35)
        try:
            ciz_fn(p, x, y-h, w, h)
        except Exception:
            pass
        return y-h-4


def _sar(metin, n):
    """Basit kelime sarma."""
    out, satir = [], ""
    for k in str(metin).split():
        if len(satir)+len(k)+1 > n:
            out.append(satir); satir = k
        else:
            satir = (satir+" "+k).strip()
    if satir: out.append(satir)
    return out or [""]
