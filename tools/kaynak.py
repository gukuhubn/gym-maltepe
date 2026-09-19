# -*- coding: utf-8 -*-
"""KAYNAK KAYIT SİSTEMİ — talimat §3.

Her kaynak için tutulan alanlar (§3'te sayılanlar):
  kimlik · tam başlık · yayıncı · URL/dosya · ülke · disiplin · baskı yılı ·
  revizyon/ekler · erişim tarihi · yürürlük · projede uygulanma gerekçesi ·
  indirme/AI kullanım izni · doğrulama durumu

DURUM KODLARI
  ERİŞİLDİ      dosya elimizde, açıldı, okundu
  BİBLİYOGRAFİK yalnız künye kaydı — metin alınmadı
  İZİN YOK      açık kısıt var; içerik AI'a verilmedi
  ÜCRETLİ       satın alma gerekir
  ERİŞİLEMEDİ   teknik engel (sunucu/sertifika) — aşılmadı
  UYGULANMAZ    bu projenin kapsamı dışında

AI KULLANIM İZNİ, indirme izninden AYRI değerlendirilir. Bir belge serbestçe
görüntülenebiliyor olsa bile içeriğinin yapay zekâya verilmesi yasak olabilir;
ASHRAE bunun açık örneğidir ve kaydı aşağıda kendi ifadesiyle durur.
"""
from __future__ import annotations
import json
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
ERISIM = "2026-09-18"


def K(kimlik, baslik, yayinci, yer, ulke, disiplin, yil, durum, izin,
      gerekce, dogrulama, rev="—", yururluk="—", erisim=ERISIM, not_=""):
    return dict(kimlik=kimlik, baslik=baslik, yayinci=yayinci, yer=yer,
                ulke=ulke, disiplin=disiplin, yil=yil, rev=rev,
                erisim=erisim, yururluk=yururluk, gerekce=gerekce,
                izin=izin, durum=durum, dogrulama=dogrulama, not_=not_)


KAYNAKLAR = [
    # ── PROJE GİRDİLERİ ──────────────────────────────────────────────────
    K("PRJ-01", "ESAT-FINAL.dwg — TRIMODE mağaza projesi (4 pafta)", "TRIMODE (işveren mimarı)",
      "input/ESAT-FINAL.dwg", "TR", "mimari", "—", "ERİŞİLDİ", "işveren teslimi",
      "Projenin TEK ölçülmüş geometri kaynağı", "DOĞRULANDI — alan etiketi ↔ poligon ±0,01 m²",
      not_="Birim cm; DUVAR PLANI · YIKIM · ALAN DAĞILIM · YERLEŞİM paftaları"),
    K("PRJ-02", "TRIMODE-Alan_Dagilimi.pdf / Duvar_Plani.pdf", "TRIMODE", "input/",
      "TR", "mimari", "—", "ERİŞİLDİ", "işveren teslimi",
      "Artık yalnız çapraz kontrol — geometri PRJ-01'den gelir",
      "RASTER — ±%3, ölçüm değil"),
    K("PRJ-03", "ADP referans dosyası (34 sayfa EPLAN pano seti)", "MAKSER Elektrik",
      "input/referans/ADP_REFERANS.pdf", "TR", "elektrik", "—", "ERİŞİLDİ",
      "işveren klasörü", "Şema düzeni, antet ve sembol referansı",
      "DOĞRULANDI — çok hatlı şema düzeni buradan alındı"),

    # ── ÇİZİM STANDARDI (resmî) ──────────────────────────────────────────
    K("STD-01", "Mimari Proje Çizim ve Sunuş Standartları", "TMMOB Mimarlar Odası",
      "docs/kaynak/MIMARLAR_ODASI_CIZIM_SUNUS_STANDARTLARI.md", "TR",
      "mimari çizim", "—", "ERİŞİLDİ", "oda yayını, kamuya açık",
      "OFİS ÇİZİM STANDARDININ ANA KAYNAĞI — plan/kesit/görünüş/detay içeriği, "
      "ölçü çizgisi düzeni, doğrama etiketi, kot gösterimi, numaralandırma",
      "DOĞRULANDI — uygulama projesi, sistem detayı ve imalat detayı "
      "bölümleri verbatim alındı", erisim="2026-09-19"),
    K("STD-02", "Mimari Proje Çizim ve Sunuş Standartları (ders notu)",
      "İTÜ Mimarlık Fakültesi",
      "input/standart/ITU_Mimari_Proje_Cizim_Sunus_Standartlari.pdf", "TR",
      "mimari çizim", "—", "ERİŞİLDİ", "üniversite, kamuya açık",
      "STD-01'in ders düzeni", "DOĞRULANDI", erisim="2026-09-19"),
    K("STD-03", "Mimari Projelerin Hazırlanmasına İlişkin Teknik Şartname",
      "İller Bankası A.Ş.",
      "input/standart/ILBANK_Mimari_Projeler_Teknik_Sartname.pdf", "TR",
      "mimari çizim", "—", "ERİŞİLDİ", "kamu kurumu, kamuya açık",
      "Kamu işveren şartnamesi — pafta içeriği ve teslim kapsamı",
      "DOĞRULANDI", erisim="2026-09-19"),

    # ── ÇİZİM TEKNİĞİ (öğrenilen) ────────────────────────────────────────
    K("CZM-01", "Yapı Elemanları Ölçülendirme ve Tarama (İnşaat Teknolojisi modülü)",
      "T.C. Millî Eğitim Bakanlığı — MEGEP",
      "input/standart/MEGEP_Yapi_Elemanlari_Olculendirme_ve_Tarama.pdf",
      "TR", "mimari çizim", "—", "ERİŞİLDİ", "kamuya açık, serbest",
      "Malzeme tarama gösterimlerinin ve ÖLÇEĞE GÖRE İFADE ilkesinin kaynağı",
      "DOĞRULANDI — Tablo 2.1, 2.7, 2.8 ve Şekil 2.24–2.48 okundu",
      not_="tools/malzeme.py doğrudan buna dayanır"),
    K("CZM-02", "Alçı Levha ile Bölme Duvar (İnşaat Teknolojisi modülü)",
      "MEB — MEGEP", "input/standart/MEGEP_Alci_Levha_Bolme_Duvar.pdf",
      "TR", "mimari", "—", "ERİŞİLDİ", "kamuya açık, serbest",
      "Karkas duvarın YATAY KESİT gösterimi; aks aralığı ve C profil kesiti",
      "DOĞRULANDI — Şekil 1.3 ve Tablo 1.2 okundu"),
    K("CZM-03", "Alçı Uygulama Kılavuzu", "DALSAN Alçı",
      "input/standart/DALSAN_Alci_Uygulama.pdf", "TR", "mimari", "—",
      "ERİŞİLDİ", "üretici, kamuya açık", "Levha/profil ölçüleri ve uygulama sırası",
      "DOĞRULANDI"),
    K("CZM-04", "Duvar Hazırlığı (İnşaat Teknolojisi modülü)", "MEB — MEGEP",
      "input/standart/MEGEP_Duvar_Hazirligi.pdf", "TR", "mimari", "—",
      "ERİŞİLDİ", "kamuya açık, serbest", "Duvar örgü ve sıra ölçüleri",
      "DOĞRULANDI"),
    K("CZM-05", "TS 88 / ISO 128 — Teknik resim çizgi ve gösterim kuralları",
      "TSE / ISO", "—", "TR/INT", "genel çizim", "—", "ÜCRETLİ",
      "satın alma gerekir", "Çizgi tipi, kalem serisi ve kesit gösterimi",
      "DOĞRULANMADI — tam metin alınmadı; uygulanan kalem serisi "
      "(0,13–1,00) yaygın ISO 128 serisidir, madde alıntısı YAPILMADI"),

    # ── MEVZUAT (Türkiye — bu projenin BAĞLAYICI seti) ───────────────────
    K("MVZ-01", "Elektrik İç Tesisleri Yönetmeliği", "Resmî Gazete / mevzuat.gov.tr",
      "https://www.mevzuat.gov.tr/", "TR", "elektrik", "—", "ERİŞİLDİ",
      "kamuya açık, serbest", "Kaçak akım, kesici seçimi ve topraklama kuralları",
      "DOĞRULANDI — md.18 kaçak akım koruması uygulandı"),
    K("MVZ-02", "Elektrik İç Tesisleri Proje Hazırlama Yönetmeliği",
      "Resmî Gazete", "input/standart/Elektrik_Ic_Tesisleri_Proje_Hazirlama_Yonetmeligi.pdf",
      "TR", "elektrik", "—", "ERİŞİLDİ", "kamuya açık, serbest",
      "Proje içeriği ve pafta gerekleri", "DOĞRULANDI"),
    K("MVZ-03", "Elektrik Projesi Kontrol Formu", "TMMOB EMO",
      "input/standart/EMO_Elektrik_Projesi_Kontrol_Formu.pdf", "TR", "elektrik",
      "—", "ERİŞİLDİ", "oda yayını, kamuya açık",
      "Mesleki denetimde neye bakıldığının listesi — ajan kurallarına girdi",
      "DOĞRULANDI"),
    K("MVZ-04", "Binaların Yangından Korunması Hakkında Yönetmelik (BYKHY)",
      "Resmî Gazete", "https://www.mevzuat.gov.tr/", "TR", "yangın", "—",
      "ERİŞİLDİ", "kamuya açık, serbest",
      "Kaçış mesafesi (md.33) ve kapı net genişliği (md.32)",
      "DOĞRULANDI — ajan kurallarında kullanılıyor"),
    K("MVZ-05", "Planlı Alanlar İmar Yönetmeliği", "Resmî Gazete",
      "https://www.mevzuat.gov.tr/", "TR", "mimari", "—", "ERİŞİLDİ",
      "kamuya açık, serbest", "Net yükseklik (md.28)", "DOĞRULANDI"),
    K("MVZ-06", "TMMOB MMO Proje Hazırlama ve Mesleki Denetim Esasları",
      "TMMOB MMO", "input/standart/MMO_Proje_Hazirlama_Mesleki_Denetim_Esaslari.pdf",
      "TR", "mekanik", "—", "ERİŞİLDİ", "oda yayını, kamuya açık",
      "Mekanik proje teslim içeriği", "DOĞRULANDI"),

    # ── MESLEKİ KAYNAKLAR ────────────────────────────────────────────────
    K("MSL-01", "Havalandırma ve İklimlendirme Semineri", "TMMOB MMO İzmir Şubesi",
      "input/standart/MMO_Havalandirma_Semineri.pdf", "TR", "mekanik", "—",
      "ERİŞİLDİ", "oda yayını, kamuya açık",
      "Taze hava debisi ve kanal tasarımı yaklaşımı", "DOĞRULANDI"),
    K("MSL-02", "Sıhhi Tesisat Projesi (modül)", "MEB — MEGEP",
      "input/standart/MEGEP_Sihhi_Tesisat_Projesi.pdf", "TR", "mekanik", "—",
      "ERİŞİLDİ", "kamuya açık, serbest", "Sıhhi tesisat çizim tekniği",
      "DOĞRULANDI"),
    K("MSL-03", "Kuvvet Projeleri / Aydınlatma Projeleri (modüller)", "MEB — MEGEP",
      "input/standart/MEGEP_Kuvvet_Projeleri.pdf", "TR", "elektrik", "—",
      "ERİŞİLDİ", "kamuya açık, serbest",
      "Linye/sorti gösterimi ve pano çizelgesi düzeni", "DOĞRULANDI"),
    K("MSL-04", "TS 2164 tesisat sembolleri (türev yayın)", "TSE türevi",
      "input/standart/TS2164_Tesisat_Sembolleri.pdf", "TR", "mekanik", "—",
      "ERİŞİLDİ", "kamuya açık", "Sembol karşılıkları",
      "KISMİ — tam TSE metni değil, türev özet"),

    # ── ULUSLARARASI STANDARTLAR ─────────────────────────────────────────
    K("ULS-01", "HVAC Duct Construction Standards — Metal and Flexible, 2. baskı",
      "SMACNA (Public.Resource.Org üzerinden)",
      "input/standart/law_resource/SMACNA_Duct_1995.html", "US", "mekanik",
      "1995 (+Ek 1, 1997)", "ERİŞİLDİ",
      "SMACNA, şartname makamlarına imalat detaylarını çoğaltma için "
      "telifsiz izin verir; Public.Resource.Org 'hukuku bilme hakkı' "
      "temelinde yayımlar",
      "Kanal sac kalınlığı ve takviye çizelgeleri — KARŞILAŞTIRMA amaçlı",
      "DOĞRULANDI — 322 tablo indirildi",
      not_="ESKİ BASKI (güncel 4. baskı değil) ve ABD standardı. Bu projede "
           "BAĞLAYICI DEĞİLDİR; Türkiye'de kanal imalatı TS EN 1507 / "
           "TS EN 12237'ye tabidir. Yalnız çapraz kontrol için tutulur."),
    K("ULS-02", "ASHRAE 55 · 62.1 · 90.1 · 154", "ASHRAE", "ashrae.org",
      "US", "mekanik", "—", "İZİN YOK",
      "ASHRAE kendi ifadesiyle: «ASHRAE prohibits the entry of content from "
      "any ASHRAE publication or related ASHRAE intellectual property (IP) "
      "into any AI tool… creating derivative works of ASHRAE IP using AI is "
      "also prohibited without express written permission.»",
      "Konfor ve taze hava kriterleri için aday referanstı",
      "İÇERİK ALINMADI — yalnız bibliyografik kayıt. Yerine TS EN ve "
      "MMO kaynakları kullanıldı."),
    K("ULS-03", "SMACNA güncel 4. baskı · BESA DW/144 · DW/172", "SMACNA / BESA",
      "store.smacna.org · publications.thebesa.com", "US/UK", "mekanik", "—",
      "ÜCRETLİ", "satın alma gerekir",
      "Mutfak egzozu (DW/172) restoran projelerinde gerekli olabilir",
      "DOĞRULANMADI — satın alınmadı"),
    K("ULS-04", "NFPA 13 · 72 · 96 (free access)", "NFPA", "nfpa.org",
      "US", "yangın", "—", "BİBLİYOGRAFİK",
      "NFPA ücretsiz GÖRÜNTÜLEME sunar; kayıt gerektirir, indirme yoktur",
      "Bu projede kapsam dışı — sprinkler/mutfak söndürme yok",
      "DOĞRULANMADI — sayfa şartları otomatik okunamadı"),
    K("ULS-05", "TS EN 12464-1 · TS 825 · TS 9111 · TS EN 1507 tam metinleri",
      "TSE", "tse.org.tr", "TR", "çok disiplinli", "—", "ÜCRETLİ",
      "satın alma gerekir",
      "Aydınlatma, ısı yalıtımı, erişilebilirlik, kanal imalatı",
      "DOĞRULANMADI — madde alıntısı YAPILMADI; projede yalnız yaygın "
      "bilinen eşik değerler (200/300/500 lx gibi) kullanıldı ve bunlar "
      "'doğrulanacak' olarak işaretlendi"),
    K("ULS-06", "IBC · IPC · IMC · NEC (NFPA 70)", "ICC / NFPA", "codes.iccsafe.org",
      "US", "çok disiplinli", "—", "UYGULANMAZ", "—",
      "Proje Türkiye'dedir; idare bu seti istemez",
      "UYGULANMAZ — kapsam dışı"),

    # ── ERİŞİM ENGELİ ────────────────────────────────────────────────────
    K("ENG-01", "CADD — Bilgisayar Destekli Tasarım ve Çizim Düzenleme Usul ve Esasları",
      "T.C. Çevre ve Şehircilik Bakanlığı", "webdosya.csb.gov.tr", "TR",
      "CAD standardı", "2016", "ERİŞİLEMEDİ", "kamuya açık olmalı",
      "Kamu projelerinde katman ve pafta düzeni standardı",
      "ERİŞİLEMEDİ — sunucunun TLS sertifika zinciri eksik (sunucu tarafı "
      "sorunu). Engel AŞILMADI; işverenden kopya istenecek."),
]


def kayit(kimlik):
    return next((k for k in KAYNAKLAR if k["kimlik"] == kimlik), None)


def ozet():
    from collections import Counter
    return Counter(k["durum"] for k in KAYNAKLAR)


def yaz(yol=None):
    yol = Path(yol or KOK/"data"/"kaynaklar.json")
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(KAYNAKLAR, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    return yol


if __name__ == "__main__":
    import signal
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)      # `| head` ile sessiz bitsin
    print(f"KAYNAK ENVANTERİ — {len(KAYNAKLAR)} kayıt\n")
    for d, n in ozet().most_common():
        print(f"  {d:14s} {n}")
    print()
    for k in KAYNAKLAR:
        print(f"  [{k['durum']:12s}] {k['kimlik']}  {k['baslik'][:62]}")
    p = yaz()
    print(f"\n  → {p.relative_to(KOK)}")
