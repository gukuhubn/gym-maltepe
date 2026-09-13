# -*- coding: utf-8 -*-
"""Her render'ın altına zorunlu not şeridi. IDEMPOTENT: varsa eski şerit kırpılır,
sonra güncel başlıkla yeniden basılır."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

D   = json.load(open("data/dimensions.json"))
BAS = {k["ad"]: k["baslik"] for k in D["kameralar"]}
STL = {k: v["ad"] for k, v in D["stiller"].items()}
F   = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB  = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LACI = (22, 39, 61)

def serit_yuksekligi(h_orj):
    return max(46, int(h_orj * 0.072))

def eski_serit_kirp(im):
    """Altta düz lacivert şerit varsa kırp. Şerit yüksekliği formülden çözülür."""
    W, H = im.size
    for bh in range(40, 200):
        h0 = H - bh
        if h0 <= 0 or serit_yuksekligi(h0) != bh:
            continue
        # şeridin üst kenarı gerçekten düz lacivert mi? (sol ve sağ kenardan örnekle)
        px = im.load()
        ok = all(
            abs(px[x, H - 3][0] - LACI[0]) < 14 and
            abs(px[x, H - 3][1] - LACI[1]) < 14 and
            abs(px[x, H - 3][2] - LACI[2]) < 14
            for x in (3, W // 2, W - 4))
        if ok:
            return im.crop((0, 0, W, h0)), True
    return im, False

n = k = 0
for p in sorted(Path("output/render").glob("*.png")):
    im = Image.open(p).convert("RGB")
    im, kirpildi = eski_serit_kirp(im)
    k += kirpildi
    W, H = im.size
    bh = serit_yuksekligi(H)
    out = Image.new("RGB", (W, H + bh), LACI)
    out.paste(im, (0, 0))
    d = ImageDraw.Draw(out)
    d.rectangle([0, H, W, H + 3], fill=(184, 115, 51))
    fb = ImageFont.truetype(FB, int(bh * 0.36))
    f  = ImageFont.truetype(F,  int(bh * 0.28))
    ad = p.stem
    stil = ad.rsplit("_", 1)[1]
    kam  = ad[:-(len(stil) + 1)]
    d.text((int(bh * 0.45), H + int(bh * 0.18)),
           f"{BAS.get(kam, kam)}  ·  {STL.get(stil, stil)}", font=fb, fill=(255, 255, 255))
    t = "temsilî görsel — imalat ölçüsü değildir"
    d.text((W - int(bh * 0.45) - d.textlength(t, font=f), H + int(bh * 0.58)),
           t, font=f, fill=(150, 173, 197))
    meta = PngImagePlugin.PngInfo(); meta.add_text("altyazi", "1")
    out.save(p, pnginfo=meta)
    n += 1
print(f"{n} render'a altyazı basıldı ({k} tanesinde eski şerit kırpıldı)")
