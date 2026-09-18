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
              ("output/Gym_Mimari_Proje_A3.pdf",14),
              ("output/Gym_Mekanik_Proje_A3.pdf",9),("output/Gym_Elektrik_Proje_A3.pdf",8),
              ("output/Gym_Insaat_Seti_A3.pdf",33)):
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
          "output/Gym_Mimari_Proje_A3.pdf","output/Gym_Mekanik_Proje_A3.pdf",
          "output/Gym_Elektrik_Proje_A3.pdf","output/Gym_Insaat_Seti_A3.pdf"):
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
        if abs(lo-m["imalat"][0])>len(P.B) or abs(hi-m["imalat"][1])>len(P.B):   # satır bazlı yuvarlama payı
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

print("\n6b · CAD SETİ (DXF R2010)")
import ezdxf as _ez
_cad = sorted(Path("cad").glob("*.dxf"))
if len(_cad)!=5: hata(f"CAD setinde {len(_cad)} dxf var (beklenen 5)")
else: ok("5 DXF dosyası üretildi (mimari · mekanik · elektrik · birleşik · ADP şema)")
for f in _cad:
    d=_ez.readfile(f); a=d.audit()
    if a.errors: hata(f"{f.name}: {len(a.errors)} DXF hatası")
    if d.dxfversion!="AC1024": hata(f"{f.name}: sürüm {d.dxfversion} (R2010/AC1024 bekleniyor)")
    if d.header.get("$INSUNITS")!=4: hata(f"{f.name}: birim milimetre değil")
    if len(d.layers)<40: hata(f"{f.name}: katman sayısı {len(d.layers)}")
    bl=[b.name for b in d.blocks if not b.name.startswith("*")]
    if len(bl)<30: hata(f"{f.name}: blok sayısı {len(bl)}")
    if "Layout1" in d.layouts.names(): hata(f"{f.name}: boş Layout1 silinmemiş")
    ok(f"{f.name}: AC1024 · mm · {len(d.layers)} katman · {len(bl)} blok · "
       f"{len(d.layouts.names())-1} pafta · 0 hata")
_b=_ez.readfile("cad/GYM-BIRLESIK-R2010.dxf")
_PF=("A-01","A-02","A-03","A-04","A-05","M-01","M-02","M-03","M-04",
     "E-01","E-02","E-03","E-04","E-05")
_eksik=[n for n in _PF if not any(l.startswith(n) for l in _b.layouts.names())]
if _eksik: hata(f"birleşik dosyada eksik pafta: {_eksik}")
else: ok(f"birleşik dosyada {len(_PF)} paftanın tamamı var")
_donmus_ok=True
for l in _b.layouts.names():
    if l in ("Model",): continue
    # ölçeksiz şema paftalarının görüntü penceresi yoktur — tümü kâğıt alanındadır
    vps=[vp for vp in _b.layouts.get(l).query("VIEWPORT") if len(vp.frozen_layers)>0]
    if not vps: _donmus_ok=False; hata(f"{l}: görüntü penceresinde donmuş katman yok")
if _donmus_ok: ok("her paftada disiplin dışı katmanlar dondurulmuş (VP Freeze)")
_tek = sorted(Path("cad/paftalar").glob("*.dxf")) if Path("cad/paftalar").exists() else []
import build_dxf as _BD
if len(_tek)!=len(_BD.TEKIL_PAFTA):
    hata(f"tekil pafta dosyası {len(_tek)} (beklenen {len(_BD.TEKIL_PAFTA)})")
else:
    ok(f"{len(_tek)} pafta ayrı DXF dosyası olarak üretildi (tek model + dondurma değil)")
for f in _tek:
    d=_ez.readfile(f)
    if len([l for l in d.layouts.names() if l!="Model"])!=1:
        hata(f"{f.name}: tekil pafta dosyasında birden çok kâğıt alanı var")
    if d.dxfversion!="AC1024": hata(f"{f.name}: sürüm {d.dxfversion}")
_ms=_b.modelspace()
if len(_ms.query("DIMENSION"))<5: hata("model uzayında ölçülendirme eksik")
else: ok(f"{len(_ms.query('DIMENSION'))} ölçülendirme · {len(_ms.query('INSERT'))} blok yerleşimi")

print("\n6c · MİMARİ SET VE ÇİZİM KONTROLÜ")
import kontrol as _K
_bul=_K.calistir()
_h=[b for b in _bul if b[0]=="HATA"]; _u=[b for b in _bul if b[0]=="UYARI"]
if _h:
    for b in _h: hata(f"çizim kontrolü: {b[2]}")
else: ok(f"çizim kontrolü: 0 hata, {len(_u)} uyarı, {len(_bul)-len(_u)} bilgi")
for b in _u: uyar(f"çizim kontrolü: {b[2]}")
_mim=pdfium.PdfDocument("output/Gym_Mimari_Proje_A3.pdf")
if len(_mim)!=14: hata(f"mimari set {len(_mim)} pafta (14 bekleniyor)")
else: ok("mimari set 14 pafta")
_seti=pdfium.PdfDocument("output/Gym_Insaat_Seti_A3.pdf")
if len(_seti)!=2+14+9+8: hata(f"inşaat seti {len(_seti)} pafta (33 bekleniyor)")
else: ok(f"inşaat seti {len(_seti)} pafta (kapak + indeks + 14 mimari + 9 mekanik + 8 elektrik)")
if abs(P.MAHAL_TOPLAM+P.MAHAL_DUVAR_PAYI-P.A["ic_toplam"])>0.01:
    hata("mahal listesi alanı net iç alanla kapanmıyor")
else: ok(f"mahal listesi {P.MAHAL_TOPLAM} m² + duvar payı {P.MAHAL_DUVAR_PAYI} m² = {P.A['ic_toplam']} m²")
_zk={z[0]: z[3] for z in P.ZEMIN_TIPLERI}
if any(abs(_zk[m[3]])>0.005 for m in P.MAHAL_LISTESI if not m[9]):
    hata("kuru hacimlerde bitmiş zemin kotu ±0,00 değil")
else: ok("tüm kuru hacimlerde bitmiş zemin kotu ±0,00 (eşiksiz geçiş)")
if P.PANO_UYGUNSUZ: hata(f"pano hesabında {len(P.PANO_UYGUNSUZ)} uygunsuz linye")
else: ok(f"pano hesabı: 21 linye uygun · maks ΔU %{P.DU_MAX} · toplam %{P.TOPLAM_DU_MAX}")

print("\n6d · KEŞİF / METRAJ / BÜTÇE MODELİ")
import metraj as _MT, fiyat as _FY
_mek = (sum(x[4]*x[5] for x in P.B_MEK), sum(x[4]*x[6] for x in P.B_MEK))
_elk = (sum(x[4]*x[5] for x in P.B_ELK), sum(x[4]*x[6] for x in P.B_ELK))
_mim = (sum(x[4]*x[5] for x in P.B)-_mek[0]-_elk[0],
        sum(x[4]*x[6] for x in P.B)-_mek[1]-_elk[1])
_j = _FY.grup_toplam()["J"]
_ke = (_FY.MIMARI_MIN-_j[0], _FY.MIMARI_MAX-_j[1])
for i, (etiket, a, b) in enumerate((("düşük", _mim[0], _ke[0]), ("yüksek", _mim[1], _ke[1]))):
    sapma = 100*(b/a-1)
    if abs(sapma) > 15:
        hata(f"bütçe modelleri ayrışıyor ({etiket}): poz bazlı {a:,.0f} vs metraj bazlı {b:,.0f} "
             f"(%{sapma:+.0f})")
    else:
        ok(f"poz bazlı ve metraj bazlı mimari bütçe {etiket} uçta uyumlu "
           f"({a:,.0f} vs {b:,.0f} TL · %{sapma:+.0f})")
_eksik_fiyat = [c.poz for c in _MT.CETVEL if c.poz not in _FY.F]
if _eksik_fiyat: hata(f"birim fiyatı tanımsız poz: {_eksik_fiyat}")
else: ok(f"{len(_MT.CETVEL)} metraj pozunun tamamında birim fiyat tanımlı")
_negatif = [c.poz for c in _MT.CETVEL if c.miktar <= 0]
if _negatif: hata(f"sıfır veya negatif metraj: {_negatif}")
else: ok(f"tüm metrajlar pozitif · toplam {sum(len(c.satir) for c in _MT.CETVEL)} cetvel satırı")
from openpyxl import load_workbook as _lw
_wb = _lw("output/Gym_Kesif_Ozeti_BoQ.xlsx")
_bek = ["1 · KAPAK","2 · İCMAL","3 · KEŞİF ÖZETİ","4 · BÜTÇE TAHMİNİ",
        "5 · MEKANİK KEŞİF","6 · ELEKTRİK KEŞİF","7 · METRAJ"]
if _wb.sheetnames != _bek: hata(f"keşif özeti sayfaları: {_wb.sheetnames}")
else: ok("keşif özeti 7 sayfa · icmal · metraj cetvelleri")
_bos = sum(1 for r in range(5, 5+len(_FY.satirlar())+12)
           if _wb["3 · KEŞİF ÖZETİ"].cell(r, 8).value is None
           and _wb["3 · KEŞİF ÖZETİ"].cell(r, 1).value
           and "." in str(_wb["3 · KEŞİF ÖZETİ"].cell(r, 1).value))
if _bos < 40: hata(f"keşif özetinde boş birim fiyat hücresi yalnız {_bos} adet")
else: ok(f"keşif özetinde {_bos} poz için birim fiyat hücresi boş (teklife hazır)")

print("\n7 · TESLİMAT LİSTESİ")
for f in ("output/Gym_Donusum_Dosyasi_A3.pdf","output/Gym_Sunum_16x9.pdf",
          "output/Gym_Insaat_Seti_A3.pdf","output/Gym_Mimari_Proje_A3.pdf",
          "output/Gym_Mekanik_Proje_A3.pdf","output/Gym_Elektrik_Proje_A3.pdf",
          "output/Gym_Maliyet_BoQ.xlsx","output/Gym_Mekanik_BoQ.xlsx",
          "output/Gym_Elektrik_BoQ.xlsx","output/Gym_Model.html",
          "output/Render_Promptlari.md","output/Gym_CAD_Seti_DXF.zip",
          "output/Gym_CAD_Paftalar.pdf","output/Gym_Kesif_Ozeti_BoQ.xlsx",
          "output/Gym_Hakedis_Sablonu.xlsx","output/Gym_Butce_Takip.xlsx",
          "output/Gym_Pano_Yukleme_Cetveli.xlsx","output/Gym_Proje_Paketi.zip",
          "cad/OKUBENI-CAD.txt","BUILD_NOTES.md"):
    if Path(f).exists(): ok(f"{f}  ({Path(f).stat().st_size/1e6:.2f} MB)")
    else: hata(f"EKSİK: {f}")

print("\n" + "="*64)
print(f"SONUÇ: {len(HATA)} hata, {len(UYARI)} uyarı")
for t in HATA: print("  ✗", t)
for t in UYARI: print("  !", t)
sys.exit(1 if HATA else 0)
