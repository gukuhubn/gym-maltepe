# -*- coding: utf-8 -*-
"""DENETİM AJANI ALTYAPISI — bulgu modeli ve ajan taban sınıfı."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dataclasses import dataclass, field

# Talimat §3: kural kontrolünde EN AZ DÖRT SONUÇ olmalı — geçti, kaldı,
# veri eksik, uygulanmaz. "Kontrol edilmemiş bir alanı geçti olarak gösterme."
# HATA = kaldı · BİLGİ = geçti · VERİ EKSİK ve UYGULANMAZ ayrı raporlanır.
HATA, UYARI, BILGI = "HATA", "UYARI", "BİLGİ"
VERI_EKSIK, UYGULANMAZ = "VERİ EKSİK", "UYGULANMAZ"
SIRA = {HATA: 0, UYARI: 1, VERI_EKSIK: 2, UYGULANMAZ: 3, BILGI: 4}

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
    def eksik(self, *a, **k): self.ekle(VERI_EKSIK, *a, **k)
    def disi(self, *a, **k):  self.ekle(UYGULANMAZ, *a, **k)
    @property
    def n_hata(self):  return sum(1 for b in self.bulgular if b.seviye == HATA)
    @property
    def n_uyari(self): return sum(1 for b in self.bulgular if b.seviye == UYARI)
    @property
    def n_bilgi(self): return sum(1 for b in self.bulgular if b.seviye == BILGI)
    @property
    def n_eksik(self): return sum(1 for b in self.bulgular if b.seviye == VERI_EKSIK)
    @property
    def n_disi(self):  return sum(1 for b in self.bulgular if b.seviye == UYGULANMAZ)
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
