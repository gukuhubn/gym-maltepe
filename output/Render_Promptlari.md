# RENDER PROMPT SETİ

**MALTEPE / İDEALTEPE — MOBİLYA MAĞAZASI → FONKSİYONEL ANTRENMAN STÜDYOSU** · Rev C · 13 Eylül 2026

Bu dosyadaki görseller Three.js kütle modelinden alınan PNG'ler **image-to-image** girdisi
yapılarak üretilmiştir; böylece geometri plana sadık kalır ve model halüsinasyon yapmaz.
Aynı çıktıyı harici bir modelde tekrar üretmek isterseniz:

1. `output/render/` altındaki ilgili görseli **veya** `site/index.html`'i tarayıcıda açıp
   `?cam=N&style=X&ui=0` ile aldığınız ekran görüntüsünü referans görsel olarak yükleyin.
2. Aşağıdaki ortak prompt + stil bloğu + kamera cümlesini birleştirip yapıştırın.

> Üretilen her görselin altına **“temsilî görsel — imalat ölçüsü değildir”** notu düşülmelidir.
> Marka adı, logo ve okunabilir metin üretilmemelidir.

---

## Mekân verisi (prompt'a gömülü)

| Parametre | Değer |
|---|---|
| Net iç kullanım alanı | 103,78 m² |
| Salon | 87,05 m² |
| Islak hacim (2 blok) | 16,73 m² |
| Tavan yüksekliği (varsayım) | 3,20 m |
| Altıgen arena | 10,60 m² · kenar 2,02 m |
| Eşzamanlı kapasite | 12 kişi |

---

## 1 · ORTAK PROMPT (her görselde aynı)

```
Photorealistic architectural interior visualisation of a small boutique combat-and-functional training gym converted from a furniture shop in Istanbul. Keep the EXACT camera position, focal length, perspective, room proportions, wall and column positions, ceiling height and the position, footprint and height of every object in the supplied massing render — change only materials, lighting and realism. Do not add, remove or move any wall, opening, machine or structure. Total interior floor area is 104 m²; clear ceiling height 3.2 m.

THE CENTREPIECE IS A HEXAGONAL BOXING / MMA TRAINING RING, 10.6 m²: a low canvas-covered platform about 30 cm high with a dark charcoal apron and a thin red trim line, SIX padded steel corner posts wrapped in dark red vinyl pads, and FOUR rows of black ring ropes running between the posts on every side, with visible rope tension and turnbuckles. It is a real ring — NOT a wooden frame, NOT a timber rack, NOT shelving, NOT a pergola, NOT a gazebo. There must be NO WOOD, NO TIMBER BEAMS and NO OAK-COLOURED STRUCTURE anywhere in the centre of the room. Ring materials are steel, vinyl padding, rope and canvas only.

THE OWNER'S EQUIPMENT MUST BE CLEARLY VISIBLE AND RECOGNISABLE AS REAL GYM MACHINES, exactly where the massing render places them: two commercial treadmills with running decks, side rails and upright consoles; one upright exercise bike with a flywheel, saddle and handlebar console; two low two-tier dumbbell racks loaded with hex dumbbells; one cable-crossover / functional trainer with two tall weight-stack towers, adjustable pulley arms and a pull-up bar across the top; one multi-station weight machine with a weight stack, seat pad and back pad. Render these as believable professional equipment with realistic proportions — do not leave them as plain boxes and do not invent extra machines that are not in the reference render.

No brand names, no logos, no readable text anywhere. No people. Shot on a 24 mm tilt-shift lens, vertical lines perfectly vertical, f/8, natural interior light balanced with the ceiling linear LEDs, clean architectural photography, high dynamic range, no fisheye distortion, no lens flare.
```

---

## 2 · STİL BLOKLARI

### Ham endüstriyel (`endustriyel`)

```
STYLE: raw industrial. Exposed dark-charcoal ceiling with visible ducts and cable trays, black powder-coated steel, micro-cement and bare concrete texture on walls, matte black 40 mm rubber tile flooring with visible tile joints in the free-weight zone, warm oak accent only at the reception counter and the lounge floor. Copper-bronze finish on the hexagonal rig. Moody, high-contrast lighting.
```

### Sıcak minimal (`minimal`)

```
STYLE: warm minimal. Light plastered off-white walls, pale oak slat feature wall, soft diffused daylight from the glazed shopfront, warm 3000 K linear LEDs, light oak LVT floor in the lounge and entrance, dark grey rubber tiles only in the training zones, brushed brass accents on the hexagonal rig. Calm, airy, low-contrast, editorial interior photography.
```

---

## 3 · KAMERA CÜMLELERİ

### Girişten ringe (`01_giristen_arenaya`)

- Kamera konumu (plan, m): **1,10, 1,60** · göz yüksekliği 1,70 m
- Bakış hedefi (plan, m): **7,00, 6,10**
- Görüş açısı: 70°

```
View from the entrance door looking diagonally across the hall towards the hexagonal ring, which fills the centre of the frame with its red corner pads and four rope rows. The timber-topped reception counter is at the left edge; the cable-crossover trainer and a dumbbell rack stand against the far wall behind the ring.
```

### Ringden soyunma bloğuna (`02_arenadan_soyunmaya`)

- Kamera konumu (plan, m): **3,20, 6,60** · göz yüksekliği 1,70 m
- Bakış hedefi (plan, m): **9,35, 4,20**
- Görüş açısı: 66°

```
View across the training floor, past the near corner posts and ropes of the hexagonal ring, towards the two changing-room blocks on the east wall; their doors and the white partition wall are visible, with the multi-station weight machine in front of them.
```

### Ring ve serbest ağırlık alanı (`03_agirlik_alani`)

- Kamera konumu (plan, m): **5,90, 7,90** · göz yüksekliği 1,68 m
- Bakış hedefi (plan, m): **4,30, 0,80**
- Görüş açısı: 72°

```
Wide view over the hexagonal ring towards the cardio zone along the south glazed façade, with the two treadmills lined up against the window wall and the exercise bike and a dumbbell rack on the right.
```

### Banko ve karşılama (`04_banko_karsilama`)

- Kamera konumu (plan, m): **8,05, 1,25** · göz yüksekliği 1,65 m
- Bakış hedefi (plan, m): **1,50, 5,60**
- Görüş açısı: 70°

```
View from the training floor back towards the reception counter and the glazed entrance façade, with the ring's ropes and red corner pads in the right foreground; the lounge floor finish changes from dark rubber to light timber at the threshold.
```

---

## 4 · ÜRETİLEN DOSYALAR

| Dosya | Açı | Stil |
|---|---|---|
| `output/render/01_giristen_arenaya_endustriyel.png` | Girişten ringe | Ham endüstriyel |
| `output/render/01_giristen_arenaya_minimal.png` | Girişten ringe | Sıcak minimal |
| `output/render/02_arenadan_soyunmaya_endustriyel.png` | Ringden soyunma bloğuna | Ham endüstriyel |
| `output/render/02_arenadan_soyunmaya_minimal.png` | Ringden soyunma bloğuna | Sıcak minimal |
| `output/render/03_agirlik_alani_endustriyel.png` | Ring ve serbest ağırlık alanı | Ham endüstriyel |
| `output/render/03_agirlik_alani_minimal.png` | Ring ve serbest ağırlık alanı | Sıcak minimal |
| `output/render/04_banko_karsilama_endustriyel.png` | Banko ve karşılama | Ham endüstriyel |
| `output/render/04_banko_karsilama_minimal.png` | Banko ve karşılama | Sıcak minimal |

Kütle modeli PNG'leri: `work/model/` · tek dosya offline model: `output/Gym_Model.html`

---

## 5 · GERÇEK ÖNCE / SONRA ÇİFTLERİ (henüz üretilemedi)

İşverenden mevcut durum fotoğrafları gelmediği için brief §7.A atlanmıştır. Fotoğraflar geldiğinde:

1. Her fotoğrafı image-to-image girdisi yapın.
2. Ortak prompt'a şunu ekleyin: *“Keep the exact camera angle, window and column positions and
   ceiling height of the supplied photograph of the existing furniture shop; replace only the
   fit-out with the gym described below.”*
3. En az üç çift üretin: ① ana salon ② giriş / banko bölgesi ③ soyunma koridoru.

Gerçek ÖNCE/SONRA çiftleri, kredi ve ortak görüşmelerinde en ikna edici çıktıdır.
