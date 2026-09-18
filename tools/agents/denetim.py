# -*- coding: utf-8 -*-
"""DENETİM KOŞUCUSU — tüm ajanları çalıştırır, konsol/JSON/PDF raporu üretir.

    python3 tools/agents/denetim.py            # tümü
    python3 tools/agents/denetim.py elektrik   # tek ajan
    python3 tools/agents/denetim.py --pdf      # PDF raporunu da bas
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT  = ROOT/"output"
DATA = ROOT/"data"

from agents.a_mimari      import MimariAjani
from agents.a_mekanik     import MekanikAjani
from agents.a_elektrik    import ElektrikAjani
from agents.a_standart    import StandartAjani
from agents.a_koordinasyon import KoordinasyonAjani
from agents.a_teslim      import TeslimAjani
from agents.a_pilot       import PilotAjani

AJANLAR = [MimariAjani, MekanikAjani, ElektrikAjani,
           StandartAjani, KoordinasyonAjani, PilotAjani, TeslimAjani]

RENK = {"HATA": "\033[31m", "UYARI": "\033[33m", "BİLGİ": "\033[90m",
        "VERİ EKSİK": "\033[36m", "UYGULANMAZ": "\033[35m"}
SIFIRLA = "\033[0m"
DURUM_RENK = {"RED": "\033[31m", "ŞARTLI": "\033[33m", "UYGUN": "\033[32m"}


def calistir(secim=None, sessiz=False):
    raporlar = []
    for A in AJANLAR:
        if secim and A.ad not in secim: continue
        raporlar.append(A().calistir())
    if not sessiz: yaz(raporlar)
    return raporlar


def yaz(raporlar):
    print("\n" + "═"*78)
    print("  PROJE DENETİM AJANLARI — otomatik kontrol raporu")
    print("═"*78)
    for r in raporlar:
        d = DURUM_RENK.get(r.durum, "")
        print(f"\n▸ {r.baslik}")
        print(f"  {d}{r.durum}{SIFIRLA}  ·  {r.n_hata} hata · {r.n_uyari} uyarı · "
              f"{r.n_bilgi} geçti · {r.n_eksik} veri eksik · {r.n_disi} uygulanmaz"
              f"  ·  {r.sure*1000:.0f} ms")
        _S = {"HATA":0,"UYARI":1,"VERİ EKSİK":2,"UYGULANMAZ":3,"BİLGİ":4}
        for b in sorted(r.bulgular, key=lambda b: _S[b.seviye]):
            c = RENK.get(b.seviye, "")
            im = {"HATA": "✗", "UYARI": "!", "BİLGİ": "·",
                  "VERİ EKSİK": "?", "UYGULANMAZ": "—"}[b.seviye]
            print(f"    {c}{im} [{b.kategori}] {b.mesaj}{SIFIRLA}")
            if b.dayanak: print(f"        dayanak: {b.dayanak}")
            if b.oneri:   print(f"        öneri  : {b.oneri}")
    h = sum(r.n_hata for r in raporlar); u = sum(r.n_uyari for r in raporlar)
    genel = "RED" if h else ("ŞARTLI" if u else "UYGUN")
    print("\n" + "═"*78)
    print(f"  GENEL SONUÇ: {DURUM_RENK[genel]}{genel}{SIFIRLA}  —  {h} hata · {u} uyarı · "
          f"{sum(r.n_bilgi for r in raporlar)} bilgi · {len(raporlar)} ajan")
    print("═"*78 + "\n")
    return genel


def json_yaz(raporlar, dosya=None):
    dosya = dosya or DATA/"denetim.json"
    dosya.parent.mkdir(parents=True, exist_ok=True)
    d = {"tarih": time.strftime("%Y-%m-%d %H:%M"),
         "genel": "RED" if sum(r.n_hata for r in raporlar) else
                  ("ŞARTLI" if sum(r.n_uyari for r in raporlar) else "UYGUN"),
         "ajanlar": [{"ad": r.ajan, "baslik": r.baslik, "durum": r.durum,
                      "sure_ms": round(r.sure*1000),
                      "bulgular": [b.__dict__ for b in r.bulgular]} for r in raporlar]}
    dosya.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    return dosya


def pdf_yaz(raporlar, dosya=None):
    """A3 yatay denetim raporu."""
    import helpers as h; h.register()
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A3, landscape
    from reportlab.lib.units import mm
    import proj as P
    dosya = dosya or OUT/"Gym_Denetim_Raporu.pdf"
    dosya.parent.mkdir(parents=True, exist_ok=True)
    W, H = landscape(A3)
    c = canvas.Canvas(str(dosya), pagesize=(W, H))
    SOL, SAG, UST, ALT = 18*mm, 18*mm, H-20*mm, 18*mm
    ikon = {"HATA": "■", "UYARI": "▲", "BİLGİ": "·",
            "VERİ EKSİK": "?", "UYGULANMAZ": "—"}
    renk = {"VERİ EKSİK": (0.10, 0.45, 0.55), "UYGULANMAZ": (0.45, 0.35, 0.60),
            "HATA": (0.78, 0.16, 0.13), "UYARI": (0.83, 0.58, 0.05),
            "BİLGİ": (0.42, 0.45, 0.48)}
    say = [1]

    def antet(baslik):
        c.setFillColorRGB(0.09, 0.11, 0.13)
        c.rect(0, H-16*mm, W, 16*mm, 0, 1)
        c.setFillColorRGB(1, 1, 1); c.setFont("DJB", 11)
        c.drawString(SOL, H-10.5*mm, "PROJE DENETİM RAPORU — otomatik kontrol ajanları")
        c.setFont("DJ", 8)
        c.drawRightString(W-SAG, H-10.5*mm,
                          f"{P.PROJE_ADI if hasattr(P,'PROJE_ADI') else 'GYM MALTEPE'} · "
                          f"{P.REV} · {P.TARIH} · sayfa {say[0]}")
        c.setFillColorRGB(0, 0, 0)
        c.setFont("DJB", 9); c.drawString(SOL, H-24*mm, baslik)
        return H-30*mm

    genel_h = sum(r.n_hata for r in raporlar)
    genel_u = sum(r.n_uyari for r in raporlar)
    genel = "RED" if genel_h else ("ŞARTLI" if genel_u else "UYGUN")

    y = antet("ÖZET")
    c.setFont("DJB", 8)
    bas = ["AJAN", "KAPSAM", "DURUM", "HATA", "UYARI", "BİLGİ", "SÜRE"]
    gen = [26*mm, 118*mm, 22*mm, 16*mm, 18*mm, 18*mm, 18*mm]
    x = SOL
    c.setFillColorRGB(0.92, 0.93, 0.94); c.rect(SOL, y-1.5*mm, sum(gen), 6*mm, 0, 1)
    c.setFillColorRGB(0, 0, 0)
    for b, g in zip(bas, gen): c.drawString(x+1.5*mm, y+0.5*mm, b); x += g
    y -= 7*mm
    c.setFont("DJ", 8)
    for r in raporlar:
        x = SOL
        for v, g in zip([r.ajan, r.baslik, r.durum, r.n_hata, r.n_uyari, r.n_bilgi,
                         f"{r.sure*1000:.0f} ms"], gen):
            if v == r.durum:
                c.setFillColorRGB(*{"RED": (0.78,0.16,0.13), "ŞARTLI": (0.83,0.58,0.05),
                                    "UYGUN": (0.11,0.49,0.30)}[r.durum])
                c.setFont("DJB", 8)
            c.drawString(x+1.5*mm, y, str(v))
            c.setFillColorRGB(0, 0, 0); c.setFont("DJ", 8)
            x += g
        y -= 5.4*mm
    y -= 4*mm
    c.setFont("DJB", 10)
    c.setFillColorRGB(*{"RED": (0.78,0.16,0.13), "ŞARTLI": (0.83,0.58,0.05),
                        "UYGUN": (0.11,0.49,0.30)}[genel])
    c.drawString(SOL, y, f"GENEL SONUÇ: {genel}  —  {genel_h} hata · {genel_u} uyarı")
    c.setFillColorRGB(0, 0, 0); c.setFont("DJ", 7.5)
    y -= 6*mm
    for satir in ("RED    — en az bir hata var; pafta imalata verilmez.",
                  "ŞARTLI — hata yok, uyarılar şantiye şefince değerlendirilmeli.",
                  "UYGUN  — otomatik denetimden geçti; mühendis onayı ayrıca gerekir."):
        c.drawString(SOL, y, satir); y -= 4.2*mm

    for r in raporlar:
        c.showPage(); say[0] += 1
        y = antet(f"{r.baslik}  —  {r.durum}")
        c.setFont("DJ", 7.5)
        for b in sorted(r.bulgular,
                        key=lambda b: {"HATA":0,"UYARI":1,"VERİ EKSİK":2,
                                       "UYGULANMAZ":3,"BİLGİ":4}[b.seviye]):
            satirlar = [f"{ikon[b.seviye]}  [{b.kategori}]  {b.mesaj}"]
            if b.dayanak: satirlar.append(f"      dayanak: {b.dayanak}")
            if b.konum:   satirlar.append(f"      konum  : {b.konum}")
            if b.oneri:   satirlar.append(f"      öneri  : {b.oneri}")
            gerek = len(satirlar)*4.2*mm
            if y - gerek < ALT:
                c.showPage(); say[0] += 1; y = antet(f"{r.baslik} (devam)")
                c.setFont("DJ", 7.5)
            c.setFillColorRGB(*renk[b.seviye])
            for i, s in enumerate(satirlar):
                if i: c.setFillColorRGB(0.45, 0.47, 0.50)
                c.drawString(SOL, y, s[:240]); y -= 4.2*mm
            c.setFillColorRGB(0, 0, 0)
            y -= 0.8*mm
    c.save()
    return dosya


if __name__ == "__main__":
    arg = [a for a in sys.argv[1:] if not a.startswith("--")]
    rp = calistir(set(arg) if arg else None)
    j = json_yaz(rp); print(f"  → {j.relative_to(ROOT)}")
    if "--pdf" in sys.argv or not arg:
        p = pdf_yaz(rp); print(f"  → {p.relative_to(ROOT)}  "
                              f"({p.stat().st_size/1024:.0f} KB)")
    sys.exit(1 if sum(r.n_hata for r in rp) else 0)
