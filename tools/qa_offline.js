/* Gym_Model.html iki senaryoda da çalışıyor mu?
   1) JS AÇIK, dosya dışı her istek reddedilmiş → gerçekten offline mı, 3B açılıyor mu
   2) JS KAPALI (iOS Quick Look / sohbet önizlemesi) → tüm içerik okunabiliyor mu */
const {chromium, devices}=require('playwright');
(async()=>{
 const F='file://'+process.argv[2];
 const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
   args:['--no-sandbox','--use-gl=swiftshader','--enable-unsafe-swiftshader']});

 const ctx=await b.newContext({viewport:{width:1280,height:900}});
 const dis=[], errs=[];
 await ctx.route('**/*', r=>{
   const u=r.request().url();
   if(u.startsWith('file:')||u.startsWith('data:')||u.startsWith('blob:')) return r.continue();
   dis.push(u); return r.abort();
 });
 const p=await ctx.newPage();
 p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
 p.on('pageerror',e=>errs.push('PAGEERROR '+e.message));
 await p.goto(F,{waitUntil:'load'});
 await p.waitForTimeout(1500);
 const n=await p.evaluate(()=>({
   nav:document.querySelectorAll('nav a').length,
   render:document.querySelectorAll('#render figure').length,
   bolum:document.querySelectorAll('section').length }));
 await p.locator('#basla').click();
 await p.waitForTimeout(4000);
 const boy=await p.evaluate(()=>{const c=document.getElementById('c');
   return !!c && c.width>200 && c.height>150;});
 const kamDugme=await p.$$eval('#cams button',b=>b.length).catch(()=>0);
 const tasma=await p.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+2);

 // ── JS KAPALI senaryosu (telefon önizlemesi)
 const c2=await b.newContext({...devices['iPhone 13'], javaScriptEnabled:false});
 const p2=await c2.newPage();
 await p2.goto(F,{waitUntil:'load'}); await p2.waitForTimeout(400);
 const njs=await p2.evaluate(()=>({
   gorunurBolum:Array.prototype.filter.call(document.querySelectorAll('section'),
     s=>getComputedStyle(s).display!=='none').length,
   bolum:document.querySelectorAll('section').length,
   nav:document.querySelectorAll('nav a').length,
   render:document.querySelectorAll('#render figure').length,
   tabloSatir:document.querySelectorAll('table tbody tr').length,
   yukseklik:document.body.scrollHeight }));
 const njsTasma=await p2.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+2);

 console.log(JSON.stringify({disIstek:dis, hata:errs, ...n, canvasBoyut:boy,
   kamDugme, yatayTasma:tasma, nojs:njs, nojsTasma:njsTasma}));
 await b.close();
})().catch(e=>{console.log(JSON.stringify({hata:[String(e.message)]}));process.exit(1)});
