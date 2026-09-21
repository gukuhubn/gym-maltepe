# -*- coding: utf-8 -*-
"""Enerji raporu grafikleri. Bütün sayılar tools/enerji.py'den okunur."""
import os, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import enerji as E

KOK = Path(__file__).resolve().parent.parent
CIK = KOK/"work"/"enerji"
CIK.mkdir(parents=True, exist_ok=True)

NAVY="#16273D"; COPPER="#B87333"; GREY="#8A8F98"; GREYL="#E7E9EC"
RED="#C8322B"; GREEN="#2E7D5B"; AMBER="#D79A1E"; BLUE="#2F6FB3"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":7.5,
                     "axes.edgecolor":GREY,"axes.labelcolor":NAVY,
                     "text.color":NAVY,"xtick.color":NAVY,"ytick.color":NAVY,
                     "axes.spines.top":False,"axes.spines.right":False})

def _bin(x, p=None):
    return f"{int(round(x)):,}".replace(",", ".")

def _kaydet(fig, ad):
    yol = CIK/ad
    fig.savefig(yol, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(yol)


def g_bagli_guc():
    """Bağlı gücün sınıflara dağılımı — pano yükleme cetvelinden."""
    d = [(E.SINIF_AD[s], g["kw"]) for s, g in E.SINIF.items() if s != "YEDEK"]
    d.sort(key=lambda t: t[1])
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    renk = [COPPER if v >= 20 else NAVY for _, v in d]
    ax.barh([a for a, _ in d], [v for _, v in d], color=renk, height=0.68)
    for i, (a, v) in enumerate(d):
        ax.text(v+2, i, f"{v:.1f} kW", va="center", fontsize=6.8, color=NAVY)
    ax.set_xlabel("bağlı güç (kW)")
    ax.set_xlim(0, max(v for _, v in d)*1.22)
    ax.set_title(f"Bağlı güç dağılımı · toplam {E.BAGLI_KW:.1f} kW "
                 f"(yedek hariç {E.AKTIF_KW:.1f} kW)",
                 fontsize=8.5, fontweight="bold", loc="left", pad=10)
    return _kaydet(fig, "g_bagli_guc.png")


def g_tuketim_pay():
    """Yıllık tüketimin sınıflara dağılımı — modelden."""
    d = [(E.SINIF_AD[s], v) for s, v in E.YILLIK.items() if v > 0]
    d.sort(key=lambda t: t[1])
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    tot = E.YILLIK_TOPLAM
    renk = [RED if v/tot >= 0.15 else (COPPER if v/tot >= 0.05 else NAVY)
            for _, v in d]
    ax.barh([a for a, _ in d], [v for _, v in d], color=renk, height=0.68)
    for i, (a, v) in enumerate(d):
        ax.text(v+tot*0.008, i, f"{_bin(v)}  (%{100*v/tot:.1f})",
                va="center", fontsize=6.8, color=NAVY)
    ax.set_xlabel("yıllık tüketim (kWh)")
    ax.set_xlim(0, max(v for _, v in d)*1.30)
    ax.xaxis.set_major_formatter(FuncFormatter(_bin))
    ax.set_title(f"Yıllık elektrik tüketimi · model toplamı {_bin(tot)} kWh",
                 fontsize=8.5, fontweight="bold", loc="left", pad=10)
    return _kaydet(fig, "g_tuketim_pay.png")


def g_aylik():
    """Aylık tüketim ve mevsimsel bileşenler."""
    fig, ax = plt.subplots(figsize=(7.2, 3.3))
    ana = ["HVAC", "HAVALANDIRMA", "MUTFAK_PISIR", "TERAS_ISITMA",
           "HAVA_PERDESI"]
    alt = [0.0]*12
    renkler = [RED, COPPER, AMBER, BLUE, GREEN]
    for s, r in zip(ana, renkler):
        v = E.TUKETIM[s]
        ax.bar(E.AY_AD, v, bottom=alt, color=r, label=E.SINIF_AD[s], width=0.7)
        alt = [a+b for a, b in zip(alt, v)]
    dig = [E.AYLIK_TOPLAM[i]-alt[i] for i in range(12)]
    ax.bar(E.AY_AD, dig, bottom=alt, color=GREYL, label="diğer", width=0.7)
    for i, t in enumerate(E.AYLIK_TOPLAM):
        ax.text(i, t+900, _bin(t), ha="center", fontsize=6, color=NAVY)
    ax.set_ylabel("kWh / ay")
    ax.yaxis.set_major_formatter(FuncFormatter(_bin))
    ax.set_ylim(0, max(E.AYLIK_TOPLAM)*1.16)
    ax.legend(fontsize=6.2, ncol=3, frameon=False, loc="upper center",
              bbox_to_anchor=(0.5, -0.16))
    ax.tick_params(axis="x", labelsize=6.4)
    ax.set_title("Aylık tüketim profili (model)", fontsize=8.5,
                 fontweight="bold", loc="left", pad=10)
    return _kaydet(fig, "g_aylik.png")


def g_onlem():
    """Önlemlerin kWh tasarrufu — yalnız modellenebilenler."""
    d = [(o["kod"]+"  "+o["ad"], E.onlem_tasarruf(o)) for o in E.ONLEM]
    d = [x for x in d if x[1] > 0]
    d.sort(key=lambda t: t[1])
    fig, ax = plt.subplots(figsize=(7.2, 3.9))
    ax.barh([a[:56] for a, _ in d], [v for _, v in d], color=GREEN, height=0.66)
    for i, (a, v) in enumerate(d):
        ax.text(v+600, i, f"{_bin(v)} kWh  (%{100*v/E.YILLIK_TOPLAM:.1f})",
                va="center", fontsize=6.6, color=NAVY)
    ax.set_xlabel("yıllık tasarruf (kWh)")
    ax.set_xlim(0, max(v for _, v in d)*1.42)
    ax.xaxis.set_major_formatter(FuncFormatter(_bin))
    ax.tick_params(axis="y", labelsize=6.3)
    ax.set_title("Modellenebilen tasarruf kalemleri "
                 f"· birleşik etki {_bin(E.teknik_toplam())} kWh/yıl "
                 f"(%{100*E.teknik_toplam()/E.YILLIK_TOPLAM:.1f})",
                 fontsize=8.5, fontweight="bold", loc="left", pad=10)
    return _kaydet(fig, "g_onlem.png")


def uret_hepsi():
    return {"bagli": g_bagli_guc(), "pay": g_tuketim_pay(),
            "aylik": g_aylik(), "onlem": g_onlem()}


if __name__ == "__main__":
    for k, v in uret_hepsi().items():
        print(k, "→", v)
