"""Alan Dagilimi PDF (raster) -> olcekli poligon geometrisi.
Yontem: renk maskesi -> morfolojik kapatma -> en buyuk kontur -> Douglas-Peucker
       -> bilinen m2 degerleriyle piksel->metre olcek kalibrasyonu."""
import json, numpy as np, cv2, pypdfium2 as pdfium
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / "data"; OUT.mkdir(exist_ok=True)
WORK = ROOT / "work"; WORK.mkdir(exist_ok=True)

DPI = 400
doc = pdfium.PdfDocument(str(ROOT/"input/TRIMODE-Alan_Dagilimi.pdf"))
img = doc[0].render(scale=DPI/72).to_pil().rotate(90, expand=True)
bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
cv2.imwrite(str(WORK/"alan_400.png"), bgr)
H, W = bgr.shape[:2]

# hedef renkler (BGR) ve bilinen alanlar (pafta etiketlerinden)
TARGETS = {
    "salon":  (dict(c=(232,232,232), tol=10), 87.05),   # gri  - TRIMODE ana hacim
    "kadin":  (dict(c=(248,176,248), tol=28), 8.49),    # pembe - guney soyunma blogu
    "erkek":  (dict(c=(248,176,176), tol=28), 8.24),    # mavi  - kuzey soyunma blogu
}

def mask_for(c, tol):
    c = np.array(c, dtype=np.int16)
    d = np.abs(bgr.astype(np.int16) - c).max(axis=2)
    m = (d <= tol).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9,9), np.uint8), iterations=3)
    cnts,_ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = [c_ for c_ in cnts if cv2.contourArea(c_) > 5000]
    cnts.sort(key=cv2.contourArea, reverse=True)
    return m, cnts

raw = {}
for key,(spec, m2) in TARGETS.items():
    m, cnts = mask_for(**spec)
    c = cnts[0]
    filled = np.zeros_like(m); cv2.drawContours(filled,[c],-1,255,-1)
    apx = cv2.approxPolyDP(c, 0.0016*cv2.arcLength(c,True), True).reshape(-1,2)
    raw[key] = dict(px_area=float(cv2.contourArea(c)), poly=apx.tolist(), m2=m2)
    print(f"{key:7s} px={raw[key]['px_area']:12.0f}  m2={m2:6.2f}  "
          f"px/m2={raw[key]['px_area']/m2:9.0f}  kose={len(apx)}")

# olcek: uc bolgenin agirlikli ortalamasi (buyuk bolge daha guvenilir)
tot_px = sum(v["px_area"] for v in raw.values())
tot_m2 = sum(v["m2"] for v in raw.values())
px_per_m2 = tot_px / tot_m2
S = 1.0/np.sqrt(px_per_m2)          # metre / piksel
print(f"\nBirlesik olcek: {px_per_m2:.0f} px/m2 -> {S*1000:.4f} mm/px")
for k,v in raw.items():
    print(f"  kontrol {k}: {v['px_area']*S*S:7.2f} m2 (pafta {v['m2']:.2f})  sapma "
          f"{100*(v['px_area']*S*S/v['m2']-1):+5.1f}%")

# ortak orijin: salon poligonunun sol-alt kosesi; y yukari pozitif
allpts = np.vstack([np.array(v["poly"]) for v in raw.values()])
x0, y0 = allpts[:,0].min(), allpts[:,1].max()
def to_m(poly):
    return [[round(float((p[0]-x0)*S),3), round(float((y0-p[1])*S),3)] for p in poly]

geom = {
  "kaynak": "TRIMODE-Alan_Dagilimi.pdf (raster/JPEG) — renk maskesiyle vektorlestirildi",
  "yontem": "poligon piksel alani, paftadaki m2 etiketleriyle kalibre edildi",
  "tolerans": "+/- %3 (raster izleme) — yerinde dogrulanacak",
  "olcek_mm_per_px": round(S*1000,5),
  "dpi": DPI,
  "alanlar_m2": {"salon":87.05,"kadin_blok":8.49,"erkek_blok":8.24,
                 "on_bahce":24.39,"arka_bahce":32.82,
                 "ic_toplam":round(87.05+8.49+8.24,2)},
  "poligonlar_m": {k: to_m(v["poly"]) for k,v in raw.items()},
}
(OUT/"geometry_raw.json").write_text(json.dumps(geom, ensure_ascii=False, indent=1))
print("\n-> data/geometry_raw.json")
for k,v in geom["poligonlar_m"].items():
    xs=[p[0] for p in v]; ys=[p[1] for p in v]
    print(f"  {k:7s} kose={len(v):3d}  bbox {max(xs)-min(xs):.2f} x {max(ys)-min(ys):.2f} m")
