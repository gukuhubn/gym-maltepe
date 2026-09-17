# -*- coding: utf-8 -*-
"""ADP TEK HAT / AÇILIM ŞEMASI SETİ — A3 yatay, çok paftalı.

Düzen, işverenin referans pano şeması setini (UDP / ADP, IEC 61439-1&2)
izler:
  E-TH-01  Kapak
  E-TH-02  Pano karakteristik tablosu (IEC 61439-1&2 tip test beyanı)
  E-TH-03  Sembol listesi (IEC 60617, TR/EN)
  E-TH-04  Pano önden görünüş ve modül yerleşimi
  E-TH-05… Şematik diyagram — potansiyel rayları, çapraz sayfa referansları,
           cihaz etiketleri (-F1, -ID1, -X1…), klemens blokları, kablo ve
           tel numaraları, yedek linyeler
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
import proj as P, helpers as h
import draw_sema as S

h.register()
W, HH = 420*mm, 297*mm
L, R = 14*mm, W-14*mm
UST, ALT = HH-16*mm, 46*mm            # antet altta
CW = R-L

PANO_ADI = "ADP"
PROJE_NO = "GYM-25-001-001"
SUTUN = 8                              # sayfa başına linye sütunu
SUTUN_W = CW/SUTUN

# ── linye verisi: RCD gruplaması ile ─────────────────────────────────────────
RCD_GRUP = []
for kod, cihaz, kapsam in P.KACAK_AKIM:
    linyeler = [l for l in P.LINYE
                if l[0] in kapsam.replace("—", " ").replace("·", " ").split()]
    if linyeler: RCD_GRUP.append((kod, cihaz, linyeler))
_ATANAN = {l[0] for _, _, ls in RCD_GRUP for l in ls}
_KALAN = [l for l in P.LINYE if l[0] not in _ATANAN]
if _KALAN: RCD_GRUP.append(("—", "Korumasız (izlenir)", _KALAN))

KABLO_CINS = {"3×1,5": "NHXMH", "3×2,5": "NHXMH", "3×6": "N2XH"}

# sıralı linye listesi + cihaz numaralandırması
AKIS = []
_f = _id = 0
for gk, gc, linyeler in RCD_GRUP:
    _id += 1
    for i, l in enumerate(linyeler):
        _f += 1
        AKIS.append({"linye": l, "F": f"-F{_f}", "ID": f"-ID{_id}" if gk != "—" else None,
                     "ID_ilk": i == 0, "ID_cihaz": gc, "ID_kod": gk,
                     "ID_adet": len(linyeler)})
YEDEK = [{"linye": (f"Y{i}", "YEDEK — ileride ilave edilecek tüketici", "1×16 A",
                    "3×2,5", "L%d" % (i % 3 + 1), 0.0, 1.0, 0.0),
          "F": f"-F{_f+i}", "ID": None, "ID_ilk": False, "ID_cihaz": "", "ID_kod": "—",
          "ID_adet": 0} for i in range(1, 5)]
AKIS += YEDEK
SEMA_SAYFA = math.ceil(len(AKIS)/SUTUN)
N = 4 + SEMA_SAYFA

# ══ ANTET ═════════════════════════════════════════════════════════════════════
def antet(c, no, sayfa_aciklama, sonraki=None):
    y0 = 12*mm; hgt = 30*mm
    c.saveState(); c.setStrokeColor(h.NAVY); c.setLineWidth(0.9)
    c.rect(L, y0, CW, hgt, 0, 0)
    for x in (L+96*mm, L+200*mm, L+286*mm, L+342*mm):
        c.line(x, y0, x, y0+hgt)
    for yy in (y0+10*mm, y0+20*mm):
        c.line(L, yy, L+342*mm, yy)
    c.restoreState()
    def hu(x, y, k, v, w=None, fs=6.4):
        h.txt(c, x+2.2*mm, y+6.4*mm, k, h.F, 4.2, h.GREY)
        h.txt(c, x+2.2*mm, y+2.0*mm, v, h.FB, fs, h.INK)
    hu(L,        y0+20*mm, "Customer Name / Müşteri Adı", "………………………………")
    hu(L+96*mm,  y0+20*mm, "Project Description / Proje Açıklaması", P.KISA)
    hu(L+200*mm, y0+20*mm, "Project Number / Proje Numarası", PROJE_NO)
    hu(L+286*mm, y0+20*mm, "Panel Name / Pano Adı", PANO_ADI, fs=8)
    hu(L,        y0+10*mm, "Drawn By / Çizen", "………………")
    hu(L+96*mm,  y0+10*mm, "Checked By / Kontrol Eden", "………………")
    hu(L+200*mm, y0+10*mm, "Approved By / Onaylayan", "………………")
    hu(L+286*mm, y0+10*mm, "Revision / Revizyon", P.REV)
    hu(L,        y0,       "Project Date / Proje Tarihi", P.TARIH)
    hu(L+96*mm,  y0,       "Page Description / Sayfa Açıklaması", sayfa_aciklama)
    hu(L+200*mm, y0,       "Location / Konum", "Maltepe · İdealtepe")
    hu(L+286*mm, y0,       "Next Sheet / Sonraki Sayfa", sonraki or "—")
    c.saveState(); c.setFillColor(h.NAVY); c.rect(L+342*mm, y0, CW-342*mm, hgt, 0, 1)
    c.restoreState()
    h.txt(c, L+342*mm+(CW-342*mm)/2, y0+20*mm, "SHEET / SAYFA", h.F, 5.0, h.COPPER, "c")
    h.txt(c, L+342*mm+(CW-342*mm)/2, y0+11*mm, f"{no}", h.FB, 22, HexColor("#FFFFFF"), "c")
    h.txt(c, L+342*mm+(CW-342*mm)/2, y0+5*mm, f"Total sheets / Toplam: {N}",
          h.F, 5.0, HexColor("#9FB0C4"), "c")
    # çerçeve
    c.saveState(); c.setStrokeColor(h.NAVY); c.setLineWidth(1.1)
    c.rect(L, y0, CW, HH-y0-10*mm, 0, 0); c.restoreState()

def sayfa_basligi(c, metin, alt=None):
    h.txt(c, L+4*mm, UST-3*mm, h.TR_UP(metin), h.FB, 11, h.NAVY)
    if alt: h.txt(c, L+4*mm, UST-9*mm, alt, h.F, 6.4, h.GREY)

# ══ 1 · KAPAK ═════════════════════════════════════════════════════════════════
def s1(c):
    antet(c, 1, "Cover Page / Kapak", "2")
    c.saveState(); c.setFillColor(h.NAVY)
    c.rect(L, HH-150*mm, CW, 96*mm, 0, 1); c.restoreState()
    h.txt(c, L+16*mm, HH-86*mm, h.TR_UP("Elektrik pano şeması"), h.FB, 30, HexColor("#FFFFFF"))
    h.txt(c, L+16*mm, HH-99*mm, "ELECTRICAL PANEL SCHEMATIC  ·  IEC 61439-1 & 2",
          h.F, 11, h.COPPER_L)
    c.saveState(); c.setStrokeColor(h.COPPER); c.setLineWidth(1.2)
    c.line(L+16*mm, HH-106*mm, L+96*mm, HH-106*mm); c.restoreState()
    h.txt(c, L+16*mm, HH-120*mm, P.PROJE, h.F, 9.5, HexColor("#C9D3E0"))
    h.txt(c, L+16*mm, HH-131*mm, f"Pano adı / Panel name:  {PANO_ADI}    ·    "
          f"Proje no:  {PROJE_NO}    ·    {P.REV}  ·  {P.TARIH}",
          h.F, 9, HexColor("#9FB0C4"))
    y = HH-162*mm
    kols = [("PANO KARAKTERİSTİĞİ", [
                ("Anma gerilimi Ue", "400/230 V  50 Hz"),
                ("Anma akımı In", f"{P.ANA_KESICI//3} A"),
                ("Kısa devre dayanımı Icw", "6 kA / 1 s"),
                ("Nötr işletmesi", "TN-S"),
                ("Koruma sınıfı", "IP 41 (iç mekân)"),
                ("Bölümleme / Form", "Form 2b")]),
             ("İÇERİK", [
                ("Sayfa 1", "Kapak"),
                ("Sayfa 2", "Pano karakteristik tablosu"),
                ("Sayfa 3", "Sembol listesi (IEC 60617)"),
                ("Sayfa 4", "Pano önden görünüş ve modül yerleşimi"),
                (f"Sayfa 5–{N}", "Şematik diyagram"),
                ("Ek", "Pano yükleme cetveli (.xlsx)")]),
             ("ÖZET", [
                ("Linye sayısı", f"{len(P.LINYE)} + {len(YEDEK)} yedek"),
                ("Bağlı güç", f"{h.tl(P.BAGLI_KW,2)} kW"),
                ("Talep gücü", f"{h.tl(P.TALEP_KW,2)} kW"),
                ("Hesap akımı", f"{P.ANA_IB:.1f} A".replace(".", ",")),
                ("Besleme kablosu", P.ANA_KABLO),
                ("Kaçak akım grubu", f"{len(RCD_GRUP)-1} adet 30 mA")])]
    kw = (CW-2*10*mm)/3
    for i, (bas, satirlar) in enumerate(kols):
        x = L+i*(kw+10*mm)
        h.txt(c, x, y, h.TR_UP(bas), h.FB, 9, h.NAVY)
        yy = y-7*mm
        for k, v in satirlar:
            h.txt(c, x, yy, k, h.F, 7.2, h.GREY)
            h.txt(c, x+kw, yy, v, h.FB, 7.2, h.INK, "r")
            c.saveState(); c.setStrokeColor(h.GREY_L); c.setLineWidth(0.4)
            c.line(x, yy-2.2*mm, x+kw, yy-2.2*mm); c.restoreState()
            yy -= 7.0*mm

# ══ 2 · PANO KARAKTERİSTİK TABLOSU ════════════════════════════════════════════
KARAKTER = [
 ("STANDARTLAR / STANDARDS", [
   ("Tip test edilmiş montaj / Type tested assembly", "IEC 61439-1 & 2"),
   ("Diğer / Other", "VDE 0660 · DIN 41488 · BS 5486 · EN 61439-1"),
   ("Tasarım doğrulaması / Design verification", "Üretici beyanı — sevkiyat öncesi rapor")]),
 ("GÜÇ KAYNAĞI / POWER SUPPLY", [
   ("Anma işletme gerilimi / Rated service voltage", "400 V (L-L) · 230 V (L-N)"),
   ("Anma akımı / Rated current", f"{P.ANA_KESICI//3} A"),
   ("Anma kısa süreli dayanım akımı / Icw", "6 kA / 1 s"),
   ("Nötr işletmesi / Neutral operation", "TN-S  (TN-C-S şebeke girişinde ayrılır)"),
   ("Faz sayısı / Number of phases", "3 + N + PE")]),
 ("GENEL ÖZELLİKLER / GENERAL", [
   ("Anma izolasyon gerilimi / Ui", "690 V"),
   ("Anma darbe dayanım gerilimi / Uimp", "6 kV"),
   ("Aşırı gerilim kategorisi / Overvoltage category", "III"),
   ("Anma frekansı / Rated frequency", "50 Hz"),
   ("Dielektrik dayanım / Dielectric withstand", "1,89 kV / 1 s"),
   ("Eşzamanlılık faktörü / Diversity factor", "0,80 – 0,90 (yük grubuna göre)")]),
 ("İKLİM / CLIMATIC", [
   ("Montaj / Installation", "İç mekân — elektrik dolabı (banko arkası nişi)"),
   ("Ortam sıcaklığı / Ambient temperature", "−5 … +40 °C"),
   ("Günlük ortalama / Daily average", "≤ 35 °C"),
   ("Bağıl nem / Humidity", "%10 … %70 (yoğuşmasız)")]),
 ("PANO / ENCLOSURE", [
   ("Tip / Type", "Sıva üstü metal dağıtım panosu, kilitli kapaklı"),
   ("Koruma derecesi / Degree of protection", "IP 41"),
   ("Bölümleme / Segregation", "Form 2b"),
   ("Boya rengi / Colour", "RAL 7035"),
   ("Modül kapasitesi / Module capacity", "54 modül (3 sıra × 18) + %25 yedek hacim")]),
 ("BARALAR / BUSBARS", [
   ("Malzeme / Material", "Elektrolitik bakır"),
   ("Ana bara L1-L2-L3 / Main busbar", "12 × 2 mm (In ≥ 63 A)"),
   ("Nötr barası N / Neutral busbar", "Tam kesit / same section"),
   ("Topraklama barası PE / Earthing bar", "Ayrı, pano gövdesine cıvatalı"),
   ("Kaplama / Coating", "Kalay / tin")]),
 ("BAĞLANTI VE ETİKETLEME / CONNECTION & MARKING", [
   ("Giriş / Incoming", "Alttan · klemens (kablo ile)"),
   ("Çıkış / Outgoing", "Alttan · klemens (kablo ile)"),
   ("Devre işaretleme / Circuit marking", "PVC etiket, vidalı · siyah zemine beyaz"),
   ("Etiket dili / Label language", "Türkçe"),
   ("Şema cebi / Drawing pocket", "Pano kapağı içinde — bu set konulacak")]),
 ("EK İSTEKLER / ADDITIONAL", [
   ("Pano aydınlatması / Panel lighting", "Var — kapı anahtarlı"),
   ("Havalandırma / Ventilation", "Filtreli panjur (doğal)"),
   ("Isıtıcı / Heater", "Yok"),
   ("Deprem seçeneği / Earthquake option", "Duvara 4 noktadan dübelli sabitleme")]),
]
def s2(c):
    antet(c, 2, "Panel Characteristics Table / Pano Karakteristik Tablosu", "3")
    sayfa_basligi(c, "Pano karakteristik tablosu",
                  "IEC 61439-1 & 2 · tip test edilmiş montaj beyanı · TR / EN")
    kol = 2; kw = (CW-8*mm-14*mm)/kol
    y = [UST-16*mm]*kol
    for i, (bas, satirlar) in enumerate(KARAKTER):
        k = 0 if i < 4 else 1
        x = L+4*mm + k*(kw+14*mm)
        c.saveState(); c.setFillColor(h.NAVY2)
        c.rect(x, y[k]-5.6*mm, kw, 5.6*mm, 0, 1); c.restoreState()
        h.txt(c, x+2.5*mm, y[k]-4.0*mm, bas, h.FB, 6.2, HexColor("#FFFFFF"))
        y[k] -= 5.6*mm
        for j, (a, b) in enumerate(satirlar):
            hgt = 6.4*mm
            if j % 2 == 0:
                c.saveState(); c.setFillColor(HexColor("#F4F5F7"))
                c.rect(x, y[k]-hgt, kw, hgt, 0, 1); c.restoreState()
            h.txt(c, x+2.5*mm, y[k]-4.2*mm, a, h.F, 6.0, h.INK)
            h.txt(c, x+kw-2.5*mm, y[k]-4.2*mm, b, h.FB, 6.0, h.NAVY, "r")
            y[k] -= hgt
        c.saveState(); c.setStrokeColor(h.GREY_L); c.setLineWidth(0.5)
        c.rect(x, y[k], kw, UST-16*mm-y[k], 0, 0); c.restoreState()
        y[k] -= 7*mm

# ══ 3 · SEMBOL LİSTESİ ════════════════════════════════════════════════════════
SEMBOLLER = [
 ("mcb",       "Otomatik sigorta (B/C eğrili)", "Miniature circuit breaker (MCB)"),
 ("rcd",       "Kaçak akım koruma rölesi 30 mA", "Residual current device (RCCB)"),
 ("tms",       "Termik-manyetik şalter — pano girişi", "Moulded case circuit breaker (MCCB)"),
 ("kontaktor", "Kontaktör", "Contactor"),
 ("secici",    "1-0-2 seçici (pako) anahtar", "1-0-2 selector switch"),
 ("lamba",     "Sinyal lambası", "Indicator lamp"),
 ("klemens",   "Klemens (terminal)", "Terminal"),
 ("parafudr",  "Parafudr (aşırı gerilim koruma)", "Surge protective device (SPD)"),
 ("gk",        "Güç kaynağı 230 VAC / 24 VDC", "Power supply unit"),
 ("motor",     "Üç fazlı asenkron motor", "Three-phase AC motor"),
 ("armatur",   "Aydınlatma armatürü", "Luminaire"),
 ("priz",      "Priz çıkışı", "Socket outlet"),
 ("toprak",    "Koruma iletkeni / topraklama", "Protective earth"),
]
def s3(c):
    antet(c, 3, "Symbol List / Sembol Listesi", "4")
    sayfa_basligi(c, "Sembol listesi  ·  Symbol list",
                  "IEC 60617 · bu sette kullanılan tüm şema sembolleri")
    kol = 3; kw = (CW-2*12*mm)/kol
    for i, (tip, tr, en) in enumerate(SEMBOLLER):
        k = i % kol; satir = i // kol
        x = L + k*(kw+12*mm); y = UST-22*mm - satir*42*mm
        c.saveState(); c.setStrokeColor(h.GREY_L); c.setLineWidth(0.5)
        c.setFillColor(HexColor("#FBFAF8")); c.rect(x, y-34*mm, kw, 34*mm, 1, 1)
        c.restoreState()
        sx = x+18*mm; sy = y-5*mm
        if   tip == "mcb":       S.mcb(c, sx, sy, 1)
        elif tip == "rcd":       S.rcd(c, sx, sy, 2)
        elif tip == "tms":       S.tmsalter(c, sx, sy)
        elif tip == "kontaktor": S.kontaktor(c, sx, sy, 3)
        elif tip == "secici":    S.secici(c, sx, sy)
        elif tip == "lamba":     S.sinyal_lamba(c, sx, sy, "KIRMIZI", "-H")
        elif tip == "klemens":   S.klemens(c, sx, sy, "1")
        elif tip == "parafudr":  S.parafudr(c, sx, sy)
        elif tip == "gk":        S.guc_kaynagi(c, sx, sy)
        elif tip == "motor":     S.motor(c, sx, sy)
        elif tip == "armatur":   S.armatur_sembol(c, sx, sy)
        elif tip == "priz":      S.priz_sembol(c, sx, sy)
        elif tip == "toprak":    S.toprak(c, sx, sy-4*mm)
        h.txt(c, x+2.5*mm, y-27.5*mm, tr, h.FB, 6.2, h.NAVY)
        h.txt(c, x+2.5*mm, y-31.5*mm, en, h.F, 5.6, h.GREY)

# ══ 4 · PANO ÖNDEN GÖRÜNÜŞ ════════════════════════════════════════════════════
def s4(c):
    antet(c, 4, "Panel Overview / Pano Önden Görünüş", "5")
    sayfa_basligi(c, "Pano önden görünüş ve modül yerleşimi",
                  "Sıva üstü metal dağıtım panosu · 3 sıra × 18 modül · IP 41 · RAL 7035")
    # pano gövdesi — 1 modül = 17,5 mm gerçek; çizimde 1:2
    olc = 0.42
    SIRA_PITCH = 125.0           # mm — gerçek sıra aralığı
    pw = 18*17.5*olc*mm; ph = 3*SIRA_PITCH*olc*mm
    x0 = L+34*mm; y0 = ALT+30*mm
    c.saveState(); c.setStrokeColor(h.NAVY); c.setLineWidth(1.4)
    c.setFillColor(HexColor("#F1F3F5"))
    c.rect(x0-12*mm, y0-16*mm, pw+24*mm, ph+32*mm, 1, 1)
    c.setLineWidth(0.8); c.setFillColor(HexColor("#FFFFFF"))
    c.rect(x0, y0, pw, ph, 1, 1); c.restoreState()
    h.txt(c, x0-12*mm, y0+ph+18*mm, "ADP — ANA DAĞITIM PANOSU", h.FB, 9, h.NAVY)
    h.txt(c, x0-12*mm, y0+ph+13*mm,
          f"Dış ölçü ≈ {int(18*17.5)+70} × {int(3*SIRA_PITCH)+90} × 120 mm (G×Y×D)  ·  "
          f"ölçek 1:{1/olc:.1f}".replace(".", ","), h.F, 6.0, h.GREY)
    # modül sıraları
    sira_h = SIRA_PITCH*olc*mm
    yer = []
    for akim in AKIS:
        kor = akim["linye"][2]
        kutup = int(kor.split("×")[0])
        if akim["ID"] and akim["ID_ilk"]:
            yer.append(("RCD", akim["ID"], 2 if akim["ID_cihaz"].startswith("2") else 4))
        yer.append(("MCB", akim["F"], kutup))
    yer = [("TMŞ", "-1F1", 3), ("SPD", "-F0", 2)] + yer
    mi = 0
    for sira in range(3):
        sy = y0 + ph - (sira+1)*sira_h
        c.saveState(); c.setStrokeColor(h.GREY); c.setLineWidth(0.5); c.setDash(2, 2)
        c.line(x0, sy+sira_h*0.50, x0+pw, sy+sira_h*0.50)     # DIN ray
        c.restoreState()
        h.txt(c, x0-3*mm, sy+sira_h*0.5, f"{sira+1}", h.FB, 6, h.GREY, "r")
        mx = x0
        while mi < len(yer) and mx + yer[mi][2]*17.5*olc*mm <= x0+pw+0.01:
            tip, kod, n = yer[mi]
            ww = n*17.5*olc*mm
            col = {"TMŞ": "#16273D", "SPD": "#B87333", "RCD": "#2F6FB3", "MCB": "#E7EAEE"}[tip]
            c.saveState(); c.setFillColor(HexColor(col)); c.setStrokeColor(h.NAVY)
            c.setLineWidth(0.5)
            c.rect(mx+0.3*mm, sy+sira_h*0.18, ww-0.6*mm, sira_h*0.64, 1, 1)
            c.restoreState()
            _fg = HexColor("#FFFFFF") if tip in ("TMŞ", "SPD", "RCD") else h.NAVY
            _fg2 = HexColor("#C9D3E0") if tip in ("TMŞ", "SPD", "RCD") else h.GREY
            if ww > 5*mm:
                h.txt(c, mx+ww/2, sy+sira_h*0.56, kod, h.FB, 4.0, _fg, "c")
                h.txt(c, mx+ww/2, sy+sira_h*0.30, f"{n}M", h.F, 3.2, _fg2, "c")
            else:
                c.saveState(); c.translate(mx+ww/2, sy+sira_h*0.26); c.rotate(90)
                h.txt(c, 0, 0, kod, h.FB, 3.8, _fg, "l"); c.restoreState()
            mx += ww; mi += 1
        if mx < x0+pw:
            c.saveState(); c.setFillColor(HexColor("#FFFFFF")); c.setStrokeColor(h.GREY_L)
            c.setDash(1.6, 1.6); c.setLineWidth(0.5)
            c.rect(mx+0.3*mm, sy+sira_h*0.18, x0+pw-mx-0.6*mm, sira_h*0.64, 0, 1)
            c.restoreState()
            h.txt(c, (mx+x0+pw)/2, sy+sira_h*0.46, "YEDEK MODÜL YERİ",
                  h.F, 4.4, h.GREY, "c")
    # klemens sırası
    c.saveState(); c.setFillColor(HexColor("#FFF6E8")); c.setStrokeColor(h.COPPER)
    c.setLineWidth(0.6); c.rect(x0, y0-11*mm, pw, 8*mm, 1, 1); c.restoreState()
    h.txt(c, x0+pw/2, y0-9*mm, "-X1  ÇIKIŞ KLEMENS SIRASI  ·  "
          f"{len(P.LINYE)+len(YEDEK)} linye × (L + N) + PE barası", h.FB, 5.4, h.COPPER, "c")
    # açıklama sütunu
    x2 = x0+pw+26*mm; w2 = R-x2-4*mm
    yy = UST-24*mm
    h.txt(c, x2, yy, h.TR_UP("Yerleşim kuralları"), h.FB, 8, h.NAVY); yy -= 6*mm
    for n in ["Giriş şalteri (-1F1) ve parafudr 1. sıranın başındadır; "
              "kaçak akım röleleri kendi grup linyelerinin hemen solundadır.",
              "Aydınlatma linyeleri B eğrili, priz ve cihaz linyeleri C eğrili "
              "otomatik sigorta ile korunur.",
              "Yangın algılama linyesi (Z2) kaçak akım rölesi ARKASINA ALINMAZ; "
              "ayrı ve doğrudan barada beslenir.",
              "Islak hacim linyeleri (L5, P5) ayrı kaçak akım rölesindedir "
              "(TS HD 60364-7-701).",
              "Pano kapağı içine bu şema seti ve yükleme cetveli konulur; "
              "her linye PVC etiketle işaretlenir.",
              "Pano önünde en az 700 mm serbest işletme mesafesi bırakılır.",
              "Modül doluluğu %75'i geçmeyecek; kalan hacim ileride ilave "
              "linye için ayrılmıştır."]:
        for ln in h.wrap(c, "— "+n, h.F, 6.2, w2):
            h.txt(c, x2, yy, ln, h.F, 6.2, h.INK); yy -= 3.4*mm
        yy -= 1.6*mm
    yy -= 3*mm
    h.txt(c, x2, yy, h.TR_UP("Modül sayımı"), h.FB, 8, h.NAVY); yy -= 6*mm
    say = {}
    for tip, kod, n in yer: say[tip] = say.get(tip, [0, 0]); say[tip][0] += 1; say[tip][1] += n
    for tip, (adet, mod) in say.items():
        h.txt(c, x2, yy, {"TMŞ": "Giriş şalteri (TMŞ)", "SPD": "Parafudr",
                          "RCD": "Kaçak akım rölesi", "MCB": "Otomatik sigorta"}[tip],
              h.F, 6.4, h.INK)
        h.txt(c, x2+w2, yy, f"{adet} adet · {mod} modül", h.FB, 6.4, h.NAVY, "r")
        yy -= 5.2*mm
    h.txt(c, x2, yy, "TOPLAM", h.FB, 6.8, h.NAVY)
    h.txt(c, x2+w2, yy, f"{sum(v[0] for v in say.values())} cihaz · "
          f"{sum(v[1] for v in say.values())} modül / 54", h.FB, 6.8, h.COPPER, "r")

# ══ 5… · ŞEMATİK DİYAGRAM ═════════════════════════════════════════════════════
def sema_sayfasi(c, sayfa_no, dilim, ilk, son):
    antet(c, sayfa_no, "Schematic Diagram / Şematik Diyagram",
          str(sayfa_no+1) if not son else "—")
    sayfa_basligi(c, f"Şematik diyagram  ·  sayfa {sayfa_no-4} / {SEMA_SAYFA}",
                  "Potansiyel rayları ve çapraz sayfa referansları · cihaz etiketleri · "
                  "klemens ve kablo bilgileri")
    # ── düşey istasyonlar (mm, sayfa üstünden) ───────────────────────────────
    Y_RAY    = UST-26*mm                 # L1 rayı
    Y_ROZET  = Y_RAY-27*mm               # linye kodu rozeti
    Y_RCD    = Y_ROZET-8*mm              # kaçak akım rölesi girişi
    Y_MCB    = Y_RCD-19*mm               # otomatik sigorta girişi
    Y_SINIR  = ALT+96*mm                 # pano sınırı (saha kablolaması altta)
    Y_KLEMENS= ALT+84*mm                 # çıkış klemensi
    Y_KABLO  = Y_KLEMENS-13*mm
    Y_TANIM  = Y_KABLO-6*mm
    sol_ref = "—" if ilk else f"[{sayfa_no-1}.{SUTUN-1}]"
    sag_ref = "—" if son else f"[{sayfa_no+1}.0]"
    ys = S.potansiyel_raylari(c, L+18*mm, R-18*mm, Y_RAY, 4.2*mm, sol_ref, sag_ref)

    # sütun ızgarası ve sütun numarası
    c.saveState(); c.setStrokeColor(HexColor("#EDEFF2")); c.setLineWidth(0.4)
    for k in range(1, SUTUN):
        xx = L+k*SUTUN_W
        c.line(xx, Y_TANIM-16*mm, xx, Y_ROZET+6*mm)
    c.restoreState()
    for k in range(SUTUN):
        h.txt(c, L+(k+0.5)*SUTUN_W, Y_ROZET+8.4*mm, f"{sayfa_no-4}.{k}",
              h.F, 4.4, HexColor("#B9BEC6"), "c")

    # ── kaçak akım grubu kapsam kutuları (rozetlerin ALTINDA) ────────────────
    k = 0
    while k < len(dilim):
        a = dilim[k]
        if a["ID"] and a["ID_ilk"]:
            n = 1
            while k+n < len(dilim) and dilim[k+n]["ID"] == a["ID"]: n += 1
            x0 = L+k*SUTUN_W+2*mm; x1 = L+(k+n)*SUTUN_W-2*mm
            c.saveState(); c.setStrokeColor(HexColor("#2F6FB3")); c.setLineWidth(0.6)
            c.setDash(2.4, 1.8)
            c.rect(x0, Y_SINIR+4*mm, x1-x0, Y_RCD+5*mm-(Y_SINIR+4*mm), 1, 0)
            c.restoreState()
            c.saveState(); c.setFillColor(HexColor("#EAF1F8"))
            c.rect(x0+0.4*mm, Y_RCD+5*mm-4.6*mm, x1-x0-0.8*mm, 4.2*mm, 0, 1)
            c.restoreState()
            h.txt(c, x0+2.4*mm, Y_RCD+5*mm-3.6*mm,
                  f"{a['ID']}   {a['ID_cihaz'].split(' — ')[0]}   ·   "
                  f"{a['ID_adet']} linye", h.FB, 4.6, HexColor("#1B4F86"))
            k += n
        else:
            k += 1

    # ── pano sınırı: üstü pano içi, altı saha kablolaması
    c.saveState(); c.setStrokeColor(h.COPPER); c.setLineWidth(0.9); c.setDash(6, 3)
    c.line(L+6*mm, Y_SINIR, R-6*mm, Y_SINIR); c.restoreState()
    h.txt(c, L+8*mm, Y_SINIR+2.2*mm, "PANO İÇİ  ·  INSIDE PANEL", h.FB, 5.0, h.COPPER)
    h.txt(c, L+8*mm, Y_SINIR-4.6*mm, "SAHA KABLOLAMASI  ·  FIELD WIRING",
          h.FB, 5.0, h.GREY)
    h.txt(c, R-8*mm, Y_SINIR+2.2*mm, f"PANO SINIRI — {PANO_ADI}", h.FB, 5.0, h.COPPER, "r")

    tn = (sayfa_no-5)*100 + 1
    for k, akim in enumerate(dilim):
        kod, tanim, kor, kes, faz, bagli, es, talep = akim["linye"]
        x = L+(k+0.5)*SUTUN_W
        kutup = int(kor.split("×")[0])
        akim_a = int(kor.split("×")[1].split()[0])
        egri = "B" if kod[0] == "L" else "C"

        # ── rozet
        c.saveState(); c.setFillColor(h.NAVY)
        c.roundRect(x-9*mm, Y_ROZET, 18*mm, 5.2*mm, 1.2*mm, 0, 1); c.restoreState()
        h.txt(c, x, Y_ROZET+1.6*mm, kod, h.FB, 6.0, HexColor("#FFFFFF"), "c")

        # ── faz rayından iniş
        faz_y = ys.get(faz, ys["L1"])
        S.raydan_in(c, faz_y, x, Y_ROZET+5.2*mm, faz)
        S.tel_no(c, x, faz_y-3.2*mm, tn); tn += 1
        h.txt(c, x-1.6*mm, faz_y+1.4*mm, faz, h.FB, 4.2, S.TEL, "r")
        S.tel(c, (x, Y_ROZET), (x, Y_RCD))

        # ── RCD
        y = Y_RCD
        if akim["ID"] and akim["ID_ilk"]:
            _kp = int(akim["ID_cihaz"].split("×")[0]) if "×" in akim["ID_cihaz"] else 2
            _ra = akim["ID_cihaz"].split("×")[1].split()[0] if "×" in akim["ID_cihaz"] else "40"
            y = S.rcd(c, x, y, _kp, [akim["ID"], f"{_kp}×{_ra} A", "30 mA", "A tipi"])
            S.tel_no(c, x, y+3*mm, tn); tn += 1
        elif akim["ID"]:
            h.txt(c, x, Y_RCD-7*mm, f"{akim['ID']} çıkışından",
                  h.F, 4.4, HexColor("#2F6FB3"), "c")
            c.saveState(); c.setStrokeColor(HexColor("#2F6FB3")); c.setLineWidth(0.5)
            c.setDash(1.6, 1.4); c.line(x, Y_RCD, x, Y_MCB); c.restoreState()
            y = Y_MCB
        else:
            h.txt(c, x, Y_RCD-7*mm, "kaçak akım rölesi arkasına alınmaz",
                  h.F, 3.8, S.KIRMIZI, "c")
            S.tel(c, (x, Y_RCD), (x, Y_MCB))
            y = Y_MCB
        if y > Y_MCB: S.tel(c, (x, y), (x, Y_MCB))

        # ── MCB
        y = S.mcb(c, x, Y_MCB, kutup, [akim["F"], f"{akim_a} A", f"{kutup}P {egri}", "6 kA"])
        S.tel_no(c, x, y+3*mm, tn); tn += 1

        # ── klemens
        S.tel(c, (x, y), (x, Y_KLEMENS))
        y2 = S.klemens(c, x, Y_KLEMENS, kod)

        # ── L / N / PE çıkışı
        c.saveState(); c.setLineWidth(0.5)
        c.setStrokeColor(S.TEL); c.line(x-6*mm, y2, x+6*mm, y2)
        for dx, col, lbl in ((-6*mm, S.TEL, "L"), (0, S.NOTR, "N"), (6*mm, S.TOPRAK, "PE")):
            c.setStrokeColor(col); c.line(x+dx, y2, x+dx, y2-3.0*mm)
        c.restoreState()
        for dx, col, lbl in ((-6*mm, S.TEL, "L"), (0, S.NOTR, "N"), (6*mm, S.TOPRAK, "PE")):
            h.txt(c, x+dx, y2-5.4*mm, lbl, h.F, 4.0, col, "c")
        # ── kablo
        h.txt(c, x, Y_KABLO, f"{kes}  {'N2XH' if kes == '3×6' else 'NHXMH'}",
              h.FB, 5.4, h.NAVY, "c")
        c.saveState(); c.setStrokeColor(h.GREY_L); c.setLineWidth(0.5)
        c.line(x-SUTUN_W*0.42, Y_KABLO-2.6*mm, x+SUTUN_W*0.42, Y_KABLO-2.6*mm)
        c.restoreState()
        # ── yük açıklaması
        yy = Y_TANIM
        for ln in h.wrap(c, tanim, h.F, 5.4, SUTUN_W-5*mm)[:3]:
            h.txt(c, x, yy, ln, h.F, 5.4, h.INK, "c"); yy -= 3.2*mm
        if bagli:
            h.txt(c, x, yy-1.4*mm, f"{int(bagli*1000)} W  ·  {faz}",
                  h.FB, 5.2, h.COPPER, "c")
        else:
            h.txt(c, x, yy-1.4*mm, "— (yedek)", h.FB, 5.2, h.GREY, "c")
        # ── mahal / güzergâh notu
        h.txt(c, x, yy-6.4*mm, "→ E-02/E-03 planı", h.F, 4.2, h.GREY, "c")

def build(path="output/Gym_ADP_Tek_Hat_Semasi.pdf"):
    c = canvas.Canvas(path, pagesize=(W, HH))
    c.setTitle(f"{PANO_ADI} — Tek Hat / Açılım Şeması ({P.REV})")
    for fn in (s1, s2, s3, s4):
        fn(c); c.showPage()
    for i in range(SEMA_SAYFA):
        dilim = AKIS[i*SUTUN:(i+1)*SUTUN]
        sema_sayfasi(c, 5+i, dilim, i == 0, i == SEMA_SAYFA-1)
        c.showPage()
    c.save()
    print(f"→ {path}  ·  {N} pafta  ·  {len(P.LINYE)} linye + {len(YEDEK)} yedek "
          f"· {len(RCD_GRUP)} kaçak akım grubu")

if __name__ == "__main__":
    build()
