# -*- coding: utf-8 -*-
"""DENETİM AJANI ALTYAPISI — bulgu modeli ve ajan taban sınıfı."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dataclasses import dataclass, field

HATA, UYARI, BILGI = "HATA", "UYARI", "BİLGİ"
SIRA = {HATA: 0, UYARI: 1, BILGI: 2}

@dataclass
class Bulgu:
    seviye: str                  # HATA / UYARI / BİLGİ
    kategori: str                # kısa kod — "kesit", "güzergâh", "çakışma"…
    mesaj: str
    dayanak: str = ""            # yönetmelik / standart referansı
    konum: str = ""              # pafta / poz / linye
    oneri: str = ""              # ne yapılmalı

@dataclass
class Rapor:
    ajan: str
    baslik: str
    bulgular: list = field(default_factory=list)
    sure: float = 0.0
    def ekle(self, seviye, kategori, mesaj, dayanak="", konum="", oneri=""):
        self.bulgular.append(Bulgu(seviye, kategori, mesaj, dayanak, konum, oneri))
    def hata(self, *a, **k):  self.ekle(HATA, *a, **k)
    def uyari(self, *a, **k): self.ekle(UYARI, *a, **k)
    def bilgi(self, *a, **k): self.ekle(BILGI, *a, **k)
    @property
    def n_hata(self):  return sum(1 for b in self.bulgular if b.seviye == HATA)
    @property
    def n_uyari(self): return sum(1 for b in self.bulgular if b.seviye == UYARI)
    @property
    def n_bilgi(self): return sum(1 for b in self.bulgular if b.seviye == BILGI)
    @property
    def durum(self):
        return "RED" if self.n_hata else ("ŞARTLI" if self.n_uyari else "UYGUN")

class Ajan:
    """Her denetim ajanı bunu türetir ve `denetle(r)` yazar."""
    ad = "ajan"
    baslik = "Denetim"
    def calistir(self):
        r = Rapor(self.ad, self.baslik)
        t0 = time.time()
        try:
            self.denetle(r)
        except Exception as e:
            r.hata("ajan", f"{type(e).__name__}: {e}",
                   oneri="Ajan kodunu veya girdi verisini kontrol edin.")
        r.sure = time.time()-t0
        return r
    def denetle(self, r): raise NotImplementedError
