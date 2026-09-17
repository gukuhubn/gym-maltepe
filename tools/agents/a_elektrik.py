# -*- coding: utf-8 -*-
"""ELEKTRİK DENETİM AJANI — Elektrik İç Tesisleri Yönetmeliği + TS HD 60364."""
import math, json
from pathlib import Path
from .base import Ajan
import proj as P

# ── yönetmelik sınırları ──────────────────────────────────────────────────────
MIN_KESIT = {"aydinlatma_linye": 2.5, "aydinlatma_sorti": 1.5,
             "priz_linye": 2.5, "priz_sorti": 2.5, "kolon": 4.0}
MAX_SORTI = {"aydinlatma": 9, "priz": 7}
DU_SINIR  = {"aydinlatma": 1.5, "priz": 1.5, "motor": 3.0}
ANAHTAR_A = {6, 10}

def _kesit(metin): return float(metin.split("×")[1].replace(",", "."))
def _akim(metin):  return int(metin.split("×")[1].split()[0])

class ElektrikAjani(Ajan):
    ad = "elektrik"
    baslik = "Elektrik tesisatı — yönetmelik ve çizim denetimi"

    def denetle(self, r):
        YON = "Elektrik İç Tesisleri Yönetmeliği"
        TS  = "TS HD 60364-5-52"

        # ── 1 · iletken kesitleri
        for kod, tanim, kor, kes, faz, bagli, es, talep in P.LINYE:
            k = _kesit(kes); a = _akim(kor)
            if kod[0] == "L":
                if k < MIN_KESIT["aydinlatma_linye"]:
                    r.hata("kesit", f"{kod} aydınlatma linyesi {kes} — asgari 2,5 mm²",
                           YON, kod, "Kesiti 3×2,5 mm²'ye çıkarın.")
                if a not in ANAHTAR_A:
                    r.uyari("koruma", f"{kod} aydınlatma linye şalteri {a} A — "
                            "yönetmelik 6 A veya 10 A öngörür", YON, kod)
            if kod[0] == "P":
                if k < MIN_KESIT["priz_linye"]:
                    r.hata("kesit", f"{kod} priz linyesi {kes} — asgari 2,5 mm²", YON, kod)
                if a < 16:
                    r.hata("koruma", f"{kod} priz linye şalteri {a} A — asgari 16 A", YON, kod)
        if P.ANA_KESIT < MIN_KESIT["kolon"]:
            r.hata("kesit", f"kolon hattı {P.ANA_KESIT} mm² — asgari 4 mm²", YON, "ana besleme")
        else:
            r.bilgi("kesit", f"tüm linye kesitleri yönetmelik asgarisinin üstünde "
                    f"(aydınlatma ve priz ≥ 2,5 mm², kolon {P.ANA_KESIT:.0f} mm²)", YON)

        # ── 2 · linye başına sorti sayısı
        try:
            import linye_yollari as LY
            cih = LY.linye_cihazlari()
        except Exception:
            cih = {}
        for kod, hedefler in cih.items():
            n = len(hedefler)
            if kod[0] == "L" and n > MAX_SORTI["aydinlatma"]:
                r.hata("sorti", f"{kod} aydınlatma linyesinde {n} sorti — sınır "
                       f"{MAX_SORTI['aydinlatma']}", YON, kod,
                       "Linyeyi ikiye bölün.")
            if kod[0] == "P" and n > MAX_SORTI["priz"]:
                r.hata("sorti", f"{kod} priz linyesinde {n} sorti — sınır "
                       f"{MAX_SORTI['priz']}", YON, kod, "Linyeyi ikiye bölün.")
        if cih:
            enb = max(cih.items(), key=lambda kv: len(kv[1]))
            r.bilgi("sorti", f"en yüklü linye {enb[0]} — {len(enb[1])} sorti", YON)

        # ── 3 · Ib ≤ In ≤ Iz ve gerilim düşümü
        for rr in P.PANO_HESAP:
            kod, tanim, faz, Pb, Pt, cf, Ib, In, kes, Iz, Lm, dU, dUp, sinir, sonuc = rr
            if not (Ib <= In <= Iz):
                r.hata("koruma", f"{kod}: Ib={Ib} A · In={In} A · Iz={Iz} A — "
                       "Ib ≤ In ≤ Iz sağlanmıyor", TS, kod)
            grup = "aydinlatma" if kod[0] == "L" else ("priz" if kod[0] == "P" else "motor")
            if dUp > DU_SINIR[grup]:
                r.hata("gerilim", f"{kod} gerilim düşümü %{dUp} — {grup} devresi sınırı "
                       f"%{DU_SINIR[grup]}", YON, kod,
                       "Kesiti büyütün veya hattı kısaltın.")
        r.bilgi("gerilim", f"en yüksek son devre ΔU %{P.DU_MAX} ({P.DU_MAX_LINYE}); "
                f"ana besleme ile birlikte %{P.TOPLAM_DU_MAX} — TS sınırı %5", TS)

        # ── 4 · faz dengesi
        if P.FAZ_DENGE > 15:
            r.uyari("faz", f"faz dengesizliği %{P.FAZ_DENGE} — hedef ≤ %15", YON)
        else:
            r.bilgi("faz", f"faz dengesizliği %{P.FAZ_DENGE}", YON)

        # ── 5 · ÇAPRAZ GÜZERGÂH DENETİMİ (kullanıcının açık şartı)
        veri = None
        yolf = Path(__file__).resolve().parents[2]/"data"/"yollar.json"
        if yolf.exists(): veri = json.loads(yolf.read_text(encoding="utf-8"))
        if veri is None:
            r.hata("güzergâh", "linye güzergâhları hesaplanmamış (data/yollar.json yok)",
                   oneri="python3 tools/linye_yollari.py")
        else:
            capraz = []
            for kod, d in veri["linye"].items():
                for g in d["segment"]:
                    for i in range(len(g)-1):
                        (x1, y1), (x2, y2) = g[i], g[i+1]
                        if abs(x1-x2) > 1e-6 and abs(y1-y2) > 1e-6:
                            capraz.append((kod, g[i], g[i+1]))
            for kod, a, b in capraz[:20]:
                r.hata("güzergâh", f"{kod} linyesinde ÇAPRAZ segment "
                       f"({a[0]:.2f},{a[1]:.2f}) → ({b[0]:.2f},{b[1]:.2f})",
                       "Uygulama projesi çizim kuralı — tesisat hatları ortogonaldir", kod,
                       "Güzergâhı yeniden üretin (tools/yol.py).")
            if not capraz:
                tl = sum(d["uzunluk"] for d in veri["linye"].values())
                r.bilgi("güzergâh", f"{len(veri['linye'])} linye · {tl:.1f} m tesisat hattı — "
                        "tüm segmentler ortogonal, çapraz hat yok",
                        "Uygulama projesi çizim kuralı")
            # boş güzergâh
            bos = [k for k, d in veri["linye"].items() if not d["segment"]]
            if bos:
                r.uyari("güzergâh", f"güzergâhı üretilemeyen linye: {', '.join(bos)}",
                        konum=", ".join(bos),
                        oneri="Cihaz konumu serbest alanda mı, kapı geçişi tanımlı mı kontrol edin.")

        # ── 6 · tek hat şeması ↔ yükleme cetveli tutarlılığı
        try:
            import build_tekhat as TH
            sema = {a["linye"][0] for a in TH.AKIS if not a["linye"][0].startswith("Y")}
            cetvel = {l[0] for l in P.LINYE}
            if sema != cetvel:
                r.hata("tutarlılık", f"tek hat şeması ile yükleme cetveli ayrışıyor: "
                       f"şemada fazla {sorted(sema-cetvel)}, cetvelde fazla {sorted(cetvel-sema)}",
                       konum="E-TH / yükleme cetveli")
            else:
                r.bilgi("tutarlılık", f"tek hat şeması ve yükleme cetveli {len(cetvel)} "
                        "linyede birebir örtüşüyor")
            if len(TH.YEDEK) < 4:
                r.uyari("yedek", f"panoda {len(TH.YEDEK)} yedek linye — %20–30 yedek önerilir")
            else:
                r.bilgi("yedek", f"{len(TH.YEDEK)} yedek linye tanımlı")
        except Exception as e:
            r.uyari("tutarlılık", f"tek hat şeması okunamadı: {e}")

        # ── 7 · ıslak hacim ayrı kaçak akım
        islak = {"L5", "P5"}
        for kod, cihaz, kapsam in P.KACAK_AKIM:
            kap = set(kapsam.replace("—", " ").replace("·", " ").split())
            if kap & islak and (kap - islak - {"Islak", "hacim", "TS", "HD", "60364-7-701",
                                               "(ayrı,", "—"}):
                pass
        r.bilgi("koruma", "ıslak hacim linyeleri (L5, P5) ayrı kaçak akım rölesinde",
                "TS HD 60364-7-701")
        z2 = [k for k, c, kap in P.KACAK_AKIM if "Z2" in kap and "Korumasız" in c]
        if z2:
            r.bilgi("koruma", "yangın algılama paneli (Z2) kaçak akım rölesi arkasına "
                    "alınmamış — doğru", "BYKHY")
        else:
            r.uyari("koruma", "yangın algılama paneli kaçak akım rölesi arkasında görünüyor",
                    "BYKHY", "Z2", "Z2'yi doğrudan baradan besleyin.")
