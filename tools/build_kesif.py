# -*- coding: utf-8 -*-
"""KEŞİF ÖZETİ VE METRAJ CETVELLERİ — .xlsx

Düzen, işverenin referans projesindeki (AQUA FLORYA / SALTBAE) keşif özeti ve
metraj cetveli formatını izler:
  ŞARTNAME NO · POZ NO · YAPILACAK İŞİN CİNSİ · MAHAL / PROJE REFERANS ·
  AÇIKLAMA / MARKA · BİRİM · MİKTAR · MALZEME BF/TF · İŞÇİLİK BF/TF ·
  GENEL GİDER · KÂR + RİSK · TOPLAM BF/TF
Metraj cetvelleri: S.NO · YAPILACAK İMALAT AÇIKLAMASI · Birim · Adet ·
  En · Boy · Yükseklik · TOPLANAN (+) · ÇIKARILAN (−) · KISMİ / SAYFA YEKÜNÜ
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from openpyxl import Workbook
import proj as P, metraj as MT, fiyat as FY
from xl import *

# MasterFormat benzeri şartname numaraları (referanstaki "05 75 00" mantığı)
SARTNAME = {
 "A": "02 41 00", "B": "09 21 16", "C": "03 54 00", "D": "09 65 00",
 "E": "09 30 00", "F": "09 51 00", "G": "08 14 00", "H": "12 35 00",
 "I": "10 44 00", "J": "01 50 00",
}
MARKA = {
 "B": "Knauf · Lafarge · Dalsan — eşdeğer",
 "C": "Ardex · Weber · Baumit — eşdeğer",
 "D": "Pavigym · Gerflor · Tarkett — eşdeğer",
 "E": "Vitra · Kalekim · Weber — eşdeğer",
 "F": "Knauf · Dyo · Filli Boya — eşdeğer",
 "G": "Şişecam · Asaş — eşdeğer",
 "H": "Yerli imalat — numune onaylı",
 "I": "TSE belgeli",
 "A": "—", "J": "—",
}

wb = Workbook(); wb.remove(wb.active)

# ═══════════════ 1 · KAPAK ════════════════════════════════════════════════════
ws = wb.create_sheet("1 · KAPAK"); sayfa_ayari(ws, False)
genislikler(ws, [4, 34, 6, 30, 22, 22, 4])
r = baslik(ws, 1, "KEŞİF ÖZETİ VE METRAJ CETVELLERİ  ·  BILL OF QUANTITIES", None, 6)
r += 1
for k, v in (("PROJE ADI (PROJECT NAME)", P.PROJE),
             ("İŞİN ADI (PACKAGE NAME)", "Mobilya mağazası → fonksiyonel antrenman stüdyosu dönüşümü"),
             ("İŞVEREN (EMPLOYER)", "………………………………  (işveren adı doldurulacak)"),
             ("YÜKLENİCİ (CONTRACTOR)", "………………………………  (teklif veren firma doldurulacak)"),
             ("NET İÇ KULLANIM ALANI", f"{P.A['ic_toplam']:.2f} m²  ·  {len(P.MAHAL_LISTESI)} mahal"),
             ("REVİZYON (REVISION)", P.REV),
             ("TARİH (DATE)", P.TARIH),
             ("PARA BİRİMİ (CURRENCY)", "TL  ·  KDV hariç"),
             ("FİYAT REFERANSI", FY.REF_TARIH)):
    st(ws.cell(r, 2, k), True, 10, NAVY, LIGHT, "left")
    ws.merge_cells(start_row=r, start_column=4, end_row=r, end_column=6)
    st(ws.cell(r, 4, v), False, 10, INK, WHITE, "left", True)
    ws.row_dimensions[r].height = 20; r += 1

r += 1
st(ws.cell(r, 2, "TEKLİF VERENE NOTLAR"), True, 11, WHITE, NAVY2, "left")
ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6); r += 1
NOTLAR = [
 "1) MALZEME BİRİM FİYATI ve İŞÇİLİK BİRİM FİYATI sütunları BOŞ bırakılmıştır; teklif veren firma doldurur. "
 "Tutar sütunları canlı formülle kendiliğinden hesaplanır.",
 "2) Miktarlar mimari uygulama projesinden (A-01…A-13) türetilmiş, metraj cetvelleri bu dosyanın "
 "«METRAJ» sayfalarında satır satır verilmiştir. Kapı ve pencere boşlukları MİNHA olarak düşülmüştür.",
 "3) Birim fiyatlara; malzeme, işçilik, şantiye içi yatay-düşey taşıma, iskele, koruma, zayiat, "
 "montaj sarfı ve imalat sonrası temizlik dâhildir.",
 "4) Genel gider ile kâr ve risk bedeli ayrı sütunlarda gösterilecek, birim fiyata gömülmeyecektir.",
 "5) Tüm imalatlarda numune onayı zorunludur; onaysız sipariş bedeli yükleniciye aittir.",
 "6) Mevcut duvar kalınlığı, tavan yüksekliği ve şap üst kotu VARSAYIMDIR. Söküm sonrası rölöve ile "
 "doğrulanacak, metrajlar bu dosya üzerinden tek yerden güncellenecektir.",
 "7) Mekanik ve elektrik keşifleri ayrı sayfalardadır; koordinasyon bedeli icmalde ayrıca gösterilir.",
 "8) KDV oranı imalat cinsine göre %20 / %10 olarak icmalde ayrıştırılmıştır.",
]
for n in NOTLAR:
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
    st(ws.cell(r, 2, n), False, 9, INK, WHITE, "left", True)
    ws.row_dimensions[r].height = 26; r += 1
r += 1
imza_blogu(ws, r, 2, 2)

# ═══════════════ 2 · İCMAL ════════════════════════════════════════════════════
ws = wb.create_sheet("2 · İCMAL"); sayfa_ayari(ws)
genislikler(ws, [8, 46, 9, 16, 16, 16, 12, 16, 16])
r = baslik(ws, 1, "İMALAT İCMALİ  ·  SUMMARY OF WORKS",
           f"{P.PROJE} · {P.REV} · {P.TARIH} · Tutarlar KDV hariç TL", 9)
r += 1
r = tablo_basligi(ws, r, ["PAKET\nNO", "UYGULAMA PAKETİ", "POZ\nADEDİ",
                          "TEKLİF TUTARI\n(KDV hariç)", "BÜTÇE TAHMİNİ\nDÜŞÜK",
                          "BÜTÇE TAHMİNİ\nYÜKSEK", "KDV\nORANI",
                          "KDV DÂHİL\nTEKLİF", "KOORDİNASYON\nBEDELİ"])
bas = r
gt = FY.grup_toplam()
icmal_satir = {}
for g, ad, firma, kdv in FY.GRUP:
    lo, hi, n = gt.get(g, (0, 0, 0))
    alt = LIGHT if (r - bas) % 2 == 0 else WHITE
    st(ws.cell(r, 1, g), True, 10, NAVY, alt, "center")
    st(ws.cell(r, 2, ad), False, 10, INK, alt, "left", True)
    st(ws.cell(r, 3, n), False, 10, GREY, alt, "center")
    st(ws.cell(r, 4, f"=SUMIF('3 · KEŞİF ÖZETİ'!$A:$A,\"{g}*\",'3 · KEŞİF ÖZETİ'!$Q:$Q)"),
       True, 10, NAVY, alt, "right", fmt=TL0)
    st(ws.cell(r, 5, lo), False, 10, GREY, alt, "right", fmt=TL0)
    st(ws.cell(r, 6, hi), False, 10, GREY, alt, "right", fmt=TL0)
    st(ws.cell(r, 7, kdv), False, 10, INK, alt, "center", fmt=PCT)
    st(ws.cell(r, 8, f"=D{r}*(1+G{r})"), False, 10, INK, alt, "right", fmt=TL0)
    st(ws.cell(r, 9, f"=D{r}*0.20"), False, 10, COPPER, alt, "right", fmt=TL0)
    icmal_satir[g] = r; r += 1

# MEP paketleri
mek = (sum(x[4]*x[5] for x in P.B_MEK), sum(x[4]*x[6] for x in P.B_MEK))
elk = (sum(x[4]*x[5] for x in P.B_ELK), sum(x[4]*x[6] for x in P.B_ELK))
for g, ad, n, lo, hi, sh, kdv, koord in (
        ("K", "MEKANİK TESİSAT İŞLERİ", len(P.B_MEK), mek[0], mek[1], "5 · MEKANİK KEŞİF", 0.20, 0.10),
        ("L", "ELEKTRİK TESİSAT İŞLERİ", len(P.B_ELK), elk[0], elk[1], "6 · ELEKTRİK KEŞİF", 0.20, 0.10)):
    alt = LIGHT if (r - bas) % 2 == 0 else WHITE
    st(ws.cell(r, 1, g), True, 10, NAVY, alt, "center")
    st(ws.cell(r, 2, ad), False, 10, INK, alt, "left", True)
    st(ws.cell(r, 3, n), False, 10, GREY, alt, "center")
    st(ws.cell(r, 4, f"='{sh}'!$H$3"), True, 10, NAVY, alt, "right", fmt=TL0)
    st(ws.cell(r, 5, lo), False, 10, GREY, alt, "right", fmt=TL0)
    st(ws.cell(r, 6, hi), False, 10, GREY, alt, "right", fmt=TL0)
    st(ws.cell(r, 7, kdv), False, 10, INK, alt, "center", fmt=PCT)
    st(ws.cell(r, 8, f"=D{r}*(1+G{r})"), False, 10, INK, alt, "right", fmt=TL0)
    st(ws.cell(r, 9, f"=D{r}*{koord}"), False, 10, COPPER, alt, "right", fmt=TL0)
    icmal_satir[g] = r; r += 1
son = r-1

st(ws.cell(r, 1, ""), True, 10, NAVY, GRUPBG, "center")
st(ws.cell(r, 2, "DOĞRUDAN İMALAT TOPLAMI"), True, 11, NAVY, GRUPBG, "left")
st(ws.cell(r, 3, ""), True, 10, NAVY, GRUPBG, "center")
for col, f in ((4, f"=SUM(D{bas}:D{son})"), (5, f"=SUM(E{bas}:E{son})"),
               (6, f"=SUM(F{bas}:F{son})"), (8, f"=SUM(H{bas}:H{son})"),
               (9, f"=SUM(I{bas}:I{son})")):
    st(ws.cell(r, col, f), True, 11, NAVY, GRUPBG, "right", fmt=TL0)
st(ws.cell(r, 7, ""), True, 10, NAVY, GRUPBG, "center")
dogrudan = r; r += 2

# ── maliyet kurgusu (referanstaki koordinasyon bedeli mantığı) ───────────────
st(ws.cell(r, 2, "MALİYET KURGUSU"), True, 11, WHITE, NAVY2, "left")
ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6); r += 1
kurgu = [
 ("1", "Doğrudan imalat toplamı (A–L)", f"=D{dogrudan}", f"=E{dogrudan}", f"=F{dogrudan}", ""),
 ("2", f"Yüklenici koordinasyon bedeli — inşaat %20, MEP %10 (referans oranları)",
  f"=I{dogrudan}", f"=E{dogrudan}*0.18", f"=F{dogrudan}*0.18", ""),
 ("3", f"Beklenmedik giderler payı %{int(P.V['beklenmedik'][0]*100)} "
       "(ıslak hacim ve mevcut durum belirsizliği)",
  f"=(D{r-1+0}+0)*0", "", "", ""),
]
lines = []
st(ws.cell(r, 1, "1"), True, 10, NAVY, LIGHT, "center")
st(ws.cell(r, 2, "Doğrudan imalat toplamı (A–L)"), False, 10, INK, LIGHT, "left")
st(ws.cell(r, 4, f"=D{dogrudan}"), True, 10, NAVY, LIGHT, "right", fmt=TL0)
st(ws.cell(r, 5, f"=E{dogrudan}"), False, 10, GREY, LIGHT, "right", fmt=TL0)
st(ws.cell(r, 6, f"=F{dogrudan}"), False, 10, GREY, LIGHT, "right", fmt=TL0)
a1 = r; r += 1
st(ws.cell(r, 1, "2"), True, 10, NAVY, WHITE, "center")
st(ws.cell(r, 2, "Yüklenici koordinasyon / genel gider ve kâr bedeli — "
                 "inşaat %20, mekanik-elektrik %10 (referans proje oranları)"),
   False, 10, INK, WHITE, "left", True)
st(ws.cell(r, 4, f"=I{dogrudan}"), True, 10, NAVY, WHITE, "right", fmt=TL0)
st(ws.cell(r, 5, f"=E{dogrudan}*0.18"), False, 10, GREY, WHITE, "right", fmt=TL0)
st(ws.cell(r, 6, f"=F{dogrudan}*0.18"), False, 10, GREY, WHITE, "right", fmt=TL0)
ws.row_dimensions[r].height = 26
a2 = r; r += 1
bp = P.V["beklenmedik"][0]
st(ws.cell(r, 1, "3"), True, 10, NAVY, LIGHT, "center")
st(ws.cell(r, 2, f"Beklenmedik giderler payı %{int(bp*100)} — "
                 "ıslak hacim ve mevcut durum belirsizliği"), False, 10, INK, LIGHT, "left", True)
st(ws.cell(r, 4, f"=(D{a1}+D{a2})*{bp}"), True, 10, NAVY, LIGHT, "right", fmt=TL0)
st(ws.cell(r, 5, f"=(E{a1}+E{a2})*{bp}"), False, 10, GREY, LIGHT, "right", fmt=TL0)
st(ws.cell(r, 6, f"=(F{a1}+F{a2})*{bp}"), False, 10, GREY, LIGHT, "right", fmt=TL0)
ws.row_dimensions[r].height = 26
a3 = r; r += 1
st(ws.cell(r, 1, ""), True, 10, NAVY, GRUPBG, "center")
st(ws.cell(r, 2, "SÖZLEŞME BEDELİ (KDV HARİÇ)"), True, 11, NAVY, GRUPBG, "left")
for col, L in ((4, "D"), (5, "E"), (6, "F")):
    st(ws.cell(r, col, f"={L}{a1}+{L}{a2}+{L}{a3}"), True, 11, NAVY, GRUPBG, "right", fmt=TL0)
a4 = r; r += 1
st(ws.cell(r, 1, ""), True, 10, NAVY, WHITE, "center")
st(ws.cell(r, 2, "KDV (%20 · imalat cinsine göre icmal satırlarından)"), False, 10, INK, WHITE, "left")
for col, L in ((4, "D"), (5, "E"), (6, "F")):
    st(ws.cell(r, col, f"={L}{a4}*0.20"), False, 10, INK, WHITE, "right", fmt=TL0)
a5 = r; r += 1
st(ws.cell(r, 1, ""), True, 10, NAVY, COPPER, "center")
st(ws.cell(r, 2, "GENEL TOPLAM (KDV DÂHİL)"), True, 12, WHITE, COPPER, "left")
for col, L in ((4, "D"), (5, "E"), (6, "F")):
    st(ws.cell(r, col, f"={L}{a4}+{L}{a5}"), True, 12, WHITE, COPPER, "right", fmt=TL0)
ws.row_dimensions[r].height = 22
r += 2
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=9)
st(ws.cell(r, 1, "BÜTÇE TAHMİNİ sütunları, işverenin referans projesi (Aqua Florya / Saltbae, "
                 "Vogelkopp kesin hakedişi 13.05.2025) gerçekleşen birim fiyatlarının Eylül 2026'ya "
                 f"×{FY.ESKALASYON} ile eskale edilmesiyle kurulmuştur. TEKLİF TUTARI sütunu, "
                 "«3 · KEŞİF ÖZETİ» sayfasına girilen birim fiyatlardan canlı hesaplanır."),
   False, 9, GREY, WHITE, "left", True)
ws.row_dimensions[r].height = 34
dondur(ws, "A5")

# ═══════════════ 3 · KEŞİF ÖZETİ ══════════════════════════════════════════════
ws = wb.create_sheet("3 · KEŞİF ÖZETİ"); sayfa_ayari(ws)
genislikler(ws, [9, 11, 58, 16, 24, 7, 11, 14, 15, 14, 15, 12, 14, 12, 14, 15, 15])
r = baslik(ws, 1, "KEŞİF ÖZETİ  ·  BILL OF QUANTITIES — MİMARİ İMALATLAR",
           f"{P.PROJE} · {P.REV} · {P.TARIH} · KDV hariç TL · "
           "sarı hücreler teklif veren firma tarafından doldurulacaktır", 17)
r += 1
r = tablo_basligi(ws, r, [
 "POZ NO", "ŞARTNAME\nNO", "YAPILACAK İŞİN CİNSİ", "MAHAL / PROJE\nREFERANSI",
 "AÇIKLAMA / MARKA", "BİRİM", "MİKTAR",
 "MALZEME\nBİRİM FİYATI", "MALZEME\nTOPLAM FİYATI",
 "İŞÇİLİK\nBİRİM FİYATI", "İŞÇİLİK\nTOPLAM FİYATI",
 "GENEL GİDER\n(TL)", "GENEL GİDER\nTOPLAM",
 "KÂR + RİSK\n(TL)", "KÂR + RİSK\nTOPLAM",
 "TOPLAM\nBİRİM FİYAT", "TOPLAM\nFİYAT"], 38)
bas = r
grup = None
for poz, ad, birim, mahal, mik, mm, mM, im, iM, tlo, thi in FY.satirlar():
    g = poz[0]
    if g != grup:
        grup = g
        r = grup_satiri(ws, r, g, f"{SARTNAME[g]}   ·   {FY.GRUP_AD[g]}", 17)
    alt = LIGHT if (r - bas) % 2 == 0 else WHITE
    st(ws.cell(r, 1, poz), True, 9, NAVY, alt, "center")
    st(ws.cell(r, 2, SARTNAME[g]), False, 8, GREY, alt, "center")
    st(ws.cell(r, 3, ad), False, 9, INK, alt, "left", True)
    st(ws.cell(r, 4, mahal), False, 8, GREY, alt, "center", True)
    st(ws.cell(r, 5, MARKA[g]), False, 8, GREY, alt, "left", True)
    st(ws.cell(r, 6, birim), False, 9, INK, alt, "center")
    st(ws.cell(r, 7, mik), True, 9, INK, alt, "right", fmt=NUM)
    st(ws.cell(r, 8, None), False, 10, NAVY, BOS, "right", fmt=TL)       # malzeme BF — BOŞ
    st(ws.cell(r, 9, f"=$G{r}*H{r}"), False, 9, INK, alt, "right", fmt=TL)
    st(ws.cell(r, 10, None), False, 10, NAVY, BOS, "right", fmt=TL)      # işçilik BF — BOŞ
    st(ws.cell(r, 11, f"=$G{r}*J{r}"), False, 9, INK, alt, "right", fmt=TL)
    st(ws.cell(r, 12, None), False, 10, NAVY, BOS, "right", fmt=TL)      # genel gider BF
    st(ws.cell(r, 13, f"=$G{r}*L{r}"), False, 9, INK, alt, "right", fmt=TL)
    st(ws.cell(r, 14, None), False, 10, NAVY, BOS, "right", fmt=TL)      # kâr + risk BF
    st(ws.cell(r, 15, f"=$G{r}*N{r}"), False, 9, INK, alt, "right", fmt=TL)
    st(ws.cell(r, 16, f"=H{r}+J{r}+L{r}+N{r}"), True, 9, NAVY, alt, "right", fmt=TL)
    st(ws.cell(r, 17, f"=$G{r}*P{r}"), True, 9, NAVY, alt, "right", fmt=TL)
    ws.row_dimensions[r].height = 30
    r += 1
son = r-1
st(ws.cell(r, 1, ""), True, 10, NAVY, GRUPBG, "center")
ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
st(ws.cell(r, 2, "MİMARİ İMALATLAR TOPLAMI (KDV hariç)"), True, 11, NAVY, GRUPBG, "left")
for j in (7,): st(ws.cell(r, j, ""), True, 10, NAVY, GRUPBG, "center")
for j, L in ((9, "I"), (11, "K"), (13, "M"), (15, "O"), (17, "Q")):
    st(ws.cell(r, j, f"=SUM({L}{bas}:{L}{son})"), True, 11, NAVY, GRUPBG, "right", fmt=TL0)
for j in (8, 10, 12, 14, 16): st(ws.cell(r, j, ""), True, 10, NAVY, GRUPBG, "center")
dondur(ws, "A5")

# ═══════════════ 4 · İŞVEREN BÜTÇE TAHMİNİ ════════════════════════════════════
ws = wb.create_sheet("4 · BÜTÇE TAHMİNİ"); sayfa_ayari(ws)
genislikler(ws, [9, 58, 7, 11, 13, 13, 13, 13, 15, 15, 15])
r = baslik(ws, 1, "İŞVEREN BÜTÇE TAHMİNİ — REFERANS BİRİM FİYATLARLA",
           f"Kaynak: {FY.REF_TARIH}  ·  eskalasyon ×{FY.ESKALASYON}  ·  KDV hariç TL", 11)
r += 1
r = tablo_basligi(ws, r, ["POZ NO", "YAPILACAK İŞİN CİNSİ", "BİRİM", "MİKTAR",
                          "MALZEME\nDÜŞÜK", "MALZEME\nYÜKSEK", "İŞÇİLİK\nDÜŞÜK",
                          "İŞÇİLİK\nYÜKSEK", "TOPLAM BF\nDÜŞÜK", "TUTAR\nDÜŞÜK",
                          "TUTAR\nYÜKSEK"], 34)
bas = r; grup = None
for poz, ad, birim, mahal, mik, mm, mM, im, iM, tlo, thi in FY.satirlar():
    g = poz[0]
    if g != grup:
        grup = g; r = grup_satiri(ws, r, g, FY.GRUP_AD[g], 11)
    alt = LIGHT if (r - bas) % 2 == 0 else WHITE
    st(ws.cell(r, 1, poz), True, 9, NAVY, alt, "center")
    st(ws.cell(r, 2, ad), False, 9, INK, alt, "left", True)
    st(ws.cell(r, 3, birim), False, 9, INK, alt, "center")
    st(ws.cell(r, 4, mik), False, 9, INK, alt, "right", fmt=NUM)
    st(ws.cell(r, 5, mm), False, 9, GREY, alt, "right", fmt=TL0)
    st(ws.cell(r, 6, mM), False, 9, GREY, alt, "right", fmt=TL0)
    st(ws.cell(r, 7, im), False, 9, GREY, alt, "right", fmt=TL0)
    st(ws.cell(r, 8, iM), False, 9, GREY, alt, "right", fmt=TL0)
    st(ws.cell(r, 9, f"=E{r}+G{r}"), False, 9, INK, alt, "right", fmt=TL0)
    st(ws.cell(r, 10, f"=D{r}*(E{r}+G{r})"), True, 9, NAVY, alt, "right", fmt=TL0)
    st(ws.cell(r, 11, f"=D{r}*(F{r}+H{r})"), True, 9, NAVY, alt, "right", fmt=TL0)
    ws.row_dimensions[r].height = 28; r += 1
son = r-1
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=9)
st(ws.cell(r, 1, "MİMARİ İMALATLAR TOPLAMI (KDV hariç)"), True, 11, NAVY, GRUPBG, "left")
st(ws.cell(r, 10, f"=SUM(J{bas}:J{son})"), True, 11, NAVY, GRUPBG, "right", fmt=TL0)
st(ws.cell(r, 11, f"=SUM(K{bas}:K{son})"), True, 11, NAVY, GRUPBG, "right", fmt=TL0)
dondur(ws, "A5")

# ═══════════════ 5 / 6 · MEKANİK VE ELEKTRİK KEŞİF ════════════════════════════
def mep_sayfa(ad, poz_listesi, sartname):
    w = wb.create_sheet(ad); sayfa_ayari(w)
    genislikler(w, [9, 64, 9, 11, 15, 15, 15, 16])
    rr = baslik(w, 1, f"{ad.split(' · ')[1]}  ·  KEŞİF ÖZETİ",
                f"{P.PROJE} · {P.REV} · KDV hariç TL · sarı hücre teklif verence doldurulur", 8)
    rr += 1
    # H3 hücresi icmalde referans verilir → toplam formülünü sabit satıra koy
    w["H3"] = None
    rr = tablo_basligi(w, rr, ["POZ NO", "YAPILACAK İŞİN CİNSİ", "BİRİM", "MİKTAR",
                               "BİRİM FİYAT\n(teklif)", "TUTAR\n(teklif)",
                               "BÜTÇE DÜŞÜK", "BÜTÇE YÜKSEK"], 32)
    b0 = rr
    for poz, gr, tanim, birim, mik, lo, hi, sen in poz_listesi:
        alt = LIGHT if (rr - b0) % 2 == 0 else WHITE
        st(w.cell(rr, 1, poz), True, 9, NAVY, alt, "center")
        st(w.cell(rr, 2, tanim), False, 9, INK, alt, "left", True)
        st(w.cell(rr, 3, birim), False, 9, INK, alt, "center")
        st(w.cell(rr, 4, round(mik, 2)), False, 9, INK, alt, "right", fmt=NUM)
        st(w.cell(rr, 5, None), False, 10, NAVY, BOS, "right", fmt=TL)
        st(w.cell(rr, 6, f"=D{rr}*E{rr}"), True, 9, NAVY, alt, "right", fmt=TL)
        st(w.cell(rr, 7, round(mik*lo)), False, 9, GREY, alt, "right", fmt=TL0)
        st(w.cell(rr, 8, round(mik*hi)), False, 9, GREY, alt, "right", fmt=TL0)
        w.row_dimensions[rr].height = 26; rr += 1
    s0 = rr-1
    ws_ = w
    ws_.merge_cells(start_row=rr, start_column=1, end_row=rr, end_column=5)
    st(ws_.cell(rr, 1, "TOPLAM (KDV hariç)"), True, 11, NAVY, GRUPBG, "left")
    st(ws_.cell(rr, 6, f"=SUM(F{b0}:F{s0})"), True, 11, NAVY, GRUPBG, "right", fmt=TL0)
    st(ws_.cell(rr, 7, f"=SUM(G{b0}:G{s0})"), True, 11, NAVY, GRUPBG, "right", fmt=TL0)
    st(ws_.cell(rr, 8, f"=SUM(H{b0}:H{s0})"), True, 11, NAVY, GRUPBG, "right", fmt=TL0)
    # icmalin okuduğu hücre
    st(ws_.cell(3, 8, f"=F{rr}"), False, 9, WHITE, NAVY, "right", fmt=TL0)
    dondur(w, "A5")

mep_sayfa("5 · MEKANİK KEŞİF", P.B_MEK, "23 00 00")
mep_sayfa("6 · ELEKTRİK KEŞİF", P.B_ELK, "26 00 00")

# ═══════════════ 7 · METRAJ CETVELLERİ ════════════════════════════════════════
ws = wb.create_sheet("7 · METRAJ"); sayfa_ayari(ws)
genislikler(ws, [7, 62, 8, 9, 9, 9, 11, 13, 13])
r = baslik(ws, 1, "METRAJ CETVELLERİ  ·  MEASUREMENT SHEETS",
           f"{P.PROJE} · {P.REV} · {P.TARIH} · Boşluklar MİNHA olarak (−) satırla düşülmüştür. "
           "Ölçüler mimari uygulama projesinden türetilmiştir.", 9)
r += 1
for c in MT.CETVEL:
    # poz başlığı (referanstaki metraj cetveli antedi)
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=9)
    st(ws.cell(r, 1, f"POZ NO: {c.poz}      {c.ad}"), True, 10, WHITE, NAVY2, "left", True)
    ws.row_dimensions[r].height = 24; r += 1
    st(ws.cell(r, 1, "MAHAL:"), True, 8, GREY, LIGHT, "right")
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
    st(ws.cell(r, 2, c.mahal or "—"), False, 8, INK, LIGHT, "left")
    st(ws.cell(r, 6, "BİRİM:"), True, 8, GREY, LIGHT, "right")
    st(ws.cell(r, 7, c.birim), True, 8, INK, LIGHT, "center")
    st(ws.cell(r, 8, "PROJE REF:"), True, 8, GREY, LIGHT, "right")
    st(ws.cell(r, 9, "A-01…A-13", ), False, 8, INK, LIGHT, "center")
    r += 1
    r = tablo_basligi(ws, r, ["S.NO", "YAPILACAK İMALAT AÇIKLAMASI", "BİRİM", "ADET",
                              "EN (m)", "BOY (m)", "YÜKSEKLİK (m)",
                              "TOPLANAN (+)", "ÇIKARILAN (−)"], 26)
    b0 = r
    for i, (aciklama, adet, en, boy, yuk, mik, isaret) in enumerate(c.satir, 1):
        alt = LIGHT if i % 2 == 0 else WHITE
        if isaret == "−": alt = CREAM
        st(ws.cell(r, 1, i), False, 9, GREY, alt, "center")
        st(ws.cell(r, 2, aciklama), False, 9, INK, alt, "left", True)
        st(ws.cell(r, 3, c.birim), False, 9, GREY, alt, "center")
        st(ws.cell(r, 4, adet), False, 9, INK, alt, "right", fmt=NUM)
        st(ws.cell(r, 5, en), False, 9, INK, alt, "right", fmt=NUM)
        st(ws.cell(r, 6, boy), False, 9, INK, alt, "right", fmt=NUM)
        st(ws.cell(r, 7, yuk), False, 9, INK, alt, "right", fmt=NUM)
        if isaret == "+":
            st(ws.cell(r, 8, abs(mik)), True, 9, NAVY, alt, "right", fmt=NUM3)
            st(ws.cell(r, 9, None), False, 9, INK, alt, "right", fmt=NUM3)
        else:
            st(ws.cell(r, 8, None), False, 9, INK, alt, "right", fmt=NUM3)
            st(ws.cell(r, 9, abs(mik)), True, 9, RED, alt, "right", fmt=NUM3)
        r += 1
    s0 = r-1
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=7)
    st(ws.cell(r, 1, "KISMİ YEKÜN"), True, 9, NAVY, GRUPBG, "right")
    st(ws.cell(r, 8, f"=SUM(H{b0}:H{s0})"), True, 9, NAVY, GRUPBG, "right", fmt=NUM3)
    st(ws.cell(r, 9, f"=SUM(I{b0}:I{s0})"), True, 9, RED, GRUPBG, "right", fmt=NUM3)
    r += 1
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=7)
    st(ws.cell(r, 1, f"SAYFA YEKÜNÜ  ·  POZ {c.poz} METRAJI"), True, 10, WHITE, COPPER, "right")
    ws.merge_cells(start_row=r, start_column=8, end_row=r, end_column=9)
    st(ws.cell(r, 8, f"=H{r-1}-I{r-1}"), True, 11, WHITE, COPPER, "right", fmt=NUM)
    ws.row_dimensions[r].height = 20
    r += 2

# ═══════════════ KAYDET ═══════════════════════════════════════════════════════
def build(path="output/Gym_Kesif_Ozeti_BoQ.xlsx"):
    wb.save(path)
    n_poz = len(FY.satirlar())
    n_sat = sum(len(c.satir) for c in MT.CETVEL)
    print(f"→ {path}  ·  {n_poz} mimari poz + {len(P.B_MEK)} mekanik + {len(P.B_ELK)} elektrik "
          f"·  {n_sat} metraj satırı  ·  {len(wb.sheetnames)} sayfa")

if __name__ == "__main__":
    build()
