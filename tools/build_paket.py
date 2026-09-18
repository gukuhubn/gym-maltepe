# -*- coding: utf-8 -*-
"""TESLİM PAKETİ — referans projedeki klasör ve dosya adlandırma düzeninde.

Referans (AQUA FLORYA / SALTBAE) klasör yapısı:
   AS BUILT PROJESİ-(VOGELKOPP İNŞAAT)        → mimari dwg + as-built raporu
   AS BUILT PROJELERİ - MEKANİK (TOROS)       → mekanik dwg
   AS BUILT PROJESİ-ELEKTRİK (MAKSER)         → elektrik dwg + ADP/UDP pdf + yükleme cetveli
   ..._Butce.xlsx / ..._KESİN HAKEDİŞİ.xlsx   → bütçe ve hakediş

Dosya adı kodlaması referanstakiyle aynıdır:
   A_00_00_GF_00_1_01 (Zemin Kat Planı)
   disiplin _ yapı _ blok _ kat _ tip _ ölçek _ sıra   (pafta adı parantez içinde)
"""
import sys, os, shutil, zipfile
sys.path.insert(0, os.path.dirname(__file__))
from pathlib import Path
import proj as P

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT/"output"
PKT  = OUT/"paket"

# (hedef klasör, hedef dosya adı, kaynak)
DOSYALAR = [
 # ── 01 MİMARİ ────────────────────────────────────────────────────────────────
 ("01_MİMARİ", "A_00_00_GF_00_1_00 (Mimari Uygulama Seti).pdf",
  "output/Gym_Mimari_Proje_A3.pdf"),
 ("01_MİMARİ", "A_00_00_GF_00_1_01 (Uygulama · Zemin Döşeme · Tavan Planı).dxf",
  "cad/GYM-MIM-Uygulama-R2010.dxf"),
 ("01_MİMARİ", "MAHAL LİSTESİ VE İMALAT ŞARTNAMESİ.pdf", None),     # A-09 sayfası
 ("01_MİMARİ", "PROJE RAPORU.pdf", None),                            # üretilir
 # ── 02 MEKANİK ───────────────────────────────────────────────────────────────
 ("02_MEKANİK", "M_00_00_GF_00_1_00 (Mekanik Tesisat Projesi).pdf",
  "output/Gym_Mekanik_Proje_A3.pdf"),
 ("02_MEKANİK", "M_00_00_GF_00_1_01 (Mekanik Uygulama).dxf",
  "cad/GYM-MEK-Uygulama-R2010.dxf"),
 # ── 03 ELEKTRİK ──────────────────────────────────────────────────────────────
 ("03_ELEKTRİK", "E_00_00_GF_00_1_00 (Elektrik Tesisat Projesi).pdf",
  "output/Gym_Elektrik_Proje_A3.pdf"),
 ("03_ELEKTRİK", "E_00_00_GF_00_1_01 (Elektrik Uygulama).dxf",
  "cad/GYM-ELK-Uygulama-R2010.dxf"),
 ("03_ELEKTRİK", "ADP TEK HAT ŞEMASI (8 pafta).pdf", "output/Gym_ADP_Tek_Hat_Semasi.pdf"),
 ("03_ELEKTRİK", "E_00_00_GF_00_1_03 (ADP Tek Hat Şeması).dxf",
  "cad/paftalar/E-06_ADP_TEK_HAT_ŞEMASI.dxf"),
 ("03_ELEKTRİK", "E_00_00_GF_00_1_02 (Topraklama Planı).dxf",
  "cad/paftalar/E-05_TOPRAKLAMA_VE_POTANSİYEL_DENGELEME_PLANI.dxf"),
 ("03_ELEKTRİK", "ADP Yükleme Cetveli R00.xlsx",
  "output/Gym_Pano_Yukleme_Cetveli.xlsx"),
 # ── 04 BÜTÇE VE HAKEDİŞ ──────────────────────────────────────────────────────
 ("04_BÜTÇE VE HAKEDİŞ", f"{P.TARIH.replace(' ', '')}_Gym_Maltepe_Kesif_Ozeti_BoQ.xlsx",
  "output/Gym_Kesif_Ozeti_BoQ.xlsx"),
 ("04_BÜTÇE VE HAKEDİŞ", f"{P.TARIH.replace(' ', '')}_Gym_Maltepe_Butce.xlsx",
  "output/Gym_Butce_Takip.xlsx"),
 ("04_BÜTÇE VE HAKEDİŞ", "Gym_Maltepe_HAKEDİŞ ŞABLONU.xlsx",
  "output/Gym_Hakedis_Sablonu.xlsx"),
 # ── 05 BİRLEŞİK SET ──────────────────────────────────────────────────────────
 ("05_BİRLEŞİK SET", "GYM MALTEPE — İNŞAAT UYGULAMA SETİ (33 pafta).pdf",
  "output/Gym_Insaat_Seti_A3.pdf"),
 ("05_BİRLEŞİK SET", "GYM MALTEPE — CAD PAFTA ÖNİZLEMESİ (15 pafta · A1).pdf",
  "output/Gym_CAD_Paftalar.pdf"),
 ("05_BİRLEŞİK SET", "GYM-BIRLESIK-R2010.dxf", "cad/GYM-BIRLESIK-R2010.dxf"),
 ("05_BİRLEŞİK SET", "KATMAN-LISTESI.csv", "cad/KATMAN-LISTESI.csv"),
 ("05_BİRLEŞİK SET", "TEKİL PAFTALAR (15 × DXF).zip", None),
 ("05_BİRLEŞİK SET", "OTOMATİK DENETİM RAPORU.pdf", "output/Gym_Denetim_Raporu.pdf"),
 # ── 06 YATIRIM DOSYASI ───────────────────────────────────────────────────────
 ("06_YATIRIM DOSYASI", "GYM MALTEPE — DÖNÜŞÜM VE FİZİBİLİTE DOSYASI.pdf",
  "output/Gym_Donusum_Dosyasi_A3.pdf"),
 ("06_YATIRIM DOSYASI", "GYM MALTEPE — SUNUM (16x9).pdf", "output/Gym_Sunum_16x9.pdf"),
 ("06_YATIRIM DOSYASI", "GYM MALTEPE — 3B MODEL VE RENDER GALERİSİ.html",
  "output/Gym_Model.html"),
 ("06_YATIRIM DOSYASI", "GYM MALTEPE — ANA BoQ (111 poz).xlsx",
  "output/Gym_Maliyet_BoQ.xlsx"),
 ("02_MEKANİK", "Gym_Mekanik_BoQ.xlsx", "output/Gym_Mekanik_BoQ.xlsx"),
 ("03_ELEKTRİK", "Gym_Elektrik_BoQ.xlsx", "output/Gym_Elektrik_BoQ.xlsx"),
 ("05_BİRLEŞİK SET", "OKUBENI — CAD SETİ.txt", "cad/OKUBENI-CAD.txt"),
 ("00_OKUMA", "PROJE NOTLARI — VARSAYIMLAR VE DOĞRULANACAKLAR.md", "BUILD_NOTES.md"),
 ("00_OKUMA", "DEPO REHBERİ.md", "README.md"),
]

def _pdf_sayfa(kaynak, sayfalar, hedef):
    """PDF'ten belirli sayfaları ayıklar."""
    import types
    for _m in ("cryptography", "cryptography.exceptions", "cryptography.hazmat"):
        sys.modules.setdefault(_m, types.ModuleType(_m))
    from pypdf import PdfReader, PdfWriter
    rd = PdfReader(str(kaynak)); wr = PdfWriter()
    for i in sayfalar: wr.add_page(rd.pages[i])
    with open(hedef, "wb") as f: wr.write(f)

OKUBENI = f"""GYM MALTEPE / İDEALTEPE — PROJE VE BÜTÇE TESLİM PAKETİ
{P.PROJE}
{P.REV} · {P.TARIH}
================================================================================

Bu paket, işverenin AQUA FLORYA / SALTBAE projesindeki teslim düzeni örnek
alınarak hazırlanmıştır: disiplin bazlı klasörler, aynı dosya adı kodlaması,
aynı keşif özeti / metraj cetveli / hakediş ve pano yükleme cetveli formatları.

1 · KLASÖR YAPISI
--------------------------------------------------------------------------------
  01_MİMARİ              Mimari uygulama seti (14 pafta) · DXF · mahal listesi · rapor
  02_MEKANİK             Mekanik tesisat projesi (7 pafta) · DXF
  03_ELEKTRİK            Elektrik tesisat projesi (7 pafta) · DXF · ADP tek hat şeması
                         · ADP yükleme cetveli (referans formatında)
  04_BÜTÇE VE HAKEDİŞ    Keşif özeti + metraj cetvelleri · bütçe takibi · hakediş şablonu
  05_BİRLEŞİK SET        33 paftalık tek PDF · birleşik DXF · 14 tekil pafta DXF ·
                         katman listesi · otomatik denetim raporu
  06_YATIRIM DOSYASI     Fizibilite dosyası · sunum · 3B model

2 · DOSYA ADI KODLAMASI
--------------------------------------------------------------------------------
  A_00_00_GF_00_1_01 (Pafta Adı)
  │ │  │  │  │  │ └─ sıra no
  │ │  │  │  │  └─── ölçek grubu (1 = plan, 3 = kesit/görünüş)
  │ │  │  │  └────── kat kodu (GF = zemin kat)
  │ │  │  └───────── blok
  │ │  └──────────── yapı
  │ └─────────────── disiplin (A mimari · M mekanik · E elektrik)

3 · FORMAT
--------------------------------------------------------------------------------
  Paftalar : A3 yatay (420 × 297 mm), 1/1 ölçekte basılır
  Plan     : 1/75 · Kesit-görünüş : 1/50 · Detay : 1/10 – 1/1
  CAD      : DXF R2010 (AC1024), model uzayı MİLİMETRE ($INSUNITS = 4)
             AutoCAD / BricsCAD / ZWCAD / DraftSight doğrudan açar.
             DWG'ye çevirmek için: Farklı Kaydet → AutoCAD 2018 Çizim (*.dwg)

4 · BÜTÇE DOSYALARININ KULLANIMI
--------------------------------------------------------------------------------
  Keşif Özeti BoQ    : «3 · KEŞİF ÖZETİ» sayfasındaki SARI hücrelere birim fiyat
                       girilir; malzeme / işçilik / genel gider / kâr-risk ayrı
                       sütunlardadır. İcmal ve toplamlar canlı formülle hesaplanır.
                       «7 · METRAJ» sayfasında her pozun metraj cetveli satır satır
                       verilmiştir; kapı-pencere boşlukları MİNHA olarak düşülmüştür.
  Bütçe Takibi       : Sözleşmeler imzalandıkça SÖZLEŞME BEDELİ ve ÖDENEN sütunları
                       doldurulur; sapma yüzdesi otomatik hesaplanır.
  Hakediş Şablonu    : Her dönem «BU HAKEDİŞ %» veya poz bazında «BU HAKEDİŞ METRAJ»
                       doldurulur; kapak sayfası KDV, tevkifat ve avans mahsubuyla
                       ödenecek net tutarı verir.

5 · BİRİM FİYAT KAYNAĞI — ÖNEMLİ
--------------------------------------------------------------------------------
  Bütçe tahmini sütunları, işverenin kendi referans projesi olan
  AQUA FLORYA / SALTBAE (Vogelkopp İnşaat kesin hakedişi, 13.05.2025) gerçekleşen
  birim fiyatlarının Eylül 2026'ya ×1,40 ile eskale edilmesiyle kurulmuştur.

  Bu kalibrasyon sonucunda mimari imalat bütçesi, önceki revizyona (Rev C) göre
  yaklaşık 2,8 kat yükselmiştir. Rev C'deki birim fiyatlar piyasa gerçeğinin
  altındaydı; örneğin alçıpan bölme 663 TL/m² iken referans karşılığı 3.430 TL/m².

  Mekanik ve elektrik kalemleri, referans projenin kapsamı (restoran mutfağı, VRF,
  soğuk oda, 630 A abonelik) bu projeyle karşılaştırılabilir olmadığı için
  kalibrasyona dâhil edilmemiş, Rev C değerleriyle korunmuştur.

6 · SINIRLAR
--------------------------------------------------------------------------------
  Bu set MİMARİ + MEKANİK + ELEKTRİK UYGULAMA SETİDİR. Ruhsat başvurusu için proje
  müellifi mimar ve tesisat mühendislerince imzalanmış 1/50 onaylı takım ayrıca
  düzenlenecektir. Statik proje kapsam dışıdır; taşıyıcı sisteme müdahale yoktur.

  Yapısal döşeme altı kotu (+3,20), mevcut duvar kalınlığı (200 mm), mevcut şap üst
  kotu (−0,053) ve mevcut asma tavan varlığı VARSAYIMDIR. Söküm sonrası rölöve ile
  doğrulanacak; tüm paftalar, metrajlar ve bütçe tek kaynaktan (tools/proj.py)
  yeniden üretilecektir.

  Ön tasarım — yerinde doğrulanmadan ve ruhsat alınmadan uygulama yapılamaz.
"""

def build(cikti="output/Gym_Proje_Paketi.zip"):
    if PKT.exists(): shutil.rmtree(PKT)
    PKT.mkdir(parents=True)
    # ── türetilen dosyalar
    _pdf_sayfa(OUT/"Gym_Mimari_Proje_A3.pdf", [8],
               PKT/"__mahal.pdf")
    _pdf_sayfa(OUT/"Gym_Mimari_Proje_A3.pdf", [0],
               PKT/"__rapor.pdf")
    # tekil pafta DXF'leri ayrı bir zip olarak pakete girer
    _tek = ROOT/"cad"/"paftalar"
    _tekzip = PKT/"__tekil.zip"
    if _tek.exists():
        with zipfile.ZipFile(_tekzip, "w", zipfile.ZIP_DEFLATED) as _z:
            for f in sorted(_tek.glob("*.dxf")):
                _z.write(f, f"PAFTALAR/{f.name}")
    tureti = {"MAHAL LİSTESİ VE İMALAT ŞARTNAMESİ.pdf": PKT/"__mahal.pdf",
              "TEKİL PAFTALAR (15 × DXF).zip": _tekzip,
              "PROJE RAPORU.pdf": PKT/"__rapor.pdf"}
    n = 0
    for klasor, ad, kaynak in DOSYALAR:
        hedef = PKT/klasor; hedef.mkdir(parents=True, exist_ok=True)
        src = Path(tureti[ad]) if kaynak is None else ROOT/kaynak
        if not src.exists():
            print(f"  ! eksik: {src}"); continue
        shutil.copy2(src, hedef/ad); n += 1
    for t in tureti.values():
        if Path(t).exists(): Path(t).unlink()
    (PKT/"OKUBENI.txt").write_text(OKUBENI, encoding="utf-8")
    # renderlar
    rk = PKT/"06_YATIRIM DOSYASI"/"RENDER"
    rn = sorted((OUT/"render").glob("*.png")) if (OUT/"render").exists() else []
    if rn:
        rk.mkdir(parents=True, exist_ok=True)
        for f in rn: shutil.copy2(f, rk/f.name)
    with zipfile.ZipFile(cikti, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(PKT.rglob("*")):
            if f.is_file():
                z.write(f, f"Gym_Maltepe_Proje_Paketi/{f.relative_to(PKT)}")
    boyut = Path(cikti).stat().st_size/1e6
    print(f"→ {cikti}  ·  {n+1} dosya · 6 klasör · {boyut:.2f} MB")

if __name__ == "__main__":
    build()
