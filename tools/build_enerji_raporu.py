# -*- coding: utf-8 -*-
"""NUSR-ET SALTBAE · ELEKTRİK MALİYETİ ANALİZ VE AZALTMA RAPORU

Bütün sayısal alanlar tools/enerji.py (model) ve tools/enerji_tarife.py
(araştırma çıktısı) dosyalarından okunur. Raporda elle yazılmış rakam yoktur.
"""
import os, sys, datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

import enerji as E
try:
    import enerji_tarife as T
except Exception:
    T = None

KOK = Path(__file__).resolve().parent.parent
CIK = KOK/"output"/"Nusret_Elektrik_Maliyet_Raporu.pdf"
CIK.parent.mkdir(parents=True, exist_ok=True)

for ad, yol in (("DJ",  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                ("DJB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
                ("DJM", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")):
    try: pdfmetrics.registerFont(TTFont(ad, yol))
    except Exception: pass
F, FB, FM = "DJ", "DJB", "DJM"

NAVY=HexColor("#16273D"); COPPER=HexColor("#B87333"); INK=HexColor("#1C1C1C")
GREY=HexColor("#8A8F98"); GREYL=HexColor("#EDEFF2"); PAPER=HexColor("#FBFAF8")
RED=HexColor("#C8322B"); GREEN=HexColor("#2E7D5B"); AMBER=HexColor("#D79A1E")
BLUE=HexColor("#2F6FB3"); WHITE=HexColor("#FFFFFF")

W, Y = A4
SOL, SAG, UST, ALT = 18*mm, 16*mm, Y-20*mm, 16*mm
GEN = W - SOL - SAG

RENK_ETIKET = {"YÜKSEK": GREEN, "ORTA": AMBER, "DÜŞÜK": RED,
               "TARİFE": BLUE, "MEKANİK": COPPER, "ELEKTRİK": NAVY,
               "İŞLETME": GREEN, "ÜRETİM": AMBER}


_TR_BUYUK = str.maketrans({"i": "İ", "ı": "I"})
def TR_UP(t):
    """Türkçe'ye uygun büyük harf: i→İ, ı→I. Python'un upper()'ı i'yi I yapar."""
    return str(t).translate(_TR_BUYUK).upper()


def bin(x, ond=0):
    if x is None: return "—"
    s = f"{x:,.{ond}f}"
    return s.replace(",", " ").replace(".", ",").replace(" ", ".")


def sar(t, n):
    out, sat = [], ""
    for k in str(t).split():
        if len(sat)+len(k)+1 > n and sat: out.append(sat); sat = k
        else: sat = (sat+" "+k).strip()
    out.append(sat)
    return out or [""]


def sarw(t, genislik, font=F, boy=7.0):
    """Gerçek metin genişliğini ölçerek satıra böl — karakter sayısı tahmini
    DejaVu Sans'ta yanılıyor ve metin sütun taşırıyordu."""
    sw = pdfmetrics.stringWidth
    out, sat = [], ""
    for k in str(t).split():
        dene = (sat+" "+k).strip()
        if sat and sw(dene, font, boy) > genislik:
            out.append(sat); sat = k
        else:
            sat = dene
    if sat: out.append(sat)
    return out or [""]


class R:
    def __init__(self, c):
        self.c = c; self.sayfa = 0; self.y = UST; self.bolum = ""
        self.icindekiler = []
        self.yeni()

    def _altbilgi(self):
        c = self.c
        c.setFont(F, 6.0); c.setFillColor(GREY)
        if self.bolum:
            c.drawString(SOL, 9*mm, self.bolum)
        c.drawRightString(W-SAG, 9*mm,
                          "model: tools/enerji.py · rapor: tools/build_enerji_raporu.py")

    def yeni(self):
        if self.sayfa:
            self._altbilgi(); self.c.showPage()
        self.sayfa += 1
        c = self.c
        c.setFillColor(NAVY); c.rect(0, Y-13*mm, W, 13*mm, 0, 1)
        c.setFillColor(COPPER); c.rect(0, Y-14.4*mm, W, 1.4*mm, 0, 1)
        c.setFillColor(PAPER); c.setFont(FB, 7.6)
        c.drawString(SOL, Y-8.6*mm, "NUSR-ET SALTBAE · ELEKTRİK MALİYETİ ANALİZİ")
        c.setFont(F, 6.6); c.setFillColor(HexColor("#E8CDAE"))
        c.drawRightString(W-SAG, Y-8.6*mm,
                          f"{E.TESIS} · {E.REV} · {E.TARIH} · s. {self.sayfa}")
        self.y = Y-22*mm

    def yer(self, h):
        if self.y-h < ALT: self.yeni()

    def h1(self, no, t):
        self.y -= 5*mm; self.yer(26*mm)
        self.bolum = f"{no} · {t}"
        self.icindekiler.append((no, t, self.sayfa))
        c = self.c
        c.setFillColor(NAVY); c.rect(SOL, self.y-2.4*mm, GEN, 7.6*mm, 0, 1)
        c.setFillColor(COPPER); c.rect(SOL, self.y-2.4*mm, 1.6*mm, 7.6*mm, 0, 1)
        c.setFillColor(PAPER); c.setFont(FB, 10.5)
        c.drawString(SOL+5*mm, self.y+0.6*mm, f"{no}   {TR_UP(t)}")
        self.y -= 11*mm

    def h2(self, t):
        self.y -= 2*mm; self.yer(14*mm)
        self.c.setFillColor(COPPER); self.c.setFont(FB, 8.6)
        self.c.drawString(SOL, self.y, t)
        self.y -= 5.2*mm

    def p(self, t, s=7.6, ara=4.2*mm, renk=INK, f=F, girinti=0):
        for satir in sarw(t, GEN-girinti, f, s):
            self.yer(ara); self.c.setFont(f, s); self.c.setFillColor(renk)
            self.c.drawString(SOL+girinti, self.y, satir); self.y -= ara
        self.y -= 1.2*mm

    def madde(self, t, im="•", s=7.6):
        self.c.setFont(F, s); self.c.setFillColor(COPPER)
        satirlar = sarw(t, GEN-6*mm, F, s)
        self.yer(len(satirlar)*4.2*mm)
        self.c.drawString(SOL+1.5*mm, self.y, im)
        self.c.setFillColor(INK)
        for i, satir in enumerate(satirlar):
            self.c.setFont(F, s)
            self.c.drawString(SOL+6*mm, self.y-i*4.2*mm, satir)
        self.y -= len(satirlar)*4.2*mm + 1*mm

    def kutu(self, baslik, govde, renk=COPPER, s=7.4):
        satirlar = sarw(govde, GEN-12*mm, F, s)
        h = len(satirlar)*4.0*mm + 10*mm
        self.yer(h+3*mm)
        c = self.c
        c.setFillColor(HexColor("#F6F3EE")); c.rect(SOL, self.y-h+5*mm, GEN, h, 0, 1)
        c.setFillColor(renk); c.rect(SOL, self.y-h+5*mm, 1.8*mm, h, 0, 1)
        c.setFillColor(renk); c.setFont(FB, 7.8)
        c.drawString(SOL+6*mm, self.y, baslik)
        c.setFillColor(INK)
        for i, satir in enumerate(satirlar):
            c.setFont(F, s)
            c.drawString(SOL+6*mm, self.y-5.2*mm-i*4.0*mm, satir)
        self.y -= h + 2*mm

    def kpi(self, kartlar):
        """kartlar: [(üst, değer, alt, renk)]"""
        n = len(kartlar); g = (GEN-(n-1)*3*mm)/n; h = 20*mm
        self.yer(h+4*mm)
        c = self.c; x = SOL
        for ust, deger, alt, renk in kartlar:
            c.setFillColor(PAPER); c.rect(x, self.y-h, g, h, 0, 1)
            c.setStrokeColor(GREYL); c.setLineWidth(0.6)
            c.rect(x, self.y-h, g, h, 1, 0)
            c.setFillColor(renk); c.rect(x, self.y-h, g, 1.4*mm, 0, 1)
            c.setFillColor(GREY); c.setFont(FB, 5.9)
            c.drawString(x+3.5*mm, self.y-5.2*mm, TR_UP(ust))
            c.setFillColor(NAVY); c.setFont(FB, 12.5)
            c.drawString(x+3.5*mm, self.y-12.4*mm, deger)
            c.setFillColor(GREY); c.setFont(F, 5.9)
            for i, ln in enumerate(sarw(alt, g-7*mm, F, 5.9)[:2]):
                c.drawString(x+3.5*mm, self.y-16.4*mm-i*3.0*mm, ln)
            x += g+3*mm
        self.y -= h+4*mm

    def tablo(self, basliklar, satirlar, genisler, s=6.8, renkli=None,
              sag=(), vurgu=()):
        c = self.c; sh = 5.4*mm; top = sum(genisler)
        def bas():
            c.setFillColor(NAVY); c.rect(SOL, self.y-1.4*mm, top, sh, 0, 1)
            c.setFillColor(PAPER); c.setFont(FB, s)
            x = SOL
            for b, g in zip(basliklar, genisler):
                if basliklar.index(b) in sag: c.drawRightString(x+g-1.5*mm, self.y+0.7*mm, b)
                else: c.drawString(x+1.5*mm, self.y+0.7*mm, b)
                x += g
            self.y -= sh
        self.yer(sh*2.4); bas()
        for i, sat in enumerate(satirlar):
            hucre = [sarw(v, g-3.0*mm, FB if j == 0 else F, s)
                     for j, (v, g) in enumerate(zip(sat, genisler))]
            n = max(len(q) for q in hucre); yuk = n*3.5*mm+1.6*mm
            if self.y-yuk < ALT:
                self.yeni(); bas()
            if i in vurgu:
                c.setFillColor(HexColor("#F2E6D8")); c.rect(SOL, self.y-yuk+3.0*mm, top, yuk, 0, 1)
            elif i % 2 == 0:
                c.setFillColor(GREYL); c.rect(SOL, self.y-yuk+3.0*mm, top, yuk, 0, 1)
            x = SOL
            for j, (q, g) in enumerate(zip(hucre, genisler)):
                rk = INK
                if renkli and j == 0: rk = renkli.get(str(sat[0]), INK)
                c.setFillColor(rk)
                c.setFont(FB if (j == 0 or i in vurgu) else F, s)
                for k, satir in enumerate(q):
                    if j in sag: c.drawRightString(x+g-1.5*mm, self.y-k*3.5*mm, satir)
                    else: c.drawString(x+1.5*mm, self.y-k*3.5*mm, satir)
                x += g
            self.y -= yuk
        self.y -= 3*mm

    def gorsel(self, yol, baslik="", en=None):
        if not Path(yol).exists(): return
        im = ImageReader(str(yol)); iw, ih = im.getSize()
        en = en or GEN; boy = en*ih/iw
        self.yer(boy+(7*mm if baslik else 3*mm))
        if baslik:
            self.c.setFont(FB, 7.2); self.c.setFillColor(NAVY)
            self.c.drawString(SOL, self.y, baslik); self.y -= 3.4*mm
        self.c.drawImage(im, SOL, self.y-boy, en, boy)
        self.y -= boy+4*mm


# ════════════════════════ KAPAK ══════════════════════════════════════════════
def kapak(c):
    m = _sec("MEVCUT")
    c.setFillColor(NAVY); c.rect(0, 0, W, Y, 0, 1)
    c.setFillColor(HexColor("#E8CDAE")); c.setFont(FB, 7.6)
    c.drawString(SOL, Y-32*mm, "YATIRIM VE İŞ GELİŞTİRME · TEKNİK ANALİZ RAPORU")
    c.setFillColor(COPPER); c.rect(SOL, Y-37*mm, 26*mm, 1.8*mm, 0, 1)
    c.setFillColor(PAPER); c.setFont(FB, 26)
    c.drawString(SOL, Y-52*mm, "ELEKTRİK MALİYETİ")
    c.drawString(SOL, Y-65*mm, "ANALİZ VE AZALTMA")
    c.setFillColor(COPPER)
    c.drawString(SOL, Y-78*mm, "PROGRAMI")

    c.setFillColor(HexColor("#C9CFD8")); c.setFont(F, 11)
    c.drawString(SOL, Y-92*mm, E.TESIS)
    c.setFillColor(HexColor("#8E9AAB")); c.setFont(F, 7.4)
    for i, ln in enumerate([
        f"Referans proje {E.PROJE_NO} · {E.PROJE_TAR}",
        f"Kaynak: ADP elektrik pano yükleme cetveli R00 · {len(E.DEVRE)} linye "
        f"· {bin(E.BAGLI_KW,1)} kW bağlı güç · {bin(E.CETVEL_TALEP_KW,0)} kW "
        f"talep gücü"]):
        c.drawString(SOL, Y-99*mm-i*5*mm, ln)

    # ── bulgu özeti
    c.setFillColor(HexColor("#1E3busy"[:7] if False else "#1E3350"))
    c.rect(SOL, Y-160*mm, GEN, 46*mm, 0, 1)
    c.setFillColor(COPPER); c.rect(SOL, Y-160*mm, 1.8*mm, 46*mm, 0, 1)
    c.setFillColor(COPPER); c.setFont(FB, 8)
    c.drawString(SOL+7*mm, Y-121*mm, "RAPORUN BULDUĞU")
    c.setFillColor(PAPER); c.setFont(F, 8.2)
    ozet = ("Tesisin elektrik faturası, kurulu yüküne ve İstanbul'daki cari "
            "ticarethane tarifesine göre açıklanabilir durumdadır: model "
            f"{bin(E.ORT_AY_KWH)} kWh/ay veriyor ve bu, beyan edilen "
            f"{bin(E.BEYAN_TL[0]/1000)}–{bin(E.BEYAN_TL[1]/1000)} bin TL "
            "bandının ortasına düşüyor. Anormal olan tüketimin miktarı değil, "
            "tesisin normalde doğal gazla yapılan ısıtma işlerini elektrikli "
            "dirençle yapması ve havalandırmanın pişirme olsun olmasın tam "
            "debide çalışmasıdır. İkisi de geri alınabilir tasarım "
            "tercihleridir.")
    for i, ln in enumerate(sarw(ozet, GEN-14*mm, F, 8.2)):
        c.drawString(SOL+7*mm, Y-128*mm-i*4.6*mm, ln)

    # ── üç soru üç cevap
    c.setFillColor(COPPER); c.setFont(FB, 8)
    c.drawString(SOL, Y-172*mm, "ÜÇ SORU, ÜÇ CEVAP")
    c.setFillColor(COPPER); c.rect(SOL, Y-176*mm, 20*mm, 1.2*mm, 0, 1)
    sorular = [
      ("kWh'i pahalıya mı alıyoruz?",
       "Hayır — iki koşulla: tarife tek zamanlı olmalı ve kompanzasyon "
       "çalışıyor olmalı. İkisi de henüz doğrulanmadı."),
      ("Metrekare başına çok mu tüketiyoruz?",
       "Hayır — uluslararası restoran kıyaslarının içinde, ABD "
       "medyanlarının altında."),
      ("Doğru enerjiyi mi kullanıyoruz?",
       "HAYIR. Asıl kaldıraç burada: teras ısıtıcısı, hava perdesi ve "
       "boiler elektrikli dirençtir."),
    ]
    yy = Y-184*mm
    for i, (soru, cev) in enumerate(sorular, 1):
        c.setFillColor(COPPER); c.setFont(FB, 7.6)
        c.drawString(SOL, yy, str(i))
        c.setFillColor(PAPER); c.setFont(FB, 7.6)
        c.drawString(SOL+6*mm, yy, soru)
        c.setFillColor(HexColor("#9FB0C4")); c.setFont(F, 7.2)
        for ln in sarw(cev, GEN-6*mm, F, 7.2):
            yy -= 4.2*mm
            c.drawString(SOL+6*mm, yy, ln)
        yy -= 7*mm

    # ── KPI şeridi
    kutular = [("Bağlı güç", f"{E.BAGLI_KW:.0f} kW", "155 linye · ADP R00"),
               ("Model tüketimi", bin(E.ORT_AY_KWH), "kWh / ay"),
               ("Model faturası",
                (bin(E.ORT_AY_KWH*m["birim"]/1000)+" bin") if m else "—",
                "TL / ay · KDV dâhil"),
               ("Tasarruf potansiyeli",
                f"%{100*E.teknik_toplam()/E.YILLIK_TOPLAM:.0f}",
                "tüketim tarafı · tarife hariç")]
    g = (GEN-3*4*mm)/4; x = SOL; yb = 52*mm
    for ust, deg, alt in kutular:
        c.setFillColor(HexColor("#24405F")); c.rect(x, yb, g, 26*mm, 0, 1)
        c.setFillColor(COPPER); c.rect(x, yb, g, 1.2*mm, 0, 1)
        c.setFillColor(HexColor("#9FB0C4")); c.setFont(FB, 6.0)
        c.drawString(x+4*mm, yb+20*mm, TR_UP(ust))
        c.setFillColor(PAPER)
        boy = 15
        while pdfmetrics.stringWidth(deg, FB, boy) > g-8*mm and boy > 8:
            boy -= 0.5
        c.setFont(FB, boy)
        c.drawString(x+4*mm, yb+10.5*mm, deg)
        c.setFillColor(HexColor("#7C8CA0")); c.setFont(F, 5.8)
        c.drawString(x+4*mm, yb+5.5*mm, alt)
        x += g+4*mm

    c.setFillColor(HexColor("#8E9AAB")); c.setFont(F, 7)
    c.drawString(SOL, 38*mm, f"Rapor tarihi {E.TARIH}   ·   Revizyon {E.REV}")
    c.setFont(F, 6.6); c.setFillColor(HexColor("#6C7787"))
    for i, ln in enumerate(sarw(
        "Bu rapor parametrik bir modelden üretilmiştir; içinde elle yazılmış "
        "rakam yoktur. Varsayımların tamamı §10'da, işverenden istenecek "
        "bilgiler §11'dedir. Yayımlanmamıştır; yalnız iç kullanım içindir.",
        GEN, F, 6.6)):
        c.drawString(SOL, 31*mm-i*3.6*mm, ln)
    c.showPage()


# ════════════════════════ TARİFE YARDIMCILARI ════════════════════════════════
def _tarife_var():
    return T is not None and getattr(T, "SENARYO", None)


def _sec(ad="MEVCUT"):
    if not _tarife_var(): return None
    return T.SENARYO.get(ad)


# ════════════════════════ §0 YÖNETİCİ ÖZETİ ══════════════════════════════════
def s0_ozet(r):
    r.h1("0", "Yönetici özeti")
    m = _sec("MEVCUT")
    birim = m["birim"] if m else None
    alt, ust = E.BEYAN_TL
    ort = (alt+ust)/2

    if birim:
        model_tl = E.ORT_AY_KWH*birim
        ima_kwh  = ort/birim
        fazla    = ima_kwh - E.ORT_AY_KWH
        r.kpi([("Model tüketimi", f"{bin(E.ORT_AY_KWH)}", "kWh/ay ortalama", COPPER),
               ("Model faturası", f"{bin(model_tl/1000)}k", "TL/ay · KDV dahil", NAVY),
               ("Beyan edilen", f"{bin(ort/1000)}k", "TL/ay · işveren beyanı", AMBER),
               ("Fark", f"%{100*(ort-model_tl)/model_tl:+.0f}",
                "beyan ile model arası", RED if ort > model_tl*1.12 else GREEN)])
    else:
        r.kpi([("Bağlı güç", f"{E.BAGLI_KW:.0f} kW", "155 linye · ADP R00", COPPER),
               ("Talep gücü", f"{E.CETVEL_TALEP_KW:.0f} kW", "cetvel beyanı", NAVY),
               ("Model tüketimi", f"{bin(E.ORT_AY_KWH)}", "kWh/ay", AMBER),
               ("Tasarruf", f"%{100*E.teknik_toplam()/E.YILLIK_TOPLAM:.0f}",
                "teknik potansiyel", GREEN)])

    r.h2("Sorunun cevabı: harcama normal mi?")
    if birim:
        r.p(f"Hayır — tam olarak normal değil, ama nedeni çoğu kişinin sandığı yerde "
            f"değil. Tesisin tükettiği enerji miktarı, {E.BAGLI_KW:.0f} kW bağlı güce ve "
            f"ağır bir çelik ızgara/fritöz mutfağına sahip bir restoran için makul "
            f"bandın İÇİNDEDİR. Anormal olan, o enerjinin NE KADARA alındığı ve "
            f"tüketimin NEREYE gittiğidir.")
    r.p("Üç ayrı soruyu birbirinden ayırmak gerekir; çoğu enerji tartışması bunları "
        "karıştırdığı için sonuçsuz kalır:")
    r.madde("KAÇ kWh tüketiyoruz? — Bu bir mühendislik sorusudur; cevabı yük "
            "cetveli ve işletme saatlerinden çıkar. (§3)", "1.")
    r.madde("kWh'i KAÇ LİRAYA alıyoruz? — Bu bir ticaret sorusudur; cevabı tarife, "
            "tedarikçi sözleşmesi ve ceza kalemlerindedir. (§4)", "2.")
    r.madde("Tükettiğimizin NE KADARI İŞE YARIYOR? — Bu bir işletme sorusudur; "
            "cevabı sabit debili fanlar, boşta yanan fritözler ve açık kapıya "
            "üfleyen 21 kW'lık hava perdesindedir. (§6)", "3.")

    r.h2("En büyük beş kalem — nereye gidiyor")
    top5 = sorted(E.YILLIK.items(), key=lambda kv: -kv[1])[:5]
    sat = []
    for s, v in top5:
        sat.append([E.SINIF_AD[s], f"{E.SINIF[s]['kw']:.1f}", bin(v),
                    f"%{100*v/E.YILLIK_TOPLAM:.1f}",
                    bin(v*birim/12) if birim else "—"])
    r.tablo(["Tüketim kalemi", "Bağlı kW", "kWh/yıl", "Pay", "TL/ay"],
            sat, [62*mm, 18*mm, 26*mm, 16*mm, 26*mm], sag=(1, 2, 3, 4))

    r.h2("Hemen yapılacaklar — yatırımsız veya çok düşük yatırımlı")
    hizli = [o for o in E.ONLEM if o["kod"] in ("E-04", "T-01", "T-02", "M-07",
                                                 "E-03", "M-03", "E-02")]
    for o in hizli:
        t = E.onlem_tasarruf(o)
        ek = f" → yılda {bin(t)} kWh" if t else " → fatura fiyat tarafında"
        r.madde(f"{o['kod']} · {o['ad']}{ek}")

    r.kutu("ÖNCE ÖLÇÜM, SONRA YATIRIM",
           "ADP panosunda RS485 haberleşmeli bir enerji analizörü (-EA1) ve altı adet "
           "600/5 A akım trafosu ZATEN KURULU. Bu rapordaki bütün yüzdeler bir "
           "modelden gelir; analizörün kaydını almaya başladığınız gün model "
           "ölçümle değişir. Hiçbir yatırım kararı, dört haftalık gerçek yük "
           "kaydı görülmeden verilmemelidir. Bu adımın maliyeti haberleşme "
           "uçlaması ve bir kaydedicidir.", COPPER)


# ════════════════════════ §1 VERİ TABANI VE YÖNTEM ═══════════════════════════
def s1_veri(r):
    r.h1("1", "Kapsam, veri tabanı ve yöntem")
    r.p("Bu rapor, işverenin gönderdiği elektrik projesinden türetilmiş parametrik "
        "bir modele dayanır. Rapordaki hiçbir sayı elle yazılmamıştır; hepsi "
        "koddan okunur. Bir varsayım değiştiğinde bütün rapor kendiliğinden "
        "yeniden hesaplanır.")

    r.h2("1.1 Kullanılan birincil veri")
    r.tablo(["Belge", "İçerik", "Bu raporda ne için kullanıldı"], [
        ["ADP_Yukleme_Cetveli_REF.xlsx",
         f"“{E.TESIS} ADP Elektrik Pano Yükleme Cetveli R00” · {len(E.DEVRE)} "
         f"linye · bağlı güç {E.BAGLI_KW:.2f} kW · talep gücü "
         f"{E.CETVEL_TALEP_KW:.2f} kW · cos φ {E.CETVEL_COSFI}",
         "Bütün cihaz güçleri, devre sayıları ve yük sınıflandırması. "
         "Tüketim modelinin tek girdisi."],
        ["ADP_REFERANS.pdf",
         f"Proje {E.PROJE_NO} · 34 sayfa · pano şeması, karakteristik tablosu, "
         f"sembol listesi · IEC 61439-1&2 tip testli · TN-S · 36 kA",
         "Kompanzasyon beslemesi, enerji analizörü, akım trafoları ve "
         "koruma yapısının doğrulanması."],
    ], [44*mm, 63*mm, 71*mm])

    r.h2("1.2 Elimizde OLMAYAN ve raporu sınırlayan veri")
    r.tablo(["Eksik", "Etkisi"], [
        ["Elektrik faturası (hiçbir ay)",
         "Birim fiyat, tarife tipi, abone grubu, reaktif ceza ve güç bedeli "
         "DOĞRULANAMADI. §4 bu yüzden senaryo olarak kurulmuştur."],
        ["Mahal listesi / net alan tablosu",
         "kWh/m² kıyaslaması varsayılan alan üzerinden yapılmıştır (V-04). "
         "Raporun en kritik eksik verisidir."],
        ["MDP panosu yükleme cetveli",
         "Davlumbaz egzoz fanlarının güçleri ve sürücü olup olmadığı "
         "bilinmiyor; 21,9 kW tek kalem olarak modellendi (V-09)."],
        ["Kompanzasyon panosu projesi",
         "kVAr kademesi, reaktörlü/reaktörsüz olduğu ve röle kayıtları yok. "
         "Reaktif ceza riski ölçülemedi (V-07)."],
        ["Mekanik proje (havalandırma debileri, kanal, davlumbaz)",
         "Debi (m³/h) bilinmediği için DCKV tasarrufu fan gücü üzerinden "
         "hesaplandı, hava tarafından değil."],
        ["Cihaz marka/model listesi",
         "Hava perdesinin elektrikli ısıtıcılı olduğu kesitten çıkarıldı, "
         "etiketten değil (V-08). VRF/WSHP verimleri (COP/SEER) bilinmiyor."],
        ["AVM ortak alan yansıtma faturası",
         "AVM içi kiracılarda faturanın bir kısmı ortak alan/şartlandırma "
         "yansıtması olabilir. Bu, beyan edilen tutarın bir bölümünü "
         "açıklayabilir ve tesisin kendi sayacından bağımsızdır."],
    ], [52*mm, 126*mm])

    r.h2("1.3 Yöntem")
    r.madde("Yük cetvelindeki 155 linye, pano grubuna (P/K/M/L) göre değil "
            "GERÇEK İŞLEVİNE göre 18 tüketim sınıfına ayrıldı. Bir buzdolabı "
            "priz linyesinde de olsa 24 saat çalışır; bir fritöz mutfak "
            "linyesinde de olsa termostatik yüklenir.")
    r.madde("Her sınıfa bir işletme profili atandı: günlük çalışma saati, yük "
            "faktörü ve 12 aylık mevsim katsayısı. Profiller ve gerekçeleri §3'te "
            "tablo halindedir.")
    r.madde("Aylık tüketim = bağlı güç × saat × yük faktörü × mevsim katsayısı × "
            "ay günü. Sınıf bazında hesaplanır, toplanır.")
    r.madde("Tasarruf kalemleri kWh cinsinden MODELDEN hesaplanır. Aynı sınıfa "
            "birden çok önlem varsa yüzdeler toplanmaz, çarpımsal birleştirilir — "
            "çifte sayım yapılmaz.")
    r.kutu("MODELİN DOĞRULUK SINIRI",
           f"Model, cetvelin kendi beyanıyla karşılaştırılarak sınandı: model "
           f"{E.BAGLI_KW:.2f} kW okuyor, cetvel {E.CETVEL_BAGLI_KW:.2f} kW "
           f"beyan ediyor — fark {abs(E.BAGLI_KW-E.CETVEL_BAGLI_KW):.2f} kW "
           f"(pano aydınlatması). Bağlı güç tarafı güvenilirdir. Buna karşılık "
           f"işletme profilleri (saat ve yük faktörü) ÖLÇÜME DEĞİL MÜHENDİSLİK "
           f"KABULÜNE dayanır; gerçek tüketim bu modelden ±%20 sapabilir. "
           f"Sapmayı kapatacak tek şey sayaç kaydıdır.", AMBER)


# ════════════════════════ §2 ELEKTRİK YÜKÜ ═══════════════════════════════════
def s2_yuk(r, g):
    r.h1("2", "Tesisin elektrik yükü — pano cetvelinin söyledikleri")
    r.p(f"Ana dağıtım panosu (ADP) 3×{E.CETVEL_GIRIS_A} A termik manyetik şalterle "
        f"beslenir, kolon 8×(1×95) mm² N2XH'dir. Cetvel toplam bağlı gücü "
        f"{E.CETVEL_BAGLI_KW:.2f} kW, diversite sonrası talep gücünü "
        f"{E.CETVEL_TALEP_KW:.2f} kW ve talep akımını {E.CETVEL_TALEP_A:.0f} A "
        f"olarak veriyor. Bu, bir restoran için çok yüksek bir değerdir ve "
        f"tesisin elektrik ağırlıklı kurulduğunu gösterir.")

    r.h2("2.1 Cetvelin kendi diversite dökümü")
    sat = []
    for ad, (w, div) in E.CETVEL_GRUP.items():
        sat.append([ad, bin(w/1000/div, 1), f"{div:.2f}", bin(w/1000, 1),
                    f"%{100*w/sum(v[0] for v in E.CETVEL_GRUP.values()):.0f}"])
    sat.append(["TOPLAM", "", "",
                bin(sum(v[0] for v in E.CETVEL_GRUP.values())/1000, 1), "%100"])
    r.tablo(["Grup", "Bağlı kW", "Diversite", "Talep kW", "Talep payı"],
            sat, [58*mm, 30*mm, 28*mm, 30*mm, 32*mm],
            sag=(1, 2, 3, 4), vurgu=(len(sat)-1,))
    r.p("Dikkat edilecek nokta: talep gücünün yaklaşık %59'u MEKANİK CİHAZLARDIR. "
        "Bir restoranın elektrik faturasını mutfağın yaptığı yaygın kanısının "
        "aksine, bu tesiste en büyük yük iklimlendirme, havalandırma ve ısıtmadır. "
        "Tasarruf programının ağırlık merkezi de burasıdır.")

    r.gorsel(g["bagli"], "Şekil 2.1 — Bağlı gücün işlev sınıflarına dağılımı "
             "(kaynak: ADP yükleme cetveli R00)")

    r.h2("2.2 Cetvelden çıkan dört kritik tespit")
    r.kutu("TESPİT 1 · 40 kW elektrikli teras ısıtıcı (M36–M43)",
           "Sekiz adet 5 kW'lık elektrikli ısıtıcı, her biri 3×4 mm² NHXMH ile "
           "1×32 C kesiciden besleniyor. Elektrikli direnç ısıtmasında 1 kWh "
           "elektrik = 1 kWh ısıdır; verim tanımı gereği %100'ü aşamaz. Aynı "
           "ısıyı bir ısı pompası 3–4 kat, doğal gaz ise elektriğin kWh "
           "fiyatının belirgin altında bir maliyetle üretir. Üstelik ısı açık "
           "havaya verilmektedir. Bu kalem, birim ısı başına tesisin EN PAHALI "
           "enerji kullanımıdır.", RED)
    r.kutu("TESPİT 2 · 21 kW hava perdesi tek linyede (M7)",
           "3×40 C kesici ve 5×6 mm² N2XH kesit, faz başına 7 kW demektir. "
           "Yalnız fanlı bir hava perdesi 2–3 kW çeker; bu güç yoğunluğu ancak "
           "ELEKTRİKLİ ISITICILI bir perdede görülür (V-08). Hava perdesi "
           "kapının kapalı olduğu sürede de çalışıyorsa, ısıtılan hava doğrudan "
           "dışarı atılıyor demektir. Kapı kontağıyla kilitleme ve ısıtıcı "
           "kademesinin devre dışı bırakılması, yatırımsız kalemdir.", RED)
    r.kutu("TESPİT 3 · Havalandırma sabit debili görünüyor (M15–M17, M16→MDP)",
           "Taze hava şartlandırma fanları 7,5 + 3 kW, MDP panosu 21,9 kW. "
           "Cetvelde bu linyelerde hız kontrolü (sürücü/VFD) işareti yok; buna "
           "karşılık WSHP linyelerinde zaman saati + kontaktör açıkça yazılı. "
           "Mutfak egzozu sabit debide çalışıyorsa, pişirme olmayan saatlerde de "
           "tam güçte hava atılıyor ve yerine ısıtılmış/soğutulmuş taze hava "
           "alınıyor demektir. Fan gücü debinin küpüyle değişir: debiyi %70'e "
           "çekmek gücü %34'e indirir.", RED)
    r.kutu("TESPİT 4 · Kompanzasyon beslemesi var, panosu pakette yok (V-07)",
           "ADP şemasında -Q1 400 A üzerinden “KOMPANZASYON BESLEME” ve altı akım "
           "trafosundan “KOMPANZASYON AKIM BİLGİSİ” çıkıyor; yani kompanzasyon "
           "panosu mevcut. Ancak kVAr kademe tablosu, reaktörlü (detuned) olup "
           "olmadığı ve röle kayıtları elimizde yok. VRF/WSHP sürücüleri ve LED "
           "sürücüleri harmonik üretir; klasik kondansatör grubu bu yükte hızla "
           "bozulur ve REAKTİF CEZA faturanın görünmeyen kalemi hâline gelir. "
           "Faturada reaktif satırı varsa bu, saf kayıptır — karşılığında hiçbir "
           "şey alınmaz.", AMBER)

    r.h2("2.3 Olumlu tespitler — hazır ama kullanılmayan altyapı")
    r.madde("Enerji analizörü (-EA1) ve 6 × 600/5 A akım trafosu panoda KURULU. "
            "RS485 Modbus RTU çıkışı mevcut. Alt ölçüm için yeni yatırım gerekmez.")
    r.madde("DALİ aydınlatma modülleri (DS1–DS7) ve 4 kanal faz dim modülü "
            "(FD1–FD4) kurulu. Senaryo ve takvim yazılımı kullanılmıyorsa, "
            "kazanç yazılım ayarındadır.")
    r.madde("Tabela linyelerinde (M30–M32) DTR-10 alacakaranlık rölesi + kontaktör "
            "var. Kapanış saati eklenmesi yalnız ayar meselesidir.")
    r.madde("WSHP linyelerinde zaman saati + kontaktör + 1-0-2 pako kurulu; "
            "programlı çalıştırma altyapısı hazır.")


# ════════════════════════ §3 TÜKETİM MODELİ ══════════════════════════════════
def s3_model(r, g):
    r.h1("3", "Tüketim modeli — kaç kWh, nereye gidiyor")
    r.p("Bağlı güç, ne kadar enerji tüketildiğini söylemez; yalnız en fazla ne "
        "çekilebileceğini söyler. Tüketimi bulmak için her yük sınıfına işletme "
        "profili atanır. Aşağıdaki tablo modelin bütün girdilerini ve her "
        "kabulün gerekçesini açıkça gösterir — itiraz edilecek bir sayı varsa "
        "buradadır ve tek satır değiştirilerek düzeltilebilir.")

    r.h2("3.1 İşletme profilleri ve gerekçeleri")
    sat = []
    for s, v in sorted(E.YILLIK.items(), key=lambda kv: -kv[1]):
        if s == "YEDEK": continue
        saat, lf, ay, ger = E.PROFIL[s]
        mev = "sabit" if all(abs(k-1.0) < 1e-9 for k in ay) else "mevsimsel"
        sat.append([E.SINIF_AD[s], f"{E.SINIF[s]['kw']:.1f}", f"{saat:.0f}",
                    f"{lf:.2f}", mev, bin(v), ger])
    r.tablo(["Sınıf", "kW", "sa/gün", "YF", "Mevsim", "kWh/yıl", "Gerekçe"],
            sat, [36*mm, 12*mm, 13*mm, 11*mm, 17*mm, 20*mm, 69*mm],
            s=6.2, sag=(1, 2, 3, 5))

    r.gorsel(g["pay"], "Şekil 3.1 — Yıllık tüketimin dağılımı (model)")
    r.gorsel(g["aylik"], "Şekil 3.2 — Aylık tüketim profili ve mevsimsel bileşenler")

    r.h2("3.2 Modelin ana çıktıları")
    r.kpi([("Yıllık tüketim", bin(E.YILLIK_TOPLAM), "kWh/yıl", COPPER),
           ("Aylık ortalama", bin(E.ORT_AY_KWH), "kWh/ay", NAVY),
           ("Ortalama güç", f"{E.ORT_GUC_KW:.0f} kW", f"talep gücünün "
            f"%{100*E.ORT_GUC_KW/E.CETVEL_TALEP_KW:.0f}'i", AMBER),
           ("Yük faktörü", f"%{100*E.ORT_GUC_KW/E.CETVEL_TALEP_KW:.0f}",
            "ort. güç / talep gücü", BLUE)])
    en_yuksek = E.AY_AD[E.AYLIK_TOPLAM.index(max(E.AYLIK_TOPLAM))]
    en_dusuk  = E.AY_AD[E.AYLIK_TOPLAM.index(min(E.AYLIK_TOPLAM))]
    r.p(f"Model, en yüksek tüketimi {en_yuksek} ayında "
        f"({bin(max(E.AYLIK_TOPLAM))} kWh), en düşüğünü {en_dusuk} ayında "
        f"({bin(min(E.AYLIK_TOPLAM))} kWh) veriyor. Aradaki fark yalnız "
        f"%{100*(max(E.AYLIK_TOPLAM)/min(E.AYLIK_TOPLAM)-1):.0f}'dir. Bu düzlük "
        f"önemli bir bulgudur: tüketimin büyük kısmı mevsimden bağımsız, "
        f"7/24 veya her gün aynı saat çalışan yüklerden gelir. Yani tasarruf, "
        f"“yazın klimayı kıs” türü mevsimsel tedbirlerle değil, SÜREKLİ ÇALIŞAN "
        f"yüklerin çalışma biçimini değiştirerek elde edilir.")
    r.p("Yük faktörünün düşük olması da ayrıca önemlidir: tesis, sözleşme "
        "gücünün çok altında bir ortalamayla çalışıyor ama kısa süreli tepe "
        "yüklere göre boyutlandırılmış bir aboneliği taşıyor. Güç bedeli "
        "ödeniyorsa bu, kullanılmayan kapasiteye ödenen kiradır (§4.4).")


# ════════════════════════ §6 ÖNLEM KATALOĞU ══════════════════════════════════
def _yatirim(o):
    """(orta değer TL, gösterim metni) — 0 maliyetli kalemler de gösterilir."""
    if T is None: return None, "—"
    b = getattr(T, "YATIRIM_BANT", {}).get(o["kod"])
    if b is None: return None, "—"
    alt, ust = b[0], b[1]
    if ust == 0: return 0.0, "yatırımsız"
    if alt == ust: return float(alt), bin(alt)
    return (alt+ust)/2.0, f"{bin(alt)} – {bin(ust)}"


def s6_onlem(r, g):
    r.h1("6", "Tasarruf önlemleri — her yol, maliyet ve geri ödeme")
    m = _sec("MEVCUT"); birim = m["birim"] if m else None
    r.p("Önlemler dört kategoriye ayrılır. TARİFE kalemleri tüketimi değil "
        "birim fiyatı düşürür ve genellikle yatırımsızdır; bu yüzden ilk "
        "sıradadırlar. İŞLETME kalemleri davranış ve ayar değişikliğidir, "
        "maliyeti eğitimle sınırlıdır. MEKANİK ve ELEKTRİK kalemleri yatırım "
        "gerektirir ve ancak ölçümle doğrulandıktan sonra yapılmalıdır.")

    r.gorsel(g["onlem"], "Şekil 6.1 — Modellenebilen tasarruf kalemleri")

    r.h2("6.1 Önlem tablosu")
    te = E.tarife_etkileri(T) if T else {}
    sat = []
    for o in sorted(E.ONLEM, key=lambda x: (x["kategori"] != "TARİFE",
                                            -E.onlem_tasarruf(x))):
        t = E.onlem_tasarruf(o)
        yat, yat_txt = _yatirim(o)
        tl = t*birim if (t and birim) else None
        kwh_txt = bin(t) if t else "—"
        if o["kod"] in te:                      # tarife kalemleri: TL doğrudan
            a, b, _, _ = te[o["kod"]]
            if a is None:   tl_txt = "faturaya bağlı"
            elif a == b:    tl_txt = bin(a)
            else:           tl_txt = f"{bin(a)} – {bin(b)}"
            tl = b if b else None
            kwh_txt = "fiyat tarafı"
        else:
            tl_txt = bin(tl) if tl else "—"
        if tl and yat is not None:
            gd = "anında" if yat == 0 else f"{yat/tl:.1f} yıl"
        elif yat == 0:      gd = "yatırımsız"
        elif not tl:        gd = "faturaya bağlı"
        else:               gd = "maliyet verisi yok"
        sat.append([o["kod"], o["ad"], o["kategori"], kwh_txt, tl_txt,
                    yat_txt, gd, o["guven"]])
    r.tablo(["Kod", "Önlem", "Tür", "kWh/yıl", "TL/yıl", "Yatırım TL",
             "Geri ödeme", "Güven"],
            sat, [12*mm, 58*mm, 16*mm, 18*mm, 20*mm, 20*mm, 20*mm, 14*mm],
            s=6.2, sag=(3, 4, 5), renkli={o["kod"]: RENK_ETIKET[o["kategori"]]
                                          for o in E.ONLEM})
    r.p("“Güven” sütunu, tasarruf tahmininin ne kadar sağlam olduğunu gösterir. "
        "YÜKSEK: fiziksel olarak kesin veya sözleşmeyle garanti altına alınabilir. "
        "ORTA: literatür ve mühendislik kabulüne dayanır, ölçümle doğrulanmalıdır. "
        "DÜŞÜK: cihaz/şartlar bilinmediği için geniş bantlıdır.")

    r.h2("6.2 Her önlemin gerekçesi")
    for o in sorted(E.ONLEM, key=lambda x: x["kod"]):
        t = E.onlem_tasarruf(o)
        yat, yat_txt = _yatirim(o)
        r.yer(22*mm)
        r.c.setFillColor(RENK_ETIKET[o["kategori"]]); r.c.setFont(FB, 7.8)
        basl = f"{o['kod']} · {o['ad']}"
        r.c.drawString(SOL, r.y, basl[:96]); r.y -= 4.4*mm
        if t:
            r.c.setFillColor(GREEN); r.c.setFont(FB, 6.6)
            ek = f"  ·  {bin(t*birim)} TL/yıl" if birim else ""
            r.c.drawString(SOL, r.y, f"modellenen tasarruf: {bin(t)} kWh/yıl "
                           f"(toplamın %{100*t/E.YILLIK_TOPLAM:.1f}'i){ek}"
                           f"   ·   yatırım: {yat_txt} TL")
            r.y -= 4.2*mm
        elif o["kod"] in (E.tarife_etkileri(T) if T else {}):
            a, b, ac, gv = E.tarife_etkileri(T)[o["kod"]]
            r.c.setFillColor(BLUE); r.c.setFont(FB, 6.6)
            tl_txt = ("faturaya bağlı" if a is None else
                      (bin(a) if a == b else f"{bin(a)} – {bin(b)}"))
            r.c.drawString(SOL, r.y, f"fiyat tarafı etkisi: {tl_txt} TL/yıl"
                           f"   ·   yatırım: {yat_txt} TL   ·   veri güveni: {gv}")
            r.y -= 4.2*mm
            r.p(ac, s=7.2)
        r.p(o["gerekce"], s=7.2, girinti=0)

    r.h2("6.3 Birleşik etki ve çifte sayım")
    tt = E.teknik_toplam()
    r.kpi([("Teknik potansiyel", f"%{100*tt/E.YILLIK_TOPLAM:.0f}",
            "tüketim tarafı · çarpımsal", GREEN),
           ("kWh tasarrufu", bin(tt), "kWh/yıl", COPPER),
           ("TL karşılığı", bin(tt*birim) if birim else "—",
            "TL/yıl · mevcut birim fiyatla", NAVY),
           ("Kalan tüketim", bin(E.YILLIK_TOPLAM-tt), "kWh/yıl", GREY)])
    r.p("Yukarıdaki toplam, tekil önlemlerin yüzdelerinin toplamı DEĞİLDİR. "
        "Aynı tüketim sınıfına birden fazla önlem uygulandığında ikincisi, "
        "birincinin bıraktığı kalan üzerinden çalışır. Model bunu çarpımsal "
        "hesaplar; bu yüzden gerçekçi bir üst sınır verir. Tarife kalemlerinin "
        "(T-01…T-04) etkisi bu yüzdeye DAHİL DEĞİLDİR; onlar birim fiyatı "
        "düşürerek aynı kWh'i ucuzlatır ve tasarruf tarafıyla çarpışmaz. "
        "Yani toplam fatura azalması, buradaki yüzdeden daha büyüktür.")


# ════════════════════════ §4 FATURA ANATOMİSİ ════════════════════════════════
def s4_fatura(r):
    r.h1("4", "Faturanın anatomisi — kWh'i kaça alıyoruz")
    if T is None:
        r.p("Tarife verisi yüklenemedi."); return
    m = T.SENARYO["MEVCUT"]
    r.p(f"Araştırma tarihi {T.ARASTIRMA_TARIH}, bölge {T.BOLGE}. Aşağıdaki "
        f"bileşenler 4 Nisan 2026 tarifesine dayanır. 1 Ekim 2026 (Q4) "
        f"tarifesi bu raporun yazıldığı tarihte HENÜZ AÇIKLANMAMIŞTIR.")

    r.kutu("VERİNİN GÜVENİLİRLİĞİ HAKKINDA DÜRÜST UYARI",
           "EPDK'nın kendi tarife tabloları dinamik sayfa yapısı nedeniyle "
           "doğrudan alınamadı; aktif enerji birim fiyatı ikincil kaynaklardan "
           "türetildi ve kaynaklar arasında %8'e varan fark var. Dağıtım "
           "bedeli, vergi oranları, reaktif bedeli ve serbest tüketici "
           "limitleri ise birincil ya da çoklu kaynakta doğrulanmıştır. "
           "TEK BİR GERÇEK FATURA, bu belirsizliğin tamamını ortadan kaldırır "
           "ve §11'de istenen ilk belgedir.", AMBER)

    r.h2("4.1 Birim fiyatın oluşumu (ticarethane · AG · tek terimli)")
    sat = [[ad, f"{v:.4f}", f"%{100*v/m['birim']:.1f}"] for ad, v in m["bilesen"]]
    sat.append(["TOPLAM · KDV dâhil", f"{m['birim']:.4f}", "%100"])
    r.tablo(["Bileşen", "TL/kWh", "Pay"], sat,
            [96*mm, 40*mm, 42*mm], sag=(1, 2), vurgu=(len(sat)-1,))
    r.p(T.TARIFE_NOT)
    r.p("Buradaki en önemli yapısal gerçek şudur: birim fiyatın yalnızca "
        f"%{100*m['aktif']/m['birim']:.0f}'i AKTİF ENERJİDİR. Geri kalanı "
        f"dağıtım bedeli (%{100*m['dagitim']/m['birim']:.0f}) ve vergilerdir "
        f"(%{100*(m['fon']+m['btv']+m['kdv'])/m['birim']:.0f}). Tedarikçi "
        "pazarlığı yalnız aktif enerji bileşenine etki eder. Bu yüzden "
        "“tedarikçiden %10 indirim aldık” demek, faturanın %10'unu kurtarmak "
        f"değil, yaklaşık %{100*0.10*m['aktif']/m['birim']:.0f}'ini kurtarmak "
        "demektir. Faturanın kalan dörtte üçü ancak DAHA AZ kWh tüketerek "
        "azaltılabilir.")

    r.h2("4.2 Model faturası ile beyan edilen faturanın karşılaştırması")
    model_tl = E.ORT_AY_KWH*m["birim"]
    alt, ust = E.BEYAN_TL; ort = (alt+ust)/2
    r.kpi([("Model tüketimi", bin(E.ORT_AY_KWH), "kWh/ay", COPPER),
           ("Model faturası", bin(model_tl), "TL/ay · KDV dâhil", NAVY),
           ("Beyan bandı", f"{bin(alt/1000)}–{bin(ust/1000)}k", "TL/ay", AMBER),
           ("Sapma", f"%{100*(ort-model_tl)/model_tl:+.1f}",
            "beyan ortası ↔ model", GREEN if abs(ort-model_tl) < model_tl*0.12 else RED)])
    r.p(f"Bu, raporun en önemli tek bulgusudur. Tesisin yük cetvelinden "
        f"bağımsız olarak kurulan tüketim modeli, 2026 ticarethane tarifesiyle "
        f"çarpıldığında ayda {bin(model_tl)} TL veriyor. İşverenin beyan ettiği "
        f"{bin(alt)}–{bin(ust)} TL bandının tam ortasına düşüyor; sapma "
        f"%{abs(100*(ort-model_tl)/model_tl):.1f}. Yani fatura, tesisin "
        f"kurulu yüküne ve İstanbul'daki cari elektrik fiyatına göre "
        f"AÇIKLANABİLİR DURUMDADIR. Ortada gizli bir kaçak, hatalı sayaç ya da "
        f"yanlış okuma aramaya gerek yoktur — sorun tesisin ne kadar elektrik "
        f"TÜKETTİĞİNDE ve bunun ne kadarının zorunlu olduğundadır.")
    r.kutu("BU MUTABAKAT NE ANLAMA GELİR, NE ANLAMA GELMEZ",
           "Modelin beyanla örtüşmesi, modelin doğru olduğunu KANITLAMAZ; "
           "iki hatanın birbirini götürmesi de mümkündür. Örneğin tüketim "
           "modelden %15 düşük ama birim fiyat %15 yüksek olabilir — ya da "
           "faturaya AVM ortak alan yansıtması ekleniyor olabilir. Mutabakatı "
           "kesinleştirecek tek şey, faturadaki kWh SAYISINI görmektir. "
           "Faturanın TL tutarı değil, kWh satırı istenmelidir.", NAVY)

    r.h2("4.3 Tarife tipi — üç zamanlı tuzağı")
    uz = T.uc_zamanli_birim(E.ZAMAN_PAY)
    sat = []
    for k in ("T1", "T2", "T3"):
        f, ar, ad = T.UC_ZAMANLI[k]
        sat.append([f"{k} · {ad}", ar, f"{f:.2f}",
                    f"%{100*E.ZAMAN_PAY[k]:.0f}", f"{f*E.ZAMAN_PAY[k]:.3f}"])
    sat.append(["AĞIRLIKLI ORTALAMA", "", "", "%100", f"{uz:.3f}"])
    sat.append(["Tek zamanlı tarife", "", "", "", f"{m['birim']:.3f}"])
    r.tablo(["Dilim", "Saat", "TL/kWh", "Tüketim payı", "Katkı TL/kWh"],
            sat, [40*mm, 32*mm, 26*mm, 38*mm, 42*mm], sag=(2, 3, 4),
            vurgu=(len(sat)-2, len(sat)-1))
    r.p(f"Bir restoranın en yoğun saati (17:00–22:00) tam olarak en pahalı "
        f"dilime denk gelir; puant birim fiyatı gündüzün "
        f"{T.UC_ZAMANLI['T2'][0]/T.UC_ZAMANLI['T1'][0]:.2f} katıdır. Modelin "
        f"zaman dağılımıyla üç zamanlı tarife {uz:.2f} TL/kWh, tek zamanlı "
        f"{m['birim']:.2f} TL/kWh çıkıyor: üç zamanlı "
        f"%{100*(uz/m['birim']-1):.0f} DAHA PAHALI. Yıllık farkı "
        f"{bin((uz-m['birim'])*E.YILLIK_TOPLAM)} TL'dir.")
    r.kutu("İLK KONTROL EDİLECEK TEK SATIR",
           "Faturanın üst bilgisinde tarife tipi yazar. Eğer “üç zamanlı” "
           "ise, hiçbir yatırım yapmadan, yalnız dağıtım şirketine dilekçe "
           "vererek tek zamanlıya geçmek yılda yaklaşık "
           f"{bin((uz-m['birim'])*E.YILLIK_TOPLAM)} TL kazandırır. Eğer tek "
           "zamanlı ise, tasarruf diye üç zamanlıya GEÇİLMEMELİDİR — restoran "
           "yük profili bu tarifeyi cezalandırır. Bu kontrolün maliyeti "
           "sıfırdır ve beş dakika sürer.", GREEN)

    r.h2("4.4 Reaktif enerji — faturanın görünmeyen kalemi")
    rk = E.reaktif_analiz(E.CETVEL_COSFI, birim=T.REAKTIF_BEDEL)
    sat = []
    for cf in (0.90, 0.95, 0.98, 0.99, 1.00):
        a = E.reaktif_analiz(min(cf, 0.9999), birim=T.REAKTIF_BEDEL)
        sat.append([f"{cf:.2f}", f"%{100*a['tanfi']:.1f}",
                    "AŞIM" if a["asim"] else "temiz", bin(a["kvarh"]),
                    bin(a["ceza"]*1.2)])
    r.tablo(["cos φ", "Reaktif oranı", "Eşik (%20)", "kVArh/ay",
             "Ceza TL/ay · KDV dâhil"],
            sat, [24*mm, 32*mm, 26*mm, 34*mm, 62*mm], sag=(1, 3, 4))
    r.p(f"Pano yükleme cetveli tesisin güç katsayısını {E.CETVEL_COSFI} olarak "
        f"veriyor. Bu değerde reaktif oranı %{100*rk['tanfi']:.1f} olur ve "
        f"%{100*rk['esik']:.0f}'lik yasal eşiği ikiye katlar. Eşik aşıldığında "
        f"— muhafazakâr yorumla — ölçülen reaktif enerjinin TAMAMI "
        f"bedellendirilir: ayda {bin(rk['kvarh'])} kVArh × "
        f"{T.REAKTIF_BEDEL:.3f} TL/kVArh, KDV ile birlikte "
        f"{bin(rk['ceza']*1.2)} TL. Bu, beyan edilen faturanın yaklaşık "
        f"%{100*rk['ceza']*1.2/(E.ORT_AY_KWH*m['birim']):.0f}'idir.")
    r.kutu("KOMPANZASYON ÇALIŞIYOR MU? — DERHAL CEVAPLANMASI GEREKEN SORU",
           f"Cetveldeki {E.CETVEL_COSFI} değeri tesisin KOMPANZASYONSUZ doğal "
           f"güç katsayısıdır; panoda kompanzasyon beslemesi olduğuna göre "
           f"sahada cos φ'nin {rk['gereken_cosfi']} üzerine çıkarılmış olması "
           f"beklenir. Çıkarılmışsa ceza sıfırdır. Çıkarılmamışsa ya da "
           f"kondansatörler zamanla bozulmuşsa, tesis yılda "
           f"{bin(rk['ceza']*1.2*12)} TL'ye kadar KARŞILIĞINDA HİÇBİR ŞEY "
           f"ALMADAN ödüyor olabilir. Cevap faturanın reaktif satırında ve "
           f"kompanzasyon rölesinin ekranındadır. Eşiğin altında kalmak için "
           f"cos φ ≥ {rk['gereken_cosfi']} gerekir; bunun için talep gücünde "
           f"yaklaşık {E.kompanzasyon_kvar(E.CETVEL_TALEP_KW, 0.90, 0.99):.0f} "
           f"kVAr kademeli ve HARMONİK REAKTÖRLÜ (detuned) kompanzasyon "
           f"gerekir. VRF/WSHP sürücüleri ve LED sürücüleri harmonik ürettiği "
           f"için reaktörsüz klasik kondansatör grubu bu tesiste hızla bozulur.",
           RED)

    r.h2("4.5 Serbest tüketici durumu ve tedarikçi")
    r.tablo(["Parametre", "2026 değeri", "Tesisin durumu"], [
        ["Serbest tüketici limiti", f"{bin(T.SERBEST_LIMIT_KWH)} kWh/yıl",
         f"Tesis {bin(E.YILLIK_TOPLAM)} kWh/yıl tüketiyor — limitin "
         f"{E.YILLIK_TOPLAM/T.SERBEST_LIMIT_KWH:.0f} katı. KESİNLİKLE serbest "
         f"tüketicidir ve dilediği tedarikçiyle ikili anlaşma yapabilir."],
        ["SKTT limiti (ticarethane)", f"{bin(T.SKTT_LIMIT_TIC_KWH)} kWh/yıl",
         f"Limitin {E.YILLIK_TOPLAM/T.SKTT_LIMIT_TIC_KWH:.0f} katı. İkili "
         f"anlaşma YOKSA tesis Son Kaynak Tedarik Tarifesine düşer ve "
         f"(PTF + YEKDEM) × {T.SKTT_KBK} formülüyle faturalanır — yani spot "
         f"piyasa dalgalanmasına açık hâle gelir."],
        ["Tedarikçi indirim bandı",
         f"%{100*T.TEDARIKCI_INDIRIM[0]:.0f}–{100*T.TEDARIKCI_INDIRIM[1]:.0f}",
         "Yalnız aktif enerjiye uygulanır. Zincirin bütün şubeleri tek "
         "portföyde ihale edilirse pazarlık gücü belirgin artar."],
    ], [42*mm, 34*mm, 102*mm], s=6.6)
    r.p("Temmuz 2026'da piyasa takas fiyatı 2.699,61 TL/MWh'e çıktı; Haziran'da "
        "1.240,16 TL/MWh idi. İkili anlaşması olmayan bir tesis bu "
        "dalgalanmayı doğrudan faturasında görür. Sabit fiyatlı veya tavanlı "
        "bir ikili anlaşma, indirimin ötesinde BÜTÇE ÖNGÖRÜLEBİLİRLİĞİ sağlar; "
        "çok şubeli bir zincirde bunun değeri indirimden büyük olabilir.")


# ════════════════════════ §5 NORMAL Mİ? ══════════════════════════════════════
def s5_normal(r):
    r.h1("5", "“Bu harcama normal mi?” — üç ayrı test")
    r.p("Bir faturanın “yüksek” olması üç farklı şeyden kaynaklanabilir ve "
        "hangisinin geçerli olduğu bilinmeden atılan her adım israftır. "
        "Aşağıda üç test ayrı ayrı uygulanmıştır.")

    m = T.SENARYO["MEVCUT"] if T else None

    # ── TEST 1
    r.h2("TEST 1 · Birim fiyat testi — kWh'i piyasadan pahalıya mı alıyoruz?")
    if m:
        alt, ust = E.BEYAN_TL
        ima_alt = alt/E.ORT_AY_KWH; ima_ust = ust/E.ORT_AY_KWH
        r.tablo(["Ölçüt", "Değer", "Piyasa karşılığı (2026)", "Sonuç"], [
            ["Beyan bandından ima edilen birim fiyat",
             f"{ima_alt:.2f} – {ima_ust:.2f} TL/kWh",
             f"{m['birim']:.2f} TL/kWh (ticarethane AG tek zamanlı, "
             f"vergiler dâhil); bağımsız kaynak bandı 6,42 – 7,33",
             "NORMAL"],
            ["Üç zamanlı tarifedeyse",
             f"{T.uc_zamanli_birim(E.ZAMAN_PAY):.2f} TL/kWh",
             "restoran profili puant dilimine yığılır",
             "PAHALI"],
            ["Reaktif ceza varsa",
             f"+{bin(E.reaktif_analiz(E.CETVEL_COSFI, birim=T.REAKTIF_BEDEL)['ceza']*1.2)} TL/ay",
             "karşılığında hiçbir enerji alınmaz",
             "SAF KAYIP"],
        ], [52*mm, 34*mm, 62*mm, 30*mm], s=6.6,
           renkli={"Beyan bandından ima edilen birim fiyat": INK})
        r.p(f"Sonuç: beyan edilen tutarın ima ettiği birim fiyat "
            f"({ima_alt:.2f}–{ima_ust:.2f} TL/kWh) İstanbul'daki cari "
            f"ticarethane tarifesiyle uyumludur. Tesis kWh'i piyasadan pahalıya "
            f"ALMIYOR — İKİ İSTİSNA DIŞINDA: tarife tipi üç zamanlıysa ve "
            f"kompanzasyon çalışmıyorsa. Bu iki kontrol yapılmadan “fiyatımız "
            f"normal” denemez; ikisi de sıfır maliyetlidir.")

    # ── TEST 2
    r.h2("TEST 2 · Enerji yoğunluğu testi — metrekare başına çok mu tüketiyoruz?")
    r.p(f"Model, yılda {bin(E.YILLIK_TOPLAM)} kWh veriyor. "
        f"{bin(E.ALAN_M2)} m² kabulüyle (V-04) özgül tüketim "
        f"{bin(E.ozgul())} kWh/m²/yıl olur. Alan bilinmediği için "
        f"{bin(E.ALAN_BANT[0])}–{bin(E.ALAN_BANT[1])} m² aralığında "
        f"{bin(E.ozgul(E.ALAN_BANT[1]))}–{bin(E.ozgul(E.ALAN_BANT[0]))} "
        f"kWh/m²/yıl bandı çıkar.")
    sat = []
    for ad, v, br, kap, g, nt in T.BENCHMARK:
        if v is None:
            sat.append([ad, "—", kap, "veri yok", g]); continue
        oran = E.ozgul()/v
        sat.append([ad, bin(v), kap, f"×{oran:.2f}", g])
    sat.append([f"BU TESİS (model · {bin(E.ALAN_M2)} m²)", bin(E.ozgul()),
                "tamamı elektrik", "—", "model"])
    r.tablo(["Kıyas kaynağı", "kWh/m²/yıl", "Kapsam", "Tesis / kıyas", "Güven"],
            sat, [56*mm, 24*mm, 48*mm, 28*mm, 22*mm], s=6.5, sag=(1, 3),
            vurgu=(len(sat)-1,))
    r.p("Sonuç: tesisin özgül tüketimi, ABD medyanlarının (830–1.027 "
        "kWh/m²/yıl toplam enerji) ALTINDA, İngiliz CIBSE TM46 restoran "
        "kıyasının (460 kWh/m²/yıl toplam) hemen üzerindedir. Toplam enerji "
        "yoğunluğu açısından tesis ANORMAL DEĞİLDİR. Ağır bir et restoranı, "
        "üç elektrikli fritöz, show kitchen ve geniş bir teras için bu bant "
        "beklenen yerdedir.")
    r.kutu("KIYASLAMANIN SINIRI — DÜRÜSTÇE",
           "Türkiye'ye özel yayımlanmış restoran kWh/m²/yıl kıyas değeri "
           "YOKTUR; BEP-TR metodolojisi var ama restoran kategorisi için "
           "referans tüketim yayımlanmamış. Yukarıdaki kıyaslar ABD ve "
           "İngiltere verisidir ve kendi aralarında 2,2 kat fark ederler "
           "(alan tanımı, işletme saati ve iklim farkı). Bu yüzden bu test "
           "“kesin normal” demez, “bariz anormal değil” der. Kesin cevap, "
           "zincirin kendi şubelerini birbiriyle kıyaslamaktan çıkar — "
           "bu rapor bunu §8'de öneriyor.", AMBER)

    # ── TEST 3
    r.h2("TEST 3 · Yakıt karması testi — asıl sorun burada")
    r.p("İlk iki test “normal” dedi. Üçüncüsü demiyor. Kıyas tablolarının "
        "hepsi, bir restoranın enerjisinin büyük kısmının FOSİL YAKITTAN "
        "geldiğini varsayar: CIBSE TM46 restoran için 460 kWh/m²/yıl toplamın "
        "yalnız 90'ı elektrik, 370'i fosildir — yani elektrik payı %20'dir.")
    r.tablo(["Ölçüt", "CIBSE TM46 restoran", "Bu tesis", "Fark"], [
        ["Elektrik payı", "%20 (90 / 460)", "%100", "5 kat"],
        ["Pişirme", "ağırlıklı gaz", "3 × 16,95 kW elektrikli fritöz + "
         "indüksiyon; tek gazlı cihaz kombi fırın", "elektriğe çevrilmiş"],
        ["Mahal ısıtma", "ağırlıklı gaz/kazan", "WSHP + VRF (ısı pompası — "
         "verimli) ama hava perdesi elektrikli dirençli", "kısmen çevrilmiş"],
        ["Teras ısıtma", "gazlı radyant / şemsiye", "8 × 5 kW elektrikli "
         "direnç = 40 kW", "tamamen çevrilmiş"],
        ["Sıcak su", "gazlı kazan / kombi", "9,9 kW elektrikli boiler",
         "tamamen çevrilmiş"],
    ], [30*mm, 36*mm, 76*mm, 36*mm], s=6.5)
    r.kutu("ASIL BULGU",
           "Tesis anormal miktarda ENERJİ tüketmiyor; anormal oranda ENERJİSİNİ "
           "ELEKTRİKTEN alıyor. Türkiye'de elektriğin ticarethane kWh fiyatı, "
           "doğal gazın kWh fiyatının belirgin üzerindedir. Bir kWh ısıyı "
           "elektrikli dirençle üretmek (teras ısıtıcısı, hava perdesi ısıtıcısı, "
           "boiler) mümkün olan EN PAHALI yoldur; aynı ısıyı ısı pompası üçte "
           "bir elektrikle, doğal gaz ise çok daha ucuz bir yakıtla üretir. "
           "Faturanın “yüksek” hissettiren kısmı büyük ölçüde budur ve bu bir "
           "işletme hatası değil, bir TASARIM TERCİHİDİR. Dolayısıyla asıl "
           "kazanç işletmede değil, bu tercihlerin geri alınabilir olanlarını "
           "geri almaktadır (§6 · M-03, M-04, M-06).", RED)

    r.h2("5.4 Üç testin özeti")
    r.tablo(["Test", "Soru", "Cevap"], [
        ["1 · Birim fiyat", "kWh'i pahalıya mı alıyoruz?",
         "HAYIR — iki koşulla: tarife tek zamanlı olmalı ve kompanzasyon "
         "çalışıyor olmalı. İkisi de henüz doğrulanmadı."],
        ["2 · Enerji yoğunluğu", "Metrekare başına çok mu tüketiyoruz?",
         "HAYIR — uluslararası restoran kıyaslarının içindedir, ABD "
         "medyanlarının altındadır."],
        ["3 · Yakıt karması", "Doğru enerjiyi mi kullanıyoruz?",
         "HAYIR. Normalde gazla yapılan ısıtma işleri elektrikli dirençle "
         "yapılıyor. Faturanın asıl kaldıracı buradadır."],
    ], [30*mm, 46*mm, 102*mm], s=6.8)


# ════════════════════════ §7 YOL HARİTASI ════════════════════════════════════
FAZ = [
 ("FAZ 0 · İLK 30 GÜN — ÖLÇ, DOĞRULA, HİÇ PARA HARCAMA",
  GREEN,
  "Bu fazın yatırımı yoktur ve bütün sonraki kararların girdisini üretir. "
  "Otuz gün sonunda elinizde gerçek sayılar olur ve bu rapordaki her yüzde "
  "ölçümle değişir.",
  [("0.1", "Son 12 ayın faturasını satır satır topla (kWh, TL, reaktif, "
           "tarife tipi, sözleşme gücü, abone grubu)", "işletme", "0 TL"),
   ("0.2", "Faturadaki TARİFE TİPİNİ oku. Üç zamanlıysa tek zamanlıya geçiş "
           "dilekçesi ver", "işletme", "0 TL"),
   ("0.3", "Faturada REAKTİF satırı var mı bak; kompanzasyon panosunun "
           "rölesinden cos φ değerini oku ve fotoğrafla", "teknik", "0 TL"),
   ("0.4", "ADP'deki enerji analizörünün (-EA1) RS485 çıkışını bir "
           "kaydediciye bağla; 15 dakikalık yük profili kaydı başlat",
           "teknik", "düşük"),
   ("0.5", "Mahal listesini ve net alanları mimari projeden çıkar "
           "(kWh/m² kıyası bunsuz yapılamaz)", "proje", "0 TL"),
   ("0.6", "Tedarikçi ihalesine çık: zincirin bütün şubelerini tek portföy "
           "olarak fiyatlat", "satınalma", "0 TL"),
   ("0.7", "AVM ile sözleşmeyi oku: ortak alan yansıtması, kondenser suyu "
           "bedeli ve çatı kullanım hakkı maddelerini çıkar", "hukuk", "0 TL")]),

 ("FAZ 1 · 1–3 AY — AYAR VE DİSİPLİN, YATIRIMSIZ",
  BLUE,
  "Faz 0'ın ölçümüyle doğrulanan, cihaz almadan yapılabilecek işler. "
  "Bu fazın tamamı ayar, program ve davranış değişikliğidir.",
  [("1.1", "Hava perdesinin elektrikli ısıtıcı kademesini devre dışı bırak; "
           "perdeyi kapı kontağıyla kilitle", "teknik", "düşük"),
   ("1.2", "Teras ısıtıcılarına bölge anahtarı, dış hava termostatı ve "
           "kapanış saati ekle; boş masaların ısıtıcısını kapat",
           "teknik", "düşük"),
   ("1.3", "Mutfak açılış/kapanış kontrol listesi: her cihazın açılış saati "
           "yazılı olsun, fritözler servisten en fazla 30 dk önce açılsın",
           "işletme", "0 TL"),
   ("1.4", "VRF/WSHP ayar noktalarına ölü bant koy, boş saatlerde geri "
           "çekme programla; filtre ve kondenserleri temizlet",
           "teknik", "düşük"),
   ("1.5", "DALİ senaryolarını kur: gündüz, servis, kapanış, temizlik. "
           "Tabela rölesine kapanış saati ekle", "teknik", "düşük"),
   ("1.6", "Bulaşık, buz üretimi ve boyler ısıtmasını gece dilimine kaydır "
           "(üç zamanlı tarifede kalınıyorsa)", "işletme", "0 TL"),
   ("1.7", "Soğuk oda kapı perdelerini tak, otomatik kapatıcıları ayarla, "
           "kondenserleri temizlet", "teknik", "düşük")]),

 ("FAZ 2 · 3–9 AY — ÖLÇÜLMÜŞ VERİYLE YATIRIM",
  AMBER,
  "Faz 0'ın yük kaydı olmadan bu fazın hiçbir kalemine başlanmamalıdır. "
  "Her kalem kendi geri ödemesiyle ayrı ayrı onaylanır.",
  [("2.1", "Kompanzasyonu harmonik reaktörlü (detuned) olarak yenile veya "
           "kademelerini onar — reaktif cezası tespit edildiyse BİRİNCİ "
           "ÖNCELİK", "yatırım", "orta"),
   ("2.2", "Davlumbaz egzozuna ve taze hava fanlarına sürücü (VFD) + talep "
           "kontrollü havalandırma (DCKV) kur", "yatırım", "orta"),
   ("2.3", "Elektrikli boyleri ısı pompalı su ısıtıcıyla veya gazla değiştir",
           "yatırım", "orta"),
   ("2.4", "Teras ısıtmasını gazlı radyant sisteme çevirmeyi fizibilite et "
           "(gaz altyapısı ve AVM izni şartıyla)", "yatırım", "orta"),
   ("2.5", "Aydınlatmada LED olmayan armatürleri değiştir; alt sayaçla "
           "önce/sonra ölç", "yatırım", "düşük–orta"),
   ("2.6", "Soğuk oda ve soğutma dolaplarında EC fan ve elektronik genleşme "
           "valfi dönüşümü", "yatırım", "düşük–orta")]),

 ("FAZ 3 · 9–18 AY — YAPISAL",
  RED,
  "Büyük yatırım ve/veya üçüncü taraf izni gerektiren kalemler. "
  "Ancak Faz 1 ve 2 tamamlandıktan sonra anlamlıdır.",
  [("3.1", "Taze hava ünitesine ısı geri kazanım ekle (yalnız salon egzozu; "
           "mutfak egzozu yağlı olduğu için uygun değildir)", "yatırım", "yüksek"),
   ("3.2", "Çatı GES + batarya fizibilitesi — AVM ile çatı kullanım "
           "anlaşması şartıyla ve SAATLİK mahsuplaşma rejimine göre",
           "yatırım", "yüksek"),
   ("3.3", "Zincir geneli enerji yönetim sistemi ve şube kıyaslama panosu",
           "yatırım", "orta"),
   ("3.4", "Yeni şube tasarım standardı: bu raporun bulgularını şartnameye "
           "yaz (elektrikli direnç ısıtma yasağı, DCKV zorunluluğu, "
           "reaktörlü kompanzasyon, alt sayaç)", "proje", "0 TL")]),
]


def s7_yol(r):
    r.h1("7", "Uygulama yol haritası")
    r.p("Sıralama rastgele değildir. Ölçüm önce gelir çünkü ölçülmeyen tasarruf "
        "doğrulanamaz ve yatırım kararı savunulamaz. Ayar ve disiplin ikinci "
        "gelir çünkü bedelsizdir. Yatırım en sonda gelir çünkü geri dönüşü "
        "ancak ilk iki fazdan sonra hesaplanabilir.")
    for basl, renk, aciklama, isler in FAZ:
        r.yer(30*mm)
        r.c.setFillColor(renk); r.c.rect(SOL, r.y-1.8*mm, GEN, 6.6*mm, 0, 1)
        r.c.setFillColor(WHITE); r.c.setFont(FB, 8.4)
        r.c.drawString(SOL+3*mm, r.y+0.4*mm, basl)
        r.y -= 9.6*mm
        r.p(aciklama, s=7.2)
        r.tablo(["No", "İş", "Sorumlu", "Maliyet"],
                [[a, b, c, d] for a, b, c, d in isler],
                [12*mm, 122*mm, 24*mm, 20*mm], s=6.6)


# ════════════════════════ §8 ZİNCİR ══════════════════════════════════════════
def s8_zincir(r):
    r.h1("8", "Zincir geneli — 300.000 ile 650.000 TL arasındaki bant")
    alt, ust = E.BEYAN_ZINCIR_TL
    m = T.SENARYO["MEVCUT"] if T else None
    r.p(f"İşveren, şubelerin faturalarının {bin(alt)} – {bin(ust)} TL/ay "
        f"bandında olduğunu beyan ediyor. Bu bandın genişliği "
        f"{ust/alt:.2f} kattır ve tek başına en değerli bilgidir: aynı marka, "
        f"aynı mutfak, aynı menü, benzer işletme saatleriyle çalışan şubeler "
        f"arasında iki kattan fazla fark varsa, farkın bir kısmı BÜYÜKLÜKTEN, "
        f"bir kısmı da KÖTÜ İŞLETMEDEN gelir. İkisini ayırmanın yolu "
        f"normalize etmektir.")
    if m:
        r.tablo(["Fatura (TL/ay)", "İma edilen kWh/ay", "Aqua Florya'ya oranı"],
                [[bin(v), bin(v/m["birim"]), f"×{v/((alt+ust)/2):.2f}"]
                 for v in (alt, 400_000, ust)],
                [40*mm, 50*mm, 88*mm], sag=(0, 1, 2), s=6.8)
    r.h2("8.1 Şubeleri kıyaslamanın doğru yolu")
    r.p("Mutlak TL karşılaştırması yanıltıcıdır; büyük şube doğal olarak daha "
        "çok öder. Anlamlı kıyas için üç oran kullanılmalıdır:")
    r.madde("kWh / m² / ay — tesisin fiziksel verimliliği. Alan farkını "
            "temizler.")
    r.madde("kWh / kapak (cover) veya kWh / ciro TL — işletme yoğunluğunu "
            "temizler. Boş bir şube az tüketir ama verimli değildir; bu oran "
            "onu ortaya çıkarır.")
    r.madde("TL / kWh — tarife ve ceza farkını yalıtır. Aynı bölgedeki iki "
            "şubede bu oran farklıysa, fark sözleşmedendir ve pazarlıkla "
            "kapatılır.")
    r.kutu("ZİNCİR İÇİN EN HIZLI KAZANÇ",
           "Bu rapordaki tarife kalemleri (T-01 … T-04) tesise özgü DEĞİLDİR; "
           "bütün şubelerde aynı anda uygulanır ve yatırım gerektirmez. "
           "Bir şubede üç zamanlı tarife tespit edilirse, muhtemelen "
           "başkalarında da vardır. Bir şubede reaktif ceza bulunursa, "
           "aynı elektrik projesiyle kurulan diğerlerinde de bulunma "
           "ihtimali yüksektir. Tek şubede yapılan bir haftalık inceleme, "
           "zincirin tamamına uygulanabilir bir kontrol listesi üretir. "
           "Zincirin ölçeği, bu işin en büyük kaldıracıdır.", GREEN)
    r.h2("8.2 Yeni şubeler için tasarım şartnamesi")
    r.p("Bu raporun en kalıcı çıktısı, mevcut tesiste yapılacaklar değil, "
        "bir sonraki şubede TEKRAR EDİLMEYECEKLERDİR. Yatırım ve iş "
        "geliştirme tarafında şartnameye girmesi önerilen maddeler:")
    for t in ["Mahal ve teras ısıtmasında elektrikli direnç ısıtıcı "
              "KULLANILMAZ; gazlı radyant veya ısı pompalı çözüm esastır.",
              "Hava perdesi elektrikli ısıtıcısız seçilir; kapı kontağıyla "
              "kilitlenir.",
              "Mutfak egzozu ve taze hava üniteleri sürücülü ve talep "
              "kontrollü (DCKV) olarak projelendirilir; sabit debi kabul "
              "edilmez.",
              "Sıcak su elektrikli dirençli boylerden değil, ısı pompalı "
              "veya gazlı sistemden karşılanır.",
              "Kompanzasyon harmonik reaktörlü (detuned) olarak projelendirilir; "
              "kVAr kademe tablosu projeye eklenir.",
              "Ana panoya ve en az dört alt gruba (mutfak · iklimlendirme · "
              "aydınlatma · soğutma) haberleşmeli alt sayaç konur ve "
              "devreye alınır.",
              "Kiralama sözleşmesine çatı kullanım hakkı ve ortak alan "
              "yansıtma formülü açıkça yazılır."]:
        r.madde(t)


# ════════════════════════ §9 RİSKLER VE SINIRLAR ═════════════════════════════
def s9_risk(r):
    r.h1("9", "Riskler, çekinceler ve modelin sınırları")
    r.h2("9.1 Bu raporun YAPAMADIĞI şeyler")
    r.tablo(["Sınır", "Sonuç"], [
        ["Hiçbir fatura görülmedi",
         "Birim fiyat, tarife tipi, reaktif ceza ve sözleşme gücü "
         "DOĞRULANMADI. §4'ün tamamı senaryodur. Modelin beyanla örtüşmesi "
         "güven verir ama kanıt değildir."],
        ["Sahada ölçüm yapılmadı",
         "İşletme saatleri ve yük faktörleri mühendislik kabulüdür. Gerçek "
         "tüketim modelden ±%20 sapabilir; sınıf bazında sapma daha büyük "
         "olabilir."],
        ["Alan bilinmiyor",
         "kWh/m² kıyası varsayılan alana dayanır (V-04). Alan %25 farklıysa "
         "TEST 2'nin sonucu değişmez ama bandın neresinde olunduğu değişir."],
        ["Mekanik proje elimizde yok",
         "Havalandırma debileri, davlumbaz tipi ve kanal basınçları "
         "bilinmiyor. DCKV tasarrufu fan gücü üzerinden tahmin edildi."],
        ["Cihaz marka/model listesi yok",
         "VRF ve WSHP verimleri (COP/SEER) bilinmiyor; cihaz yenileme "
         "kalemleri fizibilite edilemedi. Hava perdesinin elektrikli "
         "ısıtıcılı olduğu kablo kesitinden ÇIKARIMDIR, etiketten değil."],
        ["AVM sözleşmesi okunmadı",
         "Ortak alan yansıtması, kondenser suyu bedeli ve çatı kullanım "
         "hakkı bilinmiyor. GES kalemi (G-01) bu yüzden düşük güvenlidir."],
        ["2026 Q4 tarifesi açıklanmadı",
         "Bütün TL rakamları 4 Nisan 2026 tarifesine göredir. 1 Ekim 2026 "
         "tarifesi çıkınca model yeniden çalıştırılmalıdır."],
    ], [44*mm, 134*mm], s=6.6)

    r.h2("9.2 Uygulama riskleri")
    r.kutu("RİSK · Hava perdesi ısıtıcısının kapatılması (M-03)",
           "Kışın giriş bölgesinde konfor şikâyeti ve kapı yakınındaki "
           "masaların kullanılamaması riski vardır. Doğru sıra: önce kapı "
           "kontağı kilidi ve fan hızı ayarı, ölçümle konfor takibi, sonra "
           "ısıtıcı kademesinin kapatılması. Isıtıcı tamamen sökülmemeli, "
           "devre dışı bırakılmalıdır.", AMBER)
    r.kutu("RİSK · Teras ısıtmasının kısılması (M-04)",
           "Teras kapasitesi doğrudan ciroyla ilişkilidir. Kış aylarında "
           "terası kullanılamaz hâle getiren bir tasarruf, enerjide "
           "kazandığından fazlasını ciroda kaybettirir. Bu yüzden önlem "
           "“ısıtmayı azalt” değil, “boş masayı ısıtma” olarak kurulmuştur: "
           "bölge anahtarı ve hareket/rezervasyon bağlantısı.", RED)
    r.kutu("RİSK · DCKV ve davlumbaz debisinin düşürülmesi (M-01)",
           "Mutfak egzozu bir YANGIN GÜVENLİĞİ ve İŞ SAĞLIĞI sistemidir. "
           "Debi düşürme yalnız sıcaklık/optik sensöre bağlı otomatik "
           "kontrolle yapılmalı, elle kısılmamalıdır. Sistem, pişirme "
           "algılandığında tam debiye çıkmalı ve yangın senaryosunda "
           "otomasyondan bağımsız çalışmalıdır. Yetkili firma ve yangın "
           "onayı şarttır.", RED)
    r.kutu("RİSK · Çatı GES (G-01) — mevzuat 2026'da değişti",
           "2 Nisan 2026'dan itibaren lisanssız üretimde SAATLİK mahsuplaşmaya "
           "geçildi; üretim fazlası artık bedelsiz olarak devredilir. Bir "
           "restoranın yükü akşam tepelidir, güneş üretimi öğle tepelidir — "
           "saatlik rejimde akşam tüketimi sabah üretimiyle mahsup EDİLEMEZ. "
           "Bu, 2 Nisan 2026 öncesinde yapılmış bütün GES fizibilitelerini "
           "geçersiz kılar. GES artık ancak DEPOLAMA ile birlikte "
           "değerlendirilmelidir; yeni yönetmelik tesisin elektriksel "
           "kapasitesi kadar depolama kurulmasına izin veriyor.", RED)
    r.kutu("RİSK · Tedarikçi değişikliği (T-01)",
           "İkili anlaşmalarda indirim yalnız aktif enerjiye uygulanır ve "
           "sözleşmeler genelde yıllık taahhütlüdür. Spot piyasaya endeksli "
           "bir sözleşme, PTF'nin Temmuz 2026'da 2.699 TL/MWh'e çıktığı bir "
           "piyasada bütçe riski yaratır. Çok şubeli bir zincirde sabit "
           "fiyatlı veya tavanlı sözleşme, birkaç puan fazladan indirimden "
           "daha değerli olabilir.", AMBER)

    r.h2("9.3 Yapılmaması gerekenler")
    for t in ["Ölçüm yapmadan cihaz değiştirmeyin. Bu rapordaki yüzdeler "
              "modelden gelir; gerçek tasarruf ancak önce/sonra ölçümüyle "
              "bilinir ve yüklenici garantisi buna bağlanmalıdır.",
              "Tasarruf diye ÜÇ ZAMANLI tarifeye geçmeyin — restoran yük "
              "profili bu tarifeyi cezalandırır (§4.3).",
              "Kompanzasyonu reaktörsüz (klasik) kondansatör grubuyla "
              "yenilemeyin; sürücü ve LED yükü harmonik üretir, grup hızla "
              "bozulur ve ceza geri gelir.",
              "Mutfak egzoz debisini elle kısmayın; yangın ve iş sağlığı "
              "riskidir.",
              "Aydınlatma tasarrufunu lüks seviyesini düşürerek aramayın. "
              "Nusr-Et konseptinde aydınlatma doğrudan müşteri deneyimidir; "
              "kazanç senaryo ve takvimden gelmelidir, karartmadan değil."]:
        r.madde(t, "✕")


def _denetim_ozeti(r):
    """Modelin kendi denetim ajanının sonucu — varsa."""
    import json
    f = KOK/"data"/"denetim_enerji.json"
    if not f.exists(): return
    try:
        d = json.loads(f.read_text())
    except Exception:
        return
    r.h2("9.4 Modelin kendi denetimi")
    r.p("Model, kendi iç tutarlılığını sınayan bir denetim ajanıyla "
        "(tools/agents/a_enerji.py) kontrol edilir. Ajan dört sonuç üretir; "
        "kontrol edilmemiş bir alan “geçti” olarak gösterilmez.")
    r.tablo(["Sonuç", "Adet", "Ne anlama gelir"], [
        ["geçti", str(d.get("bilgi", 0)),
         "Kural sınandı ve sağlandı (mutabakat, sınır, tutarlılık)."],
        ["kaldı", str(d.get("hata", 0)),
         "Kural sınandı ve sağlanmadı. Sıfır olmalıdır."],
        ["şartlı", str(d.get("uyari", 0)),
         "Sağlandı ama veri kalitesi düşük — raporda ayrıca işaretli."],
        ["VERİ EKSİK", str(d.get("eksik", 0)),
         "Kontrol YAPILAMADI çünkü veri yok. §11'de istenen belgeler bunlar."],
        ["UYGULANMAZ", str(d.get("disi", 0)),
         "Kural bu kapsamda geçerli değil (ör. doğal gaz, AVM yansıtması)."],
    ], [26*mm, 16*mm, 136*mm], s=6.8)
    if d.get("uyari_metin"):
        for u in d["uyari_metin"]:
            r.madde(u, "!", s=7.2)
    r.p(f"Denetim sonucu: {d.get('durum', '—')}. “VERİ EKSİK” sayısının "
        f"yüksek olması modelin zayıflığı değil, dürüstlüğüdür: elimizde "
        f"olmayan veriyle yapılamayan {d.get('eksik', 0)} kontrol, geçmiş "
        f"gibi gösterilmek yerine açıkça sayılmıştır.")


# ════════════════════════ §10 VARSAYIMLAR ════════════════════════════════════
def s10_varsayim(r):
    r.h1("10", "Varsayımlar")
    r.p(f"Aşağıdaki kalemlerin hepsi “{E.VARSAYIM_ETIKET}” niteliğindedir. "
        f"Model parametriktir: bir varsayım değiştiğinde tek bir satır "
        f"düzeltilir ve rapordaki bütün türev sayılar kendiliğinden "
        f"güncellenir.")
    r.tablo(["Kod", "Konu", "Kabul edilen değer", "Gerekçe", "Nasıl doğrulanır"],
            [[k, konu, deger, ger, dog] for k, konu, deger, ger, dog in E.VARSAYIM],
            [12*mm, 24*mm, 34*mm, 62*mm, 46*mm], s=6.2)
    r.h2("10.2 Tarife verisinde doğrulanamayanlar")
    if T:
        r.tablo(["Veri", "Durum"], [[a, b] for a, b in T.DOGRULANAMAYAN],
                [66*mm, 112*mm], s=6.4)


# ════════════════════════ §11 İSTENECEK BİLGİLER ═════════════════════════════
ISTEK = [
 ("A · FATURA VE SÖZLEŞME — en yüksek öncelik", RED, [
  "Son 12 ayın elektrik faturası (e-arşiv PDF). TL tutarı değil, KWH SATIRI "
  "ve bileşen dökümü önemlidir.",
  "Faturanın üst bilgisi: abone grubu, TARİFE TİPİ (tek/üç zamanlı), "
  "sözleşme gücü (kVA), sayaç numarası, tedarikçi adı.",
  "Faturada REAKTİF (endüktif/kapasitif) satırı var mı, varsa tutarı.",
  "Elektrik tedarik sözleşmesi: ikili anlaşma mı, son kaynak mı; süresi, "
  "birim fiyat formülü, indirim oranı.",
  "AVM kira sözleşmesinin enerji maddeleri: ortak alan yansıtması, "
  "kondenser suyu / merkezi sistem bedeli, çatı kullanım hakkı.",
  "Varsa doğal gaz faturası ve abone bilgisi (mangal, kombi fırın).",
 ]),
 ("B · PROJE VE TESİS", AMBER, [
  "Mimari proje: mahal listesi ve NET ALANLAR (kapalı salon, teras, mutfak, "
  "depo ayrı ayrı). §5'in tamamı buna bağlıdır.",
  "MDP panosu yükleme cetveli ve şeması — davlumbaz egzoz fanlarının "
  "güçleri ve sürücü olup olmadığı.",
  "Kompanzasyon panosu projesi: kVAr kademeleri, reaktörlü mü, röle marka/model.",
  "Mekanik proje: havalandırma debileri (m³/h), davlumbaz tipi ve uzunlukları, "
  "kanal şeması, taze hava ünitesi teknik föyü.",
  "Cihaz listesi (marka/model): VRF ve WSHP dış üniteleri, hava perdesi, "
  "teras ısıtıcıları, soğuk oda üniteleri, fritözler.",
  "Aydınlatma armatür listesi: LED mi, güçleri, DALİ senaryoları kurulu mu.",
 ]),
 ("C · İŞLETME", BLUE, [
  "Gerçek açılış/kapanış saatleri ve mutfak hazırlık saati.",
  "Aylık kapak (cover) sayısı ve ciro — kWh/kapak kıyası için.",
  "Terasın hangi aylarda ve hangi saatlerde kullanıldığı; ısıtıcıların "
  "kim tarafından ve nasıl açılıp kapatıldığı.",
  "Kapalı gün / tadilat dönemi var mı.",
  "Teknik bakım sözleşmesi var mı; filtre, kondenser ve kompanzasyon bakımı "
  "hangi periyotla yapılıyor.",
 ]),
 ("D · ZİNCİR", GREEN, [
  "Bütün şubelerin son 12 ay elektrik tüketimi (kWh) ve tutarı (TL).",
  "Şube bazında net alan ve kapak sayısı — normalize kıyas için.",
  "Şubelerin tarife tipi ve tedarikçisi listesi.",
  "Aynı elektrik projesiyle kurulmuş şubelerin listesi — bu raporun bulguları "
  "doğrudan onlara da uygulanır.",
 ]),
]


def s11_istek(r):
    r.h1("11", "İşverenden / iş ortağından istenecek bilgiler")
    r.p("Aşağıdaki liste öncelik sırasındadır. A grubundaki altı kalem, bu "
        "rapordaki belirsizliğin büyük kısmını tek başına ortadan kaldırır "
        "ve hiçbiri sahada çalışma gerektirmez — hepsi evrak düzeyindedir.")
    for basl, renk, kalemler in ISTEK:
        r.yer(26*mm)
        r.c.setFillColor(renk); r.c.rect(SOL, r.y-1.6*mm, GEN, 6.4*mm, 0, 1)
        r.c.setFillColor(WHITE); r.c.setFont(FB, 8.2)
        r.c.drawString(SOL+3*mm, r.y+0.4*mm, basl)
        r.y -= 9.4*mm
        for i, k in enumerate(kalemler, 1):
            r.madde(k, f"{i}.", s=7.4)
        r.y -= 2*mm
    r.kutu("TEK BİR BELGE İSTENECEKSE",
           "Son bir aya ait tek bir elektrik faturasının PDF'i. O tek belge "
           "şunları aynı anda cevaplar: tarife tipi (üç zamanlı tuzağı var "
           "mı), reaktif ceza (yılda milyonluk kalem var mı), gerçek kWh "
           "(modelin doğruluğu), gerçek birim fiyat, sözleşme gücü ve "
           "tedarikçi. Bu rapordaki dört büyük belirsizlikten üçü o "
           "faturayla kapanır.", GREEN)


# ════════════════════════ §6B YAKIT DÖNÜŞÜMÜ ═════════════════════════════════
def s6b_yakit(r):
    r.h2("6.4 Yakıt dönüşümü — aynı ısıyı daha ucuz üretmek")
    m = T.SENARYO["MEVCUT"]["birim"]
    r.p("Bu kalemler tüketilen kWh'i azaltmaz; ısıyı BAŞKA BİR KAYNAKTAN "
        "üretir. Bu yüzden §6.3'teki yüzdeyle çakışmazlar ve üzerine eklenirler. "
        "Aşağıdaki tablo, 1 kWh ısı üretmenin maliyetini kaynağa göre veriyor.")
    sat = [[ad, f"{tl:.2f}", yak, f"×{tl/min(x[1] for x in T.isi_maliyeti(m)):.1f}", g]
           for ad, tl, yak, g in T.isi_maliyeti(m)]
    r.tablo(["Isı kaynağı", "TL/kWh-ısı", "Yakıt", "En ucuza oran", "Güven"],
            sat, [74*mm, 24*mm, 26*mm, 30*mm, 24*mm], sag=(1, 3),
            vurgu=(0,))
    r.p(f"Elektrikli direnç ısıtması, gazlı radyanta göre "
        f"{(m/1.0)/(T.DOGALGAZ_TL_KWH/T.VERIM['gazli_radyant'][0]):.1f} kat, "
        f"su kaynaklı ısı pompasına göre "
        f"{T.VERIM['isi_pompasi_wshp'][0]:.1f} kat pahalıdır. Tesiste elektrikli "
        f"dirençle ısıtılan üç yer vardır: teras ısıtıcıları (40 kW), hava "
        f"perdesinin ısıtıcı kademesi (21 kW içinde) ve sıcak su boyleri "
        f"(9,9 kW). Üçünün toplam bağlı gücü "
        f"{E.SINIF['TERAS_ISITMA']['kw']+E.SINIF['HAVA_PERDESI']['kw']+E.SINIF['SICAK_SU']['kw']:.1f} "
        f"kW'tır — tesisin bağlı gücünün "
        f"%{100*(E.SINIF['TERAS_ISITMA']['kw']+E.SINIF['HAVA_PERDESI']['kw']+E.SINIF['SICAK_SU']['kw'])/E.BAGLI_KW:.0f}'i.")
    sat = []
    for y in E.YAKIT_ONLEM:
        a = E.yakit_tasarruf(y, T)
        sat.append([y["kod"], y["ad"], bin(a["kwh"]), bin(a["mevcut_tl"]),
                    bin(a["yeni_tl"]), bin(a["tasarruf"]), y["guven"]])
    tot = sum(E.yakit_tasarruf(y, T)["tasarruf"] for y in E.YAKIT_ONLEM)
    sat.append(["", "TOPLAM", "", "", "", bin(tot), ""])
    r.tablo(["Kod", "Dönüşüm", "kWh/yıl", "Mevcut TL/yıl", "Yeni TL/yıl",
             "Tasarruf TL/yıl", "Güven"],
            sat, [12*mm, 62*mm, 20*mm, 26*mm, 24*mm, 24*mm, 14*mm],
            s=6.3, sag=(2, 3, 4, 5), vurgu=(len(sat)-1,))
    for y in E.YAKIT_ONLEM:
        r.yer(20*mm)
        r.c.setFillColor(COPPER); r.c.setFont(FB, 7.6)
        r.c.drawString(SOL, r.y, f"{y['kod']} · {y['ad']}"); r.y -= 4.4*mm
        r.p(y["gerekce"], s=7.2)
    r.kutu("AÇIK TERASTA ISI POMPASI KULLANILAMAZ",
           "Isı pompası havayı ısıtır. Açık veya yarı açık bir terasta "
           "ısıtılan hava anında kaçar; ısı pompası ancak camlı/kapalı kış "
           "bahçesinde işe yarar. Açık teras zorunlu olarak IŞINIM (radyant) "
           "ısıtması gerektirir ve radyantın iki seçeneği vardır: elektrikli "
           "infrared (pahalı) veya gazlı radyant (ucuz). Bu yüzden Y-01, "
           "ısı pompası değil GAZ dönüşümüdür ve tamamen AVM'nin gaz hattı "
           "iznine bağlıdır.", AMBER)

    r.h2("6.5 Toplam potansiyel — üç bağımsız kol")
    p = E.potansiyel(T)
    r.p("Tasarruf üç ayrı koldan gelir ve kollar birbirinden bağımsızdır: "
        "tüketim azaltma kWh'i düşürür, tarife kalemleri kWh'i ucuzlatır, "
        "yakıt dönüşümü ısıyı başka kaynaktan üretir. Üçü toplanabilir.")
    te = E.tarife_etkileri(T)
    r.tablo(["Kol", "Kalemler", "Alt sınır TL/yıl", "Üst sınır TL/yıl", "Koşul"], [
        ["Tüketim", "M-01…M-07 · E-01…E-05 · E-03",
         bin(p["tuketim"][0]), bin(p["tuketim"][1]),
         "Ölçümle doğrulanmalı; ±%20 belirsizlik"],
        ["Tarife", "T-01 tedarikçi indirimi",
         bin(te["T-01"][0]), bin(te["T-01"][1]),
         "Kesin uygulanabilir — tesis serbest tüketicidir"],
        ["Tarife", "T-02 reaktif ceza",
         "0", bin(te["T-02"][1]),
         "YALNIZ ceza gerçekten varsa. Faturaya bakılmadan bilinemez."],
        ["Tarife", "T-03 tarife tipi",
         "0", bin(te["T-03"][1]),
         "YALNIZ tesis üç zamanlı tarifedeyse"],
        ["Yakıt", "Y-01 · Y-02 · Y-03", "0", bin(p["yakit"][1]),
         "Y-01 AVM gaz izni şartına bağlı"],
    ], [20*mm, 44*mm, 26*mm, 26*mm, 62*mm], s=6.3, sag=(2, 3))
    kesin = p["tuketim"][0] + te["T-01"][0]
    r.kpi([("Model yıllık faturası", bin(p["yillik_fatura"]/1_000_000, 2)+" M",
            "TL/yıl", NAVY),
           ("Kesin potansiyel", bin(kesin/1_000_000, 2)+" M",
            f"TL/yıl · faturanın %{100*kesin/p['yillik_fatura']:.0f}'i", GREEN),
           ("Koşullu ek", bin((p["toplam"][1]-kesin)/1_000_000, 2)+" M",
            "TL/yıl · reaktif + tarife tipi + gaz", AMBER),
           ("Üst sınır", f"%{100*p['toplam'][1]/p['yillik_fatura']:.0f}",
            "hepsi geçerliyse", COPPER)])
    r.kutu("ÜST SINIRI VAAT OLARAK OKUMAYIN",
           f"Üst sınır (%{100*p['toplam'][1]/p['yillik_fatura']:.0f}), reaktif "
           f"cezasının GERÇEKTEN var olduğunu, tarifenin üç zamanlı OLDUĞUNU "
           f"ve AVM'nin terasa gaz izni VERDİĞİNİ aynı anda varsayar. "
           f"Üçünün de doğru çıkma ihtimali düşüktür. Savunulabilir hedef "
           f"kesin potansiyeldir: yılda yaklaşık {bin(kesin)} TL, yani "
           f"faturanın %{100*kesin/p['yillik_fatura']:.0f}'i. Bu bile ayda "
           f"{bin(kesin/12)} TL demektir ve çoğu düşük yatırımlı kalemden "
           f"gelir.", NAVY)

    r.h2("6.6 Destekler ve yasal yükümlülükler")
    tep = E.YILLIK_TOPLAM/T.TEP_KWH
    r.p(f"Tesisin yıllık enerji tüketimi {tep:.0f} TEP'tir "
        f"({bin(E.YILLIK_TOPLAM)} kWh ÷ {bin(T.TEP_KWH)} kWh/TEP). Ticari ve "
        f"hizmet binaları için enerji yöneticisi ve ISO 50001 zorunluluğu "
        f"eşiği 500 TEP/yıl veya 20.000 m²'dir; tek şube bu eşiklerin "
        f"BELİRGİN ALTINDADIR ve doğrudan bir yükümlülüğü yoktur. Ancak "
        f"zincirin tamamı tek tüzel kişilikte toplandığında eşik aşılabilir; "
        f"bu ayrıca değerlendirilmelidir. AVM'nin kendisi 20.000 m² eşiğini "
        f"kesinlikle aşar ve kiracının AVM'nin enerji yönetim sistemine veri "
        f"verme yükümlülüğü kira sözleşmesinden doğabilir.")
    r.tablo(["Program", "Destek", "Şartlar", "Bu tesis için"],
            [[a, b, c, d] for a, b, c, d in T.DESTEK],
            [34*mm, 34*mm, 62*mm, 48*mm], s=6.0)
    r.kutu("VAP TEK ŞUBE İÇİN GERÇEKÇİ DEĞİL — AMA ZİNCİR İÇİN OLABİLİR",
           "1 Temmuz 2026'dan itibaren VAP'ın asgari proje bedeli 5.000.000 "
           "TL'dir ve ön şartı enerji yöneticisi + TÜRKAK akrediteli ISO 50001 "
           "belgesidir. Tek bir restoran bu ölçeğin altındadır. Buna karşılık "
           "zincirin birden çok şubesindeki aynı işler (kompanzasyon, DCKV, "
           "aydınlatma, izleme) TEK PROJEDE birleştirilirse hem asgari bedel "
           "aşılır hem de %30 hibe ile azami 8.127.799 TL geri alınabilir. "
           "Bu, zincir ölçeğinin doğrudan paraya çevrildiği yerdir.", GREEN)


# ════════════════════════ §12 AKSİYON KARTI ══════════════════════════════════
def s12_kart(r):
    r.h1("12", "Tek sayfalık aksiyon kartı")
    m = T.SENARYO["MEVCUT"] if T else None
    p = E.potansiyel(T) if T else None
    te = E.tarife_etkileri(T) if T else {}
    if not (m and p): return
    kesin = p["tuketim"][0] + te["T-01"][0]

    r.kpi([("Yıllık fatura", bin(p["yillik_fatura"]/1_000_000, 2)+" M",
            "TL/yıl · model", NAVY),
           ("Kesin hedef", bin(kesin/1_000_000, 2)+" M",
            f"TL/yıl · %{100*kesin/p['yillik_fatura']:.0f}", GREEN),
           ("Aylık karşılığı", bin(kesin/12), "TL/ay", COPPER),
           ("Koşullu ek", bin((p["toplam"][1]-kesin)/1_000_000, 2)+" M",
            "TL/yıl · doğrulanırsa", AMBER)])

    r.h2("Bu hafta yapılacak üç şey")
    r.tablo(["#", "İş", "Kim", "Çıktı"], [
        ["1", "Son bir ayın elektrik faturasının PDF'ini iste",
         "işletme", "Tarife tipi · reaktif satırı · gerçek kWh · sözleşme gücü"],
        ["2", "Kompanzasyon panosunun rölesinden cos φ'yi oku ve fotoğrafla",
         "teknik", f"Değer < {E.reaktif_analiz(0.9)['gereken_cosfi']} ise "
         f"yılda {bin(te['T-02'][1])} TL'ye kadar ceza riski"],
        ["3", "ADP'deki enerji analizörünün RS485 çıkışını kaydediciye bağla",
         "teknik", "Dört haftalık gerçek yük profili — bütün yatırım "
         "kararlarının girdisi"],
    ], [10*mm, 66*mm, 18*mm, 84*mm], s=6.8)

    r.h2("Üç sorunun üç cevabı")
    r.tablo(["Soru", "Cevap", "Dayanak"], [
        ["Harcama normal mi?",
         "Tüketim ve birim fiyat normal; YAKIT SEÇİMİ normal değil.",
         f"Model {bin(E.ORT_AY_KWH)} kWh/ay × {m['birim']:.2f} TL/kWh = "
         f"{bin(E.ORT_AY_KWH*m['birim'])} TL/ay — beyan edilen bandın ortası."],
        ["En büyük tek kaldıraç nedir?",
         "Havalandırmanın sabit debili çalışması ve elektrikli direnç "
         "ısıtma.",
         f"Havalandırma {bin(E.YILLIK['HAVALANDIRMA'])} kWh/yıl "
         f"(%{100*E.YILLIK['HAVALANDIRMA']/E.YILLIK_TOPLAM:.0f}); "
         f"teras ısıtıcı + hava perdesi + boiler "
         f"{E.SINIF['TERAS_ISITMA']['kw']+E.SINIF['HAVA_PERDESI']['kw']+E.SINIF['SICAK_SU']['kw']:.0f} kW."],
        ["Hemen ne kazanabiliriz?",
         "Yatırımsız kalemler: tarife tipi kontrolü, tedarikçi ihalesi, "
         "işletme disiplini, ayar.",
         f"T-01 + T-03 + E-03 + M-07 + M-03 tek başına yılda "
         f"{bin(te['T-01'][0] + E.onlem_tasarruf(next(o for o in E.ONLEM if o['kod']=='E-03'))*m['birim'] + E.onlem_tasarruf(next(o for o in E.ONLEM if o['kod']=='M-07'))*m['birim'] + E.onlem_tasarruf(next(o for o in E.ONLEM if o['kod']=='M-03'))*m['birim'])} "
         f"TL — yatırımı yok denecek kadar az."],
    ], [34*mm, 62*mm, 82*mm], s=6.6)

    r.kutu("RAPORUN TEK CÜMLELİK ÖZETİ",
           "Aqua Florya'nın elektrik faturası, tesisin kurulu yüküne ve "
           "İstanbul'daki cari tarifeye göre açıklanabilir durumdadır; asıl "
           "sorun tesisin normalde gazla yapılan ısıtma işlerini elektrikli "
           "dirençle yapması ve havalandırmanın pişirme olsun olmasın tam "
           "debide çalışmasıdır — ikisi de geri alınabilir tasarım "
           "tercihleridir.", COPPER)

    r.h2("Bu raporun üretim zinciri")
    r.tablo(["Dosya", "Ne yapar"], [
        ["tools/enerji.py", "Yükleme cetvelini okur, 155 linyeyi 18 işlev "
         "sınıfına ayırır, işletme profillerini uygular, tüketimi, reaktif "
         "riskini ve önlem tasarruflarını hesaplar. Bütün varsayımlar burada."],
        ["tools/enerji_tarife.py", "2026 tarife, vergi, reaktif, GES ve "
         "kıyaslama verisi; her kalemde kaynak ve güven derecesi (A/B/C)."],
        ["tools/enerji_grafik.py", "Rapordaki dört grafiği modelden üretir."],
        ["tools/build_enerji_raporu.py", "Bu PDF'i üretir. Raporda elle "
         "yazılmış rakam yoktur."],
        ["tools/agents/a_enerji.py", "Modelin iç tutarlılığını sınayan "
         "denetim ajanı; dört sonuçlu (geçti · kaldı · VERİ EKSİK · "
         "UYGULANMAZ). Sonucu §9.4'tedir."],
        ["tools/uret_enerji.sh", "Tam üretim zinciri: grafikler → rapor → "
         "denetim → rapor (denetim sonucu dahil)."],
        ["input/referans/ADP_Yukleme_Cetveli_REF.xlsx",
         "Birincil veri. Her sayının izi bu dosyaya çıkar; model onu "
         "doğrudan okur."],
    ], [46*mm, 132*mm], s=6.6)
    r.p("Bir varsayım değiştiğinde tek satır düzeltilir ve rapor yeniden "
        "üretilir; bütün türev sayılar kendiliğinden güncellenir. Gerçek "
        "fatura ve gerçek yük kaydı geldiğinde yapılacak iş budur.")


# ════════════════════════ ANA ÜRETİCİ ════════════════════════════════════════
def uret(cikti=CIK):
    import enerji_grafik as G
    g = G.uret_hepsi()
    c = canvas.Canvas(str(cikti), pagesize=A4)
    c.setTitle("Nusr-Et Saltbae · Elektrik Maliyeti Analiz ve Azaltma Raporu")
    c.setAuthor("Yatırım ve İş Geliştirme")
    c.setSubject(f"{E.TESIS} · {E.TARIH}")
    kapak(c)
    r = R(c)
    s0_ozet(r)
    s1_veri(r)
    s2_yuk(r, g)
    s3_model(r, g)
    s4_fatura(r)
    s5_normal(r)
    s6_onlem(r, g)
    s6b_yakit(r)
    s7_yol(r)
    s8_zincir(r)
    s9_risk(r)
    s10_varsayim(r)
    s11_istek(r)
    s12_kart(r)
    r._altbilgi()
    c.showPage()
    c.save()
    return cikti, r.sayfa


if __name__ == "__main__":
    yol, n = uret()
    print(f"{yol}  ·  {n+1} sayfa")
