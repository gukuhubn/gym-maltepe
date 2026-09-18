# -*- coding: utf-8 -*-
"""ADP ÇOK HATLI ŞEMA SETİ — A3, EPLAN düzeninde çok sayfalı DXF + PDF."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import proj as P, dxf_lib as X, sema as S

ROOT = Path(__file__).resolve().parent.parent
CAD  = ROOT/"cad"; CAD.mkdir(exist_ok=True)
OUT  = ROOT/"output"; OUT.mkdir(exist_ok=True)

PROJE = {"musteri": "ÖZEL — MALTEPE / İDEALTEPE",
         "aciklama": "MOBİLYA MAĞAZASI → FONKSİYONEL ANTRENMAN STÜDYOSU",
         "pano": "ADP", "no": "GYM-25-001-001", "tarih": P.TARIH,
         "cizen": "CC", "kontrol": "—", "onay": "—", "rev": P.REV}


def sayfalar():
    kay = S.linye_kayitlari()
    grup = [kay[i:i+S.SUTUN] for i in range(0, len(kay), S.SUTUN)]
    sf = [("Cover Sheet / Kapak", "kapak", None),
          ("Panel Characteristics / Pano Karakteristiği", "karakter", None),
          ("Symbol List / Sembol Listesi", "sembol", None),
          ("Incoming Supply / Ana Besleme", "besleme", None)]
    for g in grup:
        sf.append(("Schematic Diagram / Şematik Diyagram", "sema", g))
    sf.append(("Terminal Diagram / Klemens Planı", "klemens", kay))
    sf.append(("Panel Overview / Pano Önden Görünüş", "pano", kay))
    sf.append(("Load Schedule / Yükleme Cetveli", "yukleme", kay))
    sf.append(("Parts List / Malzeme Listesi", "malzeme", kay))
    return sf


def uret(dosya="cad/GYM-ADP-SEMA-R2010.dxf"):
    doc = X.yeni_belge("ADP çok hatlı şema"); X.bloklari_kur(doc)
    sf = sayfalar(); n = len(sf)
    for i, (ad, tip, veri) in enumerate(sf, 1):
        lay = doc.layouts.new(f"{i:02d} {ad}".replace("/", "-")[:60])
        lay.page_setup(size=(int(S.W), int(S.H)), margins=(0, 0, 0, 0),
                       units="mm")
        psp = lay
        S.sayfa_cercevesi(psp)
        S.antet(psp, i, (i+1 if i < n else "—"), n, ad, PROJE)
        onc, son = f"{max(1,i-1)}.7", f"{min(n,i+1)}.0"
        if tip == "besleme":
            S.besleme_sayfasi(psp, i, onc, son)
        elif tip == "sema":
            S.sematik_sayfa(psp, veri, i, onc, son)
        elif tip == "kapak":
            _kapak(psp, sf)
        elif tip == "karakter":
            _karakteristik(psp)
        elif tip == "sembol":
            _sembol_listesi(psp)
        elif tip == "klemens":
            _klemens_plani(psp, veri)
        elif tip == "pano":
            _pano_gorunus(psp, veri)
        elif tip == "yukleme":
            _yukleme_cetveli(psp, veri)
        elif tip == "malzeme":
            _malzeme_listesi(psp, veri)
    if "Layout1" in doc.layouts: doc.layouts.delete("Layout1")
    yol = ROOT/dosya
    doc.saveas(yol)
    print(f"  → {dosya}  ·  {n} sayfa · {yol.stat().st_size/1e6:.2f} MB")
    return doc, n


# ── yardımcı sayfalar ───────────────────────────────────────────────────────
def _t(psp, x, y, m, h=S.YZ["kucuk"], kat="yazi", hiza=None, aci=0, stil="GYM"):
    from ezdxf.enums import TextEntityAlignment as TA
    return S._t(psp, x, y, m, h, kat, hiza or TA.MIDDLE_LEFT, aci, stil)


def _kapak(psp, sf):
    from ezdxf.enums import TextEntityAlignment as TA
    x, y = S.DX0+14, S.DY1-18
    _t(psp, x, y, "ADP — ANA DAĞITIM PANOSU", S.YZ["baslik"]*1.6, "yazi",
       stil="GYM-B"); y -= 9
    _t(psp, x, y, "ÇOK HATLI ŞEMATİK DİYAGRAM SETİ / MULTI-LINE SCHEMATIC SET",
       S.YZ["etiket"], "yazi"); y -= 12
    for k, v in (("Müşteri / Customer", PROJE["musteri"]),
                 ("Proje / Project", PROJE["aciklama"]),
                 ("Pano / Panel", PROJE["pano"]),
                 ("Proje No / Project No", PROJE["no"]),
                 ("Tarih / Date", PROJE["tarih"]),
                 ("Revizyon / Revision", P.REV),
                 ("Standartlar / Standards",
                  "IEC 61439-1&2 · IEC 60617 · IEC 81346-2 · "
                  "TS HD 60364 · Elektrik İç Tesisleri Yönetmeliği")):
        _t(psp, x, y, k, S.YZ["kucuk"], "yazi")
        _t(psp, x+52, y, v, S.YZ["orta"], "yazi"); y -= 5.4
    y -= 6
    _t(psp, x, y, "SAYFA İÇERİĞİ / SHEET INDEX", S.YZ["etiket"], "yazi",
       stil="GYM-B"); y -= 2.4
    S._l(psp, (x, y), (S.DX1-14, y), "antet", 35); y -= 5
    for i, (ad, tip, veri) in enumerate(sf, 1):
        _t(psp, x, y, f"{i:02d}", S.YZ["orta"], "yazi")
        _t(psp, x+10, y, ad, S.YZ["orta"], "yazi")
        y -= 4.6


def _karakteristik(psp):
    from ezdxf.enums import TextEntityAlignment as TA
    x, y = S.DX0+10, S.DY1-14
    _t(psp, x, y, "PANO KARAKTERİSTİK TABLOSU / PANEL CHARACTERISTICS",
       S.YZ["baslik"], "yazi", stil="GYM-B"); y -= 8
    gruplar = [
      ("STANDARTLAR / STANDARDS", [
        ("Tip testli pano / Type tested assembly", "IEC 61439-1 & IEC 61439-2"),
        ("Semboller / Symbols", "IEC 60617"),
        ("Referans işaretleri / Designations", "IEC 81346-2"),
        ("Tesisat / Installation", "TS HD 60364 · Elektrik İç Tes. Yön.")]),
      ("BESLEME / POWER SUPPLY", [
        ("Anma işletme gerilimi / Rated voltage", "400/230 V  50 Hz"),
        ("Faz sayısı / Number of phases", "3F + N + PE"),
        ("Nötr işletmesi / Neutral operation", "TN-S"),
        ("Anma akımı / Rated current", f"{P.ANA_KESICI//3} A"),
        ("Kısa devre dayanımı / Icw", "6 kA  1 s"),
        ("Ana besleme kablosu / Main cable",
         f"{P.ANA_KABLO} · {P.ANA_L:.0f} m")]),
      ("KORUMA / PROTECTION", [
        ("Ana şalter / Main switch", f"4×{P.ANA_KESICI//3} A"),
        ("Ana kaçak akım / Main RCD",
         f"4×{P.ANA_KACAK_A} A / {P.ANA_KACAK_MA} mA  S tipi"),
        ("Son devre kaçak akım / Final RCD", "30 mA  A tipi"),
        ("Aşırı gerilim / SPD", "Tip 2 · Up 1,4 kV · In 20 kA"),
        ("Kesici eğrisi / MCB curve",
         "Aydınlatma B · Priz ve motor C · tümü 6 kA")]),
      ("GÖVDE / ENCLOSURE", [
        ("Koruma sınıfı / Degree of protection", "IP 54"),
        ("Ayrıştırma / Segregation", "Form 2b"),
        ("Gövde / Enclosure", "Sac · RAL 7035"),
        ("Bara / Busbar", "Bakır · nötr tam kesit"),
        ("Montaj / Mounting", "Sabit · kapı arkası kumanda"),
        ("Etiketleme / Labelling", "PVC · Türkçe · vidalı")]),
      ("ÖZET / SUMMARY", [
        ("Linye sayısı / Number of circuits",
         f"{len(P.LINYE)} + 4 yedek"),
        ("Bağlı güç / Connected load", f"{P.BAGLI_KW:.2f} kW".replace(".", ",")),
        ("Talep gücü / Demand", f"{P.TALEP_KW:.2f} kW".replace(".", ",")),
        ("Faz dengesizliği / Imbalance", f"%{P.FAZ_DENGE:.1f}".replace(".", ",")),
        ("Toplam ΔU / Total voltage drop",
         f"%{P.TOPLAM_DU_MAX:.2f}".replace(".", ","))]),
    ]
    sol = True
    x0 = {True: S.DX0+10, False: S.DX0+196}
    ycol = {True: y, False: y}
    for baslik, satirlar in gruplar:
        xx = x0[sol]; yy = ycol[sol]
        _t(psp, xx, yy, baslik, S.YZ["etiket"], "yazi", stil="GYM-B")
        S._l(psp, (xx, yy-2.2), (xx+172, yy-2.2), "antet", 35)
        yy -= 6
        for k, v in satirlar:
            _t(psp, xx+1, yy, k, S.YZ["kucuk"], "yazi")
            _t(psp, xx+171, yy, v, S.YZ["kucuk"], "yazi", TA.MIDDLE_RIGHT)
            yy -= 4.4
        yy -= 5
        ycol[sol] = yy
        sol = not sol if baslik.startswith("KORUMA") else sol
        if baslik.startswith("KORUMA"): sol = False


def _sembol_listesi(psp):
    from ezdxf.enums import TextEntityAlignment as TA
    _t(psp, S.DX0+10, S.DY1-14, "SEMBOL LİSTESİ / SYMBOL LIST — IEC 60617",
       S.YZ["baslik"], "yazi", stil="GYM-B")
    kalemler = [
      ("mcb1", "-F", "Otomatik sigorta, 1 kutup / MCB 1P"),
      ("mcb2", "-F", "Otomatik sigorta, 1F+N / MCB 1P+N"),
      ("rcd2", "-ID", "Kaçak akım rölesi 2 kutup / RCD 2P"),
      ("rcd4", "-ID", "Kaçak akım rölesi 4 kutup / RCD 4P"),
      ("spd", "-F0", "Aşırı gerilim koruma Tip 2 / SPD Type 2"),
      ("klem", "-X", "Klemens / Terminal"),
      ("toprak", "PE", "Koruma topraklaması / Protective earth"),
      ("dot", "", "Bağlantı noktası / Junction"),
      ("yuk", "P", "Saha cihazı ve kablo / Field device and cable"),
      ("ray", "L1 L2 L3 N", "Potansiyel rayı / Potential rail"),
      ("ref", "", "Sayfalar arası referans / Cross-page reference"),
    ]
    y = S.DY1-26
    for kod, tag, ack in kalemler:
        x = S.DX0+24
        if kod == "mcb1":
            S.kesici_kutbu(psp, x, y+5, y-5)
        elif kod == "mcb2":
            S.kesici_kutbu(psp, x, y+5, y-5); S.kesici_kutbu(psp, x+4, y+5, y-5)
            S._l(psp, (x, y+2.4), (x+4, y+2.4), "sembol", 18, "DASHED")
        elif kod in ("rcd2", "rcd4"):
            n = 2 if kod == "rcd2" else 4
            for k in range(n): S.kesici_kutbu(psp, x+k*4, y+5, y-1)
            S._pl(psp, [(x-2.6, y-5), (x+(n-1)*4+2.6, y-5),
                        (x+(n-1)*4+2.6, y-1), (x-2.6, y-1)], "sembol", True, 35)
            S._t(psp, x+(n-1)*2, y-3, "I", S.YZ["kucuk"], "sembol")
        elif kod == "spd":
            S._pl(psp, [(x-1.6, y-4), (x+1.6, y-4), (x+1.6, y+4), (x-1.6, y+4)],
                  "sembol", True, 35)
            S._l(psp, (x-1.6, y-4), (x+1.6, y+4), "sembol", 25)
        elif kod == "klem":
            S._c(psp, x, y, 0.8, "klemens", 25)
        elif kod == "toprak":
            S._l(psp, (x, y+3), (x, y), "sembol", 25)
            for i, w in enumerate((2.2, 1.4, 0.7)):
                S._l(psp, (x-w, y-i*0.9), (x+w, y-i*0.9), "sembol", 25)
        elif kod == "dot":
            S._dot(psp, x, y)
        elif kod == "yuk":
            S.yuk_blogu(psp, x, ("L", "N", "PE"), "", ())
        elif kod == "ray":
            S._l(psp, (x-6, y), (x+10, y), "ray", 35)
        elif kod == "ref":
            S._pl(psp, [(x-6, y-1.3), (x-2.2, y-1.3), (x-0.6, y),
                        (x-2.2, y+1.3), (x-6, y+1.3)], "yazi", True, 18)
        S._t(psp, S.DX0+46, y, tag, S.YZ["orta"], "yazi", TA.MIDDLE_LEFT,
             stil="GYM-B")
        S._t(psp, S.DX0+62, y, ack, S.YZ["orta"], "yazi", TA.MIDDLE_LEFT)
        y -= 14


def _tablo(psp, x, y, sutunlar, basliklar, satirlar, sh=5.0,
           fs=None, hizalar=None):
    """Çizgi + yazı tablosu (ezdxf ACAD_TABLE yazamaz)."""
    from ezdxf.enums import TextEntityAlignment as TA
    fs = fs or S.YZ["mikro"]
    w = sum(sutunlar); n = len(satirlar)+1
    S._pl(psp, [(x, y-n*sh), (x+w, y-n*sh), (x+w, y), (x, y)], "antet", True, 50)
    for i in range(1, n):
        S._l(psp, (x, y-i*sh), (x+w, y-i*sh), "antet", 13)
    cx = x
    for s in sutunlar[:-1]:
        cx += s; S._l(psp, (cx, y-n*sh), (cx, y), "antet", 13)
    cx = x
    for b, s in zip(basliklar, sutunlar):
        S._t(psp, cx+s/2, y-sh/2, b, fs, "antet", TA.MIDDLE_CENTER,
             stil="GYM-B")
        cx += s
    hizalar = hizalar or ["c"]*len(sutunlar)
    for r_i, r in enumerate(satirlar):
        cx = x
        for v, s, hz in zip(r, sutunlar, hizalar):
            al = {"l": TA.MIDDLE_LEFT, "c": TA.MIDDLE_CENTER,
                  "r": TA.MIDDLE_RIGHT}[hz]
            px = cx+1.0 if hz == "l" else (cx+s-1.0 if hz == "r" else cx+s/2)
            S._t(psp, px, y-(r_i+1.5)*sh, str(v), fs, "yazi", al)
            cx += s
    return y-n*sh


def _yukleme_cetveli(psp, kay):
    """YÜKLEME CETVELİ — grup kaçak akım sütunu ile (referans proje biçimi)."""
    from ezdxf.enums import TextEntityAlignment as TA
    _t(psp, S.DX0+6, S.DY1-10, "ADP YÜKLEME CETVELİ / LOAD SCHEDULE",
       S.YZ["baslik"], "yazi", stil="GYM-B")
    _t(psp, S.DX0+6, S.DY1-16,
       "Grup kaçak akım röleleri ve kapsadıkları linyeler ayrı sütunda "
       "gösterilmiştir.", S.YZ["kucuk"], "yazi")
    sut =  [9, 14, 50, 11, 22, 38, 22, 13, 15, 15, 14, 14, 14, 13]
    bas =  ["NO", "LİNYE", "MAHAL / YÜK", "FAZ", "KESİCİ",
            "KAÇAK AKIM (GRUP)", "KABLO", "BORU", "UZUNLUK",
            "Pb (kW)", "cos φ", "Ib (A)", "ΔU (%)", "SONUÇ"]
    hz =   ["c", "c", "l", "c", "c", "l", "c", "c", "r", "r", "c", "r", "r", "c"]
    satir = []
    onceki_rcd = None
    for k in kay:
        # grup kaçak akımı YALNIZ grubun ilk satırında yazılır, altındakiler
        # aynı gruba ait olduğunu düşey bağ ile gösterir
        if k["rcd"] != onceki_rcd:
            rcd_h = f"{k['rcd']} · {k['rcd_ozel'].replace(', ', ' ')}" \
                if k["rcd"] != "—" else "— kaçak akım rölesi yok (kesintisiz)"
            onceki_rcd = k["rcd"]
        else:
            rcd_h = "↑  aynı grup"
        satir.append([
            k["no"], k["kod"], (k["tanim"][:38]), k["faz"],
            f"{k['amper']} A · {3 if k['kutup'] >= 3 else 1}P {k['egri']} · "
            f"{k['kesme']}",
            rcd_h,
            f"{k['kablo']} {k['kesit']}" if not k["yedek"] else "—",
            k["boru"], f"{k['L']:.0f} m" if not k["yedek"] else "—",
            f"{k['kw']:.2f}".replace(".", ",") if not k["yedek"] else "—",
            f"{k['cosfi']:.2f}".replace(".", ",") if not k["yedek"] else "—",
            f"{k['ib']:.1f}".replace(".", ",") if not k["yedek"] else "—",
            f"{k['du']:.2f}".replace(".", ",") if not k["yedek"] else "—",
            k["sonuc"]])
    alt = _tablo(psp, S.DX0+6, S.DY1-20, sut, bas, satir, sh=5.6)
    # grup parantezleri — hangi linyelerin hangi röleye bağlı olduğu
    x_rcd = S.DX0+6+sum(sut[:5])
    ust = S.DY1-20-5.6
    gruplar = {}
    for i, k in enumerate(kay):
        gruplar.setdefault(k["rcd"], []).append(i)
    for gkod, idxs in gruplar.items():
        if len(idxs) < 2: continue
        y1 = ust - idxs[0]*5.6 - 1.0
        y2 = ust - idxs[-1]*5.6 - 4.6
        xb = x_rcd + sut[5] - 2.0
        S._pl(psp, [(xb-1.6, y1), (xb, y1), (xb, y2), (xb-1.6, y2)],
              "antet", False, 25)
    # özet
    y = alt - 8
    _t(psp, S.DX0+6, y, "ÖZET / SUMMARY", S.YZ["etiket"], "yazi", stil="GYM-B")
    y -= 5
    ozet = [
      ("Bağlı güç / Connected", f"{P.BAGLI_KW:.2f} kW".replace(".", ",")),
      ("Talep gücü / Demand", f"{P.TALEP_KW:.2f} kW".replace(".", ",")),
      ("L1 / L2 / L3 (kW)",
       " / ".join(f"{P.FAZ_YUK[f]:.2f}" for f in ("L1", "L2", "L3"))
       .replace(".", ",")),
      ("Faz dengesizliği / Imbalance", f"%{P.FAZ_DENGE:.1f}".replace(".", ",")),
      ("Ana şalter / Main switch", f"4×{P.ANA_KESICI//3} A"),
      ("Ana kaçak akım / Main RCD",
       f"4×{P.ANA_KACAK_A} A / {P.ANA_KACAK_MA} mA S tipi"),
      ("Grup kaçak akım sayısı / RCD groups", f"{len(gruplar)} adet"),
      ("Toplam ΔU / Total", f"%{P.TOPLAM_DU_MAX:.2f}".replace(".", ",")),
    ]
    for i, (k, v) in enumerate(ozet):
        col = i % 4
        row = i // 4
        xx = S.DX0+6+col*90
        _t(psp, xx, y-row*4.6, k, S.YZ["kucuk"], "yazi")
        _t(psp, xx+56, y-row*4.6, v, S.YZ["kucuk"], "yazi", stil="GYM-B")


def _klemens_plani(psp, kay):
    from ezdxf.enums import TextEntityAlignment as TA
    _t(psp, S.DX0+6, S.DY1-10, "KLEMENS PLANI / TERMINAL DIAGRAM  —  -X1",
       S.YZ["baslik"], "yazi", stil="GYM-B")
    sut = [14, 18, 22, 22, 30, 60, 26, 26]
    bas = ["KLEMENS", "LİNYE", "İLETKEN", "TEL NO", "KABLO",
           "HEDEF / DESTINATION", "SAYFA", "KAÇAK AKIM"]
    hz = ["c", "c", "c", "c", "c", "l", "c", "c"]
    satir = []
    sayfa_of = {}
    for i, k in enumerate(kay):
        sayfa_of[k["kod"]] = 5 + i//S.SUTUN
    for k in kay:
        if k["yedek"]: continue
        for il, tel in (("L", k["tel"]), ("N", f"N{k['rcd_no']}"), ("PE", "PE")):
            satir.append([k["klem"] if il == "L" else "", k["kod"], il, tel,
                          f"{k['kablo']} {k['kesit']}", k["tanim"][:44],
                          f"{sayfa_of[k['kod']]}", k["rcd"]])
    _tablo(psp, S.DX0+6, S.DY1-16, sut, bas, satir, sh=4.0)


def _pano_gorunus(psp, kay):
    from ezdxf.enums import TextEntityAlignment as TA
    _t(psp, S.DX0+6, S.DY1-10,
       "PANO ÖNDEN GÖRÜNÜŞ / PANEL FRONT VIEW  —  ölçek 1:5",
       S.YZ["baslik"], "yazi", stil="GYM-B")
    MOD = 17.5/5.0            # 1 modül = 17,5 mm → 1:5 ölçekte 3,5 mm
    SIRA_H = 125.0/5.0
    n_sira = 4
    x0, y0 = S.DX0+30, S.DY0+40
    gen = 24*MOD + 16.0
    yuk = n_sira*SIRA_H + 24.0
    S._pl(psp, [(x0-8, y0-8), (x0+gen, y0-8), (x0+gen, y0+yuk),
                (x0-8, y0+yuk)], "antet", True, 50)
    _t(psp, x0-8, y0+yuk+4, "ADP · 800×1000×250 mm · IP54 · Form 2b · "
       "sac gövde RAL 7035", S.YZ["kucuk"], "yazi")
    # cihaz yerleşimi
    sira = [[] for _ in range(n_sira)]
    # ana cihazlar 1. sırada
    sira[0] = [("-Q1", 4, "ANA ŞALTER 4×%d A" % (P.ANA_KESICI//3)),
               ("-ID0", 4, "ANA KAÇAK AKIM 4×%d A/%d mA" %
                (P.ANA_KACAK_A, P.ANA_KACAK_MA)),
               ("-F0", 4, "SPD Tip 2")]
    grup_ciz = set()
    cur = 1
    for k in kay:
        if k["rcd"] != "—" and k["rcd"] not in grup_ciz:
            grup_ciz.add(k["rcd"])
            ad = f"-ID{k['rcd_no']}"
            w = 2 if "2×" in k["rcd_ozel"] else 4
            if sum(m for _, m, _ in sira[cur]) + w > 24: cur += 1
            if cur >= n_sira: cur = n_sira-1
            sira[cur].append((ad, w, k["rcd_ozel"]))
        w = k["kutup"]+1 if k["kutup"] > 1 else 1
        if sum(m for _, m, _ in sira[cur]) + w > 24: cur += 1
        if cur >= n_sira: cur = n_sira-1
        sira[cur].append((k["tag"], w, f"{k['kod']} {k['amper']}A {k['egri']}"))
    for r in range(n_sira):
        yr = y0 + (n_sira-1-r)*SIRA_H
        S._l(psp, (x0, yr+SIRA_H*0.45), (x0+24*MOD, yr+SIRA_H*0.45),
             "sembol", 35)      # DIN ray
        _t(psp, x0-10, yr+SIRA_H*0.45, f"R{r+1}", S.YZ["mikro"], "yazi",
           TA.MIDDLE_RIGHT)
        xm = x0
        for tag, w, ack in sira[r]:
            S._pl(psp, [(xm, yr+SIRA_H*0.12), (xm+w*MOD, yr+SIRA_H*0.12),
                        (xm+w*MOD, yr+SIRA_H*0.78), (xm, yr+SIRA_H*0.78)],
                  "sembol", True, 25)
            S._t(psp, xm+w*MOD/2, yr+SIRA_H*0.60, tag, S.YZ["mikro"], "yazi")
            S._t(psp, xm+w*MOD/2, yr+SIRA_H*0.30, str(w), 1.2, "yazi")
            xm += w*MOD
        kalan = 24 - sum(w for _, w, _ in sira[r])
        if kalan > 0:
            S._pl(psp, [(xm, yr+SIRA_H*0.12), (xm+kalan*MOD, yr+SIRA_H*0.12),
                        (xm+kalan*MOD, yr+SIRA_H*0.78), (xm, yr+SIRA_H*0.78)],
                  "yuk", True, 18, "DASHED")
            S._t(psp, xm+kalan*MOD/2, yr+SIRA_H*0.45, f"BOŞ {kalan} MOD",
                 S.YZ["mikro"], "yazi")
    # açıklama tablosu
    sut = [16, 16, 18, 60]
    bas = ["SIRA", "CİHAZ", "MODÜL", "AÇIKLAMA"]
    satir = [[f"R{r+1}", tag, w, ack] for r in range(n_sira)
             for tag, w, ack in sira[r]]
    _tablo(psp, S.DX0+180, S.DY1-16, sut, bas, satir, sh=3.6,
           hizalar=["c", "c", "c", "l"])


def _malzeme_listesi(psp, kay):
    from ezdxf.enums import TextEntityAlignment as TA
    _t(psp, S.DX0+6, S.DY1-10, "MALZEME LİSTESİ / PARTS LIST",
       S.YZ["baslik"], "yazi", stil="GYM-B")
    say = {}
    for k in kay:
        a = f"Otomatik sigorta {k['kutup']}×{k['amper']} A {k['egri']} eğrisi · {k['kesme']}"
        say[a] = say.get(a, 0)+1
    for k in kay:
        if k["rcd"] == "—": continue
        a = f"Kaçak akım rölesi {k['rcd_ozel']}"
        say.setdefault(a, 0)
    grup = {}
    for k in kay:
        if k["rcd"] != "—": grup[k["rcd"]] = k["rcd_ozel"]
    for g, oz in grup.items():
        say[f"Kaçak akım rölesi {oz}"] = say.get(f"Kaçak akım rölesi {oz}", 0)+1
    ek = [(f"Ana şalter 4×{P.ANA_KESICI//3} A yük ayırıcı", 1),
          (f"Ana kaçak akım rölesi 4×{P.ANA_KACAK_A} A / {P.ANA_KACAK_MA} mA S tipi", 1),
          ("Parafudr Tip 2 · Up 1,4 kV · In 20 kA (3F+N)", 1),
          ("Pano gövdesi 800×1000×250 mm IP54 Form 2b", 1),
          ("Bakır bara seti 3F+N+PE", 1),
          ("Klemens sırası -X1 (vidalı, 4 mm²)", len([k for k in kay if not k["yedek"]])*3),
          ("Etiket seti (PVC, Türkçe, vidalı)", 1)]
    satir = [[i+1, a, "adet", n] for i, (a, n) in
             enumerate(sorted(say.items(), key=lambda t: -t[1]))]
    satir += [[len(satir)+i+1, a, "adet", n] for i, (a, n) in enumerate(ek)]
    _tablo(psp, S.DX0+6, S.DY1-16, [14, 240, 24, 22],
           ["S.NO", "MALZEME / MATERIAL", "BİRİM", "MİKTAR"], satir, sh=5.2,
           hizalar=["c", "l", "c", "r"])


# ── PDF ─────────────────────────────────────────────────────────────────────
def pdf_uret(doc, n, cikti="output/Gym_ADP_Sema_A3.pdf"):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    from ezdxf.addons.drawing import RenderContext, Frontend
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from ezdxf.addons.drawing import config as C
    import ezdxf.bbox
    cfg = C.Configuration(background_policy=C.BackgroundPolicy.WHITE,
                          color_policy=C.ColorPolicy.COLOR,
                          circle_approximation_count=160)
    adlar = [l for l in doc.layouts.names() if l != "Model"]
    adlar.sort()
    yol = ROOT/cikti
    with PdfPages(yol) as pdf:
        for ad in adlar:
            lay = doc.layouts.get(ad)
            fig = plt.figure(figsize=(S.W/25.4, S.H/25.4))
            ax = fig.add_axes([0, 0, 1, 1]); ax.set_axis_off()
            Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg,
                     bbox_cache=ezdxf.bbox.Cache()).draw_layout(lay,
                                                                finalize=True)
            ax.set_xlim(0, S.W); ax.set_ylim(0, S.H)
            ax.set_aspect("equal", adjustable="box")
            fig.set_size_inches(S.W/25.4, S.H/25.4)
            pdf.savefig(fig, facecolor="white"); plt.close(fig)
    print(f"  → {cikti}  ·  {len(adlar)} sayfa · "
          f"{yol.stat().st_size/1e6:.2f} MB")
    return yol


if __name__ == "__main__":
    doc, n = uret()
    pdf_uret(doc, n)
