# -*- coding: utf-8 -*-
"""Enerji modeli denetimini çalıştır, sonucu data/denetim_enerji.json'a yaz."""
import json, os, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agents.a_enerji import AjanEnerji

KOK = Path(__file__).resolve().parent.parent


def main():
    r = AjanEnerji().calistir()
    d = {"durum": r.durum, "hata": r.n_hata, "uyari": r.n_uyari,
         "bilgi": r.n_bilgi, "eksik": r.n_eksik, "disi": r.n_disi,
         "uyari_metin": [b.mesaj for b in r.bulgular if b.seviye == "UYARI"],
         "hata_metin":  [b.mesaj for b in r.bulgular if b.seviye == "HATA"]}
    (KOK/"data").mkdir(exist_ok=True)
    (KOK/"data"/"denetim_enerji.json").write_text(
        json.dumps(d, ensure_ascii=False, indent=1))
    print(f"ENERJİ DENETİMİ · {r.durum} · geçti {r.n_bilgi} · kaldı {r.n_hata} "
          f"· şartlı {r.n_uyari} · VERİ EKSİK {r.n_eksik} · UYGULANMAZ {r.n_disi}")
    for b in r.bulgular:
        if b.seviye in ("HATA", "UYARI"):
            print(f"  {b.seviye:5s} {b.kategori:14s} {b.mesaj}")
    return 1 if r.n_hata else 0


if __name__ == "__main__":
    sys.exit(main())
