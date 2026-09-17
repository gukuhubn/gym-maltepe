# -*- coding: utf-8 -*-
"""BÜTÇE TAKİP TABLOSU — referans «Saltbae_AquaFlorya_Butce» düzeninde.

Yüklenici/firma bazında: keşif-sözleşme bedeli, revize bütçe, para birimi, kur,
ödenen, kalan, açıklama.  Çok para birimli toplam ve TL karşılığı alt tabloda.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from openpyxl import Workbook
from openpyxl.worksheet.datavalidation import DataValidation
import proj as P, fiyat as FY
from xl import *

MEK = (sum(x[4]*x[5] for x in P.B_MEK), sum(x[4]*x[6] for x in P.B_MEK))
ELK = (sum(x[4]*x[5] for x in P.B_ELK), sum(x[4]*x[6] for x in P.B_ELK))
GT = FY.grup_toplam()

# (sıra, iş kalemi, önerilen yüklenici tipi, para birimi, bütçe düşük, bütçe yüksek, açıklama)
KALEM = []
for g, ad, firma, kdv in FY.GRUP:
    lo, hi, n = GT.get(g, (0, 0, 0))
    KALEM.append((ad.title(), firma, "TL", lo, hi,
                  f"{n} poz · keşif özeti paket {g}"))
KALEM.append(("Mekanik Tesisat İşleri", "Mekanik taşeronu", "TL", MEK[0], MEK[1],
              f"{len(P.B_MEK)} poz · M-01…M-07"))
KALEM.append(("Elektrik Tesisat İşleri", "Elektrik taşeronu", "TL", ELK[0], ELK[1],
              f"{len(P.B_ELK)} poz · E-01…E-07"))
DOGRUDAN = (sum(k[3] for k in KALEM), sum(k[4] for k in KALEM))
KALEM += [
 ("Yüklenici Koordinasyon / Genel Gider ve Kâr", "Ana yüklenici", "TL",
  DOGRUDAN[0]*0.18, DOGRUDAN[1]*0.18, "İnşaat %20 · MEP %10 (referans proje oranları)"),
 ("Beklenmedik Giderler Payı", "—", "TL",
  DOGRUDAN[0]*1.18*P.V["beklenmedik"][0], DOGRUDAN[1]*1.18*P.V["beklenmedik"][0],
  f"%{int(P.V['beklenmedik'][0]*100)} · ıslak hacim ve mevcut durum belirsizliği"),
 ("Mimari Proje Müellifliği ve Ruhsat Dosyası", "Proje müellifi mimar", "TL",
  180000, 320000, "1/50 onaylı takım · ruhsat başvurusu — VARSAYIM"),
 ("Statik ve Tesisat Proje Onayı", "Mühendislik büroları", "TL",
  60000, 120000, "Gerekirse — VARSAYIM"),
 ("GSİM Tescil ve Belediye Ruhsat Harçları", "Kamu", "TL",
  45000, 95000, "Harç ve döner sermaye — VARSAYIM, yerinde teyit edilecek"),
 ("Spor Ekipmanı (ring, istasyon, kardiyo)", "İşverence temin", "EUR",
  0, 0, "İşveren tarafından satın alındı — bütçe dışı"),
 ("Hareketli Mobilya ve Dekorasyon", "Mobilya firması", "TL",
  85000, 160000, "Oturma grubu, bitki, aksesuar — VARSAYIM"),
 ("Tabela, Reklam ve Görsel Kimlik", "Reklam firması", "TL",
  95000, 185000, "Cephe tabelası + iç yönlendirme"),
 ("Sigorta Poliçesi (all-risk)", "Sigorta", "TL",
  35000, 70000, "Tadilat süresi all-risk + 3. şahıs mali mesuliyet"),
 ("Enerji Aboneliği / Güç Artırımı", "Dağıtım şirketi", "TL",
  0, 0, "BİLİNMİYOR — mevcut pano gücü tespit edilmeden fiyatlanamaz"),
]

wb = Workbook(); wb.remove(wb.active)

# ═══════════════ 1 · BÜTÇE TAKİBİ ═════════════════════════════════════════════
ws = wb.create_sheet("1 · BÜTÇE TAKİBİ"); sayfa_ayari(ws)
genislikler(ws, [6, 44, 24, 9, 17, 17, 17, 9, 11, 17, 17, 44])
r = baslik(ws, 1, "BÜTÇE TAKİP TABLOSU  ·  BUDGET CONTROL",
           f"{P.PROJE} · {P.REV} · {P.TARIH} · Tutarlar KDV hariç", 12)
r += 1
r = tablo_basligi(ws, r, ["SIRA", "İŞ KALEMİ", "YÜKLENİCİ / FİRMA", "PARA\nBİRİMİ",
                          "BÜTÇE TAHMİNİ\nDÜŞÜK", "BÜTÇE TAHMİNİ\nYÜKSEK",
                          "SÖZLEŞME BEDELİ", "KUR", "SAPMA\n%", "ÖDENEN", "KALAN",
                          "AÇIKLAMA"], 34)
bas = r
for i, (ad, firma, pb, lo, hi, ack) in enumerate(KALEM, 1):
    alt = LIGHT if i % 2 == 0 else WHITE
    st(ws.cell(r, 1, i), False, 9, GREY, alt, "center")
    st(ws.cell(r, 2, ad), False, 10, INK, alt, "left", True)
    st(ws.cell(r, 3, firma), False, 9, GREY, alt, "left")
    st(ws.cell(r, 4, pb), False, 9, INK, alt, "center")
    st(ws.cell(r, 5, round(lo)), False, 10, GREY, alt, "right", fmt=TL0)
    st(ws.cell(r, 6, round(hi)), False, 10, GREY, alt, "right", fmt=TL0)
    st(ws.cell(r, 7, None), True, 10, NAVY, BOS, "right", fmt=TL0)       # gerçek sözleşme
    st(ws.cell(r, 8, 1 if pb == "TL" else None), False, 9, INK,
       alt if pb == "TL" else BOS, "center", fmt=NUM)
    st(ws.cell(r, 9, f'=IF(G{r}=0,"",G{r}/AVERAGE(E{r}:F{r})-1)'),
       False, 9, INK, alt, "center", fmt='+0%;-0%;0%')
    st(ws.cell(r, 10, None), False, 10, NAVY, BOS, "right", fmt=TL0)     # ödenen
    st(ws.cell(r, 11, f"=G{r}*H{r}-J{r}"), True, 10, NAVY, alt, "right", fmt=TL0)
    st(ws.cell(r, 12, ack), False, 9, GREY, alt, "left", True)
    ws.row_dimensions[r].height = 26; r += 1
son = r-1
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
st(ws.cell(r, 1, "TOPLAM (KDV HARİÇ)"), True, 11, NAVY, GRUPBG, "left")
for j, L in ((5, "E"), (6, "F"), (7, "G"), (10, "J"), (11, "K")):
    st(ws.cell(r, j, f"=SUM({L}{bas}:{L}{son})"), True, 11, NAVY, GRUPBG, "right", fmt=TL0)
for j in (8, 9, 12): st(ws.cell(r, j, ""), True, 10, NAVY, GRUPBG, "center")
top = r; r += 1
st(ws.cell(r, 1, ""), True, 10, NAVY, WHITE, "center")
ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
st(ws.cell(r, 2, "KDV (%20)"), False, 10, INK, WHITE, "left")
for j, L in ((5, "E"), (6, "F"), (7, "G")):
    st(ws.cell(r, j, f"={L}{top}*0.20"), False, 10, INK, WHITE, "right", fmt=TL0)
for j in (8, 9, 10, 11, 12): st(ws.cell(r, j, ""), False, 10, INK, WHITE, "center")
kdv = r; r += 1
st(ws.cell(r, 1, ""), True, 10, WHITE, COPPER, "center")
ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
st(ws.cell(r, 2, "GENEL TOPLAM (KDV DÂHİL)"), True, 12, WHITE, COPPER, "left")
for j, L in ((5, "E"), (6, "F"), (7, "G")):
    st(ws.cell(r, j, f"={L}{top}+{L}{kdv}"), True, 12, WHITE, COPPER, "right", fmt=TL0)
for j in (8, 9, 10, 11, 12): st(ws.cell(r, j, ""), True, 10, WHITE, COPPER, "center")
ws.row_dimensions[r].height = 22
r += 2
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=12)
st(ws.cell(r, 1, "SÖZLEŞME BEDELİ ve ÖDENEN sütunları sözleşmeler imzalandıkça doldurulur; "
                 "SAPMA sütunu bütçe tahmininin ortalamasına göre otomatik hesaplanır. "
                 "Yabancı para birimli sözleşmelerde KUR sütununa sözleşme kuru yazılır; "
                 "KALAN sütunu TL karşılığını verir."), False, 9, GREY, WHITE, "left", True)
ws.row_dimensions[r].height = 28
dondur(ws, "A5")

# ═══════════════ 2 · NAKİT AKIŞI ══════════════════════════════════════════════
ws = wb.create_sheet("2 · NAKİT AKIŞI"); sayfa_ayari(ws)
genislikler(ws, [6, 40, 12] + [14]*8)
r = baslik(ws, 1, "NAKİT AKIŞI  ·  CASH FLOW",
           f"Program süresi {P.PROGRAM_HAFTA} hafta — paket bazında hakediş dağılımı (%)", 11)
r += 1
aylar = ["1. AY", "2. AY", "3. AY", "4. AY", "5. AY", "6. AY", "7. AY", "8. AY"]
r = tablo_basligi(ws, r, ["SIRA", "UYGULAMA PAKETİ", "BÜTÇE\n(orta)"] + aylar, 26)
bas = r
for i, (ad, firma, pb, lo, hi, ack) in enumerate(KALEM, 1):
    alt = LIGHT if i % 2 == 0 else WHITE
    st(ws.cell(r, 1, i), False, 9, GREY, alt, "center")
    st(ws.cell(r, 2, ad), False, 9, INK, alt, "left", True)
    st(ws.cell(r, 3, round((lo+hi)/2)), False, 9, NAVY, alt, "right", fmt=TL0)
    for j in range(4, 12):
        st(ws.cell(r, j, None), False, 9, NAVY, BOS, "center", fmt=PCT)
    r += 1
son = r-1
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
st(ws.cell(r, 1, "AYLIK NAKİT İHTİYACI (TL)"), True, 10, NAVY, GRUPBG, "left")
st(ws.cell(r, 3, f"=SUM(C{bas}:C{son})"), True, 10, NAVY, GRUPBG, "right", fmt=TL0)
for j in range(4, 12):
    L = chr(64+j)
    st(ws.cell(r, j, f"=SUMPRODUCT($C{bas}:$C{son},{L}{bas}:{L}{son})"),
       True, 10, NAVY, GRUPBG, "right", fmt=TL0)
ay = r; r += 1
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
st(ws.cell(r, 1, "KÜMÜLATİF"), True, 10, COPPER, WHITE, "left")
st(ws.cell(r, 3, ""), True, 10, COPPER, WHITE, "right")
for j in range(4, 12):
    L = chr(64+j)
    prev = chr(64+j-1)
    f = f"={L}{ay}" if j == 4 else f"={prev}{r}+{L}{ay}"
    st(ws.cell(r, j, f), True, 10, COPPER, WHITE, "right", fmt=TL0)
r += 2
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=11)
st(ws.cell(r, 1, "Her satırda aylık gerçekleşme yüzdeleri toplamı %100 olmalıdır. "
                 "Sarı hücreler iş programına göre doldurulur; aylık nakit ihtiyacı ve "
                 "kümülatif eğri otomatik hesaplanır."), False, 9, GREY, WHITE, "left", True)
ws.row_dimensions[r].height = 26
dondur(ws, "A5")

def build(path="output/Gym_Butce_Takip.xlsx"):
    wb.save(path)
    print(f"→ {path}  ·  {len(KALEM)} iş kalemi · doğrudan imalat "
          f"{DOGRUDAN[0]:,.0f}–{DOGRUDAN[1]:,.0f} TL")

if __name__ == "__main__":
    build()
