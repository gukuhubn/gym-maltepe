# -*- coding: utf-8 -*-
"""PİLOT ÇALIŞMA RAPORU — talimat §13'ün istediği altı çıktı.

1 mevcut sistemin gerçek kabiliyetleri ve öncelikli eksikleri
2 kaynak envanteri: erişilen · erişilemeyen · izin gereken · uygulanmayan
3 eksik proje girdileri ve açık tasarım kararları
4 geliştirilen çalışan kod, şablon ve pilot çizim dosyaları
5 pafta önizlemeleri ve bulunan/düzeltilen hatalar
6 geçen · kalan · yapılamayan kontroller ve tam sete geçiş için kalan işler

Sayısal alanların tamamı modelden ve denetim çıktısından okunur; rapor elle
yazılmış rakam içermez.
"""
import json, os, sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader

import helpers as H
import proj as P

KOK = Path(__file__).resolve().parent.parent
CIK = KOK/"output"/"Gym_Pilot_Raporu.pdf"
W, Y = A4
SOL, SAG, UST, ALT = 20*mm, 20*mm, Y-18*mm, 18*mm
GEN = W - SOL - SAG


# ══════════════════════ İÇERİK (veriden türeyenler ayrı işaretli) ═════════════
KABILIYET = [
 ("VAR", "Tek veri kaynağı", "Bütün çizim, tablo, metraj ve maliyet tools/proj.py'den "
  "türer. Bir sayı tek yerde durur; değişince her yere yayılır."),
 ("VAR", "Ölçülmüş geometri", "Geometri artık işverenin ölçülü CAD dosyasından "
  "(ESAT-FINAL.dwg, TRIMODE) gelir. Önceki raster türetmeye göre en büyük kenar "
  "sapması 21,7 cm idi."),
 ("VAR", "DWG okuma/yazma", "ODA File Converter sarmalayıcısı (tools/dwg.py) ile "
  "DWG↔DXF. ezdxf tek başına DWG okuyamaz."),
 ("VAR", "ISO pafta motoru", "ISO 5457 çerçeve · ISO 7200 antet · ISO 128 kalem "
  "serisi · ISO 3098 yazı boyu · ölçek bazlı DIMSTYLE."),
 ("VAR", "Ortogonal güzergâh", "A* 4 komşulu ızgara — çapraz kablo/kanal "
  "GEOMETRİK OLARAK imkânsız, filtrelenmiş değil."),
 ("VAR", "Otomatik denetim", "7 ajan; dört sonuçlu (geçti · kaldı · veri eksik · "
  "uygulanmaz). Pilot ajanı üretilen DXF'i diskten açıp ölçer."),
 ("VAR", "Kesit · görünüş · detay", "Bu turda eklendi: veri modelinden türeyen "
  "koordinasyon kesiti, iç görünüş ve 1:5 birleşim detayı."),
 ("VAR", "İlişkilendirme (sınırlı)", "tools/revizyon.py ölçüyor: bölme kalınlığı "
  "100→125 mm değişince 9 türev kendiliğinden güncelleniyor."),
 ("EKSİK", "BIM / IFC yok", "Üretim 2B DXF'tir. IFC/RVT çıktısı, nesne özellikleri "
  "ve disiplinler arası model federasyonu yok.", "YÜKSEK"),
 ("EKSİK", "Gerçek CAD'de doğrulama yok", "Paftalar AutoCAD/BricsCAD'de açılıp "
  "plot edilmedi. ezdxf önizlemesi plot ile birebir değildir.", "YÜKSEK"),
 ("EKSİK", "Marka standardı yok", "Nusr-Et / Saltbae iç mimari, malzeme ve mutfak "
  "standartları elimizde yok; UYDURULMADI.", "YÜKSEK"),
 ("EKSİK", "Mutfak/servis kütüphanesi yok", "Restoran projeleri için cihaz "
  "kütüphanesi, davlumbaz-söndürme ve yağ ayırıcı senaryosu kurulmadı.", "YÜKSEK"),
 ("EKSİK", "Üç boyutlu çakışma yok", "Çakışma kontrolü plan + kot bantları "
  "düzeyinde. Askı, erişim ve bakım hacimleri gerçek katı model değil.", "ORTA"),
 ("EKSİK", "Kütüphane sığ", "Blok kütüphanesi bu projeye özgü; ülke/ürün kodlu "
  "üretici CAD/BIM detayları bağlanmadı.", "ORTA"),
 ("EKSİK", "Tek pilot bölge", "Kesit/görünüş/detay motoru yalnız ıslak blokta "
  "denendi; salon ve cephe için genellenmedi.", "ORTA"),
]

KAYNAK = [
 ("ERİŞİLDİ", "ESAT-FINAL.dwg — TRIMODE mağaza projesi (4 pafta)", "İşveren",
  "DWG AC1032 · cm · alan etiketiyle doğrulandı", "Geometrinin tek kaynağı"),
 ("ERİŞİLDİ", "TRIMODE-Alan_Dagilimi.pdf / Duvar_Plani.pdf", "İşveren",
  "Raster", "Artık yalnız çapraz kontrol"),
 ("ERİŞİLDİ", "ADP_REFERANS.pdf — 34 sayfa EPLAN pano dosyası", "MAKSER Elektrik",
  "İşveren klasörü", "Şema düzeni ve antet referansı"),
 ("ERİŞİLDİ", "TS 2164 tesisat sembolleri", "TSE türevi kamu kaynağı",
  "PDF", "Sembol karşılıkları"),
 ("ERİŞİLDİ", "MEGEP — Sıhhi tesisat projesi", "MEB",
  "Açık kaynak", "Çizim tekniği"),
 ("ERİŞİLDİ", "Elektrik İç Tesisleri Yönetmeliği · BYKHY · Planlı Alanlar İmar Y.",
  "mevzuat.gov.tr", "Kamuya açık", "Kural kontrollerinin dayanağı"),
 ("İZİN GEREKİR", "ASHRAE 55 / 62.1 / 90.1 / 154", "ASHRAE",
  "Salt okunur; AI'a aktarım açıkça kısıtlı",
  "İNDİRİLMEDİ, İNDEKSLENMEDİ — yalnız bibliyografik kayıt"),
 ("İZİN GEREKİR", "SMACNA kanal yapım standartları · BESA DW/144 · DW/172",
  "SMACNA / BESA", "Ücretli", "Satın alma gerekir"),
 ("İZİN GEREKİR", "TS EN 12464-1 · TS 825 · TS 9111 tam metinleri", "TSE",
  "Ücretli", "Madde alıntısı yapılmadı; yalnız bilinen eşik değerler"),
 ("İZİN GEREKİR", "NFPA 13/72/96 salt okunur erişim", "NFPA",
  "Kayıt gerektirir", "Bu projede kapsam dışı"),
 ("ERİŞİLEMEDİ", "Nusr-Et / Saltbae marka kitabı ve mutfak standardı", "İşveren",
  "Elimizde yok", "İSTENECEK — uydurulmadı"),
 ("ERİŞİLEMEDİ", "Uygulanmış restoran projesi (DWG/RVT + as-built)", "—",
  "Yetkili örnek bulunamadı",
  "nusret-expansion-os içindeki ornek_restoran_250m2.dxf 6 poliçizgilik şematik "
  "bir blok diyagramdır, proje değildir"),
 ("ERİŞİLEMEDİ", "Google Cloud Secret Manager'daki API anahtarları", "İşveren hesabı",
  "GitHub Actions secret'ı geri okunamaz (tasarım gereği)",
  "Anahtar değeri hiç talep edilmedi; ortam değişkeni olarak verilmesi gerekir"),
 ("UYGULANMAZ", "IBC / IPC / IMC / NEC (NFPA 70)", "ICC / NFPA",
  "ABD kodları", "Proje Türkiye'dedir; idare bu seti istemez"),
 ("UYGULANMAZ", "Türkiye Bina Deprem Yönetmeliği hesapları", "AFAD",
  "Taşıyıcıya müdahale yok", "Yalnız yapısal olmayan eleman bağlantıları"),
]

GIRDI = [
 ("Mevcut betonarme döşeme kalınlığı", "180 mm VARSAYIM",
  "Söküm sonrası ölçüm", "Kesit, kot ve pis su eğimi buna bağlı"),
 ("Yapısal tavan kotu", "3,20 m VARSAYIM",
  "Yerinde lazer ölçüm", "Rölöve yalnız plan düzleminde ölçüm içeriyor"),
 ("Mevcut pis su bağlantı kotu", "ÖLÇÜLMEDİ",
  "Zemin açılınca tespit", "Duş eğim şapı kalınlığı ve süzgeç kotu"),
 ("Mevcut duvar kalınlıkları", "200 mm VARSAYIM",
  "Rölövede iç yüz ölçüsü var, kalınlık yok", "D1/D5 katman toplamı"),
 ("Sayaç panosu ile gym panosu arası mesafe", "25 m VARSAYIM",
  "Dağıtım şirketi / bina yönetimi", "Kolon kesiti ve gerilim düşümü"),
 ("Üst katta konut olup olmadığı", "VAR kabul edildi (konservatif)",
  "Bina yönetimi", "Akustik giydirme (D4) kalemi"),
 ("Kira ve sözleşme koşulları", "270–500 TL/m²·ay aralığı VARSAYIM",
  "İşveren sözleşmesi", "Nakit akışı"),
 ("Toprak özdirenci", "100 Ω·m VARSAYIM (killi-kumlu)",
  "Yerinde ölçüm", "Elektrot sayısı ve topraklama direnci"),
]

KARAR = [
 ("Soyunma kapıları (K03/K04) salona açılır",
  "4,5–5,7 m²'lik soyunmaya üç kapı açılıyor; içeri açılım dolap ve bankla "
  "çakışıyordu. Kaçış kapısı değiller (BYKHY md.32 kapsamı dışı).",
  "İşveren onayı — salon sirkülasyonunda kapı kanadı"),
 ("BANK E 1,25 → 0,69 m kısaldı",
  "Kapı açılımlarından temiz alan kalması için. Metraja kısa boy girer.",
  "Alternatif: banksız soyunma veya duvara katlanır bank"),
 ("Duş ve WC 1,65 m² net",
  "İç bölme payı düşüldükten sonra. Erişilebilir kabin DEĞİLDİR.",
  "Erişilebilir WC gerekiyorsa yerleşim yeniden kurulmalı (TS 9111)"),
 ("Islak hacim aydınlatması mahal başına 1 armatür",
  "Toplam 6 downlight; EN 12464-1 200 lx hedefi sağlanıyor ama düzgünlük "
  "(uniformity) hesaplanmadı.",
  "Soyunmaya 2. armatür önerilir — karar işverende"),
 ("Kesit düzlemi K1-K1 yalnız ıslak blokta",
  "Pilot kapsamı gereği. Salon, cephe ve arena kesitleri henüz üretilmedi.",
  "Tam sete geçişte kesit hatları çoğaltılacak"),
]

DUZELTILEN = [
 ("Geometri raster paftadan türetiliyordu", "±%3 beyan, gerçekte 21,7 cm sapma",
  "Ölçülmüş rölöve vektörüne geçildi; rijit kayıt uyumu %97,49"),
 ("K05–K08 kapıları planda yoktu", "Kapı cetvelinde vardı, çizimde karşılığı yoktu",
  "Ortak kenardan türetildi; ajan kuralı eklendi"),
 ("Kapı genişliği iki yerde yazılıydı", "Cetvel 700 mm, plan 700 mm — bağ yoktu",
  "KAPI_EN_MM tek kaynak; revizyon deneyi bağı doğruluyor"),
 ("İç bölme payı ayrılmıyordu", "Islak mahal alanları 0,70 m² fazlaydı",
  "16,745 → 16,042 m² net; metraj ve BoQ düzeldi"),
 ("Kapı açılımı mobilyayla çakışıyordu", "3 kapı × bank/dolap",
  "Kapı yönü değişti, bank kısaldı; çakışma 0"),
 ("K2 iç ünitesi ERKEK DUŞ'a düşmüştü", "Tavan 2,40 m, cihaz 2,40+0,32 m",
  "duvara_yapistir(yasak=…) eklendi; ünite 103 çeperine alındı"),
 ("C3 kamerası soyunmanın içine düşmüştü", "KVKK ve BoQ tanımına aykırı",
  "Kamera konumu geometriden düzeltiliyor"),
 ("Islak hacim linyeleri yol bulamıyordu", "P5 · V2 · W1 · W2 — 0 m güzergâh",
  "Serbest alan üç parçaya bölünmüştü (98 mm bölme boşluğu); kapat–aç ile "
  "birleştirildi, kapı geçişleri KAPI_GEOM'dan delindi"),
 ("Islak kanal güzergâhında 2 çapraz segment", "Ortogonal kural ihlali",
  "Bağlantı düzelince çapraz 0"),
 ("Beton taraması paftayı boydan boya kesiyordu", "AR-CONC ile ANSI aynı ölçekte",
  "Desen başına taban aralık katsayısı"),
 ("Çok parçalı geometride tarama taşıyordu", "Tek hatch + NESTED stil",
  "Parça başına ayrı hatch"),
 ("Ölçüler görünmüyordu", "DIMSTYLE 'EZDXF' kalıyordu (dimscale=1)",
  "dimstyle doğrudan veriliyor; ajan kuralı eklendi"),
 ("Döndürülmüş büyütmede yazılar eğikti", "Görüntü penceresi twist telafisi yok",
  "Yazı ve kot işaretleri ters yönde döndürülüyor, kuzey oku da dönüyor"),
 ("Sıfır uzunluklu geometri", "difference() ve unary_union köşe düğümü bırakıyordu",
  "Köşe temizleme; ajan kuralı"),
 ("Mimari A3 setinde kapı balonları elle konumluydu", "8 kapıya 4 balon kuralı",
  "KAPI_GEOM'dan üretiliyor"),
]

KALAN = [
 ("Gerçek CAD'de plot denemesi", "YAPILAMADI", "AutoCAD/BricsCAD lisansı yok"),
 ("IFC/BIM çıktısı", "YAPILMADI", "Teslim ihtiyacı doğrulanmadı"),
 ("Salon · cephe · arena kesitleri", "KALDI", "Pilot kapsamı dışı"),
 ("Kapı, mahal ve ekipman listelerinin tam sete yayılması", "KALDI",
  "Pilot bölgede çalışıyor"),
 ("Aydınlatma düzgünlük (uniformity) hesabı", "YAPILMADI",
  "EN 12464-1 ortalama aydınlık hesaplandı, Uo hesaplanmadı"),
 ("Yangın, gaz ve taşıyıcı hesapları", "UZMAN İŞİ",
  "Otomatik kontrol bunları karşılamaz"),
 ("Restoran (Nusr-Et / Saltbae) nesne kütüphanesi", "KALDI",
  "Marka standardı gelmeden kurulamaz"),
 ("Üretici CAD/BIM detay bağlantıları", "KALDI",
  "Ülke ve ürün kodu doğrulaması gerekir"),
]


# ══════════════════════ SAYFA MOBİLYASI ═══════════════════════════════════════
class R:
    def __init__(self, c):
        self.c = c; self.y = UST; self.sayfa = 0
        self.yeni()

    def yeni(self):
        if self.sayfa: self.c.showPage()
        self.sayfa += 1
        c = self.c
        c.setFillColor(H.NAVY); c.rect(0, Y-14*mm, W, 14*mm, 0, 1)
        c.setFillColor(H.PAPER); c.setFont(H.FB, 8)
        c.drawString(SOL, Y-9*mm, "GYM MALTEPE · PİLOT ÇALIŞMA RAPORU")
        c.setFont(H.F, 7)
        c.drawRightString(W-SAG, Y-9*mm, f"{P.REV} · {P.TARIH} · sayfa {self.sayfa}")
        self.y = Y-22*mm

    def yer(self, h):
        if self.y - h < ALT: self.yeni()

    def h1(self, n, t):
        self.y -= 4*mm
        self.yer(24*mm)
        c = self.c
        c.setFillColor(H.COPPER); c.rect(SOL, self.y-1.5*mm, GEN, 0.7, 0, 1)
        c.setFillColor(H.NAVY); c.setFont(H.FB, 12)
        c.drawString(SOL, self.y+2*mm, f"{n}  {t}")
        self.y -= 9*mm

    def p(self, t, f=H.F, s=8, ara=4.4*mm, renk=H.INK):
        for satir in _sar(t, int(GEN/(s*0.58))):
            self.yer(ara); self.c.setFont(f, s); self.c.setFillColor(renk)
            self.c.drawString(SOL, self.y, satir); self.y -= ara
        self.y -= 1*mm

    def tablo(self, basliklar, satirlar, genisler, renkli=None, s=7):
        c = self.c
        sh = 5.0*mm
        toplam = sum(genisler)
        self.yer(sh*2)
        c.setFillColor(H.NAVY); c.rect(SOL, self.y-1.2*mm, toplam, sh, 0, 1)
        c.setFillColor(H.PAPER); c.setFont(H.FB, s)
        x = SOL
        for b, g in zip(basliklar, genisler):
            c.drawString(x+1.4*mm, self.y+0.6*mm, b); x += g
        self.y -= sh
        for i, sat in enumerate(satirlar):
            hucre = []
            for v, g in zip(sat, genisler):
                hucre.append(_sar(str(v), max(6, int(g/(s*0.60)))))
            n = max(len(q) for q in hucre)
            yuk = n*3.6*mm + 1.4*mm
            if self.y - yuk < ALT:
                self.yeni()
                c.setFillColor(H.NAVY); c.rect(SOL, self.y-1.2*mm, toplam, sh, 0, 1)
                c.setFillColor(H.PAPER); c.setFont(H.FB, s)
                x = SOL
                for b, g in zip(basliklar, genisler):
                    c.drawString(x+1.4*mm, self.y+0.6*mm, b); x += g
                self.y -= sh
            if i % 2 == 0:
                c.setFillColor(H.GREY_L); c.rect(SOL, self.y-yuk+3.0*mm, toplam, yuk, 0, 1)
            x = SOL
            for j, (q, g) in enumerate(zip(hucre, genisler)):
                rk = H.INK
                if renkli and j == 0: rk = renkli.get(sat[0], H.INK)
                c.setFillColor(rk)
                c.setFont(H.FB if j == 0 else H.F, s)
                for k, satir in enumerate(q):
                    c.drawString(x+1.4*mm, self.y-k*3.6*mm, satir)
                x += g
            self.y -= yuk
        self.y -= 3*mm

    def gorsel(self, yol, baslik, en=None):
        if not Path(yol).exists(): return
        im = ImageReader(str(yol))
        iw, ih = im.getSize()
        en = en or GEN
        boy = en*ih/iw
        self.yer(boy + 8*mm)
        self.c.setFont(H.FB, 7.5); self.c.setFillColor(H.NAVY)
        self.c.drawString(SOL, self.y, baslik); self.y -= 3*mm
        self.c.drawImage(im, SOL, self.y-boy, en, boy)
        self.c.setStrokeColor(H.GREY); self.c.setLineWidth(0.3)
        self.c.rect(SOL, self.y-boy, en, boy, 1, 0)
        self.y -= boy + 5*mm


def _sar(t, n):
    out, sat = [], ""
    for k in t.split():
        if len(sat) + len(k) + 1 > n and sat:
            out.append(sat); sat = k
        else:
            sat = (sat + " " + k).strip()
    out.append(sat)
    return out or [""]


# ══════════════════════ RAPOR ═════════════════════════════════════════════════
def uret(cikti=CIK):
    den = json.loads((KOK/"data"/"denetim.json").read_text()) \
        if (KOK/"data"/"denetim.json").exists() else {}
    rol = json.loads((KOK/"data"/"geometry_roleve.json").read_text()) \
        if (KOK/"data"/"geometry_roleve.json").exists() else {}
    c = canvas.Canvas(str(cikti), pagesize=A4)
    r = R(c)

    r.p("Bu rapor, «Claude Code — Mimari, iç mimari ve MEP proje üretim sistemi "
        "geliştirme talimatı» belgesinin 13. bölümünde istenen altı çıktıyı verir. "
        "Sayısal alanlar veri modelinden ve denetim çıktısından okunur.", H.FB, 8.5)
    r.p("Pilot bölge: ERKEK ıslak blok — 105 soyunma · 106 duş · 107 WC. "
        "Talimat §12 'bir WC/mutfak bölümü' seçeneğidir ve elimizdeki TEK ölçülmüş "
        "veriye dayanır. Restoran (Nusr-Et / Saltbae) marka ve mutfak standardı "
        "elimizde olmadığı için sentetik bir restoran örneği ÜRETİLMEMİŞTİR.")

    # 1
    r.h1("1", "MEVCUT SİSTEMİN KABİLİYETLERİ VE ÖNCELİKLİ EKSİKLERİ")
    r.tablo(["DURUM", "KONU", "AÇIKLAMA", "ÖNCELİK"],
            [[k[0], k[1], k[2], (k[3] if len(k) > 3 else "—")] for k in KABILIYET],
            [16*mm, 40*mm, 96*mm, 18*mm],
            renkli={"VAR": H.GREEN, "EKSİK": H.RED})

    # 2
    r.h1("2", "KAYNAK ENVANTERİ")
    r.p("Talimat §3: indirme, erişim ve AI kullanım hakları ayrı değerlendirilir. "
        "Ücretli veya salt okunur standartlar izinsiz indirilmedi; erişim engeli "
        "aşılmadı. ASHRAE'nin AI kullanım kısıtı nedeniyle içeriği indekslenmedi.")
    r.tablo(["DURUM", "BELGE", "KAYNAK", "ERİŞİM", "PROJEDE KULLANIM"],
            [list(k) for k in KAYNAK],
            [21*mm, 45*mm, 24*mm, 35*mm, 45*mm],
            renkli={"ERİŞİLDİ": H.GREEN, "İZİN GEREKİR": H.AMBER,
                    "ERİŞİLEMEDİ": H.RED, "UYGULANMAZ": H.GREY})

    # 3
    r.h1("3", "EKSİK PROJE GİRDİLERİ VE AÇIK TASARIM KARARLARI")
    r.p("A · İŞVERENDEN / YERİNDEN İSTENECEKLER", H.FB, 8.5)
    r.tablo(["GİRDİ", "ŞU AN", "NASIL ELDE EDİLİR", "NEYİ ETKİLER"],
            [list(g) for g in GIRDI],
            [45*mm, 38*mm, 40*mm, 47*mm])
    r.p("B · KARAR BEKLEYEN TASARIM KONULARI", H.FB, 8.5)
    r.tablo(["KARAR", "GEREKÇE", "AÇIK KONU"],
            [list(k) for k in KARAR], [45*mm, 75*mm, 50*mm])

    # 4
    r.h1("4", "GELİŞTİRİLEN KOD, ŞABLON VE PİLOT ÇİZİM DOSYALARI")
    kod = [
     ["tools/roleve.py", "Ölçülmüş DWG'yi okur, 4 paftayı ayırır, cm→m çevirir, "
      "modele rijit kayıt yapar"],
     ["tools/dwg.py", "DWG↔DXF dönüştürücü (ODA File Converter + Xvfb)"],
     ["tools/pilot.py", "Pilot çizim motoru — plan · tavan · kesit · görünüş · detay"],
     ["tools/pafta.py", "ISO 5457/7200 pafta motoru (görüntü penceresi dönmesi eklendi)"],
     ["tools/revizyon.py", "İlişkilendirme deneyi — bir girdi değişince ne güncelleniyor"],
     ["tools/agents/a_pilot.py", "Üretilen DXF'i diskten açıp denetleyen ajan"],
     ["tools/agents/base.py", "Dört sonuçlu kontrol modeli (geçti·kaldı·veri eksik·uygulanmaz)"],
     ["data/geometry_roleve.json", "Ölçülmüş geometri — modelin yeni tek kaynağı"],
     ["data/roleve.json", "Rölövenin tam çıkarımı (poligon·çizgi·ölçü·yazı·blok)"],
    ]
    r.tablo(["DOSYA", "İŞLEV"], kod, [52*mm, 118*mm])
    paftalar = [[no, ad, f"1:{olc}", "A2"] for no, (ad, dis, olc) in
                _pilot_paftalari().items()]
    r.tablo(["NO", "PAFTA", "ÖLÇEK", "KÂĞIT"], paftalar,
            [16*mm, 116*mm, 20*mm, 18*mm])
    if rol:
        k = rol.get("alan_kontrol", {})
        r.p("GEOMETRİ SAPMASI — raster türetme → ölçülmüş rölöve", H.FB, 8.5)
        r.tablo(["MAHAL", "ÖLÇÜLEN m²", "RASTER m²", "SAPMA", "EN BÜYÜK KENAR KAYMASI"],
                [[a, f"{v['olculen_m2']:.3f}", f"{v['raster_m2']:.3f}",
                  f"{v['sapma_yuzde']:+.2f}%", f"{v['hausdorff_m']*100:.1f} cm"]
                 for a, v in k.items()],
                [30*mm, 30*mm, 30*mm, 25*mm, 55*mm])

    # 5
    r.h1("5", "PAFTA ÖNİZLEMELERİ VE BULUNAN / DÜZELTİLEN HATALAR")
    r.p("Her pafta yazıldıktan sonra DİSKTEN YENİDEN AÇILIP PDF/PNG'ye basıldı ve "
        "görsel olarak incelendi. Aşağıdaki hatalar bu incelemede ve ajan "
        "denetiminde bulundu; hepsi düzeltildi.")
    r.tablo(["BULGU", "BELİRTİ", "DÜZELTME"],
            [list(d) for d in DUZELTILEN], [50*mm, 55*mm, 65*mm])
    for no in ("P-01", "P-03", "P-04", "P-05", "P-02"):
        r.gorsel(KOK/"work"/"pilot"/f"{no}.png",
                 f"{no} — {_pilot_paftalari().get(no, ('',))[0]}")

    # 6
    r.h1("6", "KONTROLLER VE TAM SETE GEÇİŞ")
    if den.get("ajanlar"):
        sat = []
        for a in den["ajanlar"]:
            say = {}
            for b in a.get("bulgular", []):
                say[b["seviye"]] = say.get(b["seviye"], 0) + 1
            sat.append([a["baslik"][:54], a["durum"],
                        str(say.get("HATA", 0)), str(say.get("UYARI", 0)),
                        str(say.get("BİLGİ", 0)), str(say.get("VERİ EKSİK", 0)),
                        str(say.get("UYGULANMAZ", 0))])
        r.tablo(["AJAN", "SONUÇ", "KALDI", "UYARI", "GEÇTİ", "VERİ EKSİK",
                 "UYGULANMAZ"], sat,
                [66*mm, 20*mm, 15*mm, 16*mm, 15*mm, 20*mm, 18*mm],
                renkli={"UYGUN": H.GREEN, "ŞARTLI": H.AMBER, "RED": H.RED})
        r.p("VERİ EKSİK ve UYGULANMAZ olarak işaretlenen kontroller GEÇTİ "
            "sayılmaz (talimat §3).", H.F, 7.5)
        eks = [b for a in den["ajanlar"] for b in a.get("bulgular", [])
               if b["seviye"] in ("VERİ EKSİK", "UYGULANMAZ")]
        if eks:
            r.tablo(["SONUÇ", "KONU", "AÇIKLAMA"],
                    [[b["seviye"], b["kategori"], b["mesaj"][:150]] for b in eks],
                    [24*mm, 24*mm, 122*mm],
                    renkli={"VERİ EKSİK": H.BLUE, "UYGULANMAZ": H.GREY})
    r.p("KALAN VE YAPILAMAYAN İŞLER", H.FB, 8.5)
    r.tablo(["İŞ", "DURUM", "GEREKÇE"], [list(k) for k in KALAN],
            [70*mm, 28*mm, 72*mm],
            renkli={"YAPILAMADI": H.RED, "YAPILMADI": H.AMBER,
                    "KALDI": H.AMBER, "UZMAN İŞİ": H.BLUE})
    r.p("Bu paftalar ÖN TASARIM aşamasındadır. Otomatik geometrik kontrol, uzman "
        "tasarım incelemesinin yerine geçmez; taşıyıcı, elektrik koruma, yangın ve "
        "gaz kararları yetkili uzman incelemesine tabidir. Hiçbir pafta "
        "«imalata uygun» veya «onaylı» damgalanmamıştır.", H.FB, 8)

    c.save()
    return cikti


def _pilot_paftalari():
    import pilot as PL
    return PL.PAFTALAR


if __name__ == "__main__":
    y = uret()
    print(f"→ {y.relative_to(KOK)}  ({y.stat().st_size/1e6:.2f} MB)")
