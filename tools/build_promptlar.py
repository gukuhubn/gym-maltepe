# -*- coding: utf-8 -*-
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from pathlib import Path
import proj as P
from render_gemini import ORTAK, STIL, KAMERA
D = json.load(open("data/dimensions.json"))
L = ["# RENDER PROMPT SETİ", "",
 f"**{P.PROJE}** · {P.REV} · {P.TARIH}", "",
 "Bu dosyadaki görseller Three.js kütle modelinden alınan PNG'ler **image-to-image** girdisi",
 "yapılarak üretilmiştir; böylece geometri plana sadık kalır ve model halüsinasyon yapmaz.",
 "Aynı çıktıyı harici bir modelde tekrar üretmek isterseniz:", "",
 "1. `output/render/` altındaki ilgili görseli **veya** `site/index.html`'i tarayıcıda açıp",
 "   `?cam=N&style=X&ui=0` ile aldığınız ekran görüntüsünü referans görsel olarak yükleyin.",
 "2. Aşağıdaki ortak prompt + stil bloğu + kamera cümlesini birleştirip yapıştırın.", "",
 "> Üretilen her görselin altına **“temsilî görsel — imalat ölçüsü değildir”** notu düşülmelidir.",
 "> Marka adı, logo ve okunabilir metin üretilmemelidir.", "",
 "---", "", "## Mekân verisi (prompt'a gömülü)", "",
 "| Parametre | Değer |", "|---|---|",
 f"| Net iç kullanım alanı | {P.A['ic_toplam']:.2f} m² |".replace(".",","),
 f"| Salon | {P.A['salon']:.2f} m² |".replace(".",","),
 f"| Islak hacim (2 blok) | {P.A['islak_toplam']:.2f} m² |".replace(".",","),
 f"| Tavan yüksekliği (varsayım) | {P.V['tavan_h'][0]:.2f} m |".replace(".",","),
 f"| Altıgen arena | {P.HEX_M2:.2f} m² · kenar {P.HEX_S:.2f} m |".replace(".",","),
 f"| Eşzamanlı kapasite | {P.V['kisi_kapasite'][0]} kişi |", "",
 "---", "", "## 1 · ORTAK PROMPT (her görselde aynı)", "", "```", ORTAK, "```", ""]
L += ["---", "", "## 2 · STİL BLOKLARI", ""]
for k, v in STIL.items():
    L += [f"### {D['stiller'][k]['ad']} (`{k}`)", "", "```", v.strip(), "```", ""]
L += ["---", "", "## 3 · KAMERA CÜMLELERİ", ""]
for k in D["kameralar"]:
    L += [f"### {k['baslik']} (`{k['ad']}`)", "",
          f"- Kamera konumu (plan, m): **{k['poz'][0]:.2f}, {k['poz'][2]:.2f}** · göz yüksekliği {k['poz'][1]:.2f} m".replace(".",","),
          f"- Bakış hedefi (plan, m): **{k['hedef'][0]:.2f}, {k['hedef'][2]:.2f}**".replace(".",","),
          f"- Görüş açısı: {k['fov']}°", "", "```", KAMERA[k["ad"]], "```", ""]
L += ["---", "", "## 4 · ÜRETİLEN DOSYALAR", "",
 "| Dosya | Açı | Stil |", "|---|---|---|"]
for k in D["kameralar"]:
    for s in D["stiller"]:
        L.append(f"| `output/render/{k['ad']}_{s}.png` | {k['baslik']} | {D['stiller'][s]['ad']} |")
L += ["", "Kütle modeli PNG'leri: `work/model/` · tek dosya offline model: `output/Gym_Model.html`", "",
 "---", "", "## 5 · GERÇEK ÖNCE / SONRA ÇİFTLERİ (henüz üretilemedi)", "",
 "İşverenden mevcut durum fotoğrafları gelmediği için brief §7.A atlanmıştır. Fotoğraflar geldiğinde:", "",
 "1. Her fotoğrafı image-to-image girdisi yapın.",
 "2. Ortak prompt'a şunu ekleyin: *“Keep the exact camera angle, window and column positions and",
 "   ceiling height of the supplied photograph of the existing furniture shop; replace only the",
 "   fit-out with the gym described below.”*",
 "3. En az üç çift üretin: ① ana salon ② giriş / banko bölgesi ③ soyunma koridoru.", "",
 "Gerçek ÖNCE/SONRA çiftleri, kredi ve ortak görüşmelerinde en ikna edici çıktıdır.", ""]
Path("output/Render_Promptlari.md").write_text("\n".join(L), encoding="utf-8")
print("→ output/Render_Promptlari.md ·", len(L), "satır")
