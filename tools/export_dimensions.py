# -*- coding: utf-8 -*-
"""site/ ve Gym_Model.html icin geometri disa aktarimi -> data/dimensions.json"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
import proj as P

_R3D = {"DİNLENME SALONU":"#8E6039", "GİRİŞ · BANKO · SİRKÜLASYON":"#9C6E45",
        "ARENA · SERBEST AĞIRLIK":"#24282D", "FONKSİYONEL · KARDİYO":"#333A42"}

def ring(g):
    return [[round(x,3), round(y,3)] for x,y in list(g.exterior.coords)[:-1]]

d = {
 "proje": P.PROJE, "rev": P.REV, "tarih": P.TARIH,
 "kaynak": "TRIMODE Alan Dağılımı paftası — renk maskesiyle vektörleştirildi, m² etiketleriyle kalibre (±%3)",
 "tavan_h": P.V["tavan_h"][0],
 "duvar_t": P.V["duvar_kalinlik"][0],
 "alanlar": P.A,
 "kabuk": {"salon": ring(P.SALON), "erkek": ring(P.ERKEK), "kadin": ring(P.KADIN)},
 "bolgeler": [{"ad": z[0], "m2": P.ZON_M2[z[0]], "kaplama": z[2], "kalinlik": z[3],
               "renk": z[4], "renk3d": _R3D[z[0]], "poligon": ring(z[1])} for z in P.ZONES],
 "islak": {k: {n: {"m2": P.ISLAK_M2_DETAY[k][n], "poligon": ring(g)}
               for n, g in v.items() if n != "tum"} for k, v in P.ISLAK.items()},
 "ekipman": [{"kod": k, "ad": a, "poligon": ring(g),
              "h": 1.45 if k=="A" else (1.70 if k in ("B","C") else 0.55)}
             for k, a, g in P.ekipman_poligonlari()],
 "mobilya": [{"ad": a, "poligon": ring(g), "tip": t,
              "h": 1.05 if t=="banko" else (1.85 if t=="dolap" else 0.45)}
             for a, g, t in P.MOBILYA],
 "hex": {"merkez": list(P.EKIPMAN[0][5]), "kenar": round(P.HEX_S,3), "m2": P.HEX_M2},
 "cephe": [[list(a), list(b)] for a, b in P.CEPHE],
 "kapilar": [{"nokta": list(k[0]), "genislik": k[1], "aci": k[2], "etiket": k[3]}
             for k in P.KAPILAR],
 "aydinlatma": [[round(x,2), round(y,2)] for x, y in __import__("draw").aydinlatma_izgara(None)],
 "kameralar": [
   {"ad":"01_giristen_arenaya","baslik":"Girişten arenaya",
    "poz":[1.10,1.70,1.60],"hedef":[7.00,0.95,6.10],"fov":70},
   {"ad":"02_arenadan_soyunmaya","baslik":"Arenadan soyunma bloğuna",
    "poz":[3.20,1.70,6.60],"hedef":[9.35,1.05,4.20],"fov":66},
   {"ad":"03_agirlik_alani","baslik":"Serbest ağırlık alanı",
    "poz":[5.90,1.68,7.90],"hedef":[4.30,0.85,0.80],"fov":72},
   {"ad":"04_banko_karsilama","baslik":"Banko ve karşılama",
    "poz":[8.05,1.65,1.25],"hedef":[1.50,1.00,5.60],"fov":70},
 ],
 "stiller": {
   "endustriyel": {"ad":"Ham endüstriyel","zemin":"#2F343A","duvar":"#D9DCE0",
                   "tavan":"#22262B","aksan":"#B87333","ekipman":"#1F2328","isik":"#FFF1DC"},
   "minimal":     {"ad":"Sıcak minimal","zemin":"#4A5560","duvar":"#F2EDE5",
                   "tavan":"#EFE9E0","aksan":"#C98B4B","ekipman":"#3A4148","isik":"#FFF6E9"},
 },
}
os.makedirs("data", exist_ok=True)
json.dump(d, open("data/dimensions.json","w"), ensure_ascii=False, indent=1)
print("→ data/dimensions.json ·", len(d["ekipman"]), "ekipman ·",
      len(d["aydinlatma"]), "armatür ·", len(d["bolgeler"]), "bölge")
