"""Nihai olcekli geometri: data/geometry.json
Kaynak: TRIMODE-Alan_Dagilimi.pdf (raster) renk maskesi + m2 kalibrasyonu."""
import json, numpy as np, cv2, pypdfium2 as pdfium
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
DPI = 400
img = pdfium.PdfDocument(str(ROOT/"input/TRIMODE-Alan_Dagilimi.pdf"))[0]\
        .render(scale=DPI/72).to_pil().rotate(90, expand=True)
bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

SPEC = {"salon":((232,232,232),10,87.05,0.006),
        "erkek":((248,176,176),28, 8.24,0.010),
        "kadin":((248,176,248),28, 8.49,0.010)}

def trace(c,tol,eps):
    c=np.array(c,np.int16); d=np.abs(bgr.astype(np.int16)-c).max(axis=2)
    m=(d<=tol).astype(np.uint8)*255
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8),iterations=3)
    cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cs=[x for x in cs if cv2.contourArea(x)>5000]; cs.sort(key=cv2.contourArea,reverse=True)
    c0=cs[0]
    return cv2.approxPolyDP(c0,eps*cv2.arcLength(c0,True),True).reshape(-1,2).astype(float), cv2.contourArea(c0)

raw={k:trace(*v[:2],v[3]) for k,v in SPEC.items()}
px_tot=sum(v[1] for v in raw.values()); m2_tot=sum(SPEC[k][2] for k in raw)
S=1.0/np.sqrt(px_tot/m2_tot)                      # m / px

# -- ortak cerceve: piksel -> metre, y yukari
allp=np.vstack([v[0] for v in raw.values()])
ox,oy=allp[:,0].min(), allp[:,1].max()
def M(p): return np.column_stack([(p[:,0]-ox)*S,(oy-p[:,1])*S])
poly={k:M(v[0]) for k,v in raw.items()}

# -- guney cephe kenarini yataya oturt (en uzun ~yatay alt kenar)
sal=poly["salon"]; n=len(sal)
best=None
for i in range(n):
    a,b=sal[i],sal[(i+1)%n]; d=b-a; L=np.hypot(*d)
    ang=np.degrees(np.arctan2(d[1],d[0]))
    horiz = min(abs(ang), 180-abs(ang))
    if L>4 and horiz<25 and (a[1]+b[1])/2 < sal[:,1].mean():
        if best is None or L>best[0]:
            best=(L, ang if abs(ang)<90 else (ang-180 if ang>0 else ang+180))
rot=-best[1]; th=np.radians(rot); R=np.array([[np.cos(th),-np.sin(th)],[np.sin(th),np.cos(th)]])
poly={k:(v@R.T) for k,v in poly.items()}
allp=np.vstack(list(poly.values())); ox2,oy2=allp[:,0].min(),allp[:,1].min()
poly={k:v-np.array([ox2,oy2]) for k,v in poly.items()}

# -- alanlari pafta degerlerine birebir olceklemek icin kucuk duzeltme
def shoelace(p): return 0.5*abs(sum(p[i,0]*p[(i+1)%len(p),1]-p[(i+1)%len(p),0]*p[i,1] for i in range(len(p))))
k_glob=np.sqrt(sum(SPEC[k][2] for k in poly)/sum(shoelace(v) for v in poly.values()))
poly={k:v*k_glob for k,v in poly.items()}

out={"kaynak":"TRIMODE-Alan_Dagilimi.pdf (JPEG raster) - renk maskesi ile vektorlestirildi",
     "yontem":"kontur izleme + pafta m2 etiketleriyle olcek kalibrasyonu; guney cephe yataya donduruldu",
     "dogruluk":"+/- %3 - yerinde dogrulanacak (DXF R2010 export istenmeli)",
     "olcek_m_per_px":round(float(S),6),"rotasyon_derece":round(float(rot),3),
     "poligonlar":{k:[[round(float(x),3),round(float(y),3)] for x,y in v] for k,v in poly.items()},
     "alan_kontrol":{k:round(float(shoelace(v)),2) for k,v in poly.items()}}
(ROOT/"data").mkdir(exist_ok=True)
(ROOT/"data/geometry.json").write_text(json.dumps(out,ensure_ascii=False,indent=1))
for k,v in poly.items():
    print(f"{k:6s} alan={shoelace(v):6.2f} (pafta {SPEC[k][2]:.2f})  kose={len(v):2d} "
          f"bbox {v[:,0].max()-v[:,0].min():5.2f} x {v[:,1].max()-v[:,1].min():5.2f}")
print("rotasyon",round(rot,2),"deg;  toplam ic alan",round(sum(shoelace(v) for v in poly.values()),2))
print("\nSALON kenarlari:")
sal=poly["salon"]
for i in range(len(sal)):
    a,b=sal[i],sal[(i+1)%len(sal)]; d=b-a
    print(f"  {i:2d} ({a[0]:6.2f},{a[1]:6.2f}) -> L={np.hypot(*d):5.2f}  aci={np.degrees(np.arctan2(d[1],d[0])):7.1f}")
for k in ("erkek","kadin"):
    print(f"\n{k.upper()}:"); p=poly[k]
    for i in range(len(p)):
        a,b=p[i],p[(i+1)%len(p)]; d=b-a
        print(f"  {i:2d} ({a[0]:6.2f},{a[1]:6.2f}) -> L={np.hypot(*d):5.2f}  aci={np.degrees(np.arctan2(d[1],d[0])):7.1f}")
