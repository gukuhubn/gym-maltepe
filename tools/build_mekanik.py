# -*- coding: utf-8 -*-
"""MEKANİK PROJE — A3 yatay, 9 pafta (her konu ayrı paftada)."""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
import proj as P, helpers as h, draw as D, draw_mep as M, draw_mim as MM

W, HH = 420*mm, 297*mm
TOP, BOT, L, R = HH-24.6*mm, 14*mm, 12*mm, W-12*mm
CW = R-L
N = 9
DISIPLIN = "MEKANİK TESİSAT PROJESİ"

def sayfa(c, no, baslik, ust=None):
    h.band(c, W, HH, no, baslik, ust or DISIPLIN)
    h.footer(c, W, no, N)

def kunye(c, x, y, w, pafta, olcek="1/50 (A3)"):
    hgt = 26*mm
    h.kutu(c, x, y-hgt, w, hgt, h.PAPER, h.GREY_L)
    c.setFillColor(h.NAVY); c.rect(x, y-hgt, w, 5.4*mm, 0, 1)
    h.txt(c, x+3*mm, y-hgt+1.7*mm, h.TR_UP(DISIPLIN), h.FB, 5.6, HexColor("#FFFFFF"))
    h.txt(c, x+w-3*mm, y-hgt+1.7*mm, P.REV, h.FB, 5.6, h.COPPER, "r")
    satir = [("Pafta", pafta), ("Ölçek", olcek), ("Tarih", P.TARIH),
             ("Durum", "Ön tasarım — yerinde doğrulanacak")]
    yy = y-5*mm
    for k, v in satir:
        h.txt(c, x+3*mm, yy, k, h.FB, 5.2, h.GREY)
        h.txt(c, x+w-3*mm, yy, v, h.F, 5.6, h.INK, "r")
        yy -= 4.6*mm
    return y-hgt

# ══ 1 · KAPAK / SİSTEM ÖZETİ ═══════════════════════════════════════════════════
def s1(c):
    sayfa(c, 1, "Mekanik tesisat projesi", "Sistem özeti · tasarım kriterleri · genel notlar")
    y = TOP
    y = h.para(c, L, y-2*mm,
      "Bu dosya, Maltepe / İdealtepe'deki mobilya mağazasının fonksiyonel antrenman stüdyosuna "
      f"dönüşümü için mekanik tesisat ön projesidir. Kapsam üç sistemdir: havalandırma (taze hava ve "
      f"egzoz), iklimlendirme (bölge bazlı split küme) ve sıhhi tesisat (temiz su, sıcak su, pis su). "
      f"Net iç kullanım alanı {h.tl(P.A['ic_toplam'],2)} m², tavan yüksekliği {h.tl(P.V['tavan_h'][0],2)} m "
      "(varsayım — yerinde doğrulanacak). Metrajlar mimari altlıktan türetilmiştir; birim fiyat "
      "sütunları boş BoQ dosyası ektedir.", CW, h.F, 8.2, h.INK, 11.4)
    kw = (CW-2*6*mm)/3; ky = y-8*mm-52*mm
    for i, (no, bs, gv) in enumerate([
      ("M1", "HAVALANDIRMA",
       f"Dengeli sistem: {h.tl(P.TAZE)} m³/h taze hava besleme, aynı debide egzoz. Kişi başı "
       f"{P.TAZE/P.KISI:.0f} m³/h (yasal asgari 30) ve saatte {P.ACH:.2f} hava değişimi. "
       f"Besleme kuzey çeperden, egzoz güney çeperden — salon boyunca çapraz süpürme. "
       f"Islak hacim {P.EGZOZ_ISLAK} m³/h ayrı hatla, doğrudan dışarı.".replace(".",",",1)),
      ("M2", "İKLİMLENDİRME",
       f"Hesaplanan soğutma yükü {h.tl(P.SOGUTMA_BTU)} BTU/h. VRF yerine bütçe gereği bölge bazlı "
       f"inverter split küme: {P.ADET_KLIMA} iç ünite, toplam {h.tl(P.KLIMA_BTU)} BTU/h kurulu kapasite "
       f"(%{P.SOGUTMA_MARJ} marj). Dış üniteler arka cephe duvarında konsol üzerinde — kapalı alana dâhil değil."),
      ("M3", "SIHHİ TESİSAT",
       "İki soyunma bloğunda 1'er duş + 1'er WC. Tek düşey şaft, tek gider toplama hattı. Sıcak su "
       "blok başına 6 kW elektrikli ani ısıtıcı ile — yönetmeliğin 'çalışma boyunca sürekli sıcak su' "
       "şartı bekleme süresi olmadan karşılanır.")]):
        h.kart(c, L+i*(kw+6*mm), ky, kw, 52*mm, no, bs, gv)
    kw2 = (CW-5*5*mm)/6; ky2 = ky-8*mm-30*mm
    for i, (u, dv, al) in enumerate([
      ("TAZE HAVA", f"{h.tl(P.TAZE)} m³/h", f"{P.TAZE/P.KISI:.0f} m³/h·kişi · {P.ACH:.2f} h⁻¹".replace(".",",")),
      ("EGZOZ", f"{h.tl(P.TAZE)} m³/h", f"salon {h.tl(P.TAZE-P.EGZOZ_ISLAK)} + ıslak {P.EGZOZ_ISLAK}"),
      ("SOĞUTMA YÜKÜ", f"{h.tl(P.SOGUTMA_BTU)} BTU", f"{h.tl(P.SOGUTMA_W)} W · 180 W/m²"),
      ("KURULU KAPASİTE", f"{h.tl(P.KLIMA_BTU)} BTU", f"{P.ADET_KLIMA} iç ünite · %{P.SOGUTMA_MARJ} marj"),
      ("PİS SU ANA HAT", "Ø100", f"{h.tl(P.L_PIS100,1)} m · %2 eğim"),
      ("SICAK SU", "2 × 6 kW", "ani ısıtıcı · bekleme yok")]):
        h.kpi(c, L+i*(kw2+5*mm), ky2, kw2, 30*mm, u, dv, al, h.COPPER if i < 3 else h.NAVY2)
    h.txt(c, L, ky2-9*mm, "GENEL NOTLAR", h.FB, 8.5, h.NAVY)
    cy = h.madde_listesi(c, L, ky2-15*mm, CW*0.49, [
      "Tüm kanallar galvaniz sacdan, TS EN 1507 sızdırmazlık sınıfı B'ye uygun imal edilecektir.",
      "Besleme ve egzoz ana hatları 19 mm elastomerik kauçukla izole edilecektir.",
      "Her branşman başına debi ayar damperi konulacak; devreye almada balanslama yapılıp "
      "ölçüm raporu teslim edilecektir.",
      "Kanal askıları titreşim takozlu olacak; fanlar esnek bağlantı ile kanala bağlanacaktır.",
      "Islak hacim egzozu doğrudan dışarı atılacak; salon egzozuna bağlanmayacaktır.",
    ], fs=6.6, lead=8.8)
    h.madde_listesi(c, L+CW*0.51, ky2-15*mm, CW*0.49, [
      "Pis su hatları %2 eğimle döşenecek, her ıslak hacimde sifonlu yer süzgeci bulunacaktır.",
      "Tesisat kapatılmadan önce basınç testi yapılacak, sonuç tutanakla belgelenecektir.",
      "SÖKÜM SONRASI İLK İŞ: mevcut pis su bağlantısının kotu ve konumu ölçülecek; "
      "Seçenek A (zemin yükseltme) / B (pompa) kararı bu ölçüme bağlıdır.",
      "Binada doğalgaz bulunduğu tespit edilirse sıcak su çözümü yoğuşmalı kombiye revize edilecek, "
      "elektrik abonelik gücü buna göre yeniden hesaplanacaktır.",
      "Dış ünite yerleşimi için kat malikleri / yönetim onayı alınmalıdır.",
    ], fs=6.6, lead=8.8)
    h.notkutu(c, L, cy-6*mm, CW, "Doğrulanacak girdiler",
      "Tavan yüksekliği (3,20 m varsayım), mevcut pis su bağlantı kotu ve konumu, doğalgaz "
      "bağlantısının varlığı, dış ünite montaj yüzeyinin taşıyıcılığı ve komşuluk durumu, "
      "binanın mevcut havalandırma bacası olup olmadığı. Bu beş girdi netleşmeden imalata "
      "başlanmamalıdır.", fs=6.6, acc=h.RED)
    h.txt(c, L, BOT+58*mm, "SİSTEM KAPSAM TABLOSU", h.FB, 8.5, h.NAVY)
    krow = [["Havalandırma",
             f"3 fan · {h.tl(P.L_KANAL_B+P.L_KANAL_E+P.L_KANAL_I,1)} m kanal · 7 menfez · 4 egzoz valfi · 2 susturucu · 3 panjur",
             f"{h.tl(P.TAZE)} m³/h"],
            ["İklimlendirme",
             f"{P.ADET_KLIMA} iç ünite (24.000 + 18.000 + 2 × 12.000 BTU) · {h.tl(P.L_BAKIR,1)} m bakır hat · {h.tl(P.L_DRENAJ,1)} m drenaj",
             f"{h.tl(P.KLIMA_BTU)} BTU"],
            ["Sıhhi tesisat — temiz su",
             f"PPRC Ø25 {h.tl(P.L_TEMIZ25,1)} m + Ø20 {h.tl(P.L_TEMIZ20,1)} m · sayaç sonrası ana kesme + filtre · 8 vana",
             "4 cihaz"],
            ["Sıhhi tesisat — sıcak su",
             f"PPRC Ø20 izoleli {h.tl(P.L_SICAK,1)} m · blok başına 6 kW elektrikli ani ısıtıcı",
             "2 × 6 kW"],
            ["Sıhhi tesisat — pis su",
             f"PVC Ø100 {h.tl(P.L_PIS100,1)} m + Ø70 {h.tl(P.L_PIS70,1)} m + Ø50 {h.tl(P.L_PIS50,1)} m · 4 yer süzgeci · Ø70 baca",
             "%2 eğim"]]
    h.tablo(c, L, BOT+52*mm, [("Sistem", 0.18), ("Kapsam", 0.66), ("Kapasite", 0.16)],
            krow, CW, satir_h=6.8*mm, fs=6.4, hizala=["l", "l", "c"])

# ══ 2 · HAVALANDIRMA PLANI ═════════════════════════════════════════════════════
def s2(c):
    sayfa(c, 2, "Havalandırma planı", "Kanal güzergâhı · menfez debileri · hava dengesi")
    pw = CW*0.585
    v = D.View(c, L, BOT+8*mm, pw, TOP-BOT-10*mm)
    M.altlik(v); M.ekipman_soluk(v)
    M.kanal(v, P.KANAL["besleme"]["guzergah"], 0.50, M.C_BESLEME)
    M.kanal(v, P.KANAL["egzoz"]["guzergah"],   0.40, M.C_EGZOZ)
    M.kanal(v, P.KANAL["islak"]["guzergah"],   0.16, M.C_ISLAK)
    for kod, x, y, debi, tip in P.MENFEZ:
        hat = P.KANAL["besleme" if tip == "besleme" else ("egzoz" if tip == "egzoz" else "islak")]
        from shapely.geometry import LineString as LS, Point as Pt
        q = LS(hat["guzergah"]).interpolate(LS(hat["guzergah"]).project(Pt(x, y)))
        D.line(v, (q.x, q.y), (x, y), hat["renk"], 0.7, (1.4, 1.2))
        M.menfez(v, x, y, tip, kod, debi)
    for kod, x, y, ad, a in P.FAN:
        M.cihaz(v, x, y, kod, M.C_BESLEME if "TH" in kod else
                (M.C_ISLAK if "IS" in kod else M.C_EGZOZ), 9.5*mm, 5*mm, a)
    for kod, x, y, ad in P.PANJUR:
        D.poly(v, __import__("shapely.geometry", fromlist=["Point"]).Point(x, y).buffer(0.22),
               fill=HexColor("#FFFFFF"), stroke=h.NAVY, lw=0.8)
        D.etiket(v, (x, y), kod, 4.2, h.NAVY, h.FB, "c", dy=-1.3)
    D.kuzey_ok(v, L+pw-13*mm, TOP-13*mm); D.olcek_cubugu(v, L+5*mm, BOT+11*mm)
    h.lejant(c, L+5*mm, BOT+2*mm,
             [(M.C_BESLEME, "Taze hava (besleme)"), (M.C_EGZOZ, "Egzoz"),
              (M.C_ISLAK, "Islak hacim egzozu")], 6.0)
    x2 = L+pw+7*mm; w2 = CW-pw-7*mm; yy = TOP
    h.txt(c, x2, yy-4*mm, "HAVA DENGESİ", h.FB, 8, h.NAVY)
    rows = [["Besleme — M1…M4", "4 × 250", f"{h.tl(P.TAZE)}"],
            ["Egzoz — E1…E3 (salon)", "255 / 255 / 250", f"{h.tl(P.TAZE-P.EGZOZ_ISLAK)}"],
            ["Egzoz — V1…V4 (duş / WC)", "80 / 40 / 80 / 40", f"{P.EGZOZ_ISLAK}"],
            ["TOPLAM BESLEME", "", f"{h.tl(P.TAZE)}"],
            ["TOPLAM EGZOZ", "", f"{h.tl(P.TAZE)}"],
            ["Denge", "", "0 (nötr)"]]
    yy = h.tablo(c, x2, yy-7*mm, [("Hat", 0.46), ("Cihaz debisi (m³/h)", 0.30), ("Toplam", 0.24)],
                 rows, w2, satir_h=6.0*mm, fs=6.3, hizala=["l", "c", "r"])
    h.txt(c, x2, yy-8*mm, "KANAL BOYUTLANDIRMA", h.FB, 8, h.NAVY)
    rows2 = []
    for ad, k in (("Besleme ana hattı", "besleme"), ("Egzoz ana hattı", "egzoz"),
                  ("Islak hacim hattı", "islak")):
        d = P.KANAL[k]
        rows2.append([ad, d["kesit"], f"{h.tl(d['debi'])}", f"{d['hiz']:.1f}".replace(".", ","),
                      f"{h.tl({'besleme':P.L_KANAL_B,'egzoz':P.L_KANAL_E,'islak':P.L_KANAL_I}[k],1)}"])
    rows2.append(["Menfez branşmanları", "Ø200", "250", "2,2", f"{h.tl(P.L_BRANS,1)}"])
    rows2.append(["Valf branşmanları", "Ø125", "40–80", "1,8", f"{h.tl(P.L_BRANS_I,1)}"])
    yy = h.tablo(c, x2, yy-13*mm, [("Hat", 0.34), ("Kesit", 0.16), ("Debi m³/h", 0.18),
                                   ("Hız m/s", 0.14), ("Uzunluk m", 0.18)],
                 rows2, w2, satir_h=6.0*mm, fs=6.3, hizala=["l", "c", "r", "r", "r"])
    h.txt(c, x2, yy-8*mm, "TASARIM KRİTERLERİ", h.FB, 8, h.NAVY)
    rows3 = [["Kişi sayısı (sporcu + personel)", f"{P.KISI}"],
             ["Kişi başı taze hava", f"{P.TAZE/P.KISI:.0f} m³/h (asgari 30)"],
             ["Hava değişim sayısı", f"{P.ACH:.2f} h⁻¹".replace(".", ",")],
             ["Ana kanal hızı (gürültü sınırı)", "≤ 4,0 m/s"],
             ["Branşman hızı", "≤ 2,5 m/s"],
             ["Menfez yüz hızı", "≤ 2,0 m/s"],
             ["Salon ısısı — yönetmelik / tasarım", "≥18 °C / 20–22 °C"]]
    yy = h.tablo(c, x2, yy-13*mm, [("Kriter", 0.60), ("Değer", 0.40)], rows3,
                 w2, satir_h=5.8*mm, fs=6.3, hizala=["l", "r"])
    h.notkutu(c, x2, yy-6*mm, w2, "Isı geri kazanım — seçenek",
      "Poz 06.17 alternatif kalemdir ve bütçe toplamına dâhil edilmemiştir. %75 verimli ısı geri "
      "kazanımlı ünite, 1.000 m³/h taze havanın ısıtma/soğutma yükünü kabaca dörtte üçe kadar "
      "azaltır; işletme giderinden geri ödeme süresi kullanım yoğunluğuna bağlıdır ve teklif "
      "alındıktan sonra hesaplanmalıdır.", fs=6.3, acc=h.NAVY2)

# ══ 3 · İKLİMLENDİRME PLANI ════════════════════════════════════════════════════
def s3(c):
    sayfa(c, 3, "İklimlendirme planı", "Bölge bazlı split küme · bakır hat · drenaj")
    pw = CW*0.585
    v = D.View(c, L, BOT+8*mm, pw, TOP-BOT-10*mm)
    M.altlik(v); M.ekipman_soluk(v)
    for z in P.ZONES:
        D.poly(v, z[1], fill=HexColor(z[4]), alpha=0.45)
    for hat in P.DRENAJ.values(): M.boru(v, hat, M.C_DRENAJ, 0.9, (1.5, 1.3))
    for hat in P.BAKIR_HAT.values(): M.boru(v, hat, M.C_KLIMA, 1.5)
    for kod, zon, btu, (x, y), a in P.KLIMA:
        M.cihaz(v, x, y, kod, M.C_KLIMA, 8.5*mm, 4.6*mm, a)
        D.etiket(v, (x, y-0.55), f"{h.tl(btu)} BTU", 4.2, M.C_KLIMA, h.FB, "c")
    dx, dy = P.DIS_UNITE
    c.setFillColor(M.C_KLIMA); c.setStrokeColor(HexColor("#FFFFFF")); c.setLineWidth(0.8)
    px, py = v.p((dx, dy)); c.roundRect(px-7*mm, py-9*mm, 14*mm, 18*mm, 1*mm, 1, 1)
    h.txt(c, px, py+4*mm, "DIŞ ÜNİTE", h.FB, 4.6, HexColor("#FFFFFF"), "c")
    h.txt(c, px, py, "PLATFORMU", h.FB, 4.6, HexColor("#FFFFFF"), "c")
    h.txt(c, px, py-5*mm, "4 adet", h.F, 4.2, HexColor("#D7EEF6"), "c")
    D.kuzey_ok(v, L+pw-13*mm, TOP-13*mm); D.olcek_cubugu(v, L+5*mm, BOT+11*mm)
    h.lejant(c, L+5*mm, BOT+2*mm, [(M.C_KLIMA, "Soğutucu akışkan bakır hattı"),
                                   (M.C_DRENAJ, "Drenaj hattı")], 6.0)
    x2 = L+pw+7*mm; w2 = CW-pw-7*mm; yy = TOP
    h.txt(c, x2, yy-4*mm, "BÖLGE BAZLI SOĞUTMA YÜKÜ", h.FB, 8, h.NAVY)
    rows = []
    for kod, zon, btu, _, _a in P.KLIMA:
        m2 = P.ZON_M2[zon]
        rows.append([kod, zon.split(" · ")[0].title(), f"{m2:.2f}".replace(".", ","),
                     h.tl(int(round(m2*180))), h.tl(int(round(m2*180*3.412/1000)*1000)), h.tl(btu)])
    rows.append(["", "Islak hacim (klimasız)", f"{P.A['islak_toplam']:.2f}".replace(".", ","),
                 h.tl(int(P.A['islak_toplam']*60)), h.tl(int(P.A['islak_toplam']*60*3.412)), "—"])
    rows.append(["", "TOPLAM", f"{P.A['ic_toplam']:.2f}".replace(".", ","),
                 h.tl(P.SOGUTMA_W), h.tl(P.SOGUTMA_BTU), h.tl(P.KLIMA_BTU)])
    yy = h.tablo(c, x2, yy-7*mm, [("Ünite", 0.10), ("Bölge", 0.28), ("m²", 0.12),
                                  ("Yük W", 0.16), ("İhtiyaç BTU", 0.17), ("Seçilen", 0.17)],
                 rows, w2, satir_h=6.2*mm, fs=6.2, hizala=["c", "l", "r", "r", "r", "r"])
    h.txt(c, x2, yy-8*mm, "SİSTEM SEÇİMİ — NEDEN VRF DEĞİL", h.FB, 8, h.NAVY)
    cy = h.madde_listesi(c, x2, yy-14*mm, w2, [
      f"{h.tl(P.A['ic_toplam'],2)} m²'lik tek katlı, tek kullanıcılı bir birimde VRF'in bölge kontrolü "
      "avantajı karşılığını vermez; ilk yatırım farkı bu ölçekte iki katına yakındır.",
      "Bölge bazlı split küme, her mekânın bağımsız çalışmasını zaten sağlar: dinlenme salonu "
      "kullanılmıyorken kapatılabilir.",
      "Bir ünitenin arızası tüm tesisi durdurmaz — butik işletmede kritik avantaj.",
      f"Kurulu kapasite {h.tl(P.KLIMA_BTU)} BTU, hesaplanan ihtiyacın %{P.SOGUTMA_MARJ} üzerinde; "
      "yaz tepe yükünde ve kapı açılmalarında marj bırakır.",
    ], fs=6.4, lead=8.6)
    h.txt(c, x2, cy-4*mm, "MONTAJ NOTLARI", h.FB, 8, h.NAVY)
    rows2 = [["İç ünite montaj yüksekliği", "2,40 m (alt kot)"],
             ["Bakır hat toplam uzunluğu", f"{h.tl(P.L_BAKIR,1)} m"],
             ["Drenaj hattı toplam uzunluğu", f"{h.tl(P.L_DRENAJ,1)} m · %1 eğim"],
             ["Dış ünite konumu", "arka cephe duvarı — kapalı alana dâhil değil"],
             ["Dış ünite konsolu", "galvaniz + titreşim takozu"],
             ["Devreye alma", "vakum, gaz şarjı, performans testi"]]
    yy2 = h.tablo(c, x2, cy-10*mm, [("Kalem", 0.56), ("Değer", 0.44)], rows2,
                  w2, satir_h=5.8*mm, fs=6.3, hizala=["l", "r"])
    h.notkutu(c, x2, yy2-6*mm, w2, "Dikkat",
      "Dış ünite yerleşimi ortak alan / cephe kullanımı olduğundan bina yönetiminden yazılı onay "
      "alınmalıdır. Üst katta konut varsa dış ünite gürültüsü şikâyet konusu olabilir; konsol "
      "titreşim takozu ve gece sessiz mod bu riski azaltır.", fs=6.3, acc=h.RED)

# ══ 4 · SIHHİ TESİSAT PLANI ════════════════════════════════════════════════════
def s4(c):
    sayfa(c, 4, "Sıhhi tesisat planı", "Temiz su · sıcak su · pis su · Seçenek A/B")
    pw = CW*0.44
    v = D.View(c, L, BOT+8*mm, pw, TOP-BOT-10*mm,
               geoms=[P.ERKEK.buffer(1.1), P.KADIN.buffer(1.1)])
    ctx = P.ERKEK.union(P.KADIN).buffer(1.1).envelope
    D.poly(v, P.SALON.intersection(ctx), fill=HexColor("#F4F6F8"))
    for b in (P.ERKEK, P.KADIN):
        D.poly(v, b.buffer(0.20, join_style=2).difference(b), fill=HexColor("#B9BFC7"))
        D.poly(v, b, fill=HexColor("#E3E8EC"), stroke=HexColor("#949BA4"), lw=0.6)
    for ad, d in P.ISLAK.items():
        for n in ("dus", "wc"):
            D.poly(v, d[n], fill=HexColor("#D5DEE4"), stroke=HexColor("#A8AEB6"), lw=0.5)
        for n, lbl in (("soyunma", ad), ("dus", "DUŞ"), ("wc", "WC")):
            q = d[n].representative_point()
            D.etiket(v, (q.x, q.y), lbl, 5.2, h.NAVY, h.FB, "c", dy=4.6)
    M.boru(v, P.TEMIZ_SU["Ø25"], M.C_SOGUK, 1.6)
    for br in P.TEMIZ_SU["Ø20"]: M.boru(v, br, M.C_SOGUK, 1.0)
    for br in P.TEMIZ_SU["Ø20"]: M.boru(v, [(p[0]+0.10, p[1]+0.10) for p in br], M.C_SICAK, 1.0, (1.6, 1.3))
    M.boru(v, P.PIS_SU["Ø100"], M.C_PIS, 2.1)
    for br in P.PIS_SU["Ø70"]: M.boru(v, br, M.C_PIS, 1.4)
    for br in P.PIS_SU["Ø50"]: M.boru(v, br, M.C_PIS, 1.0, (2.0, 1.5))
    for kod, x, y, ad in P.VITRIFIYE:
        M.cihaz(v, x, y, kod, HexColor("#5A6470"), 7.5*mm, 4.2*mm)
    for kod, x, y, ad, a in P.ISITICI:
        M.cihaz(v, x, y, kod, M.C_SICAK, 8*mm, 4.4*mm, a)
    sx, sy = P.SU_GIRIS
    D.poly(v, __import__("shapely.geometry", fromlist=["Point"]).Point(sx, sy).buffer(0.26),
           fill=HexColor("#FFFFFF"), stroke=M.C_SOGUK, lw=1.2)
    D.etiket(v, (sx, sy), "SAYAÇ", 4.0, M.C_SOGUK, h.FB, "c", dy=-1.3)
    D.olcek_cubugu(v, L+5*mm, BOT+11*mm, 2)
    h.lejant(c, L+5*mm, BOT+2*mm, [(M.C_SOGUK, "Temiz su"), (M.C_SICAK, "Sıcak su"),
                                   (M.C_PIS, "Pis su")], 6.0)
    x2 = L+pw+7*mm; w2 = CW-pw-7*mm; yy = TOP
    h.txt(c, x2, yy-4*mm, "BORU METRAJI VE BOYUTLANDIRMA", h.FB, 8, h.NAVY)
    rows = [["Temiz su kolon hattı", "PPRC Ø25", f"{h.tl(P.L_TEMIZ25,1)}", "2 blok besleme"],
            ["Temiz su branşmanı", "PPRC Ø20", f"{h.tl(P.L_TEMIZ20,1)}", "4 cihaz"],
            ["Sıcak su hattı (izoleli)", "PPRC Ø20", f"{h.tl(P.L_SICAK,1)}", "ısıtıcıdan cihaza"],
            ["Pis su ana hattı", "PVC Ø100", f"{h.tl(P.L_PIS100,1)}", "%2 eğim"],
            ["Pis su branşmanı — duş", "PVC Ø70", f"{h.tl(P.L_PIS70,1)}", "sifonlu süzgeç"],
            ["Pis su branşmanı — lavabo", "PVC Ø50", f"{h.tl(P.L_PIS50,1)}", "sifonlu"],
            ["Havalandırma bacası", "PVC Ø70", "9,5", "çatı kotuna kadar — TBD"]]
    yy = h.tablo(c, x2, yy-7*mm, [("Hat", 0.34), ("Çap", 0.16), ("Uzunluk m", 0.18), ("Not", 0.32)],
                 rows, w2, satir_h=6.0*mm, fs=6.3, hizala=["l", "c", "r", "l"])
    h.txt(c, x2, yy-8*mm, "GİDER KOTU — SEÇENEK KARŞILAŞTIRMASI", h.FB, 8, h.NAVY)
    dA = [r for r in P.B if r[0] == "03.08"][0]; dB = [r for r in P.B if r[0] == "03.09"][0]
    rows2 = [["Kalem bedeli", h.bant(dA[4]*dA[5], dA[4]*dA[6]), h.bant(dB[4]*dB[5], dB[4]*dB[6])],
             ["Kot serbestliği", "Mevcut kota bağımlı", "Tam serbest"],
             ["Kullanım etkisi", "15–20 cm basamak / rampa", "Kot değişmez, eşiksiz"],
             ["Bakım / arıza riski", "Yok — mekanik parça içermez", "Pompa arızası kullanımı durdurur"],
             ["Elektrik bağımlılığı", "Yok", "Var — kesintide kullanılamaz"],
             ["ÖNERİ", "TERCİH EDİLEN — kot elverirse", "Yalnız A uygulanamazsa"]]
    yy = h.tablo(c, x2, yy-13*mm, [("Ölçüt", 0.28), ("SEÇENEK A — zemin yükseltme", 0.36),
                                   ("SEÇENEK B — atık su pompası", 0.36)],
                 rows2, w2, satir_h=6.2*mm, fs=6.2, hizala=["l", "l", "l"])
    h.txt(c, x2, yy-8*mm, "SICAK SU — SEÇENEK", h.FB, 8, h.NAVY)
    rows3 = [["Bu projede", "2 × 6 kW ani ısıtıcı", "12 kW bağlı · bekleme yok · 3×32 A abonelik"],
             ["Alternatif", "2 × 80 L elektrikli boyler", "2 kW bağlı · abonelik 3×25 A'ya iner · bekleme var"],
             ["Doğalgaz varsa", "Yoğuşmalı kombi 24 kW", "işletme gideri en düşük · baca ve gaz projesi gerekir"]]
    yy = h.tablo(c, x2, yy-13*mm, [("Durum", 0.18), ("Çözüm", 0.34), ("Etkisi", 0.48)],
                 rows3, w2, satir_h=6.4*mm, fs=6.2, hizala=["l", "l", "l"])
    h.notkutu(c, x2, yy-6*mm, w2, "Sıralama kilidi",
      "Islak hacim tesisatı ve gider kotu çözülmeden hiçbir zemin imalatına başlanamaz. Söküm biter "
      "bitmez kot ölçülür; A/B kararı ikinci haftada verilmelidir. Bu karar, iş programındaki "
      "kritik yolun ilk halkasıdır.", fs=6.3, acc=h.COPPER)

# ══ 5 · HAVALANDIRMA PRENSİP ŞEMASI ═══════════════════════════════════════════
def s5(c):
    sayfa(c, 5, "Havalandırma prensip şeması",
          "Taze hava · egzoz · ıslak hacim egzozu — ölçeksiz, ortogonal")
    import draw_tesisat as T
    yy = TOP
    h.txt(c, L, yy-4*mm, "TAZE HAVA VE EGZOZ SİSTEMİ", h.FB, 8.5, h.NAVY)
    bx, by, bw, bh = L, BOT+4*mm, CW*0.66, TOP-14*mm-(BOT+4*mm)
    h.kutu(c, bx, by, bw, bh, HexColor("#FBFCFD"), h.GREY_L)

    def kanal_hat(pts, servis="HAVA", renk=None, kal=2.6*mm, etk=None):
        r = renk or T.C_HAVA
        c.saveState(); c.setStrokeColor(h.tint(r, 0.55)); c.setLineWidth(kal/mm*2.2)
        for a, b in zip(pts, pts[1:]):
            if abs(a[0]-b[0]) > 1e-9 and abs(a[1]-b[1]) > 1e-9: continue
            c.line(a[0], a[1], b[0], b[1])
        c.restoreState()
        c.saveState(); c.setStrokeColor(r); c.setLineWidth(0.6)
        for a, b in zip(pts, pts[1:]):
            if abs(a[0]-b[0]) > 1e-9 and abs(a[1]-b[1]) > 1e-9: continue
            c.line(a[0], a[1], b[0], b[1])
        c.restoreState()
        for a, b in zip(pts, pts[1:]):
            Lh = math.hypot(b[0]-a[0], b[1]-a[1])
            if Lh > 14*mm:
                T._ok(c, (a[0]+b[0])/2, (a[1]+b[1])/2,
                      math.atan2(b[1]-a[1], b[0]-a[0]), r, 3.0*mm, 1.1*mm)
        if etk:
            a, b = pts[0], pts[1]
            T.etiket(c, (a[0]+b[0])/2, (a[1]+b[1])/2, etk, r, 4.4, "c", 2.4*mm)

    # ── taze hava kolu (üst) ────────────────────────────────────────────────
    yT = by+bh-26*mm
    x0 = bx+16*mm
    T.etiket(c, x0, yT+8*mm, "DIŞ HAVA", T.INK, 5.0, "c", 0)
    c.setStrokeColor(T.INK); c.setLineWidth(0.7)
    for i in range(4):                                  # panjur
        c.line(x0-5*mm, yT-3*mm+i*2*mm, x0-1*mm, yT-1.2*mm+i*2*mm)
    c.rect(x0-5.6*mm, yT-4*mm, 5.2*mm, 9*mm, 1, 0)
    T.etiket(c, x0-3*mm, yT-7.5*mm, "TH panjur 500×300", T.GRI, 4.0, "c", 0)
    duraklar = [x0+30*mm, x0+62*mm, x0+96*mm, x0+132*mm, x0+168*mm]
    kanal_hat([(x0, yT), (duraklar[-1]+18*mm, yT)], etk="KANAL 500×150 · 1000 m³/h · AK +2,94")
    T.filtre(c, duraklar[0], yT, 9*mm, 11*mm, T.C_HAVA, "G4")
    T.susturucu(c, duraklar[1], yT, 13*mm, 11*mm, T.C_HAVA, "SUS 1000")
    T.fan_aksiyel(c, duraklar[2], yT, 3.2*mm, T.C_HAVA, "F-TH", "1000 m³/h · 250 Pa")
    T.damper(c, duraklar[3], yT, 3.0*mm, T.C_HAVA, "HKD")
    T.yangin_damperi(c, duraklar[4], yT, 7*mm, 11*mm, T.C_SS, "YD-90")
    # menfez kolları
    mx = duraklar[-1]+18*mm
    for i, m in enumerate([m for m in P.MENFEZ if m[4] == "besleme"]):
        xx = mx + i*0.0
        kanal_hat([(mx, yT), (mx, yT-10*mm-i*11*mm), (mx+22*mm, yT-10*mm-i*11*mm)], kal=1.6*mm)
        c.setFillColor(HexColor("#FFFFFF")); c.setStrokeColor(T.C_HAVA); c.setLineWidth(0.6)
        px = mx+22*mm; py = yT-10*mm-i*11*mm
        c.rect(px, py-2.6*mm, 5.2*mm, 5.2*mm, 1, 1)
        c.line(px, py-2.6*mm, px+5.2*mm, py+2.6*mm)
        c.line(px, py+2.6*mm, px+5.2*mm, py-2.6*mm)
        h.txt(c, px+7.2*mm, py-1.0*mm,
              f"{m[0]}  595×595 (b.Ø250)  {m[3]} m³/h  (besleme)", h.F, 4.6, T.C_HAVA)

    # ── egzoz kolu (alt) ────────────────────────────────────────────────────
    yE = by+bh*0.40
    C_EG = HexColor("#C8322B")
    kanal_hat([(x0, yE), (duraklar[-1]+18*mm, yE)], renk=C_EG, kal=2.2*mm,
              etk="KANAL 400×150 · 760 m³/h · AK +2,96")
    T.fan_aksiyel(c, duraklar[2], yE, 3.2*mm, C_EG, "F-EG", "760 m³/h · 200 Pa")
    T.damper(c, duraklar[3], yE, 3.0*mm, C_EG, "HKD")
    T.susturucu(c, duraklar[1], yE, 13*mm, 11*mm, C_EG, "SUS 1000")
    c.setStrokeColor(T.INK); c.setLineWidth(0.7)
    c.rect(x0-5.6*mm, yE-4*mm, 5.2*mm, 9*mm, 1, 0)
    for i in range(4): c.line(x0-5*mm, yE-3*mm+i*2*mm, x0-1*mm, yE-1.2*mm+i*2*mm)
    T.etiket(c, x0-3*mm, yE-7.5*mm, "EG panjur 400×300", T.GRI, 4.0, "c", 0)
    mxe = duraklar[-1]+18*mm
    for i, m in enumerate([m for m in P.MENFEZ if m[4] == "egzoz"]):
        kanal_hat([(mxe, yE), (mxe, yE-10*mm-i*11*mm), (mxe+22*mm, yE-10*mm-i*11*mm)],
                  kal=1.4*mm, renk=C_EG)
        px = mxe+22*mm; py = yE-10*mm-i*11*mm
        c.setFillColor(h.tint(C_EG, 0.78)); c.setStrokeColor(C_EG)
        c.setLineWidth(0.6); c.rect(px, py-2.6*mm, 5.2*mm, 5.2*mm, 1, 1)
        for k in range(3):
            c.line(px+0.6*mm, py-1.6*mm+k*1.6*mm, px+4.6*mm, py-1.6*mm+k*1.6*mm)
        h.txt(c, px+7.2*mm, py-1.0*mm, f"{m[0]}  495×195  {m[3]} m³/h  (egzoz)", h.F, 4.6, C_EG)
    # hacim kutusu
    c.setStrokeColor(T.GRI); c.setLineWidth(0.5); c.setDash([2.4, 1.8], 0)
    hx = mx+64*mm; hw = bw-(hx-bx)-6*mm
    c.rect(hx, yE-46*mm, hw, yT-yE+40*mm, 0, 0); c.setDash()
    h.txt(c, hx+hw/2, (yT+yE)/2, "SALON — kullanım hacmi", h.FB, 6.0, T.GRI, "c")

    # ── ıslak hacim egzozu ──────────────────────────────────────────────────
    yI = by+16*mm
    kanal_hat([(bx+16*mm, yI), (bx+bw-16*mm, yI)], renk=HexColor("#8E3BB0"), kal=1.6*mm,
              etk="Ø160 · 240 m³/h — ayrı fan, ayrı çıkış")
    T.fan_aksiyel(c, duraklar[2], yI, 2.6*mm, HexColor("#8E3BB0"), "F-IS", "240 m³/h")
    c.setStrokeColor(T.INK); c.setLineWidth(0.7)
    c.rect(bx+bw-16*mm, yI-4*mm, 5.2*mm, 9*mm, 1, 0)
    for i in range(4):
        c.line(bx+bw-15.4*mm, yI-3*mm+i*2*mm, bx+bw-11.4*mm, yI-1.2*mm+i*2*mm)
    T.etiket(c, bx+bw-13*mm, yI-7.5*mm, "EI çıkışı Ø160", T.GRI, 4.0, "c", 0)
    for i, m in enumerate([m for m in P.MENFEZ if m[4] == "valf"]):
        px = bx+30*mm+i*26*mm
        kanal_hat([(px, yI), (px, yI-9*mm)], kal=1.2*mm, renk=HexColor("#8E3BB0"))
        c.setFillColor(HexColor("#FFFFFF")); c.setStrokeColor(HexColor("#8E3BB0"))
        c.setLineWidth(0.6); c.circle(px, yI-11*mm, 2.2*mm, 1, 1)
        h.txt(c, px, yI-15.5*mm, f"{m[0]} {m[3]} m³/h", h.F, 4.2, HexColor("#8E3BB0"), "c")

    # ── sağ sütun: tasarım verileri ve lejant ───────────────────────────────
    x2 = bx+bw+7*mm; w2 = CW-bw-7*mm; ty = TOP
    h.txt(c, x2, ty-4*mm, "TASARIM VERİLERİ", h.FB, 8, h.NAVY)
    kisi = P.V["kisi_kapasite"][0]+P.V["personel"][0]
    _v = lambda x, n=1: ("%.*f" % (n, x)).replace(".", ",")
    rows = [["Tasarım kişi sayısı", f"{kisi} kişi", "12 üye + 2 personel"],
            ["Kişi başı taze hava", f"{1000/kisi:.0f} m³/h", "TS EN 16798-1 · asgari 30"],
            ["Salon hava değişimi", f"{_v(P.ACH,2)} 1/h", "asgari 2,0"],
            ["Besleme / egzoz dengesi", "1000 / 760 m³/h", "hafif pozitif basınç"],
            ["Islak hacim egzozu", f"{P.EGZOZ_ISLAK} m³/h", "2 WC + 2 duş · ayrı fan"],
            ["Ana kanal hızı", f"{_v(float(P.KANAL['besleme']['hiz']))} m/s", "sınır 6,0 m/s"],
            ["Kanal en/boy oranı", "500/150 = 1:3,3", "sınır 1:4 (TS 3419)"],
            ["Kanal yalıtımı", "25 mm kauçuk köpük", "tavan içi tüm hatlar"]]
    ty = h.tablo(c, x2, ty-7*mm, [("Kalem", 0.36), ("Değer", 0.26), ("Not", 0.38)],
                 rows, w2, satir_h=5.8*mm, fs=6.2, hizala=["l", "l", "l"])
    kalemler = [
      (lambda c_, x_, y_: T.filtre(c_, x_, y_, 7*mm, 6*mm, T.C_HAVA, ""), "Filtre (G4 / F7)"),
      (lambda c_, x_, y_: T.fan_aksiyel(c_, x_, y_, 2.0*mm, T.C_HAVA), "Aksiyel / kanal tipi fan"),
      (lambda c_, x_, y_: T.susturucu(c_, x_, y_, 8*mm, 6*mm, T.C_HAVA, ""), "Susturucu"),
      (lambda c_, x_, y_: T.damper(c_, x_, y_, 2.2*mm, T.C_HAVA, "HKD"), "Hacim kontrol damperi"),
      (lambda c_, x_, y_: T.yangin_damperi(c_, x_, y_, 6*mm, 6*mm, T.C_SS, ""), "Yangın damperi YD-90"),
      (lambda c_, x_, y_: T.kesme_vana(c_, x_, y_, 2.4*mm, T.C_TS), "Kesme vanası"),
      (lambda c_, x_, y_: T.kuresel_vana(c_, x_, y_, 2.4*mm, T.C_TS), "Küresel vana"),
      (lambda c_, x_, y_: T.cekvalf(c_, x_, y_, 2.4*mm, T.C_TS), "Çekvalf"),
      (lambda c_, x_, y_: T.pislik_tutucu(c_, x_, y_, 2.2*mm, T.C_TS, ""), "Pislik tutucu"),
      (lambda c_, x_, y_: T.termometre(c_, x_, y_-2*mm, 2.2*mm), "Termometre"),
      (lambda c_, x_, y_: T.manometre(c_, x_, y_-2*mm, 2.2*mm), "Manometre"),
      (lambda c_, x_, y_: T.yer_suzgeci(c_, x_, y_, 2.2*mm, T.C_PS, ""), "Yer süzgeci"),
    ]
    ty = T.lejant(c, x2, ty-9*mm, w2, kalemler, sut=2)
    h.notkutu(c, x2, ty, w2, "Şema okuma kuralı",
      "Prensip şeması ölçekli değildir; hatlar yalnız yatay ve düşeydir. Her hat üzerinde "
      "akış yönü oku, kesit ve debi yazılıdır. Islak hacim egzozu salon egzozuna "
      "bağlanmaz — ayrı fan, ayrı kanal, ayrı çıkış. Kanalın yangın bölmesi geçtiği "
      "her noktaya YD-90 yangın damperi konur (BYKHY).", fs=6.2, acc=h.NAVY2)


# ══ 6 · SIHHİ TESİSAT KOLON ŞEMASI ════════════════════════════════════════════
def s6(c):
    sayfa(c, 6, "Sıhhi tesisat kolon şeması",
          "Düşey ölçüler ölçekli (1/50) · yatay ölçüler ölçeksiz")
    import draw_tesisat as T
    yy = TOP
    # düşey ölçek: 1/50 → 1 m = 20 mm kâğıt
    OLC = 38*mm                       # 1 m = 38 mm kâğıt (≈1/26 düşey)
    ZEM = BOT + 50*mm                 # ±0,00 bitmiş döşeme
    def K(kot): return ZEM + kot*OLC   # metre kotundan kâğıt y'sine

    bx, bw = L, CW*0.70
    h.kutu(c, bx, ZEM-26*mm, bw, TOP-4*mm-(ZEM-26*mm), HexColor("#FBFCFD"), h.GREY_L)
    # — döşeme: iki paralel çizgi (döşeme üstü ve altı)
    c.setStrokeColor(T.INK); c.setLineWidth(1.0)
    c.line(bx+6*mm, K(0.0), bx+bw-6*mm, K(0.0))
    c.setLineWidth(0.6); c.line(bx+6*mm, K(-0.20), bx+bw-6*mm, K(-0.20))
    c.setFillColor(HexColor("#E3E7EA"))
    c.rect(bx+6*mm, K(-0.20), bw-12*mm, 0.20*OLC, 0, 1)
    c.setStrokeColor(T.INK); c.setLineWidth(1.0)
    c.line(bx+6*mm, K(0.0), bx+bw-6*mm, K(0.0))
    h.txt(c, bx+7*mm, K(0.0)+1.4*mm, "ZEMİN KAT — BİTMİŞ DÖŞEME ±0,00", h.FB, 5.4, T.INK)
    h.txt(c, bx+7*mm, K(-0.20)-3.4*mm, "Mevcut betonarme döşeme (200 mm) — VARSAYIM",
          h.F, 4.6, T.GRI)
    # — yapısal tavan ve çatı
    c.setStrokeColor(T.GRI); c.setLineWidth(0.7); c.setDash([3, 2], 0)
    c.line(bx+6*mm, K(P.KOT_YAPISAL_TAVAN), bx+bw-6*mm, K(P.KOT_YAPISAL_TAVAN))
    c.setDash()
    h.txt(c, bx+7*mm, K(P.KOT_YAPISAL_TAVAN)+1.2*mm,
          f"YAPISAL TAVAN +{('%.2f' % P.KOT_YAPISAL_TAVAN).replace('.', ',')}",
          h.F, 4.8, T.GRI)

    # — kolon aksları (yatay ölçeksiz, eşit adım)
    kolonlar = [
      ("TK-1", "Temiz su kolonu — erkek bloğu", "TS", "Ø25"),
      ("SK-1", "Sıcak su kolonu — erkek bloğu", "SS", "Ø20"),
      ("PK-1", "Pis su kolonu — erkek bloğu",   "PS", "Ø100"),
      ("HK-1", "Havalık — erkek bloğu",         "HV", "Ø70"),
      ("TK-2", "Temiz su kolonu — kadın bloğu", "TS", "Ø25"),
      ("SK-2", "Sıcak su kolonu — kadın bloğu", "SS", "Ø20"),
      ("PK-2", "Pis su kolonu — kadın bloğu",   "PS", "Ø100"),
      ("HK-2", "Havalık — kadın bloğu",         "HV", "Ø70"),
    ]
    x0 = bx + 48*mm; adim = (bw - 62*mm)/len(kolonlar)
    # ana yatay hatlar
    ANA_TS = K(2.60); ANA_PS = K(-0.12)
    T.boru(c, [(bx+14*mm, ANA_TS), (x0+adim*(len(kolonlar)-1), ANA_TS)], "TS")
    T.etiket(c, bx+30*mm, ANA_TS, "TS Ø25 — tavan içi ana dağıtım", T.C_TS, 4.4, "l", 1.8*mm)
    T.boru(c, [(bx+14*mm, ANA_PS), (x0+adim*(len(kolonlar)-1), ANA_PS)], "PS")
    T.etiket(c, bx+30*mm, ANA_PS, "PS Ø100 %1 ↓ — zemin içi toplama",
             T.C_PS, 4.4, "l", -4.2*mm)
    # su girişi ve sayaç
    T.boru(c, [(bx+14*mm, K(0.90)), (bx+14*mm, ANA_TS)], "TS")
    T.sayac(c, bx+14*mm, K(1.55), 2.6*mm, T.C_TS, None)
    T.etiket(c, bx+14*mm, K(1.55), "SU SAYACI", T.C_TS, 4.0, "l", 0)
    T.kuresel_vana(c, bx+14*mm, K(1.05), 2.4*mm, T.C_TS, True, None)
    T.etiket(c, bx+14*mm+4*mm, K(1.05), "ANA KESME", T.C_TS, 4.0, "l", 0)
    T.boru(c, [(bx+14*mm, K(0.55)), (bx+14*mm, K(0.90))], "TS")
    T.etiket(c, bx+18*mm, K(0.55), "ŞEBEKE GİRİŞİ Ø25", T.C_TS, 4.2, "l", 0)
    # rögar
    c.setFillColor(HexColor("#FFFFFF")); c.setStrokeColor(T.C_PS); c.setLineWidth(0.8)
    rx = x0+adim*(len(kolonlar)-1)+6*mm
    c.rect(rx-5*mm, ANA_PS-7*mm, 10*mm, 10*mm, 1, 1)
    T.etiket(c, rx, ANA_PS-10.5*mm, "RÖGAR 50×50", T.C_PS, 4.2, "c", 0)
    T.boru(c, [(x0+adim*(len(kolonlar)-1), ANA_PS), (rx-5*mm, ANA_PS)], "PS")

    # cihaz montaj kotları (m) — TS uygulama pratiği
    CIHAZ = {"lavabo": 0.85, "klozet": 0.20, "rezervuar": 0.25, "dus": 2.10,
             "suzgec": 0.00, "boyler": 1.90}
    for i, (kod, ad, servis, cap) in enumerate(kolonlar):
        x = x0 + i*adim
        # kolon gövdesi
        if servis == "PS":
            T.boru(c, [(x, K(1.05)), (x, ANA_PS)], "PS")
            T.temizleme_kapagi(c, x, K(0.25), 2.2*mm)
            T.etiket(c, x, K(0.70), f"{cap} %1", T.C_PS, 4.0, "c", 0)
            # klozet + lavabo bağlantısı
            # klozet (çıkış 20 cm) ve lavabo (85 cm) bağlantıları
            T.boru(c, [(x-20*mm, K(CIHAZ['klozet'])), (x-20*mm, K(1.05)), (x, K(1.05))], "PS")
            T.boru(c, [(x-11*mm, K(CIHAZ['lavabo'])), (x-11*mm, K(1.05))], "PS")
            c.setFillColor(HexColor("#FFFFFF")); c.setStrokeColor(T.C_PS); c.setLineWidth(0.7)
            # klozet gövdesi
            c.roundRect(x-23*mm, K(CIHAZ['klozet']), 6*mm, 9*mm, 1.2*mm, 1, 1)
            c.rect(x-23*mm, K(CIHAZ['klozet'])+9*mm, 6*mm, 5*mm, 1, 1)
            T.etiket(c, x-20*mm, K(CIHAZ['klozet'])+14*mm, "WC", T.C_PS, 4.0, "c", 0.6*mm)
            # lavabo
            c.ellipse(x-14.5*mm, K(CIHAZ['lavabo']), x-7.5*mm, K(CIHAZ['lavabo'])+3.4*mm, 1, 1)
            T.etiket(c, x-11*mm, K(CIHAZ['lavabo'])+3.6*mm, "LV h=0,85", T.C_PS, 4.0, "c", 0.6*mm)
            T.yer_suzgeci(c, x-4*mm, K(0.06), 2.2*mm, T.C_PS, "YS Ø100")
        elif servis == "HV":
            # havalık, komşu pis su kolonundan ayrılır (2×45° yerine ortogonal şema)
            T.boru(c, [(x-adim, K(1.05)), (x, K(1.05)),
                       (x, K(P.KOT_YAPISAL_TAVAN+0.45))], "HV")
            T.havalik_bacasi(c, x, K(P.KOT_YAPISAL_TAVAN+0.45), 2.6*mm)
            T.etiket(c, x, K(P.KOT_YAPISAL_TAVAN+0.45), "ÇATI ÜSTÜ +2,00 m",
                     T.C_HV, 4.0, "c", 3.2*mm)
        elif servis == "TS":
            T.boru(c, [(x, ANA_TS), (x, K(CIHAZ['lavabo']))], "TS")
            T.kuresel_vana(c, x, K(2.20), 2.2*mm, T.C_TS, True)
            T.etiket(c, x, K(1.60), f"{cap} · 12 MB", T.C_TS, 4.0, "c", 0)
            # boyler
            if kod.endswith("1") or kod.endswith("2"):
                pass
        else:   # SS
            T.boru(c, [(x, K(CIHAZ['boyler'])), (x, K(CIHAZ['dus']))], "SS")
            T.boru(c, [(x, K(CIHAZ['dus'])), (x+12*mm, K(CIHAZ['dus']))], "SS")
            T.boyler(c, x-13*mm, K(1.45), 11*mm, 20*mm, T.C_SS,
                     "BOYLER 100 L / 3 kW")
            T.emniyet_ventili(c, x-13*mm, K(2.10), 2.2*mm, T.C_SS, "EV 6 bar")
            T.etiket(c, x, K(1.20), f"{cap}", T.C_SS, 4.0, "c", 0)
            # duş başlığı
            c.setStrokeColor(T.C_SS); c.setLineWidth(0.8)
            c.line(x+12*mm, K(CIHAZ['dus']), x+12*mm, K(CIHAZ['dus'])-2*mm)
            c.line(x+9*mm, K(CIHAZ['dus'])-2*mm, x+15*mm, K(CIHAZ['dus'])-2*mm)
            T.etiket(c, x+12*mm, K(CIHAZ['dus'])-5.5*mm, "DUŞ h=2,10", T.C_SS, 4.0, "c", 0)
        # kolon numarası — kolonun EN ÜST noktasında
        ust = K(P.KOT_YAPISAL_TAVAN+0.62) if servis == "HV" else K(2.85)
        c.setFillColor(HexColor("#FFFFFF"))
        renk = T.CIZGI[servis][0]
        c.setStrokeColor(renk); c.setLineWidth(0.7)
        c.circle(x, ust+5*mm, 3.4*mm, 1, 1)
        h.txt(c, x, ust+4.0*mm, kod, h.FB, 4.2, renk, "c")

    # — düşey kot ölçü zinciri (solda)
    ox = bx+7.5*mm
    kotlar = [(-0.20, "kaba döşeme"), (0.00, "bitmiş döşeme"),
              (0.85, "lavabo"), (1.90, "boyler"), (2.10, "duş başlığı"),
              (2.60, "TS ana dağıtım"), (P.KOT_YAPISAL_TAVAN, "yapısal tavan")]
    c.setStrokeColor(T.GRI); c.setLineWidth(0.4)
    c.line(ox, K(-0.20), ox, K(P.KOT_YAPISAL_TAVAN))
    for kot, ad in kotlar:
        c.line(ox-1.4*mm, K(kot), ox+1.4*mm, K(kot))
        h.txt(c, ox-2.2*mm, K(kot)-1.0*mm,
              f"{'+' if kot >= 0 else '−'}{abs(kot):.2f}".replace(".", ","),
              h.FB, 4.2, T.GRI, "r")
        h.txt(c, ox+2.4*mm, K(kot)-1.0*mm, ad, h.F, 4.0, T.GRI)

    # — sağ sütun ────────────────────────────────────────────────────────────
    x2 = bx+bw+7*mm; w2 = CW-bw-7*mm; ty = TOP
    _v = lambda x, n=1: ("%.*f" % (n, x)).replace(".", ",")
    h.txt(c, x2, ty-4*mm, "KOLON LİSTESİ", h.FB, 8, h.NAVY)
    rows = [[k[0], k[1], k[3]] for k in kolonlar]
    ty = h.tablo(c, x2, ty-7*mm, [("Kolon", 0.16), ("Tanım", 0.62), ("Çap", 0.22)],
                 rows, w2, satir_h=5.6*mm, fs=6.1, hizala=["c", "l", "c"])
    h.txt(c, x2, ty-8*mm, "EĞİM VE ÇAP KURALI", h.FB, 8, h.NAVY)
    rows2 = [["Ø50 (lavabo, duş)", "%2", "sifon birimi 1–2 SB"],
             ["Ø70 (ara toplama)", "%2", "3–6 SB"],
             ["Ø100 (klozet, ana hat)", "%1", "≥ 8 SB · rögara kadar"],
             ["Havalık Ø70", "—", "çatı üstü +2,00 m, şapkalı"],
             ["Temizleme kapağı TK", "—", "her kolon dibinde + her 15 m'de"],
             ["Rögar", "—", "50×50 cm, düz hatta her 30 m"]]
    ty = h.tablo(c, x2, ty-12*mm, [("Hat", 0.44), ("Eğim", 0.16), ("Not", 0.40)],
                 rows2, w2, satir_h=5.6*mm, fs=6.1, hizala=["l", "c", "l"])
    h.txt(c, x2, ty-8*mm, "MONTAJ KOTLARI (bitmiş döşemeden)", h.FB, 8, h.NAVY)
    rows3 = [["Lavabo üst kenarı", "85 cm"], ["Lavabo bataryası", "100 cm"],
             ["Klozet çıkışı", "15–20 cm"], ["Rezervuar bağlantısı", "25 cm"],
             ["Duş bataryası", "100 cm"], ["Duş başlığı", "210 cm"],
             ["Boyler alt kenarı", "190 cm"], ["Yer süzgeci", "±0,00 (−1,5 cm çukur)"]]
    ty = h.tablo(c, x2, ty-12*mm, [("Cihaz", 0.62), ("Kot", 0.38)], rows3,
                 w2, satir_h=5.4*mm, fs=6.1, hizala=["l", "r"])
    h.notkutu(c, x2, ty-6*mm, w2, "Şemanın ölçek kuralı",
      "Kolon şeması bir DÜŞEY KESİTTİR: düşey ölçüler 1/50 ölçeklidir ve kotlar "
      "gerçektir; yatay ölçüler ölçeksizdir, kolonlar eşit adımla yan yana dizilir. "
      "Pis su kolonu önce, temiz su kolonu sonra çizilir. Kolon numarası her kolonun "
      "en üst noktasına yazılır. Yatay–düşey geçişler 2 × 45° dirsekle yapılır, "
      "tek 90° dirsekle değil.", fs=6.1, acc=h.NAVY2)


# ══ 7 · İKLİMLENDİRME PRENSİP ŞEMASI ══════════════════════════════════════════
def s7(c):
    sayfa(c, 7, "İklimlendirme prensip şeması",
          "Split küme · soğutucu akışkan hatları · kondens drenajı")
    import draw_tesisat as T
    bx, bw = L, CW*0.62
    h.kutu(c, bx, BOT+4*mm, bw, TOP-BOT-10*mm, HexColor("#FBFCFD"), h.GREY_L)
    dx = bx+34*mm
    dy = TOP-30*mm
    T.klima_dis(c, dx, dy, 44*mm, 20*mm, T.C_SAG, "DIŞ ÜNİTE PLATFORMU — arka cephe")
    T.etiket(c, dx, dy-13.5*mm, f"{P.ADET_KLIMA} adet · toplam {h.tl(P.KLIMA_BTU)} BTU",
             T.GRI, 4.4)
    kolon_x = dx
    alt = dy-24*mm
    T.boru(c, [(kolon_x, dy-10*mm), (kolon_x, alt)], "SA-G")
    for i, (kod, zon, btu, pt, a) in enumerate(P.KLIMA):
        yk = alt - 6*mm - i*24*mm
        ic_x = bx+bw-52*mm
        T.boru(c, [(kolon_x, yk+8*mm), (kolon_x, yk), (ic_x-16*mm, yk)], "SA-G")
        T.boru(c, [(kolon_x+3*mm, yk+8*mm), (kolon_x+3*mm, yk-3*mm),
                   (ic_x-16*mm, yk-3*mm)], "SA-S")
        T.klima_ic(c, ic_x, yk, 26*mm, 9*mm, T.C_SAG, kod,
                   f"{h.tl(btu)} BTU · {zon.split(' · ')[0].title()}")
        L_b = __import__("shapely.geometry", fromlist=["LineString"]).LineString(
            P.BAKIR_HAT[kod]).length
        T.etiket(c, (kolon_x+ic_x)/2-8*mm, yk, f"Ø9,52 / Ø15,88 (S/G) · {L_b:.1f} m",
                 T.C_SAG, 4.2, "c", 1.8*mm)
        # kondens drenajı
        T.boru(c, [(ic_x, yk-4.5*mm), (ic_x, yk-10*mm), (kolon_x-10*mm, yk-10*mm)], "DR")
        T.etiket(c, ic_x-24*mm, yk-10*mm, "DR Ø25 %1 ↓", T.C_DR, 4.0, "c", -4.0*mm)
    T.boru(c, [(kolon_x-10*mm, alt-6*mm-3*24*mm-10*mm), (kolon_x-10*mm, BOT+16*mm),
               (bx+bw-16*mm, BOT+16*mm)], "DR")
    T.etiket(c, bx+bw-40*mm, BOT+16*mm, "Kondens toplama → yer süzgeci", T.C_DR, 4.4,
             "c", 2.0*mm)
    T.yer_suzgeci(c, bx+bw-14*mm, BOT+16*mm, 2.6*mm, T.C_PS, "")

    x2 = bx+bw+7*mm; w2 = CW-bw-7*mm; ty = TOP
    _v = lambda x, n=1: ("%.*f" % (n, x)).replace(".", ",")
    h.txt(c, x2, ty-4*mm, "İÇ ÜNİTE LİSTESİ", h.FB, 8, h.NAVY)
    zon_alan = {z[0]: z[1].area for z in P.ZONES}
    rows = []
    for kod, zon, btu, pt, a in P.KLIMA:
        alan = zon_alan.get(zon, 0)
        rows.append([kod, zon.split(" · ")[0].title(), f"{h.tl(btu)} BTU",
                     f"{_v(alan)} m²", f"{btu*0.293/alan:.0f} W/m²" if alan else "—"])
    ty = h.tablo(c, x2, ty-7*mm, [("Kod", 0.12), ("Bölge", 0.34), ("Kapasite", 0.20),
                                  ("Alan", 0.16), ("Yük", 0.18)],
                 rows, w2, satir_h=5.8*mm, fs=6.2, hizala=["c", "l", "r", "r", "r"])
    h.txt(c, x2, ty-8*mm, "HAT VE MONTAJ VERİLERİ", h.FB, 8, h.NAVY)
    rows2 = [["Toplam bakır hat", f"{_v(P.L_BAKIR)} m", "gaz + sıvı, yalıtımlı"],
             ["Toplam drenaj hattı", f"{_v(P.L_DRENAJ)} m", "%1 eğim, yalıtımlı"],
             ["En uzun bakır hat", f"{max(__import__('shapely.geometry', fromlist=['LineString']).LineString(hh).length for hh in P.BAKIR_HAT.values()):.1f} m",
              "sınır 50 m · 30 m üstü ilave şarj"],
             ["İç ünite kotu", f"{_v(P.KLIMA_KOT,2)} m", "üst kot +2,72 m"],
             ["Dış ünite servis boşluğu", "1,00 m", "ön yüz, taranmış alan"],
             ["Soğutma marjı", f"%{P.SOGUTMA_MARJ}", "tepe yük üzerine"]]
    ty = h.tablo(c, x2, ty-12*mm, [("Kalem", 0.40), ("Değer", 0.24), ("Not", 0.36)],
                 rows2, w2, satir_h=5.8*mm, fs=6.2, hizala=["l", "r", "l"])
    h.notkutu(c, x2, ty-6*mm, w2, "Kondens drenajı kritik",
      "Her iç ünitenin kondens hattı kesintisiz %1 eğimle yer süzgecine iner; "
      "eğim sağlanamayan noktada kondens pompası kullanılır. Drenaj hattı yalıtımlı "
      "olacak, asma tavan içinde terleme yapmayacaktır. Hat, asma tavan kapatılmadan "
      "önce su ile test edilip fotoğraflanacaktır.", fs=6.2, acc=h.COPPER)


# ══ 6 · METRAJ ÖZETİ VE LEJANT ═════════════════════════════════════════════════
def s8(c):
    sayfa(c, 8, "Metraj özeti ve lejant", "Poz bazlı miktarlar · semboller · teslim kriterleri")
    mek = [r for r in P.B if r[1] == "MEKANİK"]
    tw_ = CW*0.62
    rows = [[r[0], r[2], r[3], f"{r[4]:.2f}".replace(".", ","),
             "alternatif" if r[7] == "—" else ("önerilen" if r[7] == "O" else "zorunlu")]
            for r in mek]
    yy = h.tablo(c, L, TOP, [("Poz", 0.07), ("Tanım", 0.55), ("Birim", 0.09),
                             ("Miktar", 0.13), ("Kapsam", 0.16)],
                 rows, tw_, satir_h=5.4*mm, fs=6.0, hfs=6.2, hizala=["c", "l", "c", "r", "c"])
    m = P.maliyet("O", "A")
    lo, hi = m["gruplar"]["MEKANİK"]
    h.txt(c, L, yy-7*mm, f"MEKANİK İMALAT TOPLAMI (önerilen senaryo):  {h.bant(lo, hi)}",
          h.FB, 8, h.NAVY)
    h.txt(c, L, yy-13*mm, "Birim fiyat sütunları boş .xlsx dosyası: output/Gym_Mekanik_BoQ.xlsx — "
          "teklif geldikçe doldurulur, toplamlar kendiliğinden döner.", h.F, 6.4, h.GREY)
    x2 = L+tw_+7*mm; w2 = CW-tw_-7*mm
    h.txt(c, x2, TOP-4*mm, "LEJANT", h.FB, 8.5, h.NAVY)
    vv = D.View(c, x2, TOP-120*mm, w2, 112*mm)
    import shapely.geometry as _g
    def _mini(fn):
        return lambda cc, xx, yyy: fn(cc, xx, yyy)
    cy = TOP-12*mm
    kalem = [
      (M.C_BESLEME, "Taze hava kanalı — 500×150"),
      (M.C_EGZOZ,   "Egzoz kanalı — 400×150"),
      (M.C_ISLAK,   "Islak hacim egzozu — Ø160"),
      (M.C_KLIMA,   "Soğutucu akışkan bakır hattı"),
      (M.C_DRENAJ,  "Klima drenaj hattı"),
      (M.C_SOGUK,   "Temiz su — PPRC Ø25 / Ø20"),
      (M.C_SICAK,   "Sıcak su — PPRC Ø20 izoleli"),
      (M.C_PIS,     "Pis su — PVC Ø100 / Ø70 / Ø50"),
    ]
    for col, t in kalem:
        c.setFillColor(col); c.rect(x2, cy-0.8*mm, 7*mm, 2.6*mm, 0, 1)
        h.txt(c, x2+10*mm, cy, t, h.F, 6.3, h.INK); cy -= 7.2*mm
    cy -= 2*mm
    sem = [("besleme", "Besleme menfezi 300×150"), ("egzoz", "Egzoz menfezi 300×150"),
           ("valf", "Tavan egzoz valfi Ø160")]
    vtmp = D.View(c, x2, cy-30*mm, w2, 30*mm)
    for i, (tip, t) in enumerate(sem):
        px, py = x2+3.5*mm, cy-1.0*mm
        col = {"besleme": M.C_BESLEME, "egzoz": M.C_EGZOZ, "valf": M.C_ISLAK}[tip]
        c.setFillColor(HexColor("#FFFFFF")); c.setStrokeColor(col); c.setLineWidth(0.8)
        if tip == "valf":
            c.circle(px, py+1.0*mm, 1.4*mm, 1, 1)
        else:
            c.rect(px-1.8*mm, py, 3.6*mm, 2.2*mm, 1, 1)
        h.txt(c, x2+10*mm, cy, t, h.F, 6.3, h.INK); cy -= 7.2*mm
    for t in ["Kanal tipi fan (F-TH / F-EG / F-IS)", "Split klima iç ünitesi (K1–K4)",
              "Elektrikli ani su ısıtıcı (SI-1 / SI-2)"]:
        c.setFillColor(h.NAVY2); c.roundRect(x2, cy-0.9*mm, 7*mm, 3.0*mm, 0.6*mm, 0, 1)
        h.txt(c, x2+10*mm, cy, t, h.F, 6.3, h.INK); cy -= 7.2*mm
    cy = h.notkutu(c, x2, cy-4*mm, w2, "Teslim kriterleri",
      "Hava debisi ölçümü (tasarım debisinin ±%10'u içinde), tesisat basınç testi, drenaj akış "
      "kontrolü, klima performans testi ve gaz şarj kaydı. Tüm ölçümler tutanakla belgelenip "
      "işverene teslim edilecektir; bu tutanaklar GSİM komisyon tetkikinde işverenin lehine kanıttır.",
      fs=6.3, acc=h.COPPER)
    h.notkutu(c, x2, cy-4*mm, w2, "Ölçü dayanağı",
      "Geometri, alan dağılımı paftasından renk maskesiyle vektörleştirilmiş ve paftanın kendi m² "
      "etiketleriyle kalibre edilmiştir (±%3). Kanal ve boru güzergâhları bu altlık üzerinde "
      "kurulmuştur; uygulama öncesi DXF (R2010) ile yeniden kontrol edilmelidir.",
      fs=6.3, acc=h.NAVY2)

# ══ 7 · TAVAN İÇİ TESİSAT KOORDİNASYON KESİTİ ═════════════════════════════════
KAT_RENK = {"yapi":"#C9CCD1", "kanal":"#2E7D5B", "boru":"#1F8AA8", "kablo":"#1F6FB2",
            "zayif":"#7B3FA0", "su":"#2F6FB3", "tavan":"#B87333"}
def s9(c):
    sayfa(c, 9, "Tavan içi tesisat koordinasyon kesiti",
          "Kanal · boru · kablo tavası kot dizilimi · çakışma kuralları")
    y = TOP
    y = h.para(c, L, y-1*mm,
      "Bu pafta, asma tavan ile yapısal döşeme arasındaki boşlukta her disiplinin hangi kotta geçeceğini "
      "belirler. Mekanik, elektrik ve mimari paftalar aynı geometrik kaynaktan üretildiği için plan "
      "üzerindeki çakışmalar otomatik denetlenmiştir (tools/kontrol.py); bu kesit ise düşey çakışmayı, "
      "yani aynı noktada üst üste geçen elemanların kot sırasını tanımlar. Yapısal döşeme altı kotu "
      "VARSAYIMDIR (+3,20); söküm sonrası yerinde ölçülecek ve tüm kotlar tek yerden güncellenecektir.",
      CW, h.F, 7.8, h.INK, 10.8)

    # ── kesit çizimi: tam genişlik, alçak kutu ────────────────────────────────
    ch = 88*mm; cy0 = y-4*mm-ch
    h.kutu(c, L, cy0, CW, ch, HexColor("#FFFFFF"), h.GREY_L, 0.6)
    h.txt(c, L+4*mm, cy0+ch-5.4*mm, "TAVAN İÇİ KOT DİZİLİMİ  ·  şematik kesit (ölçeksiz, düşey ölçek büyütülmüş)",
          h.FB, 6.8, h.NAVY)
    v = MM.KV(c, L, cy0, CW, ch-7*mm, 0.0, 6.0, 2.26, 3.46, pad=10*mm)
    MM.kutu(v, 0.15, 3.20, 5.85, 3.40, "beton")
    MM.kutu(v, 0.15, 2.32, 0.35, 3.20, "beton")
    MM.kutu(v, 5.65, 2.32, 5.85, 3.20, "beton")
    MM.kutu(v, 0.35, 2.80, 3.60, 2.8145, "alcipan")
    MM.kutu(v, 3.72, 2.40, 5.65, 2.4145, "alcipan")
    MM.cizgi(v, (3.66, 2.40), (3.66, 2.8145), h.INK, 1.0)
    MM.kot(v, 0.95, 2.80, "+2,80  T2 asma tavan", 1)
    MM.kot(v, 4.35, 2.40, "+2,40  T3 asma tavan", 1)
    MM.kot(v, 5.55, 3.20, "+3,20  yapısal döşeme altı", -1)
    ogeler = [
      (1, 0.70, 2.94, 1.30, 3.14, "kanal", "Dikdörtgen hava kanalı 400×200 mm — taze hava beslemesi"),
      (2, 1.70, 2.94, 2.30, 3.14, "kanal", "Dikdörtgen hava kanalı 400×200 mm — egzoz"),
      (3, 2.58, 2.86, 2.70, 2.92, "boru",  "Soğutucu akışkan bakır hattı + klima drenajı (%1 eğim)"),
      (4, 2.92, 2.80, 3.32, 2.85, "kablo", "Kablo tavası 200×60 mm — kuvvet ve aydınlatma"),
      (5, 3.40, 2.74, 3.58, 2.79, "zayif", "Zayıf akım kanalı 100×50 mm — kuvvetten ≥ 200 mm ayrık"),
      (6, 4.05, 2.94, 4.45, 3.14, "kanal", "Islak hacim egzoz kanalı Ø160 mm"),
      (7, 4.70, 2.68, 4.82, 2.74, "su",    "Temiz su PPRC Ø25 + pis su Ø50–70 (%2 eğim)"),
      (8, 5.05, 2.80, 5.35, 2.85, "kablo", "Kablo tavası — ıslak blok kolu"),
    ]
    for no, s0, z0, s1, z1, tip, ad in ogeler:
        col = HexColor(KAT_RENK[tip])
        MM.gorunus_kutu(v, s0, z0, s1, z1, fill=h.tint(col, 0.50), kontur=col, lw=1.0)
        px, py = v.p((s0+s1)/2, z1)
        MM.balon(c, px, py+4.6*mm, str(no), r=2.4*mm, dolgu="#FFFFFF", kontur="#16273D", fs=5.0)
        c.saveState(); c.setStrokeColor(HexColor("#6B7078")); c.setLineWidth(0.4)
        c.line(px, py, px, py+2.2*mm); c.restoreState()
    for sx in (1.50, 3.05, 4.55):
        MM.cizgi(v, (sx, 3.20), (sx, 2.8145 if sx < 3.66 else 2.4145), HexColor("#6B7078"), 0.8)
    h.lejant(c, L+5*mm, cy0+3.5*mm, [(HexColor(KAT_RENK["kanal"]), "Hava kanalı"),
        (HexColor(KAT_RENK["boru"]), "Soğutucu + drenaj"), (HexColor(KAT_RENK["su"]), "Temiz / pis su"),
        (HexColor(KAT_RENK["kablo"]), "Kuvvet tavası"), (HexColor(KAT_RENK["zayif"]), "Zayıf akım"),
        (HexColor("#6B7078"), "Bağımsız askı çubuğu")], 6.0)

    # ── alt: kot tablosu + kurallar (iki sütun) ───────────────────────────────
    ay = cy0-6*mm; w1 = CW*0.455; x2 = L+w1+8*mm; w2 = CW-w1-8*mm
    h.txt(c, L, ay, h.TR_UP("Tavan içi kot dizilimi"), h.FB, 8.2, h.NAVY)
    _no = {ad: no for no, s0, z0, s1, z1, tip, ad in ogeler}
    rows = []
    for no, s0, z0, s1, z1, tip, ad in ogeler:
        rows.append([str(no), ("%.2f" % z1).replace(".", ","), ("%.2f" % z0).replace(".", ","), ad])
    rows += [["—", "3,20", "3,20", "Mevcut yapısal döşeme altı (VARSAYIM — yerinde ölçülecek)"],
             ["—", "2,68", "2,62", "Asma tavan askı ve taşıyıcı profil bölgesi"],
             ["—", "2,80", "2,80", "T2 asma tavan bitmiş yüzeyi (giriş · dinlenme)"],
             ["—", "2,60", "2,60", "T4 asma tavan bitmiş yüzeyi (soyunma)"],
             ["—", "2,40", "2,40", "T3 asma tavan bitmiş yüzeyi (duş · WC)"]]
    h.tablo(c, L, ay-5*mm, [("No",0.08),("Üst kot",0.14),("Alt kot",0.14),("Eleman",0.64)], rows, w1,
            satir_h=5.4*mm, bas_h=6.4*mm, fs=6.1, hfs=6.0, hizala=["c","r","r","l"])
    h.txt(c, x2, ay, h.TR_UP("Koordinasyon kuralları"), h.FB, 8.2, h.NAVY)
    yy2 = h.tablo(c, x2, ay-5*mm, [("Kural",0.24),("Açıklama",0.76)],
                  [[k[0], k[1]] for k in P.TAVAN_KOORD], w2,
                  satir_h=5.6*mm, bas_h=6.4*mm, fs=6.1, hfs=6.0, hizala=["l","l"])
    h.notkutu(c, x2, yy2-5*mm, w2, "Uygulama sırası",
      "1) Yapısal döşeme altı kotu ölçülür ve tüm kotlar revize edilir.  2) Hava kanalı askılanır.  "
      "3) Eğimli hatlar (pis su, klima drenajı) çekilir ve eğimi tutanakla ölçülür.  4) Kablo tavası "
      "ve zayıf akım kanalı çekilir.  5) Temiz su ve bakır hatlar döşenir, basınç testi yapılır.  "
      "6) Asma tavan karkası kurulur.  7) Alçıpan kapatılmadan ÖNCE tüm tesisat fotoğraflanır ve "
      "işverene teslim edilir — sonradan açmanın maliyeti yüksektir.", fs=6.3, acc=h.COPPER)

def build(path="output/Gym_Mekanik_Proje_A3.pdf"):
    c = canvas.Canvas(path, pagesize=(W, HH))
    c.setTitle(f"Maltepe / İdealtepe — Mekanik Tesisat Projesi ({P.REV})")
    for fn in (s1, s2, s3, s4, s5, s6, s7, s8, s9):
        fn(c); c.showPage()
    c.save(); print("→", path)

if __name__ == "__main__":
    build()
