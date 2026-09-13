# -*- coding: utf-8 -*-
"""TESLİMAT B — Three.js kütle modeli PNG'lerini image-to-image ile fotogerçekçileştirir."""
import os, sys, json, base64, time, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(__file__))
from pathlib import Path

KEY   = os.environ.get("GEMINI_API_KEY", "")
MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3-pro-image")
URL   = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={KEY}"
D     = json.load(open("data/dimensions.json"))
SRC   = Path("work/model"); OUT = Path("output/render"); OUT.mkdir(parents=True, exist_ok=True)

ORTAK = (
 "Photorealistic architectural interior visualisation of a small boutique combat-and-functional "
 "training gym converted from a furniture shop in Istanbul. "
 "Keep the EXACT camera position, focal length, perspective, room proportions, wall and column "
 "positions, ceiling height and the position, footprint and height of every object in the supplied "
 "massing render — change only materials, lighting and realism. Do not add, remove or move any wall, "
 "opening, machine or structure. Total interior floor area is 104 m²; clear ceiling height 3.2 m.\n\n"
 "THE CENTREPIECE IS A HEXAGONAL BOXING / MMA TRAINING RING, 10.6 m²: a low canvas-covered "
 "platform about 30 cm high with a dark charcoal apron and a thin red trim line, SIX padded steel "
 "corner posts wrapped in dark red vinyl pads, and FOUR rows of black ring ropes running between "
 "the posts on every side, with visible rope tension and turnbuckles. "
 "It is a real ring — NOT a wooden frame, NOT a timber rack, NOT shelving, NOT a pergola, NOT a "
 "gazebo. There must be NO WOOD, NO TIMBER BEAMS and NO OAK-COLOURED STRUCTURE anywhere in the "
 "centre of the room. Ring materials are steel, vinyl padding, rope and canvas only.\n\n"
 "THE OWNER'S EQUIPMENT MUST BE CLEARLY VISIBLE AND RECOGNISABLE AS REAL GYM MACHINES, exactly "
 "where the massing render places them: two commercial treadmills with running decks, side rails "
 "and upright consoles; one upright exercise bike with a flywheel, saddle and handlebar console; "
 "two low two-tier dumbbell racks loaded with hex dumbbells; one cable-crossover / functional "
 "trainer with two tall weight-stack towers, adjustable pulley arms and a pull-up bar across the "
 "top; one multi-station weight machine with a weight stack, seat pad and back pad. "
 "Render these as believable professional equipment with realistic proportions — do not leave them "
 "as plain boxes and do not invent extra machines that are not in the reference render.\n\n"
 "No brand names, no logos, no readable text anywhere. No people. "
 "Shot on a 24 mm tilt-shift lens, vertical lines perfectly vertical, f/8, natural interior light "
 "balanced with the ceiling linear LEDs, clean architectural photography, high dynamic range, "
 "no fisheye distortion, no lens flare."
)
STIL = {
 "endustriyel": (
   "STYLE: raw industrial. Exposed dark-charcoal ceiling with visible ducts and cable trays, "
   "black powder-coated steel, micro-cement and bare concrete texture on walls, matte black "
   "40 mm rubber tile flooring with visible tile joints in the free-weight zone, warm oak accent "
   "only at the reception counter and the lounge floor. Copper-bronze finish on the hexagonal rig. "
   "Moody, high-contrast lighting."),
 "minimal": (
   "STYLE: warm minimal. Light plastered off-white walls, pale oak slat feature wall, soft diffused "
   "daylight from the glazed shopfront, warm 3000 K linear LEDs, light oak LVT floor in the lounge "
   "and entrance, dark grey rubber tiles only in the training zones, brushed brass accents on the "
   "hexagonal rig. Calm, airy, low-contrast, editorial interior photography."),
}
KAMERA = {
 "01_giristen_arenaya": "View from the entrance door looking diagonally across the hall towards the "
   "hexagonal ring, which fills the centre of the frame with its red corner pads and four rope rows. "
   "The timber-topped reception counter is at the left edge; the cable-crossover trainer and a "
   "dumbbell rack stand against the far wall behind the ring.",
 "02_arenadan_soyunmaya": "View across the training floor, past the near corner posts and ropes of "
   "the hexagonal ring, towards the two changing-room blocks on the east wall; their doors and the "
   "white partition wall are visible, with the multi-station weight machine in front of them.",
 "03_agirlik_alani": "Wide view over the hexagonal ring towards the cardio zone along the south "
   "glazed façade, with the two treadmills lined up against the window wall and the exercise bike "
   "and a dumbbell rack on the right.",
 "04_banko_karsilama": "View from the training floor back towards the reception counter and the "
   "glazed entrance façade, with the ring's ropes and red corner pads in the right foreground; "
   "the lounge floor finish changes from dark rubber to light timber at the threshold.",
}

def istek(prompt, png, deneme=3):
    body = {"contents":[{"parts":[
              {"text": prompt},
              {"inline_data":{"mime_type":"image/png",
                              "data": base64.b64encode(png).decode()}}]}],
            "generationConfig":{"responseModalities":["TEXT","IMAGE"]}}
    data = json.dumps(body).encode()
    for k in range(deneme):
        try:
            req = urllib.request.Request(URL, data=data,
                     headers={"Content-Type":"application/json"})
            with urllib.request.urlopen(req, timeout=300) as r:
                j = json.load(r)
            for c in j.get("candidates", []):
                for p in c.get("content", {}).get("parts", []):
                    d_ = p.get("inlineData") or p.get("inline_data")
                    if d_: return base64.b64decode(d_["data"])
            print("    görsel dönmedi:", json.dumps(j)[:240])
        except urllib.error.HTTPError as e:
            print(f"    HTTP {e.code}: {e.read()[:200].decode('utf8','ignore')}")
        except Exception as e:
            print("    hata:", type(e).__name__, str(e)[:160])
        time.sleep(3*(k+1))
    return None

def main():
    if not KEY:
        print("GEMINI_API_KEY yok — §7.C yedek planına düşülüyor."); return 1
    tek = sys.argv[1] if len(sys.argv) > 1 else None
    ok = fail = 0
    for k in D["kameralar"]:
        for stil in D["stiller"]:
            ad = f"{k['ad']}_{stil}"
            if tek and tek not in ad: continue
            src = SRC/f"{ad}.png"
            if not src.exists(): print("  atlandı (kaynak yok):", ad); continue
            hedef = OUT/f"{ad}.png"
            if hedef.exists() and os.environ.get("FORCE") != "1":
                print("  var:", hedef.name); ok += 1; continue
            prompt = f"{ORTAK}\n\n{STIL[stil]}\n\nCAMERA: {KAMERA[k['ad']]}"
            print("  →", ad)
            png = istek(prompt, src.read_bytes())
            if png: hedef.write_bytes(png); ok += 1; print("     kaydedildi", len(png)//1024, "KB")
            else:   fail += 1; print("     BAŞARISIZ")
    print(f"render: {ok} başarılı, {fail} başarısız")
    return 0 if fail == 0 else 2

if __name__ == "__main__":
    sys.exit(main())
