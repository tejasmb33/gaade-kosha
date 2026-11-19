// Synthetic transcripts, a fake microphone and mocked services; no private audio or live ASR.
const {chromium}=require('playwright'),{spawn}=require('node:child_process'),path=require('node:path'),assert=require('node:assert/strict');
let server,browser;
(async()=>{try{
 const base='http://127.0.0.1:15180';server=spawn('npm',['run','dev','--','--host','127.0.0.1','--port','15180','--strictPort'],{cwd:path.resolve(__dirname,'..'),detached:true,stdio:'ignore'});
 for(let i=0;i<80;i++){try{if((await fetch(base)).ok)break;}catch{}await new Promise(r=>setTimeout(r,150));}
 browser=await chromium.launch({executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE||undefined,args:['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream']});
 const page=await browser.newPage({permissions:['microphone'],reducedMotion:'reduce'});const errors=[];page.on('pageerror',e=>errors.push(e.message));let transcriptions=0,releaseHealth,holdHealth=false;
 await page.addInitScript(()=>{window.speechInstances=[];window.SpeechRecognition=class{constructor(){window.speechInstances.push(this);}start(){this.started=true;}stop(){this.onend?.();}abort(){this.aborted=true;this.onend?.();}};const original=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);navigator.mediaDevices.getUserMedia=async options=>{const stream=await original(options);window.__voiceTrack=stream.getAudioTracks()[0];return stream;};});
 await page.route('**/api/**',async route=>{
  const url=new URL(route.request().url());
  if(url.pathname.endsWith('/health')){if(holdHealth)await new Promise(resolve=>releaseHealth=resolve);return route.fulfill({json:{speech:{provider:'groq',configured:true},cloud_ai:{configured:false}}});}
  if(url.pathname.endsWith('/search/voice')){const body=route.request().postDataBuffer().toString();assert(body.includes('\r\nen\r\n')&&body.includes('\r\ntranscribe\r\n'));transcriptions++;return route.fulfill({json:{text:'Synthetic editable voice situation '+transcriptions,task:'transcribe'}});}
  return route.fulfill({json:{items:[]}});
 });
 await page.goto(base+'/#home');const method=page.getByRole('combobox',{name:'Voice input method',exact:true}),input=page.getByRole('textbox',{name:'Describe your situation',exact:true});
 await page.waitForFunction(()=>document.querySelector('select[aria-label="Voice input method"]').value==='local');
 async function recordAndCheck(){const expected=transcriptions+1;await page.getByRole('button',{name:'Record situation',exact:true}).click();await page.waitForFunction(()=>document.querySelector('meter')?.value>0);await new Promise(r=>setTimeout(r,700));await page.getByRole('button',{name:'Stop situation recording',exact:true}).click();await page.waitForFunction(expected=>document.querySelector('input[aria-label="Describe your situation"]').value==='Synthetic editable voice situation '+expected,expected);assert.equal(await page.evaluate(()=>window.__voiceTrack.readyState),'ended');assert.equal(await page.getByRole('alert').count(),0);assert(await input.isEnabled());}
 await recordAndCheck();assert.equal(transcriptions,1,'Stop automatically transcribes exactly once');await input.fill('Edited synthetic situation');
 for(const code of ['network','service-not-allowed','language-not-supported']){
  await method.selectOption('browser');await page.getByRole('button',{name:'Record situation',exact:true}).click();await page.evaluate(code=>window.speechInstances.at(-1).onerror({error:code}),code);
  await page.waitForFunction(()=>document.querySelector('select[aria-label="Voice input method"]').value==='local');assert.equal(await page.getByRole('alert').count(),0);assert(await page.evaluate(()=>window.speechInstances.at(-1).aborted));await recordAndCheck();
 }
 await method.selectOption('browser');await page.getByRole('button',{name:'Record situation',exact:true}).click();await page.evaluate(()=>window.speechInstances.at(-1).onerror({error:'not-allowed'}));await page.getByRole('alert').filter({hasText:'ಮೈಕ್ರೊಫೋನ್ ಅನುಮತಿ'}).waitFor();assert.equal(await method.inputValue(),'browser','Permission denial is not bypassed');
 holdHealth=true;await page.reload();await method.selectOption('local');await method.selectOption('browser');await page.getByRole('button',{name:'Record situation',exact:true}).click();await page.waitForFunction(()=>window.speechInstances.at(-1)?.started);holdHealth=false;releaseHealth();await new Promise(r=>setTimeout(r,200));assert.equal(await method.inputValue(),'browser','Late health response must not switch active speech');
 await page.goto(base+'/#about');assert(await page.evaluate(()=>window.speechInstances.at(-1).aborted));
 await page.goto(base+'/#home');await page.waitForFunction(()=>document.querySelector('select[aria-label="Voice input method"]').value==='local');await page.evaluate(()=>navigator.mediaDevices.getUserMedia=async()=>{throw new DOMException('Synthetic permission rejection','NotAllowedError');});await page.getByRole('button',{name:'Record situation',exact:true}).click();await page.getByRole('alert').filter({hasText:'blocked'}).waitFor();assert(!(await page.getByRole('alert').innerText()).includes('localhost'));
 for(const width of [1440,390]){await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));}
 assert.deepEqual(errors,[]);console.log('PASS: hosted recording default, Stop auto-transcription, browser network/service/language recovery, permission handling, late health safety, microphone cleanup and mobile layout');
}finally{if(browser)await browser.close();if(server&&server.exitCode===null){process.kill(-server.pid,'SIGTERM');await new Promise(r=>server.once('exit',r));}}})().catch(e=>{console.error(e);process.exitCode=1});
