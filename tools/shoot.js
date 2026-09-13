const {chromium}=require('playwright');
const http=require('http'), fs=require('fs'), path=require('path'), url=require('url');
const ROOT=process.argv[2]||process.cwd(), OUT=process.argv[3]||'work/model';
const MIME={'.html':'text/html','.js':'text/javascript','.json':'application/json','.png':'image/png','.css':'text/css'};
const srv=http.createServer((req,res)=>{
  let p=path.join(ROOT, decodeURIComponent(url.parse(req.url).pathname));
  if(p.endsWith('/')) p+='index.html';
  fs.readFile(p,(e,d)=>{ if(e){res.writeHead(404);res.end('404');return;}
    res.writeHead(200,{'Content-Type':MIME[path.extname(p)]||'application/octet-stream'}); res.end(d);});
});
(async()=>{
  await new Promise(r=>srv.listen(8799,r));
  fs.mkdirSync(OUT,{recursive:true});
  const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
        args:['--no-sandbox','--use-gl=swiftshader','--enable-unsafe-swiftshader']});
  const pg=await b.newPage({viewport:{width:1600,height:1000},deviceScaleFactor:1});
  pg.on('console',m=>{if(m.type()==='error')console.log('  [browser]',m.text())});
  const dims=JSON.parse(fs.readFileSync(path.join(ROOT,'data/dimensions.json'),'utf8'));
  for(const stil of Object.keys(dims.stiller)){
    for(let i=0;i<dims.kameralar.length;i++){
      await pg.goto(`http://127.0.0.1:8799/site/index.html?cam=${i}&style=${stil}&ui=0`,{waitUntil:'networkidle'});
      await pg.waitForFunction('window.__ready===true',{timeout:30000});
      await pg.waitForTimeout(700);
      const name=`${dims.kameralar[i].ad}_${stil}.png`;
      await pg.locator('#c').screenshot({path:path.join(OUT,name)});
      console.log('  →',name);
    }
  }
  await b.close(); srv.close(); process.exit(0);
})().catch(e=>{console.error('HATA',e.message);process.exit(1)});
