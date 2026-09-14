# -*- coding: utf-8 -*-
"""§11 QA PROTOKOLÜ — otomatik kontroller."""
import sys, os, json, re, glob
sys.path.insert(0, os.path.dirname(__file__))
from pathlib import Path
import pypdfium2 as pdfium
import proj as P
from openpyxl import load_workbook
load_wb = load_workbook

HATA=[]; UYARI=[]
def ok(t): print("  ✓", t)
def hata(t): HATA.append(t); print("  ✗", t)
def uyar(t): UYARI.append(t); print("  !", t)

print("\n1 · PDF ÜRETİMİ VE SAYFA RENDER")
for f,bek in (("output/Gym_Donusum_Dosyasi_A3.pdf",12),("output/Gym_Sunum_16x9.pdf",12),
              ("output/Gym_Mekanik_Proje_A3.pdf",6),("output/Gym_Elektrik_Proje_A3.pdf",6)):
    d=pdfium.PdfDocument(f); n=len(d)
    w,h=d[0].get_size()
    print(f"  {Path(f).name}: {n} sayfa · {w:.0f}×{h:.0f} pt")
    if n!=bek: hata(f"{f}: {n} sayfa (beklenen {bek})")
    else: ok(f"{Path(f).name} sayfa sayısı")
    if "A3" in f and not (abs(w-1190)<3 and abs(h-842)<3):
        hata("A3 yatay değil"); 
    for i in range(n):
        d[i].render(scale=72/72)   # render hatası varsa burada patlar
    ok(f"{Path(f).name} tüm sayfalar hatasız render edildi")

print("\n2 · TÜRKÇE GLİF TARAMASI (ş ğ ı İ ü ö ç Ş Ğ Ü Ö Ç)")
TR="şğıİüöçŞĞÜÖÇ"
for f in ("output/Gym_Donusum_Dosyasi_A3.pdf","output/Gym_Sunum_16x9.pdf",
          "output/Gym_Mekanik_Proje_A3.pdf","output/Gym_Elektrik_Proje_A3.pdf"):
    d=pdfium.PdfDocument(f); eksik=[]
    for i in range(len(d)):
        t=d[i].get_textpage().get_text_range()
        if not any(ch in t for ch in TR): eksik.append(i+1)
        # bozuk kodlama izi
        if "�" in t or "Ã" in t: hata(f"{Path(f).name} s.{i+1}: bozuk karakter")
    if eksik: uyar(f"{Path(f).name}: Türkçe glif içermeyen sayfa {eksik}")
    else: ok(f"{Path(f).name}: her sayfada Türkçe glif okunabiliyor")
# upper() tuzagi
for f in ("output/Gym_Donusum_Dosyasi_A3.pdf","output/Gym_Sunum_16x9.pdf"):
    d=pdfium.PdfDocument(f)
    for i in range(len(d)):
        t=d[i].get_textpage().get_text_range()
        for kotu in ("ISLAK HACIM","ISTANBUL","GIRIŞ","GIRIS","IMALAT","ILK ","IŞVEREN"):
            if kotu in t: uyar(f"{Path(f).name} s.{i+1}: Türkçe büyük harf şüphesi → '{kotu}'")

print("\n3 · ÇAPRAZ TUTARLILIK — m²")
zt=round(sum(P.ZON_M2.values()),2)
if abs(zt-P.A["salon"])>0.01: hata(f"bölge toplamı {zt} ≠ salon {P.A['salon']}")
else: ok(f"bölge toplamı = salon = {P.A['salon']} m²")
it=round(P.A["salon"]+P.A["erkek_blok"]+P.A["kadin_blok"],2)
if abs(it-P.A["ic_toplam"])>0.01: hata("iç toplam tutarsız")
else: ok(f"salon + 2 blok = net iç alan = {P.A['ic_toplam']} m²")
for k,d in P.ISLAK_M2_DETAY.items():
    s=round(d["soyunma"]+d["dus"]+d["wc"],2)
    if abs(s-d["tum"])>0.06: hata(f"{k}: alt mekân toplamı {s} ≠ blok {d['tum']}")
    else: ok(f"{k}: soyunma+duş+WC ≈ blok ({s} / {d['tum']} m²)")
g=json.load(open("data/geometry.json"))
if abs(sum(g["alan_kontrol"].values())-P.A["ic_toplam"])>0.02: hata("geometry.json alanları tutmuyor")
else: ok("geometry.json ↔ pafta m² kalibrasyonu")
dm=json.load(open("data/dimensions.json"))
if abs(sum(b["m2"] for b in dm["bolgeler"])-P.A["salon"])>0.02: hata("dimensions.json bölge toplamı")
else: ok("dimensions.json ↔ proj.py bölge m²")

print("\n4 · ÇAPRAZ TUTARLILIK — TL")
wb=load_workbook("output/Gym_Maliyet_BoQ.xlsx")
ws=wb["2 · Detay metraj"]
poz_x=[r[0].value for r in ws.iter_rows(min_row=4,max_col=1) if r[0].value and re.match(r"^\d\d\.\d\d[a-z]?$",str(r[0].value))]
if len(poz_x)!=len(P.B): hata(f"xlsx poz {len(poz_x)} ≠ model {len(P.B)}")
else: ok(f"BoQ poz sayısı = {len(P.B)}")
for sen in ("M","O"):
    for isl in ("A","B"):
        m=P.maliyet(sen,isl); lo=hi=0
        for poz,gr,tn,br,mik,l,h_,s in P.B:
            kod="A" if poz=="03.08" else ("B" if poz=="03.09" else ("X" if s=="—" else s))
            dh=1 if kod=="M" else (1 if (kod=="O" and sen=="O") else
               (1 if (kod=="A" and isl=="A") else (1 if (kod=="B" and isl=="B") else 0)))
            lo+=round(mik*l)*dh; hi+=round(mik*h_)*dh
        if abs(lo-m["imalat"][0])>2 or abs(hi-m["imalat"][1])>2:
            hata(f"{sen}/{isl}: xlsx {lo}-{hi} ≠ PDF {m['imalat'][0]:.0f}-{m['imalat'][1]:.0f}")
        else: ok(f"senaryo {sen}/{isl}: BoQ formülü = PDF maliyet modeli")
mO=P.maliyet("O","A")
bek=f"{mO['toplam'][0]/1e6:.2f}–{mO['toplam'][1]/1e6:.2f}".replace(".",",")
for f in ("output/Gym_Donusum_Dosyasi_A3.pdf","output/Gym_Sunum_16x9.pdf"):
    d=pdfium.PdfDocument(f); metin="".join(d[i].get_textpage().get_text_range() for i in range(len(d)))
    if bek not in metin: uyar(f"{Path(f).name}: '{bek} M₺' bandı metinde bulunamadı")
    else: ok(f"{Path(f).name}: bütçe bandı {bek} M₺ tutarlı")

print("\n4b · MEKANİK VE ELEKTRİK PROJE TUTARLILIĞI")
# hava dengesi
bes = sum(m[3] for m in P.MENFEZ if m[4]=="besleme")
egz = sum(m[3] for m in P.MENFEZ if m[4] in ("egzoz","valf"))
if bes != P.TAZE: hata(f"besleme menfez toplamı {bes} ≠ tasarım debisi {P.TAZE}")
else: ok(f"besleme menfezleri = tasarım taze hava debisi = {bes} m³/h")
if egz != P.TAZE: hata(f"egzoz toplamı {egz} ≠ besleme {P.TAZE} — hava dengesi bozuk")
else: ok(f"egzoz toplamı = besleme = {egz} m³/h (nötr denge)")
if P.KLIMA_BTU < P.SOGUTMA_BTU: hata("kurulu klima kapasitesi hesaplanan yükün altında")
else: ok(f"kurulu klima {P.KLIMA_BTU} BTU ≥ hesaplanan {P.SOGUTMA_BTU} BTU (%{P.SOGUTMA_MARJ} marj)")
if P.FAZ_DENGE > 15: hata(f"faz dengesizliği %{P.FAZ_DENGE} — hedef ≤ %15")
else: ok(f"faz dengesizliği %{P.FAZ_DENGE} (hedef ≤ %15)")
if abs(sum(P.FAZ_YUK.values()) - P.TALEP_KW) > 0.05: hata("faz yükleri toplamı ≠ talep gücü")
else: ok(f"faz yükleri toplamı = talep gücü = {P.TALEP_KW} kW")
if max(P.AKIM_FAZ.values()) > P.ANA_KESICI/3: hata("faz akımı ana kesici anma akımını aşıyor")
else: ok(f"en yüksek faz akımı {max(P.AKIM_FAZ.values())} A ≤ ana kesici {P.ANA_KESICI//3} A")
_kam_islak = [k for k in P.KAMERA if any(P.ISLAK[b]["tum"].contains(
    __import__("shapely.geometry", fromlist=["Point"]).Point(k[1],k[2])) for b in P.ISLAK)]
if _kam_islak: hata(f"soyunma/WC içinde kamera var: {[k[0] for k in _kam_islak]}")
else: ok("soyunma ve WC içinde kamera YOK (mevzuat sınırı korunuyor)")
# disiplin BoQ'ları ana BoQ ile aynı mı
for dosya, grup in (("output/Gym_Mekanik_BoQ.xlsx","MEKANİK"),
                    ("output/Gym_Elektrik_BoQ.xlsx","ELEKTRİK")):
    w2=load_wb(dosya); d2=w2["2 · Detay metraj"]
    pozlar=[r[0].value for r in d2.iter_rows(min_row=4,max_col=1)
            if r[0].value and re.match(r"^\d\d\.\d\d[a-z]?$",str(r[0].value))]
    ana=[r[0] for r in P.B if r[1]==grup]
    if pozlar!=ana: hata(f"{Path(dosya).name}: poz listesi ana BoQ ile aynı değil")
    else: ok(f"{Path(dosya).name}: {len(ana)} poz — ana BoQ'daki {grup} grubunun birebir aynısı")
    if len(w2.sheetnames)!=4: hata(f"{Path(dosya).name} 4 sayfa değil")
    bos=sum(1 for r in range(4,4+len(ana)) if d2.cell(r,6).value is None)
    if bos!=len(ana): hata(f"{Path(dosya).name}: birim fiyat sütunu boş değil")
    else: ok(f"{Path(dosya).name}: birim fiyat sütunu tamamen boş")

print("\n5 · XLSX FORMÜL SAĞLIĞI")
s1=wb["1 · Özet"]
fml=sum(1 for row in wb["2 · Detay metraj"].iter_rows() for c in row
        if isinstance(c.value,str) and c.value.startswith("="))
fml+=sum(1 for row in s1.iter_rows() for c in row if isinstance(c.value,str) and c.value.startswith("="))
ok(f"{fml} canlı formül hücresi")
bos=sum(1 for r in range(4,4+len(P.B)) if wb["2 · Detay metraj"].cell(r,6).value is None)
if bos!=len(P.B): hata(f"birim fiyat sütunu boş değil ({len(P.B)-bos} dolu)")
else: ok("birim fiyat sütunu (F) tamamen boş — teklif girişi için hazır")
if len(wb.sheetnames)!=4: hata("xlsx 4 sayfa değil")
else: ok("xlsx sayfaları: "+", ".join(wb.sheetnames))

print("\n6 · RENDER VE MODEL ÇIKTILARI")
r=sorted(glob.glob("output/render/*.png"))
if len(r)!=8: hata(f"render sayısı {len(r)} (beklenen 8)")
else: ok("8 render (4 açı × 2 stil)")
from PIL import Image
for p in r:
    if Image.open(p).info.get("altyazi")!="1": hata(f"{Path(p).name}: altyazı şeridi yok")
ok("tüm render'larda 'temsilî görsel' şeridi var")
mh=Path("output/Gym_Model.html")
if not mh.exists(): hata("Gym_Model.html yok")
else:
    t=mh.read_text(encoding="utf-8")
    if 'type="module"' in t: hata("Gym_Model.html ES module kullanıyor")
    # GERÇEK offline testi: tarayıcıda aç, dosya dışı her isteği reddet
    import subprocess
    env=dict(os.environ, NODE_PATH=subprocess.run(["npm","root","-g"],capture_output=True,
             text=True).stdout.strip())
    r=subprocess.run(["node","tools/qa_offline.js",str(mh.resolve())],
                     capture_output=True, text=True, env=env, timeout=180)
    try: j=json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: hata("offline testi çalıştırılamadı: "+r.stderr[:180]); j={}
    if j.get("disIstek"): hata(f"Gym_Model.html dış kaynak istedi: {j['disIstek'][:3]}")
    elif j: ok("Gym_Model.html: tarayıcıda sıfır dış istek (gerçekten offline)")
    if j.get("hata"): hata(f"Gym_Model.html konsol hatası: {j['hata'][:2]}")
    elif j: ok("Gym_Model.html: konsol hatası yok")
    if j.get("render")!=8: hata(f"HTML galeri {j.get('render')} render gösteriyor")
    else: ok("HTML galeri 8 render gösteriyor")
    if not j.get("canvasBoyut"): hata("HTML 3B canvas boyutlanmadı")
    else: ok(f"HTML 3B görüntüleyici istek üzerine açılıyor ({j.get('kamDugme')} kamera düğmesi)")
    if j.get("yatayTasma"): hata("HTML yatay taşma var")
    # JS KAPALI senaryosu — telefon/sohbet önizlemesi
    nj = j.get("nojs", {})
    if nj.get("gorunurBolum") != nj.get("bolum"):
        hata(f"JS kapalıyken {nj.get('bolum')} bölümün yalnızca {nj.get('gorunurBolum')}'i görünüyor")
    else: ok(f"JS KAPALIYKEN {nj.get('bolum')} bölümün tamamı görünür")
    if nj.get("nav",0) < 4: hata(f"JS kapalıyken gezinme bağlantısı {nj.get('nav')}")
    else: ok(f"JS kapalıyken {nj.get('nav')} çapa bağlantısı çalışır durumda")
    if nj.get("render") != 8: hata(f"JS kapalıyken galeri {nj.get('render')} görsel gösteriyor")
    else: ok("JS kapalıyken 8 render görseli de görünüyor")
    if nj.get("tabloSatir",0) < 8: hata("JS kapalıyken tablolar boş")
    else: ok(f"JS kapalıyken tablolar dolu ({nj.get('tabloSatir')} satır)")
    if nj.get("nojsTasma") or j.get("nojsTasma"): hata("JS kapalıyken yatay taşma var")
    ok(f"Gym_Model.html tek dosya, offline · {len(t.encode())/1e6:.2f} MB")

print("\n7 · TESLİMAT LİSTESİ")
for f in ("output/Gym_Donusum_Dosyasi_A3.pdf","output/Gym_Sunum_16x9.pdf",
          "output/Gym_Mekanik_Proje_A3.pdf","output/Gym_Elektrik_Proje_A3.pdf",
          "output/Gym_Maliyet_BoQ.xlsx","output/Gym_Mekanik_BoQ.xlsx",
          "output/Gym_Elektrik_BoQ.xlsx","output/Gym_Model.html",
          "output/Render_Promptlari.md","BUILD_NOTES.md"):
    if Path(f).exists(): ok(f"{f}  ({Path(f).stat().st_size/1e6:.2f} MB)")
    else: hata(f"EKSİK: {f}")

print("\n" + "="*64)
print(f"SONUÇ: {len(HATA)} hata, {len(UYARI)} uyarı")
for t in HATA: print("  ✗", t)
for t in UYARI: print("  !", t)
sys.exit(1 if HATA else 0)
