# -*- coding: utf-8 -*-
"""HAKEDİŞ ŞABLONU — referans projedeki (Vogelkopp kesin hakedişi) düzende.

Sayfalar:  KAPAK · İMALAT İCMALİ · HAKEDİŞ DETAY (paket bazında) ·
           KESİNTİLER VE AVANS · ÖDEME TAKİBİ
İmalat yüzdeleri boş bırakılmıştır; her hakediş döneminde «BU HAKEDİŞ %»
sütunu doldurulur, kümülatif ve ödenecek tutarlar canlı formülle hesaplanır.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from openpyxl import Workbook
import proj as P, fiyat as FY
from xl import *

wb = Workbook(); wb.remove(wb.active)
MEK = (sum(x[4]*x[5] for x in P.B_MEK), sum(x[4]*x[6] for x in P.B_MEK))
ELK = (sum(x[4]*x[5] for x in P.B_ELK), sum(x[4]*x[6] for x in P.B_ELK))
PAKET = [(g, ad, 0.20, 0.20) for g, ad, firma, kdv in FY.GRUP] + \
        [("K", "MEKANİK TESİSAT İŞLERİ", 0.20, 0.10),
         ("L", "ELEKTRİK TESİSAT İŞLERİ", 0.20, 0.10)]
GT = FY.grup_toplam()
TAHMIN = {g: GT.get(g, (0, 0, 0))[:2] for g, *_ in PAKET}
TAHMIN["K"] = MEK; TAHMIN["L"] = ELK

# ═══════════════ 1 · KAPAK ════════════════════════════════════════════════════
ws = wb.create_sheet("1 · KAPAK"); sayfa_ayari(ws, False)
genislikler(ws, [4, 6, 48, 18, 18, 20, 4])
r = baslik(ws, 1, "HAKEDİŞ RAPORU  ·  VALUATION REPORT", None, 6); r += 1
for k, v in (("PROJE ADI (PROJECT NAME)", P.PROJE),
             ("İŞİN ADI ve NUMARASI (PACKAGE NO AND NAME)",
              "Mobilya mağazası → fonksiyonel antrenman stüdyosu dönüşümü"),
             ("İŞVEREN (EMPLOYER)", "………………………………"),
             ("YÜKLENİCİ (CONTRACTOR)", "………………………………"),
             ("HAKEDİŞ NO (VALUATION NUMBER)", "…"),
             ("HAKEDİŞ TANZİM TARİHİ (PREPARATION DATE)", "…… / …… / 20……"),
             ("DÖNEM (PERIOD)", "…… / …… / 20……  –  …… / …… / 20……")):
    st(ws.cell(r, 3, k), True, 10, NAVY, LIGHT, "left")
    ws.merge_cells(start_row=r, start_column=4, end_row=r, end_column=6)
    st(ws.cell(r, 4, v), False, 10, INK, WHITE, "left", True)
    ws.row_dimensions[r].height = 20; r += 1
r += 1
kap = []
for no, ad, f in (
        ("1-", "GERÇEKLEŞEN İŞLER TUTARI (Total Amount of Executed Works)",
         "='2 · İCMAL'!$H$%d"),
        ("2-", "TOPLAM HAKEDİŞ TUTARI (Total Amount of Valuation)", None),
        ("3-", "KDV %20 (Value Added Tax)", None),
        ("4-", "KDV TEVKİFATI 4/10 (VAT Withholding)", None),
        ("5-", "GENEL TOPLAM — TEVKİFAT HARİÇ (Grand Total)", None),
        ("6-", "ÖNCEKİ HAKEDİŞLER TOPLAMI (Previous Valuations)", None),
        ("7-", "AVANS MAHSUBU (Advance Deduction)", None),
        ("8-", "KESİNTİLER TOPLAMI (Total Deductions)", None),
        ("9-", "YÜKLENİCİYE ÖDENECEK NET TUTAR (Net Payment to Contractor)", None)):
    kap.append(r)
    fill = COPPER if no == "9-" else (GRUPBG if no in ("2-", "5-") else WHITE)
    fg = WHITE if no == "9-" else NAVY
    st(ws.cell(r, 2, no), True, 10, fg, fill, "center")
    ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=5)
    st(ws.cell(r, 3, ad), True if no == "9-" else False, 10, fg if no == "9-" else INK,
       fill, "left", True)
    st(ws.cell(r, 6, None), True, 11, fg, fill, "right", fmt=TL0)
    ws.row_dimensions[r].height = 22; r += 1
k1, k2, k3, k4, k5, k6, k7, k8, k9 = kap
ws.cell(k1, 6).value = "='2 · İCMAL'!$H$20"
ws.cell(k2, 6).value = f"=F{k1}"
ws.cell(k3, 6).value = f"=F{k2}*0.20"
ws.cell(k4, 6).value = f"=F{k3}*0.40"
ws.cell(k5, 6).value = f"=F{k2}+F{k3}-F{k4}"
ws.cell(k6, 6).value = "='2 · İCMAL'!$I$20"
ws.cell(k7, 6).value = "='4 · KESİNTİLER'!$E$20"
ws.cell(k8, 6).value = f"=F{k6}+F{k7}"
ws.cell(k9, 6).value = f"=F{k5}-F{k8}"
r += 1
ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
st(ws.cell(r, 2, "KDV tevkifatı oranı, 5018 sayılı Kanun kapsamındaki işveren statüsüne göre "
                 "değişir (yapım işlerinde 4/10). İşverenin mali müşaviriyle teyit edilecektir."),
   False, 9, GREY, WHITE, "left", True)
ws.row_dimensions[r].height = 28; r += 2
imza_blogu(ws, r, 2, 2)

# ═══════════════ 2 · İMALAT İCMALİ ════════════════════════════════════════════
ws = wb.create_sheet("2 · İCMAL"); sayfa_ayari(ws)
genislikler(ws, [8, 44, 18, 18, 13, 13, 13, 18, 18, 14])
r = baslik(ws, 1, "İMALAT İCMALİ  ·  HAKEDİŞ ÖZETİ",
           f"{P.PROJE} · {P.REV} · Sarı sütunlar her hakediş döneminde doldurulur", 10)
r += 1
r = tablo_basligi(ws, r, ["PAKET\nNO", "UYGULAMA PAKETİ", "SÖZLEŞME BEDELİ\n(KDV hariç)",
                          "BÜTÇE TAHMİNİ\n(düşük–yüksek)", "ÖNCEKİ\n%", "BU HAKEDİŞ\n%",
                          "KÜMÜLATİF\n%", "KÜMÜLATİF TUTAR", "ÖNCEKİ HAKEDİŞLER",
                          "BU HAKEDİŞ"], 34)
bas = r
for g, ad, kdv, koord in PAKET:
    lo, hi = TAHMIN[g]
    alt = LIGHT if (r - bas) % 2 == 0 else WHITE
    st(ws.cell(r, 1, g), True, 10, NAVY, alt, "center")
    st(ws.cell(r, 2, ad), False, 10, INK, alt, "left", True)
    st(ws.cell(r, 3, None), False, 10, NAVY, BOS, "right", fmt=TL0)      # sözleşme bedeli
    st(ws.cell(r, 4, f"{lo:,.0f} – {hi:,.0f}".replace(",", ".")), False, 9, GREY, alt, "center")
    st(ws.cell(r, 5, None), False, 10, NAVY, BOS, "center", fmt=PCT)
    st(ws.cell(r, 6, None), False, 10, NAVY, BOS, "center", fmt=PCT)
    st(ws.cell(r, 7, f"=E{r}+F{r}"), True, 10, NAVY, alt, "center", fmt=PCT)
    st(ws.cell(r, 8, f"=C{r}*G{r}"), True, 10, NAVY, alt, "right", fmt=TL0)
    st(ws.cell(r, 9, f"=C{r}*E{r}"), False, 10, INK, alt, "right", fmt=TL0)
    st(ws.cell(r, 10, f"=C{r}*F{r}"), True, 10, COPPER, alt, "right", fmt=TL0)
    ws.row_dimensions[r].height = 22; r += 1
son = r-1
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
st(ws.cell(r, 1, "DOĞRUDAN İMALAT TOPLAMI"), True, 11, NAVY, GRUPBG, "left")
for j, L in ((3, "C"), (8, "H"), (9, "I"), (10, "J")):
    st(ws.cell(r, j, f"=SUM({L}{bas}:{L}{son})"), True, 11, NAVY, GRUPBG, "right", fmt=TL0)
for j in (4, 5, 6, 7): st(ws.cell(r, j, ""), True, 10, NAVY, GRUPBG, "center")
d1 = r; r += 1
st(ws.cell(r, 1, ""), True, 10, NAVY, WHITE, "center")
st(ws.cell(r, 2, "Yüklenici koordinasyon / genel gider ve kâr — inşaat %20, MEP %10"),
   False, 10, INK, WHITE, "left", True)
st(ws.cell(r, 3, f"=SUMPRODUCT(C{bas}:C{son},{{" +
                 ";".join(str(k[3]) for k in PAKET) + "}})"), True, 10, NAVY, WHITE, "right", fmt=TL0)
st(ws.cell(r, 8, f"=SUMPRODUCT(H{bas}:H{son},{{" +
                 ";".join(str(k[3]) for k in PAKET) + "}})"), True, 10, NAVY, WHITE, "right", fmt=TL0)
st(ws.cell(r, 9, f"=SUMPRODUCT(I{bas}:I{son},{{" +
                 ";".join(str(k[3]) for k in PAKET) + "}})"), False, 10, INK, WHITE, "right", fmt=TL0)
st(ws.cell(r, 10, f"=SUMPRODUCT(J{bas}:J{son},{{" +
                  ";".join(str(k[3]) for k in PAKET) + "}})"), True, 10, COPPER, WHITE, "right", fmt=TL0)
for j in (4, 5, 6, 7): st(ws.cell(r, j, ""), False, 10, INK, WHITE, "center")
ws.row_dimensions[r].height = 24
d2 = r; r += 1
st(ws.cell(r, 1, ""), True, 10, NAVY, COPPER, "center")
st(ws.cell(r, 2, "GERÇEKLEŞEN İŞLER TUTARI (KDV HARİÇ)"), True, 12, WHITE, COPPER, "left")
for j, L in ((3, "C"), (8, "H"), (9, "I"), (10, "J")):
    st(ws.cell(r, j, f"={L}{d1}+{L}{d2}"), True, 12, WHITE, COPPER, "right", fmt=TL0)
for j in (4, 5, 6, 7): st(ws.cell(r, j, ""), True, 10, WHITE, COPPER, "center")
ws.row_dimensions[r].height = 22
dondur(ws, "A5")

# ═══════════════ 3 · HAKEDİŞ DETAY ════════════════════════════════════════════
ws = wb.create_sheet("3 · HAKEDİŞ DETAY"); sayfa_ayari(ws)
genislikler(ws, [9, 58, 8, 11, 13, 14, 11, 11, 11, 15, 15])
r = baslik(ws, 1, "HAKEDİŞ DETAYI  ·  POZ BAZINDA GERÇEKLEŞME",
           "Sözleşme metrajı sabittir. «BU HAKEDİŞ METRAJI» sütunu her dönem doldurulur; "
           "kümülatif metraj ve tutar canlı hesaplanır.", 11)
r += 1
r = tablo_basligi(ws, r, ["POZ NO", "YAPILACAK İŞİN CİNSİ", "BİRİM", "SÖZLEŞME\nMETRAJI",
                          "SÖZLEŞME\nBİRİM FİYATI", "SÖZLEŞME\nTUTARI", "ÖNCEKİ\nMETRAJ",
                          "BU HAKEDİŞ\nMETRAJ", "KÜMÜLATİF\nMETRAJ",
                          "KÜMÜLATİF\nTUTAR", "BU HAKEDİŞ\nTUTAR"], 34)
bas = r; grup = None
for poz, ad, birim, mahal, mik, mm, mM, im, iM, tlo, thi in FY.satirlar():
    g = poz[0]
    if g != grup:
        grup = g; r = grup_satiri(ws, r, g, FY.GRUP_AD[g], 11)
    alt = LIGHT if (r - bas) % 2 == 0 else WHITE
    st(ws.cell(r, 1, poz), True, 9, NAVY, alt, "center")
    st(ws.cell(r, 2, ad), False, 9, INK, alt, "left", True)
    st(ws.cell(r, 3, birim), False, 9, INK, alt, "center")
    st(ws.cell(r, 4, mik), True, 9, INK, alt, "right", fmt=NUM)
    st(ws.cell(r, 5, None), False, 9, NAVY, BOS, "right", fmt=TL)
    st(ws.cell(r, 6, f"=D{r}*E{r}"), False, 9, INK, alt, "right", fmt=TL0)
    st(ws.cell(r, 7, None), False, 9, NAVY, BOS, "right", fmt=NUM)
    st(ws.cell(r, 8, None), False, 9, NAVY, BOS, "right", fmt=NUM)
    st(ws.cell(r, 9, f"=G{r}+H{r}"), True, 9, NAVY, alt, "right", fmt=NUM)
    st(ws.cell(r, 10, f"=I{r}*E{r}"), True, 9, NAVY, alt, "right", fmt=TL0)
    st(ws.cell(r, 11, f"=H{r}*E{r}"), True, 9, COPPER, alt, "right", fmt=TL0)
    ws.row_dimensions[r].height = 28; r += 1
son = r-1
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
st(ws.cell(r, 1, "MİMARİ İMALATLAR TOPLAMI (KDV hariç)"), True, 11, NAVY, GRUPBG, "left")
for j, L in ((6, "F"), (10, "J"), (11, "K")):
    st(ws.cell(r, j, f"=SUM({L}{bas}:{L}{son})"), True, 11, NAVY, GRUPBG, "right", fmt=TL0)
for j in (7, 8, 9): st(ws.cell(r, j, ""), True, 10, NAVY, GRUPBG, "center")
dondur(ws, "A5")

# ═══════════════ 4 · KESİNTİLER VE AVANS ══════════════════════════════════════
ws = wb.create_sheet("4 · KESİNTİLER"); sayfa_ayari(ws, False)
genislikler(ws, [6, 30, 20, 18, 20, 30])
r = baslik(ws, 1, "KESİNTİLER VE AVANSLAR  ·  DEDUCTIONS", None, 6); r += 1
r = tablo_basligi(ws, r, ["SIRA", "AÇIKLAMA", "BELGE / NO", "TARİH", "TUTAR (TL)", "NOT"], 24)
bas = r
for i in range(1, 13):
    alt = LIGHT if i % 2 == 0 else WHITE
    st(ws.cell(r, 1, i), False, 9, GREY, alt, "center")
    st(ws.cell(r, 2, f"{i} No'lu avans" if i <= 8 else ""), False, 9, INK, BOS, "left")
    st(ws.cell(r, 3, None), False, 9, INK, BOS, "center")
    st(ws.cell(r, 4, None), False, 9, INK, BOS, "center")
    st(ws.cell(r, 5, None), True, 10, NAVY, BOS, "right", fmt=TL0)
    st(ws.cell(r, 6, None), False, 9, GREY, BOS, "left")
    r += 1
son = r-1
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
st(ws.cell(r, 1, "AVANS VE KESİNTİLER TOPLAMI"), True, 11, NAVY, GRUPBG, "left")
st(ws.cell(r, 5, f"=SUM(E{bas}:E{son})"), True, 11, NAVY, GRUPBG, "right", fmt=TL0)
st(ws.cell(r, 6, ""), True, 10, NAVY, GRUPBG, "left")
r += 2
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
st(ws.cell(r, 1, "Diğer kesintiler: teminat kesintisi, gecikme cezası, işveren tarafından karşılanan "
                 "malzeme bedeli, elektrik-su tüketim payı, sigorta primi vb. bu tabloya ayrı satır "
                 "olarak eklenir."), False, 9, GREY, WHITE, "left", True)
ws.row_dimensions[r].height = 30

# ═══════════════ 5 · ÖDEME TAKİBİ ═════════════════════════════════════════════
ws = wb.create_sheet("5 · ÖDEME TAKİBİ"); sayfa_ayari(ws)
genislikler(ws, [6, 14, 26, 26, 38, 18, 18, 18, 10])
r = baslik(ws, 1, "ÖDEME TAKİP TABLOSU  ·  PAYMENT LOG",
           "Referans projedeki «Vogelkopp tarafından yapılan ödemeler» tablosunun düzeni", 9)
r += 1
r = tablo_basligi(ws, r, ["SIRA", "TARİH", "İMALAT KALEMİ", "FİRMA", "AÇIKLAMA",
                          "ANLAŞMA BEDELİ\n(KDV dâhil)", "ÖDENEN", "BAKİYE", "KDV\n%"], 28)
bas = r
for i in range(1, 41):
    alt = LIGHT if i % 2 == 0 else WHITE
    st(ws.cell(r, 1, i), False, 9, GREY, alt, "center")
    for j in (2, 3, 4, 5): st(ws.cell(r, j, None), False, 9, INK, BOS, "left")
    st(ws.cell(r, 6, None), False, 9, NAVY, BOS, "right", fmt=TL0)
    st(ws.cell(r, 7, None), False, 9, NAVY, BOS, "right", fmt=TL0)
    st(ws.cell(r, 8, f"=F{r}-G{r}"), True, 9, NAVY, alt, "right", fmt=TL0)
    st(ws.cell(r, 9, None), False, 9, INK, BOS, "center")
    r += 1
son = r-1
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
st(ws.cell(r, 1, "GENEL TOPLAM"), True, 11, NAVY, GRUPBG, "left")
for j, L in ((6, "F"), (7, "G"), (8, "H")):
    st(ws.cell(r, j, f"=SUM({L}{bas}:{L}{son})"), True, 11, NAVY, GRUPBG, "right", fmt=TL0)
st(ws.cell(r, 9, ""), True, 10, NAVY, GRUPBG, "center")
dondur(ws, "A5")

def build(path="output/Gym_Hakedis_Sablonu.xlsx"):
    wb.save(path)
    print(f"→ {path}  ·  {len(PAKET)} uygulama paketi · {len(FY.satirlar())} poz · "
          f"{len(wb.sheetnames)} sayfa")

if __name__ == "__main__":
    build()
