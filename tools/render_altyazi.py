# -*- coding: utf-8 -*-
"""Her render'ın altına zorunlu not şeridi: 'temsilî görsel — imalat ölçüsü değildir'."""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
D=json.load(open("data/dimensions.json"))
BAS={k["ad"]:k["baslik"] for k in D["kameralar"]}
STL={k:v["ad"] for k,v in D["stiller"].items()}
F ="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FB="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
n=0
for p in sorted(Path("output/render").glob("*.png")):
    im=Image.open(p).convert("RGB")
    if im.info.get("altyazi")=="1": continue
    W,H=im.size; bh=max(46,int(H*0.072))
    out=Image.new("RGB",(W,H+bh),(22,39,61)); out.paste(im,(0,0))
    d=ImageDraw.Draw(out)
    d.rectangle([0,H,W,H+3],fill=(184,115,51))
    fb=ImageFont.truetype(FB,int(bh*0.36)); f=ImageFont.truetype(F,int(bh*0.28))
    ad=p.stem; stil=ad.rsplit("_",1)[1]; kam=ad[:-(len(stil)+1)]
    d.text((int(bh*0.45), H+int(bh*0.18)), f"{BAS.get(kam,kam)}  ·  {STL.get(stil,stil)}",
           font=fb, fill=(255,255,255))
    t="temsilî görsel — imalat ölçüsü değildir"
    d.text((W-int(bh*0.45)-d.textlength(t,font=f), H+int(bh*0.58)), t, font=f, fill=(150,173,197))
    out.save(p, pnginfo=None)
    # işaretle
    from PIL import PngImagePlugin
    meta=PngImagePlugin.PngInfo(); meta.add_text("altyazi","1")
    out.save(p, pnginfo=meta); n+=1
print(f"{n} render'a altyazı eklendi")
