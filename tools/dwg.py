# -*- coding: utf-8 -*-
"""DWG ↔ DXF DÖNÜŞTÜRÜCÜ — ODA File Converter sarmalayıcısı.

ezdxf DWG okuyamaz. Bu modül, Open Design Alliance'ın ücretsiz
ODA File Converter'ını (AppImage, /opt/oda altında açılmış) kullanarak
DWG dosyalarını DXF'e çevirir ve tersini yapar.

ODA arayüz uygulamasıdır; başsız sunucuda çalışması için sanal ekran
(Xvfb) gerekir — `xvfb-run` ile sarmalanır.

Kurulum (bir kez, ağ erişimi gerektirir):
    curl -L -o oda.AppImage \\
      "https://www.opendesign.com/guestfiles/get?filename=ODAFileConverter_QT6_lnxX64_8.3dll_27.1.AppImage"
    chmod +x oda.AppImage && ./oda.AppImage --appimage-extract
    mv squashfs-root /opt/oda/
    apt-get install -y xvfb libxkbcommon-x11-0

Kullanım:
    python3 tools/dwg.py girdi.dwg                 # yanına .dxf yazar
    python3 tools/dwg.py girdi_klasoru/ cikti/     # toplu
"""
import os, shutil, subprocess, sys, tempfile
from pathlib import Path

ODA = Path("/opt/oda/squashfs-root/usr/bin/ODAFileConverter")
SURUM = {"2000": "ACAD2000", "2004": "ACAD2004", "2007": "ACAD2007",
         "2010": "ACAD2010", "2013": "ACAD2013", "2018": "ACAD2018"}


def kullanilabilir():
    return ODA.exists() and shutil.which("xvfb-run") is not None


def cevir(kaynak, hedef_klasor=None, surum="ACAD2018", bicim="DXF",
          alt_klasor=False, zaman_asimi=600):
    """DWG → DXF (veya tersi). `kaynak` dosya ya da klasör olabilir.

    Döner: üretilen dosyaların listesi.
    """
    if not kullanilabilir():
        raise RuntimeError(
            "ODA File Converter veya xvfb bulunamadı. Modül başlığındaki "
            "kurulum adımlarını uygulayın.")
    kaynak = Path(kaynak).resolve()
    tekil = kaynak.is_file()
    hedef = Path(hedef_klasor).resolve() if hedef_klasor else \
        (kaynak.parent if tekil else kaynak.parent/(kaynak.name+"_dxf"))
    hedef.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        gir = Path(td)/"in"; cik = Path(td)/"out"
        gir.mkdir(); cik.mkdir()
        if tekil:
            shutil.copy2(kaynak, gir/kaynak.name)
        else:
            for f in kaynak.iterdir():
                if f.suffix.lower() in (".dwg", ".dxf"):
                    shutil.copy2(f, gir/f.name)
        n_gir = len(list(gir.iterdir()))
        if not n_gir:
            return []
        cmd = ["xvfb-run", "-a", "--server-args=-screen 0 1280x1024x24",
               str(ODA), str(gir), str(cik), surum, bicim,
               "1" if alt_klasor else "0", "1"]
        subprocess.run(cmd, capture_output=True, timeout=zaman_asimi,
                       env={**os.environ, "QT_QPA_PLATFORM": "xcb"})
        uretilen = []
        for f in sorted(cik.rglob("*")):
            if f.is_file():
                son = hedef/f.name
                shutil.copy2(f, son)
                uretilen.append(son)
    return uretilen


def oku(dwg_yolu, sakla=None):
    """DWG'yi çevirip ezdxf belgesi olarak döndürür."""
    import ezdxf
    ciktilar = cevir(dwg_yolu, sakla or tempfile.mkdtemp())
    dxf = next((c for c in ciktilar if c.suffix.lower() == ".dxf"), None)
    if dxf is None:
        raise RuntimeError(f"dönüşüm çıktı vermedi: {dwg_yolu}")
    return ezdxf.readfile(dxf), dxf


def ozet(dxf_yolu):
    """Dönüştürülen dosyanın hızlı envanteri — dönüşüm doğrulaması için."""
    import ezdxf, collections
    d = ezdxf.readfile(dxf_yolu)
    msp = d.modelspace()
    say = collections.Counter(e.dxftype() for e in msp)
    return {
        "surum": d.dxfversion,
        "birim": d.header.get("$INSUNITS"),
        "katman": len(d.layers),
        "blok": len([b for b in d.blocks if not b.name.startswith("*")]),
        "layout": [l for l in d.layouts.names() if l != "Model"],
        "nesne": sum(say.values()),
        "dagilim": dict(say.most_common(10)),
        "extents": (tuple(round(v) for v in d.header.get("$EXTMIN", (0, 0, 0))[:2]),
                    tuple(round(v) for v in d.header.get("$EXTMAX", (0, 0, 0))[:2])),
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(0)
    kay = sys.argv[1]
    hed = sys.argv[2] if len(sys.argv) > 2 else None
    out = cevir(kay, hed)
    for f in out:
        print(f"  → {f}  ({f.stat().st_size/1024:.0f} KB)")
        if f.suffix.lower() == ".dxf":
            for k, v in ozet(f).items():
                print(f"      {k}: {v}")
