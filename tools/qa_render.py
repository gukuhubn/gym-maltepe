import sys, pypdfium2 as pdfium
from pathlib import Path
src=sys.argv[1]; out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
dpi=float(sys.argv[3]) if len(sys.argv)>3 else 110
d=pdfium.PdfDocument(src)
for i in range(len(d)):
    d[i].render(scale=dpi/72).to_pil().save(out/f"p{i+1:02d}.png")
print(len(d),"sayfa ->",out)
