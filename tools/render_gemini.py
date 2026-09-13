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
 "Photorealistic architectural interior visualisation of a small boutique functional-training gym "
 "converted from a furniture shop in Istanbul. Keep the EXACT camera position, focal length, "
 "perspective, room proportions, wall and column positions, ceiling height and the position and "
 "footprint of every object in the supplied massing render — change only materials, lighting and "
 "realism. Do not add, remove or move any wall, opening, machine or rig. "
 "Total interior floor area is 104 m²; clear ceiling height 3.2 m. "
 "The hexagonal four-tier steel training rig in the centre covers 10.6 m². "
 "No brand names, no logos, no readable text anywhere. No people unless stated. "
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
   "hexagonal rig; the reception counter is on the left, the glazed shopfront behind the camera.",
 "02_arenadan_soyunmaya": "View across the training floor towards the two changing-room blocks on "
   "the east wall; their doors and the partition wall are visible.",
 "03_agirlik_alani": "View over the hexagonal rig towards the free-weight and cardio zone along the "
   "south glazed façade, two treadmills against the window wall.",
 "04_banko_karsilama": "View from the training floor back towards the reception counter and the "
   "glazed entrance façade; the lounge floor finish changes at the threshold.",
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
