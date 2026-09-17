# -*- coding: utf-8 -*-
"""ELEKTRİK PANO YÜKLEME CETVELİ — referans «ADP / UDP Yükleme Cetveli R00» düzeninde.

Sütunlar (TR/EN çift dilli):
  LİNYE NO · DEVRE KESİCİLER (1./2. cihaz) · YÜKLER (ışık/priz/motor) ·
  KABLO KESİTİ · KABLO CİNSİ · PANO GÜCÜ [W] L1 · L2 · L3 · TOPLAM · AÇIKLAMA
Altbilgi: pano adı, cos φ, nominal akım, talep akımı, kablo kesiti,
  yük grubu bazında talep güç ve diversite katsayıları, giriş şalteri.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from openpyxl import Workbook
import proj as P
from xl import *

# linye kodundan yük tipi
def _tip(kod):
    return {"L": "isik", "P": "priz", "K": "motor", "W": "motor",
            "V": "motor", "Z": "priz"}[kod[0]]
_TIP_AD = {"isik": "IŞIK\nLIGHT.", "priz": "PRİZ\nSOCKET", "motor": "MOTOR\nMOTOR"}

# kaçak akım grupları (proj.KACAK_AKIM) → linye eşlemesi
RCD = {}
for kod, cihaz, kapsam in P.KACAK_AKIM:
    for l in P.LINYE:
        if l[0] in kapsam.replace("—", " ").replace("·", " ").split():
            RCD[l[0]] = (kod, cihaz)

KABLO_CINS = {"3×1,5": "NHXMH", "3×2,5": "NHXMH", "3×6": "N2XH"}

wb = Workbook(); wb.remove(wb.active)

def pano_sayfasi(ad, baslik_metni, linyeler, cosfi, ana_kesici, besleme_kablo,
                 diversite, notlar):
    ws = wb.create_sheet(ad); sayfa_ayari(ws)
    genislikler(ws, [10, 26, 24, 22, 9, 8, 9, 12, 11, 11, 11, 11, 12, 56])
    r = 1
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=14)
    st(ws.cell(r, 1, baslik_metni), True, 13, WHITE, NAVY, "center")
    ws.row_dimensions[r].height = 26; r += 1
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=14)
    st(ws.cell(r, 1, f"{P.PROJE}  ·  {P.REV}  ·  {P.TARIH}"), False, 9, "FF6B7078", LIGHT, "center")
    r += 2

    # ── iki satırlı başlık (referanstaki gibi birleşik hücreli)
    h0 = r
    def mrg(c0, c1, r0, r1, metin, sz=8):
        ws.merge_cells(start_row=r0, start_column=c0, end_row=r1, end_column=c1)
        st(ws.cell(r0, c0, metin), True, sz, WHITE, NAVY2, "center", True)
        for rr in range(r0, r1+1):
            for cc in range(c0, c1+1): ws.cell(rr, cc).border = BOX
    mrg(1, 1, h0, h0+1, "LİNYE NO\nLINE NO")
    mrg(2, 4, h0, h0, "DEVRE KESİCİLER  ·  CIRCUIT BREAKERS")
    mrg(2, 2, h0+1, h0+1, "1. CİHAZ\n1st DEVICE  (kaçak akım rölesi)")
    mrg(3, 3, h0+1, h0+1, "2. CİHAZ\n2nd DEVICE  (otomatik sigorta)")
    mrg(4, 4, h0+1, h0+1, "3. CİHAZ\n3rd DEVICE")
    mrg(5, 7, h0, h0, "YÜKLER  ·  LOADS")
    for j, t in enumerate(("isik", "priz", "motor")):
        mrg(5+j, 5+j, h0+1, h0+1, _TIP_AD[t])
    mrg(8, 8, h0, h0+1, "KABLO KESİTİ\nCABLE SECTION")
    mrg(9, 9, h0, h0+1, "KABLO CİNSİ\nCABLE TYPE")
    mrg(10, 13, h0, h0, "PANO GÜCÜ [W]  ·  PANELBOARD POWER [W]")
    for j, t in enumerate(("L1", "L2", "L3", "TOPLAM\nTOTAL")):
        mrg(10+j, 10+j, h0+1, h0+1, t)
    mrg(14, 14, h0, h0+1, "AÇIKLAMA  ·  DESCRIPTION")
    ws.row_dimensions[h0].height = 18; ws.row_dimensions[h0+1].height = 32
    r = h0+2; bas = r

    onceki_rcd = None
    for kod, tanim, kor, kes, faz, bagli, es, talep in linyeler:
        alt = LIGHT if (r - bas) % 2 == 0 else WHITE
        rcd = RCD.get(kod, ("—", "Korumasız (izlenir)"))
        st(ws.cell(r, 1, kod), True, 9, NAVY, alt, "center")
        # kaçak akım rölesi yalnız grubun ilk satırında yazılır (referans düzeni)
        st(ws.cell(r, 2, rcd[1] if rcd[0] != onceki_rcd else ""), False, 8,
           COPPER if rcd[0] != onceki_rcd else GREY, alt, "left", True)
        onceki_rcd = rcd[0]
        _k = kor.replace("×", "x").replace(" A", "")
        st(ws.cell(r, 3, _k + (" B 6kA" if kod[0] == "L" else " C 6kA")),
           False, 9, INK, alt, "center")
        st(ws.cell(r, 4, "—"), False, 9, GREY, alt, "center")
        t = _tip(kod)
        for j, tt in enumerate(("isik", "priz", "motor")):
            st(ws.cell(r, 5+j, 1 if t == tt else None), False, 9, INK, alt, "center")
        st(ws.cell(r, 8, kes), False, 9, INK, alt, "center")
        st(ws.cell(r, 9, KABLO_CINS.get(kes, "NHXMH")), False, 9, INK, alt, "center")
        W = int(round(bagli*1000))
        for j, f in enumerate(("L1", "L2", "L3")):
            st(ws.cell(r, 10+j, W if faz == f else None), False, 9, INK, alt, "right", fmt="#,##0")
        st(ws.cell(r, 13, f"=SUM(J{r}:L{r})"), True, 9, NAVY, alt, "right", fmt="#,##0")
        st(ws.cell(r, 14, tanim), False, 9, INK, alt, "left", True)
        ws.row_dimensions[r].height = 22; r += 1
    son = r-1

    # yedek linyeler (referans cetvelde her panoda yedek bırakılır)
    for i in range(1, 5):
        alt = LIGHT if (r - bas) % 2 == 0 else WHITE
        st(ws.cell(r, 1, f"Y{i}"), True, 9, GREY, alt, "center")
        st(ws.cell(r, 2, ""), False, 8, GREY, alt, "left")
        st(ws.cell(r, 3, "1x16 C 6kA"), False, 9, GREY, alt, "center")
        st(ws.cell(r, 4, "—"), False, 9, GREY, alt, "center")
        for j in range(3): st(ws.cell(r, 5+j, None), False, 9, INK, alt, "center")
        st(ws.cell(r, 8, "3×2,5"), False, 9, GREY, alt, "center")
        st(ws.cell(r, 9, "NHXMH"), False, 9, GREY, alt, "center")
        for j in range(3): st(ws.cell(r, 10+j, None), False, 9, INK, alt, "right", fmt="#,##0")
        st(ws.cell(r, 13, f"=SUM(J{r}:L{r})"), True, 9, GREY, alt, "right", fmt="#,##0")
        st(ws.cell(r, 14, "YEDEK — ileride ilave edilecek tüketici için boş linye"),
           False, 9, GREY, alt, "left")
        r += 1
    son_y = r-1

    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
    st(ws.cell(r, 1, "TOPLAM / TOTAL"), True, 10, NAVY, GRUPBG, "center")
    for j in range(5, 8):
        L = chr(64+j)
        st(ws.cell(r, j, f"=SUM({L}{bas}:{L}{son_y})"), True, 10, NAVY, GRUPBG, "center")
    st(ws.cell(r, 8, ""), True, 10, NAVY, GRUPBG, "center")
    st(ws.cell(r, 9, ""), True, 10, NAVY, GRUPBG, "center")
    for j in range(10, 14):
        L = chr(64+j)
        st(ws.cell(r, j, f"=SUM({L}{bas}:{L}{son_y})"), True, 10, NAVY, GRUPBG, "right", fmt="#,##0")
    st(ws.cell(r, 14, ""), True, 10, NAVY, GRUPBG, "left")
    tp = r; r += 2

    # ── altbilgi bloğu
    st(ws.cell(r, 1, "PANO BİLGİLERİ"), True, 11, WHITE, NAVY2, "left")
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    st(ws.cell(r, 8, "DİVERSİTE KATSAYILARI"), True, 11, WHITE, NAVY2, "left")
    ws.merge_cells(start_row=r, start_column=8, end_row=r, end_column=14)
    r += 1
    r0 = r
    bilgi = [
     ("PANO ADI / PANEL NAME", ad.split("·")[-1].strip()),
     ("KOLON NO / RISER NO", "—"),
     ("COS φ / POWER FACTOR", cosfi),
     ("NOMİNAL AKIM / NOM. CURRENT [A]", None),
     ("TALEP AKIM / DEMAND CURRENT [A]", None),
     ("BESLEME KABLOSU / SUPPLY CABLE", besleme_kablo),
     ("IŞIK TALEP GÜCÜ / LIGHTING DEMAND [W]", None),
     ("PRİZ TALEP GÜCÜ / SOCKET DEMAND [W]", None),
     ("MOTOR TALEP GÜCÜ / MOTOR DEMAND [W]", None),
     ("TOPLAM TALEP GÜCÜ / TOTAL DEMAND [W]", None),
     ("GİRİŞ ŞALTERİ / MAIN CIRCUIT BREAKER", ana_kesici),
    ]
    for i, (k, v) in enumerate(bilgi):
        st(ws.cell(r, 1, k), True, 9, NAVY, LIGHT, "left")
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
        ws.merge_cells(start_row=r, start_column=5, end_row=r, end_column=6)
        st(ws.cell(r, 5, v), True, 10, INK, WHITE, "center",
           fmt=NUM if isinstance(v, float) else None)
        r += 1
    # hesaplanan hücreler
    ws.cell(r0+3, 5).value = f"=M{tp}/(SQRT(3)*400*E{r0+2})"
    ws.cell(r0+3, 5).number_format = NUM
    ws.cell(r0+4, 5).value = f"=M{r0+9}/(SQRT(3)*400*E{r0+2})"
    ws.cell(r0+4, 5).number_format = NUM
    ws.cell(r0+6, 5).value = f"=SUMIF($E${bas}:$E${son_y},1,$M${bas}:$M${son_y})*K{r0}"
    ws.cell(r0+7, 5).value = f"=SUMIF($F${bas}:$F${son_y},1,$M${bas}:$M${son_y})*K{r0+1}"
    ws.cell(r0+8, 5).value = f"=SUMIF($G${bas}:$G${son_y},1,$M${bas}:$M${son_y})*K{r0+2}"
    ws.cell(r0+9, 5).value = f"=SUM(E{r0+6}:E{r0+8})"
    for k in (6, 7, 8, 9): ws.cell(r0+k, 5).number_format = "#,##0"

    # diversite tablosu (sağ blok)
    for i, (ad_d, kat) in enumerate(diversite):
        st(ws.cell(r0+i, 8, ad_d), True, 9, NAVY, LIGHT, "left")
        ws.merge_cells(start_row=r0+i, start_column=8, end_row=r0+i, end_column=10)
        st(ws.cell(r0+i, 11, kat), True, 10, INK, BOS, "center", fmt=NUM)
        ws.merge_cells(start_row=r0+i, start_column=11, end_row=r0+i, end_column=12)
    # notlar
    for i, n in enumerate(notlar):
        rr = r0+len(diversite)+i
        ws.merge_cells(start_row=rr, start_column=8, end_row=rr, end_column=14)
        st(ws.cell(rr, 8, n), False, 9, INK, WHITE, "left", True)
        ws.row_dimensions[rr].height = 24
    dondur(ws, "A7")
    return ws

# ── ADP · ana dağıtım panosu ─────────────────────────────────────────────────
NOTLAR = [
 "1) Gerilim düşüm hesapları yapılarak kesitler belirlenmiştir — bkz. E-07 paftası.",
 "2) Tüm son devrelerde 30 mA A tipi kaçak akım koruması; ana girişte 300 mA S tipi seçici koruma.",
 "3) Yangın algılama paneli (Z2) kaçak akım rölesi arkasına ALINMAZ; kendi aküsüyle 60 dk beslenir.",
 "4) Kablolar halojensiz (NHXMH / N2XH); ıslak hacim linyeleri ayrı kaçak akım rölesindedir.",
 "5) Akım taşıma kapasiteleri TS HD 60364-5-52, B2 döşeme yöntemi, 30 °C ortam içindir.",
 "6) Pano içinde en az 4 adet yedek linye yeri bırakılacaktır.",
]
DIVERSITE = [("Aydınlatma diversitesi", 0.90), ("Priz diversitesi", 0.80),
             ("Motor / cihaz diversitesi", 0.85)]
pano_sayfasi("1 · ADP", "GYM MALTEPE — ADP ELEKTRİK PANO YÜKLEME CETVELİ R00",
             P.LINYE, 0.90, f"3x{P.ANA_KESICI//3}A TMŞ", P.ANA_KABLO,
             DIVERSITE, NOTLAR)

# ── linye özeti / kontrol sayfası ────────────────────────────────────────────
ws = wb.create_sheet("2 · GERİLİM DÜŞÜMÜ"); sayfa_ayari(ws)
genislikler(ws, [9, 40, 7, 10, 10, 9, 9, 11, 9, 9, 10, 10, 10, 13])
r = baslik(ws, 1, "GERİLİM DÜŞÜMÜ VE KESİT KONTROL CETVELİ",
           f"U={P.U_FAZ:.0f} V · ρ={str(P.RHO_CU).replace('.', ',')} Ω·mm²/m (70 °C) · "
           f"TS HD 60364-5-52 · hat boyu = kuş uçuşu × {P.HAT_KATSAYI} + {P.HAT_DUSEY:.0f} m", 14)
r += 1
r = tablo_basligi(ws, r, ["LİNYE", "TANIM", "FAZ", "Pb (kW)", "Pt (kW)", "cos φ",
                          "Ib (A)", "In (A)", "KABLO", "Iz (A)", "L (m)",
                          "ΔU (V)", "ΔU (%)", "SONUÇ"], 30)
bas = r
for rr in P.PANO_HESAP:
    ok = rr[14] == "UYGUN"
    alt = "FFE7F3EC" if ok else "FFFBE3E1"
    st(ws.cell(r, 1, rr[0]), True, 9, NAVY, alt, "center")
    st(ws.cell(r, 2, rr[1]), False, 9, INK, alt, "left", True)
    st(ws.cell(r, 3, rr[2]), False, 9, INK, alt, "center")
    st(ws.cell(r, 4, rr[3]), False, 9, INK, alt, "right", fmt=NUM)
    st(ws.cell(r, 5, rr[4]), False, 9, INK, alt, "right", fmt=NUM)
    st(ws.cell(r, 6, rr[5]), False, 9, INK, alt, "center", fmt=NUM)
    st(ws.cell(r, 7, rr[6]), False, 9, INK, alt, "right", fmt=NUM)
    st(ws.cell(r, 8, rr[7]), False, 9, INK, alt, "right")
    st(ws.cell(r, 9, rr[8]), False, 9, INK, alt, "center")
    st(ws.cell(r, 10, rr[9]), False, 9, INK, alt, "right", fmt=NUM)
    st(ws.cell(r, 11, rr[10]), False, 9, INK, alt, "right", fmt=NUM)
    st(ws.cell(r, 12, rr[11]), False, 9, INK, alt, "right", fmt=NUM)
    st(ws.cell(r, 13, rr[12]), True, 9, NAVY, alt, "right", fmt=NUM)
    st(ws.cell(r, 14, rr[14]), True, 9, "FF1E5C42" if ok else RED, alt, "center")
    r += 1
son = r-1
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
st(ws.cell(r, 1, "TOPLAM"), True, 10, NAVY, GRUPBG, "left")
st(ws.cell(r, 4, f"=SUM(D{bas}:D{son})"), True, 10, NAVY, GRUPBG, "right", fmt=NUM)
st(ws.cell(r, 5, f"=SUM(E{bas}:E{son})"), True, 10, NAVY, GRUPBG, "right", fmt=NUM)
for j in (6, 7, 8, 9, 10, 11, 12): st(ws.cell(r, j, ""), True, 10, NAVY, GRUPBG, "center")
st(ws.cell(r, 13, f"=MAX(M{bas}:M{son})"), True, 10, NAVY, GRUPBG, "right", fmt=NUM)
st(ws.cell(r, 14, f"maks ΔU"), True, 9, NAVY, GRUPBG, "center")
r += 2
ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=14)
_v = lambda x, n=2: ("%.*f" % (n, x)).replace(".", ",")
_son_not = (f"Ana besleme: {P.ANA_KABLO}, {P.ANA_L:.0f} m, Ib = {_v(P.ANA_IB, 1)} A, "
            f"In = 3×{P.ANA_IN} A, ΔU = %{_v(P.ANA_DU_P)}. En uzak tüketicide toplam "
            f"gerilim düşümü %{_v(P.TOPLAM_DU_MAX)} — TS HD 60364-5-52'nin %5 sınırının "
            f"altındadır. Faz dengesizliği %{_v(P.FAZ_DENGE, 1)}.")
st(ws.cell(r, 1, _son_not), False, 10, "FF1E5C42", "FFE7F3EC", "left", True)
ws.row_dimensions[r].height = 30
dondur(ws, "A5")

def build(path="output/Gym_Pano_Yukleme_Cetveli.xlsx"):
    wb.save(path)
    print(f"→ {path}  ·  {len(P.LINYE)} linye + 4 yedek · {len(wb.sheetnames)} sayfa")

if __name__ == "__main__":
    build()
