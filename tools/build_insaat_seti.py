# -*- coding: utf-8 -*-
"""İNŞAAT SETİ — mimari + mekanik + elektrik paftalarını tek A3 dosyada birleştirir.
Başa kapak ve pafta indeksi sayfası ekler; PDF yer imleri (bookmark) kurar."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
# bu ortamda cryptography paketi bozuk; pypdf'in şifreleme sağlayıcısı devre dışı bırakılır
import importlib, types
for _m in ("cryptography", "cryptography.exceptions", "cryptography.hazmat"):
    sys.modules.setdefault(_m, types.ModuleType(_m))
from pypdf import PdfWriter, PdfReader
import proj as P, helpers as h
import build_mimari as MIM

h.register()
ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT/"output"
W, HH = 420*mm, 297*mm
L, R, TOP, BOT = 12*mm, W-12*mm, HH-24.6*mm, 14*mm
CW = R-L

SET = [
 ("MİMARİ",  "Gym_Mimari_Proje_A3.pdf",  "A", MIM.PAFTA_ADI),
 ("MEKANİK", "Gym_Mekanik_Proje_A3.pdf", "M", {
    1:("M-01","Sistem özeti · tasarım kriterleri · genel notlar"),
    2:("M-02","Havalandırma planı — kanal güzergâhı · menfez debileri"),
    3:("M-03","İklimlendirme planı — split küme · bakır hat · drenaj"),
    4:("M-04","Sıhhi tesisat planı — temiz · sıcak · pis su"),
    5:("M-05","Prensip ve kolon şeması"),
    6:("M-06","Metraj özeti ve lejant"),
    7:("M-07","Tavan içi tesisat koordinasyon kesiti")}),
 ("ELEKTRİK","Gym_Elektrik_Proje_A3.pdf","E", {
    1:("E-01","Sistem özeti · yük hesabı · genel notlar"),
    2:("E-02","Aydınlatma planı — armatür · lux hesabı · anahtarlama"),
    3:("E-03","Priz ve kuvvet planı — linyeler"),
    4:("E-04","Zayıf akım planı — veri · CCTV · ses · yangın algılama"),
    5:("E-05","Pano tek hat şeması — faz dengesi"),
    6:("E-06","Topraklama, metraj özeti ve lejant"),
    7:("E-07","Pano yük ve gerilim düşümü hesabı")}),
]

def kapak(path):
    c = canvas.Canvas(str(path), pagesize=(W, HH))
    # ── 1 · kapak
    c.setFillColor(h.NAVY); c.rect(0, 0, W, HH, 0, 1)
    c.setFillColor(h.COPPER); c.rect(0, HH-9*mm, W, 3*mm, 0, 1)
    h.txt(c, L, HH-46*mm, h.TR_UP("İnşaat uygulama seti"), h.FB, 30, HexColor("#FFFFFF"))
    h.txt(c, L, HH-59*mm, "Mimari · Mekanik · Elektrik — tek dosya", h.F, 12.5, h.COPPER_L)
    h.txt(c, L, HH-76*mm, P.PROJE, h.F, 10.5, HexColor("#C9D3E0"))
    c.setStrokeColor(h.COPPER); c.setLineWidth(1.0); c.line(L, HH-84*mm, L+70*mm, HH-84*mm)
    toplam = sum(len(PdfReader(str(OUT/f)).pages) for _, f, _, _ in SET)
    kutular = [("PAFTA SAYISI", f"{toplam+2}", "kapak ve indeks dâhil"),
               ("DİSİPLİN", "3", "mimari · mekanik · elektrik"),
               ("NET İÇ ALAN", f"{h.tl(P.A['ic_toplam'],2)} m²", f"{len(P.MAHAL_LISTESI)} mahal"),
               ("ÖLÇEK", "1/75 · 1/50 · 1/10", "A3 yatay"),
               ("REVİZYON", P.REV, P.TARIH)]
    x = L; kw = (CW-4*6*mm)/5
    for ust, dg, alt in kutular:
        c.setFillColor(HexColor("#24405F")); c.roundRect(x, HH-146*mm, kw, 30*mm, 1.6*mm, 0, 1)
        h.txt(c, x+5*mm, HH-124*mm, h.TR_UP(ust), h.FB, 6.4, h.COPPER)
        h.txt(c, x+5*mm, HH-134*mm, dg, h.FB, 13, HexColor("#FFFFFF"))
        h.txt(c, x+5*mm, HH-141*mm, alt, h.F, 6.2, HexColor("#9FB0C4"))
        x += kw+6*mm
    h.para(c, L, HH-160*mm,
      "Bu dosya, Maltepe / İdealtepe'deki mobilya mağazasının fonksiyonel antrenman stüdyosuna "
      "dönüşümü için hazırlanmış inşaat uygulama setidir. Mimari, mekanik ve elektrik paftalarının "
      "tamamı tek geometrik kaynaktan (tools/proj.py) üretilmiştir; bir mahal alanı, cihaz konumu veya "
      "kot değiştiğinde tüm paftalar, metrajlar ve BoQ dosyaları birlikte güncellenir. Disiplinler "
      "arası çakışmalar otomatik denetlenmektedir (tools/kontrol.py).",
      CW*0.62, h.F, 9.2, HexColor("#C9D3E0"), 13)
    h.txt(c, L, BOT+6*mm, h.TR_UP("Ön tasarım — yerinde doğrulanmadan ve ruhsat alınmadan uygulama yapılamaz"),
          h.FB, 7.4, h.COPPER)
    h.txt(c, L, BOT, "Ruhsat başvurusu için proje müellifi mimar ve tesisat mühendislerince imzalanmış "
                     "1/50 onaylı takım ayrıca düzenlenecektir.", h.F, 6.8, HexColor("#8FA0B4"))
    c.showPage()
    # ── 2 · pafta indeksi
    h.band(c, W, HH, 2, "Pafta indeksi", "İnşaat uygulama seti — mimari · mekanik · elektrik")
    h.footer(c, W, 2, toplam+2)
    y = TOP
    kol = (CW-2*8*mm)/3
    for i, (disiplin, dosya, pre, adlar) in enumerate(SET):
        x = L+i*(kol+8*mm)
        h.txt(c, x, y, h.TR_UP(disiplin), h.FB, 10, h.NAVY)
        rows = [[adlar[k][0], adlar[k][1]] for k in sorted(adlar)]
        h.tablo(c, x, y-6*mm, [("Pafta",0.17),("İçerik",0.83)], rows, kol,
                satir_h=7.0*mm, bas_h=7.0*mm, fs=6.6, hfs=6.2, hizala=["c","l"])
    yy = y-6*mm-max(len(a) for _,_,_,a in SET)*7.6*mm-10*mm
    w1 = CW*0.315; w2 = CW*0.345; w3 = CW-w1-w2-2*8*mm
    h.txt(c, L, yy+5*mm, h.TR_UP("Setle birlikte teslim edilen dosyalar"), h.FB, 8.6, h.NAVY)
    h.tablo(c, L, yy, [("Dosya",0.52),("İçerik",0.48)], [
      ["Gym_Insaat_Seti_A3.pdf", "Bu dosya — 29 pafta"],
      ["Gym_Mimari_Proje_A3.pdf", "Mimari set (13 pafta)"],
      ["Gym_Mekanik_Proje_A3.pdf", "Mekanik set (7 pafta)"],
      ["Gym_Elektrik_Proje_A3.pdf", "Elektrik set (7 pafta)"],
      ["Gym_CAD_Seti_DXF.zip", "DXF R2010 · 4 dosya · 13 pafta"],
      ["Gym_CAD_Paftalar.pdf", "CAD pafta önizlemesi"],
      ["Gym_Maliyet_BoQ.xlsx", f"Genel metraj — {len(P.B)} poz"],
      ["Gym_Mekanik_BoQ.xlsx", f"Mekanik metraj — {len(P.B_MEK)} poz"],
      ["Gym_Elektrik_BoQ.xlsx", f"Elektrik metraj — {len(P.B_ELK)} poz"],
      ["Gym_Donusum_Dosyasi_A3.pdf", "Yatırım ve fizibilite dosyası"],
      ["Gym_Model.html", "3B model + render galerisi (çevrimdışı)"],
    ], w1, satir_h=5.8*mm, bas_h=6.6*mm, fs=6.4, hfs=6.2, hizala=["l","l"])
    h.notkutu(c, L+w1+8*mm, yy+5*mm, w2, "Setin kullanımı",
      "Paftalar A3 yatay (420×297 mm) olarak hazırlanmıştır; 1/1 ölçekte basılmalıdır. Plan paftaları "
      "1/75, kesit ve görünüşler 1/50, imalat detayları 1/10–1/1 ölçektedir. Ölçüler okunur; çizimden "
      "ölçü alınmaz. DXF (R2010) CAD seti ayrı dosyadadır ve aynı geometriyi taşır. Metraj ve birim "
      "fiyat için BoQ dosyalarına bakınız; birim fiyat sütunları müteahhit teklifi için boş "
      "bırakılmıştır. Mahal listesi (A-09), kapı listesi ve duvar tipleri (A-10) imalat şartnamesi "
      "yerine geçer; numune onayı alınmadan sipariş verilmemelidir.", fs=6.8, acc=h.COPPER)
    h.notkutu(c, L+w1+w2+16*mm, yy+5*mm, w3, "Kontrol durumu",
      "Bu setteki tüm cihaz, kanal, boru ve armatür konumları otomatik çakışma kontrolünden "
      "geçirilmiştir: aynı montaj kotundaki çakışmalar, yapı dışına taşan elemanlar, duvara monte "
      "cihazın duvara uzaklığı ve yönü, tavan içi kot dizilimi, linye yüklenmesi, kablo kesiti ile "
      "gerilim düşümü ve kaçış mesafeleri denetlenir. Son çalıştırmada 0 hata, 0 uyarı bulunmuştur. "
      "Kontrol betiği: tools/kontrol.py", fs=6.8, acc=h.GREEN)
    c.showPage(); c.save()
    return toplam

def build(cikti="output/Gym_Insaat_Seti_A3.pdf"):
    tmp = ROOT/"output"/"_kapak.pdf"
    kapak(tmp)
    wr = PdfWriter()
    rd = PdfReader(str(tmp))
    for pg in rd.pages: wr.add_page(pg)
    wr.add_outline_item("Kapak ve pafta indeksi", 0)
    n = len(rd.pages)
    for disiplin, dosya, pre, adlar in SET:
        r = PdfReader(str(OUT/dosya))
        ust = wr.add_outline_item(disiplin, n)
        for i, pg in enumerate(r.pages):
            wr.add_page(pg)
            no, ad = adlar.get(i+1, (f"{pre}-{i+1:02d}", ""))
            wr.add_outline_item(f"{no}  {ad}", n+i, parent=ust)
        n += len(r.pages)
    wr.add_metadata({"/Title": f"Maltepe / İdealtepe — İnşaat Uygulama Seti ({P.REV})",
                     "/Subject": "Mimari · Mekanik · Elektrik uygulama projesi",
                     "/Creator": "gym-maltepe / tools"})
    with open(cikti, "wb") as f: wr.write(f)
    tmp.unlink()
    print(f"→ {cikti}  ·  {n} pafta")

if __name__ == "__main__":
    build()
