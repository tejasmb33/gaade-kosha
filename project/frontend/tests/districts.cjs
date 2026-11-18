// Frontend-only district interactions. Uses the supplied static district dataset.
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const {spawn}=require('node:child_process');
const base=process.env.GAADE_DISTRICT_TEST_URL||'http://127.0.0.1:15175';
let browser,server;
const data=require('../src/data/karnataka-districts.json');
(async()=>{
 try{
  if(!process.env.GAADE_DISTRICT_TEST_URL){
   let log='';server=spawn('npm',['run','dev','--','--host','127.0.0.1','--port','15175','--strictPort'],{cwd:path.resolve(__dirname,'..'),detached:true,stdio:['ignore','pipe','pipe']});
   server.stdout.on('data',x=>log+=x);server.stderr.on('data',x=>log+=x);
   let ready=false;
   for(let i=0;i<80;i++){
    if(server.exitCode!==null)throw Error(log);
    try{const r=await fetch(base);if(r.ok){ready=true;break;}}catch{}
    await new Promise(r=>setTimeout(r,200));
   }
   assert(ready,'Isolated frontend did not start: '+log);
  }
  browser=await chromium.launch({executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||undefined});
  const page=await browser.newPage({viewport:{width:1440,height:1100}});const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  // Only static assets are required for this page. No cloud calls or database writes.
  await page.goto(base+'/#districts');await page.locator('.district-shape').first().waitFor();await page.locator('.launch-screen').waitFor({state:'detached'});
  assert.equal(await page.locator('.district-shape').count(),31);
  assert.equal(await page.locator('.district-list button').count(),31);
  assert.equal(await page.locator('.district-map-switch').count(),0);
  assert.equal(await page.locator('.district-map-label').count(),31);
  for(const district of data){
   const label=await page.locator('[data-label-district="'+district.id+'"] text').textContent();
   assert.equal(label.replace(/\s/g,''),district.name.kn.replace(/\s/g,''));
  }
  const flagTarget=page.locator('[data-district="vijayanagara"]');await flagTarget.focus();
  assert((await flagTarget.evaluate(el=>getComputedStyle(el).fill)).includes('-flag'));
  const colors=await page.locator('linearGradient stop').evaluateAll(stops=>stops.map(s=>s.getAttribute('stop-color')));
  assert.deepEqual(colors,['#ffdf00','#ffdf00','#d71920','#d71920']);
  for(const district of data){
   const shape=page.locator('[data-district="'+district.id+'"]');
   await shape.scrollIntoViewIfNeeded();
   const point=await shape.evaluate(el=>{
    const b=el.getBBox(),m=el.getScreenCTM(),points=[];
    for(let i=1;i<25;i++)for(let j=1;j<25;j++){
     const p=new DOMPoint(b.x+b.width*i/25,b.y+b.height*j/25);
     if(el.isPointInFill(p)){const screen=p.matrixTransform(m);if(document.elementFromPoint(screen.x,screen.y)===el)points.push({x:screen.x,y:screen.y,d:Math.hypot(i-12.5,j-12.5)});}
    }
    return points.sort((a,b)=>a.d-b.d)[0];
   });
   assert(point,'Visible clickable area for '+district.id);await page.mouse.click(point.x,point.y);
   assert.equal(await page.locator('.district-info h2').textContent(),district.name.kn);
   await page.locator('.district-photo').evaluate(img=>img.decode());
   assert(await page.locator('.district-photo').evaluate(img=>img.naturalWidth>0));
  }
  await page.getByRole('button',{name:'Show district information in English',exact:true}).click();
  assert.equal(await page.locator('.district-info h2').textContent(),'Yadgir');
  await page.getByRole('heading',{name:'Known for',exact:true}).waitFor();

  assert((await page.locator('.district-info').innerText()).includes(data.at(-1).description.en));
  const mysuru=page.locator('[data-district="mysuru"]');await mysuru.focus();await page.keyboard.press('Enter');
  assert.equal(await page.locator('.district-info h2').textContent(),'Mysuru');
  await page.getByRole('textbox',{name:'Search district names',exact:true}).fill('ಕೊಡಗು');
  assert.equal(await page.locator('.district-list button').count(),1);
  await page.locator('.district-list button').click();assert.equal(await page.locator('.district-info h2').textContent(),'Kodagu');
  await page.getByRole('textbox',{name:'Search district names',exact:true}).fill('no-such-district');
  await page.getByText('No district matches that name.',{exact:true}).waitFor();
  await page.getByRole('button',{name:'Clear district search',exact:true}).click();
  await page.getByRole('button',{name:'Close district details',exact:true}).click();await page.locator('.district-empty').waitFor();
  await mysuru.focus();await page.keyboard.press('Space');assert.equal(await page.locator('.district-info h2').textContent(),'Mysuru');
  await page.getByRole('button',{name:'Show district information in Kannada',exact:true}).click();
  assert.equal(await page.locator('.district-info h2').textContent(),'ಮೈಸೂರು');
  for(const width of [1440,1024,768,390]){
   await page.setViewportSize({width,height:1000});
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Page overflow at '+width);
  }
  await page.getByRole('combobox',{name:'ಜಿಲ್ಲೆಯನ್ನು ಆಯ್ಕೆ ಮಾಡಿ',exact:true}).selectOption('vijayanagara');
  assert.equal(await page.locator('.district-info h2').textContent(),'ವಿಜಯನಗರ');
  await page.getByRole('button',{name:'ಜಿಲ್ಲೆಯ ವಿವರಕ್ಕೆ ಹೋಗಿ',exact:true}).click();
  assert(await page.locator('.district-info').evaluate(el=>document.activeElement===el));
  await page.screenshot({path:'/tmp/gaade-districts-mobile.png',fullPage:true});
  await page.setViewportSize({width:1440,height:1100});
  await page.screenshot({path:'/tmp/gaade-districts-desktop.png',fullPage:true});
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.locator('[data-district="mysuru"]').focus();
  assert.deepEqual(errors,[]);
  console.log('PASS: default boundary map, 31 Kannada labels, yellow/red hover, reduced motion, all 31 SVG districts and supplied images, Kannada/English card content, keyboard selection, bilingual search, empty state, close/reopen, mobile selection/focus and responsive layout; no JS errors');
 }finally{if(browser)await browser.close();if(server&&server.exitCode===null){process.kill(-server.pid,'SIGTERM');await new Promise(r=>server.once('exit',r));}}
})().catch(e=>{console.error(e);process.exitCode=1});
