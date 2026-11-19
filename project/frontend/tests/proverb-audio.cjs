// Synthetic media and API fixtures only; no user recordings or external providers.
const {chromium}=require('playwright'),{spawn}=require('node:child_process'),path=require('node:path'),assert=require('node:assert/strict');
let browser,server;
(async()=>{try{
 const base='http://127.0.0.1:15179';server=spawn('npm',['run','dev','--','--host','127.0.0.1','--port','15179','--strictPort'],{cwd:path.resolve(__dirname,'..'),detached:true,stdio:'ignore'});
 for(let i=0;i<80;i++){try{if((await fetch(base)).ok)break;}catch{}await new Promise(r=>setTimeout(r,150));}
 const pcm=Buffer.alloc(24000*2*4),header=Buffer.alloc(44);header.write('RIFF');header.writeUInt32LE(36+pcm.length,4);header.write('WAVEfmt ',8);header.writeUInt32LE(16,16);header.writeUInt16LE(1,20);header.writeUInt16LE(1,22);header.writeUInt32LE(24000,24);header.writeUInt32LE(48000,28);header.writeUInt16LE(2,32);header.writeUInt16LE(16,34);header.write('data',36);header.writeUInt32LE(pcm.length,40);
 const wav=Buffer.concat([header,pcm]);
 const row={id:'synthetic-audio',proverb_kn:'ಕೃತಕ ಪರೀಕ್ಷಾ ಗಾದೆ',literal_meaning:'Synthetic literal',contextual_meaning:'Synthetic meaning',example_usage:'Synthetic example',category:'Synthetic',keywords:'synthetic',source:'https://example.org/synthetic',related:[],reading_audio:{url:'/api/proverbs/synthetic-audio/audio',media_type:'audio/mpeg'},display:{proverb_en:'Synthetic English',contextual_meaning_kn:'ಕೃತಕ ಅರ್ಥ',example:{kn:'ಕೃತಕ ಉದಾಹರಣೆ',en:'Synthetic example'},situations:[{kn:'ಕೃತಕ ಸಂದರ್ಭ ಒಂದು',en:'Synthetic situation one'},{kn:'ಕೃತಕ ಸಂದರ್ಭ ಎರಡು',en:'Synthetic situation two'}]}};
 browser=await chromium.launch({executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||undefined});const page=await browser.newPage({reducedMotion:'reduce'});let audioRequests=0,narrationRequests=0;const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/api/**',async route=>{const url=new URL(route.request().url());
  if(url.pathname.endsWith('/health'))return route.fulfill({json:{cloud_ai:{configured:false}}});
  if(url.pathname.endsWith('/audio')){audioRequests++;return route.fulfill({contentType:'audio/wav',body:wav});}
  if(url.pathname.endsWith('/narration')){narrationRequests++;return route.fulfill({status:503,json:{detail:'Synthetic unavailable'}});}
  if(url.pathname.endsWith('/search'))return route.fulfill({json:{items:[row]}});
  if(url.pathname.endsWith('/categories'))return route.fulfill({json:[]});
  if(url.pathname.endsWith('/proverbs/synthetic-audio'))return route.fulfill({json:row});
  return route.fulfill({json:{items:[row],total:1}});
 });
 await page.goto(base+'/#home');await page.getByRole('textbox',{name:'Describe your situation',exact:true}).fill('Synthetic recorded-audio situation');await page.getByRole('button',{name:'Find proverbs',exact:true}).click();
 await page.getByRole('button',{name:'Play proverb audio',exact:true}).waitFor();assert.equal(audioRequests,0,'No audio downloads before click');
 await page.getByRole('button',{name:'Play proverb audio',exact:true}).click();await page.getByRole('button',{name:'Pause proverb audio',exact:true}).waitFor();assert(audioRequests>0);assert.equal(narrationRequests,0);
 await page.locator('audio[aria-label="Proverb audio recording"]').evaluate(a=>window.__suppliedAudio=a);
 await page.getByRole('button',{name:'Pause proverb audio',exact:true}).click();assert(await page.evaluate(()=>window.__suppliedAudio.paused));
 await page.getByRole('button',{name:'Play proverb audio',exact:true}).click();await page.getByRole('button',{name:'Pause proverb audio',exact:true}).waitFor();
 await page.goto(base+'/#dictionary');await page.locator('.dictionary-row').waitFor();assert(await page.evaluate(()=>window.__suppliedAudio.paused));await page.getByRole('button',{name:'Play proverb audio',exact:true}).waitFor();
 await page.locator('.dictionary-row').click();await page.locator('.proverb-information').waitFor();await page.getByRole('button',{name:'Play proverb audio',exact:true}).click();await page.getByRole('button',{name:'Pause proverb audio',exact:true}).waitFor();
 await page.getByRole('button',{name:'Listen to Kannada explanation',exact:true}).waitFor();
 for(const width of [1440,390]){await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'No horizontal overflow');}
 assert.equal(narrationRequests,0);assert.deepEqual(errors,[]);
 console.log('PASS: supplied audio button in chat/list/detail, lazy loading, playback/pause/resume, navigation cleanup, separate explanation button, responsive layout, no provider calls or JS errors');
}finally{if(browser)await browser.close();if(server&&server.exitCode===null){process.kill(-server.pid,'SIGTERM');await new Promise(r=>server.once('exit',r));}}})().catch(e=>{console.error(e);process.exitCode=1});
