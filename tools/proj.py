# -*- coding: utf-8 -*-
"""TEK KAYNAK: tum cizim, tablo, metraj ve maliyet buradan beslenir.
Bir sayiyi degistirmek icin SADECE bu dosyayi duzenleyin."""
import json, math
from pathlib import Path
from shapely.geometry import Polygon, Point, box
from shapely import affinity

ROOT = Path(__file__).resolve().parent.parent
G    = json.loads((ROOT/"data/geometry.json").read_text())

REV        = "Rev C"
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


# ═══════════════════════ MEKANİK PROJE — sistem yerleşimi ══════════════════════
from shapely.geometry import LineString as _LS

def _uzunluk(pts): return round(_LS(pts).length, 1)

# ── havalandırma: tavan altı kanal güzergâhları (plan koordinatı, m) ───────────
KANAL = {
 "besleme": {"kesit":"500×150", "debi":1000, "hiz":3.7, "renk":"#2E7D5B",
   "guzergah":[(0.35,6.30),(1.70,7.55),(4.10,7.90),(6.05,8.05),(7.30,7.85),(7.85,9.20),(7.95,10.55)]},
 "egzoz":   {"kesit":"400×150", "debi":760,  "hiz":3.5, "renk":"#C8322B",
   "guzergah":[(0.45,2.40),(1.55,1.70),(3.30,1.45),(5.60,1.25),(8.20,1.35),(8.85,2.30)]},
 "islak":   {"kesit":"Ø160",    "debi":240,  "hiz":3.3, "renk":"#8E3BB0",
   "guzergah":[(9.55,8.05),(9.35,6.20),(9.10,4.60),(9.70,2.60),(10.60,2.10),(11.35,2.35)]},
}
# menfez / valf: (kod, x, y, debi m³/h, tip)
MENFEZ = [
 ("M1", 1.55, 5.60, 250, "besleme"), ("M2", 4.10, 6.35, 250, "besleme"),
 ("M3", 7.05, 7.20, 250, "besleme"), ("M4", 8.05,10.60, 250, "besleme"),
 ("E1", 2.90, 1.60, 255, "egzoz"),   ("E2", 5.60, 1.20, 255, "egzoz"),
 ("E3", 8.20, 1.40, 250, "egzoz"),
 ("V1", 9.45, 8.05,  80, "valf"),    ("V2",10.35, 8.10,  40, "valf"),
 ("V3",10.75, 1.85,  80, "valf"),    ("V4", 9.85, 1.35,  40, "valf"),
]
PANJUR = [("TH", 0.30, 6.25, "Dış hava panjuru 500×300 + kuş teli"),
          ("EG", 0.42, 2.45, "Egzoz panjuru 400×300"),
          ("EI",11.45, 2.40, "Islak hacim egzoz çıkışı Ø160")]
FAN = [("F-TH", 1.20, 7.05, "Kanal tipi taze hava fanı — 1.000 m³/h / 250 Pa"),
       ("F-EG", 1.25, 1.95, "Kanal tipi egzoz fanı — 760 m³/h / 200 Pa"),
       ("F-IS", 9.45, 5.40, "Islak hacim egzoz fanı — 240 m³/h, sessiz tip")]

# ── iklimlendirme: bölge bazlı split küme ─────────────────────────────────────
def _btu(m2, w=180): return int(round(m2*w*3.412/1000)*1000)
KLIMA = [
 ("K1","ARENA · SERBEST AĞIRLIK", 24000, (5.95, 0.28)),
 ("K2","FONKSİYONEL · KARDİYO",   18000, (7.95, 6.95)),
 ("K3","GİRİŞ · BANKO · SİRKÜLASYON", 12000, (1.30, 7.35)),
 ("K4","DİNLENME SALONU",         12000, (7.05,11.90)),
]
KLIMA_BTU  = sum(k[2] for k in KLIMA)
ADET_KLIMA = len(KLIMA)
DIS_UNITE = (11.90, 6.10)     # arka cephe duvarı — kapalı alana dâhil değil
# Bakır ve drenaj hatları tavan altında DUVAR BOYUNCA ortogonal yürür; salon ortasından
# çapraz geçiş yoktur. Her iç ünitenin kendi güzergâhı aşağıda açıkça tanımlıdır.
_CIKIS = [(11.20, 6.30), DIS_UNITE]                       # erkek blok tavanından dış duvara
BAKIR_HAT = {
 "K1": [(5.95,0.28),(9.05,0.62),(9.52,3.90),(10.05,5.55),(10.80,6.05)] + [DIS_UNITE],
 "K2": [(7.95,6.95),(7.95,7.92),(9.45,7.62)] + _CIKIS,
 "K3": [(1.30,7.35),(1.30,7.92),(5.95,7.92),(7.95,7.92),(9.45,7.62)] + _CIKIS,
 "K4": [(7.05,11.90),(7.05,9.10),(8.05,8.58),(9.45,7.62)] + _CIKIS,
}
DRENAJ = {                                                # %1 eğimli, dış duvara
 "K1": [(5.95,0.28),(9.05,0.62),(9.52,3.90),(10.60,5.30),(11.60,5.55)],
 "K2": [(7.95,6.95),(7.95,7.86),(9.40,7.56),(11.10,6.20),(11.60,5.90)],
 "K3": [(1.30,7.35),(1.30,7.86),(5.95,7.86),(7.95,7.86),(9.40,7.56),(11.10,6.20),(11.60,5.90)],
 "K4": [(7.05,11.90),(7.05,9.10),(8.05,8.52),(9.40,7.56),(11.10,6.20),(11.60,5.90)],
}
L_BAKIR   = round(sum(_LS(h).length for h in BAKIR_HAT.values()), 1)
L_DRENAJ  = round(sum(_LS(h).length for h in DRENAJ.values()), 1)

# ── sıhhi tesisat ─────────────────────────────────────────────────────────────
SU_GIRIS = (10.95, 1.35)                      # sayaç / ana kesme — kadın blok güneyi
TEMIZ_SU = {"Ø25": [(10.95,1.35),(10.20,2.60),(9.90,4.80),(9.80,6.90),(9.90,8.00)],
            "Ø20": [[(9.90,8.00),(9.45,8.10)],[(9.90,8.00),(10.35,8.05)],
                    [(10.20,2.60),(10.75,1.85)],[(10.20,2.60),(9.85,1.40)]]}
PIS_SU   = {"Ø100":[(9.40,8.15),(9.55,6.00),(9.85,3.40),(10.60,1.70),(11.20,1.20)],
            "Ø70": [[(9.45,8.05),(9.40,8.15)],[(10.75,1.85),(10.60,1.70)]],
            "Ø50": [[(10.35,8.10),(9.55,6.00)],[(9.85,1.35),(9.85,3.40)]]}
L_TEMIZ25 = _uzunluk(TEMIZ_SU["Ø25"])
L_TEMIZ20 = round(sum(_LS(h).length for h in TEMIZ_SU["Ø20"]), 1)
L_SICAK   = round(L_TEMIZ20*1.35, 1)
L_PIS100  = _uzunluk(PIS_SU["Ø100"])
L_PIS70   = round(sum(_LS(h).length for h in PIS_SU["Ø70"]), 1)
L_PIS50   = round(sum(_LS(h).length for h in PIS_SU["Ø50"]), 1)
ISITICI = [("SI-1", 9.70, 7.60, "Elektrikli ani su ısıtıcı 6 kW — erkek bloğu"),
           ("SI-2",10.55, 2.15, "Elektrikli ani su ısıtıcı 6 kW — kadın bloğu")]
VITRIFIYE = [("WC-1",10.35,8.10,"Klozet + lavabo"),("DU-1", 9.45,8.05,"Duş teknesi + kabin"),
             ("WC-2", 9.85,1.35,"Klozet + lavabo"),("DU-2",10.75,1.85,"Duş teknesi + kabin")]

L_KANAL_B = _uzunluk(KANAL["besleme"]["guzergah"])
L_KANAL_E = _uzunluk(KANAL["egzoz"]["guzergah"])
L_KANAL_I = _uzunluk(KANAL["islak"]["guzergah"])
def _brans(m):
    hat = KANAL["besleme" if m[4]=="besleme" else ("egzoz" if m[4]=="egzoz" else "islak")]
    return _LS(hat["guzergah"]).distance(_Pt(m[1], m[2])) + 0.60   # + düşüş payı
from shapely.geometry import Point as _Pt
L_BRANS   = round(sum(_brans(m) for m in MENFEZ if m[4] != "valf"), 1)
L_BRANS_I = round(sum(_brans(m) for m in MENFEZ if m[4] == "valf"), 1)

# ═══════════════════════ ELEKTRİK PROJE — cihaz yerleşimi ══════════════════════
def _duvar_boyunca(poly, n, ofset=0.18, basla=0.0):
    """Poligon çevresinde eşit aralıklı, içeri ofsetli noktalar."""
    g = poly.buffer(-ofset); g = g if not g.is_empty else poly
    r = g.exterior if hasattr(g, "exterior") else list(g.geoms)[0].exterior
    L = r.length
    return [(r.interpolate((basla + i/n) * L).x, r.interpolate((basla + i/n) * L).y)
            for i in range(n)]

PRIZ = [("P%d" % (i+1), x, y, "ikili topraklı priz")
        for i, (x, y) in enumerate(_duvar_boyunca(SALON, 18, 0.20, 0.02))]
PRIZ += [("PB1", 1.95, 6.35, "banko kuvvet + veri kutusu"),
         ("PK1", 4.70, 1.05, "kardiyo prizi — koşu bandı 1"),
         ("PK2", 7.30, 1.05, "kardiyo prizi — koşu bandı 2"),
         ("PK3", 8.30, 2.55, "kardiyo prizi — bisiklet")]
PRIZ_IP44 = [("PI1", 9.80, 7.45, "IP44 priz — erkek soyunma"),
             ("PI2",10.45, 2.75, "IP44 priz — kadın soyunma")]
ANAHTAR = [("A1", 0.62, 4.05, "vaviyen — ana giriş"), ("A2", 2.45, 6.95, "vaviyen — banko"),
           ("A3", 6.85, 8.35, "komütatör — fonksiyonel"), ("A4", 7.40, 9.35, "dinlenme salonu"),
           ("A5", 3.55, 0.55, "arena aydınlatma"), ("A6", 8.70, 7.85, "erkek soyunma"),
           ("A7", 9.15, 3.15, "kadın soyunma")]
SENSOR  = [("S1", 9.70, 8.10, "hareket sensörü — erkek ıslak"),
           ("S2",10.55, 1.90, "hareket sensörü — kadın ıslak"),
           ("S3", 7.60, 9.60, "hareket sensörü — dinlenme geçişi")]
# zayıf akım — SOYUNMA VE WC İÇİNE KAMERA KONULMAZ
KAMERA  = [("C1", 1.35, 6.60, "giriş ve banko"), ("C2", 3.05, 7.95, "salon kuzey"),
           ("C3", 8.15, 6.40, "salon doğu — soyunma koridoru girişi"),
           ("C4", 4.40, 0.75, "kardiyo ve güney cephe"),
           ("C5", 7.35, 9.85, "dinlenme salonu")]
HOPARLOR= [("H%d" % (i+1), x, y, "tavan hoparlörü 6 W / 100 V")
           for i, (x, y) in enumerate([(2.20,5.20),(5.30,6.90),(7.55,5.40),
                                       (4.10,2.10),(7.60,2.30),(8.05,10.90)])]
VERI    = [("D1", 1.95, 6.20, "banko — router + NVR rack 9U"),
           ("D2", 1.95, 6.05, "banko — POS / kayıt"),
           ("AP1",4.60, 6.60, "kablosuz erişim noktası"),
           ("AP2",7.90, 9.80, "kablosuz erişim noktası — dinlenme")]
DEDEKTOR= [("Y%d" % (i+1), x, y, "optik duman dedektörü")
           for i, (x, y) in enumerate([(2.55,6.05),(5.30,7.20),(7.70,4.40),(4.60,1.65),
                                       (7.85,11.10),(9.60,6.70)])]
YANGIN  = [("YB1", 0.85, 3.35, "yangın ihbar butonu — ana çıkış"),
           ("YB2", 3.60, 0.60, "yangın ihbar butonu — ikinci çıkış"),
           ("SR1", 2.25, 7.30, "siren + flaşör")]
ACIL    = [("AA%d" % (i+1), x, y, t) for i, (x, y, t) in enumerate([
           (0.90,4.40,"acil aydınlatma"),(3.40,0.95,"acil aydınlatma"),
           (5.25,7.35,"acil aydınlatma"),(8.00,9.90,"acil aydınlatma"),
           (9.55,7.10,"acil aydınlatma"),
           (0.75,3.85,"çıkış yönlendirme"),(3.45,0.45,"çıkış yönlendirme"),
           (6.30,8.55,"çıkış yönlendirme")])]
PANO    = (2.35, 7.55)     # ana dağıtım panosu — banko arkası

# ── linye (devre) tablosu ─────────────────────────────────────────────────────
# (kod, tanım, koruma, kesit, bağlı güç kW, eşzamanlılık katsayısı)
_LINYE = [
 ("L1","Aydınlatma — arena / serbest ağırlık","1×10 A","3×1,5", 7*0.040, 1.00),
 ("L2","Aydınlatma — fonksiyonel / kardiyo","1×10 A","3×1,5", 3*0.040, 1.00),
 ("L3","Aydınlatma — dinlenme salonu","1×10 A","3×1,5", 3*0.040, 1.00),
 ("L4","Aydınlatma — giriş / banko","1×10 A","3×1,5", 2*0.040, 1.00),
 ("L5","Aydınlatma — ıslak hacim (IP44)","1×10 A","3×1,5", 6*0.018, 0.60),
 ("L6","Acil aydınlatma ve yönlendirme","1×6 A","3×1,5", 8*0.008, 1.00),
 ("P1","Priz — salon kuzey ve batı","1×16 A","3×2,5", 1.20, 0.50),
 ("P2","Priz — salon güney ve doğu","1×16 A","3×2,5", 1.20, 0.50),
 ("P3","Priz — banko, POS, veri","1×16 A","3×2,5", 1.00, 0.70),
 ("P4","Priz — kardiyo ekipmanı (ayrı linye)","1×16 A","3×2,5", 2.40, 0.80),
 ("P5","Priz — ıslak hacim IP44 (ayrı kaçak akım)","1×16 A","3×2,5", 0.50, 0.30),
 ("K1","Klima — arena 24.000 BTU","1×16 A","3×2,5", 2.20, 0.85),
 ("K2","Klima — fonksiyonel 18.000 BTU","1×16 A","3×2,5", 1.70, 0.85),
 ("K3","Klima — giriş 12.000 BTU","1×16 A","3×2,5", 1.15, 0.85),
 ("K4","Klima — dinlenme 12.000 BTU","1×16 A","3×2,5", 1.15, 0.70),
 ("W1","Su ısıtıcı — erkek bloğu 6 kW","1×32 A","3×4", 6.00, 0.50),
 ("W2","Su ısıtıcı — kadın bloğu 6 kW","1×32 A","3×4", 6.00, 0.50),
 ("V1","Havalandırma — taze hava + egzoz fanı","1×10 A","3×1,5", 0.45, 1.00),
 ("V2","Islak hacim egzoz fanı","1×6 A","3×1,5", 0.12, 0.80),
 ("Z1","Zayıf akım — rack, CCTV, ses, geçiş kontrol","1×10 A","3×2,5", 0.60, 0.90),
 ("Z2","Yangın algılama paneli (kesintisiz)","1×6 A","3×1,5", 0.15, 1.00),
]
# faz dağıtımı: talep gücü büyükten küçüğe, her linye o an EN AZ yüklü faza verilir
def _fazlari_dagit(ls):
    yuk = {"L1":0.0, "L2":0.0, "L3":0.0}; atama = {}
    for l in sorted(ls, key=lambda x: -x[4]*x[5]):
        f = min(yuk, key=yuk.get); atama[l[0]] = f; yuk[f] += l[4]*l[5]
    return atama, {k: round(v,2) for k,v in yuk.items()}
_ATAMA, FAZ_YUK = _fazlari_dagit(_LINYE)
LINYE = [(k, t, kor, kes, _ATAMA[k], bg, es, round(bg*es,3))
         for k, t, kor, kes, bg, es in _LINYE]
BAGLI_KW  = round(sum(l[5] for l in LINYE), 2)          # toplam bağlı güç
TALEP_KW_E= round(sum(l[7] for l in LINYE), 2)          # eşzamanlılık sonrası talep
FAZ_DENGE = round(100*(max(FAZ_YUK.values())-min(FAZ_YUK.values()))/
                  (sum(FAZ_YUK.values())/3), 1)
AKIM_FAZ  = {f: round(FAZ_YUK[f]*1000/(230*0.92), 1) for f in FAZ_YUK}
ANA_KESICI= 3*32 if max(AKIM_FAZ.values()) > 22 else 3*25
ABONELIK  = f"Trifaze 3×{ANA_KESICI//3} A · {round(ANA_KESICI/3*230*3*0.92/1000)} kW"
L_LINYE15 = round(sum(1 for l in LINYE if l[3]=="3×1,5")*14.5 + L_SALON*0.9, 0)
L_LINYE25 = round(sum(1 for l in LINYE if l[3]=="3×2,5")*16.5 + L_SALON*0.6, 0)
L_ZAYIF   = round(L_SALON*2.6 + 90, 0)
SOGUTMA_MARJ = round(100*(KLIMA_BTU/SOGUTMA_BTU-1))
# A3 sayfa 8'deki özet yük tablosu — linye tablosundan türetilir (tek kaynak)
def _grup(pre): return round(sum(l[5] for l in LINYE if l[0].startswith(pre)), 2)
ELEKTRIK_YUK = [("Aydınlatma (LED + acil)", _grup("L")),
                ("Priz ve ekipman", _grup("P")),
                ("Klima (4 iç ünite)", _grup("K")),
                ("Elektrikli sıcak su (2 × 6 kW)", _grup("W")),
                ("Havalandırma fanları", _grup("V")),
                ("Zayıf akım ve yangın algılama", _grup("Z"))]
KURULU_KW = BAGLI_KW
TALEP_KW  = TALEP_KW_E


# ── MEKANİK poz listesi (detay) ───────────────────────────────────────────────
B_MEK = [
("06.01","MEKANİK","Kanal tipi taze hava fanı — 1.000 m³/h / 250 Pa, hız kontrollü","adet",1, 18500, 31000,"M"),
("06.02","MEKANİK","Kanal tipi egzoz fanı — 760 m³/h / 200 Pa","adet",1, 14500, 24000,"M"),
("06.03","MEKANİK","Islak hacim egzoz fanı — 240 m³/h, sessiz tip, nem sensörlü","adet",1, 6500, 11500,"M"),
("06.04","MEKANİK",f"Galvaniz dikdörtgen kanal {KANAL['besleme']['kesit']} — besleme ana hattı","m", L_KANAL_B, 1350, 2200,"M"),
("06.05","MEKANİK",f"Galvaniz dikdörtgen kanal {KANAL['egzoz']['kesit']} — egzoz ana hattı","m", L_KANAL_E, 1150, 1900,"M"),
("06.06","MEKANİK","Spiro kanal Ø200 — menfez branşmanları","m", L_BRANS, 620, 1050,"M"),
("06.06b","MEKANİK","Spiro kanal Ø125 — ıslak hacim valf branşmanları","m", L_BRANS_I, 420, 720,"M"),
("06.07","MEKANİK","Spiro kanal Ø160 — ıslak hacim egzoz hattı","m", L_KANAL_I, 540, 900,"M"),
("06.08","MEKANİK","Çift sıra ayarlı besleme menfezi 300×150 + plenum","adet",4, 2400, 3900,"M"),
("06.09","MEKANİK","Egzoz menfezi 300×150 + plenum","adet",3, 2100, 3400,"M"),
("06.10","MEKANİK","Tavan egzoz valfi Ø160 (duş / WC)","adet",4, 950, 1600,"M"),
("06.11","MEKANİK","Debi ayar damperi (branşman başı)","adet",7, 1150, 1900,"M"),
("06.12","MEKANİK","Kanal susturucusu 1.000 mm — besleme ve egzoz","adet",2, 6800, 11500,"M"),
("06.13","MEKANİK","Dış hava / egzoz panjuru + kuş teli","adet",3, 3200, 5400,"M"),
("06.14","MEKANİK","Kanal izolasyonu — 19 mm elastomerik kauçuk","m²", round((L_KANAL_B+L_KANAL_E)*1.3,1), 780, 1300,"M"),
("06.15","MEKANİK","Kanal askı, taşıyıcı ve titreşim takozu","m", round(L_KANAL_B+L_KANAL_E+L_KANAL_I,1), 320, 540,"M"),
("06.16","MEKANİK","Hava debisi ölçümü, balanslama ve test raporu","götürü",1, 12000, 22000,"M"),
("06.17","MEKANİK","SEÇENEK — ısı geri kazanımlı taze hava ünitesi 1.000 m³/h (%75 verim)","adet",1, 95000, 165000,"—"),
("06.20","MEKANİK","Duvar tipi inverter split klima 24.000 BTU (iç + dış ünite)","adet",1, 34000, 55000,"M"),
("06.21","MEKANİK","Duvar tipi inverter split klima 18.000 BTU (iç + dış ünite)","adet",1, 27000, 44000,"M"),
("06.22","MEKANİK","Duvar tipi inverter split klima 12.000 BTU (iç + dış ünite)","adet",2, 19500, 32000,"M"),
("06.23","MEKANİK","Bakır boru seti (1/4\"–5/8\") + izolasyon + bağlantı kablosu","m", L_BAKIR, 1100, 1850,"M"),
("06.24","MEKANİK","Dış ünite galvaniz montaj konsolu ve titreşim takozu","adet",4, 3800, 6200,"M"),
("06.25","MEKANİK","Drenaj hattı PPRC Ø25 + izolasyon","m", L_DRENAJ, 420, 720,"M"),
("06.26","MEKANİK","Vakum, gaz şarjı, devreye alma ve test","adet",4, 3200, 5400,"M"),
("06.30","MEKANİK","PPRC temiz su borusu Ø25 (ek parça ve montaj dahil)","m", L_TEMIZ25, 620, 1050,"M"),
("06.31","MEKANİK","PPRC temiz su borusu Ø20 (ek parça ve montaj dahil)","m", L_TEMIZ20, 520, 880,"M"),
("06.32","MEKANİK","PPRC sıcak su hattı Ø20 + boru izolasyonu","m", L_SICAK, 680, 1150,"M"),
("06.33","MEKANİK","PVC pis su borusu Ø100 (%2 eğimli, askılı)","m", L_PIS100, 780, 1300,"M"),
("06.34","MEKANİK","PVC pis su borusu Ø70","m", L_PIS70, 560, 950,"M"),
("06.35","MEKANİK","PVC pis su borusu Ø50","m", L_PIS50, 430, 740,"M"),
("06.36","MEKANİK","Pis su havalandırma bacası Ø70 — çatı kotuna kadar","m", 9.5, 620, 1050,"M"),
("06.37","MEKANİK","Paslanmaz sifonlu yer süzgeci 15×15","adet",4, 1450, 2400,"M"),
("06.38","MEKANİK","Küresel vana Ø25 / Ø20 (kolon ve branşman kesme)","adet",8, 780, 1300,"M"),
("06.39","MEKANİK","Sayaç sonrası ana kesme vanası + pislik tutucu filtre","takım",1, 6500, 11000,"M"),
("06.40","MEKANİK","Elektrikli ani su ısıtıcı 6 kW (blok başına)","adet",2, 9800, 17000,"M"),
("06.41","MEKANİK","Tesisat basınç testi, dezenfeksiyon ve teslim raporu","götürü",1, 9500, 17000,"M"),
]

# ── ELEKTRİK poz listesi (detay) ──────────────────────────────────────────────
B_ELK = [
("05.01","ELEKTRİK","Ana dağıtım panosu — sıva üstü metal, 36 modül, montajlı","adet",1, 22000, 37000,"M"),
("05.02","ELEKTRİK","Ana kesici 3×40 A, C eğrisi","adet",1, 3200, 5400,"M"),
("05.03","ELEKTRİK","Kaçak akım rölesi 4×40 A / 30 mA (genel + ıslak hacim ayrı)","adet",2, 4200, 7000,"M"),
("05.04","ELEKTRİK","Otomatik sigorta (1×6 / 1×10 / 1×16 / 1×32 A)","adet", len(LINYE), 620, 1050,"M"),
("05.05","ELEKTRİK","Parafudr Tip 2 (aşırı gerilim koruma)","adet",1, 6800, 11500,"M"),
("05.06","ELEKTRİK","NYY kolon hattı 5×10 mm² — sayaçtan panoya","m", 22, 780, 1300,"M"),
("05.07","ELEKTRİK","Pano etiketleme, tek hat şeması çerçevesi ve fonksiyon testi","götürü",1, 6500, 11000,"M"),
("05.10","ELEKTRİK","Lineer LED armatür 40 W / 4400 lm, 1.200 mm (montaj dahil)","adet", ARMATUR_ADET, 1400, 2600,"M"),
("05.11","ELEKTRİK","IP44 downlight 18 W / 1800 lm — ıslak hacim ve soyunma","adet", DOWNLIGHT_ADET, 850, 1550,"M"),
("05.12","ELEKTRİK","Acil aydınlatma armatürü — 3 saat bataryalı","adet",5, 1250, 2200,"M"),
("05.13","ELEKTRİK","Acil çıkış yönlendirme armatürü","adet",3, 1150, 1950,"M"),
("05.14","ELEKTRİK","Aydınlatma linyesi NHXMH 3×1,5 mm² — spiral boru ve işçilik dâhil","m", L_LINYE15, 110, 185,"M"),
("05.15","ELEKTRİK","Anahtar / komütatör / vaviyen — sıva altı","adet", len(ANAHTAR), 480, 820,"M"),
("05.16","ELEKTRİK","Hareket sensörü — ıslak hacim ve geçiş","adet", len(SENSOR), 1450, 2400,"M"),
("05.20","ELEKTRİK","İkili topraklı priz — sıva altı, komple","adet", len(PRIZ), 620, 1050,"M"),
("05.21","ELEKTRİK","IP44 priz — ıslak hacim","adet", len(PRIZ_IP44), 950, 1600,"M"),
("05.22","ELEKTRİK","Priz linyesi NHXMH 3×2,5 mm² — spiral boru ve işçilik dâhil","m", L_LINYE25, 140, 230,"M"),
("05.23","ELEKTRİK","Klima besleme hattı 3×2,5 mm² + hat sonu kesici","adet", len(KLIMA), 3400, 5700,"M"),
("05.24","ELEKTRİK","Su ısıtıcı besleme hattı 3×4 mm² + 32 A kesici","adet",2, 5200, 8800,"M"),
("05.25","ELEKTRİK","Havalandırma fanı besleme ve hız kontrol hattı","adet",3, 2400, 4000,"M"),
("05.26","ELEKTRİK","Banko kuvvet + veri kutusu (gömme)","adet",1, 7500, 12500,"M"),
("05.30","ELEKTRİK","Cat6 veri prizi + kablolama","adet",6, 1450, 2450,"M"),
("05.31","ELEKTRİK","Kablosuz erişim noktası (AP) + PoE besleme","adet",2, 6800, 11500,"M"),
("05.32","ELEKTRİK","IP güvenlik kamerası — iç mekân (soyunma ve WC HARİÇ)","adet", len(KAMERA), 5400, 9000,"M"),
("05.33","ELEKTRİK","NVR + 4 TB disk + 9U rack kabinet","takım",1, 24000, 40000,"M"),
("05.34","ELEKTRİK","Tavan hoparlörü 6 W / 100 V hat","adet", len(HOPARLOR), 1650, 2800,"M"),
("05.35","ELEKTRİK","Anfi / ses matrisi 120 W + kaynak","takım",1, 14000, 24000,"M"),
("05.36","ELEKTRİK","Geçiş kontrol — kapı okuyucu + elektrikli kilit + buton","takım",1, 16500, 28000,"M"),
("05.37","ELEKTRİK","Yangın algılama paneli — 2 zon, aküleriyle","adet",1, 14500, 24500,"M"),
("05.38","ELEKTRİK","Optik duman dedektörü","adet", len(DEDEKTOR), 1250, 2100,"M"),
("05.39","ELEKTRİK","Yangın ihbar butonu / siren + flaşör","adet",3, 1850, 3100,"M"),
("05.40","ELEKTRİK","Zayıf akım kablolaması (Cat6, koaksiyel, ses, algılama)","m", L_ZAYIF, 60, 105,"M"),
("05.45","ELEKTRİK","Topraklama çubuğu, bağlantı ve ölçüm kutusu","takım",1, 8500, 14500,"M"),
("05.46","ELEKTRİK","Ana potansiyel dengeleme barası ve iletkenleri","takım",1, 5200, 8800,"M"),
("05.47","ELEKTRİK","Islak hacim ek potansiyel dengeleme","takım",2, 2800, 4700,"M"),
("05.48","ELEKTRİK","Topraklama direnci ölçümü, izolasyon testi ve rapor","götürü",1, 7500, 13000,"M"),
]

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
("03.02","ISLAK HACİM","Su yalıtımı — çift bileşenli, dönüş 30 cm","m²",             round(ISLAK_M2+L_ISLAK*0.30,1), 480, 780,"M"),
("03.03","ISLAK HACİM","Zemin seramiği R11 kaymaz (malzeme + işçilik)","m²",         ISLAK_M2,         750,  1200,"M"),
("03.04","ISLAK HACİM","Duvar fayansı h=2,20 m (malzeme + işçilik)","m²",            M2_SERAMIK_D,     850,  1350,"M"),
("03.05","ISLAK HACİM","Vitrifiye seti — 2 klozet, 2 lavabo, armatürler","takım",    2,              12000, 22000,"M"),
("03.06","ISLAK HACİM","Duş teknesi + cam duşakabin (2 adet)","adet",                2,              16000, 30000,"M"),
("03.08","ISLAK HACİM","SEÇENEK A — ıslak hacim zemini 15–20 cm yükseltme (hafif dolgu + şap + basamak/rampa)","m²", ISLAK_M2, 850, 1400,"O"),
("03.09","ISLAK HACİM","SEÇENEK B — öğütücülü gri su / atık su pompası (2 ünite + hat)","takım",  1, 72000, 128000,"—"),
("04.01","ZEMİN","Kauçuk karo 40 mm — arena / serbest ağırlık","m²",                ZON_M2["ARENA · SERBEST AĞIRLIK"], 1150, 1800,"M"),
("04.02","ZEMİN","Titreşim matı 10 mm (arena altı — üst katta konut varsayımı)","m²",ZON_M2["ARENA · SERBEST AĞIRLIK"],  300,  520,"O"),
("04.03","ZEMİN","Kauçuk karo 20 mm — fonksiyonel / kardiyo","m²",                  ZON_M2["FONKSİYONEL · KARDİYO"],    700, 1150,"M"),
("04.04","ZEMİN","LVT / laminat parke — dinlenme + giriş / banko","m²",             round(ZON_M2["DİNLENME SALONU"]+ZON_M2["GİRİŞ · BANKO · SİRKÜLASYON"],2), 550, 950,"M"),
("04.05","ZEMİN","Süpürgelik, geçiş profilleri, eşikler","m",                       round(L_SALON+L_ISLAK,1),           160,  290,"M"),
("07.01","BOYA · DEKOR","Silinebilir mat duvar boyası (astar + 2 kat)","m²",         M2_DUVAR_SALON,   150,   280,"M"),
("07.02","BOYA · DEKOR","Tavan boyası / açık tavan siyah boya (endüstriyel)","m²",   M2_TAVAN,         180,   310,"M"),
("07.03","BOYA · DEKOR","Ayna — arena ve fonksiyonel alan (6 mm, montaj dahil)","m²",14,              1150,  1950,"O"),
("07.04","BOYA · DEKOR","Duvar grafiği / marka uygulaması","götürü",                 1,              28000,  60000,"O"),
("08.01","MARANGOZ","Resepsiyon bankosu — 2,40 m, kompakt lamine tezgâh","m",        2.4,            11000,  19000,"M"),
("08.02","MARANGOZ","Soyunma dolabı / askılık — 24 göz (2 blok)","göz",              24,              2400,   4200,"M"),
("08.03","MARANGOZ","Oturma bankı (soyunma) + dinlenme mobilyası","götürü",          1,              34000,  66000,"O"),
("09.01","YANGIN · GÜVENLİK","6 kg KKT yangın söndürücü + dolap + montaj","adet",     4,               3200,   5400,"M"),
("09.03","YANGIN · GÜVENLİK","Keskin köşe / kolon darbe hafifletici kaplama","m",     18,               850,   1500,"M"),
("09.04","YANGIN · GÜVENLİK","Engelli erişimi — rampa, tutamak, kapı genişliği düzenlemesi","götürü",1,30000,  65000,"M"),
("09.05","YANGIN · GÜVENLİK","İlk yardım dolabı, AED, acil çıkış donanımı","takım",   1,              24000,  45000,"M"),
("10.01","TABELA · DIŞ","Işıklı kutu harf tabela + cephe folyo","götürü",            1,              48000,  95000,"O"),
("10.02","TABELA · DIŞ","Cephe doğrama temizlik / bakım, giriş kapısı revizyonu","götürü",1,          26000,  50000,"M"),
] + B_MEK + B_ELK
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
 "2 × 6 kW elektrikli ani ısıtıcı — poz 06.40. Doğalgaz varsa kombi daha ekonomik", "S"),
("Dinlenme salonu ≥15 m², zemini halıfleks/parke vb.",
 "Kuzey kol → 17,33 m², LVT/laminat parke", "Sağlanıyor — plan sabitlenmeli", "Y"),
("Sporcu sayısı kadar soyunma dolabı / askılık",
 "Mevcut yok", "24 göz dolap + 2 bank — poz 08.02", "Y"),
("Salon ısısı ≥18 °C",
 "Mevcut ısıtma bilinmiyor", "Bölge bazlı split küme — 4 iç ünite, 66.000 BTU kurulu (57.000 BTU hesaplandı) — poz 06.20–06.22", "Y"),
("Sporcu sayısına göre yeterli havalandırma",
 "Mekanik havalandırma yok",
 "1.000 m³/h taze hava = 3,0 hava değişimi/saat = 71 m³/h·kişi — poz 06.01–06.16", "Y"),
("Zeminin spor dalına uygun malzemeyle kaplanması",
 "Mağaza zemini — çıplak/mobilya kaplaması",
 "3 bölgeli kauçuk (40/20 mm) + LVT + ıslak hacim R11 seramik", "Y"),
("Yangın söndürme ekipmanı · itfaiye uygunluk raporu",
 "Mevcut değil",
 "4 adet 6 kg KKT (poz 09.01) + 2 zonlu algılama paneli ve 6 dedektör (poz 05.37–05.39); İBB İtfaiye denetim başvurusu", "S"),
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
 "Bağlı güç 26,59 kW / talep 17,03 kW — trifaze 3×32 A abonelik gerekir (elektrik projesi s.5)", "S"),
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
