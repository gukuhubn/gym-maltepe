# -*- coding: utf-8 -*-
"""TEK DOSYA TESLİM — tüm paftalar tek PDF'te.

İçerik:
    00      Kapak ve pafta indeksi (A1)
    A-01…05 Mimari uygulama paftaları (A1, 1:50)
    M-01…04 Mekanik tesisat paftaları (A1, 1:50)
    E-01…05 Elektrik paftaları (A1, 1:50)
    ADP-01…12 ADP çok hatlı şematik diyagram seti (A3, ölçeksiz)

Kâğıt boyutu setin içinde değişir (A1 planlar, A3 şemalar) — bu, gerçek
proje setlerinin standart pratiğidir.
"""
import sys, os, types
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
for _m in ("cryptography", "cryptography.exceptions", "cryptography.hazmat"):
    sys.modules.setdefault(_m, types.ModuleType(_m))
from pathlib import Path
import proj as P, dxf_lib as X, build_dxf as BD, build_sema as BS, sema as S

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT/"output"; OUT.mkdir(exist_ok=True)

INDEKS = [
 ("BÖLÜM 1 — MİMARİ", None, None),
 ("A-01", "MİMARİ ALTLIK", "Mevcut durum · ölçü ve aks sistemi · 1:50"),
 ("A-02", "MİMARİ UYGULAMA PLANI", "Bölme duvarlar · kapılar · mahal no · 1:50"),
 ("A-03", "ZEMİN KAPLAMA PLANI", "Kaplama tipleri · kot · derz yönü · 1:50"),
 ("A-04", "TAVAN PLANI (RCP)", "Tavan tipleri · kot · MEP koordinasyonu · 1:50"),
 ("A-05", "YANGIN VE TAHLİYE PLANI", "Kaçış yolları · çıkışlar · söndürücü · 1:50"),
 ("BÖLÜM 2 — MEKANİK TESİSAT", None, None),
 ("M-01", "HAVALANDIRMA PLANI", "Kanal güzergâhı · menfez debileri · 1:50"),
 ("M-02", "İKLİMLENDİRME PLANI", "Split küme · bakır hat · drenaj · 1:50"),
 ("M-03", "SIHHİ TESİSAT PLANI", "Temiz su · sıcak su · pis su · 1:50"),
 ("M-04", "MEKANİK GENEL YERLEŞİM", "Disiplin genel yerleşimi · 1:50"),
 ("BÖLÜM 3 — ELEKTRİK", None, None),
 ("E-01", "AYDINLATMA PLANI", "Armatür · anahtar · aydınlatma linyeleri · 1:50"),
 ("E-02", "PRİZ VE KUVVET PLANI", "Priz · kuvvet linyeleri · cihazlar · 1:50"),
 ("E-03", "ZAYIF AKIM PLANI", "Veri · CCTV · ses · yangın algılama · 1:50"),
 ("E-04", "ELEKTRİK GENEL YERLEŞİM", "Disiplin genel yerleşimi · 1:50"),
 ("E-05", "TOPRAKLAMA PLANI", "Elektrot grubu · ATB · EPDB · 1:50"),
 ("BÖLÜM 4 — ADP ÇOK HATLI ŞEMA SETİ (A3)", None, None),
]


def _kapak_dxf():
    """Kapak + indeks paftası — A1, pafta motoruyla."""
    from pafta import Pafta, YZ, KAT_YAZI, KAT_ANTET, _t, _l
    from ezdxf.enums import TextEntityAlignment as TA
    doc = X.yeni_belge("kapak"); X.bloklari_kur(doc); BD.antet_blogu(doc)
    pf = Pafta(doc, "00", "PAFTA İNDEKSİ", "GENEL", boy="A1",
               proje=BD.PROJE_BILGI, ust_ad="Proje kapağı ve pafta listesi")
    pf.cerceve()
    pf.antet(olcek="—", tarih=P.TARIH, rev=P.REV.split()[-1],
             durum="ÖN TASARIM", muellif=BD.MUELLIF, sicil=BD.SICIL,
             cizen="CC", kontrol="—", onay="—", birim="milimetre (mm)",
             revizyonlar=BD.REVIZYONLAR, sonraki="A-01")
    psp = pf.psp
    x, y = pf.x0+16, pf.y1-22
    _t(psp, "MALTEPE / İDEALTEPE", (x, y), 14.0, KAT_YAZI, "GYM-B"); y -= 12
    _t(psp, "MOBİLYA MAĞAZASI → FONKSİYONEL ANTRENMAN STÜDYOSU",
       (x, y), 8.0, KAT_YAZI, "GYM-B"); y -= 8
    _t(psp, "UYGULAMA PROJESİ — MİMARİ · MEKANİK · ELEKTRİK",
       (x, y), 5.0, KAT_YAZI); y -= 14
    for k, v in (("Proje no", BD.PROJE_BILGI["no"]),
                 ("Yapı", BD.PROJE_BILGI["yapi"]),
                 ("İç alan", f"{P.A['ic_toplam']:.2f} m²".replace(".", ",")),
                 ("Tarih", P.TARIH), ("Revizyon", P.REV),
                 ("Pafta boyutu", "A1 (841×594) planlar · A3 (420×297) şemalar"),
                 ("Ölçek", "Planlar 1:50 · şemalar ölçeksiz"),
                 ("Standartlar", "TS EN ISO 5457 · TS EN ISO 7200 · ISO 128 · "
                                 "ISO 3098 · IEC 60617 · IEC 61439 · IEC 81346-2")):
        _t(psp, k, (x, y), 3.5, KAT_YAZI)
        _t(psp, v, (x+46, y), 3.5, KAT_YAZI, "GYM-B"); y -= 6.2
    y -= 8
    _t(psp, "PAFTA İNDEKSİ", (x, y), 7.0, KAT_YAZI, "GYM-B"); y -= 4
    _l(psp, (x, y), (pf.ax-10, y), KAT_ANTET, 50); y -= 7
    for no, ad, ack in INDEKS:
        if ad is None:
            y -= 2
            _t(psp, no, (x, y), 4.5, KAT_YAZI, "GYM-B"); y -= 6.4
            continue
        _t(psp, no, (x+4, y), 3.5, KAT_YAZI, "GYM-B")
        _t(psp, ad, (x+24, y), 3.5, KAT_YAZI)
        _t(psp, ack, (x+124, y), 2.5, KAT_YAZI)
        y -= 5.4
    for i in range(1, 13):
        _t(psp, f"ADP-{i:02d}", (x+4, y), 3.5, KAT_YAZI, "GYM-B")
        _t(psp, BS.sayfalar()[i-1][0], (x+24, y), 3.5, KAT_YAZI)
        y -= 5.4
    # notlar
    nx = pf.ax
    ny = pf.sag()[1]
    ny = pf.baslik(nx, ny, "OKUMA NOTLARI")
    for i, t in enumerate((
        "Bu set ön tasarım aşamasındadır; yerinde röleve alınmadan ve ruhsat "
        "alınmadan uygulama yapılamaz.",
        "Ölçü alınmaz — yazılı ölçüler geçerlidir. Tüm ölçüler milimetredir.",
        "Aks sistemi yapının kendi doğrultusuna kurulmuştur (kuzeye göre 8,0°).",
        "Elektrik linye güzergâhları ortogonaldir; çapraz hat yoktur.",
        "Aydınlatma linyelerinde B eğrili, priz ve motor linyelerinde C eğrili "
        "kesici kullanılır.",
        "Ana kaçak akım rölesi ana şalterle orantılıdır (4×32 A → 4×40 A "
        "300 mA S tipi).",
        "Yedek linyeler dâhil tüm son devreler 30 mA kaçak akım rölesi "
        "arkasındadır; yangın algılama paneli hariç.",
        "Mimari altlık tüm disiplin paftalarında ortaktır ve değiştirilmez.",
    ), 1):
        for j, par in enumerate(_sar(t, 60)):
            _t(psp, (f"{i}. " if j == 0 else "   ")+par, (nx, ny), 2.5,
               KAT_YAZI)
            ny -= 4.0
        ny -= 1.2
    if "Layout1" in doc.layouts: doc.layouts.delete("Layout1")
    return doc


def _sar(m, n):
    out, s = [], ""
    for k in str(m).split():
        if len(s)+len(k)+1 > n: out.append(s); s = k
        else: s = (s+" "+k).strip()
    if s: out.append(s)
    return out or [""]


def _layout_pdf(doc, ad, boy, hedef):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.addons.drawing import config as C
    import ezdxf.bbox
    W_, H_ = boy
    cfg = C.Configuration(background_policy=C.BackgroundPolicy.WHITE,
                          color_policy=C.ColorPolicy.COLOR,
                          circle_approximation_count=160, hatching_timeout=90.0)
    lay = doc.layouts.get(ad)
    fig = plt.figure(figsize=(W_/25.4, H_/25.4))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg,
             bbox_cache=ezdxf.bbox.Cache()).draw_layout(lay, finalize=True)
    ax.set_xlim(0, W_); ax.set_ylim(0, H_)
    ax.set_aspect("equal", adjustable="box")
    fig.set_size_inches(W_/25.4, H_/25.4)
    fig.savefig(hedef, facecolor="white"); plt.close(fig)


def build(cikti="output/GYM_MALTEPE_UYGULAMA_PROJESI.pdf"):
    from pypdf import PdfReader, PdfWriter
    gecici = ROOT/"output"/"_tek"
    gecici.mkdir(parents=True, exist_ok=True)
    parcalar = []
    # 1) kapak
    doc = _kapak_dxf()
    ad = [l for l in doc.layouts.names() if l != "Model"][0]
    f = gecici/"00_kapak.pdf"; _layout_pdf(doc, ad, (841, 594), f)
    parcalar.append(f)
    # 2) A1 planlar — her pafta kendi DXF dosyasından
    for no in BD.TEKIL_PAFTA:
        adx = BD.PAFTALAR[no][0].replace(" ", "_").replace("/", "-")
        src = ROOT/"cad"/"paftalar"/f"{no}_{adx}.dxf"
        if not src.exists(): continue
        import ezdxf
        d = ezdxf.readfile(src)
        lay = f"{no} {BD.PAFTALAR[no][0]}"
        f = gecici/f"{no}.pdf"; _layout_pdf(d, lay, (841, 594), f)
        parcalar.append(f)
    # 3) A3 şema seti
    import ezdxf
    d = ezdxf.readfile(ROOT/"cad"/"GYM-ADP-SEMA-R2010.dxf")
    for lay in sorted(l for l in d.layouts.names() if l != "Model"):
        f = gecici/f"ADP_{lay[:2]}.pdf"; _layout_pdf(d, lay, (S.W, S.H), f)
        parcalar.append(f)
    # 4) birleştir
    wr = PdfWriter()
    for f in parcalar:
        rd = PdfReader(str(f))
        for pg in rd.pages: wr.add_page(pg)
    yol = ROOT/cikti
    with open(yol, "wb") as fh: wr.write(fh)
    for f in parcalar: f.unlink()
    gecici.rmdir()
    print(f"  → {cikti}  ·  {len(wr.pages)} pafta · "
          f"{yol.stat().st_size/1e6:.2f} MB")
    return yol


if __name__ == "__main__":
    build()
