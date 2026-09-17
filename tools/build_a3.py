# -*- coding: utf-8 -*-
"""TESLİMAT A — Ana dosya, A3 yatay, 12 sayfa."""
import sys, math, os
sys.path.insert(0, os.path.dirname(__file__))
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from shapely.ops import unary_union
import proj as P, helpers as h, draw as D

W, HH = 420*mm, 297*mm
TOP   = HH - 18.6*mm - 6*mm
BOT   = 14*mm
L, R  = 12*mm, W-12*mm
CW    = R-L
N     = 12

def _sayfa(c, no, baslik, ust=None):
    h.band(c, W, HH, no, baslik, ust); h.footer(c, W, no, N)

# ══ 1 KAPAK ════════════════════════════════════════════════════════════════════
def s01(c):
    c.setFillColor(h.NAVY); c.rect(0,0,W,HH,0,1)
    c.setFillColor(h.NAVY2); c.rect(0,0,W*0.46,HH,0,1)
    v = D.View(c, W*0.44, 22*mm, W*0.58, HH-52*mm, pad=16*mm)
    D.poly(v, unary_union([P.SALON,P.ERKEK,P.KADIN]).buffer(0.20,join_style=2),
           fill=HexColor("#1E3350"))
    for z in P.ZONES: D.poly(v, z[1], fill=HexColor("#24405F"))
    for ad,d in P.ISLAK.items(): D.poly(v, d["tum"], fill=HexColor("#24405F"))
    D.poly(v, unary_union([P.SALON,P.ERKEK,P.KADIN]), stroke=HexColor("#4E6C8E"), lw=0.8)
    for kod,ad,g in P.ekipman_poligonlari():
        D.poly(v, g, fill=HexColor("#B87333") if kod=="A" else HexColor("#3D5876"))
    for i in range(1,4):
        D.poly(v, P.hex_poly(*P.EKIPMAN[0][5], s=P.HEX_S*i/4.0), stroke=HexColor("#D79A4E"), lw=0.6)
    c.setFillColor(h.COPPER); c.rect(26*mm, HH-104*mm, 30*mm, 1.8*mm, 0, 1)
    h.txt(c, 26*mm, HH-96*mm, "ÖN TASARIM VE YATIRIM DOSYASI", h.FB, 8, h.COPPER)
    for i, ln in enumerate(["MOBİLYA MAĞAZASI →","FONKSİYONEL","ANTRENMAN STÜDYOSU"]):
        h.txt(c, 26*mm, HH-124*mm-i*15*mm, ln, h.FB, 26, HexColor("#FFFFFF"))
    h.txt(c, 26*mm, HH-181*mm, "MALTEPE / İDEALTEPE  ·  İSTANBUL", h.F, 11, HexColor("#C9D6E4"))
    h.txt(c, 26*mm, HH-190*mm, f"Net iç kullanım alanı {h.tl(P.A['ic_toplam'],2)} m²  ·  "
          f"ön bahçe {h.tl(P.A['on_bahce'],2)} m²  ·  arka bahçe {h.tl(P.A['arka_bahce'],2)} m²",
          h.F, 8, HexColor("#8FA6BE"))
    c.setStrokeColor(HexColor("#35506F")); c.setLineWidth(0.7)
    c.line(26*mm, HH-205*mm, 150*mm, HH-205*mm)
    for i,(k,vv) in enumerate([("REVİZYON",P.REV),("TARİH",P.TARIH),
                               ("DURUM","Ön tasarım — yerinde doğrulanacak"),
                               ("ÖLÇÜ DAYANAĞI","Raster paftadan ölçeklendirme ±%3")]):
        y = HH-216*mm-i*11*mm
        h.txt(c, 26*mm, y, k, h.FB, 6.2, h.COPPER)
        h.txt(c, 26*mm, y-5*mm, vv, h.F, 8, HexColor("#E4EBF2"))
    h.txt(c, 26*mm, 16*mm, "Bu dosya ruhsat başvurusu yerine geçmez; uygulama öncesi proje müellifi "
          "onayı ve kurum izinleri zorunludur.", h.F, 6.2, HexColor("#7B93AC"))

# ══ 2 PROJEYE BAKIŞ ════════════════════════════════════════════════════════════
def s02(c):
    _sayfa(c, 2, "Projeye bakış", "Kapsam · kilitli kararlar · rakamlar")
    y = TOP
    y = h.para(c, L, y-2*mm,
      "Maltepe / İdealtepe'de kirası imzalanmış, hâlen mobilya mağazası olarak kullanılan "
      f"{h.tl(P.A['ic_toplam'],2)} m² net kullanım alanlı ticari birim, mevcut TRIMODE yerleşimi korunarak "
      "butik bir fonksiyonel antrenman stüdyosuna dönüştürülmektedir. Ekipman işverence satın alınmış "
      "olduğundan yerleşim mevcut ekipman ölçülerine göre çözülmüş, ekipman bedeli bütçe dışında "
      "bilgi satırı olarak gösterilmiştir. Tasarım ilkesi: duvar hareketini asgaride tutmak ve bütçeyi "
      "ıslak hacim, zemin ve aydınlatma-havalandırma olmak üzere üç başlıkta yoğunlaştırmak. "
      "Dosyanın en kritik çıktısı 3. sayfadaki uygunluk kontrolüdür: kira imzalanmış olduğundan "
      "mekânın fiziki uygunluğu artık bir seçim değil, yönetilmesi gereken bir risktir.",
      CW, h.F, 8.2, h.INK, 11.4)
    kw=(CW-3*6*mm)/4; ky=y-8*mm-46*mm
    for i,(no,bs,gv) in enumerate([
      ("1","MEVZUAT SIRASI","Önce İstanbul GSİM tesis açılış izni ve komisyon tetkiki, sonra Maltepe "
       "Belediyesi işyeri açma ruhsatı. Belediye GSİM uygunluk yazısını ister; sıra ters kurulursa süreç başa döner."),
      ("2","ISLAK HACİM","Maliyetin kalbi. Mevcut iki blok korunur, içleri komple yenilenir: her blokta "
       "1 duş + 1 WC → toplam 2+2. Gider kotu yerçekimiyle çözülmezse Seçenek A (zemin yükseltme) devreye girer."),
      ("3","ZEMİN STRATEJİSİ","Üç bölge: arena/serbest ağırlıkta 40 mm kauçuk + 10 mm titreşim matı, "
       "fonksiyonel-kardiyo alanında 20 mm kauçuk, dinlenme ve girişte LVT. Islak hacim R11 kaymaz seramik."),
      ("4","BÜTÇE YAKLAŞIMI",f"Tek m² fiyatı kullanılmadı; {len(P.B)} poz üzerinden kalem bazlı, düşük-yüksek bantlı "
       "kuruldu. %9 şantiye genel gideri ve %15 beklenmedik payı ayrıca eklendi.")]):
        h.kart(c, L+i*(kw+6*mm), ky, kw, 46*mm, no, bs, gv)
    m=P.maliyet("O","A")
    kw2=(CW-5*5*mm)/6; ky2=ky-8*mm-30*mm
    for i,(u,dv,al) in enumerate([
      ("NET İÇ ALAN", f"{h.tl(P.A['ic_toplam'],2)} m²", f"salon {h.tl(P.A['salon'],2)} + ıslak {h.tl(P.A['islak_toplam'],2)}"),
      ("KAPASİTE", f"{P.V['kisi_kapasite'][0]} kişi", "seans başı eşzamanlı · 65,14 m² serbest sirkülasyon"),
      ("TADİLAT BÜTÇESİ", f"{m['toplam'][0]/1e6:.2f}–{m['toplam'][1]/1e6:.2f} M₺".replace(".",","), f"önerilen senaryo · Seçenek A · {P.FIYAT_TARIH}"),
      ("RUHSAT ZİNCİRİ", "16–28 hafta", "ön görüşten belediye ruhsatına, adım 0–10"),
      ("ŞANTİYE SÜRESİ", f"{P.PROGRAM_HAFTA:.0f} hafta", "14 adımlık iş programı · kritik yol ıslak hacim"),
      ("BEKLENMEDİK PAY", "%15", "+ %9 şantiye genel gideri")]):
        h.kpi(c, L+i*(kw2+5*mm), ky2, kw2, 30*mm, u, dv, al,
              h.COPPER if i<3 else h.NAVY2)
    yb = h.notkutu(c, L, ky2-8*mm, CW,
      "EN KRİTİK TEK BULGU — ÖNCE BUNU ÇÖZ",
      f"Özel Beden Eğitimi ve Spor Tesisleri mevzuatının il müdürlüklerince yaygın uygulanan biçiminde "
      f"spor salonlarında en az 125 m² çalışma alanı, 15'er m² kadın/erkek soyunma odası ve 15 m² dinlenme "
      f"salonu ile toplam en az 170 m² ve 2,50 m tavan yüksekliği aranmaktadır. Bu birimin net iç alanı "
      f"{h.tl(P.A['ic_toplam'],2)} m²'dir. Kapalı alanı artırmak için bahçelerin kapatılması "
      f"işveren kararıyla kapsam dışıdır: ön ({h.tl(P.A['on_bahce'],2)} m²) ve arka bahçe "
      f"({h.tl(P.A['arka_bahce'],2)} m²) açık kullanımda kalır ve hiçbir alan hesabına girmez. "
      f"Buna karşılık yönetmelik metninin kendisi salon için asgari m² şartı getirmez — yalnızca soyunma odası "
      f"için 8 m² ve dinlenme salonu için 15 m² der; bu iki şart mevcut planda sağlanmaktadır (8,24 / 8,49 ve 17,33 m²). "
      f"Karar bu nedenle teknik değil idaridir ve tek çözüm yolu İstanbul GSİM'den YAZILI ÖN GÖRÜŞ almaktır. "
      f"Aşağıdaki üç rota, ön görüşün üç olası sonucuna karşılık gelir.",
      fs=7.0, acc=h.RED)
    kw3=(CW-2*6*mm)/3; ky3=yb-7*mm-44*mm
    for i,(no,ttl,body) in enumerate([
      ("R1","ÖN GÖRÜŞ OLUMLU",
       "GSİM yönetmelik metnini esas alır ve mevcut alanı yeterli görür. Bu dosya olduğu gibi uygulanır; "
       "ek maliyet yoktur. En hızlı senaryo — tadilat 3. adımda başlar."),
      ("R2","KAPSAM REVİZYONU",
       "Tesis, çok kullanıcılı 'spor salonu' yerine randevulu kişisel antrenman / özel ders stüdyosu olarak "
       "konumlanır; ring zaten bire bir ve küçük grup çalışmasına uygundur. GSİM tescil kapsamı ve belediye "
       "NACE kodu buna göre seçilir. Hukuki görüş şarttır; yanlış kodla açılış denetimde kapatma riski taşır."),
      ("R3","SÖZLEŞME YOLU",
       "İki rota da kapanırsa mesele mimari değil ticarîdir: kira sözleşmesindeki fesih veya indirim "
       "imkânı avukatla değerlendirilir, gerekirse mal sahibiyle yeniden görüşülür. Bu yüzden ön görüş "
       "başvurusu ilk aydan geç kalmamalıdır — sözleşmede manevra alanı süreyle daralır.")]):
        h.kart(c, L+i*(kw3+6*mm), ky3, kw3, 44*mm, no, ttl, body,
               h.GREEN if i==0 else (h.AMBER if i==1 else h.RED))
    h.txt(c, L, ky3-6*mm,
      "Her üç rotada da ortak olan tek şey şudur: yazılı ön görüş alınmadan imalata başlanması, tescil reddi "
      "hâlinde harcanan tüm tadilat bedelini geri dönüşü olmayan biçimde riske atar. "
      "Bahçelerin kapatılması yoluyla alan kazanımı işveren kararıyla değerlendirme dışıdır.",
      h.F, 6.6, h.RED)

# ══ 3 UYGUNLUK KONTROL ═════════════════════════════════════════════════════════
def s03(c):
    _sayfa(c, 3, "Uygunluk kontrol sayfası", "Kira imzalandı — mekânın fiziki uygunluğu artık yönetilecek bir risktir")
    y = TOP
    bw=(CW-2*6*mm)/3
    for i,(rk,ad,acik) in enumerate([
      ("K", f"{P.UYG_SAYIM['K']} madde  ·  KIRMIZI",
       "Projeyi durdurabilir. Çözülmeden imalata başlanmamalıdır."),
      ("S", f"{P.UYG_SAYIM['S']} madde  ·  SARI",
       "Tasarım veya bütçeyle çözülür; veri eksikliği nedeniyle açık."),
      ("Y", f"{P.UYG_SAYIM['Y']} madde  ·  YEŞİL",
       "Bu dosyadaki tasarım ve BoQ ile karşılanmaktadır.")]):
        x=L+i*(bw+6*mm)
        h.kutu(c, x, y-17*mm, bw, 15*mm, h.tint(h.RISK[rk],0.90), h.RISK[rk])
        c.setFillColor(h.RISK[rk]); c.rect(x, y-17*mm, 2.4*mm, 15*mm, 0,1)
        h.txt(c, x+7*mm, y-8*mm, ad, h.FB, 9, h.RISK[rk])
        h.txt(c, x+7*mm, y-13.6*mm, acik, h.F, 6.4, h.INK)
    y -= 22*mm
    rows=[[r[0],r[1],r[2],{"K":"KIRMIZI","S":"SARI","Y":"YEŞİL"}[r[3]]] for r in P.UYGUNLUK]
    yy=h.tablo(c, L, y, [("Yönetmelik / uygulama şartı",0.30),("Mevcut durum",0.24),
                      ("Gerekli aksiyon",0.38),("Risk",0.08)], rows, CW,
            satir_h=5.6*mm, fs=6.2, hfs=6.3,
            renkli_sutun={3: lambda r: h.RISK[{"KIRMIZI":"K","SARI":"S","YEŞİL":"Y"}[r[3]]]},
            hizala=["l","l","l","c"])
    h.txt(c, L, yy-8*mm, "KIRMIZI MADDELER — ÇÖZÜM VE MALİYET ETKİSİ", h.FB, 8.5, h.RED)
    krows=[
     ["Çalışma alanı / toplam tesis alanı eşiği",
      "GSİM'den yazılı ön görüş (R1). Olumsuzsa kapsam revizyonu (R2) veya kira sözleşmesi yolu (R3). "
      "Bahçe kapatarak alan kazanımı işveren kararıyla kapsam dışıdır",
      "Ön görüş: harç dışında maliyetsiz · R2: hukuki görüş bedeli · R3: sözleşme müzakeresi"],
     ["Bağımsız bölüm niteliği / iskân",
      "Tapu ve yapı kullanma izin belgesinin çıkarılması; niteliği uygun değilse tapu tashihi",
      "Belge temini düşük bedelli; tashih gerekirse süre etkisi 4–10 hafta"],
     ["Kat malikleri muvafakatnamesi",
      "Yönetim planının incelenmesi, muvafakat toplanması; gürültü önlemlerinin argüman olarak sunulması",
      "Doğrudan bedeli yok; alınamazsa ruhsat çıkmaz — projeyi durdurur"],
     ["Pis su bağlantı kotu",
      "Söküm sonrası ilk iş kot ölçümü; Seçenek A (zemin yükseltme) hazır, olmazsa Seçenek B (pompa)",
      "A: 14.220–23.422 TL · B: 72.000–128.000 TL (aradaki fark bütçenin %2–4'ü)"],
    ]
    yy=h.tablo(c, L, yy-13*mm, [("Kırmızı madde",0.22),("Çözüm yolu",0.44),("Maliyet / takvim etkisi",0.34)],
               krows, CW, satir_h=6.4*mm, fs=6.2,
               renkli_sutun={0: lambda r: h.tint(h.RED,0.84)}, hizala=["l","l","l"])
    h.txt(c, L, BOT+3.5*mm, "Yerel uygulama farklılık gösterebilir; Maltepe Belediyesi Ruhsat ve Denetim "
          "Müdürlüğü ile İstanbul Gençlik ve Spor İl Müdürlüğü'nden güncel liste teyit edilmelidir.",
          h.F, 6.2, h.GREY)

# ══ 4 MEVCUT DURUM ═════════════════════════════════════════════════════════════
def s04(c):
    _sayfa(c, 4, "Mevcut durum ve alan dağılımı", "TRIMODE yerleşim / duvar / alan dağılımı paftalarından üretilmiştir")
    y=TOP; pw=CW*0.50
    v=D.View(c, L, BOT+8*mm, pw, y-BOT-10*mm)
    D.poly(v, unary_union([P.SALON,P.ERKEK,P.KADIN]).buffer(0.20,join_style=2), fill=D.C_DUVAR)
    D.poly(v, P.SALON, fill=HexColor("#EDEFF2"))
    for ad,d in P.ISLAK.items(): D.poly(v, d["tum"], fill=HexColor("#DFE6EA"))
    D.kabuk(v); D.cephe(v)
    D.etiket(v,(5.0,4.6),"MAĞAZA — AÇIK SATIŞ ALANI",7,h.NAVY,h.FB,"c")
    D.etiket(v,(5.0,4.6),f"{h.tl(P.A['salon'],2)} m²",6.4,h.COPPER,h.FB,"c",dy=-4.4)
    D.etiket(v,(8.0,11.0),"ARKA KOL",6.2,h.NAVY,h.FB,"c")
    for ad,d in P.ISLAK.items():
        q=d["tum"].representative_point()
        D.etiket(v,(q.x,q.y),ad,5.8,h.NAVY,h.FB,"c")
        D.etiket(v,(q.x,q.y),f"{P.ISLAK_M2_DETAY[ad]['tum']:.2f} m²".replace(".",","),5.2,h.COPPER,h.F,"c",dy=-3.6)
    D.olcu(v,(3.24,0.0),(8.92,0.0),off=0.75); D.olcu(v,(0.0,6.84),(0.58,1.25),off=-0.75)
    D.olcu(v,(9.53,0.50),(8.31,8.46),off=1.4); D.olcu(v,(6.39,8.96),(0.85,8.37),off=0.75)
    D.kuzey_ok(v, L+pw-14*mm, y-14*mm); D.olcek_cubugu(v, L+6*mm, BOT+12*mm)
    h.lejant(c, L+6*mm, BOT+2*mm, [(D.C_DUVAR,"Mevcut duvar"),(D.C_CEPHE,"Cephe doğraması"),
                                   (HexColor("#DFE6EA"),"Mevcut ıslak hacim blokları")])
    x2=L+pw+8*mm; w2=CW-pw-8*mm; yy=y
    h.txt(c, x2, yy-4*mm, "ALAN DAĞILIMI", h.FB, 8.5, h.NAVY)
    rows=[["Salon (açık satış alanı)", h.tl(P.A['salon'],2), "Pafta etiketi · gri"],
          ["Erkek soyunma bloğu", h.tl(P.A['erkek_blok'],2), "Pafta etiketi · mavi"],
          ["Kadın soyunma bloğu", h.tl(P.A['kadin_blok'],2), "Pafta etiketi · pembe"],
          ["NET İÇ KULLANIM ALANI", h.tl(P.A['ic_toplam'],2), "Tüm hesapların temeli"],
          ["Ön bahçe (açık)", h.tl(P.A['on_bahce'],2), "Kapalı alana dâhil değil"],
          ["Arka bahçe (açık)", h.tl(P.A['arka_bahce'],2), "Kapalı alana dâhil değil"],
          ["Bahçe toplamı", h.tl(P.A['bahce'],2), "Kapatma senaryosunun konusu"]]
    yy=h.tablo(c, x2, yy-7*mm, [("Bölüm",0.50),("m²",0.16),("Kaynak / not",0.34)], rows, w2,
               satir_h=6.0*mm, fs=6.6, hizala=["l","r","l"])
    h.txt(c, x2, yy-7*mm, "SÖKÜM KAPSAMI (mobilyacıdan kalan imalatlar)", h.FB, 8.5, h.NAVY)
    rows2=[["Raf, vitrin, teşhir podyumu, tezgâh sökümü", f"{h.tl(P.A['ic_toplam'],2)} m²"],
           ["Mevcut zemin kaplaması sökümü ve şap tesviyesi", f"{h.tl(P.A['ic_toplam'],2)} m²"],
           ["Islak hacim seramik + vitrifiye sökümü", f"{h.tl(P.A['islak_toplam'],2)} m²"],
           ["Mevcut aydınlatma, kablaj ve zayıf akım sökümü", "komple"],
           ["Moloz yükleme, indirme, nakliye (konteyner)", "götürü"]]
    yy=h.tablo(c, x2, yy-12*mm, [("İş",0.74),("Metraj",0.26)], rows2, w2,
               satir_h=6.0*mm, fs=6.6, hizala=["l","r"])
    yb = h.notkutu(c, x2, yy-8*mm, w2, "ÖLÇÜ DAYANAĞI VE DOĞRULUK",
      "Teslim edilen DWG dosyası AutoCAD 2018 (AC1032) formatındadır ve bu ortamda açılamamıştır; "
      "PDF paftaları ise vektör değil JPEG raster olarak üretilmiştir. Bu nedenle geometri, alan dağılımı "
      "paftasındaki renk alanları izlenerek vektörleştirilmiş ve paftanın kendi m² etiketleriyle "
      "kalibre edilmiştir; üç bölgede sapma %3'ün altındadır. Uygulama projesi için işverenden "
      "DXF (R2010) export istenmelidir.", fs=6.4, acc=h.COPPER)
    h.txt(c, x2, yb-8*mm, "YERİNDE TESPİT LİSTESİ — ölçüm günü doldurulacak", h.FB, 8, h.NAVY)
    trow=[["Tavan yüksekliği (salon / ıslak hacim)","m","VARSAYIM 3,20"],
          ["Pis su bağlantı kotu ve konumu","cm / kroki","—"],
          ["Elektrik pano gücü · trifaze var mı","kW / E-H","—"],
          ["Doğalgaz bağlantısı var mı","E-H","—"],
          ["Üst katta konut var mı","E-H","VARSAYIM: var"],
          ["Kolon sayısı, kesiti ve konumu","adet / cm","—"],
          ["Cephe doğrama genişliği ve kapı açıklığı","cm","—"],
          ["Zemin kotu farkı (giriş eşiği)","cm","—"],
          ["Mevcut aydınlatma ve pano konumu","kroki","—"]]
    h.tablo(c, x2, yb-14*mm, [("Tespit edilecek",0.58),("Birim",0.18),("Şu anki kabul",0.24)],
            trow, w2, satir_h=6.0*mm, fs=6.3, hizala=["l","c","r"])

# ══ 5 ÖNERİ PLANI ══════════════════════════════════════════════════════════════
def s05(c):
    _sayfa(c, 5, "Öneri planı", "Yerleşim korunur · duvar hareketi asgaride · ekipman mevcut ölçülerle")
    y=TOP; pw=CW*0.615
    v=D.View(c, L, BOT+10*mm, pw, y-BOT-12*mm)
    D.zeminler(v)
    for ad,d in P.ISLAK.items(): D.poly(v, d["tum"], fill=D.C_SERAMIK)
    D.kabuk(v); D.ic_bolme(v); D.cephe(v); D.kapilar(v)
    D.mobilya(v); D.ekipman(v); D.mekan_adlari(v)
    D.olcu(v,(3.24,0.0),(8.92,0.0),off=-0.8); D.olcu(v,(0.0,6.84),(0.58,1.25),off=-0.8)
    D.olcu(v,(11.56,1.10),(11.01,4.96),off=-0.8); D.olcu(v,(5.84,12.50),(9.89,12.99),off=0.8)
    D.olcu(v,(10.47,8.75),(11.00,5.08),off=-0.8)
    D.kuzey_ok(v, L+pw-13*mm, y-13*mm); D.olcek_cubugu(v, L+5*mm, BOT+13*mm)
    h.lejant(c, L+5*mm, BOT+3*mm,
        [(D.C_YENI,"Yeni imalat"),(D.C_DUVAR,"Mevcut — korunuyor"),(D.C_CEPHE,"Cephe doğraması"),
         (HexColor("#B87333"),"Altıgen ring"),(HexColor("#333940"),"Ekipman (işverence temin)")])
    x2=L+pw+7*mm; w2=CW-pw-7*mm; yy=y
    h.txt(c, x2, yy-4*mm, "EKİPMAN YERLEŞİMİ — mevcut ölçüler", h.FB, 8, h.NAVY)
    rows=[]
    for kod,ad,en,boy,adet,_,_,tip,hh in P.EKIPMAN:
        rows.append([kod, ad, "altıgen · 10,60 m²" if en is None else f"{en}×{boy}",
                     f"{hh:.2f}".replace(".",","), str(adet)])
    yy=h.tablo(c, x2, yy-7*mm, [("Kod",0.09),("Ekipman",0.52),("Ölçü (cm)",0.20),
                                ("Yük. (m)",0.11),("Ad.",0.08)],
               rows, w2, satir_h=5.8*mm, fs=6.3, hizala=["c","l","r","r","c"])
    h.txt(c, x2, yy-7*mm, "SİRKÜLASYON VE ACİL ÇIKIŞ ANALİZİ", h.FB, 8, h.NAVY)
    rows2=[["Salon brüt alanı", f"{h.tl(P.A['salon'],2)} m²"],
           ["Ekipman + arena footprint", f"{h.tl(P.EK_ALAN,2)} m²"],
           ["Serbest sirkülasyon / çalışma alanı", "65,14 m²"],
           ["Eşzamanlı kapasite kabulü", f"{P.V['kisi_kapasite'][0]} kişi (≈5,4 m²/kişi)"],
           ["Ana sirkülasyon koridoru (asgari)", "1,20 m"],
           ["Ekipman önü serbest mesafe (asgari)", "0,90 m"],
           ["Ana giriş — batı cephe", "2×80 cm çift kanat"],
           ["İkinci çıkış — güneybatı cephe", "100 cm"],
           ["En uzak noktadan çıkışa mesafe", "≈ 16,5 m"]]
    yy=h.tablo(c, x2, yy-12*mm, [("Ölçüt",0.62),("Değer",0.38)], rows2, w2,
               satir_h=5.8*mm, fs=6.4, hizala=["l","r"])
    h.txt(c, x2, yy-8*mm, "TASARIM KARARLARI VE GEREKÇELERİ", h.FB, 8, h.NAVY)
    cy=h.madde_listesi(c, x2, yy-14*mm, w2, [
      "MEVCUT YERLEŞİM KORUNDU. Altıgen arena merkezde, ekipman çeperde, soyunma blokları doğu cephede, "
      "banko girişte. Salon çeperinde tek bir duvar bile hareket etmiyor — bu, hem bütçeyi hem de "
      "tadilat ruhsatı riskini aşağı çekiyor.",
      "YENİ DUVAR YALNIZCA İKİ BLOĞUN İÇİNDE. Duş ve WC hacimlerini soyunmadan ayıran alçıpan bölmeler; "
      "toplam yeni bölme metrajı 44,6 m². Kırmızı ile gösterilmiştir.",
      "KUZEY KOL = DİNLENME SALONU. Yönetmeliğin aradığı 15 m² dinlenme salonu şartı 17,33 m² ile "
      "karşılanıyor; ayrı bir hacim olması gürültüden uzak bir bekleme alanı da sağlıyor.",
      "ARENA MERKEZDE, KARDİYO GÜNEY CEPHEDE. Koşu bantları doğal ışık alan güneybatı cephesine, "
      "serbest ağırlık ise komşu duvardan uzak merkeze yerleştirildi — titreşim iletimi azalır.",
      "İKİ ÇIKIŞ NOKTASI. Batı cephesinden ana giriş (2×80 cm) ve güneybatı cephesinden ikinci çıkış "
      "(100 cm); en uzak noktadan çıkışa mesafe yaklaşık 16,5 m.",
      "BANKO GİRİŞTE, GÖRÜŞ HÂKİM. Resepsiyon bankosu hem girişi hem arenayı görür; tek personelle "
      "işletmeyi mümkün kılar.",
    ], fs=6.3, lead=8.4)
    h.notkutu(c, x2, cy-4*mm, w2, "Doğrulanacak",
      "Kolon konumları paftada net okunamamıştır; yerinde tespit sonrası ekipman yerleşimi ve "
      "keskin köşe kaplama metrajı revize edilebilir.", fs=6.2, acc=h.NAVY2)

# ══ 6 ZEMİN VE AKUSTİK ═════════════════════════════════════════════════════════
def s06(c):
    _sayfa(c, 6, "Zemin ve akustik paftası", "Üç bölgeli zemin · ıslak hacim R11 · titreşim yalıtımı")
    y=TOP; pw=CW*0.52
    v=D.View(c, L, BOT+10*mm, pw, y-BOT-12*mm)
    D.zeminler(v)
    for ad,d in P.ISLAK.items(): D.poly(v, d["tum"], fill=D.C_SERAMIK)
    D.kabuk(v); D.ic_bolme(v); D.cephe(v)
    for z in P.ZONES:
        pt=z[5]; D.etiket(v,pt,h.TR_UP(z[0].split(" · ")[0]),6,h.NAVY,h.FB,"c",dy=3)
        D.etiket(v,pt,z[2],5.2,h.NAVY2,h.F,"c",dy=-1)
        D.etiket(v,pt,f"{P.ZON_M2[z[0]]:.2f} m² · {z[3]}".replace(".",","),5.4,h.COPPER,h.FB,"c",dy=-5.4)
    for ad,d in P.ISLAK.items():
        q=d["tum"].representative_point()
        D.etiket(v,(q.x,q.y),"SERAMİK R11",5.2,h.NAVY,h.FB,"c",dy=2)
        D.etiket(v,(q.x,q.y),f"{P.ISLAK_M2_DETAY[ad]['tum']:.2f} m²".replace(".",","),5,h.COPPER,h.F,"c",dy=-2.6)
    D.kuzey_ok(v, L+pw-13*mm, y-13*mm); D.olcek_cubugu(v, L+5*mm, BOT+13*mm)
    x2=L+pw+7*mm; w2=CW-pw-7*mm; yy=y
    h.txt(c, x2, yy-4*mm, "ZEMİN BÖLGELERİ VE KESİT KURULUŞU", h.FB, 8, h.NAVY)
    rows=[]
    for z in P.ZONES:
        rows.append([z[0], f"{P.ZON_M2[z[0]]:.2f}".replace(".",","), z[2], z[3]])
    rows.append(["ISLAK HACİM (2 blok)", f"{P.A['islak_toplam']:.2f}".replace(".",","),
                 "Seramik R11 kaymaz + su yalıtımı", "—"])
    yy=h.tablo(c, x2, yy-7*mm, [("Bölge",0.34),("m²",0.12),("Kaplama",0.38),("Kalınlık",0.16)],
               rows, w2, satir_h=6.4*mm, fs=6.3, hizala=["l","r","l","c"])
    # kesit detayi
    h.txt(c, x2, yy-8*mm, "KESİT — ARENA / SERBEST AĞIRLIK ZEMİNİ", h.FB, 8, h.NAVY)
    kx, ky, kw2 = x2, yy-58*mm, w2
    katman=[("Kauçuk karo 40 mm — EPDM üst katman", 7.0, HexColor("#3A4048")),
            ("Titreşim matı 10 mm — darbe/gürültü yalıtımı", 3.2, HexColor("#B87333")),
            ("Şap / tesviye tabakası (mevcut, tamir edilerek)", 4.0, HexColor("#C9CCD1")),
            ("Mevcut betonarme döşeme", 8.0, HexColor("#8A8F98"))]
    cy=ky+34*mm
    for ad,tk,col in katman:
        c.setFillColor(col); c.rect(kx, cy-tk*mm, kw2*0.42, tk*mm, 0, 1)
        c.setStrokeColor(HexColor("#FFFFFF")); c.setLineWidth(0.4)
        c.rect(kx, cy-tk*mm, kw2*0.42, tk*mm, 1, 0)
        h.txt(c, kx+kw2*0.44, cy-tk*mm+tk*mm/2-1.4*mm, ad, h.F, 6.2, h.INK)
        cy-=tk*mm
    c.setStrokeColor(h.NAVY); c.setLineWidth(0.5)
    c.line(kx-3*mm, cy, kx-3*mm, ky+34*mm)
    h.txt(c, kx-4*mm, (cy+ky+34*mm)/2-1.4*mm, "≈62 mm", h.F, 5.6, h.NAVY, "r")
    h.txt(c, x2, cy-9*mm, "KESİT — ISLAK HACİM ZEMİNİ (SEÇENEK A)", h.FB, 8, h.NAVY)
    ky2 = cy-15*mm; cy2 = ky2
    for ad,tk,col in [("Seramik R11 kaymaz + yapıştırıcı", 3.2, HexColor("#9FB8C4")),
                      ("Şap — eğimli, süzgeçe doğru %1,5", 4.5, HexColor("#C9CCD1")),
                      ("Çift bileşenli su yalıtımı (dönüş 30 cm)", 2.4, HexColor("#2E7D5B")),
                      ("Hafif dolgu — 15–20 cm kot yükseltme", 9.0, HexColor("#B87333")),
                      ("Mevcut betonarme döşeme", 7.0, HexColor("#8A8F98"))]:
        c.setFillColor(col); c.rect(x2, cy2-tk*mm, w2*0.42, tk*mm, 0, 1)
        c.setStrokeColor(HexColor("#FFFFFF")); c.setLineWidth(0.4)
        c.rect(x2, cy2-tk*mm, w2*0.42, tk*mm, 1, 0)
        h.txt(c, x2+w2*0.44, cy2-tk*mm+tk*mm/2-1.4*mm, ad, h.F, 6.2, h.INK)
        cy2-=tk*mm
    c.setStrokeColor(h.NAVY); c.setLineWidth(0.5); c.line(x2-3*mm, cy2, x2-3*mm, ky2)
    h.txt(c, x2-4*mm, (cy2+ky2)/2-1.4*mm, "≈26 cm", h.F, 5.6, h.NAVY, "r")
    h.txt(c, x2, cy2-5*mm, "Seçenek B uygulanırsa hafif dolgu katmanı çıkar, kot değişmez.", h.F, 6.0, h.GREY)
    h.notkutu(c, x2, cy2-9*mm, w2, "AKUSTİK VE TİTREŞİM — NEDEN AYRI KALEM",
      "Üst katta konut bulunduğu VARSAYILMIŞTIR (yerinde doğrulanacak). Serbest ağırlık alanında "
      "ağırlık düşürme darbesi taşıyıcı döşemeden yapısal ses olarak iletilir; bu, ruhsat sonrası "
      "şikâyet ve kapatma riskinin bir numaralı kaynağıdır. Önlem: 40 mm kauçuk karonun altına 10 mm "
      "titreşim matı serilmesi (poz 04.02) ve işletme kuralı olarak ağırlık düşürmenin yasaklanması. "
      "Üstte konut olmadığı tespit edilirse poz 04.02 bütçeden çıkarılabilir.",
      fs=6.4, acc=h.COPPER)
    h.txt(c, x2, BOT+52*mm, "MALZEME SEÇİM GEREKÇELERİ", h.FB, 8, h.NAVY)
    h.tablo(c, x2, BOT+46*mm, [("Seçim",0.30),("Gerekçe",0.70)], [
      ["Kauçuk 40 mm (arena)","100 kg üzeri yüklerde düşürme darbesini karşılayan asgari kalınlık; "
       "ince kaplamada döşeme ve ekipman zarar görür"],
      ["Kauçuk 20 mm (fonksiyonel)","Ağırlık düşürülmeyen alanda yeterli; 40 mm'e göre m² maliyeti "
       "yaklaşık %40 düşük — bütçe bu ayrımla korunuyor"],
      ["LVT (dinlenme + giriş)","Yönetmelik dinlenme salonu için halıfleks/parke ve benzeri istiyor; "
       "LVT ıslak temizliğe kauçuktan daha uygun ve fotojenik"],
      ["Seramik R11 (ıslak hacim)","Islak zeminde kaymazlık sınıfı; R10 duş önünde yetersiz kalır"],
    ], w2, satir_h=6.4*mm, fs=6.2, hizala=["l","l"])

# ══ 7 ISLAK HACİM ══════════════════════════════════════════════════════════════
def s07(c):
    _sayfa(c, 7, "Islak hacim çözümü", "İki blok · 2 duş + 2 WC · gider kotu için A/B karşılaştırması")
    y=TOP; pw=CW*0.40
    v=D.View(c, L, BOT+10*mm, pw, y-BOT-12*mm,
             geoms=[P.ERKEK.buffer(0.9), P.KADIN.buffer(0.9)])
    _ctx = P.ERKEK.union(P.KADIN).buffer(0.9).envelope
    D.poly(v, P.SALON.intersection(_ctx), fill=HexColor("#F2F3F5"))
    D.poly(v, P.SALON.buffer(0.20, join_style=2).difference(P.SALON).intersection(_ctx), fill=D.C_DUVAR)
    for ad,d in P.ISLAK.items():
        D.poly(v, d["soyunma"], fill=HexColor("#DCE7EC"))
        D.poly(v, d["dus"], fill=HexColor("#A9C6D4"))
        D.poly(v, d["wc"],  fill=HexColor("#BFD3DC"))
    for _b in (P.ERKEK, P.KADIN):
        D.poly(v, _b.buffer(0.20, join_style=2).difference(_b), fill=D.C_DUVAR)
        D.poly(v, _b, stroke=HexColor("#3A3F46"), lw=0.7)
    D.ic_bolme(v); D.kapilar(v); D.mobilya(v)
    for ad,d in P.ISLAK.items():
        for n,lbl in (("soyunma",ad),("dus","DUŞ"),("wc","WC")):
            q=d[n].representative_point()
            D.etiket(v,(q.x,q.y),lbl,5.6,h.NAVY,h.FB,"c",dy=1.6)
            D.etiket(v,(q.x,q.y),f"{P.ISLAK_M2_DETAY[ad][n]:.2f} m²".replace(".",","),
                     4.8,h.COPPER,h.F,"c",dy=-2.8)
    D.olcek_cubugu(v, L+5*mm, BOT+13*mm, 2)
    h.lejant(c, L+5*mm, BOT+3*mm, [(HexColor("#DCE7EC"),"Soyunma"),(HexColor("#A9C6D4"),"Duş"),
                                   (HexColor("#BFD3DC"),"WC"),(D.C_YENI,"Yeni bölme")])
    x2=L+pw+7*mm; w2=CW-pw-7*mm; yy=y
    h.txt(c, x2, yy-4*mm, "MEKÂN PROGRAMI VE YÖNETMELİK KARŞILIĞI", h.FB, 8, h.NAVY)
    rows=[]
    for ad,d in P.ISLAK.items():
        rows.append([f"{ad} soyunma", f"{P.ISLAK_M2_DETAY[ad]['soyunma']:.2f}".replace(".",","),
                     "12 göz dolap + bank", "Dolap/askılık şartı"])
        rows.append([f"{ad} duş", f"{P.ISLAK_M2_DETAY[ad]['dus']:.2f}".replace(".",","),
                     "Duş teknesi + cam kabin", "Soyunma içinde duş"])
        rows.append([f"{ad} WC", f"{P.ISLAK_M2_DETAY[ad]['wc']:.2f}".replace(".",","),
                     "Klozet + lavabo", "Soyunma içinde tuvalet"])
    rows.append(["TOPLAM ISLAK HACİM", f"{P.A['islak_toplam']:.2f}".replace(".",","),
                 "2 duş + 2 WC + 2 soyunma", "Karma kullanım şartı sağlanır"])
    yy=h.tablo(c, x2, yy-7*mm, [("Hacim",0.26),("m²",0.11),("Donanım",0.31),("Yönetmelik karşılığı",0.32)],
               rows, w2, satir_h=5.6*mm, fs=6.2, hizala=["l","r","l","l"])
    h.txt(c, x2, yy-8*mm, "GİDER KOTU — SEÇENEK KARŞILAŞTIRMASI", h.FB, 8, h.NAVY)
    mA=P.maliyet("O","A"); mB=P.maliyet("O","B")
    dA=[r for r in P.B if r[0]=="03.08"][0]; dB=[r for r in P.B if r[0]=="03.09"][0]
    rows2=[["Kalem bedeli", h.bant(dA[4]*dA[5], dA[4]*dA[6]), h.bant(dB[4]*dB[5], dB[4]*dB[6])],
           ["Toplam bütçeye etkisi", h.bant(*mA["toplam"]), h.bant(*mB["toplam"])],
           ["Kot serbestliği", "Sınırlı — mevcut kota bağımlı", "Tam serbest"],
           ["Kullanım etkisi", "15–20 cm basamak / rampa doğar", "Kot değişmez, eşiksiz"],
           ["Tavan yüksekliği etkisi", "Islak hacimde 15–20 cm kayıp", "Etkisi yok"],
           ["Bakım / arıza riski", "Yok — mekanik parça içermez", "Var — pompa arızası kullanımı durdurur"],
           ["Elektrik bağımlılığı", "Yok", "Var — kesintide kullanılamaz"],
           ["Gürültü", "Yok", "Öğütücü çalışma sesi"],
           ["ÖNERİ", "TERCİH EDİLEN — kot elverirse", "Yalnız A uygulanamazsa"]]
    yy=h.tablo(c, x2, yy-13*mm, [("Karşılaştırma ölçütü",0.30),("SEÇENEK A — zemin yükseltme",0.35),
                                 ("SEÇENEK B — atık su pompası",0.35)], rows2, w2,
               satir_h=5.6*mm, fs=6.2, hizala=["l","l","l"])
    h.txt(c, x2, yy-8*mm, "TESİSAT ŞEMASI — İLKE", h.FB, 8, h.NAVY)
    sy=yy-14*mm; sh_=30*mm; sw=w2
    c.setFillColor(HexColor("#F4F7FA")); c.setStrokeColor(h.GREY_L); c.setLineWidth(0.5)
    c.roundRect(x2, sy-sh_, sw, sh_, 1.6*mm, 1, 1)
    nx=[x2+sw*f for f in (0.10,0.30,0.50,0.70,0.90)]
    ny=sy-sh_*0.42
    etik=[("DUŞ E","#A9C6D4"),("WC E","#BFD3DC"),("ŞAFT","#B87333"),("DUŞ K","#A9C6D4"),("WC K","#BFD3DC")]
    c.setStrokeColor(h.NAVY2); c.setLineWidth(1.2)
    c.line(nx[0], ny-6*mm, nx[4], ny-6*mm)
    for i,(lbl,col) in enumerate(etik):
        c.setFillColor(HexColor(col)); c.circle(nx[i], ny, 3.4*mm, 0, 1)
        h.txt(c, nx[i], ny-1.2*mm, lbl, h.FB, 4.6, h.NAVY if i!=2 else HexColor("#FFFFFF"), "c")
        c.setStrokeColor(h.NAVY2); c.setLineWidth(0.8); c.line(nx[i], ny-3.4*mm, nx[i], ny-6*mm)
    h.txt(c, (nx[0]+nx[4])/2, ny-9.6*mm, "TEK TOPLAMA HATTI  →  MEVCUT PİS SU BAĞLANTISI", h.FB, 5.4, h.NAVY, "c")
    h.txt(c, x2+4*mm, sy-5*mm, "Her iki blokta duş ve WC bitişik; tek düşey şaft, tek gider hattı.", h.F, 5.8, h.GREY)
    h.txt(c, x2+4*mm, sy-sh_+3.4*mm, "Sıcak su: blok başına 6 kW elektrikli ani ısıtıcı — bekleme süresi yok.", h.F, 5.8, h.GREY)
    h.notkutu(c, x2, sy-sh_-6*mm, w2, "Kritik Sıra",
      "Her iki blokta duş ve WC bitişik konumlandırılmış, tek bir düşey tesisat şaftı ve tek gider "
      "toplama hattı ile mevcut bağlantıya yönlendirilmiştir; böylece kırım ve hat uzunluğu asgaride "
      "kalır. Sıcak su, iki blok için ayrı ayrı 6 kW elektrikli ani ısıtıcı ile üretilir — yönetmeliğin "
      "'çalışma boyunca sürekli sıcak su' şartı boyler bekleme süresi olmadan karşılanır. Binada "
      "doğalgaz bulunduğu tespit edilirse yoğuşmalı kombi hem işletme gideri hem de elektrik "
      "abonelik gücü açısından daha ekonomiktir; bu durumda poz 03.07 revize edilir. "
      "SÖKÜM SONRASI İLK İŞ: mevcut pis su bağlantısının kotunun ve konumunun ölçülmesi — "
      "A/B kararı bu ölçüme bağlıdır ve zemin imalatlarının tamamını kilitler.", fs=6.3, acc=h.COPPER)

# ══ 8 ELEKTRİK + MEKANİK ═══════════════════════════════════════════════════════
def s08(c):
    _sayfa(c, 8, "Elektrik ve mekanik şema", "Aydınlatma lux hedefleri · havalandırma debisi · klima yerleşimi")
    y=TOP; pw=CW*0.46
    v=D.View(c, L, BOT+10*mm, pw, y-BOT-12*mm)
    D.poly(v, P.SALON, fill=HexColor("#F4F6F8"))
    for ad,d in P.ISLAK.items(): D.poly(v, d["tum"], fill=HexColor("#E7EDF1"))
    D.kabuk(v); D.ic_bolme(v); D.cephe(v)
    from shapely.geometry import LineString as _LS
    arm = D.aydinlatma_izgara(v)
    for px,py in arm:
        D.poly(v, _LS([(px-0.62,py),(px+0.62,py)]).buffer(0.075,cap_style=2),
               fill=HexColor("#E8B93B"), stroke=HexColor("#8A6A12"), lw=0.3)
    for ad,d in P.ISLAK.items():
        for n in ("soyunma","dus","wc"):
            q=d[n].representative_point()
            D.poly(v, _LS([(q.x-0.32,q.y),(q.x+0.32,q.y)]).buffer(0.065,cap_style=2),
                   fill=HexColor("#E8B93B"), stroke=HexColor("#8A6A12"), lw=0.25)
    # klima
    for i,(kx,ky) in enumerate([(2.10,7.95),(7.10,7.95),(3.10,0.55)]):
        from shapely.geometry import box as _bx
        D.poly(v, _bx(kx-0.55,ky-0.16,kx+0.55,ky+0.16), fill=HexColor("#2F6FB3"))
        D.etiket(v,(kx,ky+0.42),f"K{i+1}",4.8,HexColor("#2F6FB3"),h.FB,"c")
    # taze hava / egzoz
    for (ax,ay,lbl,col) in [(0.95,8.05,"TH",HexColor("#2E7D5B")),(8.90,7.95,"EG",HexColor("#C8322B")),
                            (9.60,2.60,"EG",HexColor("#C8322B"))]:
        c.setFillColor(col); px,py=v.p((ax,ay)); c.circle(px,py,1.9*mm,0,1)
        h.txt(c,px,py-1.2*mm,lbl,h.FB,4.4,HexColor("#FFFFFF"),"c")
    D.kuzey_ok(v, L+pw-13*mm, y-13*mm); D.olcek_cubugu(v, L+5*mm, BOT+13*mm)
    h.lejant(c, L+5*mm, BOT+3*mm, [(HexColor("#E8B93B"),"Lineer LED armatür"),
        (HexColor("#2F6FB3"),"Split klima iç ünite"),(HexColor("#2E7D5B"),"Taze hava"),
        (HexColor("#C8322B"),"Egzoz")])
    x2=L+pw+7*mm; w2=CW-pw-7*mm; yy=y
    h.txt(c, x2, yy-4*mm, "AYDINLATMA — LUX HEDEFİ VE ARMATÜR ADEDİ", h.FB, 8, h.NAVY)
    rows=[[a[0], f"{a[1]:.2f}".replace(".",","), str(a[2]), h.tl(a[3]),
           "Lineer 40 W" if a[5]=="lineer" else "IP44 18 W", str(a[4])] for a in P.AYDINLATMA]
    rows.append(["TOPLAM","","","", f"{P.ARMATUR_ADET} lineer + {P.DOWNLIGHT_ADET} downlight",
                 str(P.ARMATUR_ADET+P.DOWNLIGHT_ADET)])
    yy=h.tablo(c, x2, yy-7*mm, [("Bölge",0.30),("m²",0.11),("Lux",0.09),("Gerekli lümen",0.19),
                                ("Armatür tipi",0.19),("Adet",0.12)],
               rows, w2, satir_h=5.6*mm, fs=6.2, hizala=["l","r","r","r","l","r"])
    h.txt(c, x2, yy-8*mm, "HAVALANDIRMA VE İKLİMLENDİRME", h.FB, 8, h.NAVY)
    rows2=[["Tasarım kullanıcı sayısı", f"{P.KISI} kişi ({P.V['kisi_kapasite'][0]} sporcu + {P.V['personel'][0]} personel)"],
           ["İç hacim (tavan 3,20 m varsayımı)", f"{h.tl(P.HACIM,1)} m³"],
           ["Taze hava debisi — tasarım", f"{h.tl(P.TAZE)} m³/h"],
           ["Kişi başı taze hava", f"{P.TAZE/P.KISI:.0f} m³/h·kişi (yasal asgari 30)"],
           ["Hava değişim sayısı", f"{P.ACH:.2f} h⁻¹".replace(".",",")],
           ["Islak hacim egzozu", f"{P.EGZOZ_ISLAK} m³/h (2 duş × 80 + 2 WC × 40)"],
           ["Soğutma yükü — hesaplanan", f"{h.tl(P.SOGUTMA_W)} W = {h.tl(P.SOGUTMA_BTU)} BTU/h"],
           ["Klima çözümü", f"{P.ADET_KLIMA} bölge · {h.tl(P.KLIMA_BTU)} BTU kurulu (%{P.SOGUTMA_MARJ} marj)"],
           ["Salon ısısı — yönetmelik / tasarım", "≥18 °C / 20–22 °C"]]
    yy=h.tablo(c, x2, yy-13*mm, [("Parametre",0.48),("Değer",0.52)], rows2, w2,
               satir_h=5.6*mm, fs=6.2, hizala=["l","r"])
    h.txt(c, x2, yy-8*mm, "ELEKTRİK YÜK TABLOSU", h.FB, 8, h.NAVY)
    rows3=[[k, f"{val:.2f}".replace(".",",")] for k,val in P.ELEKTRIK_YUK]
    rows3.append(["TOPLAM KURULU GÜÇ", f"{P.KURULU_KW:.1f}".replace(".",",")])
    rows3.append(["TALEP GÜCÜ (eşzamanlılık 0,75)", f"{P.TALEP_KW:.1f}".replace(".",",")])
    rows3.append(["ÖNERİLEN ABONELİK", "Trifaze 3×25 A · ≥16 kW"])
    yy=h.tablo(c, x2, yy-13*mm, [("Yük kalemi",0.70),("kW",0.30)], rows3, w2,
               satir_h=5.4*mm, fs=6.2, hizala=["l","r"])
    h.notkutu(c, x2, yy-6*mm, w2, "Ayrıntı: disiplin projeleri",
      "Bu sayfa mekanik ve elektriğin özetidir. Kanal güzergâhları, menfez debileri, klima "
      "yerleşimi, sıhhi tesisat kolon şeması, aydınlatma ve priz planları, zayıf akım planı ve "
      "pano tek hat şeması ayrı dosyalardadır: Gym_Mekanik_Proje_A3.pdf (6 pafta) ve "
      "Gym_Elektrik_Proje_A3.pdf (6 pafta). Bunların birim fiyat sütunu boş BoQ karşılıkları "
      "Gym_Mekanik_BoQ.xlsx ve Gym_Elektrik_BoQ.xlsx dosyalarıdır.", fs=6.3, acc=h.COPPER)
    h.notkutu(c, x2, yy-46*mm, w2, "Doğrulanacak — hesabın tek bilinmeyeni",
      "Mevcut pano gücü ve trifaze durumu BİLİNMİYOR. Hesaplanan 12,1 kW talep gücü mevcut abonelikle "
      "karşılanamazsa dağıtım şirketine güç artırım başvurusu yapılır; bu başvuru 3–8 hafta sürebilir ve "
      "takvime eklenmelidir. Tavan yüksekliği de varsayımdır (3,20 m): 2,80 m çıkarsa armatür adedi artar, "
      "3,60 m çıkarsa taze hava debisi yükselir. Her iki değer de yerinde ölçüm günü netleşir.",
      fs=6.3, acc=h.RED)

# ══ 9 YOL HARİTASI ═════════════════════════════════════════════════════════════
def s09(c):
    _sayfa(c, 9, "Yol haritası — ruhsat ve başvurular", "Sıra kritik: önce GSİM, sonra belediye")
    y=TOP
    h.kutu(c, L, y-14*mm, CW, 12*mm, HexColor("#F4F7FA"), h.NAVY2)
    seq=["TESPİT","GSİM ÖN GÖRÜŞ","PROJE","TADİLAT","İTFAİYE + SAĞLIK",
         "GSİM BAŞVURU","KOMİSYON TETKİKİ","TESCİL","BELEDİYE RUHSATI","VERGİ / SGK"]
    bw=(CW-10*mm)/len(seq)
    for i,s in enumerate(seq):
        x=L+5*mm+i*bw
        col=h.COPPER if i in (1,6,8) else h.NAVY2
        c.setFillColor(col); c.rect(x, y-11.2*mm, bw-2.2*mm, 6.4*mm, 0, 1)
        h.txt(c, x+(bw-2.2*mm)/2, y-9.2*mm, s, h.FB, 5.0, HexColor("#FFFFFF"), "c")
        if i<len(seq)-1:
            c.setFillColor(h.GREY)
            p=c.beginPath(); xa=x+bw-2.1*mm
            p.moveTo(xa, y-6.6*mm); p.lineTo(xa+1.8*mm, y-8.0*mm); p.lineTo(xa, y-9.4*mm); p.close()
            c.drawPath(p,0,1)
    y-=18*mm
    tw_=CW*0.66
    rows=[[r[0],r[1],r[2],r[3],r[4],r[5]] for r in P.YOL]
    yy=h.tablo(c, L, y, [("#",0.04),("Kurum",0.15),("Yapılacak iş",0.47),("Kim",0.11),("Süre",0.11),("Ön koşul",0.08)],
               rows, tw_, satir_h=6.0*mm, fs=6.2, hizala=["c","l","l","l","c","c"])
    x2=L+tw_+7*mm; w2=CW-tw_-7*mm
    h.txt(c, x2, y-4*mm, "EVRAK KONTROL LİSTESİ", h.FB, 8, h.NAVY)
    cy=y-10*mm
    for e in P.EVRAK:
        c.setStrokeColor(h.NAVY2); c.setLineWidth(0.6); c.rect(x2, cy-0.6*mm, 2.6*mm, 2.6*mm, 1, 0)
        n=h.para(c, x2+5*mm, cy+1.4*mm, e, w2-6*mm, h.F, 6.2, h.INK, 8.0)
        cy=n-3.4*mm
    h.kutu(c, x2, cy-58*mm, w2, 55*mm, HexColor("#FDF3EC"), h.COPPER)
    h.txt(c, x2+5*mm, cy-11*mm, "HARÇ · ÜCRET KALEMLERİ", h.FB, 7.4, h.COPPER)
    rows2=[["GSİM tesis tescil ücreti (bir defaya mahsus)","Genel Müdürlükçe belirlenir"],
           ["İBB itfaiye denetim / rapor ücreti","m² esaslı yıllık tarife"],
           ["Belediye işyeri açma ve çalışma ruhsatı harcı","Meclis tarifesi"],
           ["Sağlık müdürlüğü denetim / rapor","Tarifeye göre"],
           ["Proje müellifi ve müşavirlik","Sözleşmeye göre"]]
    yy2=h.tablo(c, x2+5*mm, cy-14*mm, [("Kalem",0.62),("Tutar",0.38)], rows2, w2-10*mm,
                satir_h=5.2*mm, fs=5.9, zebra=False, hizala=["l","r"])
    h.para(c, x2+5*mm, yy2-3*mm,
      "Tutarlar her yıl güncellenir; başvuru öncesi ilgili kurumdan teyit alınmalıdır. "
      "Nakit planında 85.000–175.000 TL bandı öngörülmüştür.", w2-10*mm, h.F, 5.8, h.GREY, 7.4)
    h.txt(c, L, yy-9*mm, "SÜREÇTE SIK YAPILAN HATALAR", h.FB, 8.5, h.NAVY)
    bw2=(tw_-2*5*mm)/3
    for i,(ttl,body) in enumerate([
      ("SIRAYI TERS KURMAK",
       "Önce belediyeye gidilmesi. Belediye GSİM uygunluk yazısını istediği için dosya geri döner ve "
       "harç ile zaman kaybedilir. Doğru sıra: GSİM → belediye."),
      ("MEKÂNI KONTROL ETMEDEN KİRALAMAK",
       "Kaynaklarda en sık anılan hata. Tavan yüksekliği, m² ve havalandırma kontrol edilmeden sözleşme "
       "imzalanıyor. Bu projede kira imzalanmış durumda — bu yüzden 3. sayfa hazırlandı."),
      ("KOMİSYON TETKİKİNE ERKEN GİRMEK",
       "Komisyon tesisi bitmiş hâlde görmek ister. Eksik tesisle yapılan tetkik olumsuz tutanakla sonuçlanır "
       "ve ikinci tur için yeniden sıra beklenir.")]):
        h.kart(c, L+i*(bw2+5*mm), yy-15*mm-34*mm, bw2, 34*mm, str(i+1), ttl, body, h.RED)
    h.txt(c, L, BOT+3.5*mm, "Toplam ruhsat zinciri tahmini 16–28 hafta. Tadilat (adım 3) ile evrak "
          "süreçlerinin paralel yürütülmesi bu süreyi kısaltır; ancak adım 1 tamamlanmadan imalata "
          "başlanması, tescil reddi hâlinde yapılan tüm harcamayı riske atar.", h.F, 6.2, h.RED)

# ══ 10 MALİYET ═════════════════════════════════════════════════════════════════
def s10(c):
    _sayfa(c, 10, "Maliyet planı", f"Kalem bazlı · düşük–yüksek bant · {P.FIYAT_TARIH}")
    y=TOP; tw_=CW*0.58
    mO=P.maliyet("O","A"); mM=P.maliyet("M","A")
    rows=[]
    for g in P.GRUPLAR:
        lo,hi=mO["gruplar"][g]
        pay=100*(lo+hi)/2/((mO["imalat"][0]+mO["imalat"][1])/2)
        rows.append([g, h.tl(lo), h.tl(hi), f"%{pay:.0f}"])
    rows.append(["İMALAT ARA TOPLAMI", h.tl(mO["imalat"][0]), h.tl(mO["imalat"][1]), "%100"])
    rows.append([f"Şantiye genel giderleri (%{int(P.V['santiye_gider'][0]*100)})",
                 h.tl(mO["santiye"][0]), h.tl(mO["santiye"][1]), ""])
    rows.append(["Beklenmedik giderler (%15)", h.tl(mO["beklenmedik"][0]), h.tl(mO["beklenmedik"][1]), ""])
    rows.append(["GENEL TOPLAM — ÖNERİLEN", h.tl(mO["toplam"][0]), h.tl(mO["toplam"][1]), ""])
    yy=h.tablo(c, L, y, [("Maliyet başlığı",0.48),("Düşük (TL)",0.20),("Yüksek (TL)",0.20),("Pay",0.12)],
               rows, tw_, satir_h=6.0*mm, fs=6.5, hizala=["l","r","r","r"])
    h.txt(c, L, yy-8*mm, "SENARYO KARŞILAŞTIRMASI", h.FB, 8, h.NAVY)
    rows2=[["MİNİMUM — yalnız zorunlu kalemler", h.tl(mM["toplam"][0]), h.tl(mM["toplam"][1]),
            f"{h.tl(mM['toplam'][0]/P.A['ic_toplam'])}–{h.tl(mM['toplam'][1]/P.A['ic_toplam'])}"],
           ["ÖNERİLEN — akustik, ayna, zayıf akım, tabela dâhil", h.tl(mO["toplam"][0]), h.tl(mO["toplam"][1]),
            f"{h.tl(mO['toplam'][0]/P.A['ic_toplam'])}–{h.tl(mO['toplam'][1]/P.A['ic_toplam'])}"],
           ["ÖNERİLEN + Seçenek B (pompa)", h.tl(P.maliyet("O","B")["toplam"][0]), h.tl(P.maliyet("O","B")["toplam"][1]),
            f"{h.tl(P.maliyet('O','B')['toplam'][0]/P.A['ic_toplam'])}–{h.tl(P.maliyet('O','B')['toplam'][1]/P.A['ic_toplam'])}"]]
    yy=h.tablo(c, L, yy-13*mm, [("Senaryo",0.46),("Düşük (TL)",0.18),("Yüksek (TL)",0.18),("TL/m²",0.18)],
               rows2, tw_, satir_h=6.4*mm, fs=6.5, hizala=["l","r","r","r"])
    h.txt(c, L, yy-8*mm, "MALİYET DAĞILIMI — BAŞLIK BAZINDA BANT", h.FB, 8, h.NAVY)
    veri=sorted([(g, *mO["gruplar"][g]) for g in P.GRUPLAR], key=lambda r:-(r[1]+r[2]))
    by=D.bar_araligi(c, L, yy-16*mm, tw_, 70*mm, veri)
    h.notkutu(c, L, by-2*mm, tw_, "TL/m² NEDEN YÜKSEK GÖRÜNÜYOR?",
      "2026 İstanbul konut yenilemesi için sıkça anılan çıpalar bu projeye "
      "doğrudan uygulanamaz. Birinci neden: bu bir ticari dönüşümdür — ıslak hacmin komple yenilenmesi, "
      "mekanik havalandırma, yangın algılama, engelli düzenlemesi ve spor zemini konut yenilemesinde "
      "bulunmayan kalemlerdir. İkinci ve daha belirleyici neden ölçek: pano, yangın algılama, "
      "havalandırma seti, tabela ve tesisat gibi götürü kalemler alandan büyük ölçüde bağımsızdır ve "
      "bu 103,78 m²'lik birimde imalat bedelinin yaklaşık %40'ını oluşturur. Aynı işler 250 m²'lik bir "
      f"birimde yapılsaydı TL/m² yarıya inerdi. Bu nedenle tek m² fiyatı kullanılmamış, {len(P.B)} poz "
      "kalem bazlı kurulmuştur.", fs=6.4, acc=h.NAVY2)
    x2=L+tw_+7*mm; w2=CW-tw_-7*mm
    h.txt(c, x2, y-4*mm, "AÇILIŞ ÖNCESİ NAKİT İHTİYACI", h.FB, 8, h.NAVY)
    rows3=[]; tl_=th=0
    for ad,lo,hi in P.NAKIT:
        if lo is None: lo,hi = mO["toplam"]
        tl_+=lo; th+=hi
        rows3.append([ad, h.tl(lo), h.tl(hi)])
    rows3.append(["TOPLAM AÇILIŞ ÖNCESİ NAKİT", h.tl(tl_), h.tl(th)])
    yy3=h.tablo(c, x2, y-7*mm, [("Kalem",0.52),("Düşük (TL)",0.24),("Yüksek (TL)",0.24)], rows3, w2,
                satir_h=6.2*mm, fs=6.4, hizala=["l","r","r"])
    h.txt(c, x2, yy3-8*mm, "KARŞILAŞTIRMA ÇIPALARI (kendi hesabın yerine geçmez)", h.FB, 7.2, h.NAVY)
    rows4=[["Butik salon başlangıç bütçesi — 2026 kaynakları","500.000 – 1.000.000 TL"],
           ["Orta ölçekli salon — 2026 kaynakları","1.500.000 – 3.000.000 TL (ekipman dâhil)"],
           ["Bu projenin tadilat bandı (önerilen)", h.bant(*mO["toplam"])],
           ["Bu projenin açılış öncesi toplam nakdi", h.bant(tl_, th)]]
    yy4=h.tablo(c, x2, yy3-13*mm, [("Referans",0.58),("Tutar",0.42)], rows4, w2,
                satir_h=6.0*mm, fs=6.2, hizala=["l","r"])
    h.notkutu(c, x2, yy4-8*mm, w2, "EKİPMAN — BÜTÇE DIŞI",
      "TRIMODE arena ve tüm antrenman ekipmanı işverence temin edilmiştir; bu dosyadaki hiçbir "
      "maliyet kaleminde yer almaz. Ekipman yerleşimi mevcut ölçüler (244×62, 175×232, 155×39 ×2, "
      "84×150, 245×74 ×2 cm ve 10,60 m² altıgen arena) üzerinden çözülmüştür. Marka/model listesi "
      "işverenden alındığında BoQ'nun 3. sayfasına bilgi amaçlı işlenmelidir. "
      "Nakliye, montaj ve devreye alma bedelleri tedarikçi kapsamında değilse ayrıca bütçelenmelidir.",
      fs=6.3, acc=h.COPPER)
    h.notkutu(c, x2, yy4-8*mm-46*mm, w2, "BİRİM FİYATLAR NEREDEN GELİYOR — REV E KALİBRASYONU",
      "Birim fiyatlar, işverenin kendi referans projesi AQUA FLORYA / SALTBAE'nin gerçekleşen "
      "sözleşme fiyatlarıyla (Vogelkopp İnşaat kesin hakedişi, 13.05.2025, KDV hariç) kalibre edilmiş "
      "ve Eylül 2026'ya ×1,40 ile eskale edilmiştir. Referanstan alınan başlıca oranlar: alçıpan "
      "bölme (çift yüz çift kat) 2.450 TL/m², alçıpan asma tavan 1.450 TL/m², seramik işçiliği "
      "700–725 TL/m², şap 600 TL/m², çimento esaslı su yalıtımı 610 TL/m², düz işçi yevmiyesi "
      "3.500 TL. Rev C'deki mimari birim fiyatlar bu referansın belirgin altında kalmıştı (örneğin "
      "alçıpan bölme 663 TL/m²); Rev E'de tüm mimari kalemler yeniden fiyatlandırılmış, mimari "
      "imalat bedeli yaklaşık 2,1 kat artmıştır. Mekanik ve elektrik kalemleri, referans projenin "
      "kapsamı (restoran mutfağı, VRF, soğuk oda, 630 A abonelik) bu projeyle karşılaştırılabilir "
      "olmadığı için Rev C değerleriyle korunmuştur. Poz bazlı ayrıntı ve metraj cetvelleri için "
      "Gym_Kesif_Ozeti_BoQ.xlsx dosyasına bakınız.", fs=6.3, acc=h.NAVY2)

# ══ 11 İŞ PROGRAMI ═════════════════════════════════════════════════════════════
def s11(c):
    _sayfa(c, 11, "İş programı ve şantiye sırası", f"{len(P.PROGRAM)} adım · {P.PROGRAM_HAFTA:.0f} hafta · kritik yol ıslak hacimden geçer")
    y=TOP
    lw_=CW*0.42; gx=L+lw_+6*mm; gw=CW-lw_-6*mm-16*mm
    hafta=int(math.ceil(P.PROGRAM_HAFTA)); cell=gw/hafta
    h.txt(c, L, y-4*mm, "UYGULAMA SIRASI", h.FB, 8, h.NAVY)
    h.txt(c, gx, y-4*mm, "TAKVİM (hafta)", h.FB, 8, h.NAVY)
    c.setFillColor(h.NAVY); c.rect(gx, y-11*mm, gw, 6*mm, 0, 1)
    for i in range(hafta):
        h.txt(c, gx+i*cell+cell/2, y-9.2*mm, str(i+1), h.FB, 5.4, HexColor("#FFFFFF"), "c")
    cy=y-11*mm; rh=6.8*mm
    for no, ad, bas, sur, kr in P.PROGRAM:
        if (no-1) % 2 == 0:
            c.setFillColor(HexColor("#F4F5F7")); c.rect(L, cy-rh, CW-16*mm, rh, 0, 1)
        c.setFillColor(h.COPPER if kr else h.NAVY2)
        c.circle(L+3.4*mm, cy-rh/2, 2.2*mm, 0, 1)
        h.txt(c, L+3.4*mm, cy-rh/2-1.5*mm, str(no), h.FB, 5.0, HexColor("#FFFFFF"), "c")
        h.txt(c, L+8*mm, cy-rh/2-1.6*mm, ad, h.F, 6.3, h.INK)
        c.setFillColor(h.COPPER if kr else h.NAVY2)
        c.roundRect(gx+bas*cell+0.4*mm, cy-rh+1.5*mm, sur*cell-0.8*mm, rh-3*mm, 0.8*mm, 0, 1)
        h.txt(c, gx+bas*cell+sur*cell/2, cy-rh+2.9*mm, f"{sur:g}h".replace(".",","),
              h.FB, 4.8, HexColor("#FFFFFF"), "c")
        cy -= rh
    c.setStrokeColor(h.GREY_L); c.setLineWidth(0.4)
    for i in range(hafta+1): c.line(gx+i*cell, cy, gx+i*cell, y-11*mm)
    h.lejant(c, L, cy-7*mm, [(h.COPPER,"Kritik yol — gecikmesi bitişi öteler"),
                             (h.NAVY2,"Paralel yürütülebilir")])
    bw=(CW-2*6*mm)/3
    for i,(ttl,body) in enumerate([
      ("SIRAYI BELİRLEYEN KURAL",
       "Islak hacim tesisatı ve gider kotu çözülmeden hiçbir zemin imalatına başlanamaz. Söküm biter "
       "bitmez kot ölçülür; Seçenek A/B kararı 2. haftada verilmelidir. Zemin kaplaması (adım 9) en "
       "sona bırakılır — kauçuk ve LVT, boya ve montaj sırasında zarar görmemelidir."),
      ("PARALEL YÜRÜTÜLECEK EVRAK",
       "Tadilat sürerken itfaiye ve sağlık başvuruları hazırlanır, antrenör ve doktor sözleşmeleri "
       "imzalanır, mimar onaylı vaziyet planı tamamlanır. GSİM komisyonu ancak tesis bitmiş hâlde "
       "tetkik ettiğinden, başvuru 13. adımdan önce yapılmamalıdır."),
      ("KABUL VE TESLİM",
       "Son hafta: eksik-kusur (punch) listesi, tesisat basınç testi, elektrik topraklama ölçümü, "
       "havalandırma debi ölçümü, aydınlatma lux ölçümü ve tüm garanti belgelerinin teslimi. "
       "Bu ölçüm tutanakları GSİM komisyon tetkikinde işverenin lehine kanıttır.")]):
        h.kart(c, L+i*(bw+6*mm), cy-14*mm-40*mm, bw, 40*mm, str(i+1), ttl, body, h.NAVY2)
    h.txt(c, L, cy-60*mm, "KABUL KRİTERLERİ — son hafta tutanakla belgelenecek ölçümler", h.FB, 8, h.NAVY)
    krow=[["Tesisat","Temiz su hattı basınç testi · pis su akış ve sızdırmazlık kontrolü"],
          ["Elektrik","Topraklama direnci ölçümü · kaçak akım rölesi testi · pano etiketleme"],
          ["Havalandırma","Menfez debi ölçümü — tasarım 1.000 m³/h taze hava, 240 m³/h ıslak hacim egzozu"],
          ["Aydınlatma","Lux ölçümü — arena 500, çalışma alanı 300, soyunma 200, ıslak hacim 150 lux"],
          ["Zemin","Kauçuk karo ek yerleri · titreşim matı sürekliliği · ıslak hacim eğim ve süzgeç kontrolü"],
          ["Yangın","Söndürücü yerleşimi ve etiketleri · algılama paneli devreye alma · acil aydınlatma testi"]]
    h.tablo(c, L, cy-66*mm, [("Başlık",0.16),("Ölçüm / kabul kriteri",0.84)], krow, CW,
            satir_h=6.2*mm, fs=6.3, hizala=["l","l"])

# ══ 12 RİSK + SONRAKI ADIMLAR ══════════════════════════════════════════════════
def s12(c):
    _sayfa(c, 12, "Risk kaydı ve sonraki 5 adım", "Olasılık · etki · önlem · sahip")
    y=TOP; tw_=CW*0.63
    def _c(s):
        return {"Yüksek":h.tint(h.RED,0.72),"Çok yüksek":h.tint(h.RED,0.55),
                "Orta":h.tint(h.AMBER,0.70),"Düşük":h.tint(h.GREEN,0.75)}.get(s)
    rows=[[r[0],r[1],r[2],r[3],r[4]] for r in P.RISKLER]
    yy=h.tablo(c, L, y, [("Risk",0.30),("Olasılık",0.09),("Etki",0.09),("Önlem",0.42),("Sahip",0.10)],
               rows, tw_, satir_h=6.0*mm, fs=6.1,
               renkli_sutun={1:lambda r:_c(r[1]), 2:lambda r:_c(r[2])},
               hizala=["l","c","c","l","c"])
    h.txt(c, L, yy-9*mm, "RİSK MATRİSİ", h.FB, 8.5, h.NAVY)
    mx0=L+18*mm; my0=yy-16*mm; cwid=(tw_*0.52-18*mm)/3; chg=13*mm
    olas=["Düşük","Orta","Yüksek"]; etki=["Orta","Yüksek","Çok yüksek"]
    ton={(0,0):0.86,(1,0):0.80,(2,0):0.72,(0,1):0.80,(1,1):0.68,(2,1):0.55,
         (0,2):0.72,(1,2):0.55,(2,2):0.40}
    for i,o in enumerate(olas):
        for j,e in enumerate(etki):
            x=mx0+i*cwid; yb2=my0-(j+1)*chg
            c.setFillColor(h.tint(h.RED, ton[(i,j)])); c.setStrokeColor(HexColor("#FFFFFF"))
            c.setLineWidth(1.0); c.rect(x, yb2, cwid, chg, 1, 1)
            n=sum(1 for r in P.RISKLER if r[1]==o and r[2]==e)
            if n: h.txt(c, x+cwid/2, yb2+chg/2-2*mm, str(n), h.FB, 11,
                        HexColor("#FFFFFF") if ton[(i,j)]<0.6 else h.NAVY, "c")
        h.txt(c, mx0+i*cwid+cwid/2, my0+1.6*mm, h.TR_UP(o), h.FB, 5.8, h.NAVY, "c")
    for j,e in enumerate(etki):
        h.txt(c, mx0-2*mm, my0-(j+1)*chg+chg/2-1.6*mm, h.TR_UP(e), h.FB, 5.8, h.NAVY, "r")
    h.txt(c, mx0+cwid*1.5, my0+6*mm, "OLASILIK →", h.FB, 5.6, h.GREY, "c")
    c.saveState(); c.translate(mx0-13*mm, my0-chg*1.5); c.rotate(90)
    h.txt(c, 0, 0, "ETKİ →", h.FB, 5.6, h.GREY, "c"); c.restoreState()
    h.txt(c, mx0+cwid*3+6*mm, my0-6*mm, f"{len(P.RISKLER)} risk kaydı", h.FB, 7, h.NAVY)
    h.madde_listesi(c, mx0+cwid*3+6*mm, my0-12*mm, tw_-(mx0-L)-cwid*3-6*mm, [
      "Yüksek olasılık × çok yüksek etki hücresindeki tek risk, 125/170 m² uygulamasıdır — "
      "bu yüzden yatırımın ilk adımı yazılı ön görüştür.",
      "Matristeki risklerin yarısı veri eksikliğinden kaynaklanıyor; yerinde ölçüm günü "
      "matrisin sol-üst köşesini büyük ölçüde boşaltır."], fs=6.2, lead=8.0)
    h.notkutu(c, L, my0-chg*3-8*mm, tw_, "RENDER PROMPT SETİ VE 3D MODEL",
      "Bu dosyanın eki olarak: (a) plana sadık Three.js kütle modelinden alınmış dört sabit kamera "
      "açısı, (b) bu görsellerin image-to-image yöntemiyle fotogerçekçileştirilmiş iki stil varyantı "
      "(ham endüstriyel / sıcak minimal), (c) tek dosya offline Gym_Model.html (WhatsApp'tan "
      "paylaşılabilir, render galerisi gömülü) ve (d) Render_Promptlari.md üretilmiştir. "
      "İşverenden mevcut durum fotoğrafları geldiğinde aynı kamera açılarıyla gerçek ÖNCE/SONRA "
      "çiftleri üretilebilir — bu, kredi ve ortak görüşmelerinde en ikna edici çıktıdır. "
      "Tüm görseller temsilîdir; imalat ölçüsü değildir.", fs=6.4, acc=h.NAVY2)
    x2=L+tw_+7*mm; w2=CW-tw_-7*mm
    h.txt(c, x2, y-4*mm, "SONRAKİ 5 ADIM", h.FB, 9, h.NAVY)
    cy=y-9*mm
    for no,ttl,body in P.SONRAKI_5:
        hh=25*mm
        h.kutu(c, x2, cy-hh, w2, hh, h.PAPER, h.GREY_L)
        c.setFillColor(h.COPPER); c.circle(x2+7*mm, cy-7*mm, 3.6*mm, 0, 1)
        h.txt(c, x2+7*mm, cy-8.6*mm, no, h.FB, 8, HexColor("#FFFFFF"), "c")
        h.txt(c, x2+13.5*mm, cy-8.6*mm, h.TR_UP(ttl), h.FB, 7.2, h.NAVY)
        h.para(c, x2+5*mm, cy-15*mm, body, w2-10*mm, h.F, 6.2, h.INK, 8.2)
        cy -= hh+3*mm
    h.kutu(c, x2, BOT+3*mm, w2, cy-BOT-1*mm, HexColor("#FDF3EC"), h.COPPER)
    h.txt(c, x2+5*mm, cy-8*mm, "İŞVERENDEN İSTENECEK BİLGİ", h.FB, 7.4, h.COPPER)
    ist=["DXF export (AutoCAD R2010)","Mevcut durum fotoğrafları (salon, giriş, soyunma)",
         "Ölçülmüş net m² ve tavan yüksekliği","Satın alınan ekipman listesi (marka/model/ölçü/ağırlık)",
         "Pis su bağlantısı fotoğrafı ve kotu","Elektrik pano gücü ve trifaze durumu",
         "Tapu bağımsız bölüm niteliği ve iskân","Bina bağımsız mı; değilse yönetim planı",
         "Hedeflenen açılış tarihi ve üye kapasitesi"]
    cc=cy-12*mm
    for e in ist:
        h.txt(c, x2+5*mm, cc, "•", h.FB, 6.4, h.COPPER)
        cc=h.para(c, x2+8.5*mm, cc, e, w2-14*mm, h.F, 6.2, h.INK, 8.0)-1.2*mm

# ══ BUILD ══════════════════════════════════════════════════════════════════════
def build(path="output/Gym_Donusum_Dosyasi_A3.pdf"):
    c = canvas.Canvas(path, pagesize=(W, HH))
    c.setTitle(f"Maltepe / İdealtepe — Gym Dönüşüm Dosyası ({P.REV})")
    c.setAuthor("Ön tasarım dosyası"); c.setSubject(P.PROJE)
    for fn in (s01,s02,s03,s04,s05,s06,s07,s08,s09,s10,s11,s12):
        fn(c); c.showPage()
    c.save(); print("→", path)

if __name__ == "__main__":
    build()
