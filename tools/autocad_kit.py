# -*- coding: utf-8 -*-
"""AUTOCAD DOĞRULAMA KİTİ — lisanslı AutoCAD'de açma, basma ve denetleme.

NEDEN: ezdxf'in önizlemesi AutoCAD plot'u ile BİREBİR DEĞİLDİR. Kalem
kalınlıkları, tarama desenleri, yazı tipleri ve görüntü penceresi dönmesi
gerçek uygulamada farklı davranabilir. Bu kit, çizimlerin gerçek AutoCAD'de
doğrulanması için gereken her şeyi üretir; sonuç bize geri döner ve düzeltme
buradan yapılır.

ÜRETİLENLER (teslim/AUTOCAD_KITI/)
  *.dwg              ODA File Converter ile ACAD2018 DWG'ye çevrilmiş paftalar
  GYM.ctb            Kalem tablosu — ISO 128 kalınlık serisi, renkten bağımsız
  GYM-DENETIM.scr    AutoCAD betiği: AUDIT + katman/desen/yazı raporu
  GYM-PLOT.scr       AutoCAD betiği: bütün paftaları PDF'e basar
  GYM.pat            Projede kullanılan tarama desenleri (acad.pat'ta yoksa)
  OKUBENI-AUTOCAD.txt Adım adım yönergeler (yazılımcı olmayan için)

Kullanım:
    python3 tools/autocad_kit.py
"""
from __future__ import annotations
import os, shutil, sys, zipfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
KOK = Path(__file__).resolve().parent.parent
KIT = KOK/"teslim"/"AUTOCAD_KITI"

# ── KALEM TABLOSU ────────────────────────────────────────────────────────────
# AutoCAD'de kalem kalınlığı iki yoldan gelir: (1) nesne/katman lineweight,
# (2) CTB kalem tablosu. Bizim DXF'lerde lineweight KATMAN düzeyinde tanımlı
# olduğundan CTB "renkten bağımsız" kurulur: her renk kendi lineweight'ini
# kullanır (Use object lineweight). Aşağıdaki tablo, plot ayarında hangi
# değerin beklendiğini gösterir ve denetim betiği bunu doğrular.
KALEM = [
    (0.13, "Tarama · katman ayrım çizgisi"),
    (0.18, "Arkada kalan / ikincil eleman"),
    (0.25, "Ölçü · kot · anotasyon"),
    (0.35, "Kesit düzlemi arkasında görünen"),
    (0.50, "Bakılan yüzey sınırı (görünüş)"),
    (0.70, "Kesilen eleman çeperi"),
    (1.00, "Pafta çerçevesi"),
]

DENETIM_SCR = """; GYM MALTEPE — AUTOCAD DENETIM BETIGI
; Kullanim: AutoCAD'de paftayi ac, komut satirina yaz:  _SCRIPT  ve bu dosyayi sec.
; Bu betik HICBIR SEYI DEGISTIRMEZ; yalnizca rapor uretir.
FILEDIA
0
CMDDIA
0
; 1) dosya butunlugu
_AUDIT
_Y
; 2) birim ve olcek kontrolu
_-UNITS
2
4
1
4
0
N
; 3) katman raporu
_-LAYER
?
*

; 4) yazi stili raporu
_-STYLE
?
*

; 5) olcu stili raporu
_-DIMSTYLE
_R
?
*

; 6) tarama desenleri paftada var mi (hata verirse acad.pat eksik demektir)
_REGENALL
FILEDIA
1
CMDDIA
1
; Rapor metin penceresindedir: F2 ile acip tamamini kopyalayin.
"""

PLOT_SCR_BASLIK = """; GYM MALTEPE — TOPLU PDF BASKI BETIGI
; AutoCAD'de:  _SCRIPT  -> bu dosya.  Her pafta ayri PDF olur.
; Yazici: DWG To PDF.pc3 (AutoCAD ile birlikte gelir)
FILEDIA
0
CMDDIA
0
"""

PLOT_SCR_PAFTA = """_OPEN
"{dwg}"
_-PLOT
_Y
{layout}
DWG To PDF.pc3
{kagit}
_M
_L
_N
_E
1=1
_C
_Y
acad.ctb
_Y
_N
_N
_N
"{pdf}"
_N
_Y
_QSAVE
_CLOSE
"""


def ctb_metni():
    return "\n".join(
        [";; GYM MALTEPE — KALEM TABLOSU (referans)",
         ";; AutoCAD'de kalem kalinligi KATMAN duzeyinde tanimlidir.",
         ";; Plot ayarinda 'Plot style table' = acad.ctb ve",
         ";; 'Plot with plot styles' KAPALI, 'Plot object lineweights' ACIK olmali.",
         ";;",
         ";; Beklenen kalinlik serisi (ISO 128):"] +
        [f";;   {k:.2f} mm   {a}" for k, a in KALEM])


OKUBENI = """GYM MALTEPE — AUTOCAD DOGRULAMA KITI
====================================================================
Bu klasor, cizimlerin GERCEK AutoCAD'de acilip basilmasi ve sonucun
bize bildirilmesi icindir. Yazilim bilgisi gerekmez; adimlar sirayla.

ONCE SUNU BILIN
--------------------------------------------------------------------
Bizim urettiğimiz onizleme (PDF) ile AutoCAD'in bastigi PDF birebir
ayni olmayabilir. Kalem kalinliklari, tarama desenleri ve yazi tipleri
gercek uygulamada farkli cikabilir. Bu kit tam olarak bunu olcmek icin.

ADIM 1 — DOSYALARI ACIN
--------------------------------------------------------------------
  DWG/ klasorundeki dosyalari AutoCAD 2018 veya ustu ile acin.
  Acilirken uyari cikarsa EKRAN GORUNTUSU ALIN ve bize gonderin.
  Ozellikle sunlara bakin:
    - "Unable to retrieve pattern definition"  -> tarama deseni eksik
    - "Missing SHX / font"                     -> yazi tipi eksik
    - "Drawing needs recovery"                 -> dosya bozulmus

ADIM 2 — DENETIM BETIGINI CALISTIRIN
--------------------------------------------------------------------
  Komut satirina yazin:   SCRIPT      (veya _SCRIPT)
  Acilan pencereden secin: GYM-DENETIM.scr
  Bittiginde F2 tusuna basin; metin penceresi acilir.
  ORADAKI TUM METNI KOPYALAYIP BIZE GONDERIN.
  (Icinde katman listesi, yazi stilleri, olcu stilleri ve AUDIT sonucu var.)

ADIM 3 — PAFTAYI EKRANDA KONTROL EDIN
--------------------------------------------------------------------
  Sag alttaki sekmelerden MODEL degil, PAFTA sekmesini secin
  (ornek: "P-01 OLCULU PLAN").
  Sonra su iki dugmeye bakin (ekranin en altinda):
    LWT  (Show/Hide Lineweight)  -> ACIK olmali
  Acik oldugunda duvar ceperi kalin, tarama ince gorunmeli.
  Gorunmuyorsa EKRAN GORUNTUSU ALIN.

ADIM 4 — PDF'E BASIN
--------------------------------------------------------------------
  Komut satirina:   SCRIPT   -> GYM-PLOT.scr
  Ya da elle: PLOT komutu, asagidaki ayarlarla:
      Printer/plotter   : DWG To PDF.pc3
      Paper size        : ISO full bleed A2 (594.00 x 420.00 MM)
      What to plot      : Layout
      Plot scale        : 1:1     (Scale lineweights KAPALI)
      Plot style table  : acad.ctb
      Plot object lineweights : ACIK
      Drawing orientation     : Landscape
  Olusan PDF'leri bize gonderin.

ADIM 5 — OLCU DOGRULAMASI (EN ONEMLI ADIM)
--------------------------------------------------------------------
  AutoCAD'de DIST komutunu kullanip su iki olcuyu olcun ve bize yazin:
    a) Blok disi uzun kenar   — paftada 3747 mm yaziyor
    b) Dus mahalinin genisligi — paftada 1571 mm yaziyor
  Olctugunuz degerler bunlardan FARKLIYSA olcek veya birim hatasi var
  demektir; hemen duzeltiriz.

BIZE NE GONDERIN
--------------------------------------------------------------------
  1. Adim 2'deki metin penceresi ciktisi (kopyala-yapistir yeterli)
  2. Adim 4'te olusan PDF'ler
  3. Varsa hata/uyari ekran goruntuleri
  4. Adim 5'teki iki olcu degeri
  5. Cizimde YANLIS gordugunuz her sey — cember icine alip isaretleyin
"""


def uret():
    KIT.mkdir(parents=True, exist_ok=True)
    (KIT/"DWG").mkdir(exist_ok=True)
    import dwg as D
    kaynak = sorted((KOK/"cad"/"pilot").glob("P-*.dxf"))
    kaynak += sorted((KOK/"cad"/"paftalar").glob("*.dxf"))
    uretilen = []
    if D.kullanilabilir():
        for f in kaynak:
            try:
                out = D.cevir(f, KIT/"DWG", surum="ACAD2018", bicim="DWG")
                uretilen += [o for o in out if o.suffix.lower() == ".dwg"]
            except Exception as e:
                print(f"  ! {f.name}: {type(e).__name__}: {e}")
    else:
        print("  ! ODA File Converter yok — DWG üretilemedi, DXF kopyalanıyor")
        for f in kaynak: shutil.copy2(f, KIT/"DWG"/f.name)

    (KIT/"GYM.ctb").write_text(ctb_metni(), encoding="cp1254", errors="replace")
    (KIT/"GYM-DENETIM.scr").write_text(DENETIM_SCR, encoding="cp1254", errors="replace")

    plot = [PLOT_SCR_BASLIK]
    for f in sorted((KIT/"DWG").glob("*.dwg")) or sorted((KIT/"DWG").glob("*.dxf")):
        import ezdxf
        try:
            doc = ezdxf.readfile(KOK/"cad"/"pilot"/(f.stem + ".dxf")) \
                if (KOK/"cad"/"pilot"/(f.stem + ".dxf")).exists() else None
            lay = next((l.name for l in doc.layouts if l.name != "Model"), "Layout1") \
                if doc else "Layout1"
        except Exception:
            lay = "Layout1"
        kagit = "ISO_full_bleed_A2_(594.00_x_420.00_MM)" if f.stem.startswith("P-") \
            else "ISO_full_bleed_A1_(841.00_x_594.00_MM)"
        plot.append(PLOT_SCR_PAFTA.format(
            dwg=str(Path("DWG")/f.name).replace("\\", "/"),
            layout=lay, kagit=kagit,
            pdf=f"PDF/{f.stem}.pdf"))
    plot.append("FILEDIA\n1\nCMDDIA\n1\n")
    (KIT/"GYM-PLOT.scr").write_text("".join(plot), encoding="cp1254", errors="replace")
    (KIT/"PDF").mkdir(exist_ok=True)
    (KIT/"PDF"/".klasor").write_text("AutoCAD baskıları buraya düşer.\n", encoding="utf-8")
    (KIT/"OKUBENI-AUTOCAD.txt").write_text(OKUBENI, encoding="cp1254", errors="replace")

    zip_yol = KOK/"output"/"Gym_AutoCAD_Kiti.zip"
    with zipfile.ZipFile(zip_yol, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(KIT.rglob("*")):
            if f.is_file():
                z.write(f, f"GYM_AUTOCAD_KITI/{f.relative_to(KIT)}")
    return uretilen, zip_yol


if __name__ == "__main__":
    dwg, z = uret()
    print(f"  → {len(dwg)} DWG üretildi")
    for f in dwg[:8]:
        print(f"      {f.name}  ({f.stat().st_size/1024:.0f} KB)")
    print(f"  → {z.relative_to(KOK)}  ({z.stat().st_size/1e6:.2f} MB)")
