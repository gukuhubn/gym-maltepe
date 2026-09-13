# -*- coding: utf-8 -*-
"""Tek dosya offline model + render galerisi — ES module ve fetch YOK, her şey gömülü."""
import sys, os, json, base64, io, glob
sys.path.insert(0, os.path.dirname(__file__))
from pathlib import Path
from PIL import Image
import proj as P

THREE = Path("site/vendor/three.min.js").read_text()
MODEL = Path("site/model.js").read_text()
DIM   = Path("data/dimensions.json").read_text()

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
    gal.append({"ad": ad, "baslik": BAS.get(kam, kam), "stil": D["stiller"][stil]["ad"],
                "stilkod": stil, "src": jpg(p)})
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

HTML = f"""<!doctype html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Maltepe / İdealtepe — Gym Dönüşümü · {P.REV}</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;background:#0E1620;color:#E7EDF3;
 font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}}
header{{padding:22px 18px 16px;border-bottom:3px solid #B87333;background:#16273D}}
h1{{margin:0;font-size:20px;letter-spacing:.01em}}
.sub{{color:#8FA6BE;font-size:13px;margin-top:5px}}
nav{{display:flex;gap:6px;padding:12px 18px;background:#101C29;position:sticky;top:0;z-index:10;
 overflow-x:auto;border-bottom:1px solid #1E3350}}
nav button{{background:#1B2B40;color:#C9D6E4;border:1px solid #2E4D70;border-radius:6px;
 padding:8px 13px;font-size:13px;cursor:pointer;white-space:nowrap}}
nav button.on{{background:#B87333;border-color:#B87333;color:#fff;font-weight:600}}
section{{display:none;padding:18px}} section.on{{display:block}}
.grid{{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}}
.card{{background:#16232F;border:1px solid #24405F;border-radius:9px;padding:14px}}
.card .k{{color:#B87333;font-size:11px;font-weight:700;letter-spacing:.07em;text-transform:uppercase}}
.card .v{{font-size:25px;font-weight:700;margin:7px 0 3px}}
.card .n{{color:#8FA6BE;font-size:12px}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}}
th{{background:#1B2B40;color:#fff;text-align:left;padding:9px 10px;font-size:12px;
 text-transform:uppercase;letter-spacing:.05em}}
td{{padding:9px 10px;border-bottom:1px solid #1E3350;color:#D5DFE9}}
td.n{{text-align:right;font-variant-numeric:tabular-nums}}
tr:nth-child(even) td{{background:#121E2A}}
figure{{margin:0 0 14px;background:#16232F;border:1px solid #24405F;border-radius:9px;overflow:hidden}}
figure img{{width:100%;display:block}}
figcaption{{padding:9px 12px;font-size:12px;color:#9FB4C9;display:flex;justify-content:space-between;gap:8px}}
figcaption b{{color:#E7EDF3}}
#wrap{{position:relative;background:#0A1119;border:1px solid #24405F;border-radius:9px;overflow:hidden}}
#c{{display:block;width:100%;height:64vh;min-height:300px}}
.ctrl{{display:flex;gap:6px;flex-wrap:wrap;padding:11px 0}}
.ctrl button{{background:#1B2B40;color:#C9D6E4;border:1px solid #2E4D70;border-radius:6px;
 padding:7px 11px;font-size:12px;cursor:pointer}}
.ctrl button.on{{background:#B87333;border-color:#B87333;color:#fff}}
.uyari{{background:#2A1C20;border:1px solid #C8322B;border-radius:9px;padding:13px;margin:12px 0}}
.uyari b{{color:#E5837E}}
.not{{color:#5E7690;font-size:11.5px;padding:14px 18px;border-top:1px solid #1E3350}}
h2{{font-size:16px;margin:22px 0 8px;color:#fff}} h2:first-child{{margin-top:4px}}
ul{{padding-left:20px}} li{{margin:5px 0;color:#C9D6E4;font-size:13.5px}}
@media(max-width:520px){{.card .v{{font-size:21px}} #c{{height:46vh}}}}
</style></head><body>
<header>
 <h1>Mobilya mağazası → Fonksiyonel antrenman stüdyosu</h1>
 <div class="sub">Maltepe / İdealtepe · İstanbul &nbsp;·&nbsp; {P.REV} &nbsp;·&nbsp; {P.TARIH}
 &nbsp;·&nbsp; ön tasarım — yerinde doğrulanacak</div>
</header>
<nav id="nav"></nav>
<section id="s-ozet" class="on">
 <div class="grid">
 {''.join(f'<div class="card"><div class="k">{k}</div><div class="v">{v}</div><div class="n">{n}</div></div>' for k,v,n in KPI)}
 </div>
 <div class="uyari"><b>EN KRİTİK BULGU —</b> Mevzuatın il müdürlüklerince yaygın uygulanan
 biçiminde spor salonlarında en az 125 m² çalışma alanı, 15'er m² kadın/erkek soyunma ve 15 m²
 dinlenme salonu ile toplam en az 170 m² aranmaktadır. Bu birimin net iç alanı
 {P.A['ic_toplam']:.2f} m²'dir. Kapalı alanı artırmak için bahçelerin kapatılması işveren kararıyla
 kapsam dışıdır — ön ve arka bahçe açık kullanımda kalır, hiçbir alan hesabına girmez.
 Yönetmelik metninin kendisi salon için m² şartı getirmez (soyunma ≥8 m², dinlenme ≥15 m² der) ve
 bu iki şart mevcut planda sağlanır. Yatırımın ilk adımı imalat değil,
 İstanbul GSİM'den alınacak <b>yazılı ön görüş</b>tür.</div>
 <h2>Zemin bölgeleri</h2>
 <table><tr><th>Bölge</th><th style="text-align:right">m²</th><th>Kaplama</th><th>Kalınlık</th></tr>
 {''.join(f'<tr><td>{a}</td><td class="n">{b:.2f}</td><td>{c_}</td><td>{d_}</td></tr>'.replace(">"+f"{b:.2f}"+"<", ">"+f"{b:.2f}".replace(".",",")+"<") for a,b,c_,d_ in BOLGE)}
 </table>
</section>
<section id="s-model">
 <div id="wrap"><canvas id="c"></canvas></div>
 <div class="ctrl" id="cams"></div><div class="ctrl" id="sty"></div>
 <div class="n" style="color:#5E7690;font-size:12px">Sürükle: döndür · iki parmak / tekerlek: yakınlaş.
 Temsilî kütle modeli — imalat ölçüsü değildir.</div>
</section>
<section id="s-render"></section>
<section id="s-adim">
 <h2>Sonraki 5 adım</h2><ul>
 {''.join(f'<li><b>{n}. {t}</b> — {b}</li>' for n,t,b in P.SONRAKI_5)}</ul>
 <h2>İşverenden istenecekler</h2><ul>
 <li>DXF export (AutoCAD R2010)</li><li>Mevcut durum fotoğrafları (salon, giriş, soyunma koridoru)</li>
 <li>Ölçülmüş net m² ve tavan yüksekliği</li><li>Satın alınan ekipman listesi (marka/model/ölçü/ağırlık)</li>
 <li>Pis su bağlantısı fotoğrafı ve kotu</li><li>Elektrik pano gücü ve trifaze durumu</li>
 <li>Tapu bağımsız bölüm niteliği ve iskân belgesi</li>
 <li>Bina bağımsız mı; değilse yönetim planı ve kat malikleri durumu</li>
 <li>Hedeflenen açılış tarihi ve üye kapasitesi</li></ul>
 <h2>Ölçü dayanağı</h2>
 <ul><li>DWG dosyası AutoCAD 2018 (AC1032) formatında ve bu ortamda açılamadı.</li>
 <li>PDF paftaları vektör değil JPEG raster; geometri renk alanları izlenerek vektörleştirildi.</li>
 <li>Paftanın kendi m² etiketleriyle kalibre edildi — üç bölgede sapma %3'ün altında.</li>
 <li>Uygulama projesi için işverenden DXF (R2010) export istenmelidir.</li></ul>
</section>
<div class="not">Ön tasarım — yerinde doğrulanmadan ve ruhsat alınmadan uygulama yapılamaz.
Görseller temsilîdir, imalat ölçüsü değildir. Yerel uygulama farklılık gösterebilir;
Maltepe Belediyesi Ruhsat ve Denetim Müdürlüğü ile İstanbul Gençlik ve Spor İl Müdürlüğü'nden
güncel liste teyit edilmelidir.</div>
<script>{THREE}</script>
<script>{MODEL}</script>
<script>
var D={DIM};
var GAL={json.dumps(gal, ensure_ascii=False)};
/* ——— sekmeler ——— */
var SEK=[["s-ozet","Özet"],["s-model","3B model"],["s-render","Render galerisi"],["s-adim","Sonraki adımlar"]];
var nav=document.getElementById("nav");
SEK.forEach(function(s,i){{var b=document.createElement("button");b.textContent=s[1];
 b.className=i===0?"on":"";b.onclick=function(){{
  document.querySelectorAll("section").forEach(function(x){{x.className=""}});
  document.getElementById(s[0]).className="on";
  nav.querySelectorAll("button").forEach(function(x){{x.className=""}});b.className="on";
  if(s[0]==="s-model"){{resize();}} }};nav.appendChild(b);}});
/* ——— galeri ——— */
var g=document.getElementById("s-render");
GAL.forEach(function(r){{var f=document.createElement("figure");
 f.innerHTML='<img loading="lazy" src="'+r.src+'"><figcaption><b>'+r.baslik+' · '+r.stil+
 '</b><span>temsilî görsel — imalat ölçüsü değildir</span></figcaption>';g.appendChild(f);}});
/* ——— 3B ——— */
var cv=document.getElementById("c");
var ren=new THREE.WebGLRenderer({{canvas:cv,antialias:true}});
ren.setPixelRatio(Math.min(devicePixelRatio,2));ren.shadowMap.enabled=true;
ren.shadowMap.type=THREE.PCFSoftShadowMap;ren.outputEncoding=THREE.sRGBEncoding;
ren.toneMapping=THREE.ACESFilmicToneMapping;ren.toneMappingExposure=1.05;
var stil="endustriyel",cam=0,scene,camera,yaw=0,pit=0,dist=1;
function kur(){{
 scene=new THREE.Scene();
 scene.background=new THREE.Color(stil==="minimal"?0x1A222B:0x0E1620);
 scene.add(GymModel.build(D,stil));
 var k=D.kameralar[cam];
 camera=new THREE.PerspectiveCamera(k.fov,1,0.05,120);
 yaw=0;pit=0;dist=1;yerlestir();
 document.querySelectorAll("#cams button").forEach(function(b,i){{b.className=i===cam?"on":""}});
 document.querySelectorAll("#sty button").forEach(function(b){{b.className=b.dataset.s===stil?"on":""}});
 resize();
}}
function yerlestir(){{
 var k=D.kameralar[cam],t=new THREE.Vector3(k.hedef[0],k.hedef[1],k.hedef[2]);
 var p=new THREE.Vector3(k.poz[0],k.poz[1],k.poz[2]).sub(t);
 var sp=new THREE.Spherical().setFromVector3(p);
 sp.theta+=yaw;sp.phi=Math.max(0.25,Math.min(Math.PI-0.25,sp.phi+pit));sp.radius*=dist;
 camera.position.copy(t.clone().add(new THREE.Vector3().setFromSpherical(sp)));
 camera.lookAt(t);
}}
function resize(){{var w=cv.clientWidth,hh=cv.clientHeight;if(!w||!hh)return;
 ren.setSize(w,hh,false);camera.aspect=w/hh;camera.updateProjectionMatrix();ren.render(scene,camera);}}
D.kameralar.forEach(function(k,i){{var b=document.createElement("button");
 b.textContent=(i+1)+" · "+k.baslik;b.onclick=function(){{cam=i;kur()}};
 document.getElementById("cams").appendChild(b);}});
Object.keys(D.stiller).forEach(function(k){{var b=document.createElement("button");
 b.textContent=D.stiller[k].ad;b.dataset.s=k;b.onclick=function(){{stil=k;kur()}};
 document.getElementById("sty").appendChild(b);}});
var drag=false,lx=0,ly=0;
function down(e){{drag=true;var t=e.touches?e.touches[0]:e;lx=t.clientX;ly=t.clientY;}}
function move(e){{if(!drag)return;var t=e.touches?e.touches[0]:e;
 yaw-=(t.clientX-lx)*0.006;pit-=(t.clientY-ly)*0.005;lx=t.clientX;ly=t.clientY;
 yerlestir();ren.render(scene,camera);e.preventDefault();}}
function up(){{drag=false}}
cv.addEventListener("mousedown",down);addEventListener("mousemove",move);addEventListener("mouseup",up);
cv.addEventListener("touchstart",down,{{passive:true}});
cv.addEventListener("touchmove",move,{{passive:false}});cv.addEventListener("touchend",up);
cv.addEventListener("wheel",function(e){{dist=Math.max(0.35,Math.min(3.2,dist*(1+e.deltaY*0.0012)));
 yerlestir();ren.render(scene,camera);e.preventDefault();}},{{passive:false}});
addEventListener("resize",resize);
kur();
</script></body></html>"""
Path("output/Gym_Model.html").write_text(HTML, encoding="utf-8")
mb = len(HTML.encode())/1e6
print(f"→ output/Gym_Model.html  ·  {mb:.2f} MB  ·  {len(gal)} render gömülü")
