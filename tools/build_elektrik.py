# -*- coding: utf-8 -*-
"""ELEKTRİK PROJESİ — A3 yatay, 6 pafta."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
import proj as P, helpers as h, draw as D, draw_mep as M

W, HH = 420*mm, 297*mm
TOP, BOT, L, R = HH-24.6*mm, 14*mm, 12*mm, W-12*mm
CW = R-L
N = 7
DISIPLIN = "ELEKTRİK PROJESİ"

def sayfa(c, no, baslik, ust=None):
    h.band(c, W, HH, no, baslik, ust or DISIPLIN); h.footer(c, W, no, N)

def _linye(pre):
    return [l for l in P.LINYE if l[0].startswith(pre)]

# ══ 1 · KAPAK / SİSTEM ÖZETİ ═══════════════════════════════════════════════════
def s1(c):
    sayfa(c, 1, "Elektrik projesi", "Sistem özeti · yük hesabı · genel notlar")
    y = TOP
    y = h.para(c, L, y-2*mm,
      "Bu dosya, Maltepe / İdealtepe'deki mobilya mağazasının fonksiyonel antrenman stüdyosuna "
      "dönüşümü için elektrik ön projesidir. Kapsam beş sistemdir: ana dağıtım panosu, aydınlatma "
      "(acil aydınlatma dâhil), priz ve kuvvet, zayıf akım (veri, CCTV, ses, geçiş kontrol, yangın "
      f"algılama) ve topraklama. Toplam bağlı güç {h.tl(P.BAGLI_KW,2)} kW, eşzamanlılık katsayıları "
      f"uygulanmış talep gücü {h.tl(P.TALEP_KW,2)} kW; önerilen abonelik {P.ABONELIK}. "
      "Üç faz arasındaki yük dengesizliği %"
      f"{h.tl(P.FAZ_DENGE,1)}'dir.", CW, h.F, 8.2, h.INK, 11.4)
    kw = (CW-3*6*mm)/4; ky = y-8*mm-50*mm
    for i, (no, bs, gv) in enumerate([
      ("E1", "ANA DAĞITIM",
       f"Sıva üstü metal pano, 36 modül. 3×{P.ANA_KESICI//3} A ana kesici, iki ayrı 30 mA kaçak akım "
       "rölesi (biri yalnız ıslak hacim linyeleri için), Tip 2 parafudr. Sayaçtan panoya 5×10 mm² "
       "NYY kolon hattı."),
      ("E2", "AYDINLATMA",
       f"{P.ARMATUR_ADET} lineer LED (40 W) + {P.DOWNLIGHT_ADET} IP44 downlight (18 W) + "
       "5 acil aydınlatma + 3 yönlendirme armatürü. Bölge bazlı anahtarlama; ıslak hacim ve geçişte "
       "hareket sensörü."),
      ("E3", "PRİZ VE KUVVET",
       f"{len(P.PRIZ)} ikili topraklı priz + {len(P.PRIZ_IP44)} IP44 priz. Kardiyo ekipmanı ayrı "
       "linyede; klima ve su ısıtıcıları hat sonu kesicili bağımsız linyelerde."),
      ("E4", "ZAYIF AKIM",
       f"{len(P.KAMERA)} IP kamera (soyunma ve WC hariç), {len(P.HOPARLOR)} tavan hoparlörü, "
       f"{len(P.DEDEKTOR)} duman dedektörü + 2 zonlu yangın paneli, geçiş kontrol, Cat6 veri "
       "altyapısı ve 2 erişim noktası.")]):
        h.kart(c, L+i*(kw+6*mm), ky, kw, 50*mm, no, bs, gv)
    kw2 = (CW-5*5*mm)/6; ky2 = ky-8*mm-30*mm
    for i, (u, dv, al) in enumerate([
      ("BAĞLI GÜÇ", f"{h.tl(P.BAGLI_KW,2)} kW", f"{len(P.LINYE)} linye"),
      ("TALEP GÜCÜ", f"{h.tl(P.TALEP_KW,2)} kW", "eşzamanlılık katsayıları uygulanmış"),
      ("ABONELİK", f"3×{P.ANA_KESICI//3} A", f"faz başına {h.tl(max(P.AKIM_FAZ.values()),1)} A"),
      ("FAZ DENGESİZLİĞİ", f"%{h.tl(P.FAZ_DENGE,1)}", "hedef ≤ %15"),
      ("ARMATÜR", f"{P.ARMATUR_ADET} + {P.DOWNLIGHT_ADET}", "lineer LED + IP44 downlight"),
      ("KAÇAK AKIM", "2 × 30 mA", "ıslak hacim ayrı röle")]):
        h.kpi(c, L+i*(kw2+5*mm), ky2, kw2, 30*mm, u, dv, al, h.COPPER if i < 3 else h.NAVY2)
    h.txt(c, L, ky2-9*mm, "GENEL NOTLAR", h.FB, 8.5, h.NAVY)
    cy = h.madde_listesi(c, L, ky2-15*mm, CW*0.49, [
      "Tüm tesisat sıva altı spiral boru içinde, NHXMH (halojensiz) kablo ile yapılacaktır.",
      "Islak hacim linyeleri (L5, P5) ayrı bir 30 mA kaçak akım rölesinden beslenecek; böylece "
      "bir arıza tüm tesisi karartmayacaktır.",
      "Her klima iç ünitesi ve her su ısıtıcısı hat sonu kesicili bağımsız linyeden beslenecektir.",
      "Kardiyo ekipmanı (koşu bandı, bisiklet) ayrı linyeye alınmıştır — motor yol alma akımı "
      "diğer prizleri etkilemez.",
      "Acil aydınlatma armatürleri 3 saat bataryalı, kendinden testli tip olacaktır.",
    ], fs=6.6, lead=8.8)
    h.madde_listesi(c, L+CW*0.51, ky2-15*mm, CW*0.49, [
      "SOYUNMA ODALARINA VE WC'LERE KAMERA KONULMAYACAKTIR — kişisel verilerin korunması "
      "mevzuatı ve yönetmelik açısından zorunludur. Kamera yalnızca salon, giriş ve koridorda.",
      "Yangın algılama paneli kesintisiz beslenecek, aküleri 24 saat yedekleme sağlayacaktır.",
      "Topraklama direnci ≤ 10 Ω olacak; ölçüm raporu itfaiye ve GSİM dosyasına eklenecektir.",
      "Islak hacimlerde ek potansiyel dengeleme yapılacak, tüm metal aksam barada birleştirilecektir.",
      "Pano üzerinde tek hat şeması ve linye etiketleri kalıcı olarak bulunacaktır.",
    ], fs=6.6, lead=8.8)
    h.notkutu(c, L, cy-6*mm, CW, "Doğrulanacak girdiler",
      "Mevcut pano gücü ve trifaze abonelik durumu BİLİNMİYOR. Hesaplanan talep gücü "
      f"{h.tl(P.TALEP_KW,2)} kW'tır ve {P.ABONELIK} gerektirir. Mevcut abonelik yetersizse dağıtım "
      "şirketine güç artırım başvurusu yapılacak — bu başvuru 3–8 hafta sürebilir ve takvimin "
      "kritik yoluna girer. Sıcak su çözümü boylere çevrilirse talep gücü yaklaşık 5 kW düşer ve "
      "3×25 A abonelik yeterli olur (mekanik proje sayfa 4).", fs=6.6, acc=h.RED)
    h.txt(c, L, BOT+54*mm, "SİSTEM KAPSAM TABLOSU", h.FB, 8.5, h.NAVY)
    krow = [["Ana dağıtım", f"1 pano · 3×{P.ANA_KESICI//3} A · 2 × 30 mA kaçak akım · Tip 2 parafudr",
             f"{len(_linye(''))} linye"],
            ["Aydınlatma", f"{P.ARMATUR_ADET} lineer + {P.DOWNLIGHT_ADET} downlight + 8 acil/yönlendirme",
             f"{len(_linye('L'))} linye"],
            ["Priz ve kuvvet", f"{len(P.PRIZ)} priz + {len(P.PRIZ_IP44)} IP44 + {len(P.KLIMA)} klima + 2 ısıtıcı + 3 fan",
             f"{sum(1 for l in P.LINYE if l[0][0] in 'PKWV')} linye"],
            ["Zayıf akım", f"{len(P.KAMERA)} kamera · {len(P.HOPARLOR)} hoparlör · {len(P.DEDEKTOR)} dedektör · veri · geçiş kontrol",
             f"{len(_linye('Z'))} linye"],
            ["Topraklama", "TN-S · ana potansiyel dengeleme · 2 ıslak hacim ek dengeleme", "≤ 10 Ω"]]
    h.tablo(c, L, BOT+48*mm, [("Sistem", 0.16), ("Kapsam", 0.68), ("Ölçek", 0.16)],
            krow, CW, satir_h=6.6*mm, fs=6.4, hizala=["l", "l", "c"])

# ══ 2 · AYDINLATMA PLANI ═══════════════════════════════════════════════════════
def s2(c):
    sayfa(c, 2, "Aydınlatma planı", "Armatür yerleşimi · lux hesabı · anahtarlama")
    pw = CW*0.585
    v = D.View(c, L, BOT+8*mm, pw, TOP-BOT-10*mm)
    M.altlik(v); M.ekipman_soluk(v)
    for px, py in D.aydinlatma_izgara(): M.sembol(v, px, py, "armatur")
    for ad, d in P.ISLAK.items():
        for n in ("soyunma", "dus", "wc"):
            q = d[n].representative_point(); M.sembol(v, q.x, q.y, "downlight")
    for kod, x, y, t, a in P.ACIL:
        M.sembol(v, x, y, "acil", "E" if "acil" in t else "→", a)
    for kod, x, y, t, a in P.ANAHTAR: M.sembol(v, x, y, "anahtar", kod, a)
    for kod, x, y, t, a in P.SENSOR:  M.sembol(v, x, y, "sensor")
    M.sembol(v, *P.PANO, "pano", None, P.PANO_ACI)
    D.kuzey_ok(v, L+pw-13*mm, TOP-13*mm); D.olcek_cubugu(v, L+5*mm, BOT+11*mm)
    h.lejant(c, L+5*mm, BOT+2*mm, [(HexColor("#FFF3C4"), "Lineer LED 40 W"),
        (HexColor("#E8F5EC"), "Acil / yönlendirme"), (M.C_AYD, "Anahtar · sensör")], 6.0)
    x2 = L+pw+7*mm; w2 = CW-pw-7*mm; yy = TOP
    h.txt(c, x2, yy-4*mm, "LUX HESABI", h.FB, 8, h.NAVY)
    rows = [[a[0], f"{a[1]:.2f}".replace(".", ","), str(a[2]), h.tl(a[3]),
             "Lineer 40 W" if a[5] == "lineer" else "IP44 18 W", str(a[4])] for a in P.AYDINLATMA]
    rows.append(["TOPLAM", "", "", "", f"{P.ARMATUR_ADET} + {P.DOWNLIGHT_ADET}",
                 str(P.ARMATUR_ADET+P.DOWNLIGHT_ADET)])
    yy = h.tablo(c, x2, yy-7*mm, [("Bölge", 0.30), ("m²", 0.11), ("Lux", 0.09),
                                  ("Gerekli lm", 0.16), ("Armatür tipi", 0.19), ("Adet", 0.15)],
                 rows, w2, satir_h=5.8*mm, fs=6.2, hizala=["l", "r", "r", "r", "l", "r"])
    h.txt(c, x2, yy-6*mm, "Bakım faktörü 0,80 · mekân verimi 0,70 · lineer armatür 4.400 lm · "
          "downlight 1.800 lm", h.F, 5.8, h.GREY)
    h.txt(c, x2, yy-13*mm, "AYDINLATMA LİNYELERİ", h.FB, 8, h.NAVY)
    rows2 = [[l[0], l[1], l[2], l[3], l[4], f"{l[5]:.3f}".replace(".", ",")] for l in _linye("L")]
    yy = h.tablo(c, x2, yy-17*mm, [("Linye", 0.10), ("Tanım", 0.40), ("Koruma", 0.13),
                                   ("Kesit", 0.11), ("Faz", 0.09), ("kW", 0.17)],
                 rows2, w2, satir_h=5.8*mm, fs=6.2, hizala=["c", "l", "c", "c", "c", "r"])
    h.txt(c, x2, yy-8*mm, "ANAHTARLAMA VE KUMANDA", h.FB, 8, h.NAVY)
    rows3 = [[k[0], k[3]] for k in P.ANAHTAR] + [[s[0], s[3]] for s in P.SENSOR]
    yy = h.tablo(c, x2, yy-12*mm, [("Kod", 0.14), ("İşlev", 0.86)], rows3,
                 w2, satir_h=5.6*mm, fs=6.2, hizala=["c", "l"])
    h.notkutu(c, x2, yy-6*mm, w2, "Acil aydınlatma",
      "5 acil aydınlatma + 3 çıkış yönlendirme armatürü, kaçış yolu boyunca ve her iki çıkış "
      "üzerinde konumlandırılmıştır. Armatürler 3 saat bataryalı ve kendinden testli tiptir; "
      "test kayıtları itfaiye denetiminde istenebilir.", fs=6.3, acc=h.NAVY2)

# ══ 3 · PRİZ VE KUVVET PLANI ═══════════════════════════════════════════════════
def s3(c):
    sayfa(c, 3, "Priz ve kuvvet planı", "Priz yerleşimi · klima ve ısıtıcı beslemeleri · linyeler")
    pw = CW*0.585
    v = D.View(c, L, BOT+8*mm, pw, TOP-BOT-10*mm)
    M.altlik(v); M.ekipman_soluk(v)
    for kod, x, y, t, a in P.PRIZ:      M.sembol(v, x, y, "priz", kod, a)
    for kod, x, y, t, a in P.PRIZ_IP44: M.sembol(v, x, y, "priz_ip44", kod, a)
    for kod, zon, btu, (x, y), a in P.KLIMA:
        M.cihaz(v, x, y, kod, M.C_KLIMA, 7.5*mm, 4.2*mm, a)
    for kod, x, y, ad, a in P.ISITICI:
        M.cihaz(v, x, y, kod, M.C_SICAK, 7.5*mm, 4.2*mm, a)
    for kod, x, y, ad, a in P.FAN:
        M.cihaz(v, x, y, kod, M.C_BESLEME if "TH" in kod else
                (M.C_ISLAK if "IS" in kod else M.C_EGZOZ), 7.5*mm, 4.2*mm, a)
    M.sembol(v, *P.PANO, "pano", None, P.PANO_ACI)
    D.kuzey_ok(v, L+pw-13*mm, TOP-13*mm); D.olcek_cubugu(v, L+5*mm, BOT+11*mm)
    h.lejant(c, L+5*mm, BOT+2*mm, [(M.C_PRIZ, "İkili topraklı priz"), (M.C_SICAK, "Su ısıtıcı"),
                                   (M.C_KLIMA, "Klima iç ünite"), (M.C_BESLEME, "Fan")], 6.0)
    x2 = L+pw+7*mm; w2 = CW-pw-7*mm; yy = TOP
    h.txt(c, x2, yy-4*mm, "PRİZ VE KUVVET LİNYELERİ", h.FB, 8, h.NAVY)
    rows = [[l[0], l[1], l[2], l[3], l[4], f"{l[5]:.2f}".replace(".", ","),
             f"{l[6]:.2f}".replace(".", ","), f"{l[7]:.2f}".replace(".", ",")]
            for l in P.LINYE if l[0][0] in "PKWV"]
    yy = h.tablo(c, x2, yy-7*mm, [("Linye", 0.09), ("Tanım", 0.33), ("Koruma", 0.11),
                                  ("Kesit", 0.10), ("Faz", 0.08), ("Bağlı kW", 0.10),
                                  ("Eşz.", 0.08), ("Talep kW", 0.11)],
                 rows, w2, satir_h=5.8*mm, fs=6.0, hfs=5.8,
                 hizala=["c", "l", "c", "c", "c", "r", "r", "r"])
    h.txt(c, x2, yy-8*mm, "PRİZ DAĞILIMI", h.FB, 8, h.NAVY)
    rows2 = [["Çeper prizleri (salon)", f"{len(P.PRIZ)-4} adet", "≈3 m aralık, 40 cm kot"],
             ["Banko kuvvet + veri kutusu", "1 adet", "gömme, POS ve rack besleme"],
             ["Kardiyo ekipman prizi", "3 adet", "ayrı linye — P4"],
             ["Islak hacim IP44 prizi", f"{len(P.PRIZ_IP44)} adet", "ayrı kaçak akım — P5"],
             ["Klima besleme", f"{len(P.KLIMA)} adet", "hat sonu kesicili"],
             ["Su ısıtıcı besleme", "2 adet", "3×4 mm² · 32 A"],
             ["Fan besleme ve hız kontrol", "3 adet", "havalandırma"]]
    yy = h.tablo(c, x2, yy-12*mm, [("Kalem", 0.42), ("Adet", 0.18), ("Not", 0.40)],
                 rows2, w2, satir_h=5.8*mm, fs=6.2, hizala=["l", "c", "l"])
    h.txt(c, x2, yy-8*mm, "KABLO METRAJI", h.FB, 8, h.NAVY)
    rows3 = [["Aydınlatma linyesi NHXMH 3×1,5", f"{h.tl(P.L_LINYE15,0)} m"],
             ["Priz / kuvvet linyesi NHXMH 3×2,5", f"{h.tl(P.L_LINYE25,0)} m"],
             ["Su ısıtıcı hattı NHXMH 3×4", "2 × ≈14 m"],
             ["Kolon hattı NYY 5×10", "22 m"],
             ["Zayıf akım kablolaması", f"{h.tl(P.L_ZAYIF,0)} m"]]
    yy = h.tablo(c, x2, yy-12*mm, [("Kablo", 0.66), ("Miktar", 0.34)], rows3,
                 w2, satir_h=5.8*mm, fs=6.2, hizala=["l", "r"])
    h.notkutu(c, x2, yy-6*mm, w2, "Kardiyo prizleri neden ayrı",
      "Koşu bandı ve benzeri motorlu ekipman yol alırken yüksek anlık akım çeker. Aynı linyede "
      "bulunan hassas cihazlar (POS, ses sistemi, kamera kaydedici) bundan etkilenir. Bu nedenle "
      "kardiyo ekipmanı P4 linyesine ayrılmıştır.", fs=6.3, acc=h.NAVY2)

# ══ 4 · ZAYIF AKIM PLANI ═══════════════════════════════════════════════════════
def s4(c):
    sayfa(c, 4, "Zayıf akım planı", "Veri · CCTV · ses · geçiş kontrol · yangın algılama")
    pw = CW*0.585
    v = D.View(c, L, BOT+8*mm, pw, TOP-BOT-10*mm)
    M.altlik(v); M.ekipman_soluk(v)
    for kod, x, y, t in P.HOPARLOR: M.sembol(v, x, y, "hoparlor", kod)
    for kod, x, y, t, a in P.KAMERA: M.sembol(v, x, y, "kamera", kod, a)
    for kod, x, y, t in P.VERI:     M.sembol(v, x, y, "veri", kod)
    for kod, x, y, t in P.DEDEKTOR: M.sembol(v, x, y, "dedektor", kod)
    for kod, x, y, t, a in P.YANGIN:   M.sembol(v, x, y, "yangin", kod, a)
    # yangın algılama çevrimi: panodan başlayıp dedektörleri dolaşan tek hat
    _loop = [P.PANO] + [(d[1], d[2]) for d in P.DEDEKTOR] + [(P.YANGIN[2][1], P.YANGIN[2][2])]
    for i in range(len(_loop)-1):
        D.line(v, _loop[i], _loop[i+1], h.tint(M.C_YANGIN, 0.55), 0.6, (2.2, 1.6))
    M.sembol(v, *P.PANO, "pano", None, P.PANO_ACI)
    # soyunma bloklarına "kamera yok" notu
    for ad, d in P.ISLAK.items():
        q = d["tum"].representative_point()
        D.etiket(v, (q.x, q.y), "KAMERA YOK", 4.6, h.RED, h.FB, "c", dy=-6)
    D.kuzey_ok(v, L+pw-13*mm, TOP-13*mm); D.olcek_cubugu(v, L+5*mm, BOT+11*mm)
    h.lejant(c, L+5*mm, BOT+2*mm, [(M.C_ZAYIF, "Kamera · hoparlör · veri"),
                                   (M.C_YANGIN, "Duman dedektörü · buton")], 6.0)
    x2 = L+pw+7*mm; w2 = CW-pw-7*mm; yy = TOP
    h.txt(c, x2, yy-4*mm, "ZAYIF AKIM SİSTEMLERİ", h.FB, 8, h.NAVY)
    rows = [["Veri", f"{len(P.VERI)-2} priz + {2} erişim noktası", "Cat6 · PoE · rack 9U"],
            ["CCTV", f"{len(P.KAMERA)} IP kamera", "NVR + 4 TB · soyunma ve WC hariç"],
            ["Ses", f"{len(P.HOPARLOR)} tavan hoparlörü", "100 V hat · 120 W anfi"],
            ["Geçiş kontrol", "1 kapı", "okuyucu + elektrikli kilit + çıkış butonu"],
            ["Yangın algılama", f"{len(P.DEDEKTOR)} dedektör + 3 buton/siren", "2 zonlu panel, akülü"]]
    yy = h.tablo(c, x2, yy-7*mm, [("Sistem", 0.22), ("Kapsam", 0.36), ("Not", 0.42)],
                 rows, w2, satir_h=6.4*mm, fs=6.3, hizala=["l", "l", "l"])
    h.txt(c, x2, yy-8*mm, "CİHAZ LİSTESİ", h.FB, 8, h.NAVY)
    rows2 = [[k[0], k[3]] for k in P.KAMERA] + [[d[0], d[3]] for d in P.DEDEKTOR] + \
            [[y_[0], y_[3]] for y_ in P.YANGIN] + [[d[0], d[3]] for d in P.VERI]
    yy = h.tablo(c, x2, yy-12*mm, [("Kod", 0.13), ("Konum / işlev", 0.87)], rows2,
                 w2, satir_h=5.4*mm, fs=6.1, hizala=["c", "l"])
    h.notkutu(c, x2, yy-6*mm, w2, "Kamera yerleşiminde yasal sınır",
      "Soyunma odalarına, duşlara ve tuvaletlere kamera konulamaz. Bu yalnızca etik değil, "
      "kişisel verilerin korunması mevzuatı açısından da açık bir yasaktır ve denetimde tespit "
      "edilmesi işletmeyi doğrudan yaptırıma açar. Kameralar salon, giriş ve soyunma koridoru "
      "girişiyle sınırlandırılmıştır; soyunma bloklarının içi kapsam dışıdır.", fs=6.3, acc=h.RED)

# ══ 5 · PANO TEK HAT ŞEMASI ════════════════════════════════════════════════════
def s5(c):
    sayfa(c, 5, "Pano tek hat şeması", "Ana dağıtım · linyeler · faz dengesi")
    yy = TOP
    sw = CW*0.63
    h.kutu(c, L, BOT+2*mm, sw, yy-BOT-4*mm, HexColor("#FBFCFD"), h.GREY_L)
    bx = L+8*mm; by = yy-10*mm
    # — besleme zinciri
    def kut(x, y, w, hh, t1, t2, col=h.NAVY2):
        c.setFillColor(col); c.setStrokeColor(HexColor("#FFFFFF")); c.setLineWidth(0.7)
        c.roundRect(x, y, w, hh, 1.0*mm, 1, 1)
        h.txt(c, x+w/2, y+hh/2+0.3*mm, t1, h.FB, 5.4, HexColor("#FFFFFF"), "c")
        if t2: h.txt(c, x+w/2, y+hh/2-3.8*mm, t2, h.F, 4.6, HexColor("#C9D6E4"), "c")
    zincir = [("SAYAÇ", "dağıtım şirketi"), (f"NYY 5×10 mm²", "22 m kolon"),
              (f"ANA KESİCİ 3×{P.ANA_KESICI//3} A", "C eğrisi"), ("PARAFUDR", "Tip 2")]
    xw = 44*mm
    for i, (t1, t2) in enumerate(zincir):
        kut(bx+i*(xw+7*mm), by-11*mm, xw, 11*mm, t1, t2, h.NAVY if i == 2 else h.NAVY2)
        if i < len(zincir)-1:
            c.setStrokeColor(h.NAVY2); c.setLineWidth(1.2)
            c.line(bx+i*(xw+7*mm)+xw, by-5.5*mm, bx+(i+1)*(xw+7*mm), by-5.5*mm)
    by -= 16*mm
    # — kaçak akım röleleri
    kut(bx, by-10*mm, 92*mm, 10*mm, "KAÇAK AKIM RÖLESİ 1 — 4×40 A / 30 mA", "genel linyeler")
    kut(bx+99*mm, by-10*mm, 92*mm, 10*mm, "KAÇAK AKIM RÖLESİ 2 — 4×40 A / 30 mA",
        "yalnız ıslak hacim (L5, P5)", HexColor("#2E7D5B"))
    by -= 15*mm
    # — linye barası
    c.setFillColor(h.COPPER); c.rect(bx, by-3*mm, sw-16*mm, 3*mm, 0, 1)
    h.txt(c, bx+2*mm, by-2.3*mm, "LİNYE BARASI  ·  L1 / L2 / L3 / N / PE", h.FB, 5.0,
          HexColor("#FFFFFF"))
    by -= 8*mm
    # — linyeler (3 sütun)
    kol = 3; ws = (sw-16*mm)/kol
    for i, l in enumerate(P.LINYE):
        cx0 = bx+(i % kol)*ws; cy0 = by-(i//kol)*8.2*mm
        renk = {"L": M.C_AYD, "P": M.C_PRIZ, "K": M.C_KLIMA, "W": M.C_SICAK,
                "V": M.C_BESLEME, "Z": M.C_ZAYIF}[l[0][0]]
        c.setStrokeColor(renk); c.setLineWidth(0.8)
        c.line(cx0+2*mm, cy0+3.2*mm, cx0+2*mm, cy0-1.4*mm)
        c.setFillColor(renk); c.circle(cx0+2*mm, cy0+1.2*mm, 1.5*mm, 0, 1)
        h.txt(c, cx0+2*mm, cy0+0.2*mm, l[0], h.FB, 3.8, HexColor("#FFFFFF"), "c")
        h.txt(c, cx0+6*mm, cy0+2.2*mm, l[1][:38], h.F, 5.4, h.INK)
        h.txt(c, cx0+6*mm, cy0-1.6*mm, f"{l[2]} · {l[3]} mm² · faz {l[4]} · {l[5]:.2f} kW"
              .replace(".", ","), h.F, 4.6, h.GREY)
    ny = by-(len(P.LINYE)//kol+1)*8.2*mm-4*mm
    c.setFillColor(h.NAVY2); c.rect(bx, ny-3*mm, sw-16*mm, 3*mm, 0, 1)
    h.txt(c, bx+2*mm, ny-2.3*mm, "NÖTR (N) VE KORUMA (PE) BARASI  ·  ayrı barada, TN-S",
          h.FB, 5.0, HexColor("#FFFFFF"))
    h.madde_listesi(c, bx, ny-9*mm, sw-16*mm, [
      "Islak hacim linyeleri (L5, P5) ikinci kaçak akım rölesinden beslenir; bir arıza tüm tesisi karartmaz.",
      "Su ısıtıcıları (W1, W2) farklı fazlara atanmıştır — faz dengesizliği %"
      f"{h.tl(P.FAZ_DENGE,1)}'de tutulmuştur.",
      "Yangın algılama linyesi (Z2) kesintisiz beslenir; panel aküsü 24 saat yedekler.",
      "Pano üzerinde kalıcı tek hat şeması ve linye etiketleri bulunacaktır.",
    ], fs=6.2, lead=8.4)
    x2 = L+sw+7*mm; w2 = CW-sw-7*mm; yy2 = TOP
    h.txt(c, x2, yy2-4*mm, "FAZ DENGESİ", h.FB, 8, h.NAVY)
    rows = [[f, f"{P.FAZ_YUK[f]:.2f}".replace(".", ","), f"{P.AKIM_FAZ[f]:.1f}".replace(".", ","),
             str(sum(1 for l in P.LINYE if l[4] == f))] for f in ("L1", "L2", "L3")]
    rows.append(["TOPLAM", f"{P.TALEP_KW:.2f}".replace(".", ","), "", str(len(P.LINYE))])
    yy2 = h.tablo(c, x2, yy2-7*mm, [("Faz", 0.22), ("Talep kW", 0.28), ("Akım A", 0.25),
                                    ("Linye", 0.25)], rows, w2, satir_h=6.4*mm, fs=6.4,
                  hizala=["c", "r", "r", "c"])
    # faz denge çubukları
    h.txt(c, x2, yy2-8*mm, "FAZ YÜK DAĞILIMI", h.FB, 7.4, h.NAVY)
    mx = max(P.FAZ_YUK.values()); by2 = yy2-13*mm
    for f in ("L1", "L2", "L3"):
        wbar = (w2-18*mm)*P.FAZ_YUK[f]/mx
        h.txt(c, x2, by2-3.2*mm, f, h.FB, 6.0, h.NAVY)
        c.setFillColor(h.NAVY2); c.roundRect(x2+7*mm, by2-4.4*mm, wbar, 4.4*mm, 0.7*mm, 0, 1)
        h.txt(c, x2+9*mm+wbar, by2-3.2*mm, f"{P.FAZ_YUK[f]:.2f} kW".replace(".", ","),
              h.F, 5.6, h.NAVY)
        by2 -= 7.0*mm
    h.txt(c, x2, by2-1*mm, f"Dengesizlik %{h.tl(P.FAZ_DENGE,1)} — hedef ≤ %15", h.F, 6.0, h.GREEN)
    h.txt(c, x2, by2-10*mm, "YÜK ÖZETİ", h.FB, 8, h.NAVY)
    rows2 = [[k, f"{v:.2f}".replace(".", ",")] for k, v in P.ELEKTRIK_YUK]
    rows2.append(["TOPLAM BAĞLI GÜÇ", f"{P.BAGLI_KW:.2f}".replace(".", ",")])
    rows2.append(["TALEP GÜCÜ (eşzamanlılık)", f"{P.TALEP_KW:.2f}".replace(".", ",")])
    rows2.append(["ÖNERİLEN ABONELİK", P.ABONELIK])
    yy2 = h.tablo(c, x2, by2-14*mm, [("Yük kalemi", 0.66), ("kW", 0.34)], rows2,
                  w2, satir_h=5.8*mm, fs=6.2, hizala=["l", "r"])
    h.notkutu(c, x2, yy2-6*mm, w2, "Faz dağıtım yöntemi",
      "Linyeler talep gücüne göre büyükten küçüğe sıralanmış ve her biri o an en az yüklü faza "
      "atanmıştır. İki 6 kW'lık su ısıtıcısı farklı fazlara düşürülerek dengesizlik %"
      f"{h.tl(P.FAZ_DENGE,1)}'e indirilmiştir. Uygulamada linye değişirse denge yeniden "
      "hesaplanmalıdır.", fs=6.3, acc=h.NAVY2)

# ══ 6 · TOPRAKLAMA, METRAJ VE LEJANT ═══════════════════════════════════════════
def s6(c):
    sayfa(c, 6, "Topraklama, metraj özeti ve lejant", "Koruma · poz bazlı miktarlar · semboller")
    elk = [r for r in P.B if r[1] == "ELEKTRİK"]
    tw_ = CW*0.62
    rows = [[r[0], r[2], r[3], f"{r[4]:.2f}".replace(".", ","),
             "önerilen" if r[7] == "O" else "zorunlu"] for r in elk]
    yy = h.tablo(c, L, TOP, [("Poz", 0.07), ("Tanım", 0.55), ("Birim", 0.09),
                             ("Miktar", 0.13), ("Kapsam", 0.16)],
                 rows, tw_, satir_h=5.2*mm, fs=5.9, hfs=6.2, hizala=["c", "l", "c", "r", "c"])
    m = P.maliyet("O", "A"); lo, hi = m["gruplar"]["ELEKTRİK"]
    h.txt(c, L, yy-7*mm, f"ELEKTRİK İMALAT TOPLAMI (önerilen senaryo):  {h.bant(lo, hi)}",
          h.FB, 8, h.NAVY)
    h.txt(c, L, yy-13*mm, "Birim fiyat sütunları boş .xlsx dosyası: output/Gym_Elektrik_BoQ.xlsx",
          h.F, 6.4, h.GREY)
    x2 = L+tw_+7*mm; w2 = CW-tw_-7*mm
    h.txt(c, x2, TOP-4*mm, "TOPRAKLAMA VE KORUMA", h.FB, 8.5, h.NAVY)
    rows2 = [["Topraklama sistemi", "TN-S · ayrı N ve PE"],
             ["Hedef topraklama direnci", "≤ 10 Ω"],
             ["Ana potansiyel dengeleme", "su, pis su, havalandırma, yapı metal aksamı"],
             ["Islak hacim ek dengeleme", "2 blok — tüm metal aksam barada"],
             ["Kaçak akım koruma", "2 × 30 mA (ıslak hacim ayrı)"],
             ["Aşırı gerilim koruma", "Tip 2 parafudr"],
             ["Ölçüm ve rapor", "topraklama direnci + izolasyon testi"]]
    yy2 = h.tablo(c, x2, TOP-8*mm, [("Kalem", 0.46), ("Değer", 0.54)], rows2,
                  w2, satir_h=6.4*mm, fs=6.3, hizala=["l", "l"])
    h.txt(c, x2, yy2-8*mm, "LEJANT", h.FB, 8.5, h.NAVY)
    v = D.View(c, x2, yy2-100*mm, w2, 90*mm)
    cy = yy2-14*mm
    sem = [("priz", "İkili topraklı priz"), ("priz_ip44", "IP44 priz — ıslak hacim"),
           ("anahtar", "Anahtar / komütatör / vaviyen"), ("sensor", "Hareket sensörü"),
           ("downlight", "IP44 downlight 18 W"), ("acil", "Acil aydınlatma / yönlendirme"),
           ("kamera", "IP güvenlik kamerası"), ("hoparlor", "Tavan hoparlörü"),
           ("veri", "Veri prizi / rack"), ("dedektor", "Optik duman dedektörü"),
           ("yangin", "Yangın butonu / siren")]
    for tip, t in sem:
        vv = D.View(c, x2, cy-3*mm, 8*mm, 6*mm, pad=0)
        # sembolü doğrudan sayfa koordinatında çiz
        class _V:
            c = None; s = 1.0
            def p(self, pt): return (x2+3.2*mm, cy+1.0*mm)
            def m(self, d):  return 3.0*mm
        _v = _V(); _v.c = c
        M.sembol(_v, 0, 0, tip)
        h.txt(c, x2+9*mm, cy, t, h.F, 6.2, h.INK)
        cy -= 7.0*mm
    c.setFillColor(HexColor("#FFF3C4")); c.setStrokeColor(M.C_AYD); c.setLineWidth(0.6)
    c.rect(x2, cy-0.8*mm, 8*mm, 2.4*mm, 1, 1)
    h.txt(c, x2+9*mm, cy, "Lineer LED armatür 40 W", h.F, 6.2, h.INK); cy -= 7.0*mm
    c.setFillColor(HexColor("#16273D")); c.rect(x2, cy-1.2*mm, 8*mm, 3.4*mm, 0, 1)
    h.txt(c, x2+9*mm, cy, "Ana dağıtım panosu", h.F, 6.2, h.INK); cy -= 9.0*mm
    cy = h.notkutu(c, x2, cy, w2, "Teslim kriterleri",
      "Topraklama direnci ölçümü, izolasyon direnci testi, kaçak akım rölesi tetikleme testi, "
      "aydınlatma lux ölçümü, acil aydınlatma süre testi ve yangın algılama devreye alma raporu. "
      "Tüm ölçümler tutanakla belgelenip işverene teslim edilecektir.", fs=6.3, acc=h.COPPER)
    h.notkutu(c, x2, cy-4*mm, w2, "Ölçü dayanağı",
      "Cihaz konumları mimari altlık üzerinde (±%3) kurulmuştur. Kablo metrajları güzergâh "
      "uzunluklarından türetilmiş yaklaşık değerlerdir; uygulama öncesi DXF (R2010) ile "
      "kesinleştirilmelidir.", fs=6.3, acc=h.NAVY2)

# ══ 7 · PANO YÜK VE GERİLİM DÜŞÜMÜ HESABI ════════════════════════════════════
def s7(c):
    sayfa(c, 7, "Pano yük ve gerilim düşümü hesabı",
          "Linye bazlı akım · kesici · kablo kesiti · ΔU kontrolü")
    y = TOP
    y = h.para(c, L, y-1*mm,
      f"Hesap tek fazlı son devreler için U={P.U_FAZ:.0f} V, ana besleme için U={P.U_HAT:.0f} V üzerinden "
      f"yapılmıştır. Bakır özdirenci ρ = {str(P.RHO_CU).replace('.',',')} Ω·mm²/m (70 °C işletme sıcaklığı), "
      f"akım taşıma kapasiteleri PVC yalıtımlı bakır iletken, B2 döşeme yöntemi, 2 yüklü iletken ve 30 °C "
      f"ortam için TS HD 60364-5-52'ye göre alınmıştır. Kablo boyları pano konumundan linye ağırlık merkezine "
      f"kuş uçuşu mesafenin {str(P.HAT_KATSAYI).replace('.',',')} katı artı {P.HAT_DUSEY:.0f} m düşey pay ile "
      f"hesaplanmıştır (VARSAYIM — güzergâh kesinleştiğinde tek yerden güncellenir). Her linyede "
      f"Ib ≤ In ≤ Iz ve ΔU ≤ sınır koşulları ayrı ayrı denetlenir.", CW, h.F, 7.6, h.INK, 10.4)
    rows = [[r[0], r[1], r[2], f"{h.tl(r[3],2)}", f"{h.tl(r[4],2)}",
             str(r[5]).replace(".", ","), f"{r[6]:.1f}".replace(".", ","), f"{r[7]}",
             r[8], f"{r[9]:.1f}".replace(".", ","), f"{r[10]:.1f}".replace(".", ","),
             f"{r[12]:.2f}".replace(".", ","), f"{r[13]:.0f}", r[14]]
            for r in P.PANO_HESAP]
    rows.append(["", h.TR_UP("TOPLAM"), "", f"{h.tl(P.BAGLI_KW,2)}", f"{h.tl(P.TALEP_KW,2)}",
                 "", "", "", "", "", "", f"maks {P.DU_MAX:.2f}".replace(".", ","), "", ""])
    def _snc(row):
        return HexColor("#E7F3EC") if row[13] == "UYGUN" else (HexColor("#FBE3E1") if row[13] else None)
    y = h.tablo(c, L, y-4*mm,
        [("Linye",0.042),("Tanım",0.200),("Faz",0.034),("Pb kW",0.048),("Pt kW",0.048),
         ("cosφ",0.040),("Ib A",0.044),("In A",0.040),("Kablo",0.058),("Iz A",0.042),
         ("L m",0.042),("ΔU %",0.046),("Sınır %",0.048),("Sonuç",0.068)],
        rows, CW, satir_h=5.5*mm, bas_h=6.6*mm, fs=6.0, hfs=5.8,
        hizala=["c","l","c","r","r","c","r","r","c","r","r","r","c","c"],
        renkli_sutun={13: _snc})

    # alt bölüm: ana besleme · kaçak akım · notlar
    yy = y-7*mm; w1 = CW*0.315; w2 = CW*0.345; w3 = CW-w1-w2-2*6*mm
    h.txt(c, L, yy, h.TR_UP("Ana besleme hesabı"), h.FB, 8.0, h.NAVY)
    rows2 = [["Talep gücü (eşzamanlılık sonrası)", f"{h.tl(P.TALEP_KW,2)} kW"],
             ["Güç katsayısı (kabul)", ("%.2f" % P.ANA_COSFI).replace(".", ",")],
             ["Hesap akımı Ib = P / (√3·U·cosφ)", ("%.1f A" % P.ANA_IB).replace(".", ",")],
             ["Ana kesici In", f"3×{P.ANA_IN} A"],
             ["Ana kaçak akım koruması", P.ANA_KACAK],
             ["Besleme kablosu", P.ANA_KABLO],
             ["Kablo akım kapasitesi Iz", f"{P.ANA_IZ:.0f} A"],
             ["Hat uzunluğu (VARSAYIM)", f"{P.ANA_L:.0f} m"],
             ["Gerilim düşümü ΔU", ("%.2f V" % P.ANA_DU).replace(".", ",") + "  ·  %" +
                                   ("%.2f" % P.ANA_DU_P).replace(".", ",")],
             ["Abonelik önerisi", P.ABONELIK]]
    h.tablo(c, L, yy-5*mm, [("Büyüklük",0.62),("Değer",0.38)], rows2, w1,
            satir_h=5.4*mm, bas_h=6.4*mm, fs=6.1, hfs=6.0, hizala=["l","r"])
    x2 = L+w1+6*mm
    h.txt(c, x2, yy, h.TR_UP("Kaçak akım koruma grupları"), h.FB, 8.0, h.NAVY)
    h.tablo(c, x2, yy-5*mm, [("Kod",0.11),("Cihaz",0.30),("Kapsam",0.59)],
            [[k[0], k[1], k[2]] for k in P.KACAK_AKIM], w2,
            satir_h=5.4*mm, bas_h=6.4*mm, fs=6.1, hfs=6.0, hizala=["c","l","l"])
    x3 = x2+w2+6*mm
    _v = lambda x, n=2: ("%.*f" % (n, x)).replace(".", ",")
    yyy = h.notkutu(c, x3, yy+1*mm, w3, "Sonuç",
      f"Tüm {len(P.PANO_HESAP)} linye Ib ≤ In ≤ Iz ve ΔU ≤ sınır koşullarını sağlamaktadır "
      f"({len(P.PANO_UYGUNSUZ)} uygunsuz linye). En yüksek son devre gerilim düşümü "
      f"%{_v(P.DU_MAX)} ({P.DU_MAX_LINYE}); ana besleme ile birlikte en uzak tüketicide toplam "
      f"%{_v(P.TOPLAM_DU_MAX)} olup TS HD 60364-5-52'nin %5 sınırının altındadır. "
      f"Faz dengesizliği %{_v(P.FAZ_DENGE, 1)}'dir.", fs=6.2, acc=h.GREEN)
    h.notkutu(c, x3, yyy-4*mm, w3, "Uygulamada dikkat",
      "Mevcut sayaç ve kolon hattı kapasitesi BİLİNMİYOR; abonelik yükseltme gerekip gerekmediği "
      "yerinde tespit edilecektir. W1 ve W2 su ısıtıcıları 6 kW / 26,1 A ile panonun en büyük "
      "tekil yükleridir ve farklı fazlara dağıtılmıştır. Z2 yangın algılama paneli kaçak akım "
      "rölesi arkasına alınmaz; kendi aküsü ile 60 dakika beslenir. Tüm son devrelerde 30 mA "
      "A tipi kaçak akım koruması, ana girişte 300 mA S tipi seçici koruma kullanılacaktır.",
      fs=6.2, acc=h.RED)

def build(path="output/Gym_Elektrik_Proje_A3.pdf"):
    c = canvas.Canvas(path, pagesize=(W, HH))
    c.setTitle(f"Maltepe / İdealtepe — Elektrik Projesi ({P.REV})")
    for fn in (s1, s2, s3, s4, s5, s6, s7):
        fn(c); c.showPage()
    c.save(); print("→", path)

if __name__ == "__main__":
    build()
