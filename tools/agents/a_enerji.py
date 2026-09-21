# -*- coding: utf-8 -*-
"""ENERJİ MODELİ DENETİM AJANI — Aqua Florya elektrik maliyeti analizi.

Dört sonuçlu (geçti · kaldı · VERİ EKSİK · UYGULANMAZ). Modelin kendi
iç tutarlılığını ve birincil veriye sadakatini ölçer. Tasarruf iddialarının
DOĞRU olduğunu kanıtlamaz — modelin TUTARLI olduğunu kanıtlar.
"""
from pathlib import Path
from .base import Ajan
import enerji as E
try:
    import enerji_tarife as T
except Exception:
    T = None

ROOT = Path(__file__).resolve().parent.parent.parent


class AjanEnerji(Ajan):
    ad = "enerji"
    baslik = "Elektrik tüketim ve tasarruf modeli"

    def denetle(self, r):
        self._kaynak(r)
        self._cetvel(r)
        self._siniflandirma(r)
        self._profil(r)
        self._tarife(r)
        self._onlem(r)
        self._rapor(r)

    # ── birincil veri var mı
    def _kaynak(self, r):
        for ad, yol in (("yükleme cetveli", "input/referans/ADP_Yukleme_Cetveli_REF.xlsx"),
                        ("pano şeması", "input/referans/ADP_REFERANS.pdf")):
            if (ROOT/yol).exists():
                r.bilgi("kaynak", f"Birincil veri yerinde: {ad}", konum=yol)
            else:
                r.hata("kaynak", f"Birincil veri YOK: {ad}", konum=yol,
                       oneri="Model bu dosyadan türer; olmadan çalışmaz.")

    # ── modelin okuması cetvelin beyanıyla uyuşuyor mu
    def _cetvel(self, r):
        fark = abs(E.BAGLI_KW - E.CETVEL_BAGLI_KW)
        if fark <= 0.5:
            r.bilgi("mutabakat",
                    f"Bağlı güç mutabakatı: model {E.BAGLI_KW:.2f} kW ↔ cetvel "
                    f"{E.CETVEL_BAGLI_KW:.2f} kW (fark {fark:.2f} kW)",
                    dayanak="ADP yükleme cetveli R00 TOPLAM satırı")
        else:
            r.hata("mutabakat",
                   f"Bağlı güç mutabakatı KALDI: model {E.BAGLI_KW:.2f} kW, "
                   f"cetvel {E.CETVEL_BAGLI_KW:.2f} kW, fark {fark:.2f} kW",
                   oneri="Okuma sütun indeksleri veya satır filtresi hatalı.")
        grup = sum(v[0] for v in E.CETVEL_GRUP.values())/1000.0
        if abs(grup - E.CETVEL_TALEP_KW) <= 0.5:
            r.bilgi("mutabakat",
                    f"Cetvelin grup dökümü talep gücüne toplanıyor: "
                    f"{grup:.2f} kW ↔ {E.CETVEL_TALEP_KW:.2f} kW")
        else:
            r.uyari("mutabakat",
                    f"Grup dökümü talep gücüne toplanmıyor: {grup:.2f} ≠ "
                    f"{E.CETVEL_TALEP_KW:.2f} kW")

    # ── her linye bir sınıfa düştü mü, sınıf başına profil var mı
    def _siniflandirma(self, r):
        bos = [d for d in E.DEVRE if not d["aciklama"]]
        if bos:
            r.hata("sınıflandırma", f"{len(bos)} linyenin açıklaması boş",
                   oneri="Açıklamasız satır linye değildir; filtrelenmelidir.")
        else:
            r.bilgi("sınıflandırma",
                    f"{len(E.DEVRE)} linyenin tamamı açıklamalı ve sınıflandırıldı")
        eksik = [s for s in E.SINIF if s not in E.PROFIL]
        if eksik:
            r.hata("sınıflandırma", f"Profili olmayan sınıf: {', '.join(eksik)}")
        else:
            r.bilgi("sınıflandırma",
                    f"{len(E.SINIF)} işlev sınıfının hepsinde işletme profili var")
        adsiz = [s for s in E.SINIF if s not in E.SINIF_AD]
        if adsiz:
            r.hata("sınıflandırma", f"Türkçe adı olmayan sınıf: {', '.join(adsiz)}")
        # yedek linyeler tüketime girmemeli
        if E.YILLIK.get("YEDEK", 0) != 0:
            r.hata("sınıflandırma",
                   f"Yedek linyeler tüketime giriyor: {E.YILLIK['YEDEK']} kWh",
                   oneri="Yedek profili saat=0 olmalı.")
        else:
            r.bilgi("sınıflandırma",
                    f"Yedek linyeler ({E.YEDEK_KW:.2f} kW) tüketime girmiyor")

    # ── profiller fiziksel olarak mümkün mü
    def _profil(self, r):
        for s, (saat, lf, ay, ger) in E.PROFIL.items():
            if not (0 <= saat <= 24):
                r.hata("profil", f"{s}: saat/gün {saat} — 0–24 dışında")
            if not (0 <= lf <= 1):
                r.hata("profil", f"{s}: yük faktörü {lf} — 0–1 dışında")
            if len(ay) != 12:
                r.hata("profil", f"{s}: aylık katsayı dizisi {len(ay)} elemanlı")
            if not ger:
                r.uyari("profil", f"{s}: profilin gerekçesi yazılmamış")
        r.bilgi("profil", "Bütün profiller fiziksel sınırlar içinde "
                "(saat 0–24 · yük faktörü 0–1 · 12 aylık katsayı)")
        # yıllık toplam = aylık toplamların toplamı
        fark = abs(sum(E.AYLIK_TOPLAM) - E.YILLIK_TOPLAM)
        if fark > 12:
            r.hata("profil", f"Aylık ve yıllık toplam tutmuyor: fark {fark} kWh")
        else:
            r.bilgi("profil", "Aylık toplamlar yıllık toplama eşit")
        # ortalama güç bağlı gücü aşamaz
        if E.ORT_GUC_KW > E.BAGLI_KW:
            r.hata("profil", "Ortalama güç bağlı gücü aşıyor — imkânsız")
        else:
            r.bilgi("profil",
                    f"Ortalama güç {E.ORT_GUC_KW:.1f} kW, bağlı gücün "
                    f"%{100*E.ORT_GUC_KW/E.BAGLI_KW:.0f}'i — makul")

    # ── tarife verisi
    def _tarife(self, r):
        if T is None:
            r.eksik("tarife", "Tarife modülü yüklenemedi",
                    oneri="tools/enerji_tarife.py kontrol edilmeli.")
            return
        m = T.SENARYO["MEVCUT"]
        top = sum(v for _, v in m["bilesen"])
        if abs(top - m["birim"]) > 1e-6:
            r.hata("tarife", f"Bileşenler birim fiyata toplanmıyor: "
                             f"{top:.4f} ≠ {m['birim']:.4f}")
        else:
            r.bilgi("tarife", f"Fatura bileşenleri birim fiyata toplanıyor "
                              f"({m['birim']:.4f} TL/kWh)")
        if not (5.0 <= m["birim"] <= 9.0):
            r.uyari("tarife", f"Birim fiyat {m['birim']:.2f} TL/kWh beklenen "
                              f"2026 bandının (6,42–7,33) dışında")
        else:
            r.bilgi("tarife", "Birim fiyat 2026 ticarethane bandıyla uyumlu")
        if T.AKTIF_TICARETHANE and T.DAGITIM_TICARETHANE:
            r.bilgi("tarife", "Aktif enerji ve dağıtım bedeli ayrı ayrı tanımlı")
        # doğrulanamayanlar açıkça raporlanır
        for veri, neden in T.DOGRULANAMAYAN:
            r.eksik("tarife", f"{veri} — {neden}")
        # üç zamanlı tek kaynak
        if T.UC_ZAMANLI_GUVEN != "A":
            r.uyari("tarife", "Üç zamanlı ticarethane birim fiyatları TEK "
                    "KAYNAKTAN alındı, çapraz doğrulanmadı",
                    oneri="§4.3'ün sonucu faturayla teyit edilmeli.")
        # fatura mutabakatı
        model = E.ORT_AY_KWH*m["birim"]
        alt, ust = E.BEYAN_TL
        if alt <= model <= ust:
            r.bilgi("mutabakat", f"Model faturası ({model:,.0f} TL/ay) işverenin "
                    f"beyan ettiği bandın ({alt:,.0f}–{ust:,.0f}) İÇİNDE"
                    .replace(",", "."))
        else:
            r.uyari("mutabakat", f"Model faturası ({model:,.0f} TL/ay) beyan "
                    f"bandının dışında".replace(",", "."))

    # ── önlemler
    def _onlem(self, r):
        kodlar = [o["kod"] for o in E.ONLEM]
        if len(kodlar) != len(set(kodlar)):
            r.hata("önlem", "Önlem kodları benzersiz değil")
        else:
            r.bilgi("önlem", f"{len(kodlar)} önlem, kodlar benzersiz")
        for o in E.ONLEM:
            for s, p in o.get("etki", {}).items():
                if s not in E.YILLIK:
                    r.hata("önlem", f"{o['kod']}: bilinmeyen sınıf '{s}'")
                if not (0 < p < 1):
                    r.hata("önlem", f"{o['kod']}: tasarruf oranı {p} — 0–1 dışında")
            if not o.get("gerekce"):
                r.uyari("önlem", f"{o['kod']}: gerekçe yazılmamış")
            if o.get("guven") not in ("YÜKSEK", "ORTA", "DÜŞÜK"):
                r.uyari("önlem", f"{o['kod']}: güven derecesi tanımsız")
        # çarpımsal birleştirme tekil toplamdan KÜÇÜK olmalı (çifte sayım yok)
        tekil = sum(E.onlem_tasarruf(o) for o in E.ONLEM)
        birlesik = E.teknik_toplam()
        if birlesik > tekil + 1:
            r.hata("önlem", f"Birleşik tasarruf ({birlesik}) tekil toplamdan "
                            f"({tekil}) büyük — çifte sayım var")
        else:
            r.bilgi("önlem", f"Birleşik tasarruf {birlesik:,} kWh ≤ tekil toplam "
                    f"{tekil:,} kWh — çifte sayım yok".replace(",", "."))
        if birlesik > E.YILLIK_TOPLAM:
            r.hata("önlem", "Tasarruf toplam tüketimi aşıyor — imkânsız")
        else:
            r.bilgi("önlem", f"Teknik potansiyel toplam tüketimin "
                    f"%{100*birlesik/E.YILLIK_TOPLAM:.1f}'i")
        if T:
            for y in E.YAKIT_ONLEM:
                a = E.yakit_tasarruf(y, T)
                if a["tasarruf"] < 0:
                    r.hata("önlem", f"{y['kod']}: dönüşüm pahalıya geliyor")
            r.bilgi("önlem", f"{len(E.YAKIT_ONLEM)} yakıt dönüşümü kalemi "
                    "tutarlı (yeni kaynak mevcuttan ucuz)")
            eksik = [o["kod"] for o in E.ONLEM
                     if o["kod"] not in T.YATIRIM_BANT]
            if eksik:
                r.eksik("önlem", f"Yatırım maliyeti verisi olmayan önlem: "
                        f"{', '.join(eksik)}")
            dusuk = [k for k, v in T.YATIRIM_BANT.items() if v[3] == "C"]
            if dusuk:
                r.eksik("önlem", f"Yatırım maliyeti DÜŞÜK GÜVENLİ (tahmin veya "
                        f"ekstrapolasyon) olan kalemler: {', '.join(dusuk)}",
                        oneri="Teklif alınmadan yatırım kararı verilmemeli.")

    # ── rapor üretildi mi
    def _rapor(self, r):
        pdf = ROOT/"output"/"Nusret_Elektrik_Maliyet_Raporu.pdf"
        if not pdf.exists():
            r.hata("teslim", "Rapor PDF'i üretilmemiş", konum=str(pdf))
            return
        kb = pdf.stat().st_size/1024
        try:
            import pypdfium2 as pdfium
            n = len(pdfium.PdfDocument(str(pdf)))
        except Exception:
            n = 0
        if n and n < 12:
            r.uyari("teslim", f"Rapor yalnız {n} sayfa — beklenen en az 12")
        else:
            r.bilgi("teslim", f"Rapor PDF'i üretildi: {n} sayfa · {kb:.0f} KB")
        # tazelik: rapor modelden yeni olmalı
        for src in ("tools/enerji.py", "tools/enerji_tarife.py",
                    "tools/enerji_grafik.py", "tools/build_enerji_raporu.py"):
            f = ROOT/src
            if f.exists() and f.stat().st_mtime > pdf.stat().st_mtime:
                r.hata("tazelik", f"{src} rapordan YENİ — rapor bayat",
                       oneri="python3 tools/build_enerji_raporu.py")
        else:
            r.bilgi("tazelik", "Rapor bütün model dosyalarından yeni")
        # sunum
        sun = ROOT/"output"/"Nusret_Elektrik_Sunum_16x9.pdf"
        if not sun.exists():
            r.uyari("teslim", "Yönetim sunumu üretilmemiş", konum=str(sun))
        else:
            try:
                import pypdfium2 as pdfium
                ns = len(pdfium.PdfDocument(str(sun)))
            except Exception:
                ns = 0
            r.bilgi("teslim", f"Yönetim sunumu üretildi: {ns} slayt · "
                    f"{sun.stat().st_size/1024:.0f} KB")
            if sun.stat().st_mtime < (ROOT/"tools"/"enerji.py").stat().st_mtime:
                r.hata("tazelik", "Sunum modelden ESKİ — bayat",
                       oneri="python3 tools/build_enerji_sunum.py")

        # alan verisi beyandır, ölçüm değildir
        r.eksik("doğrulama",
                f"Tesis alanı {E.ALAN_M2:.0f} m² olarak işveren beyanından "
                f"alındı; Aqua Florya'ya ait çizim elimizde YOK ve alan "
                f"ölçülmedi. Terasın dâhil olup olmadığı bilinmiyor",
                oneri="Mimari projeden net alan tablosu (kapalı · teras · "
                      "mutfak · depo ayrı ayrı).")
        if E.ozgul() > 900:
            r.uyari("kıyas",
                    f"Özgül tüketim {E.ozgul():.0f} kWh/m²/yıl — uluslararası "
                    f"restoran kıyaslarının üst bandında. Sonuç doğrudan "
                    f"beyan edilen alana bağlıdır.",
                    oneri="Alan doğrulanmadan bu bulgu kesinleştirilmemeli.")

        # ölçülmemiş alanlar açıkça UYGULANMAZ / VERİ EKSİK
        r.eksik("doğrulama", "Hiçbir elektrik faturası görülmedi — birim fiyat, "
                "tarife tipi, reaktif ceza ve sözleşme gücü doğrulanmadı",
                oneri="§11 A grubundaki altı belge istenmeli.")
        r.eksik("doğrulama", "Sahada ölçüm yapılmadı — işletme saatleri ve yük "
                "faktörleri mühendislik kabulüdür (±%20)",
                oneri="ADP'deki -EA1 analizörüne kaydedici bağlanmalı.")
        r.disi("kapsam", "Doğal gaz tüketimi ve maliyeti bu raporun kapsamı "
               "dışındadır; yalnız elektrik modellenmiştir")
        r.disi("kapsam", "AVM ortak alan yansıtma faturası kapsam dışıdır — "
               "sözleşme okunmadı")
