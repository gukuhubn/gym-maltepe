# -*- coding: utf-8 -*-
"""METRAJ MOTORU — geometriden imalat miktarlarını türetir.

Türk müteahhitlik uygulamasındaki metraj cetveli mantığıyla çalışır:
her satır (en × boy × yükseklik × adet) ile hesaplanır, kapı/pencere
boşlukları MİNHA olarak eksi satır hâlinde girilir, kısmi ve sayfa yekünü alınır.

Tüm ölçüler tools/proj.py geometrisinden gelir — tek kaynak.
"""
import sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union
import proj as P

IC = unary_union([P.SALON, P.ERKEK, P.KADIN])

# ── kapı boşlukları (minha için) ───────────────────────────────────────────────
KAPI_MINHA = {k[0]: (k[3]/1000.0, k[4]/1000.0) for k in P.KAPI_LISTESI}   # kod: (en, yük) m

def _mahal_kapilari(mno):
    m = P._MAHAL_BILGI[mno]
    return [k.strip() for k in m[8].split("·") if k.strip().startswith("K")]

# ── mahal çevre uzunlukları ───────────────────────────────────────────────────
_GEOM = {mno: g for _ad, mno, g in P._MAHAL_GEOM}
CEVRE = {mno: round(g.exterior.length, 2) for mno, g in _GEOM.items()}
ALAN  = {m[0]: m[2] for m in P.MAHAL_LISTESI}
TAVAN_KOTU = {m[0]: m[7] for m in P.MAHAL_LISTESI}

# ── satır yapısı ──────────────────────────────────────────────────────────────
# (aciklama, birim, adet, en, boy, yukseklik)  →  miktar = adet*en*boy*yuk (0 olanlar atlanır)
def _mik(adet, en, boy, yuk):
    v = adet
    for x in (en, boy, yuk):
        if x not in (None, 0): v *= x
    return v

class Cetvel:
    """Tek bir poz için metraj cetveli."""
    def __init__(self, poz, ad, birim, mahal=""):
        self.poz, self.ad, self.birim, self.mahal = poz, ad, birim, mahal
        self.satir = []            # (aciklama, adet, en, boy, yuk, miktar, isaret)
    def ekle(self, aciklama, adet=1, en=None, boy=None, yuk=None):
        m = _mik(adet, en, boy, yuk)
        self.satir.append((aciklama, adet, en, boy, yuk, round(m, 3), "+"))
        return self
    def minha(self, aciklama, adet=1, en=None, boy=None, yuk=None):
        m = _mik(adet, en, boy, yuk)
        self.satir.append((aciklama, adet, en, boy, yuk, round(-m, 3), "−"))
        return self
    @property
    def toplanan(self): return round(sum(s[5] for s in self.satir if s[5] > 0), 2)
    @property
    def cikarilan(self): return round(-sum(s[5] for s in self.satir if s[5] < 0), 2)
    @property
    def miktar(self): return round(self.toplanan - self.cikarilan, 2)

CETVEL = []
def yeni(poz, ad, birim, mahal=""):
    c = Cetvel(poz, ad, birim, mahal); CETVEL.append(c); return c

# ═══════════════════════════════════════════════════════════════════════════════
#  A · YIKIM VE SÖKÜM
# ═══════════════════════════════════════════════════════════════════════════════
def _tum_mahal(c, filtre=None, ek_duvar_payi=True):
    for m in P.MAHAL_LISTESI:
        if filtre and not filtre(m): continue
        c.satir.append((f"{m[0]} {m[1]}", 1, None, None, None, m[2], "+"))
    if ek_duvar_payi and filtre is None:
        c.satir.append(("İç bölme duvar payı (mevcut hâlde tek hacim)", 1, None, None, None,
                        P.MAHAL_DUVAR_PAYI, "+"))
    return c

c = _tum_mahal(yeni("A.1.1", "Mevcut zemin kaplaması sökümü ve altlık temizliği",
                    "m²", "Tüm mahaller"))
c = _tum_mahal(yeni("A.1.2", "Mevcut asma tavan ve aydınlatma armatürü sökümü",
                    "m²", "Tüm mahaller"))

c = yeni("A.1.3", "Islak hacimde mevcut şap kırımı (ort. 70 mm, tesisat boşluğu)", "m²", "106·107·109·110")
for m in P.MAHAL_LISTESI:
    if m[9]: c.satir.append((f"{m[0]} {m[1]}", 1, None, None, None, m[2], "+"))

c = yeni("A.1.4", "Mevcut sıva üstü elektrik tesisatı ve tablosu sökümü", "tk", "Tüm mahaller")
c.ekle("Mevcut mağaza tesisatı — komple", 1)

c = yeni("A.1.5", "Mevcut mağaza rafı, teşhir ünitesi ve mobilya sökümü", "tk", "101–104")
c.ekle("Mağaza demirbaşı — komple söküm ve tasnif", 1)

c = yeni("A.1.6", "Moloz çuvallama, yatay-düşey taşıma ve döküm sahasına nakli", "m³", "Tüm mahaller")
c.ekle("Zemin kaplaması sökümü molozu (103,78 m² × 0,05 m)", 1, P.A["ic_toplam"], 0.05)
c.ekle("Asma tavan sökümü molozu (103,78 m² × 0,03 m)", 1, P.A["ic_toplam"], 0.03)
c.ekle("Islak hacim şap kırımı molozu (16,73 m² × 0,07 m)", 1, P.A["islak_toplam"], 0.07)
c.ekle("Mağaza demirbaşı ve ambalaj (götürü)", 1, 4.0)

# ═══════════════════════════════════════════════════════════════════════════════
#  B · BÖLME DUVAR VE ALÇIPAN İŞLERİ
# ═══════════════════════════════════════════════════════════════════════════════
H_BOLME = P.KOT_YAPISAL_TAVAN          # bölmeler döşemeye kadar: 3,20 m

# D2 — soyunma bloğu cephesi (salona bakan, kuru hacim)
c = yeni("B.1.1", "D2 alçıpan bölme — 50 mm C profil @400 + 40 mm taşyünü + "
                  "her yüz 2×12,5 mm A tipi alçıpan (toplam 100 mm)", "m²", "105 · 108 cephe")
c.ekle("Erkek soyunma bloğu salon cephesi", 1, 3.70, None, H_BOLME)
c.ekle("Kadın soyunma bloğu salon cephesi", 1, 4.22, None, H_BOLME)
c.ekle("Erkek/kadın blok arası ayırıcı bölme", 1, 2.15, None, H_BOLME)
for k in ("K03", "K04"):
    c.minha(f"{k} kapı boşluğu minha", 1, *KAPI_MINHA[k])

# D3 — ıslak hacim bölmesi
c = yeni("B.1.2", "D3 alçıpan bölme — ıslak yüzde 2×12,5 mm H2 (yeşil) alçıpan, "
                  "kuru yüzde 2×12,5 mm A tipi (toplam 100 mm)", "m²", "106·107·109·110")
for ad, d in P.ISLAK.items():
    for n, lbl in (("dus", "duş"), ("wc", "WC")):
        u = round(d[n].exterior.length, 2)
        c.ekle(f"{ad.capitalize()} {lbl} bölme duvarı (çevre {u} m)", 1, u, None, H_BOLME)
for k in ("K05", "K06", "K07", "K08"):
    c.minha(f"{k} kapı boşluğu minha", 1, *KAPI_MINHA[k])

# D4 — akustik giydirme
c = yeni("B.1.3", "D4 akustik giydirme — bağımsız C profil karkas + 50 mm taşyünü + "
                  "12,5 mm akustik + 12,5 mm A tipi alçıpan (toplam 95 mm)", "m²", "102 güney çeper")
c.ekle("Arena güney duvarı (3,24 → 8,92)", 1, 5.68, None, H_BOLME)
c.minha("K02 acil çıkış doğraması minha", 1, *KAPI_MINHA["K02"])

# taşyünü ve karkas ayrıştırması (alt pozlar)
c = yeni("B.1.4", "Taşyünü dolgu 40 mm / 50 kg/m³ — D2 ve D3 bölmelerinde", "m²", "Bölme duvarlar")
c.ekle("D2 bölme alanı", 1, 1)      # miktar aşağıda bağlanır
CETVEL.remove(c)

# ═══════════════════════════════════════════════════════════════════════════════
#  C · ŞAP VE TESVİYE İŞLERİ
# ═══════════════════════════════════════════════════════════════════════════════
for poz, zt, ad in (("C.1.1", "Z1", "Çimento esaslı kendinden yayılan tesviye şapı 3 mm"),
                    ("C.1.2", "Z2", "Çimento esaslı tesviye şapı 30 mm"),
                    ("C.1.3", "Z3", "Çimento esaslı tesviye şapı 42 mm"),
                    ("C.1.4", "Z5", "Çimento esaslı tesviye şapı 38 mm")):
    c = yeni(poz, f"{ad} — {zt} bölgesi (bitmiş kot ±0,00 eşitlemesi)", "m²", "")
    mm_ = [m for m in P.MAHAL_LISTESI if m[3] == zt]
    c.mahal = " · ".join(m[0] for m in mm_)
    for m in mm_:
        c.satir.append((f"{m[0]} {m[1]}", 1, None, None, None, m[2], "+"))

c = yeni("C.1.5", "Islak hacim tesisat şapı + süzgeğe %1,5 eğimli eğim şapı (ort. 40 mm)",
         "m²", "106·107·109·110")
for m in P.MAHAL_LISTESI:
    if m[9]: c.satir.append((f"{m[0]} {m[1]}", 1, None, None, None, m[2], "+"))

# ═══════════════════════════════════════════════════════════════════════════════
#  D · ZEMİN KAPLAMA İŞLERİ
# ═══════════════════════════════════════════════════════════════════════════════
_ZEM_AD = {z[0]: z[1] for z in P.ZEMIN_TIPLERI}
_KAPLAMA_AD = {
 "Z1": "Granül kauçuk karo 1000×1000 mm, 40 mm, EPDM %10 taneli, Shore A 55±5 "
       "(EN 14041 · Bfl-s1) — puzzle kilitli kuru derz, çeperde 5 mm genleşme boşluğu",
 "Z2": "Granül kauçuk karo 1000×1000 mm, 20 mm, Shore A 60 (EN 14041 · Bfl-s1) — "
       "puzzle kilitli kuru derz",
 "Z3": "SPC klik LVT 5 mm, 0,55 mm aşınma tabakası (EN ISO 10874 sınıf 33 / AC5) + "
       "2 mm IXPE akustik şilte — çeperde 8 mm genleşme boşluğu",
 "Z4": "Porselen seramik 300×300 mm, R11 / B kaymazlık (EN 16165) + C2TE S1 yapıştırıcı",
 "Z5": "Porselen seramik 600×600 mm, R10, rektifiye, 2 mm derz (EN 14411 BIa) + "
       "C2TE yapıştırıcı",
}
for poz, zt in (("D.1.1", "Z1"), ("D.1.2", "Z2"), ("D.1.3", "Z3"),
                ("D.1.4", "Z4"), ("D.1.5", "Z5")):
    mm_ = [m for m in P.MAHAL_LISTESI if m[3] == zt]
    if not mm_: continue
    c = yeni(poz, f"{zt} — {_KAPLAMA_AD[zt]}", "m²", " · ".join(m[0] for m in mm_))
    for m in mm_:
        c.satir.append((f"{m[0]} {m[1]}", 1, None, None, None, m[2], "+"))

c = yeni("D.1.6", "Kauçuk titreşim yalıtım matı 10 mm (SBR granül 700 kg/m³) — "
                  "duvara 50 mm yukarı dönüşlü yüzer döşeme", "m²", "102")
c.satir.append(("102 ARENA · SERBEST AĞIRLIK", 1, None, None, None, ALAN["102"], "+"))

# süpürgelik — mahal çevresi eksi kapı genişlikleri
_SUP = {"S1": [], "S2": [], "S3": [], "S4": []}
for m in P.MAHAL_LISTESI: _SUP[m[4]].append(m)
_SUP_AD = {s[0]: s[1] for s in P.SUPURGELIK}
for poz, sk in (("D.2.1", "S1"), ("D.2.2", "S2"), ("D.2.4", "S4")):
    mm_ = _SUP[sk]
    c = yeni(poz, _SUP_AD[sk], "mt", " · ".join(m[0] for m in mm_))
    for m in mm_:
        c.ekle(f"{m[0]} {m[1]} — mahal çevresi", 1, CEVRE[m[0]])
        for k in _mahal_kapilari(m[0]):
            if k in KAPI_MINHA:
                c.minha(f"{k} kapı genişliği minha", 1, KAPI_MINHA[k][0])
    # salon bölgeleri arasında fiziksel duvar yok → ortak sınırlar süpürgeliksiz
    if sk in ("S1", "S2"):
        c.minha("101–104 bölge sınırları (fiziksel duvar yok) — yaklaşık", 1, 12.60)

# ═══════════════════════════════════════════════════════════════════════════════
#  E · SERAMİK VE SU YALITIMI
# ═══════════════════════════════════════════════════════════════════════════════
c = yeni("E.1.1", "D5 duvar seramiği 300×600 mm, rektifiye — duş kabininde tavana kadar",
         "m²", "106 · 109")
for ad, d in P.ISLAK.items():
    u = round(d["dus"].exterior.length, 2)
    c.ekle(f"{ad.capitalize()} duş — çevre {u} m × tavan kotu 2,40 m", 1, u, None, 2.40)
for k in ("K07", "K08"):
    c.minha(f"{k} duş kapağı boşluğu minha", 1, *KAPI_MINHA[k])

c = yeni("E.1.2", "D5 duvar seramiği 300×600 mm — WC'de h = 1,60 m", "m²", "107 · 110")
for ad, d in P.ISLAK.items():
    u = round(d["wc"].exterior.length, 2)
    c.ekle(f"{ad.capitalize()} WC — çevre {u} m × h 1,60 m", 1, u, None, 1.60)
for k in ("K05", "K06"):
    c.minha(f"{k} kapı boşluğu minha (h 1,60 m'ye kadar)", 1, KAPI_MINHA[k][0], None, 1.60)

c = yeni("E.1.3", "Çimento esaslı 2 bileşenli su yalıtımı, 2 kat (EN 14891) — zemin",
         "m²", "106·107·109·110")
for m in P.MAHAL_LISTESI:
    if m[9]: c.satir.append((f"{m[0]} {m[1]} zemin", 1, None, None, None, m[2], "+"))

c = yeni("E.1.4", "Çimento esaslı su yalıtımı, 2 kat — duvarda dönüş "
                  "(duşta 2,00 m, WC'de 0,30 m)", "m²", "106·107·109·110")
for ad, d in P.ISLAK.items():
    c.ekle(f"{ad.capitalize()} duş — çevre × 2,00 m", 1, round(d["dus"].exterior.length, 2), None, 2.00)
    c.ekle(f"{ad.capitalize()} WC — çevre × 0,30 m", 1, round(d["wc"].exterior.length, 2), None, 0.30)

c = yeni("E.1.5", "Elastik su yalıtım bandı 120 mm — zemin-duvar birleşimi ve köşeler",
         "mt", "106·107·109·110")
for ad, d in P.ISLAK.items():
    for n, lbl in (("dus", "duş"), ("wc", "WC")):
        c.ekle(f"{ad.capitalize()} {lbl} — zemin-duvar birleşim çevresi",
               1, round(d[n].exterior.length, 2))
c.ekle("Düşey köşeler ve boru geçişleri (4 hacim × 4 köşe × 2,40 m)", 32, 1.0)

# ═══════════════════════════════════════════════════════════════════════════════
#  F · ASMA TAVAN VE BOYA
# ═══════════════════════════════════════════════════════════════════════════════
for poz, tt in (("F.1.1", "T2"), ("F.1.2", "T4"), ("F.1.3", "T3")):
    mm_ = [m for m in P.MAHAL_LISTESI if m[6] == tt]
    ad = [t[1] for t in P.TAVAN_TIPLERI if t[0] == tt][0]
    c = yeni(poz, f"{tt} {ad} — kot +{('%.2f' % P.TAVAN_KOT[tt]).replace('.', ',')}",
             "m²", " · ".join(m[0] for m in mm_))
    for m in mm_:
        c.satir.append((f"{m[0]} {m[1]}", 1, None, None, None, m[2], "+"))

c = yeni("F.1.4", "T1 açık tavan — döşeme altı raspa, temizlik ve 2 kat siyah akrilik boya "
                  "(kanal ve askılar dâhil)", "m²", "102 · 103")
for m in P.MAHAL_LISTESI:
    if m[6] == "T1": c.satir.append((f"{m[0]} {m[1]}", 1, None, None, None, m[2], "+"))

c = yeni("F.1.5", "Asma tavan revizyon kapağı 300×300 mm, menteşeli", "ad", "106·107·109·110")
c.ekle("Her ıslak hacimde 1 adet", 4)

c = yeni("F.1.6", "Akustik taşyünü asma baffle 1200×600×50 mm (αw ≈ 0,90)", "ad", "102")
c.ekle("Arena üzerinde", 12)

# duvar boyası — mahal çevresi × tavan kotu, ıslak seramik alanları minha
c = yeni("F.2.1", "Saten alçı perdah 2 kat + akrilik astar + su bazlı silikonlu mat "
                  "iç cephe boyası 2 kat (sınıf 1 yıkanabilir)", "m²", "101–105 · 108")
for m in P.MAHAL_LISTESI:
    if m[9]: continue
    c.ekle(f"{m[0]} {m[1]} — çevre {CEVRE[m[0]]} m × tavan {m[7]:.2f} m".replace(".", ","),
           1, CEVRE[m[0]], None, m[7])
    for k in _mahal_kapilari(m[0]):
        if k in KAPI_MINHA:
            c.minha(f"{k} kapı boşluğu minha", 1, *KAPI_MINHA[k])
c.minha("P01 · P02 cephe vitrini minha (5,62 + 2,02) × 2,40", 1, 7.64, None, 2.40)
c.minha("D6 ayna duvarı alanı minha", 1, 4.80, None, 2.00)

c = yeni("F.2.2", "Su bazlı küf önleyici yarı mat banyo boyası, 2 kat — seramik üstü kalan yüzey",
         "m²", "107 · 110")
for ad, d in P.ISLAK.items():
    u = round(d["wc"].exterior.length, 2)
    c.ekle(f"{ad.capitalize()} WC — çevre {u} m × (2,40 − 1,60) m", 1, u, None, 0.80)

c = yeni("F.2.3", "Asma tavan alçıpan yüzeyi — derz bandı + saten alçı + astar + 2 kat mat boya",
         "m²", "101 · 104 · 105 · 108")
for m in P.MAHAL_LISTESI:
    if m[6] in ("T2", "T4"):
        c.satir.append((f"{m[0]} {m[1]}", 1, None, None, None, m[2], "+"))

# ═══════════════════════════════════════════════════════════════════════════════
#  G · DOĞRAMA, CAM VE AYNA
# ═══════════════════════════════════════════════════════════════════════════════
for i, k in enumerate(P.KAPI_LISTESI):
    c = yeni(f"G.1.{i+1}", f"{k[0]} — {k[5]}; {k[6]} ({k[3]}×{k[4]} mm)", "ad", k[2])
    c.ekle(f"{k[7]} · {k[8]}", k[1])

c = yeni("G.2.1", "D6 ayna duvarı — 18 mm su kontraplağı altlık + 6 mm güvenlik filmli ayna, "
                  "alt/üst alüminyum mekanik emniyet profilli", "m²", "102")
c.ekle("Arena güney duvarı — alt kot +0,30 / üst kot +2,30", 1, 4.80, None, 2.00)

c = yeni("G.2.2", "Boy aynası 60×110 cm, güvenlik filmli", "ad", "105 · 108")
c.ekle("Soyunma mahalleri", 2)

c = yeni("G.2.3", "Cephe vitrininde buzlu folyo (alt 1,20 m) + güneş kontrol filmi", "m²", "101")
c.ekle("P01 batı cephe vitrini — buzlu bant", 1, 5.62, None, 1.20)
c.ekle("P02 GB cephe vitrini — buzlu bant", 1, 2.02, None, 1.20)
c.ekle("P01 + P02 üst bant güneş kontrol filmi", 1, 7.64, None, 1.20)

# ═══════════════════════════════════════════════════════════════════════════════
#  H · SABİT MOBİLYA VE DONANIM
# ═══════════════════════════════════════════════════════════════════════════════
c = yeni("H.1.1", "Resepsiyon bankosu 120×60×110 cm — lake MDF gövde + kompakt lamine tezgâh, "
                  "gömme kuvvet ve veri kutulu", "ad", "101")
c.ekle("Giriş bankosu", 1)
c = yeni("H.1.2", "8 gözlü soyunma dolabı 160×45×180 cm — laminat, havalandırma delikli, kilitli",
         "ad", "105 · 108")
c.ekle("Erkek ve kadın soyunma", 2)
c = yeni("H.1.3", "Soyunma bankı 160×35 cm — ahşap latalı, duvara konsol bağlantılı", "ad", "105 · 108")
c.ekle("Erkek ve kadın soyunma", 2)
c = yeni("H.1.4", "Paslanmaz askılık, 5 kancalı", "ad", "105 · 108")
c.ekle("Erkek ve kadın soyunma", 2)
c = yeni("H.1.5", "Depo / teknik dolap — banko arkası niş, havalandırma menfezli", "ad", "101")
c.ekle("NVR ve router dolabı (K09)", 1)

# ═══════════════════════════════════════════════════════════════════════════════
#  I · YANGIN GÜVENLİK VE İŞARETLEME
# ═══════════════════════════════════════════════════════════════════════════════
c = yeni("I.1.1", "6 kg ABC kuru kimyevi tozlu yangın söndürücü — askı aparatı ve levhası ile",
         "ad", "101 · 102 · 104")
c.ekle("Çıkış yanı, dinlenme/soyunma yakını, acil çıkış yanı", 3)
c = yeni("I.1.2", "Yangın dolabı — 30 m hortum, TS EN 671-2 (GSİM talebine bağlı opsiyon)",
         "ad", "101")
c.ekle("Ana çıkış yanı", 1)
c = yeni("I.1.3", "Fotolüminesan yönlendirme ve yasak levhaları", "ad", "Tüm mahaller")
c.ekle("Çıkış yönlendirme", 3); c.ekle("Piktogram (erkek/kadın)", 2)
c.ekle("«Ağırlık düşürmek yasaktır» uyarı levhası", 1)
c.ekle("Kapasite ve çalışma saatleri levhası", 1)

# ═══════════════════════════════════════════════════════════════════════════════
#  J · GENEL GİDERLER
# ═══════════════════════════════════════════════════════════════════════════════
c = yeni("J.1.1", "İnce ve kaba temizlik, teslim öncesi detay temizliği", "m²", "Tüm mahaller")
c.ekle("Net iç kullanım alanı", 1, P.A["ic_toplam"])
c = yeni("J.1.2", "Şantiye kurulumu, koruma örtüleri, hoarding ve güvenlik", "tk", "Tüm mahaller")
c.ekle("Götürü", 1)
c = yeni("J.1.3", "Nakliyeler (malzeme sevkiyatı, vinç/asansör kullanımı)", "tk", "Tüm mahaller")
c.ekle("Götürü", 1)
c = yeni("J.1.4", "Usta ve düz işçi çalışmaları (poz dışı ilave işler)", "yev", "Tüm mahaller")
c.ekle("Tahmini yevmiye (referans projede usta+düz işçi payı ≈ %6)", 35)

# ── metraj sözlüğü ────────────────────────────────────────────────────────────
M = {c.poz: c for c in CETVEL}
MIKTAR = {c.poz: c.miktar for c in CETVEL}

def ozet():
    return [(c.poz, c.ad, c.birim, c.mahal, c.toplanan, c.cikarilan, c.miktar) for c in CETVEL]

if __name__ == "__main__":
    print(f"{len(CETVEL)} poz için metraj cetveli\n")
    grup = None
    for c in CETVEL:
        g = c.poz.split(".")[0]
        if g != grup: grup = g; print(f"\n── {g} ──")
        print(f"  {c.poz:8s} {c.ad[:66]:66s} {c.miktar:10.2f} {c.birim:4s}"
              f"  (+{c.toplanan:.2f} / −{c.cikarilan:.2f})")
