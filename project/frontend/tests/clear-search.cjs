// Synthetic API responses only; clears must not submit searches or mutate data.
const {chromium}=require('playwright'),{spawn}=require('node:child_process');
const assert=require('node:assert/strict'),path=require('node:path');
const base=process.env.GAADE_CLEAR_TEST_URL||'http://127.0.0.1:15176';
let browser,server;
(async()=>{try{
 if(!process.env.GAADE_CLEAR_TEST_URL){
  server=spawn('npm',['run','dev','--','--host','127.0.0.1','--port','15176','--strictPort'],{cwd:path.resolve(__dirname,'..'),detached:true,stdio:'ignore'});
  let ready=false;for(let i=0;i<80;i++){if(server.exitCode!==null)throw Error('Isolated frontend stopped');try{if((await fetch(base)).ok){ready=true;break;}}catch{}await new Promise(r=>setTimeout(r,200));}assert(ready);
 }
 browser=await chromium.launch({executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||undefined});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});const errors=[];let posts=0;
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/**',route=>{
  const r=route.request(),url=new URL(r.url());if(r.method()!=='GET')posts++;
  if(url.pathname==='/api/health')return route.fulfill({json:{backend:'ok',cloud_ai:{configured:false}}});
  if(url.pathname==='/api/categories')return route.fulfill({json:[]});
  return route.fulfill({json:{items:[],total:0,page:1,page_size:12,mode:'keyword'}});
 });
 await page.goto(base+'/#home');
 await page.locator('.launch-screen').waitFor();
 assert(await page.locator('.site-stage').evaluate(el=>el.inert));
 await page.getByRole('button',{name:'ಮುಂದುವರಿಸಿ (Skip) →',exact:true}).click();
 assert.equal(await page.locator('.launch-screen').count(),0);
 assert(!(await page.locator('.site-stage').evaluate(el=>el.inert)));
 await page.reload();assert.equal(await page.locator('.launch-screen').count(),0);
 const automatic=await browser.newContext();const opening=await automatic.newPage();await opening.route('**/api/**',r=>r.fulfill({json:{items:[],total:0}}));await opening.goto(base+'/#home');await opening.locator('.launch-screen').waitFor({state:'detached',timeout:5000});assert(!(await opening.locator('.site-stage').evaluate(el=>el.inert)));await automatic.close();
 const reduced=await browser.newContext({reducedMotion:'reduce'});const reducedPage=await reduced.newPage();
 await reducedPage.route('**/api/**',r=>r.fulfill({json:{items:[],total:0}}));
 await reducedPage.goto(base+'/#home');assert.equal(await reducedPage.locator('.launch-screen').count(),0);await reduced.close();
 for(const [route,input,clear] of [['home','Describe your situation','Clear situation'],['dictionary','Search dictionary','Clear dictionary search']]){
  await page.goto(base+'/#'+route);const field=page.getByRole('textbox',{name:input,exact:true});await field.fill('ಕನ್ನಡ situation');
  const before=posts;await page.getByRole('button',{name:clear,exact:true}).click();
  assert.equal(await field.inputValue(),'');assert(await field.evaluate(el=>document.activeElement===el));
  assert.equal(await page.getByRole('button',{name:clear,exact:true}).count(),0);assert.equal(posts,before);
 }
 const searched=page.waitForResponse(r=>r.request().method()==='POST'&&r.url().includes('/api/'));
 await page.goto(base+'/#search?Synthetic%20situation');await searched;
 await page.getByRole('button',{name:'Clear situation',exact:true}).waitFor();const before=posts;
 await page.getByRole('button',{name:'Clear situation',exact:true}).click();assert.equal(await page.getByRole('textbox',{name:'Describe your situation',exact:true}).inputValue(),'');assert.equal(posts,before);
 await page.goto(base+'/#districts');const districts=page.locator('.district-search input');await districts.fill('ಮೈಸೂರು');
 await page.locator('.district-search button').click();assert.equal(await districts.inputValue(),'');assert(await districts.evaluate(el=>document.activeElement===el));
 await page.setViewportSize({width:390,height:900});await page.goto(base+'/#home');
 await page.getByRole('textbox',{name:'Describe your situation',exact:true}).fill('Synthetic mobile situation');
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 await page.getByRole('button',{name:'Clear situation',exact:true}).click();
 assert.deepEqual(errors,[]);console.log('PASS: clear controls on home/results, dictionary and districts; editable focus restored, no accidental submits, mobile fit, no JS errors');
}finally{if(browser)await browser.close();if(server&&server.exitCode===null){process.kill(-server.pid,'SIGTERM');await new Promise(r=>server.once('exit',r));}}})().catch(e=>{console.error(e);process.exitCode=1});
