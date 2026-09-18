# -*- coding: utf-8 -*-
"""TEK KAYNAK: tum cizim, tablo, metraj ve maliyet buradan beslenir.
Bir sayiyi degistirmek icin SADECE bu dosyayi duzenleyin."""
import json, math
from pathlib import Path
from shapely.geometry import Polygon, Point, box
from shapely import affinity

ROOT = Path(__file__).resolve().parent.parent
G    = json.loads((ROOT/"data/geometry.json").read_text())

REV        = "Rev G"
TARIH      = "17 Eylül 2026"
FIYAT_TARIH= ("Eylül 2026 · Aqua Florya / Saltbae kesin hakedişi (Mayıs 2025) "
              "birim fiyatları ×1,40 eskalasyonla")
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
 "santiye_gider":  (0.12,"","şantiye kurulumu, temizlik, nakliye, poz dışı işçilik — referans projede %12"),
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


# ── DUVAR YÖNÜ: cihazlar duvara göre döndürülür ───────────────────────────────
_DUVAR_SEG = []
for _g in (SALON, ERKEK, KADIN):
    _r = list(_g.exterior.coords)
    for _i in range(len(_r)-1):
        _a, _b = _r[_i], _r[_i+1]
        if math.dist(_a, _b) > 0.12:
            _DUVAR_SEG.append((_a, _b))

def _segler(poly=None):
    """Duvar segmentleri — poly verilirse yalnızca o hacmin çeperi (cihaz komşu
    hacmin duvarına yapışmasın diye)."""
    if poly is None: return _DUVAR_SEG
    r = list(poly.exterior.coords)
    return [(r[i], r[i+1]) for i in range(len(r)-1) if math.dist(r[i], r[i+1]) > 0.12]

def duvar_yonu(p, poly=None):
    """En yakın duvar segmentini bulur.
    Döner: (duvar_acisi_derece, ice_bakan_normal_acisi_derece, mesafe_m)"""
    from shapely.geometry import LineString as _L, Point as _Pt
    pt = _Pt(p); en = None
    for a, b in _segler(poly):
        d = _L([a, b]).distance(pt)
        if en is None or d < en[0]: en = (d, a, b)
    d, a, b = en
    ac = math.degrees(math.atan2(b[1]-a[1], b[0]-a[0]))
    # içe bakan normal: iki adaydan iç hacimde kalanı seç
    ref = poly if poly is not None else SALON
    for n_ac in (ac+90, ac-90):
        q = (p[0]+math.cos(math.radians(n_ac))*0.35,
             p[1]+math.sin(math.radians(n_ac))*0.35)
        if ref.contains(_Pt(q)) or SALON.contains(_Pt(q)) \
           or ERKEK.contains(_Pt(q)) or KADIN.contains(_Pt(q)):
            return round(ac % 360, 1), round(n_ac % 360, 1), round(d, 3)
    return round(ac % 360, 1), round((ac+90) % 360, 1), round(d, 3)

def duvara_yapistir(p, ofset=0.16, poly=None):
    """Noktayı en yakın duvar segmentine dik izdüşürür ve içeri ofset kadar çeker."""
    from shapely.geometry import LineString as _L, Point as _Pt
    pt = _Pt(p); en = None
    for a, b in _segler(poly):
        ls = _L([a, b]); d = ls.distance(pt)
        if en is None or d < en[0]: en = (d, ls, a, b)
    _, ls, a, b = en
    q = ls.interpolate(ls.project(pt))
    _, n_ac, _ = duvar_yonu((q.x, q.y), poly)
    return (round(q.x + math.cos(math.radians(n_ac))*ofset, 3),
            round(q.y + math.sin(math.radians(n_ac))*ofset, 3))

def _ayir_duvar_uzeri(cihazlar, asgari=0.42):
    """Duvar üzerindeki cihazları çevre boyunca 1B olarak ayırır (çakışma çözer).
    cihazlar: [(anahtar, (x,y))] → {anahtar: (x,y)}"""
    from shapely.geometry import LineString as _L, Point as _Pt
    halkalar = [(g, _L(g.exterior.coords)) for g in (SALON, ERKEK, KADIN)]
    gruplar = {}
    for k, p in cihazlar:
        i = min(range(len(halkalar)), key=lambda j: halkalar[j][1].distance(_Pt(p)))
        gruplar.setdefault(i, []).append((k, p))
    sonuc = {}
    for i, liste in gruplar.items():
        g, r = halkalar[i]; L = r.length
        kayit = sorted(((r.project(_Pt(p)), k) for k, p in liste))
        # ileri geçiş: asgari aralığı zorla
        for j in range(1, len(kayit)):
            if kayit[j][0] - kayit[j-1][0] < asgari:
                kayit[j] = (kayit[j-1][0] + asgari, kayit[j][1])
        # halka başına taşarsa geriye doğru sıkıştır
        if kayit and kayit[-1][0] > L - 0.2:
            kaydir = kayit[-1][0] - (L - 0.2)
            kayit = [(max(0.2, s0 - kaydir), k) for s0, k in kayit]
        for s0, k in kayit:
            q = r.interpolate(s0 % L)
            _, n_ac, _ = duvar_yonu((q.x, q.y), g)
            sonuc[k] = (round(q.x + math.cos(math.radians(n_ac))*0.16, 3),
                        round(q.y + math.sin(math.radians(n_ac))*0.16, 3))
    return sonuc

def cihaz_acisi(p, poly=None):
    """Duvara monte sembolün dönme açısı: sembolün 'yukarı'sı hacmin içine bakar."""
    _, n_ac, _ = duvar_yonu(p, poly)
    return round((n_ac - 90) % 360, 1)


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
# Ana kanal güzergâhları ORTOGONAL üretilir (tools/kanal_yollari.py) ve
# data/kanallar.json içinde saklanır; burada yalnızca okunur. Dosya yoksa
# yukarıdaki elle girilmiş güzergâh yedek olarak kalır.
def _kanal_guzergah_yukle():
    import json as _json
    from pathlib import Path as _Path
    f = _Path(__file__).resolve().parent.parent/"data"/"kanallar.json"
    if not f.exists(): return
    d = _json.loads(f.read_text(encoding="utf-8"))
    for ad, g in d.items():
        if ad in KANAL and len(g) > 1:
            KANAL[ad]["guzergah"] = [(float(x), float(y)) for x, y in g]
_kanal_guzergah_yukle()

# menfez / valf: (kod, x, y, debi m³/h, tip)
MENFEZ = [
 ("M1", 1.95, 4.75, 250, "besleme"), ("M2", 4.30, 5.15, 250, "besleme"),
 ("M3", 7.45, 7.15, 250, "besleme"), ("M4", 8.55,10.05, 250, "besleme"),
 ("E1", 2.90, 1.60, 255, "egzoz"),   ("E2", 5.60, 1.20, 255, "egzoz"),
 ("E3", 8.20, 1.40, 250, "egzoz"),
 ("V1", 9.45, 8.05,  80, "valf"),    ("V2",10.35, 8.10,  40, "valf"),
 ("V3",10.75, 1.85,  80, "valf"),    ("V4", 9.85, 1.35,  40, "valf"),
]
PANJUR = [("TH", 0.30, 6.25, "Dış hava panjuru 500×300 + kuş teli"),
          ("EG", 0.42, 2.45, "Egzoz panjuru 400×300"),
          ("EI",11.45, 2.40, "Islak hacim egzoz çıkışı Ø160")]
FAN = [(k, x, y, t, round(duvar_yonu((x, y))[0] % 180, 1)) for k, x, y, t in
      [("F-TH", 1.20, 7.05, "Kanal tipi taze hava fanı — 1.000 m³/h / 250 Pa"),
       ("F-EG", 1.25, 1.95, "Kanal tipi egzoz fanı — 760 m³/h / 200 Pa"),
       ("F-IS", 9.45, 5.40, "Islak hacim egzoz fanı — 240 m³/h, sessiz tip")]]

# ── iklimlendirme: bölge bazlı split küme ─────────────────────────────────────
def _btu(m2, w=180): return int(round(m2*w*3.412/1000)*1000)
_KLIMA0 = [
 ("K1","ARENA · SERBEST AĞIRLIK", 24000, (6.85, 0.28)),
 ("K2","FONKSİYONEL · KARDİYO",   18000, (7.95, 6.95)),
 ("K3","GİRİŞ · BANKO · SİRKÜLASYON", 12000, (1.30, 7.35)),
 ("K4","DİNLENME SALONU",         12000, (7.05,11.90)),
]
# iç üniteler SALON çeperine yapışır — komşu ıslak hacmin duvarına kaymamalı
KLIMA = [(k, z, b, duvara_yapistir(p, 0.18, SALON),
          cihaz_acisi(duvara_yapistir(p, 0.18, SALON), SALON))
         for k, z, b, p in _KLIMA0]
KLIMA_KOT = 2.40                      # iç ünite alt kotu (m)
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
def _isitici(k, x, y, t, poly):
    q = duvara_yapistir((x, y), 0.15, poly)
    return (k, q[0], q[1], t, cihaz_acisi(q, poly))
ISITICI = [_isitici("SI-1", 9.70, 7.60, "Depolu elektrikli boyler 100 L / 3 kW — erkek bloğu", ERKEK),
           _isitici("SI-2",10.55, 2.15, "Depolu elektrikli boyler 100 L / 3 kW — kadın bloğu", KADIN)]
ISITICI_KOT = 1.90
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

def _duvara_oturt(liste, poly=None):
    """(kod, x, y, tanım) → (kod, x, y, tanım, açı) — sembol duvara göre döner."""
    return [(k, x, y, t, cihaz_acisi((x, y), poly)) for k, x, y, t in liste]

# MONTAJ TÜRÜ belirleyicidir: duvar cihazları duvara oturtulur ve çakışmaları
# çevre boyunca çözülür; tavan ve zemin cihazları serbest konumlandırılır.

# — duvara monte: konumlar duvara izdüşürülüp 1B ayrıştırma ile çakışmadan kurtarılır
_DUVAR_CIHAZ = (
  [("PR%d" % (i+1), (x, y), "ikili topraklı priz", "PRIZ")
   for i, (x, y) in enumerate(_duvar_boyunca(SALON, 16, 0.20, 0.03))]
+ [("PI1", (9.80, 7.45), "IP44 priz — erkek soyunma", "PRIZ44"),
   ("PI2", (10.45, 2.75), "IP44 priz — kadın soyunma", "PRIZ44"),
   ("A1", (0.30, 4.40), "vaviyen — ana giriş", "ANAHTAR"),
   ("A2", (1.05, 7.95), "vaviyen — banko", "ANAHTAR"),
   ("A3", (6.10, 8.75), "komütatör — fonksiyonel", "ANAHTAR"),
   ("A4", (6.45, 9.95), "dinlenme salonu", "ANAHTAR"),
   ("A5", (3.95, 0.10), "arena aydınlatma", "ANAHTAR"),
   ("A6", (8.85, 8.30), "erkek soyunma", "ANAHTAR"),
   ("A7", (9.05, 4.40), "kadın soyunma", "ANAHTAR"),
   ("C1", (0.55, 6.60), "giriş ve banko", "KAMERA"),
   ("C2", (3.05, 8.55), "salon kuzey", "KAMERA"),
   ("C3", (8.75, 6.05), "salon doğu — soyunma koridoru girişi", "KAMERA"),
   ("C4", (5.60, 0.10), "kardiyo ve güney cephe", "KAMERA"),
   ("C5", (9.60, 11.20), "dinlenme salonu", "KAMERA"),
   ("YB1", (0.42, 3.55), "yangın ihbar butonu — ana çıkış", "YANGIN"),
   ("YB2", (3.05, 0.55), "yangın ihbar butonu — ikinci çıkış", "YANGIN"),
   ("SR1", (1.55, 8.30), "siren + flaşör", "YANGIN"),
   ("AY1", (0.55, 4.95), "çıkış yönlendirme — ana giriş", "ACILY"),
   ("AY2", (3.60, 0.15), "çıkış yönlendirme — ikinci çıkış", "ACILY"),
   ("AY3", (6.75, 8.85), "çıkış yönlendirme — dinlenme geçişi", "ACILY"),
   ("AP",  (2.35, 8.15), "ana dağıtım panosu", "PANO")]
)
_YERLESIM = _ayir_duvar_uzeri([(k, p_) for k, p_, t, tip in _DUVAR_CIHAZ], asgari=0.45)
def _al(tip):
    return [(k, _YERLESIM[k][0], _YERLESIM[k][1], t, cihaz_acisi(_YERLESIM[k]))
            for k, p_, t, tp in _DUVAR_CIHAZ if tp == tip]

PRIZ_DUVAR = _al("PRIZ")
PRIZ_IP44  = _al("PRIZ44")
ANAHTAR    = _al("ANAHTAR")
KAMERA     = [(k, x, y, t, round((cihaz_acisi((x, y)) + 90) % 360, 1)) for k, x, y, t, a in _al("KAMERA")]
YANGIN     = _al("YANGIN")
ACIL_YON   = _al("ACILY")
PANO       = (_YERLESIM["AP"][0], _YERLESIM["AP"][1])
PANO_ACI   = cihaz_acisi(PANO)

# — zemin / mobilya üstü prizler (duvarda DEĞİL: yer kutusu veya banko gömme)
PRIZ_ZEMIN = [("PB1", 1.92, 6.20, "banko gömme kuvvet + veri kutusu", 0),
              ("PK1", 4.70, 1.02, "yer kutusu — koşu bandı 1", 0),
              ("PK2", 7.30, 1.02, "yer kutusu — koşu bandı 2", 0),
              ("PK3", 8.62, 2.62, "yer kutusu — kondisyon bisikleti", 0)]
PRIZ = PRIZ_DUVAR + PRIZ_ZEMIN

# — tavana monte
SENSOR   = [("S1", 9.98, 7.34, "hareket sensörü — erkek ıslak", 0),
            ("S2",10.25, 2.05, "hareket sensörü — kadın ıslak", 0),
            ("S3", 7.10, 9.55, "hareket sensörü — dinlenme geçişi", 0)]
HOPARLOR = [("H%d" % (i+1), x, y, "tavan hoparlörü 6 W / 100 V")
            for i, (x, y) in enumerate([(2.30,4.60),(5.10,6.95),(7.85,4.95),
                                        (3.60,2.20),(7.35,2.05),(8.35,11.35)])]
VERI     = [("D1", 1.92, 6.05, "banko — router + NVR rack 9U"),
            ("D2", 1.92, 5.55, "banko — POS / kayıt"),
            ("AP1",4.60, 6.10, "kablosuz erişim noktası — tavan"),
            ("AP2",7.55, 10.35,"kablosuz erişim noktası — dinlenme, tavan")]
DEDEKTOR = [("Y%d" % (i+1), x, y, "optik duman dedektörü")
            for i, (x, y) in enumerate([(2.95,5.55),(5.90,7.05),(7.95,3.85),(4.10,1.70),
                                        (7.20,11.45),(9.85,6.35)])]
ACIL_TAVAN = [("AA%d" % (i+1), x, y, "acil aydınlatma — tavan")
              for i, (x, y) in enumerate([(1.50,4.05),(4.05,1.40),(5.65,7.55),
                                          (8.60,10.30),(9.20,5.95)])]
ACIL     = [(k, x, y, "acil aydınlatma", 0) for k, x, y, t in ACIL_TAVAN] + ACIL_YON


# ── linye (devre) tablosu ─────────────────────────────────────────────────────
# (kod, tanım, koruma, kesit, bağlı güç kW, eşzamanlılık katsayısı)
_LINYE = [
 ("L1","Aydınlatma — arena / serbest ağırlık","1×10 A","3×2,5", 7*0.040, 1.00),
 ("L2","Aydınlatma — fonksiyonel / kardiyo","1×10 A","3×2,5", 3*0.040, 1.00),
 ("L3","Aydınlatma — dinlenme salonu","1×10 A","3×2,5", 3*0.040, 1.00),
 ("L4","Aydınlatma — giriş / banko","1×10 A","3×2,5", 2*0.040, 1.00),
 ("L5","Aydınlatma — ıslak hacim (IP44)","1×10 A","3×2,5", 6*0.018, 0.60),
 ("L6","Acil aydınlatma ve yönlendirme","1×6 A","3×2,5", 8*0.008, 1.00),
 ("P1","Priz — salon kuzey (PR12–PR16, PR1)","1×16 A","3×2,5", 0.90, 0.50),
 ("P2","Priz — salon güney (PR5–PR9)","1×16 A","3×2,5", 0.75, 0.50),
 ("P6","Priz — salon batı ve doğu (PR2–PR4, PR10, PR11)","1×16 A","3×2,5", 0.75, 0.50),
 ("P3","Priz — banko, POS, veri","1×16 A","3×2,5", 1.00, 0.70),
 ("P4","Priz — kardiyo ekipmanı (ayrı linye)","1×16 A","3×2,5", 2.40, 0.80),
 ("P5","Priz — ıslak hacim IP44 (ayrı kaçak akım)","1×16 A","3×2,5", 0.50, 0.30),
 ("K1","Klima — arena 24.000 BTU","1×16 A","3×2,5", 2.20, 0.85),
 ("K2","Klima — fonksiyonel 18.000 BTU","1×16 A","3×2,5", 1.70, 0.85),
 ("K3","Klima — giriş 12.000 BTU","1×16 A","3×2,5", 1.15, 0.85),
 ("K4","Klima — dinlenme 12.000 BTU","1×16 A","3×2,5", 1.15, 0.70),
 ("W1","Su ısıtıcı — erkek bloğu, boyler 3 kW","1×20 A","3×2,5", 3.00, 0.60),
 ("W2","Su ısıtıcı — kadın bloğu, boyler 3 kW","1×20 A","3×2,5", 3.00, 0.60),
 ("V1","Havalandırma — taze hava + egzoz fanı","1×10 A","3×2,5", 0.45, 1.00),
 ("V2","Islak hacim egzoz fanı","1×6 A","3×2,5", 0.12, 0.80),
 ("Z1","Zayıf akım — rack, CCTV, ses, geçiş kontrol","1×10 A","3×2,5", 0.60, 0.90),
 ("Z2","Yangın algılama paneli (kesintisiz)","1×6 A","3×2,5", 0.15, 1.00),
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


# ═══════════ PANO YÜK VE GERİLİM DÜŞÜMÜ HESABI (E-07) ═════════════════════════
# Kabuller — hepsi tek yerden değiştirilebilir:
U_FAZ      = 230.0        # V, faz-nötr
U_HAT      = 400.0        # V, fazlar arası
RHO_CU     = 0.0225       # Ω·mm²/m — bakır, 70 °C işletme sıcaklığı (TS HD 60364-5-52)
COSFI      = {"L": 0.95, "P": 0.90, "K": 0.85, "W": 1.00, "V": 0.85, "Z": 0.90}
DU_SINIR   = {"L": 3.0, "P": 5.0, "K": 5.0, "W": 5.0, "V": 5.0, "Z": 3.0}   # % (TS HD 60364-5-52 Ek G)
# PVC yalıtımlı bakır, B2 döşeme yöntemi, 2 yüklü iletken, 30 °C (A)
IZ_B2      = {1.5: 16.5, 2.5: 23.0, 4.0: 31.0, 6.0: 40.0, 10.0: 54.0, 16.0: 73.0}
HAT_KATSAYI = 1.25        # güzergâh kıvrımı payı
HAT_DUSEY   = 6.0         # m — panodan tavana ve cihaza iniş payı

# her linyenin ağırlık merkezi (kablo boyu hesabı için)
_LINYE_NOKTA = {
 "L1": (5.30, 3.20), "L2": (6.40, 7.45), "L3": (8.05, 11.10), "L4": (1.55, 3.60),
 "L5": (9.90, 5.20), "L6": (3.60, 5.40),
 "P1": (3.00, 9.60), "P2": (6.60, 1.10), "P3": (1.92, 6.20), "P4": (7.90, 1.40),
 "P5": (10.10, 6.60), "P6": (0.60, 5.20),
 "K1": (6.85, 0.18), "K2": (7.60, 8.10), "K3": (0.90, 3.60), "K4": (8.50, 11.60),
 "W1": (10.47, 7.71), "W2": (10.90, 2.05),
 "V1": (2.40, 2.10), "V2": (9.90, 4.90),
 "Z1": (1.92, 6.05), "Z2": (1.40, 5.60),
}
def _kesit_mm2(metin):        # "3×2,5" → 2.5
    return float(metin.split("×")[1].replace(",", "."))
def _kesici_a(metin):         # "1×16 A" → 16
    return int(metin.split("×")[1].split()[0])

def _hat_uzunluk(kod):
    return round(math.dist(PANO, _LINYE_NOKTA[kod])*HAT_KATSAYI + HAT_DUSEY, 1)

PANO_HESAP = []               # kod, tanım, faz, Pb, Pt, cosφ, Ib, In, kesit, Iz, L, ΔU V, ΔU %, sınır, sonuç
for kod, tanim, kor, kes, faz, bagli, es, talep in LINYE:
    grup = kod[0]
    cf   = COSFI[grup]
    Ib   = bagli*1000/(U_FAZ*cf)
    In   = _kesici_a(kor)
    Akes = _kesit_mm2(kes)
    Iz   = IZ_B2[Akes]
    Lm   = _hat_uzunluk(kod)
    dU   = 2*Lm*Ib*RHO_CU*cf/Akes              # V — tek fazlı
    dUp  = 100*dU/U_FAZ
    sinir= DU_SINIR[grup]
    ok   = (Ib <= In <= Iz) and (dUp <= sinir)
    PANO_HESAP.append((kod, tanim, faz, bagli, talep, cf, round(Ib,1), In, kes,
                       Iz, Lm, round(dU,1), round(dUp,2), sinir,
                       "UYGUN" if ok else "GÖZDEN GEÇİR"))
PANO_UYGUNSUZ = [r for r in PANO_HESAP if r[14] != "UYGUN"]
DU_MAX = max(r[12] for r in PANO_HESAP)
DU_MAX_LINYE = [r[0] for r in PANO_HESAP if r[12] == DU_MAX][0]

# ── ana besleme (sayaç / kolon → gym panosu) ──────────────────────────────────
ANA_COSFI   = 0.92
ANA_IB      = round(TALEP_KW*1000/(math.sqrt(3)*U_HAT*ANA_COSFI), 1)
ANA_IN      = ANA_KESICI//3
ANA_KESIT   = 10.0
ANA_IZ      = IZ_B2[ANA_KESIT]
ANA_L       = 25.0          # m — VARSAYIM: sayaç panosu ile gym panosu arası
ANA_DU      = round(math.sqrt(3)*ANA_L*ANA_IB*RHO_CU*ANA_COSFI/ANA_KESIT, 2)
ANA_DU_P    = round(100*ANA_DU/U_HAT, 2)
ANA_KABLO   = f"NYY 5×{int(ANA_KESIT)} mm²"
TOPLAM_DU_MAX = round(ANA_DU_P + DU_MAX, 2)

# ── kaçak akım koruma grupları ────────────────────────────────────────────────
KACAK_AKIM = [
 ("RCD-1","4×40 A / 30 mA, A tipi","Aydınlatma grubu — L1 · L2 · L3 · L4 · L6"),
 ("RCD-2","4×40 A / 30 mA, A tipi","Priz grubu ve zayıf akım — P1 · P2 · P3 · P4 · P6 · Z1"),
 ("RCD-3","2×40 A / 30 mA, A tipi","Islak hacim — L5 · P5 (ayrı, TS HD 60364-7-701)"),
 ("RCD-4","2×40 A / 30 mA, A tipi","Su ısıtıcıları — W1 · W2 (her biri ayrı bloklu)"),
 ("RCD-5","4×40 A / 30 mA, A tipi","Klima ve havalandırma — K1–K4 · V1 · V2"),
 ("—",    "Korumasız (izlenir)",   "Z2 yangın algılama paneli — kesintisiz beslenir, "
                                   "kaçak akım rölesi arkasına alınmaz"),
]
ANA_KACAK = "4×63 A / 300 mA, S tipi (seçicilik) — ana giriş"

# ── TOPRAKLAMA VE POTANSİYEL DENGELEME ───────────────────────────────────────
# Dayanak: Elektrik Tesislerinde Topraklamalar Yönetmeliği (RG 21.08.2001/24500),
# TS HD 60364-4-41, TS HD 60364-5-54, TS EN 62305 (yıldırım).
# Mevcut yapıda temel topraklaması bulunmadığı kabul edilmiştir (VARSAYIM —
# yerinde ölçülecek); bu nedenle çubuk elektrot grubu + çevre şeridi öngörülür.
TOPRAK_SISTEM   = "TN-S"            # sayaç sonrası N ve PE ayrılır
TOPRAK_HEDEF    = 20.0              # Ω — yönetmelik üst sınırı (RCD'li tesis)
TOPRAK_TOPRAK_R = 100.0             # Ω·m — toprak özdirenci VARSAYIM (killi-kumlu)
ELEKTROT_BOY    = 2.0               # m — çubuk elektrot (Cu kaplı çelik Ø16)
ELEKTROT_CAP    = 0.016             # m
SERIT_KESIT     = "30×3,5 mm galvanizli çelik şerit"
ANA_KORUMA_ILET = "16 mm² Cu (sarı-yeşil)"     # ana topraklama iletkeni
DENGELEME_ILET  = "6 mm² Cu"                    # ek potansiyel dengeleme

# Elektrot konumları — yapı dışı, arka bahçe çeperinde, 3 m aralıkla
ELEKTROT = [("TE-1", 11.95, 10.30), ("TE-2", 11.95, 7.30),
            ("TE-3", 11.95, 4.30),  ("TE-4", 11.95, 1.30)]
# Ana topraklama barası (ATB) panonun hemen altında
ATB = (2.95, 7.70)
# Ek potansiyel dengeleme baraları — her ıslak blokta bir adet
EPDB = [("EPDB-1", 9.60, 6.95, "Erkek bloğu — duş/WC metal boru ve süzgeç bağları"),
        ("EPDB-2", 10.05, 2.35, "Kadın bloğu — duş/WC metal boru ve süzgeç bağları")]

def _elektrot_direnci(n=len(ELEKTROT)):
    """Tek çubuk: R = ρ/(2πL)·ln(4L/d).  n çubuk paralel + %25 karşılıklı etki payı."""
    tek = TOPRAK_TOPRAK_R/(2*math.pi*ELEKTROT_BOY)*math.log(4*ELEKTROT_BOY/ELEKTROT_CAP)
    return round(tek/n*1.25, 1)
TOPRAK_R_TEK  = round(TOPRAK_TOPRAK_R/(2*math.pi*ELEKTROT_BOY)*
                      math.log(4*ELEKTROT_BOY/ELEKTROT_CAP), 1)
TOPRAK_R_HESAP = _elektrot_direnci()
TOPRAK_UYGUN  = TOPRAK_R_HESAP <= TOPRAK_HEDEF

# Potansiyel dengelemeye bağlanacak yabancı iletken parçalar
DENGELEME = [
 ("Temiz su ana giriş borusu (metal kısım)", "ATB", "6 mm² Cu, kelepçeli"),
 ("Pis su ana hattı (metal parça varsa)",    "ATB", "6 mm² Cu, kelepçeli"),
 ("Hava kanalı gövdesi — besleme ve egzoz",  "ATB", "6 mm² Cu, iki uçtan"),
 ("Kablo tavası — kuvvet ve zayıf akım",     "ATB", "6 mm² Cu, her 10 m'de bir"),
 ("Klima dış ünite şasisi",                  "ATB", "6 mm² Cu"),
 ("Ring platformu çelik karkası",            "ATB", "6 mm² Cu"),
 ("Duş ve WC metal boru uçları",             "EPDB", "4 mm² Cu"),
 ("Yer süzgeci gövdesi (metal)",             "EPDB", "4 mm² Cu"),
 ("Ayna duvarı metal taşıyıcı profilleri",   "ATB",  "6 mm² Cu"),
 ("Alçıpan karkas (C/U profil) — ıslak hacim", "EPDB", "4 mm² Cu, blok başına 1 nokta"),
]

TOPRAK_NOTLAR = [
 "Sistem TN-S'dir; sayaç panosundan itibaren N ve PE iletkenleri ayrı çekilir, "
 "gym panosunda hiçbir noktada birleştirilmez.",
 "Ana topraklama barası (ATB) panonun altında, 500×50×5 mm bakır bara olarak "
 "tesis edilir; her bağlantı ayrı cıvatalı klemensten yapılır, seri bağlantı yasaktır.",
 f"Elektrot grubu: {len(ELEKTROT)} adet {ELEKTROT_BOY:.0f} m bakır kaplı çelik çubuk, "
 f"3 m aralıkla, {SERIT_KESIT} ile birbirine bağlı.",
 f"Hesaplanan yayılma direnci {TOPRAK_R_HESAP} Ω ≤ {TOPRAK_HEDEF:.0f} Ω. "
 f"Ölçüm yerinde yapılacak; {TOPRAK_HEDEF:.0f} Ω aşılırsa elektrot eklenecektir.",
 "Her ıslak blokta ek potansiyel dengeleme barası (EPDB) bulunur; duş ve WC "
 "içindeki tüm yabancı iletken parçalar buraya bağlanır (TS HD 60364-7-701).",
 "Topraklama ölçüm raporu (yayılma direnci + süreklilik) işletme ruhsatı "
 "dosyasına konur; yılda bir yenilenir.",
 "Zayıf akım sistemleri (veri, CCTV, yangın) ayrı bir fonksiyonel topraklama "
 "barasından beslenir; bu bara ATB'ye tek noktadan bağlanır (yıldız topraklama).",
]



# ── tavan tesisat koordinasyon kotları (M-07) ────────────────────────────────
# Asma tavan boşluğu bölgeden bölgeye farklıdır; her bölge için ayrı kot dizilimi.
# (no, kot_alt, kot_ust, ad, renk_anahtari, yatay_serit)
# Yatay şerit: aynı kotta ilerleyen servisler farklı şeritlere ayrılır —
# A kanal · B mekanik boru · C kuvvet kablo tavası · D zayıf akım · * tüm genişlik
TAVAN_KATMAN = {
 "T2": [   # giriş · dinlenme — boşluk 450 mm (2,75 → 3,20).  Temiz su bu bölgeden geçmez.
  (1, 3.00, 3.17, "Kol hava kanalı 300×150 mm + 25 mm izolasyon", "kanal", "A"),
  (2, 2.93, 2.99, "Soğutucu akışkan bakır hattı + klima drenajı (%1 eğim)", "boru", "B"),
  (3, 2.86, 2.92, "Kablo tavası 100×60 mm — kuvvet ve aydınlatma", "kablo", "C"),
  (4, 2.86, 2.92, "Zayıf akım kanalı 50×50 mm — tavadan ≥ 200 mm yatay ayrık", "zayif", "D"),
  (5, 2.7625, 2.83, "Asma tavan askı + TC47 / TU27 taşıyıcı bölgesi", "tavan", "*"),
 ],
 "T4": [   # soyunma — boşluk 600 mm (2,60 → 3,20).  Islak hacim egzozu bu bölgeden geçmez.
  (6, 2.99, 3.17, "Ana hava kanalı 400×200 mm + 25 mm izolasyon", "kanal", "A"),
  (7, 2.91, 2.97, "Soğutucu akışkan bakır hattı + klima drenajı (%1 eğim)", "boru", "B"),
  (8, 2.84, 2.90, "Kablo tavası 200×60 mm — kuvvet ve aydınlatma", "kablo", "C"),
  (9, 2.78, 2.83, "Zayıf akım kanalı 100×50 mm — tavadan ≥ 200 mm ayrık", "zayif", "D"),
  (10, 2.72, 2.77, "Temiz su PPRC Ø25 (yalıtımlı) — pis su ZEMİNDE, tavanda değil", "su", "B"),
  (11, 2.6125, 2.67, "Asma tavan askı + TC47 / TU27 taşıyıcı bölgesi", "tavan", "*"),
 ],
 "T3": [   # duş · WC — boşluk 800 mm (2,40 → 3,20)
  (12, 2.94, 3.14, "Ana hava kanalı 400×200 mm + 25 mm izolasyon", "kanal", "A"),
  (13, 2.86, 2.92, "Soğutucu akışkan bakır hattı + klima drenajı (%1 eğim)", "boru", "B"),
  (14, 2.79, 2.85, "Kablo tavası 200×60 mm — kuvvet ve aydınlatma", "kablo", "C"),
  (15, 2.73, 2.78, "Zayıf akım kanalı 100×50 mm — tavadan ≥ 200 mm ayrık", "zayif", "D"),
  (16, 2.67, 2.72, "Temiz su PPRC Ø25 (yalıtımlı) — pis su ZEMİNDE, tavanda değil", "su", "B"),
  (17, 2.50, 2.66, "Islak hacim egzoz kanalı Ø160 mm + izolasyon", "kanal", "A"),
  (18, 2.4125, 2.47, "Asma tavan askı + TC47 / TU27 taşıyıcı bölgesi", "tavan", "*"),
 ],
}
TAVAN_BOSLUK = {"T2": 0.45, "T3": 0.80, "T4": 0.60}   # v("tavan_h") = 3,20 kabulüne göre
def tavan_serbestlik(tip):
    """Tesisatın en alt kotu ile asma tavan taşıyıcısının üst kotu arası (mm)."""
    kat = TAVAN_KATMAN[tip]
    tes = min(k[1] for k in kat if k[4] != "tavan")
    tas = max(k[2] for k in kat if k[4] == "tavan")
    return round((tes-tas)*1000)
TAVAN_SERBESTLIK = {t: tavan_serbestlik(t) for t in TAVAN_KATMAN}

TAVAN_KOORD = [
 ("Kanal en üstte", "Hava kanalı en büyük kesitli ve eğimsiz elemandır; önce o yerleştirilir, "
  "diğer tesisat altından geçer."),
 ("Eğimli borular önceliklidir", "Pis su (%2) ve klima drenajı (%1) eğimini kaybedemez; "
  "kanal bu hatların altından geçemez, çakışmada kanal yönlendirilir."),
 ("Kuvvet / zayıf akım ayrımı", "Kuvvet kablosu ile zayıf akım kanalı arasında en az 200 mm "
  "yatay ayrım; kesişme zorunluysa 90° ve ekranlı geçiş."),
 ("Askı bağımsızlığı", "Kanal, boru, tava ve armatür askıları doğrudan döşemeye bağlanır; "
  "alçıpan karkasına hiçbir tesisat asılmaz."),
 ("Serbest yükseklik", "T2 altında 400 mm, T4 altında 600 mm, T3 altında 800 mm tesisat boşluğu "
  "vardır; yukarıdaki katman dizilimi bu boşluklara sığar."),
 ("Revizyon erişimi", "Vana, damper, klima drenaj sifonu ve rakor bulunan her nokta altında "
  "300×300 mm revizyon kapağı açılır."),
]


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
("06.40","MEKANİK","Depolu elektrikli boyler 100 L / 3 kW, emaye kaplı, magnezyum anotlu (blok başına)","adet",2, 11500, 19500,"M"),
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
("05.24","ELEKTRİK","Boyler besleme hattı 3×2,5 mm² + 20 A kesici + 30 mA kaçak akım","adet",2, 4200, 7300,"M"),
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
("01.01","YIKIM · SÖKÜM","Mobilya mağazası raf/vitrin/tezgâh sökümü ve tasnifi","m²",A["ic_toplam"],   340,   580,"M"),
("01.02","YIKIM · SÖKÜM","Mevcut zemin kaplaması sökümü ve şap tesviyesi","m²",      A["ic_toplam"],   420,   650,"M"),
("01.03","YIKIM · SÖKÜM","Islak hacim mevcut seramik + vitrifiye sökümü","m²",       ISLAK_M2,         620,   950,"M"),
("01.04","YIKIM · SÖKÜM","Moloz yükleme, indirme ve nakliye (konteyner)","götürü",   1,             48000, 75000,"M"),
("02.01","DUVAR · ALÇIPAN","Alçıpan bölme duvar — 100 mm, çift kat, taşyünü dolgulu","m²", M2_YENI_BOLME, 3100, 3900,"M"),
("02.02","DUVAR · ALÇIPAN","Islak hacim bölmelerinde yeşil alçıpan / betopan yükseltmesi","m²", round(M2_YENI_BOLME*0.45,1), 350, 520,"M"),
("02.03","DUVAR · ALÇIPAN","Mevcut duvar tamiri, saten alçı ve yüzey hazırlığı","m²", M2_DUVAR_SALON,    380,   560,"M"),
("02.04","DUVAR · ALÇIPAN","Akustik asma tavan adası (arena üzeri) — 12 m²","m²",    12,               2600,  4200,"O"),
("03.02","ISLAK HACİM","Su yalıtımı — çift bileşenli, dönüş 30 cm","m²",             round(ISLAK_M2+L_ISLAK*0.30,1), 800, 1100,"M"),
("03.03","ISLAK HACİM","Zemin seramiği R11 kaymaz (malzeme + işçilik)","m²",         ISLAK_M2,        1730,  2500,"M"),
("03.04","ISLAK HACİM","Duvar fayansı h=2,20 m (malzeme + işçilik)","m²",            M2_SERAMIK_D,    1795,  2650,"M"),
("03.05","ISLAK HACİM","Vitrifiye seti — 2 klozet, 2 lavabo, armatürler","takım",    2,              26000, 48000,"M"),
("03.06","ISLAK HACİM","Duş teknesi + cam duşakabin (2 adet)","adet",                2,              22000, 40000,"M"),
("03.08","ISLAK HACİM","SEÇENEK A — ıslak hacim zemini 15–20 cm yükseltme (hafif dolgu + şap + basamak/rampa)","m²", ISLAK_M2, 1400, 2300,"O"),
("03.09","ISLAK HACİM","SEÇENEK B — öğütücülü gri su / atık su pompası (2 ünite + hat)","takım",  1, 95000, 170000,"—"),
("04.01","ZEMİN","Kauçuk karo 40 mm — arena / serbest ağırlık","m²",                ZON_M2["ARENA · SERBEST AĞIRLIK"], 2750, 3920,"M"),
("04.02","ZEMİN","Titreşim matı 10 mm (arena altı — üst katta konut varsayımı)","m²",ZON_M2["ARENA · SERBEST AĞIRLIK"],  830, 1260,"O"),
("04.03","ZEMİN","Kauçuk karo 20 mm — fonksiyonel / kardiyo","m²",                  ZON_M2["FONKSİYONEL · KARDİYO"],   1650, 2400,"M"),
("04.04","ZEMİN","LVT / laminat parke — dinlenme + giriş / banko","m²",             round(ZON_M2["DİNLENME SALONU"]+ZON_M2["GİRİŞ · BANKO · SİRKÜLASYON"],2), 1370, 2120,"M"),
("04.05","ZEMİN","Süpürgelik, geçiş profilleri, eşikler","m",                       round(L_SALON+L_ISLAK,1),           350,  550,"M"),
("07.01","BOYA · DEKOR","Silinebilir mat duvar boyası (astar + 2 kat)","m²",         M2_DUVAR_SALON,   385,   610,"M"),
("07.02","BOYA · DEKOR","Tavan boyası / açık tavan siyah boya (endüstriyel)","m²",   M2_TAVAN,         405,   630,"M"),
("07.03","BOYA · DEKOR","Ayna — arena ve fonksiyonel alan (6 mm, montaj dahil)","m²",14,              4600,  7400,"O"),
("07.04","BOYA · DEKOR","Duvar grafiği / marka uygulaması","götürü",                 1,              48000,  95000,"O"),
("08.01","MARANGOZ","Resepsiyon bankosu — 2,40 m, kompakt lamine tezgâh","m",        2.4,            26000,  43000,"M"),
("08.02","MARANGOZ","Soyunma dolabı / askılık — 24 göz (2 blok)","göz",              24,              2600,   4400,"M"),
("08.03","MARANGOZ","Oturma bankı (soyunma) + dinlenme mobilyası","götürü",          1,              48000,  92000,"O"),
("09.01","YANGIN · GÜVENLİK","6 kg KKT yangın söndürücü + dolap + montaj","adet",     4,               4500,   7600,"M"),
("09.03","YANGIN · GÜVENLİK","Keskin köşe / kolon darbe hafifletici kaplama","m",     18,              1200,   2100,"M"),
("09.04","YANGIN · GÜVENLİK","Engelli erişimi — rampa, tutamak, kapı genişliği düzenlemesi","götürü",1,42000,  90000,"M"),
("09.05","YANGIN · GÜVENLİK","İlk yardım dolabı, AED, acil çıkış donanımı","takım",   1,              34000,  63000,"M"),
("10.01","TABELA · DIŞ","Işıklı kutu harf tabela + cephe folyo","götürü",            1,              68000, 135000,"O"),
("10.02","TABELA · DIŞ","Cephe doğrama temizlik / bakım, giriş kapısı revizyonu","götürü",1,          50000,  85000,"M"),
("11.01","DOĞRAMA","İç kapı K03 · K04 — panel kapı 90×210, kasa, pervaz ve donanım","adet",2,  18500,  29000,"M"),
("11.02","DOĞRAMA","WC kapısı K05 · K06 — tam WPC 70×200, alt menfezli","adet",          2,  15000,  24500,"M"),
("11.03","DOĞRAMA","Duş kapağı K07 · K08 — 6 mm temperli cam 70×195","adet",             2,  17500,  28000,"M"),
("11.04","DOĞRAMA","Depo / teknik dolap kapağı K09 — havalandırma menfezli","adet",      1,   9000,  15000,"M"),
("11.05","DOĞRAMA","Acil çıkış kapısı K02 — panik bar (EN 1125), kapı kapatıcı","adet",  1,  54000,  88000,"M"),
] + B_MEK + B_ELK
GRUPLAR = ["YIKIM · SÖKÜM","DUVAR · ALÇIPAN","ISLAK HACİM","ZEMİN","ELEKTRİK",
           "MEKANİK","BOYA · DEKOR","MARANGOZ","DOĞRAMA","YANGIN · GÜVENLİK","TABELA · DIŞ"]

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
 "2 × 100 L / 3 kW depolu boyler — poz 06.40. Ani ısıtıcı 6 kW yalnız 2,9 l/dak verir, iki duşu karşılamaz. Doğalgaz varsa kombi daha ekonomik", "S"),
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


# ═══════════════════════════════════════════════════════════════════════════════
#  MİMARİ UYGULAMA PROJESİ VERİSİ  (Rev D)
#  Tüm kaplama, bölme, tavan, kapı ve detay bilgisi bu bloktan türetilir.
# ═══════════════════════════════════════════════════════════════════════════════

# ── kot referansı ──────────────────────────────────────────────────────────────
# ±0,00 = BİTMİŞ ZEMİN KOTU (salon).  Mevcut şap üst kotu = −0,053 kabul edildi;
# tüm kuru hacimlerde bitmiş kot 53 mm tesviye ile eşitlenir → eşik/tökezleme yok.
KOT_MEVCUT_SAP   = -0.053     # m — VARSAYIM, yerinde ölçümle doğrulanacak
KOT_ISLAK        = -0.020     # m — duş/WC bitmiş kotu (su taşkını kontrolü)
KOT_YAPISAL_TAVAN = v("tavan_h")          # 3,20 m — VARSAYIM

# ── ZEMİN KAPLAMA TİPLERİ ──────────────────────────────────────────────────────
# kod, ad, [(katman, mm, tarama)], bitmiş kot, standart/performans
ZEMIN_TIPLERI = [
 ("Z1", "Arena · serbest ağırlık — ağır hizmet kauçuk",
  [("Mevcut betonarme döşeme / şap — yüzey temizliği, ±3 mm/2 m tesviye", 0, "beton"),
   ("Çimento esaslı kendinden yayılan tesviye şapı", 3, "sap"),
   ("Kauçuk titreşim yalıtım matı, SBR granül 700 kg/m³", 10, "kaucuk"),
   ("Granül kauçuk karo 1000×1000 mm, EPDM %10 taneli, Shore A 55±5", 40, "kaucuk")],
  0.000, "EN 14041 · yangın Bfl-s1 · EN ISO 10140 ΔLw ≥ 18 dB · serbest ağırlık düşürmeye uygun"),
 ("Z2", "Fonksiyonel · kardiyo — kauçuk karo",
  [("Mevcut betonarme döşeme / şap", 0, "beton"),
   ("Çimento esaslı tesviye şapı (kot eşitleme)", 30, "sap"),
   ("Granül kauçuk karo 1000×1000 mm, Shore A 60", 20, "kaucuk"),
   ("Puzzle kilitli kuru derz · çeperde 5 mm genleşme boşluğu", 3, "kaucuk")],
  0.000, "EN 14041 · Bfl-s1 · kardiyo cihazı nokta yükü ≥ 4 kN/m²"),
 ("Z3", "Giriş · banko · dinlenme — SPC / LVT",
  [("Mevcut betonarme döşeme / şap", 0, "beton"),
   ("Çimento esaslı tesviye şapı (kot eşitleme)", 42, "sap"),
   ("IXPE akustik şilte", 2, "sunger"),
   ("SPC klik LVT, 0,55 mm aşınma tabakası", 5, "lvt"),
   ("Çeperde 8 mm genleşme boşluğu, süpürgelik altında gizlenir", 4, "lvt")],
  0.000, "EN ISO 10874 aşınma sınıfı 33 / AC5 · EN 14041 Bfl-s1 · kaymazlık DS"),
 ("Z4", "Duş · WC — su yalıtımlı seramik",
  [("Mevcut şap kırımı sonrası betonarme döşeme (tesisat boşluğu)", 0, "beton"),
   ("Atık boru yatağı + tesisat şapı", 25, "sap"),
   ("Eğim şapı — süzgeğe doğru %1,5", 15, "sap"),
   ("Çimento esaslı 2 bileşenli su yalıtımı, 2 kat (köşelerde 12 cm bant)", 2, "yalitim"),
   ("C2TE S1 sınıfı yapıştırıcı", 5, "sap"),
   ("Porselen seramik 300×300 mm, R11 / B kaymazlık", 8, "seramik")],
  KOT_ISLAK, "EN 14891 su yalıtımı · EN 16165 Ek B (R11) · Ek A (B sınıfı ıslak ayak)"),
 ("Z5", "Soyunma — porselen seramik",
  [("Mevcut betonarme döşeme / şap", 0, "beton"),
   ("Çimento esaslı tesviye şapı (kot eşitleme)", 38, "sap"),
   ("Çimento esaslı su yalıtımı, tek kat (sıçrama koruması)", 1, "yalitim"),
   ("C2TE yapıştırıcı", 5, "sap"),
   ("Porselen seramik 600×600 mm, R10", 9, "seramik")],
  0.000, "EN 16165 Ek B (R10) · EN 14411 BIa · rektifiye, 2 mm derz"),
 ("Z6", "Ring platformu (ekipmana bağlı — işverence temin)",
  [("Bitmiş zemin Z1 üzeri ayarlı çelik ayak + 50×100 ahşap kadron @400 mm", 200, "ahsap"),
   ("Su kontraplağı 2 kat 18 mm, şaşırtmalı vidalı", 36, "ahsap"),
   ("EVA şok emici köpük", 40, "sunger"),
   ("Kanvas kaplama, kenarda gergi profili", 10, "kaucuk"),
   ("Kenarda 100 mm kauçuk kenar bandı + sarı-siyah ikaz şeridi", 14, "kaucuk")],
  0.300, "Ekipman üreticisi montaj talimatına tabi · platform kenarı zeminden 30 cm"),
]
# Her zemin tipinin altında kalan taban kotu. Islak hacimde mevcut şabın üst
# 22 mm'si traşlanır (eşik düşümü), ring platformu bitmiş Z1 üzerine oturur.
KOT_ISLAK_TABAN = -0.075     # VARSAYIM — yerinde doğrulanacak
ZEMIN_TABAN = {"Z1": KOT_MEVCUT_SAP, "Z2": KOT_MEVCUT_SAP, "Z3": KOT_MEVCUT_SAP,
               "Z4": KOT_ISLAK_TABAN, "Z5": KOT_MEVCUT_SAP, "Z6": 0.000}
ZEMIN_KALINLIK = {z[0]: sum(k[1] for k in z[2]) for z in ZEMIN_TIPLERI}

# ── DUVAR TİPLERİ ──────────────────────────────────────────────────────────────
# kod, ad, toplam_mm, [(katman, mm)], performans
DUVAR_TIPLERI = [
 ("D1", "Mevcut taşıyıcı / dolgu duvar — boyalı", 206,
  [("Mevcut yığma veya betonarme duvar", 200),
   ("Çimento esaslı tamir harcı ile yüzey onarımı", 0),
   ("Saten alçı perdah, 2 kat", 3),
   ("Akrilik astar + su bazlı silikonlu mat iç cephe boyası, 2 kat", 3)],
  "Sınıf 1 yıkanabilir boya · mevcut duvar kalınlığı VARSAYIM, yerinde ölçülecek"),
 ("D2", "Alçıpan bölme — kuru hacim", 100,
  [("12,5 mm A tipi alçıpan, 2 kat (şaşırtmalı derz)", 25),
   ("50×0,6 mm galvaniz C profil @400 mm + U tabanlık", 50),
   ("Taşyünü dolgu 40 mm / 50 kg/m³", 0),
   ("12,5 mm A tipi alçıpan, 2 kat", 25)],
  "Rw ≈ 51 dB (EN ISO 717-1) · U tabanlık altında butil ses bandı"),
 ("D3", "Alçıpan bölme — ıslak hacim yüzü", 100,
  [("12,5 mm H2 (su itici / yeşil) alçıpan, 2 kat — ıslak yüz", 25),
   ("50×0,6 mm galvaniz C profil @400 mm + U tabanlık", 50),
   ("Taşyünü dolgu 40 mm / 50 kg/m³", 0),
   ("12,5 mm A tipi alçıpan, 2 kat — kuru yüz", 25)],
  "EN 520 tip H2 · ıslak yüzde 2 kat çimento esaslı su yalıtımı + seramik (kalınlık hariç)"),
 ("D4", "Akustik giydirme — arena çeperi", 95,
  [("Mevcut duvardan bağımsız 20 mm hava boşluğu", 20),
   ("50×0,6 mm C profil karkas (duvara bağlantısız, tavan-döşeme arası)", 50),
   ("Taşyünü dolgu 50 mm / 70 kg/m³", 0),
   ("12,5 mm yüksek yoğunluklu akustik alçıpan", 12.5),
   ("12,5 mm A tipi alçıpan + saten + boya", 12.5)],
  "ΔRw ≈ +10 dB · üst kat konut VARSAYIMI gereği arena çeperinde uygulanır"),
 ("D5", "Seramik kaplı duvar — ıslak hacim", 216,
  [("Mevcut duvar veya D3 ıslak yüzü", 200),
   ("Çimento esaslı 2 bileşenli su yalıtımı, 2 kat; köşe ve zemin birleşiminde 12 cm bant", 2),
   ("C2TE S1 yapıştırıcı", 5),
   ("Porselen seramik 300×600 mm, rektifiye", 9)],
  "EN 14891 · duş kabininde tavana kadar, WC'de h=1,60 m, üstü küf önleyici banyo boyası"),
 ("D6", "Ayna duvarı — arena güney çeperi (D1/D4 üzerine giydirme)", 24,
  [("D1 veya D4 üzerine 18 mm su kontraplağı taşıyıcı altlık", 18),
   ("6 mm güvenlik filmli ayna, yapıştırma + mekanik emniyet profili", 6)],
  "Ayna alt kotu +0,30 · üst kotu +2,30 · kırılmaya karşı arka yüz güvenlik filmi (EN 12600)"),
]
DUVAR_T_MM = {d[0]: d[2] for d in DUVAR_TIPLERI}

# ── TAVAN TİPLERİ ──────────────────────────────────────────────────────────────
# kod, ad, kot_m, [(katman/açıklama)], not
TAVAN_TIPLERI = [
 ("T1", "Açık (endüstriyel) tavan", 3.20,
  ["Mevcut döşeme altı raspa + temizlik",
   "Tüm MEP tesisatı görünür — düzenli askı ve hizalı güzergâh zorunlu",
   "2 kat siyah su bazlı akrilik boya (döşeme altı, kanal ve askılar dâhil)",
   "Arena üzerinde 12 adet 1200×600×50 mm asma akustik taşyünü baffle (αw ≈ 0,90)"],
  "Arena · fonksiyonel — serbest yükseklik korunur, ekipman kotu 2,15 m'ye kadar"),
 ("T2", "Alçıpan asma tavan — kuru hacim", 2.75,
  ["Ayarlı askı çubuğu @900 mm, TC47 ana profil @900 / TU27 taşıyıcı @400 mm",
   "12,5 mm A tipi alçıpan tek kat",
   "Derz bandı + 2 kat saten alçı + astar + 2 kat mat boya",
   "Kenar gölge derzi 10 mm (duvar birleşiminde ayrılma çatlağı önlemi)"],
  "Giriş · banko · dinlenme — üstünde 450 mm tesisat boşluğu (kanal + tava + bakır hat sığsın diye "
  "kot 2,80'den 2,75'e indirilmiştir)"),
 ("T3", "Alçıpan asma tavan — ıslak hacim", 2.40,
  ["Galvaniz ayarlı askı @900 mm, TC47 / TU27 karkas",
   "12,5 mm H2 (su itici) alçıpan tek kat",
   "Su bazlı, küf önleyici yarı mat banyo boyası, 2 kat",
   "300×300 mm menteşeli revizyon kapağı (her ıslak hacimde 1 adet)"],
  "Duş · WC — üstünde 800 mm tesisat boşluğu (egzoz kanalı geçişi)"),
 ("T4", "Alçıpan asma tavan — soyunma", 2.60,
  ["T2 ile aynı karkas ve kaplama",
   "Soyunma/duş sınırında kot geçiş bandı (dikme)",
   "Nem nedeniyle duş kapısı önünde 1,0 m şeridinde H2 alçıpan"],
  "Erkek · kadın soyunma — üstünde 600 mm tesisat boşluğu"),
]
TAVAN_KOT = {t[0]: t[2] for t in TAVAN_TIPLERI}

# ── SÜPÜRGELİK ─────────────────────────────────────────────────────────────────
SUPURGELIK = [
 ("S1", "Kauçuk süpürgelik 100×8 mm — zemin kaplamasıyla aynı malzeme, üst kenarı 45° pahlı"),
 ("S2", "MDF lake süpürgelik 80×16 mm — RAL 9003, akrilik mastik ile duvara yalanır"),
 ("S3", "Süpürgelik yok — duvar seramiği zemine iner; birleşimde içbükey (kaveto) profil"),
 ("S4", "Porselen süpürgelik 80 mm — zemin karosundan kesme, rektifiye kenar"),
]

# ── MAHAL LİSTESİ (finishes schedule) ──────────────────────────────────────────
# no, ad, m², zemin, süpürgelik, duvar, tavan, tavan_kot, kapı, ıslak?, not
MAHAL_LISTESI = [
 ("101","GİRİŞ · BANKO · SİRKÜLASYON", ZON_M2["GİRİŞ · BANKO · SİRKÜLASYON"],
  "Z3","S2","D1","T2",2.75,"K01 · K09", False,
  "Cephe vitrini mevcut (P01); alt 1,20 m buzlu folyo. Banko arkası D1 üzeri lake MDF panel."),
 ("102","ARENA · SERBEST AĞIRLIK", ZON_M2["ARENA · SERBEST AĞIRLIK"],
  "Z1","S1","D1 + D4 (güney çeper) + D6 (ayna, 4,80 m)","T1",3.20,"—", False,
  "Ring platformu Z6. Ağırlık düşürme kural olarak yasak — uyarı levhası."),
 ("103","FONKSİYONEL · KARDİYO", ZON_M2["FONKSİYONEL · KARDİYO"],
  "Z2","S1","D1 / D2 (soyunma bloğu cephesi)","T1",3.20,"—", False,
  "Koşu bandı arkasında 60 cm serbest güvenlik mesafesi bırakılacak."),
 ("104","DİNLENME SALONU", ZON_M2["DİNLENME SALONU"],
  "Z3","S2","D1","T2",2.75,"—", False,
  "Yönetmelik gereği asgari 15 m² dinlenme alanı — sağlanıyor."),
 ("105","ERKEK SOYUNMA", ISLAK_M2_DETAY["ERKEK"]["soyunma"],
  "Z5","S4","D2 / D3","T4",2.60,"K03", False,
  "8 kişilik soyunma dolabı + 1,60 m bank + boy aynası. Yönetmelik asgarisi 8 m² blok bazında."),
 ("106","ERKEK DUŞ", ISLAK_M2_DETAY["ERKEK"]["dus"],
  "Z4","S3","D3 + D5 (tavana kadar)","T3",2.40,"K07", True,
  "1 duş yeri; 100×100 mm paslanmaz süzgeç, %1,5 eğim, termostatik batarya."),
 ("107","ERKEK WC", ISLAK_M2_DETAY["ERKEK"]["wc"],
  "Z4","S3","D3 + D5 (h=1,60 m)","T3",2.40,"K05", True,
  "1 klozet + 1 lavabo; ekstraktör fan kapı menfezi ile telafi havası."),
 ("108","KADIN SOYUNMA", ISLAK_M2_DETAY["KADIN"]["soyunma"],
  "Z5","S4","D2 / D3","T4",2.60,"K04", False,
  "8 kişilik soyunma dolabı + 1,60 m bank + boy aynası."),
 ("109","KADIN DUŞ", ISLAK_M2_DETAY["KADIN"]["dus"],
  "Z4","S3","D3 + D5 (tavana kadar)","T3",2.40,"K08", True,
  "1 duş yeri; 100×100 mm paslanmaz süzgeç, %1,5 eğim, termostatik batarya."),
 ("110","KADIN WC", ISLAK_M2_DETAY["KADIN"]["wc"],
  "Z4","S3","D3 + D5 (h=1,60 m)","T3",2.40,"K06", True,
  "1 klozet + 1 lavabo; ekstraktör fan kapı menfezi ile telafi havası."),
]
MAHAL_TOPLAM = round(sum(m[2] for m in MAHAL_LISTESI), 2)
# net mahal alanları toplamı, iç bölme duvar kalınlıkları hariçtir:
MAHAL_DUVAR_PAYI = round(A["ic_toplam"] - MAHAL_TOPLAM, 2)
MAHAL_NO = {m[1]: m[0] for m in MAHAL_LISTESI}

# mahal etiket noktaları (plan üzerinde numara balonu)
MAHAL_NOKTA = {}
for _z in ZONES: MAHAL_NOKTA[MAHAL_NO[_z[0]]] = _z[5]
for _ad, _d in ISLAK.items():
    _blok = "ERKEK" if _ad == "ERKEK" else "KADIN"
    for _n, _no in (("soyunma", "105" if _blok=="ERKEK" else "108"),
                    ("dus",     "106" if _blok=="ERKEK" else "109"),
                    ("wc",      "107" if _blok=="ERKEK" else "110")):
        _q = _d[_n].representative_point(); MAHAL_NOKTA[_no] = (_q.x, _q.y)

# ── KAPI VE PENCERE LİSTESİ ────────────────────────────────────────────────────
# kod, adet, mahal, en_mm, yuk_mm, tip, kasa/kanat, donanım, yangın/özel
KAPI_LISTESI = [
 ("K01",1,"101 Giriş",1600,2400,"Çift kanat cam kapı (2×800)",
  "Mevcut alüminyum doğrama + 8 mm temperli cam",
  "Panik kolu (EN 1125), hidrolik kapı kapatıcı, eşiksiz alt profil",
  "Açılış yönü DIŞARI çevrilecek — mevcut doğrama revize"),
 ("K02",1,"101 → GB cephe",1000,2100,"Tek kanat acil çıkış",
  "Alüminyum + 8 mm temperli cam",
  "Panik bar (EN 1125), kapı kapatıcı, dışa açılır",
  "Acil çıkış levhası + acil aydınlatma AY3 üstünde"),
 ("K03",1,"105 Erkek soyunma",900,2100,"Tek kanat panel kapı",
  "MDF laminat kaplı kanat, WPC kasa ve pervaz",
  "Paslanmaz kol, silindirli kilit, 3 adet menteşe",
  "Alt kısmında 150 cm² net hava geçiş menfezi"),
 ("K04",1,"108 Kadın soyunma",900,2100,"Tek kanat panel kapı",
  "MDF laminat kaplı kanat, WPC kasa ve pervaz",
  "Paslanmaz kol, silindirli kilit, 3 adet menteşe",
  "Alt kısmında 150 cm² net hava geçiş menfezi"),
 ("K05",1,"107 Erkek WC",700,2000,"Tek kanat WC kapısı",
  "Tam WPC (su geçirmez) kanat ve kasa",
  "Kilit göstergeli WC kolu, paslanmaz menteşe",
  "Alt menfez 150 cm² — egzoz telafi havası"),
 ("K06",1,"110 Kadın WC",700,2000,"Tek kanat WC kapısı",
  "Tam WPC (su geçirmez) kanat ve kasa",
  "Kilit göstergeli WC kolu, paslanmaz menteşe",
  "Alt menfez 150 cm² — egzoz telafi havası"),
 ("K07",1,"106 Erkek duş",700,1950,"Duş kapağı",
  "6 mm temperli cam, alüminyum profil",
  "Paslanmaz menteşe, manyetik fitil",
  "Alt kenar zeminden 15 mm yukarıda"),
 ("K08",1,"109 Kadın duş",700,1950,"Duş kapağı",
  "6 mm temperli cam, alüminyum profil",
  "Paslanmaz menteşe, manyetik fitil",
  "Alt kenar zeminden 15 mm yukarıda"),
 ("K09",1,"101 Depo / teknik dolap",700,2000,"Tek kanat dolap kapağı",
  "MDF laminat, banko arkası niş",
  "Bas-aç mandal, kilitli",
  "Havalandırma menfezli — NVR ve router ısısı için"),
]
PENCERE_LISTESI = [
 ("P01",1,"101 Giriş — batı cephe vitrini","Mevcut alüminyum doğrama + 8 mm temperli cam",
  "Alt 1,20 m buzlu folyo · üst bant şeffaf · iç yüzde güneş kontrol filmi",
  "Mevcut — ölçü yerinde alınacak (VARSAYIM: 5,62 m açıklık)"),
 ("P02",1,"101 Giriş — GB cephe vitrini","Mevcut alüminyum doğrama + 8 mm temperli cam",
  "Alt 1,20 m buzlu folyo · K02 acil çıkış bu doğrama içinde",
  "Mevcut — ölçü yerinde alınacak (VARSAYIM: 2,02 m açıklık)"),
]

# ── YIKIM / SÖKÜM İŞ KALEMLERİ ─────────────────────────────────────────────────
# kod, tanım, metraj, birim, not
YIKIM = [
 ("Y01","Mevcut mağaza rafı, teşhir ünitesi ve mobilyanın sökülüp taşınması",
  1,"komple","İşverence devralınacak parçalar önceden ayrılır"),
 ("Y02","Mevcut asma tavan ve aydınlatma armatürlerinin sökümü",
  A["ic_toplam"],"m²","VARSAYIM — mevcutta asma tavan bulunduğu kabul edildi"),
 ("Y03","Mevcut zemin kaplamasının (laminat / seramik) sökümü, altlık temizliği",
  A["ic_toplam"],"m²","Şap yüzeyi tesviye kontrolüne hazır bırakılır"),
 ("Y04","Islak hacim alanında mevcut şap kırımı (tesisat boşluğu için, ort. 70 mm)",
  A["islak_toplam"],"m²","Kırım öncesi döşeme donatısı için tarama yapılacak"),
 ("Y05","Mevcut sıva üstü elektrik tesisatı ve tablosunun sökümü",
  1,"komple","Enerji kesilerek, yetkili elektrikçi nezaretinde"),
 ("Y06","Mevcut ıslak hacim (varsa) armatür ve duvar seramiği sökümü",
  A["islak_toplam"],"m²","VARSAYIM — yerinde tespit sonrası revize edilecek"),
 ("Y07","Yeni kapı boşluklarının açılması, lento teşkili",
  2,"adet","Taşıyıcı duvarda ise statik görüş alınacak — ZORUNLU"),
 ("Y08","Moloz çuvallama, yatay-düşey taşıma ve belediye döküm sahasına nakli",
  14,"m³","VARSAYIM — söküm sonrası gerçek hacimle revize edilecek"),
]
YIKIM_NOT = ("Mevcutta iç bölme duvarı bulunmadığı, mekânın tek hacim mağaza olduğu VARSAYILMIŞTIR. "
             "Söküm öncesi mevcut durum rölövesi alınacak; taşıyıcı sistemde hiçbir elemana "
             "dokunulmayacaktır. Kolon, perde ve döşeme kirişlerinde kesme/delme yasaktır.")

# ── KESİT HATLARI ──────────────────────────────────────────────────────────────
KESIT_HATLARI = {
 "A-A": ((-0.70, 7.30), (12.30, 7.30),
         "Enine kesit — fonksiyonel alan, erkek duş ve WC bloğu"),
 "B-B": ((6.60, -0.70), (6.60, 13.70),
         "Boyuna kesit — arena, altıgen ring, fonksiyonel alan ve dinlenme salonu"),
}

# hangi hacimde olduğumuzu döndüren yardımcı (kesit üretimi için)
_MAHAL_GEOM = ([(z[0], MAHAL_NO[z[0]], z[1]) for z in ZONES] +
               [("ERKEK SOYUNMA","105",ISLAK["ERKEK"]["soyunma"]),
                ("ERKEK DUŞ",    "106",ISLAK["ERKEK"]["dus"]),
                ("ERKEK WC",     "107",ISLAK["ERKEK"]["wc"]),
                ("KADIN SOYUNMA","108",ISLAK["KADIN"]["soyunma"]),
                ("KADIN DUŞ",    "109",ISLAK["KADIN"]["dus"]),
                ("KADIN WC",     "110",ISLAK["KADIN"]["wc"])])
_MAHAL_BILGI = {m[0]: m for m in MAHAL_LISTESI}

def kesit_dizisi(a, b, adim=0.01):
    """Kesit hattı boyunca hangi mahalden geçildiğini tarar.
    Döner: [(mahal_no | None, s_bas, s_son)] — s = hat başından uzaklık (m).
    None = duvar veya yapı dışı."""
    import math as _m
    L = _m.dist(a, b); n = max(2, int(L/adim))
    ux, uy = (b[0]-a[0])/L, (b[1]-a[1])/L
    dizi = []
    for i in range(n+1):
        s = i*L/n; p = Point(a[0]+ux*s, a[1]+uy*s)
        no = None
        for ad, mno, g in _MAHAL_GEOM:
            if g.contains(p): no = mno; break
        if dizi and dizi[-1][0] == no: dizi[-1][2] = s
        else: dizi.append([no, s, s])
    return [(d[0], round(d[1], 3), round(d[2], 3)) for d in dizi if d[2]-d[1] > 0.015]

# kesit bakış yönü: kesit düzleminin hangi tarafındaki hacim görünür (+1 / −1)
KESIT_BAKIS = {"A-A": +1, "B-B": -1}
SALON_MAHAL = {MAHAL_NO[z[0]] for z in ZONES}     # 101–104: aralarında fiziksel bölme YOK

def kesit_uzunluk(ad):
    a, b = KESIT_HATLARI[ad][0], KESIT_HATLARI[ad][1]
    return math.dist(a, b)

# ── İÇ GÖRÜNÜŞLER ──────────────────────────────────────────────────────────────
# kod, başlık, genişlik_m, yükseklik_m (yapısal), tavan_kot, [öğeler]
# öğe: (tip, x_bas, x_son, z_alt, z_ust, etiket)
IC_GORUNUS = [
 ("G-01","GİRİŞ VE BANKO DUVARI — 101'den batıya bakış", 5.60, 3.20, 2.75, [
   ("cam",   0.20, 5.40, 0.00, 2.40, "Mevcut cephe vitrini P01 — alt 1,20 m buzlu folyo"),
   ("dolgu", 0.20, 5.40, 0.00, 1.20, "Buzlu folyo bandı"),
   ("kapi",  1.90, 3.50, 0.00, 2.40, "K01 çift kanat cam giriş kapısı — dışa açılır"),
   ("mobilya",4.20, 5.40, 0.00, 1.10, "Banko — 120×60 cm, lake MDF + kompakt lamine tezgâh"),
   ("levha", 0.40, 1.30, 1.60, 2.10, "Tesis tabelası ve çalışma saatleri"),
   ("tavan", 0.00, 5.60, 2.75, 2.75, "T2 alçıpan asma tavan +2,75"),
 ]),
 ("G-02","ARENA GÜNEY DUVARI — 102'den güneye bakış", 5.02, 3.20, 3.20, [
   ("giydirme",0.00, 5.02, 0.00, 3.20, "D4 akustik giydirme — mevcut duvardan bağımsız karkas, 50 mm taşyünü"),
   ("ayna",  0.10, 4.90, 0.30, 2.30, "D6 ayna duvarı 4,80×2,00 m — 6 mm, arka yüz güvenlik filmli"),
   ("ekipman",0.00, 2.03, 0.00, 1.45, "F1 — koşu bandı (245×74 cm), duvardan 60 cm serbest"),
   ("ekipman",2.18, 4.63, 0.00, 1.45, "F2 — koşu bandı (245×74 cm)"),
   ("supurgelik",0.00, 5.02, 0.00, 0.10, "S1 kauçuk süpürgelik 100 mm"),
   ("levha", 4.25, 4.90, 2.45, 2.90, "«Ağırlık düşürmek yasaktır» uyarı levhası"),
   ("tavan", 0.00, 5.02, 3.20, 3.20, "T1 açık tavan +3,20 — siyah boyalı, akustik baffle"),
 ]),
 ("G-03","SOYUNMA BLOĞU CEPHESİ — salondan doğuya bakış", 8.05, 3.20, 3.20, [
   ("duvar", 0.00, 8.05, 0.00, 3.20, "D2 alçıpan bölme — salon yüzü saten + mat boya"),
   ("kapi",  2.50, 3.40, 0.00, 2.10, "K04 kadın soyunma kapısı 90×210 — alt menfez 150 cm²"),
   ("kapi",  6.22, 7.12, 0.00, 2.10, "K03 erkek soyunma kapısı 90×210 — alt menfez 150 cm²"),
   ("levha", 2.70, 3.20, 2.25, 2.60, "Piktogram — KADIN"),
   ("levha", 6.42, 6.92, 2.25, 2.60, "Piktogram — ERKEK"),
   ("ekipman",3.90, 5.45, 0.00, 0.95, "D2 — dambıl rafı / sehpa (duvar önü, 155×39 cm)"),
   ("supurgelik",0.00, 8.05, 0.00, 0.10, "S1 kauçuk süpürgelik 100 mm"),
   ("tavan", 0.00, 8.05, 3.20, 3.20, "T1 açık tavan +3,20 — bölme tavan üstünden döşemeye devam eder"),
 ]),
 ("G-04","ERKEK SOYUNMA İÇ GÖRÜNÜŞ — 105'ten kuzeye bakış", 2.60, 3.20, 2.60, [
   ("duvar", 0.00, 2.60, 0.00, 2.60, "D2 / D3 alçıpan — saten + mat boya"),
   ("mobilya",0.10, 1.70, 0.00, 1.80, "8 gözlü soyunma dolabı 160×45×180 cm — laminat, havalandırma delikli"),
   ("mobilya",1.85, 2.50, 0.42, 0.45, "Bank 160×35 cm, ahşap latalı, duvara konsol bağlantılı"),
   ("ayna",  1.85, 2.45, 0.90, 2.00, "Boy aynası 60×110 cm — güvenlik filmli"),
   ("askilik",1.80, 2.55, 1.70, 1.75, "Paslanmaz askılık — 5 kancalı"),
   ("supurgelik",0.00, 2.60, 0.00, 0.08, "S4 porselen süpürgelik 80 mm"),
   ("tavan", 0.00, 2.60, 2.60, 2.60, "T4 alçıpan asma tavan +2,60"),
 ]),
]

# ── İMALAT DETAYLARI (1:10) ────────────────────────────────────────────────────
# kod, başlık, tip, veri, notlar[]
DETAYLAR = [
 ("D-01","Z1 ZEMİN KATMAN DETAYI — arena · serbest ağırlık","katman","Z1",
  ["Kauçuk karo çeperde 5 mm genleşme boşluğu ile biter; boşluk süpürgelik altında kalır.",
   "Titreşim matı duvara 50 mm yukarı dönerek yüzer döşeme teşkil eder (yan geçiş sesi kesilir).",
   "Karo altı kuru uygulamadır — yapıştırıcı kullanılmaz, sökülüp değiştirilebilir."]),
 ("D-02","Z4 ISLAK HACİM ZEMİN VE DUVAR BİRLEŞİMİ","katman","Z4",
  ["Su yalıtımı duvarda en az 300 mm, duş kabininde 2000 mm yukarı döner.",
   "Zemin-duvar köşesinde 120 mm elastik su yalıtım bandı, yalıtımın iki katı arasına gömülür.",
   "Seramik derzi çimento esaslı (CG2 WA); köşe derzleri silikon (sınıf 25LM, küf önleyici)."]),
 ("D-03","Z3 / Z1 ZEMİN KOT VE MALZEME GEÇİŞ DETAYI","gecis",None,
  ["Bitmiş zemin kotları eşittir (±0,00) — eşik veya rampa oluşmaz, tökezleme riski yoktur.",
   "Geçişte 40 mm alüminyum düz geçiş profili; kauçuk tarafta 5 mm genleşme boşluğu bırakılır.",
   "Tesviye şapı kalınlıkları farklıdır (Z1: 3 mm · Z2: 30 mm · Z3: 42 mm · Z5: 38 mm)."]),
 ("D-04","D2 ALÇIPAN BÖLME — YATAY KESİT VE KÖŞE","duvar","D2",
  ["C profiller @400 mm; kapı kenarlarında ve 3,0 m'den uzun duvarlarda kutu profil takviye.",
   "Alçıpan derzleri iki yüzde şaşırtmalı; ikinci kat ilk katla 600 mm kaydırılır.",
   "Ağır asma yük (ayna, dolap, TV) için karkas içine 18 mm kontraplak takviye gömülür."]),
 ("D-05","D3 ISLAK BÖLME + DUŞ SÜZGEÇ VE EĞİM DETAYI","islak",None,
  ["Duş zemini süzgeğe %1,5 eğimli; süzgeç 100×100 mm paslanmaz, kokulu sifon (50 mm su tutuşlu).",
   "Süzgeç flanşı su yalıtımının iki katı arasına sıkıştırılır — sızdırmazlık burada sağlanır.",
   "U tabanlık profil butil bant üzerine oturur; alçıpan alt kenarı bitmiş zeminden 10 mm yukarıda."]),
 ("D-06","T2 / T3 ASMA TAVAN KENAR VE REVİZYON KAPAĞI","tavan",None,
  ["Duvar birleşiminde 10 mm gölge derzi — farklı oturma nedeniyle çatlamayı önler.",
   "Askı @900 mm; kanal, boru veya armatür ağırlığı alçıpan karkasına asılmaz, ayrı askılanır.",
   "Her ıslak hacimde 300×300 mm revizyon kapağı; vana ve klima drenaj bağlantısı altında."]),
 ("D-07","Z6 RING PLATFORMU KENAR DETAYI","katman","Z6",
  ["Platform ekipman üreticisinin montaj talimatına tabidir; bu detay çevre bitişini tanımlar.",
   "Kenarda 100 mm kauçuk kenar bandı + sarı-siyah ikaz şeridi (kot farkı 30 cm).",
   "Platform altı boşluğu havalandırmalı bırakılır, temizlik için 2 gözde sökülebilir kapak."]),
 ("D-08","D6 AYNA MONTAJ DETAYI","ayna",None,
  ["Ayna alt kotu +0,30 (süpürgelik üstü), üst kotu +2,30.",
   "Arka yüzde güvenlik filmi (EN 12600 sınıf 2B2) ZORUNLU — serbest ağırlık alanında kırılma riski.",
   "Yapıştırma + alt ve üstte alüminyum mekanik emniyet profili; ayna arkası nemsiz kalmalı."]),
]

# ── YANGIN / TAHLİYE VERİSİ ────────────────────────────────────────────────────
CIKISLAR = [("Ç1", (0.24, 4.30), 1.60, "ANA ÇIKIŞ — batı cephe"),
            ("Ç2", (3.35, 0.10), 1.00, "ACİL ÇIKIŞ — güneybatı cephe")]
YANGIN_EKIPMAN = [
 ("YD1", (0.95, 7.55), "Yangın dolabı — 30 m hortum, TS EN 671-2 (opsiyon: GSİM talebine göre)"),
 ("YT1", (0.70, 3.90), "6 kg ABC kuru kimyevi tozlu yangın söndürücü — çıkış yanında"),
 ("YT2", (8.00, 9.20), "6 kg ABC kuru kimyevi tozlu yangın söndürücü — dinlenme/soyunma yakını"),
 ("YT3", (6.60, 0.55), "6 kg ABC kuru kimyevi tozlu yangın söndürücü — acil çıkış yanında"),
]
TAHLIYE_YOL = [  # (mahal_no, [nokta...], çıkış kodu) — kapılardan geçer, ekipmanın etrafından dolaşır
 ("104", [(8.05,11.10),(7.05,9.70),(6.55,8.88),(5.00,8.10),(2.60,6.50),(0.45,4.35)], "Ç1"),
 ("103", [(6.40,7.45),(4.60,7.30),(2.40,6.30),(0.45,4.35)], "Ç1"),
 ("102", [(5.30,1.62),(4.30,0.95),(3.40,0.40)], "Ç2"),
 ("105", [(9.80,6.30),(8.95,7.05),(8.40,7.28),(6.80,7.55),(4.20,6.70),(2.00,5.70),(0.45,4.35)], "Ç1"),
 ("108", [(10.10,3.30),(9.35,3.38),(8.60,3.50),(7.85,5.30),(7.55,7.00),(5.00,7.50),(2.20,6.10),(0.45,4.35)], "Ç1"),
]
def tahliye_uzunluk(yol): return round(sum(math.dist(yol[i],yol[i+1]) for i in range(len(yol)-1)),1)
TAHLIYE_MAX = max(tahliye_uzunluk(y[1]) for y in TAHLIYE_YOL)
TAHLIYE_SINIR = 45.0   # BYKHY Tablo 5.5 — tek yönde kaçış olmayan, 2 çıkışlı tesis

# ── MİMARİ GENEL NOTLAR ────────────────────────────────────────────────────────
MIMARI_NOTLAR = [
 "Tüm ölçüler metre (m), kaplama katman kalınlıkları milimetre (mm) cinsindendir. Ölçü okunur, çizimden ölçü alınmaz.",
 "±0,00 kotu bitmiş zemin kotudur. Mevcut şap üst kotu −0,053 VARSAYILMIŞTIR; söküm sonrası yerinde ölçülüp tüm tesviye şapı kalınlıkları revize edilecektir.",
 "Taşıyıcı sistemde (kolon, perde, kiriş, döşeme) hiçbir kesme, delme veya yük artışı yapılmayacaktır. Gerekli hâllerde statik proje müellifinden yazılı görüş alınacaktır.",
 "Mevcut duvar kalınlıkları ve tavan yüksekliği VARSAYIMDIR; rölöve sonrası mahal listesi ve tavan kotları güncellenecektir.",
 "Alçıpan imalatlarda profil aralığı 400 mm'yi geçmeyecek; 3,0 m üzeri duvarlarda ve kapı kenarlarında kutu profil takviyesi yapılacaktır.",
 "Islak hacimlerde su yalıtımı EN 14891'e uygun, çimento esaslı 2 bileşenli, 2 kat; tüm köşe ve boru geçişlerinde bant ve manşet kullanılacaktır.",
 "Islak hacim imalatı bitiminde, seramik öncesi 24 saatlik su tutma (taşkın) testi yapılacak ve tutanağa bağlanacaktır.",
 "Kauçuk zemin, üst kat konut VARSAYIMI nedeniyle titreşim matı ile yüzer döşeme olarak teşkil edilecektir; mat duvara 50 mm yukarı dönecektir.",
 "Tüm cam yüzeylerde (kapı, ayna, vitrin) temperli veya lamine güvenlik camı kullanılacaktır (EN 12600).",
 "Kaçış kapıları kaçış yönünde açılacak, üzerinde kilit veya sürgü bulunmayacak, panik donanımlı olacaktır (EN 1125).",
 "Asma tavan üstündeki mekanik ve elektrik tesisatı bağımsız askılanacak; ağırlık alçıpan karkasına aktarılmayacaktır.",
 "Boya, seramik ve kauçuk renk/desen seçimleri numune onayına tabidir; onaysız imalat bedeli yükleniciye aittir.",
 "Bu set mimari uygulama setidir; ruhsat için proje müellifi mimar tarafından imzalanmış 1/50 onaylı takım ayrıca düzenlenecektir.",
]
