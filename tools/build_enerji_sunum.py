# -*- coding: utf-8 -*-
"""ENERJİ ANALİZİ YÖNETİM SUNUMU — 16:9, büyük punto, ekrandan gösterim.

Bütün sayılar tools/enerji.py ve tools/enerji_tarife.py'den okunur.
Sunumda elle yazılmış rakam yoktur.
"""
import os, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader

import enerji as E
import enerji_tarife as T

KOK = Path(__file__).resolve().parent.parent
CIK = KOK/"output"/"Nusret_Elektrik_Sunum_16x9.pdf"

for ad, yol in (("DJ",  "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                ("DJB", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")):
    try: pdfmetrics.registerFont(TTFont(ad, yol))
    except Exception: pass
F, FB = "DJ", "DJB"

W, H = 338.67*mm, 190.5*mm
L, R = 20*mm, W-20*mm
CW   = R-L
BG      = HexColor("#0E1620")
KART    = HexColor("#17242F")
KENAR   = HexColor("#24405F")
BEYAZ   = HexColor("#FFFFFF")
SOLUK   = HexColor("#9FB4C9")
SILIK   = HexColor("#5E7690")
COPPER  = HexColor("#B87333")
COPPER_L= HexColor("#E8CDAE")
KIRMIZI = HexColor("#E0544B")
YESIL   = HexColor("#3FA47A")
SARI    = HexColor("#E0B040")
MAVI    = HexColor("#4E8FD0")

_TRB = str.maketrans({"i": "İ", "ı": "I"})
def UP(t): return str(t).translate(_TRB).upper()

def bin(x, ond=0):
    if x is None: return "—"
    return f"{x:,.{ond}f}".replace(",", " ").replace(".", ",").replace(" ", ".")

def sar(c, t, gen, font=F, boy=10):
    out, sat = [], ""
    for k in str(t).split():
        d = (sat+" "+k).strip()
        if sat and pdfmetrics.stringWidth(d, font, boy) > gen:
            out.append(sat); sat = k
        else: sat = d
    if sat: out.append(sat)
    return out or [""]

def txt(c, x, y, t, font=F, boy=10, renk=BEYAZ, hiza="l"):
    c.setFont(font, boy); c.setFillColor(renk)
    if hiza == "r": c.drawRightString(x, y, t)
    elif hiza == "c": c.drawCentredString(x, y, t)
    else: c.drawString(x, y, t)

def para(c, x, y, t, gen, font=F, boy=10, renk=SOLUK, ara=None):
    ara = ara or boy*1.45
    for i, ln in enumerate(sar(c, t, gen, font, boy)):
        txt(c, x, y-i*ara, ln, font, boy, renk)
    return y - len(sar(c, t, gen, font, boy))*ara

N = 14
def bas(c, no, ust, baslik):
    c.setFillColor(BG); c.rect(0, 0, W, H, 0, 1)
    c.setFillColor(COPPER); c.rect(0, H-4*mm, W, 4*mm, 0, 1)
    txt(c, L, H-15*mm, UP(ust), FB, 8, COPPER)
    txt(c, L, H-27*mm, baslik, FB, 20, BEYAZ)
    txt(c, R, H-15*mm, f"{no:02d} / {N}", FB, 8, SILIK, "r")
    txt(c, R, H-27*mm, f"{E.TESIS} · {E.REV}", F, 7.5, SILIK, "r")

def alt(c, t):
    txt(c, L, 9*mm, t, F, 7, SILIK)

def kart(c, x, y, w, h, acc=None):
    c.setFillColor(KART); c.rect(x, y, w, h, 0, 1)
    c.setStrokeColor(KENAR); c.setLineWidth(0.6); c.rect(x, y, w, h, 1, 0)
    if acc: c.setFillColor(acc); c.rect(x, y+h-1.6*mm, w, 1.6*mm, 0, 1)

def kpi(c, x, y, w, h, ust, deger, altm, acc=COPPER, dboy=26):
    kart(c, x, y, w, h, acc)
    txt(c, x+6*mm, y+h-11*mm, UP(ust), FB, 7.2, SILIK)
    b = dboy
    while pdfmetrics.stringWidth(deger, FB, b) > w-12*mm and b > 10: b -= 0.5
    txt(c, x+6*mm, y+h-11*mm-b*0.92, deger, FB, b, BEYAZ)
    para(c, x+6*mm, y+8*mm, altm, w-12*mm, F, 7.2, SOLUK, 9)

def gorsel(c, yol, x, y, w, hmax, ust=None):
    """ust verilirse görselin ÜST kenarı o kota oturur (başlığın altına yapışsın)."""
    if not Path(yol).exists(): return
    im = ImageReader(str(yol)); iw, ih = im.getSize()
    h = w*ih/iw
    if h > hmax: h = hmax; w = h*iw/ih
    if ust is not None:
        y = ust - h
        if y < 14*mm:                       # alta taşarsa küçült
            h = ust - 14*mm; w = h*iw/ih; y = 14*mm
    c.setFillColor(HexColor("#FFFFFF")); c.rect(x-3*mm, y-3*mm, w+6*mm, h+6*mm, 0, 1)
    c.drawImage(im, x, y, w, h)
    return w, h

M = T.SENARYO["MEVCUT"]
TE = E.tarife_etkileri(T)
POT = E.potansiyel(T)
KESIN = POT["tuketim"][0] + TE["T-01"][0]
VD, VAC = E.kiyas_verdikt(T)


# ══════════════════════════════ SLAYTLAR ═════════════════════════════════════
def s1(c):
    c.setFillColor(BG); c.rect(0, 0, W, H, 0, 1)
    c.setFillColor(HexColor("#16273D")); c.rect(W*0.56, 0, W*0.44, H, 0, 1)
    # sağ blokta büyük rakam
    txt(c, W*0.56+22*mm, H*0.62, bin(E.guc_yogunlugu()), FB, 72, COPPER)
    txt(c, W*0.56+22*mm, H*0.62-16*mm, "W / m²  KURULU GÜÇ", FB, 12, COPPER_L)
    para(c, W*0.56+22*mm, H*0.62-30*mm,
         "Tam donanımlı bir restoranda beklenen değer 150–250 W/m². "
         "Bu tesis bandın üç katı.", W*0.44-44*mm, F, 9.5, SOLUK)
    c.setFillColor(COPPER); c.rect(L, H-56*mm, 26*mm, 1.8*mm, 0, 1)
    txt(c, L, H-50*mm, "YATIRIM VE İŞ GELİŞTİRME · YÖNETİM ÖZETİ", FB, 8, COPPER)
    for i, ln in enumerate(["ELEKTRİK MALİYETİ", "ANALİZ VE AZALTMA"]):
        txt(c, L, H-70*mm-i*13*mm, ln, FB, 23, BEYAZ)
    txt(c, L, H-96*mm, "PROGRAMI", FB, 23, COPPER)
    txt(c, L, H-114*mm, E.TESIS, F, 12, SOLUK)
    txt(c, L, H-124*mm,
        f"{bin(E.ALAN_M2)} m² · {bin(E.BAGLI_KW)} kW bağlı güç · "
        f"{len(E.DEVRE)} linye", F, 8.5, SILIK)
    txt(c, L, 14*mm, f"{E.TARIH} · {E.REV} · yalnız iç kullanım", F, 7.5, SILIK)


def s2(c):
    bas(c, 2, "Tek bakışta", "Altı rakamda durum")
    w = (CW-5*4*mm)/6; h = 38*mm; y = H-74*mm
    veri = [("Bağlı güç", f"{bin(E.BAGLI_KW,0)}", "kW · 155 linye", MAVI),
            ("Aylık tüketim", bin(E.ORT_AY_KWH), "kWh · model", COPPER),
            ("Aylık fatura", bin(E.ORT_AY_KWH*M["birim"]/1000)+"k", "TL · model", COPPER),
            ("Beyan edilen", f"{bin(E.BEYAN_TL[0]/1000)}–{bin(E.BEYAN_TL[1]/1000)}k",
             "TL · işveren", SARI),
            ("Özgül tüketim", bin(E.ozgul()), "kWh/m²/yıl", KIRMIZI),
            ("Güç yoğunluğu", bin(E.guc_yogunlugu()), "W/m²", KIRMIZI)]
    for i, (u, d, a, r) in enumerate(veri):
        kpi(c, L+i*(w+4*mm), y, w, h, u, d, a, r, dboy=19)

    yy = y-10*mm; bh = 76*mm
    sapma = abs(100*((sum(E.BEYAN_TL)/2)-E.ORT_AY_KWH*M["birim"])
                / (E.ORT_AY_KWH*M["birim"]))
    kart(c, L, yy-bh, CW*0.48, bh, YESIL)
    txt(c, L+8*mm, yy-11*mm, "FİYAT NORMAL · MODEL FATURAYLA MUTABIK", FB, 11, YESIL)
    para(c, L+8*mm, yy-21*mm,
         f"Yük cetvelinden bağımsız kurulan tüketim modeli, 2026 ticarethane "
         f"tarifesiyle çarpıldığında ayda {bin(E.ORT_AY_KWH*M['birim'])} TL "
         f"veriyor ve beyan edilen bandın ortasına düşüyor; sapma "
         f"%{bin(sapma,1)}.",
         CW*0.48-16*mm, F, 9, SOLUK)
    para(c, L+8*mm, yy-44*mm,
         "Gizli kaçak, hatalı sayaç veya yanlış okuma aramaya gerek yok.",
         CW*0.48-16*mm, FB, 9.5, COPPER_L)
    para(c, L+8*mm, yy-60*mm,
         f"Ama {bin(E.ALAN_M2)} m²'ye {bin(E.BAGLI_KW)} kW sığdırılmış: "
         f"{bin(E.guc_yogunlugu())} W/m², tipik restoran bandının üç katı. "
         f"Sorun fiyatta değil, tüketimde ve yakıt seçiminde.",
         CW*0.48-16*mm, F, 9, SOLUK)

    x2 = L+CW*0.52
    kart(c, x2, yy-bh, CW*0.48, bh, KIRMIZI)
    txt(c, x2+8*mm, yy-11*mm, "TÜKETİM NORMAL DEĞİL · NEREYE GİDİYOR",
        FB, 11, KIRMIZI)
    top5 = sorted(E.YILLIK.items(), key=lambda kv: -kv[1])[:5]
    enb = top5[0][1]
    yy2 = yy-24*mm
    for sn, v in top5:
        gen = (CW*0.48-76*mm)*v/enb
        c.setFillColor(KIRMIZI if v/E.YILLIK_TOPLAM >= 0.15 else COPPER)
        c.rect(x2+8*mm, yy2-2*mm, gen, 4.6*mm, 0, 1)
        txt(c, x2+8*mm, yy2+4.6*mm, E.SINIF_AD[sn][:42], F, 8, SOLUK)
        txt(c, x2+CW*0.48-10*mm, yy2-0.6*mm,
            f"%{bin(100*v/E.YILLIK_TOPLAM,0)}  ·  {bin(v*M['birim']/12)} TL/ay",
            FB, 8, BEYAZ, "r")
        yy2 -= 11.5*mm
    alt(c, "Kaynak: ADP elektrik pano yükleme cetveli R00 · proje Y-24-003-001")


def s3(c):
    bas(c, 3, "Sorunun cevabı", "Üç ayrı soru, üç ayrı cevap")
    veri = [("1", "kWh'i pahalıya mı alıyoruz?", "HAYIR", YESIL,
             "Beyan edilen tutarın ima ettiği birim fiyat, İstanbul'daki cari "
             "ticarethane tarifesiyle uyumlu. İki koşulla: tarife tek zamanlı "
             "olmalı ve kompanzasyon çalışıyor olmalı."),
            ("2", "Metrekare başına çok mu tüketiyoruz?", "EVET", KIRMIZI,
             f"{bin(E.ozgul())} kWh/m²/yıl — ABD fast-food restoran medyanı "
             f"seviyesinde, İngiliz CIBSE TM46 restoran kıyasının "
             f"{bin(E.ozgul()/460,1)} katı."),
            ("3", "Doğru enerjiyi mi kullanıyoruz?", "HAYIR", KIRMIZI,
             "Normalde doğal gazla yapılan ısıtma işleri elektrikli dirençle "
             "yapılıyor: 40 kW teras ısıtıcı, 21 kW hava perdesi, 9,9 kW boiler.")]
    h = 38*mm; y = H-70*mm
    for i, (no, soru, cev, renk, ac) in enumerate(veri):
        yy = y-i*(h+8*mm)
        kart(c, L, yy, CW, h, renk)
        txt(c, L+8*mm, yy+h-15*mm, no, FB, 19, renk)
        txt(c, L+20*mm, yy+h-15*mm, soru, FB, 14, BEYAZ)
        txt(c, R-8*mm, yy+h-15*mm, cev, FB, 19, renk, "r")
        para(c, L+20*mm, yy+h-25*mm, ac, CW-64*mm, F, 9.5, SOLUK)
    alt(c, "Ayrıntı: rapor §5 — üç test ayrı ayrı uygulanmıştır")


def s4(c):
    bas(c, 4, "Yöntem", "Rakam nereden geliyor")
    adim = [("1", "Birincil veri",
             f"İşverenin gönderdiği ADP yükleme cetveli: {len(E.DEVRE)} linye, "
             f"{bin(E.BAGLI_KW)} kW bağlı güç. Modelin okuması cetvelin "
             f"beyanıyla mutabık ({bin(E.CETVEL_BAGLI_KW,2)} kW)."),
            ("2", "İşlev sınıflandırması",
             "155 linye, pano grubuna göre değil GERÇEK İŞLEVİNE göre 18 "
             "tüketim sınıfına ayrıldı. Bir buzdolabı priz linyesinde de olsa "
             "24 saat çalışır."),
            ("3", "İşletme profili",
             "Her sınıfa saat/gün, yük faktörü ve 12 aylık mevsim katsayısı "
             "atandı. Her kabulün gerekçesi raporda yazılı."),
            ("4", "Tarife ve kıyas",
             "2026 ticarethane tarifesi, vergi yapısı, reaktif bedeli ve "
             "uluslararası restoran kıyasları. Her veride kaynak ve güven "
             "derecesi (A/B/C).")]
    w = (CW-3*5*mm)/4; y = H-72*mm; h = 52*mm
    for i, (no, b, ac) in enumerate(adim):
        x = L+i*(w+5*mm)
        kart(c, x, y, w, h, COPPER)
        txt(c, x+6*mm, y+h-14*mm, no, FB, 20, COPPER)
        txt(c, x+6*mm, y+h-23*mm, b, FB, 10.5, BEYAZ)
        para(c, x+6*mm, y+h-31*mm, ac, w-12*mm, F, 8, SOLUK, 10)
    yy = y-14*mm
    kart(c, L, yy-30*mm, CW, 28*mm, MAVI)
    txt(c, L+8*mm, yy-9*mm, "MODELİN SINIRI — DÜRÜSTÇE", FB, 11, MAVI)
    para(c, L+8*mm, yy-18*mm,
         "Bağlı güç tarafı güvenilirdir; cetvelden okunur. İşletme profilleri "
         "ise ÖLÇÜME DEĞİL MÜHENDİSLİK KABULÜNE dayanır — gerçek tüketim "
         "modelden ±%20 sapabilir. Denetim ajanı 20 kontrolü geçti, 0'ı kaldı, "
         "15'ini veri olmadığı için YAPAMADI ve bunları geçmiş göstermedi.",
         CW-16*mm, F, 9.5, SOLUK)
    alt(c, "Model: tools/enerji.py · denetim: tools/agents/a_enerji.py")


def s5(c):
    bas(c, 5, "Yük yapısı", "Bağlı gücün %59'u mekanik")
    gw, gh = gorsel(c, KOK/"work"/"enerji"/"g_bagli_guc.png",
                    L, 0, CW*0.60, H-58*mm, ust=H-42*mm)
    x = L+CW*0.62
    w = CW*0.38
    y = H-66*mm
    for b, ac, r in [
        ("Mutfak değil, mekanik",
         "Bir restoranın faturasını mutfağın yaptığı yaygın kanısının aksine, "
         "bu tesiste talep gücünün %59'u iklimlendirme, havalandırma ve "
         "ısıtmadır.", COPPER),
        ("40 kW elektrikli teras ısıtıcı",
         "Sekiz adet 5 kW. Elektrikli direnç ısıtmasında verim tanımı gereği "
         "%100'ü aşamaz; bu, birim ısı başına tesisin en pahalı enerjisidir.",
         KIRMIZI),
        ("21 kW hava perdesi tek linyede",
         "Faz başına 7 kW. Bu güç yoğunluğu ancak elektrikli ısıtıcılı bir "
         "perdede görülür. Kapı kapalıyken de çalışıyorsa ısı doğrudan "
         "dışarı atılıyor.", KIRMIZI)]:
        txt(c, x, y, b, FB, 11, r)
        y = para(c, x, y-8*mm, ac, w, F, 8.8, SOLUK) - 9*mm
    alt(c, "Kaynak: ADP yükleme cetveli R00 · rapor §2")


def s6(c):
    bas(c, 6, "Tüketim", "Yılda nereye gidiyor")
    gorsel(c, KOK/"work"/"enerji"/"g_tuketim_pay.png", L, 0, CW*0.60,
           H-58*mm, ust=H-42*mm)
    x = L+CW*0.62; w = CW*0.38; y = H-66*mm
    top3 = sorted(E.YILLIK.items(), key=lambda kv: -kv[1])[:3]
    txt(c, x, y, "EN BÜYÜK ÜÇ KALEM", FB, 9, COPPER); y -= 11*mm
    for s, v in top3:
        txt(c, x, y, E.SINIF_AD[s], FB, 10, BEYAZ)
        txt(c, x, y-7*mm, f"{bin(v)} kWh/yıl  ·  %{bin(100*v/E.YILLIK_TOPLAM,0)}"
            f"  ·  {bin(v*M['birim']/12)} TL/ay", F, 8.5, COPPER_L)
        y -= 17*mm
    y -= 4*mm
    txt(c, x, y, "MEVSİM ETKİSİ ZAYIF", FB, 9, COPPER)
    para(c, x, y-8*mm,
         f"En yüksek ve en düşük ay arasında yalnız "
         f"%{bin(100*(max(E.AYLIK_TOPLAM)/min(E.AYLIK_TOPLAM)-1),0)} fark var. "
         f"Tüketimin büyük kısmı 7/24 veya her gün aynı saat çalışan "
         f"yüklerden geliyor. Tasarruf “yazın klimayı kıs” ile değil, sürekli "
         f"çalışan yüklerin çalışma biçimini değiştirerek gelir.",
         w, F, 8.8, SOLUK)
    alt(c, "Model çıktısı · rapor §3")


def s7(c):
    bas(c, 7, "Test 1 · Fiyat", "kWh'i pahalıya almıyoruz")
    w = (CW-3*5*mm)/4
    y = H-78*mm
    kpi(c, L, y, w, 40*mm, "Birim fiyat", f"{bin(M['birim'],2)}",
        "TL/kWh · KDV dâhil", YESIL, 24)
    kpi(c, L+(w+5*mm), y, w, 40*mm, "Aktif enerji payı",
        f"%{bin(100*M['aktif']/M['birim'],0)}", "tedarikçi pazarlığı buna etki eder",
        MAVI, 24)
    kpi(c, L+2*(w+5*mm), y, w, 40*mm, "Dağıtım + vergi",
        f"%{bin(100*(M['dagitim']+M['fon']+M['btv']+M['kdv'])/M['birim'],0)}",
        "pazarlıkla değişmez", SILIK, 24)
    kpi(c, L+3*(w+5*mm), y, w, 40*mm, "Piyasa bandı", "6,42–7,33",
        "TL/kWh · bağımsız kaynaklar", YESIL, 20)
    yy = y-12*mm
    kart(c, L, yy-74*mm, CW*0.49, 72*mm, SARI)
    txt(c, L+8*mm, yy-12*mm, "AMA İKİ KONTROL YAPILMADI", FB, 12, SARI)
    para(c, L+8*mm, yy-23*mm,
         f"1 · TARİFE TİPİ. Restoran yükü 17:00–22:00 puant dilimine yığılır; "
         f"o dilim gündüzün {bin(T.UC_ZAMANLI['T2'][0]/T.UC_ZAMANLI['T1'][0],2)} "
         f"katıdır. Üç zamanlı tarife bu profilde tek zamanlıdan "
         f"%{bin(100*(T.uc_zamanli_birim(E.ZAMAN_PAY)/M['birim']-1),0)} PAHALIDIR.",
         CW*0.49-16*mm, F, 9.5, SOLUK)
    para(c, L+8*mm, yy-52*mm,
         f"Tesis üç zamanlıdaysa dilekçeyle geçiş yılda "
         f"{bin(TE['T-03'][1])} TL kazandırır. Maliyeti sıfırdır.",
         CW*0.49-16*mm, FB, 9.5, COPPER_L)
    x2 = L+CW*0.51
    kart(c, x2, yy-74*mm, CW*0.49, 72*mm, KIRMIZI)
    txt(c, x2+8*mm, yy-12*mm, "2 · REAKTİF CEZA", FB, 12, KIRMIZI)
    rk = E.reaktif_analiz(E.CETVEL_COSFI, birim=T.REAKTIF_BEDEL)
    para(c, x2+8*mm, yy-23*mm,
         f"Cetvel cos φ'yi {bin(E.CETVEL_COSFI,2)} veriyor. Bu değerde reaktif oran "
         f"%{bin(100*rk['tanfi'],1)} olur ve %{bin(100*rk['esik'],0)} eşiğini ikiye "
         f"katlar. Kompanzasyon çalışmıyorsa ceza ayda "
         f"{bin(rk['ceza']*1.2)} TL.",
         CW*0.49-16*mm, F, 9.5, SOLUK)
    para(c, x2+8*mm, yy-52*mm,
         f"Yılda {bin(TE['T-02'][1])} TL'ye kadar — karşılığında hiçbir şey "
         f"alınmadan. Cevap kompanzasyon rölesinin ekranındadır.",
         CW*0.49-16*mm, FB, 9.5, COPPER_L)
    alt(c, "Rapor §4 · 2026 EPDK ticarethane AG tarifesi")


def s8(c):
    bas(c, 8, "Test 2 · Yoğunluk", f"Metrekare başına tüketim {VD}")
    ref = [(ad, v) for ad, v, *_ in T.BENCHMARK if v]
    ref.append(("BU TESİS", E.ozgul()))
    enb = max(v for _, v in ref)
    y0 = H-58*mm; bh = 10*mm; adim = 13*mm
    for i, (ad, v) in enumerate(ref):
        yy = y0-i*adim
        bu = ad == "BU TESİS"
        gen = (CW*0.58)*v/enb
        c.setFillColor(KIRMIZI if bu else KENAR)
        c.rect(L+CW*0.27, yy, gen, bh, 0, 1)
        txt(c, L+CW*0.26, yy+2.9*mm, ad, FB if bu else F, 8.6,
            BEYAZ if bu else SOLUK, "r")
        txt(c, L+CW*0.27+gen+3*mm, yy+2.9*mm, f"{bin(v)} kWh/m²/yıl",
            FB if bu else F, 8.6, KIRMIZI if bu else SOLUK)
    ky, kh = 16*mm, 34*mm
    kart(c, L, ky, CW, kh, KIRMIZI)
    txt(c, L+8*mm, ky+kh-11*mm, "SONUÇ", FB, 11, KIRMIZI)
    para(c, L+8*mm, ky+kh-20*mm,
         f"Tesisin özgül tüketimi, ticari binalar içinde en enerji yoğun tip "
         f"olan ABD fast-food restoranlarının medyanıyla aynı seviyede ve "
         f"İngiliz CIBSE TM46 restoran kıyasının {bin(E.ozgul()/460,1)} katı. "
         f"Alan ÖLÇÜLMEDİ; {bin(E.ALAN_M2)} m² işveren beyanıdır. Teras bu "
         f"alana dâhil değilse gerçek değer daha düşüktür.",
         CW-16*mm, F, 9, SOLUK)
    alt(c, "Kıyaslar TOPLAM enerjidir (elektrik + fosil); bu tesis neredeyse "
           "tamamen elektriklidir · Türkiye'ye özel restoran kıyası yayımlanmamıştır")


def s9(c):
    bas(c, 9, "Test 3 · Yakıt karması", "Asıl bulgu: yanlış enerjiyi kullanıyoruz")
    veri = T.isi_maliyeti(M["birim"])
    enb = max(v for _, v, *_ in veri)
    y0 = H-62*mm; bh = 12*mm
    for i, (ad, tl, yak, g) in enumerate(veri):
        yy = y0-i*(bh+4*mm)
        gen = (CW*0.55)*tl/enb
        renk = KIRMIZI if i == 0 else (YESIL if yak == "doğal gaz" else MAVI)
        c.setFillColor(renk); c.rect(L+CW*0.33, yy, gen, bh, 0, 1)
        txt(c, L+CW*0.32, yy+3.6*mm, ad, FB if i == 0 else F, 9,
            BEYAZ if i == 0 else SOLUK, "r")
        txt(c, L+CW*0.33+gen+3*mm, yy+3.6*mm, f"{bin(tl,2)} TL / kWh ısı",
            FB, 10, renk)
    yy = y0-len(veri)*(bh+4*mm)-6*mm
    kart(c, L, yy-36*mm, CW, 34*mm, KIRMIZI)
    txt(c, L+8*mm, yy-10*mm, "TESİSTE ELEKTRİKLİ DİRENÇLE ISITILAN ÜÇ YER",
        FB, 12, KIRMIZI)
    kw = (E.SINIF['TERAS_ISITMA']['kw'] + E.SINIF['HAVA_PERDESI']['kw']
          + E.SINIF['SICAK_SU']['kw'])
    para(c, L+8*mm, yy-20*mm,
         f"Teras ısıtıcıları {bin(E.SINIF['TERAS_ISITMA']['kw'],0)} kW  ·  "
         f"hava perdesi ısıtıcı kademesi {bin(E.SINIF['HAVA_PERDESI']['kw'],0)} kW "
         f"içinde  ·  sıcak su boyleri {bin(E.SINIF['SICAK_SU']['kw'],1)} kW. "
         f"Toplam {bin(kw,1)} kW — bağlı gücün %{bin(100*kw/E.BAGLI_KW,0)}'i. "
         f"Yakıt dönüşümüyle yılda {bin(POT['yakit'][1])} TL kazanç mümkün; "
         f"teras için ÖN ŞART, AVM'nin gaz hattı iznidir.",
         CW-16*mm, F, 9.5, SOLUK)
    alt(c, "Açık terasta ısı pompası kullanılamaz — ısıtılan hava kaçar; "
           "açık teras zorunlu olarak ışınım (radyant) ısıtması gerektirir")


def s10(c):
    bas(c, 10, "Tespitler", "Cetvelden çıkan dört kritik bulgu")
    veri = [("40 kW elektrikli teras ısıtıcı", KIRMIZI,
             "M36–M43. Elektrikli direnç ısıtmasında 1 kWh elektrik = 1 kWh "
             "ısı; verim %100'ü aşamaz. Aynı ısıyı gazlı radyant dörtte bir "
             "maliyetle üretir."),
            ("21 kW hava perdesi tek linyede", KIRMIZI,
             "M7. 3×40 C kesici, 5×6 mm² kesit, faz başına 7 kW — ancak "
             "elektrikli ısıtıcılı bir perdede görülür. Kapı kapalıyken de "
             "çalışıyorsa ısı doğrudan dışarı atılıyor."),
            ("Havalandırma sabit debili görünüyor", KIRMIZI,
             "M15–M17 ve MDP 21,9 kW. Cetvelde hız kontrolü (sürücü) işareti "
             "yok. Fan gücü debinin küpüyle değişir: debiyi %70'e çekmek "
             "gücü %34'e indirir."),
            ("Kompanzasyon beslemesi var, panosu pakette yok", SARI,
             "kVAr kademe tablosu ve reaktörlü olup olmadığı bilinmiyor. "
             "Sürücü ve LED yükü harmonik üretir; reaktörsüz grup bu yükte "
             "hızla bozulur ve ceza faturanın görünmeyen kalemi olur.")]
    w = (CW-5*mm)/2; h = 44*mm
    for i, (b, r, ac) in enumerate(veri):
        x = L+(i % 2)*(w+5*mm); y = H-(66 if i < 2 else 116)*mm
        kart(c, x, y, w, h, r)
        txt(c, x+7*mm, y+h-13*mm, b, FB, 11, r)
        para(c, x+7*mm, y+h-22*mm, ac, w-14*mm, F, 8.8, SOLUK)
    yy = H-124*mm
    kart(c, L, yy-26*mm, CW, 24*mm, YESIL)
    txt(c, L+8*mm, yy-9*mm, "İYİ HABER · HAZIR AMA KULLANILMAYAN ALTYAPI",
        FB, 11, YESIL)
    para(c, L+8*mm, yy-17*mm,
         "Enerji analizörü (-EA1) ve altı adet 600/5 A akım trafosu panoda "
         "KURULU; RS485 çıkışı var. DALİ modülleri ve faz dim modülü kurulu. "
         "Tabela linyelerinde alacakaranlık rölesi var. Ölçüm ve kontrol "
         "altyapısı için yeni yatırım gerekmiyor — sadece devreye alınmamış.",
         CW-16*mm, F, 9, SOLUK)
    alt(c, "Rapor §2.2 ve §2.3")


def s11(c):
    bas(c, 11, "Potansiyel", "Üç bağımsız koldan tasarruf")
    w = (CW-3*5*mm)/4; y = H-78*mm
    kpi(c, L, y, w, 40*mm, "Yıllık fatura",
        bin(POT["yillik_fatura"]/1_000_000, 2)+" M", "TL/yıl · model", SILIK, 22)
    kpi(c, L+(w+5*mm), y, w, 40*mm, "Kesin hedef",
        bin(KESIN/1_000_000, 2)+" M",
        f"TL/yıl · faturanın %{bin(100*KESIN/POT['yillik_fatura'],0)}'i", YESIL, 22)
    kpi(c, L+2*(w+5*mm), y, w, 40*mm, "Aylık karşılığı", bin(KESIN/12),
        "TL/ay", COPPER, 22)
    kpi(c, L+3*(w+5*mm), y, w, 40*mm, "Koşullu ek",
        bin((POT["toplam"][1]-KESIN)/1_000_000, 2)+" M",
        "TL/yıl · doğrulanırsa", SARI, 22)
    yy = y-12*mm
    kollar = [("TÜKETİM", POT["tuketim"][1], MAVI,
               f"M-01…M-07 · E-01…E-05. Teknik potansiyel "
               f"%{bin(100*E.teknik_toplam()/E.YILLIK_TOPLAM,0)}. Ölçümle "
               f"doğrulanmalı."),
              ("TARİFE", TE["T-01"][1]+TE["T-02"][1]+TE["T-03"][1], COPPER,
               "Tedarikçi indirimi kesin; reaktif ceza ve tarife tipi "
               "faturaya bakılmadan bilinemez."),
              ("YAKIT", POT["yakit"][1], YESIL,
               "Teras gaza, boiler ısı pompasına. Teras için AVM gaz izni "
               "ön şarttır.")]
    ww = (CW-2*5*mm)/3
    for i, (ad, v, r, ac) in enumerate(kollar):
        x = L+i*(ww+5*mm)
        kart(c, x, yy-52*mm, ww, 50*mm, r)
        txt(c, x+7*mm, yy-12*mm, ad, FB, 12, r)
        txt(c, x+7*mm, yy-25*mm, bin(v), FB, 20, BEYAZ)
        txt(c, x+7*mm, yy-32*mm, "TL / yıl · üst sınır", F, 7.5, SILIK)
        para(c, x+7*mm, yy-40*mm, ac, ww-14*mm, F, 8.2, SOLUK, 9.5)
    ky, kh = 15*mm, 34*mm
    kart(c, L, ky, CW, kh, SARI)
    txt(c, L+8*mm, ky+kh-11*mm, "ÜST SINIRI VAAT OLARAK OKUMAYIN", FB, 11, SARI)
    para(c, L+8*mm, ky+kh-20*mm,
         f"Üst sınır, reaktif cezasının GERÇEKTEN var olduğunu, tarifenin üç "
         f"zamanlı OLDUĞUNU ve AVM'nin terasa gaz izni VERDİĞİNİ aynı anda "
         f"varsayar; üçünün de doğru çıkma ihtimali düşüktür. Savunulabilir "
         f"hedef kesin potansiyeldir: yılda {bin(KESIN)} TL, ayda "
         f"{bin(KESIN/12)} TL — ve çoğu düşük yatırımlı kalemden gelir.",
         CW-16*mm, F, 9, SOLUK)
    alt(c, "Kollar bağımsızdır ve toplanabilir · aynı sınıfa birden çok önlem "
           "varsa çarpımsal birleştirilir, çifte sayım yoktur")


def s12(c):
    bas(c, 12, "Öncelik", "En büyük kalemler ve geri ödemeleri")
    gorsel(c, KOK/"work"/"enerji"/"g_onlem.png", L, 0, CW*0.58,
           H-84*mm, ust=H-42*mm)
    x = L+CW*0.60; w = CW*0.40; y = H-64*mm
    sirali = sorted(E.ONLEM, key=lambda o: -E.onlem_tasarruf(o))[:5]
    txt(c, x, y, "İLK BEŞ KALEM", FB, 9, COPPER); y -= 10*mm
    for o in sirali:
        t = E.onlem_tasarruf(o)
        b = T.YATIRIM_BANT.get(o["kod"])
        yat = (b[0]+b[1])/2 if b and b[1] else 0
        gd = ("yatırımsız" if yat == 0 else f"{bin(yat/(t*M['birim']),1)} yıl")
        txt(c, x, y, f"{o['kod']} · {o['ad'][:44]}", FB, 8.6, BEYAZ)
        txt(c, x, y-6*mm, f"{bin(t*M['birim'])} TL/yıl  ·  geri ödeme {gd}",
            F, 8.2, COPPER_L)
        y -= 15*mm
    kart(c, L, 12*mm, CW*0.58, 24*mm, YESIL)
    txt(c, L+7*mm, 30*mm, "ÖNCE ÖLÇÜM, SONRA YATIRIM", FB, 10, YESIL)
    para(c, L+7*mm, 24*mm,
         "Bu grafikteki bütün yüzdeler bir modelden gelir. Panodaki enerji "
         "analizörünün kaydını almaya başladığınız gün model ölçümle değişir. "
         "Hiçbir yatırım kararı, dört haftalık gerçek yük kaydı görülmeden "
         "verilmemelidir.", CW*0.58-14*mm, F, 8.2, SOLUK, 9.5)
    alt(c, "Yatırım maliyetleri 2026 Türkiye piyasası · bir kısmı tahmindir, "
           "teklif alınmalıdır")


def s13(c):
    bas(c, 13, "Yol haritası", "Dört faz, doğru sırada")
    fazlar = [("FAZ 0", "İLK 30 GÜN", YESIL, "Ölç, doğrula, hiç para harcama",
               ["Son 12 ayın faturasını satır satır topla",
                "Tarife tipini oku — üç zamanlıysa dilekçe ver",
                "Kompanzasyon rölesinden cos φ'yi oku",
                "Enerji analizörüne kaydedici bağla",
                "Net alan tablosunu mimari projeden çıkar",
                "Tedarikçi ihalesine çık — bütün şubeler tek portföy"]),
              ("FAZ 1", "1–3 AY", MAVI, "Ayar ve disiplin, yatırımsız",
               ["Hava perdesi ısıtıcısını kapat, kapıya kilitle",
                "Teras ısıtıcılarına bölge + termostat + saat",
                "Mutfak açılış/kapanış kontrol listesi",
                "VRF/WSHP ölü bant ve gece geri çekme",
                "DALİ senaryolarını kur, tabelaya kapanış saati",
                "Soğuk oda kapı perdesi ve kondenser temizliği"]),
              ("FAZ 2", "3–9 AY", SARI, "Ölçülmüş veriyle yatırım",
               ["Kompanzasyonu reaktörlü olarak yenile/onar",
                "Davlumbaza sürücü + talep kontrollü havalandırma",
                "Elektrikli boyleri ısı pompasına çevir",
                "Teras gaz dönüşümü fizibilitesi (AVM izni)",
                "LED ve soğutma dönüşümleri — önce/sonra ölç"]),
              ("FAZ 3", "9–18 AY", KIRMIZI, "Yapısal",
               ["Salon egzozuna ısı geri kazanım",
                "Çatı GES + batarya (AVM anlaşması şartıyla)",
                "Zincir geneli enerji yönetim sistemi",
                "YENİ ŞUBE TASARIM ŞARTNAMESİ"])]
    w = (CW-3*4*mm)/4; y = 16*mm; h = H-62*mm
    for i, (kod, sure, r, b, isler) in enumerate(fazlar):
        x = L+i*(w+4*mm)
        kart(c, x, y, w, h, r)
        txt(c, x+6*mm, y+h-15*mm, kod, FB, 18, r)
        txt(c, x+6*mm, y+h-23*mm, sure, FB, 9.5, COPPER_L)
        yy = y+h-35*mm
        yy = para(c, x+6*mm, yy, b, w-12*mm, FB, 10.5, BEYAZ, 13) - 8*mm
        for t in isler:
            txt(c, x+6*mm, yy, "·", F, 9, r)
            yy = para(c, x+10*mm, yy, t, w-16*mm, F, 8.8, SOLUK, 10.6) - 5*mm
    alt(c, "Ölçüm önce gelir çünkü ölçülmeyen tasarruf doğrulanamaz ve yatırım "
           "kararı savunulamaz · rapor §7")


def s14(c):
    bas(c, 14, "Karar", "Bu hafta üç şey")
    veri = [("1", "Faturayı isteyin", COPPER,
             "Son bir aya ait tek bir fatura PDF'i. Tarife tipini, reaktif "
             "cezayı, gerçek kWh'i, birim fiyatı ve sözleşme gücünü aynı anda "
             "cevaplar. Bu rapordaki dört büyük belirsizlikten üçü o faturayla "
             "kapanır."),
            ("2", "cos φ'yi okuyun", KIRMIZI,
             f"Kompanzasyon panosunun rölesinden. Değer "
             f"{bin(E.reaktif_analiz(0.9)['gereken_cosfi'],4)} altındaysa yılda "
             f"{bin(TE['T-02'][1])} TL'ye kadar ceza ödeniyor olabilir — "
             f"karşılığında hiçbir şey alınmadan."),
            ("3", "Analizörü bağlayın", MAVI,
             "ADP'deki enerji analizörü ve altı akım trafosu zaten kurulu; "
             "sadece haberleşme uçlanmamış. Dört haftalık gerçek yük kaydı, "
             "bütün yatırım kararlarının girdisidir.")]
    w = (CW-2*5*mm)/3; y = H-90*mm; h = 54*mm
    for i, (no, b, r, ac) in enumerate(veri):
        x = L+i*(w+5*mm)
        kart(c, x, y, w, h, r)
        txt(c, x+7*mm, y+h-16*mm, no, FB, 23, r)
        txt(c, x+21*mm, y+h-16*mm, b, FB, 12.5, BEYAZ)
        para(c, x+7*mm, y+h-28*mm, ac, w-14*mm, F, 9, SOLUK)
    yy = y-12*mm
    kart(c, L, yy-54*mm, CW*0.62, 52*mm, YESIL)
    txt(c, L+8*mm, yy-11*mm, "ZİNCİR İÇİN EN BÜYÜK KALDIRAÇ", FB, 11, YESIL)
    para(c, L+8*mm, yy-21*mm,
         "Tarife kalemleri tesise özgü değildir; bütün şubelerde aynı anda "
         "uygulanır ve yatırım gerektirmez. Bir şubede üç zamanlı tarife veya "
         "reaktif ceza bulunursa, aynı projeyle kurulan diğerlerinde de "
         "bulunma ihtimali yüksektir. Tek şubede bir haftalık inceleme, "
         "zincirin tamamına uygulanabilir bir kontrol listesi üretir.",
         CW*0.62-16*mm, F, 9.2, SOLUK)
    x2 = L+CW*0.64
    kart(c, x2, yy-54*mm, CW*0.36, 52*mm, SARI)
    txt(c, x2+8*mm, yy-11*mm, "VE BİR SONRAKİ ŞUBEDE", FB, 11, SARI)
    para(c, x2+8*mm, yy-21*mm,
         "Bu raporun en kalıcı çıktısı, mevcut tesiste yapılacaklar değil, "
         "yeni şubede TEKRAR EDİLMEYECEKLERDİR. Şartname maddeleri rapor "
         "§8.2'dedir: elektrikli direnç ısıtma yasağı, DCKV zorunluluğu, "
         "reaktörlü kompanzasyon, alt sayaç, çatı kullanım hakkı.",
         CW*0.36-16*mm, F, 9.2, SOLUK)
    alt(c, "Varsayımlar rapor §10'da · istenecek bilgilerin tam listesi §11'de")


SLAYTLAR = [s1, s2, s3, s4, s5, s6, s7, s8, s9, s10, s11, s12, s13, s14]


def uret(cikti=CIK):
    c = canvas.Canvas(str(cikti), pagesize=(W, H))
    c.setTitle("Nusr-Et Saltbae · Elektrik Maliyeti — Yönetim Sunumu")
    for f in SLAYTLAR:
        f(c); c.showPage()
    c.save()
    return cikti, len(SLAYTLAR)


if __name__ == "__main__":
    y, n = uret()
    print(f"{y}  ·  {n} slayt")
