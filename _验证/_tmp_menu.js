
const puppeteer=require('puppeteer-core');
(async()=>{
 const b=await puppeteer.launch({executablePath:String.rawC:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe,headless:'new',args:['--no-sandbox'],defaultViewport:{width:1500,height:1100}});
 const p=await b.newPage();
 await p.evaluateOnNewDocument(()=>localStorage.setItem('bp.ui.style','classic'));
 await p.goto('http://192.168.31.11:8080/',{waitUntil:'networkidle2'});
 await new Promise(r=>setTimeout(r,1200));
 await p.evaluate(()=>{const el=document.querySelectorAll('input');const s=(i,v)=>{el[i].focus();el[i].value=v;el[i].dispatchEvent(new Event('input',{bubbles:true}));el[i].dispatchEvent(new Event('change',{bubbles:true}));};s(0,'350600');s(1,'admin');s(2,'admin123');});
 await p.evaluate(()=>{const x=Array.from(document.querySelectorAll('button')).find(v=>/登\\s*录/.test(v.innerText||''));x&&x.click();});
 await new Promise(r=>setTimeout(r,5000));
 const items=await p.evaluate(()=>Array.from(document.querySelectorAll('.el-menu-item,.el-sub-menu__title')).map(e=>(e.textContent||'').trim()));
 console.log(JSON.stringify(items,null,0));
 await b.close();
})();
