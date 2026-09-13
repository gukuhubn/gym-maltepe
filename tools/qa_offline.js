/* Gym_Model.html gerçekten offline mı? Dosya dışı her isteği reddet, hata var mı bak. */
const {chromium}=require('playwright');
(async()=>{
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
 await p.goto('file://'+process.argv[2],{waitUntil:'load'});
 await p.waitForTimeout(2000);
 const n=await p.evaluate(()=>({
   sekme:document.querySelectorAll('#nav button').length,
   render:document.querySelectorAll('#s-render figure').length,
   canvas:!!document.querySelector('#c').getContext,
   satir:document.querySelectorAll('#s-ozet table tr').length }));
 // 3B sekmesi
 await p.locator('#nav button').nth(1).click(); await p.waitForTimeout(1500);
 const boy=await p.evaluate(()=>{const c=document.getElementById('c');
   return c.width>200 && c.height>150;});
 const tasma=await p.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+2);
 console.log(JSON.stringify({disIstek:dis, hata:errs, ...n, canvasBoyut:boy, yatayTasma:tasma}));
 await b.close();
})().catch(e=>{console.log(JSON.stringify({hata:[String(e.message)]}));process.exit(1)});
