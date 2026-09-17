# -*- coding: utf-8 -*-
"""IEC 60617 ŞEMA SEMBOLLERİ — tek hat / açılım şeması çizimi için.

Tüm sembollerin ankraj noktası, akımın GİRDİĞİ üst terminaldir; sembol aşağı
doğru çizilir ve `yukseklik` kadar yer kaplar. Ölçüler milimetredir (ReportLab
`mm` ile çarpılmış page unit).

Referans: işverenin UDP/ADP pano şeması seti (IEC 61439-1&2 tip test,
IEC 60617 sembolleri, TR/EN çift dilli sembol listesi).
"""
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
import helpers as h

INK   = HexColor("#111111")
TEL   = HexColor("#1C1C1C")      # iletken
NOTR  = HexColor("#2F6FB3")      # nötr
TOPRAK= HexColor("#2E7D5B")      # koruma iletkeni
ETIKET= HexColor("#16273D")
KIRMIZI = HexColor("#C8322B")
GREY  = HexColor("#8A8F98")

LW_TEL   = 0.5
LW_SEMBOL= 0.7
LW_BARA  = 1.6

def tel(c, p1, p2, col=TEL, lw=LW_TEL, dash=None):
    c.saveState(); c.setStrokeColor(col); c.setLineWidth(lw)
    if dash: c.setDash(dash)
    c.line(p1[0], p1[1], p2[0], p2[1]); c.restoreState()

def dugum(c, p, r=0.65*mm, col=TEL):
    c.saveState(); c.setFillColor(col); c.circle(p[0], p[1], r, 0, 1); c.restoreState()

def etiket(c, x, y, satirlar, hiza="l", fs=5.0, col=ETIKET, bold_ilk=True, lead=2.6):
    for i, s in enumerate(satirlar):
        h.txt(c, x, y-i*lead*mm, s, h.FB if (i == 0 and bold_ilk) else h.F, fs, col, hiza)

# ══ TEMEL SEMBOLLER ═══════════════════════════════════════════════════════════
def mcb(c, x, y, kutup=1, etiketler=None, hgt=14*mm):
    """Otomatik sigorta (MCB) — IEC 60617: açılabilir kontak + termik-manyetik
    açtırma elemanı. kutup: 1 veya 3."""
    ara = 3.2*mm
    x0 = x - (kutup-1)*ara/2
    for k in range(kutup):
        xx = x0 + k*ara
        tel(c, (xx, y), (xx, y-3.2*mm))
        # açılabilir kontak: eğik kol
        c.saveState(); c.setStrokeColor(TEL); c.setLineWidth(LW_SEMBOL)
        c.line(xx, y-3.2*mm, xx+2.6*mm, y-8.0*mm)
        c.restoreState()
        dugum(c, (xx, y-3.2*mm), 0.55*mm)
        tel(c, (xx, y-8.6*mm), (xx, y-hgt))
        dugum(c, (xx, y-8.6*mm), 0.55*mm)
        # termik açtırma (kutu) + manyetik (yarım daire)
        c.saveState(); c.setStrokeColor(TEL); c.setLineWidth(0.55)
        c.rect(xx+1.2*mm, y-7.2*mm, 1.9*mm, 1.6*mm, 0, 0)
        c.arc(xx+1.1*mm, y-5.2*mm, xx+3.3*mm, y-3.0*mm, 200, 140)
        c.restoreState()
    if etiketler: etiket(c, x0-3.0*mm, y-3.6*mm, etiketler, "r", 4.6)
    return y-hgt

def rcd(c, x, y, kutup=2, etiketler=None, hgt=15*mm):
    """Kaçak akım koruma rölesi (RCCB) — toroid + açılabilir kontaklar."""
    ara = 3.2*mm
    x0 = x - (kutup-1)*ara/2
    for k in range(kutup):
        xx = x0 + k*ara
        tel(c, (xx, y), (xx, y-3.4*mm))
        c.saveState(); c.setStrokeColor(TEL); c.setLineWidth(LW_SEMBOL)
        c.line(xx, y-3.4*mm, xx+2.4*mm, y-7.8*mm); c.restoreState()
        dugum(c, (xx, y-3.4*mm), 0.55*mm)
        tel(c, (xx, y-8.4*mm), (xx, y-hgt))
        dugum(c, (xx, y-8.4*mm), 0.55*mm)
    # toroid: tüm kutupları saran elips
    c.saveState(); c.setStrokeColor(TEL); c.setLineWidth(0.6)
    w = (kutup-1)*ara + 5.0*mm
    c.ellipse(x0-2.6*mm, y-12.6*mm, x0-2.6*mm+w, y-9.2*mm, 0, 0)
    c.restoreState()
    h.txt(c, x0-2.6*mm+w/2, y-11.6*mm, "I∆", h.FB, 4.2, TEL, "c")
    if etiketler: etiket(c, x0-3.4*mm, y-3.8*mm, etiketler, "r", 4.6)
    return y-hgt

def tmsalter(c, x, y, etiketler=None, hgt=16*mm):
    """Termik-manyetik şalter (TMŞ / MCCB) — kutulu 3 kutuplu kesici."""
    ara = 3.4*mm; x0 = x - ara
    c.saveState(); c.setStrokeColor(TEL); c.setLineWidth(0.7)
    c.rect(x0-2.4*mm, y-11.5*mm, 2*ara+4.8*mm, 8.0*mm, 0, 0); c.restoreState()
    for k in range(3):
        xx = x0 + k*ara
        tel(c, (xx, y), (xx, y-3.5*mm))
        c.saveState(); c.setStrokeColor(TEL); c.setLineWidth(LW_SEMBOL)
        c.line(xx, y-4.0*mm, xx+2.2*mm, y-8.0*mm); c.restoreState()
        dugum(c, (xx, y-4.0*mm), 0.55*mm); dugum(c, (xx, y-8.4*mm), 0.55*mm)
        tel(c, (xx, y-8.4*mm), (xx, y-hgt))
    if etiketler: etiket(c, x0-3.6*mm, y-3.8*mm, etiketler, "r", 4.6)
    return y-hgt

def kontaktor(c, x, y, kutup=3, etiketler=None, hgt=14*mm):
    """Kontaktör — açılabilir kontak + bobin kutusu."""
    ara = 3.2*mm; x0 = x - (kutup-1)*ara/2
    for k in range(kutup):
        xx = x0 + k*ara
        tel(c, (xx, y), (xx, y-3.2*mm))
        c.saveState(); c.setStrokeColor(TEL); c.setLineWidth(LW_SEMBOL)
        c.line(xx, y-3.2*mm, xx+2.4*mm, y-7.6*mm)
        c.arc(xx+1.4*mm, y-8.6*mm, xx+3.4*mm, y-6.6*mm, 0, 180)
        c.restoreState()
        dugum(c, (xx, y-3.2*mm), 0.55*mm); dugum(c, (xx, y-8.2*mm), 0.55*mm)
        tel(c, (xx, y-8.2*mm), (xx, y-hgt))
    if etiketler: etiket(c, x0-3.2*mm, y-3.6*mm, etiketler, "r", 4.6)
    return y-hgt

def sinyal_lamba(c, x, y, renk="KIRMIZI", kod="-H1", hgt=11*mm):
    """Sinyal lambası — çarpı içeren daire."""
    tel(c, (x, y), (x, y-3.4*mm))
    r = 1.9*mm; cy = y-5.3*mm
    c.saveState(); c.setStrokeColor(TEL); c.setLineWidth(LW_SEMBOL)
    c.circle(x, cy, r, 0, 0)
    d = r*0.707
    c.line(x-d, cy-d, x+d, cy+d); c.line(x-d, cy+d, x+d, cy-d)
    c.restoreState()
    tel(c, (x, y-7.2*mm), (x, y-hgt))
    etiket(c, x+3.0*mm, y-4.0*mm, [kod, renk], "l", 4.4)
    return y-hgt

def klemens(c, x, y, no="1", hgt=5.0*mm):
    """Klemens (terminal) — içi boş daire + numara."""
    c.saveState(); c.setStrokeColor(TEL); c.setLineWidth(0.6)
    c.setFillColor(HexColor("#FFFFFF")); c.circle(x, y-2.3*mm, 1.5*mm, 1, 1)
    c.restoreState()
    h.txt(c, x, y-3.0*mm, str(no), h.F, 3.8, TEL, "c")
    tel(c, (x, y), (x, y-0.8*mm)); tel(c, (x, y-3.8*mm), (x, y-hgt))
    return y-hgt

def parafudr(c, x, y, etiketler=None, hgt=13*mm):
    """Parafudr (SPD) — kutu içinde ok."""
    tel(c, (x, y), (x, y-3.0*mm))
    c.saveState(); c.setStrokeColor(TEL); c.setLineWidth(0.7)
    c.rect(x-2.0*mm, y-9.0*mm, 4.0*mm, 6.0*mm, 0, 0)
    p = c.beginPath(); p.moveTo(x, y-4.0*mm); p.lineTo(x, y-8.0*mm)
    c.drawPath(p, 1, 0)
    p = c.beginPath(); p.moveTo(x-1.1*mm, y-6.4*mm); p.lineTo(x, y-8.0*mm)
    p.lineTo(x+1.1*mm, y-6.4*mm); p.close()
    c.setFillColor(TEL); c.drawPath(p, 0, 1); c.restoreState()
    tel(c, (x, y-9.0*mm), (x, y-hgt))
    if etiketler: etiket(c, x+3.2*mm, y-4.0*mm, etiketler, "l", 4.4)
    return y-hgt

def guc_kaynagi(c, x, y, etiketler=None, hgt=14*mm):
    """230 VAC / 24 VDC güç kaynağı."""
    tel(c, (x, y), (x, y-3.0*mm))
    c.saveState(); c.setStrokeColor(TEL); c.setLineWidth(0.7)
    c.rect(x-4.5*mm, y-10.0*mm, 9.0*mm, 7.0*mm, 0, 0)
    c.line(x, y-3.0*mm, x, y-10.0*mm); c.restoreState()
    h.txt(c, x-2.2*mm, y-7.2*mm, "∼", h.FB, 6, TEL, "c")
    h.txt(c, x+2.2*mm, y-7.0*mm, "=", h.FB, 5.5, TEL, "c")
    tel(c, (x, y-10.0*mm), (x, y-hgt))
    if etiketler: etiket(c, x+5.6*mm, y-4.2*mm, etiketler, "l", 4.4)
    return y-hgt

def secici(c, x, y, etiketler=None, hgt=12*mm):
    """1-0-2 seçici (pako) anahtar."""
    tel(c, (x, y), (x, y-3.2*mm))
    c.saveState(); c.setStrokeColor(TEL); c.setLineWidth(LW_SEMBOL)
    c.line(x, y-3.2*mm, x+2.4*mm, y-7.4*mm)
    c.setDash(1, 1); c.setLineWidth(0.4)
    c.line(x+2.4*mm, y-7.4*mm, x+2.4*mm, y-3.6*mm); c.restoreState()
    dugum(c, (x, y-3.2*mm), 0.55*mm); dugum(c, (x, y-7.8*mm), 0.55*mm)
    tel(c, (x, y-7.8*mm), (x, y-hgt))
    if etiketler: etiket(c, x-3.2*mm, y-3.6*mm, etiketler, "r", 4.4)
    return y-hgt

def toprak(c, x, y, boy=4.0*mm):
    """Koruma iletkeni sembolü."""
    tel(c, (x, y), (x, y-boy), TOPRAK)
    c.saveState(); c.setStrokeColor(TOPRAK); c.setLineWidth(0.8)
    for i, w in enumerate((2.4*mm, 1.6*mm, 0.8*mm)):
        yy = y-boy-i*0.9*mm
        c.line(x-w/2, yy, x+w/2, yy)
    c.restoreState()

def motor(c, x, y, tip="3~", hgt=12*mm):
    tel(c, (x, y), (x, y-3.0*mm))
    c.saveState(); c.setStrokeColor(TEL); c.setLineWidth(LW_SEMBOL)
    c.circle(x, y-6.4*mm, 3.4*mm, 0, 0); c.restoreState()
    h.txt(c, x, y-5.6*mm, "M", h.FB, 5.4, TEL, "c")
    h.txt(c, x, y-8.4*mm, tip, h.F, 3.8, TEL, "c")
    return y-hgt

def armatur_sembol(c, x, y, hgt=10*mm):
    tel(c, (x, y), (x, y-3.0*mm))
    c.saveState(); c.setStrokeColor(TEL); c.setLineWidth(LW_SEMBOL)
    c.circle(x, y-5.4*mm, 2.2*mm, 0, 0)
    d = 2.2*mm*0.707
    c.line(x-d, y-5.4*mm-d, x+d, y-5.4*mm+d)
    c.line(x-d, y-5.4*mm+d, x+d, y-5.4*mm-d); c.restoreState()
    return y-hgt

def priz_sembol(c, x, y, hgt=10*mm):
    tel(c, (x, y), (x, y-4.4*mm))
    c.saveState(); c.setStrokeColor(TEL); c.setLineWidth(LW_SEMBOL)
    c.arc(x-2.6*mm, y-7.0*mm, x+2.6*mm, y-1.8*mm, 180, 180)
    c.line(x-2.6*mm, y-4.4*mm, x+2.6*mm, y-4.4*mm)
    c.line(x, y-4.4*mm, x, y-6.4*mm); c.restoreState()
    return y-hgt

# ══ POTANSİYEL RAYLARI ════════════════════════════════════════════════════════
RAY = [("L1", TEL), ("L2", TEL), ("L3", TEL), ("N", NOTR), ("PE", TOPRAK)]

def potansiyel_raylari(c, x0, x1, y0, ara=4.2*mm, sol_ref=None, sag_ref=None):
    """Yatay potansiyel rayları + sayfa geçiş referansları. Döner: {ad: y}"""
    ys = {}
    for i, (ad, col) in enumerate(RAY):
        y = y0 - i*ara
        tel(c, (x0, y), (x1, y), col, LW_BARA)
        h.txt(c, x0-2.0*mm, y-1.0*mm, ad, h.FB, 5.0, col, "r")
        h.txt(c, x1+2.0*mm, y-1.0*mm, ad, h.FB, 5.0, col, "l")
        if i == 0:
            if sol_ref: h.txt(c, x0-2.0*mm, y+3.2*mm, f"◄ {sol_ref}", h.F, 4.2, GREY, "r")
            if sag_ref: h.txt(c, x1+2.0*mm, y+3.2*mm, f"{sag_ref} ►", h.F, 4.2, GREY, "l")
        ys[ad] = y
    return ys

def raydan_in(c, ray_y, x, y_alt, ad="L1"):
    """Potansiyel rayından aşağı iniş — bağlantı noktası işaretli."""
    col = dict(RAY)[ad]
    tel(c, (x, ray_y), (x, y_alt), col)
    dugum(c, (x, ray_y), 0.7*mm, col)

def tel_no(c, x, y, no, dx=1.4*mm):
    """Tel numarası — iletkenin yanında küçük rakam."""
    h.txt(c, x+dx, y, str(no), h.F, 3.6, GREY, "l")
