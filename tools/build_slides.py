# -*- coding: utf-8 -*-
"""Sunum — 16:9, 12 slayt, telefon/laptop gösterimi için büyük punto."""
import sys, os, math, glob
sys.path.insert(0, os.path.dirname(__file__))
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from shapely.ops import unary_union
import proj as P, helpers as h, draw as D

W, HH = 338.67*mm, 190.5*mm
L, R  = 18*mm, W-18*mm
CW    = R-L
TOP   = HH-34*mm
BOT   = 14*mm
N     = 12
BG    = HexColor("#0E1620")

def bas(c, no, ust, baslik, koyu=True):
    c.setFillColor(BG if koyu else HexColor("#FBFAF8")); c.rect(0,0,W,HH,0,1)
    c.setFillColor(h.COPPER); c.rect(0, HH-4.2*mm, W, 4.2*mm, 0, 1)
    ink = HexColor("#FFFFFF") if koyu else h.NAVY
    h.txt(c, L, HH-15*mm, h.TR_UP(ust), h.FB, 8, h.COPPER)
    h.txt(c, L, HH-26*mm, baslik, h.FB, 19, ink)
    h.txt(c, R, HH-15*mm, f"{no:02d} / {N}", h.FB, 8,
          HexColor("#7B93AC") if koyu else h.GREY, "r")
    h.txt(c, R, HH-26*mm, P.KISA+" · "+P.REV, h.F, 7.5,
          HexColor("#5E7governance"[:7]) if False else (HexColor("#5E7690") if koyu else h.GREY), "r")

def alt(c, t, koyu=True):
    h.txt(c, L, 8*mm, t, h.F, 6.6, HexColor("#5E7690") if koyu else h.GREY)

def kut(c, x, y, w, hgt, koyu=True, acc=None):
    h.kutu(c, x, y, w, hgt,
           HexColor("#16232F") if koyu else h.PAPER,
           HexColor("#24405F") if koyu else h.GREY_L)
    if acc: c.setFillColor(acc); c.rect(x, y, 2.4*mm, hgt, 0, 1)

def s1(c):
    c.setFillColor(BG); c.rect(0,0,W,HH,0,1)
    c.setFillColor(HexColor("#16273D")); c.rect(W*0.52,0,W*0.48,HH,0,1)
    v=D.View(c, W*0.50, 14*mm, W*0.50, HH-28*mm, pad=14*mm)
    for z in P.ZONES: D.poly(v, z[1], fill=HexColor("#1E3350"))
    for ad,d in P.ISLAK.items(): D.poly(v, d["tum"], fill=HexColor("#1E3350"))
    D.poly(v, unary_union([P.SALON,P.ERKEK,P.KADIN]), stroke=HexColor("#3F5F84"), lw=1.0)
    for kod,ad,g in P.ekipman_poligonlari():
        D.poly(v, g, fill=HexColor("#B87333") if kod=="A" else HexColor("#31496A"))
    c.setFillColor(h.COPPER); c.rect(L, HH-58*mm, 26*mm, 1.8*mm, 0, 1)
    h.txt(c, L, HH-52*mm, "ÖN TASARIM VE YATIRIM DOSYASI", h.FB, 8, h.COPPER)
    for i,ln in enumerate(["MOBİLYA MAĞAZASI →","FONKSİYONEL ANTRENMAN","STÜDYOSU"]):
        h.txt(c, L, HH-72*mm-i*12*mm, ln, h.FB, 21, HexColor("#FFFFFF"))
    h.txt(c, L, HH-116*mm, "MALTEPE / İDEALTEPE · İSTANBUL", h.F, 10, HexColor("#9FB4C9"))
    h.txt(c, L, HH-126*mm, f"{h.tl(P.A['ic_toplam'],2)} m² net iç alan · {P.REV} · {P.TARIH}",
          h.F, 8, HexColor("#6C8299"))
    h.txt(c, L, 12*mm, "Ön tasarım — yerinde doğrulanmadan ve ruhsat alınmadan uygulama yapılamaz.",
          h.F, 6.4, HexColor("#5E7690"))

def s2(c):
    bas(c, 2, "Tek bakışta", "Altı rakamda proje")
    m=P.maliyet("O","A")
    kw=(CW-2*6*mm)/3; kh=34*mm
    veri=[("NET İÇ ALAN", f"{h.tl(P.A['ic_toplam'],2)} m²", "salon 87,05 + ıslak hacim 16,73"),
          ("EŞZAMANLI KAPASİTE", "12 kişi", "65,14 m² serbest sirkülasyon · ≈5,4 m²/kişi"),
          ("TADİLAT BÜTÇESİ", f"{m['toplam'][0]/1e6:.2f}–{m['toplam'][1]/1e6:.2f} M₺".replace(".",","),
           f"önerilen senaryo · {P.FIYAT_TARIH}"),
          ("RUHSAT ZİNCİRİ", "16–28 hafta", "GSİM ön görüşten belediye ruhsatına"),
          ("ŞANTİYE SÜRESİ", f"{P.PROGRAM_HAFTA:.0f} hafta", "14 adım · kritik yol ıslak hacim"),
          ("EKİPMAN", "Bütçe dışı", "işverence temin edilmiştir")]
    for i,(u,dv,a) in enumerate(veri):
        x=L+(i%3)*(kw+6*mm); y=TOP-34*mm-(i//3)*(kh+6*mm)
        kut(c, x, y, kw, kh, True, h.COPPER if i<3 else HexColor("#24405F"))
        h.txt(c, x+8*mm, y+kh-9*mm, u, h.FB, 7, h.COPPER)
        h.txt(c, x+8*mm, y+kh-21*mm, dv, h.FB, 17, HexColor("#FFFFFF"))
        h.txt(c, x+8*mm, y+kh-28*mm, a, h.F, 6.6, HexColor("#8FA6BE"))
    # alt yarı: render + dosya içeriği
    ry = BOT+10*mm; rh2 = TOP-34*mm-2*(kh+6*mm)+kh-ry-2*mm
    import os
    rp = "output/render/01_giristen_arenaya_endustriyel.png"
    rw = CW*0.60
    if os.path.exists(rp):
        img = ImageReader(rp); iw, ih = img.getSize()
        dh = min(rh2, rw*ih/iw); dw = dh*iw/ih
        c.drawImage(img, L, ry, dw, dh, preserveAspectRatio=True, anchor="sw", mask=None)
        c.setStrokeColor(HexColor("#24405F")); c.setLineWidth(0.7); c.rect(L, ry, dw, dh, 0, 0)
        xr = L+dw+8*mm
    else:
        xr = L
    h.txt(c, xr, ry+rh2-4*mm, "BU DOSYADA NE VAR", h.FB, 8, h.COPPER)
    yy2 = ry+rh2-12*mm
    for t_ in ["A3 ana dosya — 12 sayfa tasarım, mevzuat, yol haritası ve maliyet",
               f"BoQ (.xlsx) — {len(P.B)} poz, birim fiyat sütunları boş, formüller canlı",
               "8 fotogerçekçi render — 4 açı × 2 stil varyantı",
               "Gym_Model.html — tek dosya offline 3B model, WhatsApp'tan paylaşılabilir",
               "Render_Promptlari.md — harici modelde yeniden üretim için"]:
        c.setFillColor(h.COPPER); c.circle(xr+1.6*mm, yy2+1.3*mm, 1.1*mm, 0, 1)
        yy2 = h.para(c, xr+5.5*mm, yy2+2.6*mm, t_, CW-(xr-L)-6*mm, h.F, 7.6,
                     HexColor("#C9D6E4"), 9.8) - 4.4*mm
    alt(c, "Tüm ölçüler alan dağılımı paftasından ölçeklendirilmiştir (±%3).")

def s3(c):
    bas(c, 3, "Önce bunu çöz", "Mevzuat eşiği — projenin tek kritik belirsizliği")
    kut(c, L, BOT+6*mm, CW*0.54, TOP-BOT-24*mm, True, h.RED)
    x=L+9*mm; w=CW*0.54-16*mm
    h.txt(c, x, TOP-30*mm, "UYGULAMADA ARANAN", h.FB, 8, h.RED)
    y=TOP-40*mm
    for ad,val in [("Çalışma (salon) alanı","≥ 125 m²"),("Kadın soyunma","≥ 15 m²"),
                   ("Erkek soyunma","≥ 15 m²"),("Dinlenme salonu","≥ 15 m²"),
                   ("TOPLAM TESİS ALANI","≥ 170 m²"),("Tavan yüksekliği","≥ 2,50 m")]:
        son = ad.startswith("TOPLAM")
        h.txt(c, x, y, ad, h.FB if son else h.F, 9.5 if son else 9,
              HexColor("#FFFFFF") if son else HexColor("#C9D6E4"))
        h.txt(c, x+w, y, val, h.FB, 9.5 if son else 9, h.RED if son else HexColor("#E7EDF3"), "r")
        if son:
            c.setStrokeColor(HexColor("#33506F")); c.setLineWidth(0.6)
            c.line(x, y+7*mm, x+w, y+7*mm)
        y -= 11*mm
    x2=L+CW*0.54+8*mm; w2=CW-CW*0.54-8*mm
    kut(c, x2, BOT+6*mm, w2, TOP-BOT-24*mm, True, h.COPPER)
    h.txt(c, x2+9*mm, TOP-30*mm, "BU BİRİMDE VAR OLAN", h.FB, 8, h.COPPER)
    h.txt(c, x2+9*mm, TOP-48*mm, f"{h.tl(P.A['ic_toplam'],2)} m²", h.FB, 34, HexColor("#FFFFFF"))
    h.txt(c, x2+9*mm, TOP-56*mm, "net iç kullanım alanı", h.F, 8, HexColor("#8FA6BE"))
    yy=TOP-70*mm
    for t in ["Bahçeler kapatılmayacak — açık kullanımda kalır, alan hesabına girmez.",
              "Yönetmelik METNİ salon için m² şartı getirmiyor: soyunma ≥8 m² ve dinlenme ≥15 m² diyor.",
              "Bu iki şart mevcut planda sağlanıyor (8,24 / 8,49 ve 17,33 m²).",
              "Karar teknik değil İDARİ. Tek yol: İstanbul GSİM'den YAZILI ÖN GÖRÜŞ."]:
        c.setFillColor(h.COPPER); c.circle(x2+11*mm, yy+1.4*mm, 1.2*mm, 0, 1)
        yy=h.para(c, x2+15*mm, yy+3*mm, t, w2-24*mm, h.F, 8, HexColor("#DCE6EF"), 10.4)-5*mm
    alt(c, "Yerel uygulama farklılık gösterebilir; İstanbul GSİM ve Maltepe Belediyesi'nden teyit alınmalıdır.")

def s4(c):
    bas(c, 4, "Karar ağacı", "Ön görüşün üç olası sonucu, üç rota")
    kw=(CW-2*7*mm)/3; kh=TOP-BOT-26*mm
    for i,(kod,ttl,col,md) in enumerate([
      ("R1","ÖN GÖRÜŞ OLUMLU", h.GREEN,
       ["Mevcut alan yeterli görülür","Bu dosya olduğu gibi uygulanır","Ek maliyet yok",
        "Tadilat hemen başlar","EN HIZLI SENARYO"]),
      ("R2","KAPSAM REVİZYONU", h.AMBER,
       ["Randevulu kişisel antrenman stüdyosu","Ring bire bir çalışmaya zaten uygun",
        "GSİM tescil kapsamı daraltılır","Belediye NACE kodu buna göre",
        "HUKUKİ GÖRÜŞ ŞART"]),
      ("R3","SÖZLEŞME YOLU", h.RED,
       ["Mesele mimari değil, ticarî","Kira sözleşmesinde fesih / indirim",
        "Avukatla değerlendirme","Gerekirse mal sahibiyle müzakere",
        "Geciktikçe manevra alanı daralır"])]):
        x=L+i*(kw+7*mm)
        kut(c, x, BOT+6*mm, kw, kh, True, col)
        c.setFillColor(col); c.circle(x+13*mm, BOT+6*mm+kh-13*mm, 5.4*mm, 0, 1)
        h.txt(c, x+13*mm, BOT+6*mm+kh-15.4*mm, kod, h.FB, 10, HexColor("#FFFFFF"), "c")
        h.txt(c, x+22*mm, BOT+6*mm+kh-15.4*mm, ttl, h.FB, 9.5, HexColor("#FFFFFF"))
        yy=BOT+6*mm+kh-28*mm
        for t in md:
            c.setFillColor(col); c.circle(x+10*mm, yy+1.2*mm, 1.0*mm, 0, 1)
            yy=h.para(c, x+14*mm, yy+2.6*mm, t, kw-22*mm, h.F, 8, HexColor("#DCE6EF"), 10.2)-4.6*mm
    alt(c, "Ön görüş alınmadan imalata başlanması tüm harcamayı riske atar. Bahçe kapatarak alan kazanımı işveren kararıyla kapsam dışıdır.")

def _plan(c, x, y, w, hgt, mod="oneri"):
    v=D.View(c, x, y, w, hgt, pad=5*mm)
    if mod=="mevcut":
        D.poly(v, P.SALON, fill=HexColor("#EDEFF2"))
        for ad,d in P.ISLAK.items(): D.poly(v, d["tum"], fill=HexColor("#DFE6EA"))
        D.kabuk(v); D.cephe(v)
    else:
        D.zeminler(v)
        for ad,d in P.ISLAK.items(): D.poly(v, d["tum"], fill=D.C_SERAMIK)
        D.kabuk(v); D.ic_bolme(v); D.cephe(v); D.kapilar(v)
        D.mobilya(v); D.ekipman(v)
    return v

def s5(c):
    bas(c, 5, "Mevcut durum", "Alan dağılımı — tüm hesapların temeli", koyu=False)
    v=_plan(c, L, BOT+4*mm, CW*0.46, TOP-BOT-18*mm, "mevcut")
    D.etiket(v,(5.0,4.6),"MAĞAZA",8,h.NAVY,h.FB,"c")
    D.etiket(v,(5.0,4.6),f"{h.tl(P.A['salon'],2)} m²",7,h.COPPER,h.FB,"c",dy=-5)
    x2=L+CW*0.46+10*mm; w2=CW-CW*0.46-10*mm
    rows=[["Salon (açık satış alanı)", h.tl(P.A['salon'],2)],
          ["Erkek soyunma bloğu", h.tl(P.A['erkek_blok'],2)],
          ["Kadın soyunma bloğu", h.tl(P.A['kadin_blok'],2)],
          ["NET İÇ KULLANIM ALANI", h.tl(P.A['ic_toplam'],2)],
          ["Ön bahçe (açık)", h.tl(P.A['on_bahce'],2)],
          ["Arka bahçe (açık)", h.tl(P.A['arka_bahce'],2)]]
    h.tablo(c, x2, TOP-22*mm, [("Bölüm",0.68),("m²",0.32)], rows, w2,
            satir_h=11*mm, fs=9.5, hfs=8, hizala=["l","r"])
    h.notkutu(c, x2, TOP-92*mm, w2, "Ölçü dayanağı",
      "DWG dosyası AutoCAD 2018 formatında ve bu ortamda açılamadı; PDF paftaları vektör değil "
      "raster. Geometri renk alanları izlenerek vektörleştirildi ve paftanın kendi m² etiketleriyle "
      "kalibre edildi — sapma %3'ün altında. Uygulama projesi için DXF (R2010) istenmelidir.",
      fs=7.6, acc=h.COPPER)
    alt(c, "TRIMODE Alan Dağılımı paftası · ön tasarım", koyu=False)

def s6(c):
    bas(c, 6, "Öneri planı", "Yerleşim korunur, duvar hareketi asgaride", koyu=False)
    _plan(c, L, BOT+4*mm, CW*0.52, TOP-BOT-16*mm)
    x2=L+CW*0.52+8*mm; w2=CW-CW*0.52-8*mm
    yy=TOP-20*mm
    for ad,m2,nt in [("ARENA · SERBEST AĞIRLIK", P.ZON_M2["ARENA · SERBEST AĞIRLIK"], "40 mm kauçuk + 10 mm titreşim matı"),
                     ("FONKSİYONEL · KARDİYO", P.ZON_M2["FONKSİYONEL · KARDİYO"], "20 mm kauçuk karo"),
                     ("DİNLENME SALONU", P.ZON_M2["DİNLENME SALONU"], "LVT — yönetmelik şartı 15 m²"),
                     ("GİRİŞ · BANKO", P.ZON_M2["GİRİŞ · BANKO · SİRKÜLASYON"], "LVT · resepsiyon 2,40 m"),
                     ("ISLAK HACİM (2 blok)", P.A["islak_toplam"], "2 duş + 2 WC · R11 seramik")]:
        h.txt(c, x2, yy, ad, h.FB, 9, h.NAVY)
        h.txt(c, x2+w2, yy, f"{m2:.2f} m²".replace(".",","), h.FB, 9.5, h.COPPER, "r")
        h.txt(c, x2, yy-5.6*mm, nt, h.F, 7.4, h.GREY)
        c.setStrokeColor(h.GREY_L); c.setLineWidth(0.5); c.line(x2, yy-9.4*mm, x2+w2, yy-9.4*mm)
        yy -= 15*mm
    h.notkutu(c, x2, yy-2*mm, w2, "Yeni imalat nerede?",
      "Kırmızı ile gösterilen tek yeni duvar imalatı, iki soyunma bloğunun içinde duş ve WC "
      "hacimlerini ayıran alçıpan bölmelerdir. Salon çeperinde hiçbir duvar hareket etmiyor.",
      fs=7.6, acc=h.RED)
    alt(c, "Kırmızı = yeni imalat · gri = mevcut · mavi = cephe doğraması", koyu=False)

def s7(c):
    bas(c, 7, "Zemin stratejisi", "Üç bölge — para nereye harcanıyor", koyu=False)
    _plan(c, L, BOT+4*mm, CW*0.48, TOP-BOT-16*mm)
    x2=L+CW*0.48+8*mm; w2=CW-CW*0.48-8*mm
    yy=TOP-20*mm
    for z,not_ in zip(P.ZONES, [
        "Yönetmelik dinlenme salonu için halıfleks/parke ve benzeri istiyor",
        "Resepsiyon ve bekleme — ıslak temizliğe uygun, fotojenik",
        "100 kg üzeri düşürmede asgari kalınlık; altında titreşim matı",
        "Ağırlık düşürülmeyen alan — m² maliyeti %40 daha düşük"]):
        c.setFillColor(HexColor(z[4])); c.rect(x2, yy-1*mm, 5*mm, 5*mm, 0, 1)
        h.txt(c, x2+8*mm, yy, z[0].split(" · ")[0], h.FB, 9, h.NAVY)
        h.txt(c, x2+w2, yy, f"{P.ZON_M2[z[0]]:.2f} m² · {z[3]}".replace(".",","), h.FB, 8, h.COPPER, "r")
        h.para(c, x2+8*mm, yy-5.4*mm, not_, w2-10*mm, h.F, 7.2, h.GREY, 9)
        yy -= 17*mm
    c.setFillColor(D.C_SERAMIK); c.rect(x2, yy-1*mm, 5*mm, 5*mm, 0, 1)
    h.txt(c, x2+8*mm, yy, "ISLAK HACİM", h.FB, 9, h.NAVY)
    h.txt(c, x2+w2, yy, f"{P.A['islak_toplam']:.2f} m² · R11 kaymaz".replace(".",","), h.FB, 8, h.COPPER, "r")
    h.para(c, x2+8*mm, yy-5.4*mm, "Duş önünde R10 yetersiz kalır; su yalıtımı 30 cm dönüşlü",
           w2-10*mm, h.F, 7.2, h.GREY, 9)
    h.notkutu(c, x2, yy-16*mm, w2, "Akustik — ruhsat sonrası en büyük risk",
      "Üst katta konut bulunduğu varsayılmıştır. Ağırlık düşürme darbesi döşemeden yapısal ses "
      "olarak iletilir ve şikâyet → kapatma riski doğurur. Arena altına 10 mm titreşim matı "
      "serilir ve işletme kuralı olarak ağırlık düşürme yasaklanır.", fs=7.4, acc=h.RED)
    alt(c, "Kesit detayları ve metrajlar ana dosyanın 6. sayfasındadır.", koyu=False)

def s8(c):
    bas(c, 8, "Islak hacim", "Maliyetin kalbi — ve tek bilinmeyeni", koyu=False)
    v=D.View(c, L, BOT+4*mm, CW*0.34, TOP-BOT-16*mm,
             geoms=[P.ERKEK.buffer(0.8), P.KADIN.buffer(0.8)])
    for _b in (P.ERKEK, P.KADIN):
        D.poly(v, _b.buffer(0.20, join_style=2).difference(_b), fill=D.C_DUVAR)
    for ad,d in P.ISLAK.items():
        D.poly(v, d["soyunma"], fill=HexColor("#DCE7EC"))
        D.poly(v, d["dus"], fill=HexColor("#A9C6D4")); D.poly(v, d["wc"], fill=HexColor("#BFD3DC"))
    D.ic_bolme(v); D.mobilya(v)
    for ad,d in P.ISLAK.items():
        for n_,lbl in (("soyunma",ad),("dus","DUŞ"),("wc","WC")):
            q=d[n_].representative_point()
            D.etiket(v,(q.x,q.y),lbl,6.4,h.NAVY,h.FB,"c",dy=1.6)
    x2=L+CW*0.34+8*mm; w2=CW-CW*0.34-8*mm
    mA=P.maliyet("O","A"); mB=P.maliyet("O","B")
    dA=[r for r in P.B if r[0]=="03.08"][0]; dB=[r for r in P.B if r[0]=="03.09"][0]
    rows=[["Kalem bedeli", h.bant(dA[4]*dA[5],dA[4]*dA[6]), h.bant(dB[4]*dB[5],dB[4]*dB[6])],
          ["Kot serbestliği","Mevcut kota bağımlı","Tam serbest"],
          ["Kullanım etkisi","15–20 cm basamak doğar","Kot değişmez, eşiksiz"],
          ["Bakım / arıza riski","Yok","Pompa arızası kullanımı durdurur"],
          ["Elektrik bağımlılığı","Yok","Var — kesintide kullanılamaz"],
          ["ÖNERİ","TERCİH EDİLEN","Yalnız A uygulanamazsa"]]
    h.tablo(c, x2, TOP-22*mm, [("Ölçüt",0.28),("SEÇENEK A — zemin yükseltme",0.36),
                               ("SEÇENEK B — atık su pompası",0.36)], rows, w2,
            satir_h=10*mm, fs=8, hfs=7.4, hizala=["l","l","l"])
    h.notkutu(c, x2, TOP-92*mm, w2, "Söküm sonrası ilk iş",
      "Mevcut pis su bağlantısının kotu ve konumu BİLİNMİYOR. Bu tek ölçüm, A/B kararını ve "
      "dolayısıyla tüm zemin imalatlarının sırasını kilitler. Yönetmelik şartı olan 2 duş + 2 WC "
      "her iki seçenekte de sağlanır.", fs=7.6, acc=h.RED)
    alt(c, "Her blokta 1 duş + 1 WC → karma kullanımda aranan 2+2 sağlanır.", koyu=False)

def s9(c):
    bas(c, 9, "Elektrik ve mekanik", "Kapasite hesabı — kişi başı debiden başlayarak")
    kw=(CW-3*6*mm)/4; kh=30*mm
    for i,(u,dv,a) in enumerate([
        ("TAZE HAVA", f"{h.tl(P.TAZE)} m³/h", f"{P.TAZE/P.KISI:.0f} m³/h·kişi · yasal asgari 30"),
        ("HAVA DEĞİŞİMİ", f"{P.ACH:.2f} h⁻¹".replace(".",","), f"iç hacim {h.tl(P.HACIM,1)} m³"),
        ("SOĞUTMA", f"{h.tl(P.SOGUTMA_BTU)} BTU", f"{P.ADET_KLIMA} bölge · {h.tl(P.KLIMA_BTU)} BTU kurulu"),
        ("TALEP GÜCÜ", f"{P.TALEP_KW:.1f} kW".replace(".",","), "trifaze 3×25 A abonelik önerilir")]):
        x=L+i*(kw+6*mm); y=TOP-20*mm-kh
        kut(c, x, y, kw, kh, True, h.COPPER)
        h.txt(c, x+7*mm, y+kh-8*mm, u, h.FB, 7, h.COPPER)
        h.txt(c, x+7*mm, y+kh-19*mm, dv, h.FB, 15, HexColor("#FFFFFF"))
        h.txt(c, x+7*mm, y+kh-25.5*mm, a, h.F, 6.4, HexColor("#8FA6BE"))
    yy=TOP-20*mm-kh-10*mm
    rows=[[a[0], f"{a[1]:.2f}".replace(".",","), str(a[2]),
           "Lineer 40 W" if a[5]=="lineer" else "IP44 18 W", str(a[4])] for a in P.AYDINLATMA]
    rows.append(["TOPLAM","","", f"{P.ARMATUR_ADET} lineer + {P.DOWNLIGHT_ADET} downlight",
                 str(P.ARMATUR_ADET+P.DOWNLIGHT_ADET)])
    h.tablo(c, L, yy, [("Aydınlatma bölgesi",0.40),("m²",0.12),("Lux hedefi",0.14),
                       ("Armatür tipi",0.20),("Adet",0.14)], rows, CW*0.60,
            satir_h=8.4*mm, fs=8, hfs=7.4, hizala=["l","r","r","l","r"],
            bg=HexColor("#16232F"), ink=HexColor("#DCE6EF"))
    h.notkutu(c, L+CW*0.62, yy, CW*0.38, "Doğrulanacak",
      "Mevcut pano gücü ve trifaze durumu bilinmiyor. 12,1 kW talep gücü karşılanamazsa dağıtım "
      "şirketine güç artırım başvurusu gerekir — 3–8 hafta. Tavan yüksekliği de varsayım (3,20 m); "
      "değişirse armatür adedi ve taze hava debisi yeniden hesaplanır.",
      fs=7.6, acc=h.RED, bg=HexColor("#2A1C20"), ink=HexColor("#E8D2D2"))
    alt(c, "Salon ısısı yönetmelikte ≥18 °C; tasarım hedefi 20–22 °C.")

def s10(c):
    bas(c, 10, "Yol haritası", "Sıra kritik: önce GSİM, sonra belediye")
    seq=[("0","Tespit\ntapu · iskân"),("1","GSİM\nÖN GÖRÜŞ"),("2","Proje\n1/100"),
         ("3","Tadilat\n11 hafta"),("4-5","İtfaiye\nSağlık"),("6","GSİM\nbaşvuru"),
         ("7","Komisyon\nTETKİKİ"),("8","Tescil\nücreti"),("9","Belediye\nRUHSAT"),("10","Vergi\nSGK")]
    bw=(CW-9*3*mm)/10
    for i,(no,t) in enumerate(seq):
        x=L+i*(bw+3*mm); y=TOP-22*mm-26*mm
        vurgu = i in (1,6,8)
        c.setFillColor(h.COPPER if vurgu else HexColor("#1B2B40"))
        c.setStrokeColor(h.COPPER if vurgu else HexColor("#2E4D70")); c.setLineWidth(0.7)
        c.roundRect(x, y, bw, 26*mm, 1.6*mm, 1, 1)
        h.txt(c, x+bw/2, y+19.5*mm, no, h.FB, 10, HexColor("#FFFFFF"), "c")
        for j,ln in enumerate(t.split("\n")):
            h.txt(c, x+bw/2, y+12*mm-j*4.4*mm, ln, h.FB if j==1 and vurgu else h.F, 6.4,
                  HexColor("#FFFFFF") if vurgu else HexColor("#9FB4C9"), "c")
        if i<9:
            c.setFillColor(HexColor("#3E5B7C")); p=c.beginPath()
            xa=x+bw+0.5*mm; p.moveTo(xa, y+14.6*mm); p.lineTo(xa+1.9*mm, y+13*mm)
            p.lineTo(xa, y+11.4*mm); p.close(); c.drawPath(p,0,1)
    yy=TOP-22*mm-26*mm-12*mm
    kw=(CW-2*6*mm)/3
    for i,(ttl,body,col) in enumerate([
        ("TOPLAM 16–28 HAFTA","Ön görüşten belediye ruhsatına kadar. Tadilat ile evrak süreçleri "
         "paralel yürütülerek kısaltılabilir.", h.COPPER),
        ("KOMİSYON YERİNDE GELİR","En az 5 kişilik komisyon tesisi bitmiş hâlde tetkik eder ve "
         "tutanak düzenler. Eksik tesisle başvuru ikinci tur demektir.", HexColor("#24405F")),
        ("EN SIK HATA","Belediyeye önce gitmek. Belediye GSİM uygunluk yazısını istediği için "
         "dosya geri döner; harç ve zaman kaybedilir.", h.RED)]):
        x=L+i*(kw+6*mm)
        kut(c, x, BOT+4*mm, kw, yy-BOT-4*mm, True, col)
        h.txt(c, x+8*mm, yy-9*mm, ttl, h.FB, 9, col if col!=HexColor("#24405F") else HexColor("#FFFFFF"))
        h.para(c, x+8*mm, yy-16*mm, body, kw-16*mm, h.F, 7.6, HexColor("#C9D6E4"), 10)
    alt(c, "Evrak kontrol listesi ve harç kalemleri ana dosyanın 9. sayfasındadır.")

def s11(c):
    bas(c, 11, "Maliyet", f"{len(P.B)} poz · kalem bazlı · düşük–yüksek bant", koyu=False)
    mO=P.maliyet("O","A"); mM=P.maliyet("M","A")
    veri=sorted([(g,*mO["gruplar"][g]) for g in P.GRUPLAR], key=lambda r:-(r[1]+r[2]))
    D.bar_araligi(c, L, TOP-22*mm, CW*0.56, 80*mm, veri, bar_h=5.6*mm, ara=2.6*mm)
    x2=L+CW*0.58; w2=CW-CW*0.58
    rows=[["MİNİMUM — yalnız zorunlu", h.tl(mM["toplam"][0]), h.tl(mM["toplam"][1])],
          ["ÖNERİLEN — akustik, ayna, tabela dâhil", h.tl(mO["toplam"][0]), h.tl(mO["toplam"][1])],
          ["Şantiye genel gideri %9 + beklenmedik %15", "dâhil", "dâhil"]]
    yy=h.tablo(c, x2, TOP-22*mm, [("Senaryo",0.50),("Düşük (TL)",0.25),("Yüksek (TL)",0.25)],
               rows, w2, satir_h=11*mm, fs=8.4, hfs=7.4, hizala=["l","r","r"])
    tl_=th=0
    for ad,lo,hi in P.NAKIT:
        if lo is None: lo,hi = mO["toplam"]
        tl_+=lo; th+=hi
    h.kutu(c, x2, yy-34*mm, w2, 30*mm, HexColor("#FDF3EC"), h.COPPER)
    h.txt(c, x2+7*mm, yy-11*mm, "AÇILIŞ ÖNCESİ TOPLAM NAKİT", h.FB, 8, h.COPPER)
    h.txt(c, x2+7*mm, yy-22*mm, f"{tl_/1e6:.2f}–{th/1e6:.2f} M₺".replace(".",","), h.FB, 20, h.NAVY)
    h.txt(c, x2+7*mm, yy-29*mm, "tadilat + ruhsat/harç + 3 ay kira + depozito + personel + pazarlama",
          h.F, 6.6, h.GREY)
    h.notkutu(c, x2, yy-38*mm, w2, "Ekipman bütçe dışı",
      "TRIMODE arena ve tüm antrenman ekipmanı işverence temin edilmiştir; hiçbir kalemde yer almaz.",
      fs=7.4, acc=h.NAVY2)
    alt(c, f"{P.FIYAT_TARIH} · birim fiyat sütunları boş .xlsx dosyası teklif karşılaştırması için hazırdır.",
        koyu=False)

def s12(c):
    bas(c, 12, "Sonraki adımlar", "Beş madde — sırayla")
    kw=(CW-4*5*mm)/5; kh=TOP-BOT-30*mm
    for i,(no,ttl,body) in enumerate(P.SONRAKI_5):
        x=L+i*(kw+5*mm)
        kut(c, x, BOT+18*mm, kw, kh, True, h.COPPER if i<3 else HexColor("#24405F"))
        c.setFillColor(h.COPPER if i<3 else HexColor("#3E5B7C"))
        c.circle(x+11*mm, BOT+18*mm+kh-12*mm, 5*mm, 0, 1)
        h.txt(c, x+11*mm, BOT+18*mm+kh-14.2*mm, no, h.FB, 10, HexColor("#FFFFFF"), "c")
        h.para(c, x+7*mm, BOT+18*mm+kh-24*mm, h.TR_UP(ttl), kw-14*mm, h.FB, 8.4, HexColor("#FFFFFF"), 10.4)
        h.para(c, x+7*mm, BOT+18*mm+kh-40*mm, body, kw-14*mm, h.F, 7.2, HexColor("#A8BCD0"), 9.4)
    h.txt(c, L, BOT+9*mm, "İŞVERENDEN İSTENECEKLER:", h.FB, 7.6, h.COPPER)
    h.txt(c, L+42*mm, BOT+9*mm,
      "DXF (R2010) · mevcut durum fotoğrafları · ölçülmüş m² ve tavan yüksekliği · ekipman listesi · "
      "pis su kotu · pano gücü · tapu niteliği ve muvafakat durumu · hedef açılış tarihi",
      h.F, 7, HexColor("#9FB4C9"))
    alt(c, "Ayrıntılar: ana dosya (A3) · BoQ (.xlsx) · render seti · Gym_Model.html")

def build(path="output/Gym_Sunum_16x9.pdf"):
    c=canvas.Canvas(path, pagesize=(W,HH))
    c.setTitle(f"Maltepe / İdealtepe — Gym Dönüşümü · Sunum ({P.REV})")
    for fn in (s1,s2,s3,s4,s5,s6,s7,s8,s9,s10,s11,s12):
        fn(c); c.showPage()
    c.save(); print("→", path)

if __name__ == "__main__":
    build()
