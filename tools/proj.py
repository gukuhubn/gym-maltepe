# -*- coding: utf-8 -*-
"""TEK KAYNAK: tum cizim, tablo, metraj ve maliyet buradan beslenir.
Bir sayiyi degistirmek icin SADECE bu dosyayi duzenleyin."""
import json, math
from pathlib import Path
from shapely.geometry import Polygon, Point, box
from shapely import affinity

ROOT = Path(__file__).resolve().parent.parent
G    = json.loads((ROOT/"data/geometry.json").read_text())

REV        = "Rev B"
TARIH      = "13 Eylül 2026"
FIYAT_TARIH= "Eylül 2026 piyasa mertebesi"
PROJE      = "MALTEPE / İDEALTEPE — MOBİLYA MAĞAZASI → FONKSİYONEL ANTRENMAN STÜDYOSU"
KISA       = "Gym Dönüşüm Dosyası"
ALTBILGI   = ("Ön tasarım — yerinde doğrulanmadan ve ruhsat alınmadan uygulama yapılamaz.  "
              "Tüm ölçüler raster paftadan ölçeklendirilmiştir (±%3).")

# ───────────────────────── PARAMETRELER (varsayimlar tek yerde) ─────────────────
V = {  # deger, birim, kaynak/varsayim notu
 "tavan_h":        (3.20,"m","VARSAYIM — yerinde doğrulanacak (mağaza tipik 3,0–3,6 m)"),
 "duvar_kalinlik": (0.20,"m","mevcut yığma/betonarme — VARSAYIM"),
 "bolme_kalinlik": (0.10,"m","alçıpan çift kat + taşyünü"),
 "kisi_kapasite":  (12,"kişi","seans başı eşzamanlı — tasarım kabulü"),
 "personel":       (2,"kişi","1 antrenör + 1 resepsiyon"),
 "taze_hava_kisi": (55,"m³/h·kişi","spor salonu için kabul (30 m³/h yasal asgari üzeri)"),
 "lux_arena":      (500,"lux","serbest ağırlık / arena"),
 "lux_salon":      (300,"lux","genel çalışma alanı"),
 "lux_soyunma":    (200,"lux","soyunma"),
 "lux_wc":         (150,"lux","ıslak hacim"),
 "isi_hedef":      (18,"°C","yönetmelik asgarisi — tasarım 20–22 °C"),
 "pano_mevcut":    (None,"kW","BİLİNMİYOR — işverenden istenecek"),
 "pis_su_kot":     (None,"cm","BİLİNMİYOR — ıslak hacim çözümünü belirler"),
 "ust_kat_konut":  (True,"","VARSAYIM (konservatif) — akustik kalemleri buna göre"),
 "beklenmedik":    (0.15,"","ıslak hacim belirsizliği yüksek"),
 "santiye_gider":  (0.09,"","genel giderler %8–10 ortası"),
}
def v(k): return V[k][0]

# ───────────────────────── ALANLAR (pafta etiketleri = tek gerçek) ──────────────
A = {"salon":87.05, "erkek_blok":8.24, "kadin_blok":8.49,
     "on_bahce":24.39, "arka_bahce":32.82}
A["ic_toplam"]   = round(A["salon"]+A["erkek_blok"]+A["kadin_blok"],2)   # 103.78
A["islak_toplam"]= round(A["erkek_blok"]+A["kadin_blok"],2)             # 16.73
A["bahce"]       = round(A["on_bahce"]+A["arka_bahce"],2)               # 57.21

# ───────────────────────── GEOMETRİ ─────────────────────────────────────────────
SALON = Polygon(G["poligonlar"]["salon"])
ERKEK = Polygon(G["poligonlar"]["erkek"])
KADIN = Polygon(G["poligonlar"]["kadin"])
BBOX  = SALON.union(ERKEK).union(KADIN).bounds          # (minx,miny,maxx,maxy)

def _clip(g):  return g.intersection(SALON)
# kuzey kol = dinlenme salonu  (y > 8.60)
_north = box(5.55, 8.52, BBOX[2]+1, BBOX[3]+1)
Z_DINLENME = _clip(_north)
# giris / banko seridi : bati cephe onu
Z_BANKO    = _clip(box(BBOX[0]-1, 0.0, 2.60, 8.60)).difference(Z_DINLENME)
# arena + agirlik : merkez-guney
Z_ARENA    = _clip(box(2.60, 0.0, 7.40, 6.70)).difference(Z_DINLENME)
# kalan = fonksiyonel / kardiyo serbest alan
Z_SERBEST  = SALON.difference(Z_DINLENME).difference(Z_BANKO).difference(Z_ARENA)

ZONES = [  # ad, poligon, zemin, kalinlik, renk, etiket_noktasi
 ("DİNLENME SALONU",           Z_DINLENME,"LVT / laminat parke",         "8 mm",   "#E4CFB2",(8.05,11.10)),
 ("GİRİŞ · BANKO · SİRKÜLASYON",Z_BANKO,  "LVT / laminat parke",         "8 mm",   "#F1E5D6",(1.55,2.35)),
 ("ARENA · SERBEST AĞIRLIK",   Z_ARENA,   "Kauçuk karo + titreşim matı", "40+10 mm","#C3D0DE",(5.30,1.62)),
 ("FONKSİYONEL · KARDİYO",     Z_SERBEST, "Kauçuk karo",                 "20 mm",  "#DCE5EC",(6.40,7.45)),
]
_kz  = A["salon"]/sum(z[1].area for z in ZONES)      # pafta 87,05 ile birebir ortusum
ZON_M2 = {z[0]: round(z[1].area*_kz,2) for z in ZONES}
_d = round(A["salon"]-sum(ZON_M2.values()),2)
if _d: ZON_M2["FONKSİYONEL · KARDİYO"] = round(ZON_M2["FONKSİYONEL · KARDİYO"]+_d,2)
ISLAK_M2 = A["islak_toplam"]

# ───────────────────────── EKİPMAN (işverence temin — ölçüler brief'ten, cm) ────
EKIPMAN = [  # kod, ad, en_cm, boy_cm, adet, merkez(x,y) m, aci derece, tip(3B), yukseklik m
 ("A", "TRIMODE ARENA — altıgen ring, 4 sıra halat", None, None, 1, (5.30, 4.35), 0, "ring", 1.80),
 ("B", "Çok fonksiyonlu kuvvet istasyonu (ağırlık takozlu)", 244, 62, 1, (8.18, 6.30), 98.7, "istasyon", 2.10),
 ("C", "Kablo çapraz / functional trainer",      175, 232, 1, (3.90, 7.68), 96.1, "kablo", 2.15),
 ("D", "Dambıl rafı / sehpa",                    155,  39, 2, [(6.20,8.58),(8.74,4.25)], [6.1, 98.7], "raf", 0.95),
 ("E", "Kardiyo — kondisyon bisikleti",           84, 150, 1, (8.66, 1.95), 8.7, "bisiklet", 1.25),
 ("F", "Koşu bandı",                             245,  74, 2, [(4.70,0.46),(7.30,0.48)], [0, 0], "kosu", 1.45),
]
EK_TIP = {e[0]: e[7] for e in EKIPMAN}
EK_H   = {e[0]: e[8] for e in EKIPMAN}
# altıgen ring teknik tanımı (3B modeli ve render prompt'ları bunu kullanır)
RING = {"m2": 10.60, "platform_h": 0.30, "direk_h": 1.50, "halat_sayisi": 4,
        "halat_kotlari": [0.35, 0.70, 1.05, 1.40], "direk_adedi": 6,
        "minder": "kanvas kaplı şok emici minder", "direk": "siyah pedli çelik direk",
        "halat": "siyah kılıflı ring halatı"}
HEX_M2 = 10.60
HEX_S  = math.sqrt(HEX_M2/(1.5*math.sqrt(3)))     # kenar  ≈ 2.02 m
def hex_poly(cx, cy, s=HEX_S, rot=90):
    return Polygon([(cx+s*math.cos(math.radians(rot+60*i)),
                     cy+s*math.sin(math.radians(rot+60*i))) for i in range(6)])

def ekipman_poligonlari():
    out=[]
    for kod, ad, w, h, n, c, a, tip, hh in EKIPMAN:
        if w is None:
            out.append((kod, ad, hex_poly(*c))); continue
        cs = c if isinstance(c, list) else [c]
        as_= a if isinstance(a, list) else [a]*len(cs)
        for i,(cx,cy) in enumerate(cs):
            g = box(cx-w/200, cy-h/200, cx+w/200, cy+h/200)
            out.append((kod+(str(i+1) if n>1 else ""), ad,
                        affinity.rotate(g, as_[i], origin=(cx,cy))))
    return out
EK_ALAN = round(sum(p.area for _,_,p in ekipman_poligonlari()),2)

# ───────────────────────── KAPI / PENCERE / CEPHE ───────────────────────────────
CEPHE = [((0.58,1.25),(0.00,6.84)), ((1.96,1.56),(3.24,0.00))]   # mavi doğrama (batı+GB)
KAPILAR = [ # (x,y) m, genislik, aci, etiket
 ((0.24, 4.30), 1.60, 90,  "ANA GİRİŞ  2×80 cm"),
 ((8.85, 7.10), 0.90, 82,  "ERKEK SOYUNMA"),
 ((9.10, 3.40), 0.90, 82,  "KADIN SOYUNMA"),
 ((3.35, 0.10), 1.00, 0,   "ACİL ÇIKIŞ (GB cephe)"),
]

# ───────────────────────── MEKANİK / ELEKTRİK HESAP ─────────────────────────────
KISI   = v("kisi_kapasite") + v("personel")
HACIM  = round(A["ic_toplam"]*v("tavan_h"),1)
TAZE_KISI = KISI*v("taze_hava_kisi")
TAZE_ACH3 = 3.0*HACIM                                           # asgari 3 hava değişimi/saat
TAZE   = int(round(max(TAZE_KISI, TAZE_ACH3)/50.0)*50)          # yuvarlanmis m3/h
ACH    = round(TAZE/HACIM,2)
EGZOZ_ISLAK = 2*80 + 2*40                                       # 2 duş + 2 WC  m3/h
SOGUTMA_W   = int(A["salon"]*180 + A["islak_toplam"]*60)        # W
SOGUTMA_BTU = int(round(SOGUTMA_W*3.412/1000)*1000)
# armatur tipleri: lineer LED 40 W / 4400 lm (salon) · IP44 downlight 18 W / 1800 lm (ıslak)
AYDINLATMA = []
for ad, m2, lux, lm_arm, tip in [
      ("Arena / serbest ağırlık", ZON_M2["ARENA · SERBEST AĞIRLIK"],      v("lux_arena"),  4400,"lineer"),
      ("Fonksiyonel / kardiyo",   ZON_M2["FONKSİYONEL · KARDİYO"],        v("lux_salon"),  4400,"lineer"),
      ("Dinlenme salonu",         ZON_M2["DİNLENME SALONU"],              v("lux_salon"),  4400,"lineer"),
      ("Giriş / banko",           ZON_M2["GİRİŞ · BANKO · SİRKÜLASYON"],  v("lux_salon"),  4400,"lineer"),
      ("Soyunma + duş + WC (6 hacim)", ISLAK_M2,                          v("lux_soyunma"),1800,"downlight")]:
    lm = lux*m2/(0.80*0.70)                 # bakim faktoru 0,80 · mekan verimi 0,70
    n  = math.ceil(lm/lm_arm)
    if tip=="downlight": n = max(n, 6)      # her hacimde en az bir armatur
    AYDINLATMA.append((ad, m2, lux, int(lm), n, tip))
_AD2ZON = {"Arena / serbest ağırlık":"ARENA · SERBEST AĞIRLIK",
           "Fonksiyonel / kardiyo":"FONKSİYONEL · KARDİYO",
           "Dinlenme salonu":"DİNLENME SALONU",
           "Giriş / banko":"GİRİŞ · BANKO · SİRKÜLASYON"}
ZON_ARMATUR  = {_AD2ZON[a[0]]: a[4] for a in AYDINLATMA if a[0] in _AD2ZON}
ARMATUR_ADET = sum(a[4] for a in AYDINLATMA if a[5]=="lineer")
DOWNLIGHT_ADET = sum(a[4] for a in AYDINLATMA if a[5]=="downlight")
ELEKTRIK_YUK = [("Aydınlatma (LED)", round(ARMATUR_ADET*0.040 + DOWNLIGHT_ADET*0.018,2)),
                ("Klima (split küme)", round(SOGUTMA_BTU/3412*0.33,2)),
                ("Havalandırma + ıslak hacim egzozu", 0.55),
                ("Elektrikli sıcak su (2 duş, ani ısıtıcı)", 6.00),
                ("Priz + ekipman + AV/müzik", 3.50)]
KURULU_KW = round(sum(x[1] for x in ELEKTRIK_YUK),1)
TALEP_KW  = round(KURULU_KW*0.75,1)

# ───────────────────────── METRAJ DAYANAKLARI ──────────────────────────────────
def _cevre(p): return round(p.exterior.length,2)
L_SALON   = _cevre(SALON)                       # salon dış çevre
L_ERKEK   = _cevre(ERKEK); L_KADIN = _cevre(KADIN)
L_ISLAK   = round(L_ERKEK+L_KADIN,2)
L_CEPHE   = round(sum(math.dist(a,b) for a,b in CEPHE),2)
H         = v("tavan_h")
# boyanacak / siva yapilacak duvar yuzeyi (salon ic yuzey − cephe dogramasi)
M2_DUVAR_SALON = round(L_SALON*H - L_CEPHE*2.40, 1)
M2_TAVAN       = A["ic_toplam"]
M2_SERAMIK_D   = round(L_ISLAK*2.20, 1)         # ıslak hacim duvar fayansı h=2,20
M2_YENI_BOLME  = round((L_ISLAK*0.55)*H, 1)     # yeni/yenilenecek alçıpan bölme payı
ADET_ARMATUR   = ARMATUR_ADET
ADET_KLIMA     = max(2, math.ceil(SOGUTMA_BTU/24000))

# ───────────────────────── BoQ — poz listesi ───────────────────────────────────
# (poz, grup, tanim, birim, miktar, bf_dusuk, bf_yuksek, senaryo)  senaryo: M=minimum, O=onerilen
B = [
("01.01","YIKIM · SÖKÜM","Mobilya mağazası raf/vitrin/tezgâh sökümü ve tasnifi","m²",A["ic_toplam"],   180,   320,"M"),
("01.02","YIKIM · SÖKÜM","Mevcut zemin kaplaması sökümü ve şap tesviyesi","m²",      A["ic_toplam"],   260,   450,"M"),
("01.03","YIKIM · SÖKÜM","Islak hacim mevcut seramik + vitrifiye sökümü","m²",       ISLAK_M2,         380,   620,"M"),
("01.04","YIKIM · SÖKÜM","Moloz yükleme, indirme ve nakliye (konteyner)","götürü",   1,             28000, 55000,"M"),
("02.01","DUVAR · ALÇIPAN","Alçıpan bölme duvar — 100 mm, çift kat, taşyünü dolgulu","m²", M2_YENI_BOLME, 600, 950,"M"),
("02.02","DUVAR · ALÇIPAN","Islak hacim bölmelerinde yeşil alçıpan / betopan yükseltmesi","m²", round(M2_YENI_BOLME*0.45,1), 260, 420,"M"),
("02.03","DUVAR · ALÇIPAN","Mevcut duvar tamiri, saten alçı ve yüzey hazırlığı","m²", M2_DUVAR_SALON,    220,   380,"M"),
("02.04","DUVAR · ALÇIPAN","Akustik asma tavan adası (arena üzeri) — 12 m²","m²",    12,                750,  1250,"O"),
("03.01","ISLAK HACİM","Pis su + temiz su tesisatı yenileme (2 duş + 2 WC + lavabo)","götürü",1,  85000,150000,"M"),
("03.02","ISLAK HACİM","Su yalıtımı — çift bileşenli, dönüş 30 cm","m²",             round(ISLAK_M2+L_ISLAK*0.30,1), 480, 780,"M"),
("03.03","ISLAK HACİM","Zemin seramiği R11 kaymaz (malzeme + işçilik)","m²",         ISLAK_M2,         750,  1200,"M"),
("03.04","ISLAK HACİM","Duvar fayansı h=2,20 m (malzeme + işçilik)","m²",            M2_SERAMIK_D,     850,  1350,"M"),
("03.05","ISLAK HACİM","Vitrifiye seti — 2 klozet, 2 lavabo, armatürler","takım",    2,              12000, 22000,"M"),
("03.06","ISLAK HACİM","Duş teknesi + cam duşakabin (2 adet)","adet",                2,              16000, 30000,"M"),
("03.07","ISLAK HACİM","Sıcak su — elektrikli ani ısıtıcı 2×6 kW + hat","takım",     1,              28000, 52000,"M"),
("03.08","ISLAK HACİM","SEÇENEK A — ıslak hacim zemini 15–20 cm yükseltme (hafif dolgu + şap + basamak/rampa)","m²", ISLAK_M2, 850, 1400,"O"),
("03.09","ISLAK HACİM","SEÇENEK B — öğütücülü gri su / atık su pompası (2 ünite + hat)","takım",  1, 72000, 128000,"—"),
("04.01","ZEMİN","Kauçuk karo 40 mm — arena / serbest ağırlık","m²",                ZON_M2["ARENA · SERBEST AĞIRLIK"], 1150, 1800,"M"),
("04.02","ZEMİN","Titreşim matı 10 mm (arena altı — üst katta konut varsayımı)","m²",ZON_M2["ARENA · SERBEST AĞIRLIK"],  300,  520,"O"),
("04.03","ZEMİN","Kauçuk karo 20 mm — fonksiyonel / kardiyo","m²",                  ZON_M2["FONKSİYONEL · KARDİYO"],    700, 1150,"M"),
("04.04","ZEMİN","LVT / laminat parke — dinlenme + giriş / banko","m²",             round(ZON_M2["DİNLENME SALONU"]+ZON_M2["GİRİŞ · BANKO · SİRKÜLASYON"],2), 550, 950,"M"),
("04.05","ZEMİN","Süpürgelik, geçiş profilleri, eşikler","m",                       round(L_SALON+L_ISLAK,1),           160,  290,"M"),
("05.01","ELEKTRİK","Ana pano yenileme + kaçak akım + kompanzasyonsuz dağıtım","adet",1,             55000, 105000,"M"),
("05.02","ELEKTRİK","Priz / anahtar / kuvvet noktası (sıva altı, komple)","nokta",   64,               950,  1600,"M"),
("05.03","ELEKTRİK","Lineer LED armatür 40 W / 4400 lm (montaj dahil)","adet",       ADET_ARMATUR,    1400,  2600,"M"),
("05.06","ELEKTRİK","IP44 downlight 18 W / 1800 lm — ıslak hacim ve soyunma","adet", DOWNLIGHT_ADET, 850, 1550,"M"),
("05.04","ELEKTRİK","Acil aydınlatma + yönlendirme armatürü","adet",                 8,               1150,  2100,"M"),
("05.05","ELEKTRİK","Zayıf akım — ağ, ses sistemi, CCTV, geçiş kontrol altyapısı","götürü",1,        55000, 110000,"O"),
("06.01","MEKANİK","Split klima 24.000 BTU inverter + montaj","adet",                ADET_KLIMA,     32000,  52000,"M"),
("06.02","MEKANİK",f"Taze hava + egzoz seti {TAZE} m³/h (kanal, fan, menfez, susturucu)","takım",1,  65000, 120000,"M"),
("06.03","MEKANİK",f"Islak hacim egzozu {EGZOZ_ISLAK} m³/h (2 duş + 2 WC)","takım",  1,              18000,  32000,"M"),
("06.04","MEKANİK","Sıhhi tesisat gider hatları, süzgeçler, havalandırma bacası","götürü",1,         25000,  45000,"M"),
("07.01","BOYA · DEKOR","Silinebilir mat duvar boyası (astar + 2 kat)","m²",         M2_DUVAR_SALON,   150,   280,"M"),
("07.02","BOYA · DEKOR","Tavan boyası / açık tavan siyah boya (endüstriyel)","m²",   M2_TAVAN,         180,   310,"M"),
("07.03","BOYA · DEKOR","Ayna — arena ve fonksiyonel alan (6 mm, montaj dahil)","m²",14,              1150,  1950,"O"),
("07.04","BOYA · DEKOR","Duvar grafiği / marka uygulaması","götürü",                 1,              28000,  60000,"O"),
("08.01","MARANGOZ","Resepsiyon bankosu — 2,40 m, kompakt lamine tezgâh","m",        2.4,            11000,  19000,"M"),
("08.02","MARANGOZ","Soyunma dolabı / askılık — 24 göz (2 blok)","göz",              24,              2400,   4200,"M"),
("08.03","MARANGOZ","Oturma bankı (soyunma) + dinlenme mobilyası","götürü",          1,              34000,  66000,"O"),
("09.01","YANGIN · GÜVENLİK","6 kg KKT yangın söndürücü + dolap + montaj","adet",     4,               3200,   5400,"M"),
("09.02","YANGIN · GÜVENLİK","Yangın algılama (duman dedektörü + siren + panel)","götürü",1,          32000,  65000,"M"),
("09.03","YANGIN · GÜVENLİK","Keskin köşe / kolon darbe hafifletici kaplama","m",     18,               850,   1500,"M"),
("09.04","YANGIN · GÜVENLİK","Engelli erişimi — rampa, tutamak, kapı genişliği düzenlemesi","götürü",1,30000,  65000,"M"),
("09.05","YANGIN · GÜVENLİK","İlk yardım dolabı, AED, acil çıkış donanımı","takım",   1,              24000,  45000,"M"),
("10.01","TABELA · DIŞ","Işıklı kutu harf tabela + cephe folyo","götürü",            1,              48000,  95000,"O"),
("10.02","TABELA · DIŞ","Cephe doğrama temizlik / bakım, giriş kapısı revizyonu","götürü",1,          26000,  50000,"M"),
]
GRUPLAR = ["YIKIM · SÖKÜM","DUVAR · ALÇIPAN","ISLAK HACİM","ZEMİN","ELEKTRİK",
           "MEKANİK","BOYA · DEKOR","MARANGOZ","YANGIN · GÜVENLİK","TABELA · DIŞ"]

def _tut(r, hi):  return r[4]*(r[6] if hi else r[5])
def maliyet(senaryo="O", islak="A"):
    """senaryo: 'M' minimum (yalnız zorunlu) | 'O' önerilen (M + O kalemleri)"""
    lo=hi=0.0; grup={g:[0.0,0.0] for g in GRUPLAR}
    for r in B:
        s=r[7]
        if   r[0]=="03.08":                          # SEÇENEK A — kot çözümü
            if islak!="A": continue
        elif r[0]=="03.09":                          # SEÇENEK B — pompa
            if islak!="B": continue
        elif s=="—":                                 continue
        elif s=="O" and senaryo!="O":                continue
        l,h=_tut(r,False),_tut(r,True); lo+=l; hi+=h
        grup[r[1]][0]+=l; grup[r[1]][1]+=h
    sg=(lo*v("santiye_gider"), hi*v("santiye_gider"))
    ar=((lo+sg[0])*v("beklenmedik"), (hi+sg[1])*v("beklenmedik"))
    return {"gruplar":grup,"imalat":(lo,hi),"santiye":sg,"beklenmedik":ar,
            "toplam":(lo+sg[0]+ar[0], hi+sg[1]+ar[1])}

# ───────────────────────── AÇILIŞ ÖNCESİ NAKİT ─────────────────────────────────
KIRA_AY = (28000, 52000)      # 104 m² × 270–500 TL/m²·ay — VARSAYIM (sözleşme işverende)
NAKIT = [
 ("Tadilat (önerilen senaryo, Seçenek A)", None, None),
 ("Ruhsat · harç · GSİM tescil · itfaiye · sağlık raporu", 85000, 175000),
 ("Proje / mimari onaylı 1/100 vaziyet planı · müşavirlik", 45000, 95000),
 ("İlk 3 ay kira", KIRA_AY[0]*3, KIRA_AY[1]*3),
 ("Depozito (3 ay)", KIRA_AY[0]*3, KIRA_AY[1]*3),
 ("Personel (açılış öncesi 2 ay · 2 kişi)", 160000, 280000),
 ("Pazarlama · açılış kampanyası · dijital", 95000, 210000),
 ("Yazılım (üyelik/POS), sarf, ilk stok", 55000, 120000),
]

# ───────────────────────── ISLAK HACİM ALT MEKÂNLARI ───────────────────────────
def _uzun_eksen(p):
    pts=list(p.exterior.coords)[:-1]; best=(0,None)
    for i in range(len(pts)):
        a,b=pts[i],pts[(i+1)%len(pts)]; L=math.dist(a,b)
        if L>best[0]: best=(L,(a,b))
    (ax,ay),(bx,by)=best[1]; d=(bx-ax,by-ay); n=math.hypot(*d)
    return (d[0]/n, d[1]/n), best[0]

def _yarim_duzlem(p, nokta, yon, derinlik):
    """nokta'dan yon yonunde derinlik kadar dilim"""
    (ux,uy)=yon; px,py=nokta; big=60
    vx,vy=-uy,ux
    q=Polygon([(px-vx*big, py-vy*big), (px+vx*big, py+vy*big),
               (px+vx*big+ux*derinlik, py+vy*big+uy*derinlik),
               (px-vx*big+ux*derinlik, py-vy*big+uy*derinlik)])
    return p.intersection(q)

def islak_alt_mekanlar():
    """her blok: (soyunma, duş, wc) poligonlari"""
    out={}
    for ad, p, uc in (("ERKEK",ERKEK,"kuzey"), ("KADIN",KADIN,"guney")):
        u,_=_uzun_eksen(p)
        if (uc=="kuzey" and u[1]<0) or (uc=="guney" and u[1]>0): u=(-u[0],-u[1])
        ys=[c[1] for c in p.exterior.coords]
        ref=max(p.exterior.coords, key=lambda c:c[1]) if uc=="kuzey" else \
            min(p.exterior.coords, key=lambda c:c[1])
        basla=(ref[0]-u[0]*0.02, ref[1]-u[1]*0.02)
        islak=_yarim_duzlem(p, basla, (-u[0],-u[1]), 1.62)
        soyunma=p.difference(islak.buffer(0.001))
        # ıslak şeridi enine ikiye böl: duş | wc
        v=(-u[1],u[0]); c=islak.centroid
        big=60
        yar=Polygon([(c.x, c.y-big),(c.x+v[0]*big, c.y+v[1]*big-big),
                     (c.x+v[0]*big, c.y+v[1]*big+big),(c.x, c.y+big)])
        yar=Polygon([(c.x-u[0]*big, c.y-u[1]*big),(c.x+u[0]*big, c.y+u[1]*big),
                     (c.x+u[0]*big+v[0]*big, c.y+u[1]*big+v[1]*big),
                     (c.x-u[0]*big+v[0]*big, c.y-u[1]*big+v[1]*big)])
        dus=islak.intersection(yar); wc=islak.difference(yar.buffer(0.001))
        if dus.area<wc.area: dus,wc = wc,dus
        def _temiz(g):
            if g.geom_type.startswith("Multi"):
                gs=[x for x in g.geoms if x.area>0.05]
                g=max(gs, key=lambda x:x.area) if gs else g
            return g.buffer(0)
        out[ad]=dict(soyunma=_temiz(soyunma), dus=_temiz(dus), wc=_temiz(wc), tum=p)
    return out
ISLAK = islak_alt_mekanlar()
ISLAK_M2_DETAY = {k:{n:round(g.area,2) for n,g in d.items()} for k,d in ISLAK.items()}


# ───────────────────────── SABİT MOBİLYA (marangoz imalatı) ────────────────────
def _mob(cx, cy, w, d, aci, ad, tip):
    g = affinity.rotate(box(cx-w/2, cy-d/2, cx+w/2, cy+d/2), aci, origin=(cx,cy))
    return (ad, g, tip)

def mobilyalar():
    out=[_mob(1.78, 6.05, 2.40, 0.65, 96, "RESEPSİYON BANKOSU", "banko")]
    for ad, d in ISLAK.items():
        g=d["soyunma"]; u,_=_uzun_eksen(g); c=g.centroid
        v_=(-u[1],u[0])
        out.append(_mob(c.x+v_[0]*0.62, c.y+v_[1]*0.62, 1.70, 0.35,
                        math.degrees(math.atan2(*u[::-1])), f"DOLAP {ad[0]}", "dolap"))
        out.append(_mob(c.x-v_[0]*0.55, c.y-v_[1]*0.55, 1.25, 0.32,
                        math.degrees(math.atan2(*u[::-1])), f"BANK {ad[0]}", "bank"))
    return out
MOBILYA = mobilyalar()

# ───────────────────────── UYGUNLUK KONTROL LİSTESİ ────────────────────────────
# (madde, mevcut durum, gerekli aksiyon, risk K/S/Y)
UYGUNLUK = [
("Çalışma (salon) alanı — GSİM uygulamasında yaygın olarak ≥125 m²",
 "Salon 87,05 m² · net iç toplam 103,78 m²",
 "GSİM'den YAZILI ÖN GÖRÜŞ al. Olumsuzsa tescil kapsamının daraltılması (randevulu stüdyo) "
 "veya kira sözleşmesinin yeniden görüşülmesi. Bahçeler kapatılmayacaktır — işveren kararı", "K"),
("Toplam tesis alanı — uygulamada ≥170 m² (125+15+15+15)",
 "103,78 m² · açık 66,22 m² eksik",
 "Aynı karar ağacı. Kapalı alan artırımı GÜNDEMDE DEĞİL: ön ve arka bahçe açık kullanımda "
 "kalır, hiçbir alan hesabına dâhil edilmez", "K"),
("İki ayrı soyunma odası (kadın + erkek)",
 "VAR — 8,24 m² (erkek) / 8,49 m² (kadın) blok", "Korunuyor; iç bölme yenilenecek", "Y"),
("Soyunma odası kullanım alanı ≥8 m²",
 "Blok toplamı sağlıyor; duş+WC hariç net 4,48 / 5,59 m²",
 "Ölçümün blok toplamı üzerinden mi yapıldığı GSİM'e yazılı sorulacak", "S"),
("Soyunma odalarının İÇİNDE en az 2 duş + 2 tuvalet",
 "Konsept planda her blokta 1 duş + 1 WC → toplam 2+2",
 "İmalat BoQ 03.05 / 03.06 ile karşılanıyor", "Y"),
("Çalışma boyunca sürekli sıcak su",
 "Kaynak bilinmiyor (doğalgaz / elektrik?)",
 "2×6 kW elektrikli ani ısıtıcı — poz 03.07. Doğalgaz varsa kombi daha ekonomik", "S"),
("Dinlenme salonu ≥15 m², zemini halıfleks/parke vb.",
 "Kuzey kol → 17,33 m², LVT/laminat parke", "Sağlanıyor — plan sabitlenmeli", "Y"),
("Sporcu sayısı kadar soyunma dolabı / askılık",
 "Mevcut yok", "24 göz dolap + 2 bank — poz 08.02", "Y"),
("Salon ısısı ≥18 °C",
 "Mevcut ısıtma bilinmiyor", "3 × 24.000 BTU split küme (57.000 BTU hesaplandı) — poz 06.01", "Y"),
("Sporcu sayısına göre yeterli havalandırma",
 "Mekanik havalandırma yok",
 "1.000 m³/h taze hava = 3,0 hava değişimi/saat = 71 m³/h·kişi — poz 06.02", "Y"),
("Zeminin spor dalına uygun malzemeyle kaplanması",
 "Mağaza zemini — çıplak/mobilya kaplaması",
 "3 bölgeli kauçuk (40/20 mm) + LVT + ıslak hacim R11 seramik", "Y"),
("Yangın söndürme ekipmanı · itfaiye uygunluk raporu",
 "Mevcut değil",
 "4 adet 6 kg KKT + algılama paneli; İBB İtfaiye denetim başvurusu", "S"),
("Keskin köşe ve kolonların darbe hafifletici kaplanması",
 "Kolonlar çıplak", "18 m köşe/kolon kaplaması — poz 09.03", "Y"),
("Engellilere ve can güvenliğine yönelik tedbirler",
 "Giriş eşiği ve WC uygunluğu bilinmiyor",
 "Rampa, tutamak, kapı genişliği düzenlemesi — poz 09.04", "S"),
("Tavan yüksekliği (uygulamada ≥2,50 m)",
 "VARSAYIM 3,20 m — ÖLÇÜLMEDİ", "Yerinde ölçüm — tüm mekanik/aydınlatma hesabının girdisi", "S"),
("Bağımsız bölüm niteliği · yapı kullanma izni (iskân)",
 "Bilinmiyor", "Tapu kaydı + iskân belgesi kontrolü — ruhsatın ön şartı", "K"),
("Kat malikleri muvafakatnamesi (bina bağımsız değilse)",
 "Bilinmiyor",
 "Yönetim planı incelenmeli; spor salonu için muvafakat gerekebilir — ruhsatı bloke eder", "K"),
("Mevcut pis su bağlantı kotu ve konumu",
 "Bilinmiyor", "Islak hacim Seçenek A (zemin yükseltme) / B (pompa) kararını belirler", "K"),
("Elektrik pano gücü ve trifaze durumu",
 "Bilinmiyor",
 "Hesaplanan kurulu güç 16,2 kW / talep 12,1 kW — trifaze 3×25 A abonelik gerekir", "S"),
("Mimar onaylı 1/100 vaziyet ve yerleşim planı",
 "Yok", "GSİM ve belediye dosyasının zorunlu eki — proje müellifi tayini", "S"),
("Anlaşmalı doktor / sağlık memuru / klinik sözleşmesi",
 "Yok", "GSİM dosya eki — açılış öncesi imzalanır", "S"),
("Federasyon veya il müdürlüğü onaylı antrenör sözleşmesi",
 "Yok", "Her spor dalı için ayrı; işletmeci bizzat ders verecekse SGM antrenörlük belgesi", "S"),
("Üst katta konut — gürültü / titreşim şikâyeti riski",
 "VARSAYIM: üstte konut var",
 "Arena altında 40 mm kauçuk + 10 mm titreşim matı — poz 04.01 / 04.02", "S"),
("Soyunma ve dinlenme odalarında aydınlatma, havalandırma, 18 °C ısı ve hijyen",
 "Tasarımda karşılanıyor: 6 IP44 armatür, 240 m³/h egzoz, klima kümesi",
 "Yönetmelik bu şartı salon için değil ODALAR için ayrıca arıyor — komisyon tetkikinde "
 "her hacim tek tek bakılır. Temizlik protokolü yazılı hâle getirilmeli", "Y"),
("Birimin kat konumu — bodrum katta mı?",
 "BİLİNMİYOR — paftada kot bilgisi yok",
 "Bodrum konumundaki salonlarda ÖZEL havalandırma donanımı zorunludur; "
 "bu durumda poz 06.02 yeniden boyutlandırılır", "S"),
("İlçe Sağlık Müdürlüğü denetim ve onay raporu · personel hijyen eğitimi belgesi",
 "Yok", "GSİM dosyasının ve belediye ruhsatının zorunlu eki — yol haritası adım 5", "S"),
("Çevresel gürültü seviyesi değerlendirme raporu (müzik yayını yapılacaksa)",
 "Değerlendirilmedi",
 "Belediye, müzik yayını yapan işletmelerden isteyebilir. Üst katta konut varsa "
 "talep olasılığı yüksek — ölçüm ve rapor bedeli bütçeye alınmalı", "S"),
("Otopark / sığınak yükümlülüğü (kullanım değişikliği nedeniyle)",
 "Değerlendirilmedi",
 "Mağazadan spor salonuna kullanım değişikliği belediyede otopark yükümlülüğü doğurabilir; "
 "Ruhsat Müdürlüğü'ne adım 0'da sorulmalı", "S"),
]
UYG_SAYIM = {r: sum(1 for x in UYGUNLUK if x[3]==r) for r in "KSY"}

# ───────────────────────── YOL HARİTASI ────────────────────────────────────────
# (adim, kurum, ne, kim, sure, on kosul)
YOL = [
("0","İşveren / avukat","Tapu bağımsız bölüm niteliği, iskân, yönetim planı ve muvafakat durumunun tespiti","İşveren","1–2 hafta","—"),
("1","İstanbul GSİM","Tesis fiziki şartları için YAZILI ÖN GÖRÜŞ talebi (m², soyunma ölçümü, kapsam)","İşveren + müellif","2–4 hafta","0"),
("2","Proje müellifi","Mimar onaylı 1/100 vaziyet + yerleşim planı, tadilat projesi","Mimar","2–3 hafta","1"),
("3","Şantiye","Tadilat uygulaması (söküm → tesisat → zemin → mekanik → boya → montaj)","Müteahhit","8–11 hafta","2"),
("4","İBB İtfaiye","Yangın güvenlik önlemleri açısından işyeri denetimi ve uygunluk raporu","İşveren","2–4 hafta","3"),
("5","İlçe Sağlık Md.","Sağlık denetim ve onay raporu","İşveren","2–3 hafta","3"),
("6","İstanbul GSİM","Tesis açılış izni başvurusu: dilekçe, vaziyet planı, antrenör sözleşmesi, doktor sözleşmesi, itfaiye + sağlık raporu","İşveren","—","4, 5"),
("7","GSİM Komisyonu","En az 5 kişilik komisyonun YERİNDE TETKİKİ ve tutanak düzenlenmesi","Komisyon","2–5 hafta","6"),
("8","GSİM / Valilik","Yeterlilik belgesi, il başkanlığı / vali onayı, bir defaya mahsus TESCİL ÜCRETİ","İşveren","1–3 hafta","7"),
("9","Maltepe Belediyesi","İşyeri Açma ve Çalışma Ruhsatı başvurusu (GSİM uygunluk yazısı eki ile)","İşveren","3–6 hafta","8"),
("10","Vergi D. / SGK","Mükellefiyet, SGK işyeri dosyası, hijyen belgesi, personel sözleşmeleri","Mali müşavir","1–2 hafta","9"),
]
EVRAK = [
 "Kimlik / şirket evrakı (imza sirküleri, ticaret sicil)", "Vergi levhası",
 "Kira sözleşmesi veya tapu fotokopisi", "Yapı kullanma izin belgesi (iskân)",
 "Bina bağımsız değilse KAT MALİKLERİ MUVAFAKATNAMESİ",
 "Mimar onaylı 1/100 vaziyet ve yerleşim planı",
 "İtfaiye yangın güvenlik uygunluk raporu", "İlçe/İl Sağlık Müdürlüğü denetim ve onay raporu",
 "Her spor dalı için federasyon/il onaylı antrenör sözleşmesi",
 "Anlaşmalı doktor / sağlık memuru / klinik sözleşmesi",
 "İşletmeci ders verecekse SGM onaylı antrenörlük belgesi",
 "GSİM tesis açılış izni ve tescil belgesi (belediye bunu ister)",
]

# ───────────────────────── İŞ PROGRAMI ─────────────────────────────────────────
# (no, is, hafta_bas, sure_hafta, kritik_yol)
PROGRAM = [
 (1,"Söküm, moloz tahliyesi, mevcut tespit", 0, 1.5, True),
 (2,"Pis su / temiz su tesisatı — kot tespiti ve yeni hatlar", 1.0, 1.5, True),
 (3,"Islak hacim su yalıtımı ve zemin çözümü (Seçenek A/B)", 2.5, 1.0, True),
 (4,"Alçıpan bölme duvarlar, yeşil alçıpan, yüzey hazırlığı", 3.0, 1.5, True),
 (5,"Elektrik ve zayıf akım altyapısı (boru, kablo, pano)", 3.5, 1.5, False),
 (6,"Mekanik altyapı — kanal, egzoz, klima bakır hatları", 4.0, 1.5, False),
 (7,"Islak hacim seramik + vitrifiye + duşakabin", 5.0, 1.5, True),
 (8,"Sıva, saten alçı, astar ve boya", 5.5, 1.5, False),
 (9,"Zemin kaplamaları — titreşim matı, kauçuk, LVT", 7.0, 1.5, True),
 (10,"Aydınlatma, klima ve havalandırma montajı", 7.5, 1.5, False),
 (11,"Marangoz — banko, dolap, bank montajı", 8.5, 1.0, False),
 (12,"Yangın, güvenlik, engelli donanımı, tabela", 9.0, 1.0, False),
 (13,"Ekipman yerleşimi (işverence temin) ve devreye alma", 9.5, 1.0, True),
 (14,"Temizlik, eksik-kusur listesi, kabul ve teslim", 10.0, 1.0, True),
]
PROGRAM_HAFTA = max(b+s for _,_,b,s,_ in PROGRAM)

# ───────────────────────── RİSK KAYDI ──────────────────────────────────────────
# (risk, olasilik, etki, onlem, sahip)
RISKLER = [
("GSİM'in 125 m² / 170 m² uygulamasını bu tesise de uygulaması → tescil reddi",
 "Yüksek","Çok yüksek","Adım 1'deki yazılı ön görüş; reddi hâlinde tescil kapsamının randevulu kişisel antrenman stüdyosu olarak daraltılması; kira sözleşmesindeki fesih/indirim imkânının avukatla değerlendirilmesi. Bahçe kapatma seçeneği işveren kararıyla kapsam dışıdır","İşveren"),
("Kat malikleri muvafakatnamesi alınamaması → belediye ruhsatı çıkmaz",
 "Orta","Çok yüksek","Yönetim planının hemen incelenmesi; komşularla erken temas; gürültü önlemlerinin (titreşim matı) muvafakat görüşmesinde argüman olarak kullanılması","İşveren"),
("Pis su kotunun yerçekimiyle çözülememesi",
 "Orta","Orta","Seçenek A (zemin yükseltme, +%2–4 bütçe) hazır; olmazsa Seçenek B pompa. Söküm sonrası ilk iş kot tespiti","Müteahhit"),
("Tavan yüksekliğinin 2,50 m altında çıkması",
 "Düşük","Yüksek","Yerinde ölçüm ilk hafta. Asma tavan adası iptal edilir, açık tavan endüstriyel çözüme geçilir","Mimar"),
("GSİM komisyon tetkikinde eksik tespiti → ikinci tur",
 "Orta","Orta","Tetkik öncesi bu dosyanın uygunluk sayfasının madde madde kapatılması; eksik evrakın önceden tamamlanması","İşveren"),
("Islak hacim kaynaklı bütçe sapması",
 "Yüksek","Orta","%15 beklenmedik payı bütçede ayrıldı; sökümden sonra keşif revizyonu ve BoQ'nun güncellenmesi","Müteahhit"),
("Üst kat gürültü şikâyeti → ruhsat sonrası kapatma riski",
 "Orta","Yüksek","Arena altına 40 mm kauçuk + 10 mm titreşim matı; ağırlık düşürmenin kural olarak yasaklanması; çalışma saatlerinin sınırlanması","İşletme"),
("Takvim sapması — ruhsat zinciri uzarsa boş kira yükü",
 "Yüksek","Orta","Tadilat ile evrak süreçlerinin paralel yürütülmesi; ilk 3 ay kira nakit planına alındı","İşveren"),
]

SONRAKI_5 = [
 ("1","Yerinde ölçüm günü","Tavan yüksekliği, pis su kotu ve konumu, elektrik pano gücü/trifaze, kolon konumları, mevcut durum fotoğrafları. Yarım gün, maliyeti yok, her şeyin girdisi."),
 ("2","Tapu · iskân · yönetim planı dosyası","Bağımsız bölüm niteliği ve muvafakat gerekliliği netleşmeden hiçbir imalata başlanmamalı."),
 ("3","İstanbul GSİM'e yazılı ön görüş başvurusu","Bu projenin tek kritik belirsizliği. Dilekçe ekine bu dosyanın 3. ve 5. sayfası konulabilir."),
 ("4","Proje müellifi (mimar) tayini","1/100 onaylı vaziyet planı olmadan ne GSİM ne belediye dosyası açılabilir."),
 ("5","BoQ ile 3 müteahhitten teklif","Birim fiyat sütunları boş .xlsx dosyası hazır; teklifler aynı metraj üzerinden karşılaştırılabilir."),
]
