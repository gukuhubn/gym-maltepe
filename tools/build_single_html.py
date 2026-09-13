# -*- coding: utf-8 -*-
"""Tek dosya offline model + render galerisi.

TASARIM İLKESİ — İLERLEMELİ ZENGİNLEŞTİRME (progressive enhancement):
Dosya WhatsApp'tan gelip iOS Quick Look gibi JavaScript'i KAPALI bir önizleyicide
açılabilir. Bu yüzden bütün içerik (metin, tablolar, 8 render) doğrudan HTML
işaretlemesinde yer alır; gezinme gerçek çapa (#) bağlantılarıdır ve tüm bölümler
varsayılan olarak görünürdür. JavaScript yalnızca 3B görüntüleyiciyi ekler —
çalışmazsa onun yerine sabit bir model görseli görünür.
"""
import sys, os, json, base64, io, glob, html as H
sys.path.insert(0, os.path.dirname(__file__))
from pathlib import Path
from PIL import Image
import proj as P

THREE = Path("site/vendor/three.min.js").read_text()
MODEL = Path("site/model.js").read_text()
DIM   = Path("data/dimensions.json").read_text()
assert "</script" not in (THREE + MODEL).lower(), "gömülü betikte </script dizisi var"

def jpg(p, w=1180, q=84):
    im = Image.open(p).convert("RGB")
    if im.width > w: im = im.resize((w, round(im.height*w/im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=q, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()

D = json.loads(DIM)
BAS = {k["ad"]: k["baslik"] for k in D["kameralar"]}
gal = []
for p in sorted(glob.glob("output/render/*.png")):
    ad = Path(p).stem; stil = ad.rsplit("_", 1)[1]; kam = ad[:-(len(stil)+1)]
    gal.append((BAS.get(kam, kam), D["stiller"][stil]["ad"], jpg(p)))
model_gorsel = jpg("work/model/01_giristen_arenaya_endustriyel.png", 1000, 80) \
               if Path("work/model/01_giristen_arenaya_endustriyel.png").exists() else gal[0][2]

m = P.maliyet("O", "A")
KPI = [("Net iç alan", f"{P.A['ic_toplam']:.2f} m²".replace(".",","), "salon 87,05 + ıslak hacim 16,73"),
       ("Eşzamanlı kapasite", "12 kişi", "65,14 m² serbest sirkülasyon"),
       ("Tadilat bütçesi", f"{m['toplam'][0]/1e6:.2f}–{m['toplam'][1]/1e6:.2f} M₺".replace(".",","),
        f"önerilen senaryo · {P.FIYAT_TARIH}"),
       ("Ruhsat zinciri", "16–28 hafta", "GSİM ön görüşten belediye ruhsatına"),
       ("Şantiye süresi", f"{P.PROGRAM_HAFTA:.0f} hafta", "14 adım · kritik yol ıslak hacim"),
       ("Ekipman", "Bütçe dışı", "işverence temin edilmiştir")]
BOLGE = [(z[0], P.ZON_M2[z[0]], z[2], z[3]) for z in P.ZONES] + \
        [("ISLAK HACİM (2 blok)", P.A["islak_toplam"], "Seramik R11 kaymaz + su yalıtımı", "—")]
ROTA = [("R1", "Ön görüş olumlu", "#2E7D5B",
         "Mevcut alan yeterli görülür; bu dosya olduğu gibi uygulanır, ek maliyet yoktur."),
        ("R2", "Kapsam revizyonu", "#D79A1E",
         "Randevulu kişisel antrenman / özel ders stüdyosu. Ring zaten bire bir ve küçük grup "
         "çalışmasına uygundur. Tescil kapsamı ve belediye NACE kodu buna göre seçilir; hukuki görüş şarttır."),
        ("R3", "Sözleşme yolu", "#C8322B",
         "İki rota da kapanırsa mesele mimari değil ticarîdir: kira sözleşmesindeki fesih veya "
         "indirim imkânı avukatla değerlendirilir.")]

def tablo(basliklar, satirlar, sag=()):
    th = "".join(f'<th{" class=n" if i in sag else ""}>{H.escape(b)}</th>'
                 for i, b in enumerate(basliklar))
    tr = ""
    for s in satirlar:
        tr += "<tr>" + "".join(f'<td{" class=n" if i in sag else ""}>{H.escape(str(c))}</td>'
                               for i, c in enumerate(s)) + "</tr>"
    return f"<table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table>"

vir = lambda x, n=2: f"{x:.{n}f}".replace(".", ",")

SAG1 = (1,)
TBL_BOLGE = tablo(["Bölge", "m²", "Kaplama", "Kalınlık"],
                  [(a, vir(b), c, d) for a, b, c, d in BOLGE], sag=SAG1)
_DON = {"soyunma": "12 göz dolap + bank", "dus": "Duş teknesi + cam kabin",
        "wc": "Klozet + lavabo"}
_AD  = {"soyunma": "soyunma", "dus": "duş", "wc": "WC"}
TBL_ISLAK = tablo(["Hacim", "m²", "Donanım"],
                  [(f"{ad} {_AD[n]}", vir(P.ISLAK_M2_DETAY[ad][n]), _DON[n])
                   for ad in P.ISLAK_M2_DETAY for n in ("soyunma", "dus", "wc")], sag=SAG1)

HTML = f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Maltepe / İdealtepe — Gym Dönüşümü · {P.REV}</title>
<style>
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{margin:0;background:#0E1620;color:#E7EDF3;
 font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}}
header{{padding:22px 18px 16px;border-bottom:3px solid #B87333;background:#16273D}}
h1{{margin:0;font-size:20px;line-height:1.3}}
.sub{{color:#8FA6BE;font-size:13px;margin-top:6px}}
nav{{display:flex;gap:8px;padding:11px 18px;background:#101C29;position:sticky;top:0;z-index:10;
 overflow-x:auto;border-bottom:1px solid #1E3350;-webkit-overflow-scrolling:touch}}
nav a{{color:#C9D6E4;background:#1B2B40;border:1px solid #2E4D70;border-radius:6px;
 padding:9px 14px;font-size:13px;text-decoration:none;white-space:nowrap;display:inline-block}}
nav a:active{{background:#B87333;border-color:#B87333;color:#fff}}
section{{padding:20px 18px 26px;border-top:1px solid #16232F;scroll-margin-top:56px}}
section:first-of-type{{border-top:none}}
h2{{font-size:17px;margin:0 0 4px;color:#fff}}
h2 .no{{color:#B87333;font-size:12px;letter-spacing:.09em;display:block;margin-bottom:5px;
 text-transform:uppercase;font-weight:700}}
h3{{font-size:14px;margin:22px 0 6px;color:#C9D6E4;letter-spacing:.02em}}
.lead{{color:#9FB4C9;font-size:13.5px;margin:6px 0 16px}}
.grid{{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(215px,1fr))}}
.card{{background:#16232F;border:1px solid #24405F;border-radius:9px;padding:14px;
 border-left:3px solid #B87333}}
.card .k{{color:#B87333;font-size:11px;font-weight:700;letter-spacing:.07em;text-transform:uppercase}}
.card .v{{font-size:25px;font-weight:700;margin:7px 0 3px;line-height:1.15}}
.card .n{{color:#8FA6BE;font-size:12px}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin-top:10px;display:block;
 overflow-x:auto;white-space:nowrap}}
th{{background:#1B2B40;color:#fff;text-align:left;padding:9px 11px;font-size:11.5px;
 text-transform:uppercase;letter-spacing:.05em}}
td{{padding:9px 11px;border-bottom:1px solid #1E3350;color:#D5DFE9}}
th.n,td.n{{text-align:right;font-variant-numeric:tabular-nums}}
tbody tr:nth-child(even) td{{background:#121E2A}}
figure{{margin:0 0 14px;background:#16232F;border:1px solid #24405F;border-radius:9px;overflow:hidden}}
figure img{{width:100%;display:block;height:auto}}
figcaption{{padding:9px 12px;font-size:12px;color:#9FB4C9;display:flex;justify-content:space-between;
 gap:10px;flex-wrap:wrap}}
figcaption b{{color:#E7EDF3}}
#wrap{{position:relative;background:#0A1119;border:1px solid #24405F;border-radius:9px;overflow:hidden}}
#wrap img{{width:100%;display:block;height:auto}}
#c{{display:block;width:100%;height:62vh;min-height:280px}}
#basla{{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);background:#B87333;
 color:#fff;border:none;border-radius:8px;padding:14px 22px;font-size:15px;font-weight:600;
 cursor:pointer;box-shadow:0 6px 22px rgba(0,0,0,.45)}}
.ctrl{{display:flex;gap:7px;flex-wrap:wrap;padding:11px 0}}
.ctrl button{{background:#1B2B40;color:#C9D6E4;border:1px solid #2E4D70;border-radius:6px;
 padding:9px 13px;font-size:12.5px;cursor:pointer}}
.ctrl button.on{{background:#B87333;border-color:#B87333;color:#fff}}
.uyari{{background:#2A1C20;border:1px solid #C8322B;border-left-width:4px;border-radius:9px;
 padding:14px;margin:14px 0}}
.uyari b{{color:#E5837E}}
.ipucu{{background:#16232F;border:1px solid #24405F;border-left:4px solid #B87333;border-radius:9px;
 padding:13px;margin:14px 0;font-size:13px;color:#C9D6E4}}
.ipucu b{{color:#E0B07A}}
.rota{{display:grid;gap:11px;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));margin-top:12px}}
.rota div{{background:#16232F;border:1px solid #24405F;border-radius:9px;padding:13px;border-left:4px solid}}
.rota .rk{{font-weight:700;font-size:13px;margin-bottom:5px}}
.rota p{{margin:0;font-size:13px;color:#C9D6E4}}
ul{{padding-left:20px;margin:8px 0}} li{{margin:6px 0;color:#C9D6E4;font-size:13.5px}}
footer{{color:#5E7690;font-size:11.5px;padding:18px;border-top:1px solid #1E3350}}
@media(max-width:520px){{
 .card .v{{font-size:22px}} #c{{height:48vh}} h1{{font-size:18px}}
 section{{padding:18px 14px 22px}} nav{{padding:10px 14px}}}}
</style></head><body>

<header>
 <h1>Mobilya mağazası → Fonksiyonel antrenman stüdyosu</h1>
 <div class="sub">Maltepe / İdealtepe · İstanbul &nbsp;·&nbsp; {P.REV} &nbsp;·&nbsp; {P.TARIH}
 &nbsp;·&nbsp; ön tasarım — yerinde doğrulanacak</div>
</header>

<nav>
 <a href="#ozet">Özet</a><a href="#karar">Kritik karar</a><a href="#zemin">Zemin</a>
 <a href="#render">Render galerisi</a><a href="#model">3B model</a><a href="#adim">Sonraki adımlar</a>
</nav>

<section id="ozet">
 <h2><span class="no">01 · Özet</span>Altı rakamda proje</h2>
 <div class="grid">
 {''.join(f'<div class="card"><div class="k">{H.escape(k)}</div><div class="v">{H.escape(v)}</div>'
          f'<div class="n">{H.escape(n)}</div></div>' for k, v, n in KPI)}
 </div>
</section>

<section id="karar">
 <h2><span class="no">02 · Önce bunu çöz</span>Mevzuat eşiği — projenin tek kritik belirsizliği</h2>
 <div class="uyari"><b>EN KRİTİK BULGU —</b> Mevzuatın il müdürlüklerince yaygın uygulanan
 biçiminde spor salonlarında en az 125 m² çalışma alanı, 15'er m² kadın/erkek soyunma ve 15 m²
 dinlenme salonu ile toplam en az 170 m² aranmaktadır. Bu birimin net iç alanı
 {vir(P.A['ic_toplam'])} m²'dir. Kapalı alanı artırmak için bahçelerin kapatılması işveren
 kararıyla kapsam dışıdır — ön ve arka bahçe açık kullanımda kalır, hiçbir alan hesabına girmez.
 Yönetmelik metninin kendisi salon için m² şartı getirmez (soyunma ≥8 m², dinlenme ≥15 m² der) ve
 bu iki şart mevcut planda sağlanır. Yatırımın ilk adımı imalat değil,
 İstanbul GSİM'den alınacak <b>yazılı ön görüş</b>tür.</div>
 <h3>Ön görüşün üç olası sonucu, üç rota</h3>
 <div class="rota">
 {''.join(f'<div style="border-left-color:{c}"><div class="rk" style="color:{c}">{k} · {H.escape(t)}</div>'
          f'<p>{H.escape(b)}</p></div>' for k, t, c, b in ROTA)}
 </div>
</section>

<section id="zemin">
 <h2><span class="no">03 · Tasarım</span>Zemin bölgeleri ve ıslak hacim</h2>
 <p class="lead">Üç bölgeli zemin stratejisi: para arena kauçuğuna, ıslak hacme ve
 aydınlatma-havalandırmaya harcanır.</p>
 {TBL_BOLGE}
 <h3>Islak hacim</h3>
 <p class="lead">İki blok korunur, içleri komple yenilenir: her blokta 1 duş + 1 WC →
 karma kullanımda aranan 2+2 sağlanır. Gider kotu yerçekimiyle çözülmezse Seçenek A
 (zemin yükseltme) devreye girer.</p>
 {TBL_ISLAK}
</section>

<section id="render">
 <h2><span class="no">04 · Render galerisi</span>Dört açı, iki stil varyantı</h2>
 <p class="lead">Ortadaki altıgen <b>ring</b>: kanvas platform, altı kırmızı pedli çelik köşe direği,
 dört sıra halat. Ekipman işverence temin edilmiştir ve görsellerde yerinde gösterilmiştir.</p>
 {''.join(f'<figure><img src="{src}" alt="{H.escape(b)} — {H.escape(s)}">'
          f'<figcaption><b>{H.escape(b)} · {H.escape(s)}</b>'
          f'<span>temsilî görsel — imalat ölçüsü değildir</span></figcaption></figure>'
          for b, s, src in gal)}
</section>

<section id="model">
 <h2><span class="no">05 · 3B model</span>Döndürülebilir kütle modeli</h2>
 <p class="lead">Aşağıdaki düğmeye basınca model tarayıcıda çalışır: sürükleyerek döndürün,
 iki parmakla yakınlaşın. Telefon önizlemesinde çalışmazsa üstteki sabit görsel geçerlidir.</p>
 <div id="wrap">
  <img id="model-sabit" src="{model_gorsel}" alt="Kütle modeli — sabit görsel">
  <button id="basla" type="button">▶ 3B modeli başlat</button>
 </div>
 <div class="ctrl" id="cams"></div><div class="ctrl" id="sty"></div>
 <div class="ipucu"><b>Not:</b> 3B görüntüleyici JavaScript gerektirir. Dosya bir sohbet
 uygulamasının önizlemesinde açıldıysa bu bölüm çalışmaz; dosyayı bilgisayarda tarayıcıda
 açın. Dosyanın geri kalanı her durumda okunur.</div>
</section>

<section id="adim">
 <h2><span class="no">06 · Sonraki adımlar</span>Beş madde, sırayla</h2>
 <ul>{''.join(f'<li><b>{n}. {H.escape(t)}</b> — {H.escape(b)}</li>' for n, t, b in P.SONRAKI_5)}</ul>
 <h3>İşverenden istenecekler</h3>
 <ul><li>DXF export (AutoCAD R2010)</li><li>Mevcut durum fotoğrafları (salon, giriş, soyunma koridoru)</li>
 <li>Ölçülmüş net m² ve tavan yüksekliği</li><li>Satın alınan ekipman listesi (marka/model/ölçü/ağırlık)</li>
 <li>Pis su bağlantısı fotoğrafı ve kotu</li><li>Elektrik pano gücü ve trifaze durumu</li>
 <li>Tapu bağımsız bölüm niteliği ve iskân belgesi</li>
 <li>Bina bağımsız mı; değilse yönetim planı ve kat malikleri durumu</li>
 <li>Hedeflenen açılış tarihi ve üye kapasitesi</li></ul>
 <h3>Ölçü dayanağı</h3>
 <ul><li>DWG dosyası AutoCAD 2018 (AC1032) formatında ve bu ortamda açılamadı.</li>
 <li>PDF paftaları vektör değil JPEG raster; geometri renk alanları izlenerek vektörleştirildi.</li>
 <li>Paftanın kendi m² etiketleriyle kalibre edildi — üç bölgede sapma %3'ün altında.</li>
 <li>Uygulama projesi için işverenden DXF (R2010) export istenmelidir.</li></ul>
</section>

<footer>Ön tasarım — yerinde doğrulanmadan ve ruhsat alınmadan uygulama yapılamaz.
Görseller temsilîdir, imalat ölçüsü değildir. Yerel uygulama farklılık gösterebilir;
Maltepe Belediyesi Ruhsat ve Denetim Müdürlüğü ile İstanbul Gençlik ve Spor İl Müdürlüğü'nden
güncel liste teyit edilmelidir.</footer>

<!-- 3B yükü: yalnızca kullanıcı isteyince çalıştırılır (telefonda gereksiz yük olmasın) -->
<script type="text/plain" id="three-src">{THREE}</script>
<script type="text/plain" id="model-src">{MODEL}</script>
<script>
(function(){{
 var D={DIM};
 var wrap=document.getElementById("wrap"), btn=document.getElementById("basla");
 var stil="endustriyel", cam=0, ren, scene, camera, cv, yaw=0, pit=0, dist=1, hazir=false;
 function calistir(id){{
   var el=document.getElementById(id); if(!el) return;
   var s=document.createElement("script"); s.textContent=el.textContent;
   document.body.appendChild(s);
 }}
 function hata(msg){{
   var d=document.createElement("div"); d.className="ipucu";
   d.innerHTML="<b>3B model açılamadı:</b> "+msg+" Üstteki sabit görsel ve render galerisi geçerlidir.";
   wrap.parentNode.insertBefore(d, wrap.nextSibling);
 }}
 btn.addEventListener("click", function(){{
   btn.disabled=true; btn.textContent="Yükleniyor…";
   try{{
     calistir("three-src"); calistir("model-src");
     if(!window.THREE||!window.GymModel) throw new Error("kütüphane yüklenemedi.");
     var img=document.getElementById("model-sabit"); if(img) img.style.display="none";
     cv=document.createElement("canvas"); cv.id="c"; wrap.appendChild(cv); btn.remove();
     ren=new THREE.WebGLRenderer({{canvas:cv,antialias:true}});
     ren.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
     ren.shadowMap.enabled=true; ren.shadowMap.type=THREE.PCFSoftShadowMap;
     ren.outputEncoding=THREE.sRGBEncoding; ren.toneMapping=THREE.ACESFilmicToneMapping;
     ren.toneMappingExposure=1.05;
     D.kameralar.forEach(function(k,i){{var b=document.createElement("button");
       b.type="button"; b.textContent=(i+1)+" · "+k.baslik;
       b.onclick=function(){{cam=i;kur();}}; document.getElementById("cams").appendChild(b);}});
     Object.keys(D.stiller).forEach(function(k){{var b=document.createElement("button");
       b.type="button"; b.textContent=D.stiller[k].ad; b.dataset.s=k;
       b.onclick=function(){{stil=k;kur();}}; document.getElementById("sty").appendChild(b);}});
     baglaKontrol(); hazir=true; kur();
   }}catch(e){{ btn.remove(); hata(e.message||"tarayıcı desteklemiyor."); }}
 }});
 function kur(){{
   scene=new THREE.Scene();
   scene.background=new THREE.Color(stil==="minimal"?0x1A222B:0x0E1620);
   scene.add(GymModel.build(D,stil));
   var k=D.kameralar[cam];
   camera=new THREE.PerspectiveCamera(k.fov,1,0.05,120);
   yaw=0;pit=0;dist=1;yerlestir();
   Array.prototype.forEach.call(document.querySelectorAll("#cams button"),
     function(b,i){{b.className=i===cam?"on":"";}});
   Array.prototype.forEach.call(document.querySelectorAll("#sty button"),
     function(b){{b.className=b.dataset.s===stil?"on":"";}});
   boyutla();
 }}
 function yerlestir(){{
   var k=D.kameralar[cam], t=new THREE.Vector3(k.hedef[0],k.hedef[1],k.hedef[2]);
   var p=new THREE.Vector3(k.poz[0],k.poz[1],k.poz[2]).sub(t);
   var sp=new THREE.Spherical().setFromVector3(p);
   sp.theta+=yaw; sp.phi=Math.max(0.25,Math.min(Math.PI-0.25,sp.phi+pit)); sp.radius*=dist;
   camera.position.copy(t.clone().add(new THREE.Vector3().setFromSpherical(sp)));
   camera.lookAt(t);
 }}
 function boyutla(){{
   if(!hazir&&!cv) return;
   var w=cv.clientWidth, h=cv.clientHeight; if(!w||!h) return;
   ren.setSize(w,h,false); camera.aspect=w/h; camera.updateProjectionMatrix();
   ren.render(scene,camera);
 }}
 function baglaKontrol(){{
   var drag=false,lx=0,ly=0;
   function down(e){{drag=true;var t=e.touches?e.touches[0]:e;lx=t.clientX;ly=t.clientY;}}
   function move(e){{if(!drag)return;var t=e.touches?e.touches[0]:e;
     yaw-=(t.clientX-lx)*0.006; pit-=(t.clientY-ly)*0.005; lx=t.clientX; ly=t.clientY;
     yerlestir(); ren.render(scene,camera); if(e.cancelable) e.preventDefault();}}
   function up(){{drag=false;}}
   cv.addEventListener("mousedown",down); window.addEventListener("mousemove",move);
   window.addEventListener("mouseup",up);
   cv.addEventListener("touchstart",down,{{passive:true}});
   cv.addEventListener("touchmove",move,{{passive:false}});
   cv.addEventListener("touchend",up);
   cv.addEventListener("wheel",function(e){{
     dist=Math.max(0.35,Math.min(3.2,dist*(1+e.deltaY*0.0012)));
     yerlestir(); ren.render(scene,camera); if(e.cancelable) e.preventDefault();
   }},{{passive:false}});
   window.addEventListener("resize",boyutla);
 }}
}})();
</script>
</body></html>"""
Path("output/Gym_Model.html").write_text(HTML, encoding="utf-8")
print(f"→ output/Gym_Model.html  ·  {len(HTML.encode())/1e6:.2f} MB  ·  {len(gal)} render gömülü")
