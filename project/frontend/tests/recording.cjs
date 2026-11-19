// Isolated fake-device recording checks. Does not validate the user's physical mic or Kannada ASR.
const {chromium}=require('playwright');
const {spawn}=require('node:child_process');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..');
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'gaade-recording-'));
const python=process.env.GAADE_TEST_PYTHON||(fs.existsSync(path.join(root,'.venv/bin/python'))?path.join(root,'.venv/bin/python'):'python3');
const base='http://127.0.0.1:15173';
const delay=ms=>new Promise(r=>setTimeout(r,ms));
let server,browser;
async function main(){
 let log='';
 server=spawn(python,['scripts/dev.py','--frontend-port','15173','--backend-port','18123','--data-dir',temp,'--config-file',path.join(temp,'absent.env')],{cwd:root,env:{...process.env,E5_MODEL_PATH:'',WHISPER_MODEL_PATH:'',ADMIN_TOKEN:''},stdio:['ignore','pipe','pipe']});
 server.stdout.on('data',x=>log+=x);server.stderr.on('data',x=>log+=x);
 for(let i=0;i<100&&!log.includes('Ready:');i++){if(server.exitCode!==null)throw Error(log);await delay(200);}
 assert(log.includes('Ready:'),'Isolated launcher did not start: '+log);
 browser=await chromium.launch({headless:true,...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE?{executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE}:{}),args:['--use-fake-ui-for-media-stream','--use-fake-device-for-media-stream']});
 const page=await browser.newPage({permissions:['microphone']});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'/#contribute');
 await page.evaluate(()=>{const original=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);navigator.mediaDevices.getUserMedia=async constraints=>{const stream=await original(constraints);window.__testMicTrack=stream.getAudioTracks()[0];return stream;};});
 await page.getByRole('button',{name:'Record proverb',exact:true}).click();
 await page.getByRole('button',{name:'Stop recording',exact:true}).waitFor();
 await page.waitForFunction(()=>document.querySelector('meter')?.value>0);
 await delay(1600);
 await page.getByRole('button',{name:'Stop recording',exact:true}).click();
 await page.getByText(/Recorded [0-9.]+ seconds/).waitFor();
 assert.equal(await page.evaluate(()=>window.__testMicTrack.readyState),'ended');
 await page.waitForFunction(()=>{let a=document.querySelector('audio');return a&&a.readyState>=1&&Number.isFinite(a.duration)&&a.duration>0;});
 await page.locator('audio').evaluate(async a=>{await a.play();});
 await delay(300);
 assert(await page.locator('audio').evaluate(a=>a.currentTime>0),'Playback did not advance');
 await page.getByRole('button',{name:'Upload audio',exact:true}).click();
 await page.getByRole('button',{name:'Audio uploaded',exact:true}).waitFor();
 const privateDir=path.join(temp,'audio');assert(fs.readdirSync(privateDir).length===1);
 console.log('PASS: fake microphone → input meter → stop → finite playback duration → advancing playback → real isolated API upload');
 await page.getByRole('button',{name:'Record proverb',exact:true}).click();
 await page.getByRole('button',{name:'Stop recording',exact:true}).waitFor();
 await page.getByRole('button',{name:'Our story',exact:true}).click();
 await page.waitForFunction(()=>!document.querySelector('meter'));
 assert.equal(await page.evaluate(()=>window.__testMicTrack.readyState),'ended');
 console.log('PASS: navigation safely unmounts an active recording');
 await page.goto(base+'/#contribute');
 await page.evaluate(()=>{navigator.mediaDevices.getUserMedia=()=>Promise.reject(new DOMException('Blocked','NotAllowedError'));});
 await page.getByRole('button',{name:'Record proverb',exact:true}).click();
 await page.getByRole('alert').filter({hasText:'Microphone access was blocked'}).waitFor();
 assert(await page.getByRole('button',{name:'Record proverb',exact:true}).isEnabled());
 console.log('PASS: blocked microphone shows permission guidance and allows retry');
 await page.reload();
 await page.evaluate(()=>{
  window.MediaRecorder=class EmptyRecorder{
   static isTypeSupported(){return true;}
   constructor(){this.state='inactive';this.mimeType='audio/webm';}
   start(){this.state='recording';}
   stop(){this.state='inactive';this.ondataavailable?.({data:new Blob([])});this.onstop?.();}
  };
 });
 await page.getByRole('button',{name:'Record proverb',exact:true}).click();
 await page.getByRole('button',{name:'Stop recording',exact:true}).waitFor();await delay(400);
 await page.getByRole('button',{name:'Stop recording',exact:true}).click();
 await page.getByRole('alert').filter({hasText:'No usable audio was captured'}).waitFor();
 assert.equal(await page.locator('audio').count(),0);
 console.log('PASS: empty recorder output is rejected, without a misleading playback/upload control');
 await page.reload();
 await page.goto(base+'/#home');
 await page.addInitScript(()=>{
   window.speechInstances=[];
   window.SpeechRecognition=class {
     constructor(){window.speechInstances.push(this);}
     start(){this.started=true;}
     stop(){this.onend?.();}
     abort(){this.aborted=true;this.onend?.();}
   };
 });
 await page.reload();
 await page.getByLabel('Voice input method',{exact:true}).selectOption('browser');
 for(const [language,locale,transcript] of [['en','en-IN','I need patience']]){
   await page.getByLabel('Voice input method',{exact:true}).selectOption('browser');
   await page.getByRole('button',{name:'Record situation',exact:true}).click();
   assert.equal(await page.evaluate(()=>window.speechInstances.at(-1).lang),locale);
   await page.evaluate(text=>window.speechInstances.at(-1).onresult({results:[[{transcript:text}]]}),transcript);
   await page.getByRole('button',{name:'Stop situation recording',exact:true}).click();
   assert.equal(await page.getByRole('textbox',{name:'Describe your situation'}).inputValue(),transcript);
 }
 await page.getByRole('button',{name:'Record situation',exact:true}).click();
 await page.evaluate(()=>{const r=window.speechInstances.at(-1);r.onerror({error:'not-allowed'});});
 await page.getByRole('alert').filter({hasText:'ಮೈಕ್ರೊಫೋನ್ ಅನುಮತಿ'}).waitFor();
 await page.getByRole('button',{name:'Record situation',exact:true}).click();
 await page.evaluate(()=>window.speechInstances.at(-1).onerror({error:'network'}));
 await page.waitForFunction(()=>document.querySelector('select[aria-label="Voice input method"]').value==='local');
 await page.getByText('ಧ್ವನಿ ದಾಖಲಿಸುವ ವಿಧಾನಕ್ಕೆ ಬದಲಾಯಿಸಲಾಗಿದೆ.',{exact:false}).waitFor();
 assert.equal(await page.getByRole('alert').count(),0);
 await page.getByRole('button',{name:'Record situation',exact:true}).click();
 await page.getByRole('button',{name:'Stop situation recording',exact:true}).waitFor();await delay(700);
 await page.getByRole('button',{name:'Stop situation recording',exact:true}).click();
 await page.getByRole('button',{name:'Use voice as text',exact:true}).waitFor();
 await page.getByLabel('Voice input method',{exact:true}).selectOption('browser');
 await page.getByRole('button',{name:'Record situation',exact:true}).click();
 await page.goto(base+'/#about');
 await page.waitForFunction(()=>window.speechInstances.at(-1).aborted);
 await page.goto(base+'/#home');
 console.log('PASS: browser English locale, editable transcripts, permission errors, retry and navigation cleanup (mock speech service)');
 await page.getByLabel('Voice input method',{exact:true}).selectOption('local');
 // Mock ASR text only; recording/playback uses Chromium's actual fake device.
 const speechRequests=[];
 await page.route('**/api/search/voice',async route=>{
  const body=route.request().postDataBuffer().toString();speechRequests.push(body);
  const translating=body.includes('\r\ntranslate\r\n');
  await route.fulfill({json:{text:translating?'I need patience':'ನನಗೆ ಸಹನೆ ಬೇಕು',task:translating?'translate':'transcribe',source_text:'ನನಗೆ ಸಹನೆ ಬೇಕು',warning:translating?'Automatic translation may change meaning.':null}});
 });
 await page.getByRole('button',{name:'Record situation',exact:true}).click();
 await page.getByRole('button',{name:'Stop situation recording',exact:true}).waitFor();await delay(700);
 await page.getByRole('button',{name:'Stop situation recording',exact:true}).click();
 await page.waitForFunction(()=>{const a=document.querySelector('audio');return a&&a.readyState>=1&&Number.isFinite(a.duration)&&a.duration>0;});
 await page.getByRole('button',{name:'Use voice as text',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('input[aria-label="Describe your situation"]').value==='ನನಗೆ ಸಹನೆ ಬೇಕು');
 await page.getByLabel('Voice output',{exact:true}).selectOption('translate');
 await page.getByRole('button',{name:'Translate speech to English',exact:true}).click();
 await page.waitForFunction(()=>document.querySelector('input[aria-label="Describe your situation"]').value==='I need patience');
 assert(speechRequests[0].includes('\r\nen\r\n')&&speechRequests[1].includes('\r\ntranslate\r\n'));
 await page.getByRole('textbox',{name:'Original speech transcript'}).fill('ಮನೆಗೆ ಬಾ');
 await page.getByRole('button',{name:'Use original transcript for search',exact:true}).click();
 assert.equal(await page.getByRole('textbox',{name:'Describe your situation'}).inputValue(),'ಮನೆಗೆ ಬಾ');
 await page.getByRole('textbox',{name:'Describe your situation'}).fill('A corrected situation');
 await page.getByRole('button',{name:'Find proverbs',exact:true}).click();
 await page.locator('.chat-user-bubble').filter({hasText:'A corrected situation'}).waitFor();
 await page.getByText('No reliable match yet.',{exact:true}).last().waitFor();
 await page.setViewportSize({width:390,height:844});
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'Mobile horizontal overflow');
 console.log('PASS: home voice input, editable transcription, English speech translation, corrected-query search and mobile layout (mock ASR text)');
 await page.route('**/api/search/ai',async route=>route.fulfill({json:{mode:'cloud',items:[],interpretation:'Persistence despite obstacles',message:'No reviewed match',external_sources:[{url:'https://example.org/reference',title:'Synthetic test source'}],notice:'Unverified references only'}}));
 await page.getByLabel('Search engine',{exact:true}).selectOption('cloud');
 await page.getByRole('textbox',{name:'Describe your situation'}).fill('She overcame financial difficulties and completed her education.');
 await page.getByRole('button',{name:'Find proverbs',exact:true}).click();
 await page.getByRole('heading',{name:'ಬಾಹ್ಯ ಉಲ್ಲೇಖಗಳು (Unverified web references)'}).waitFor();
 assert.equal(await page.getByRole('link',{name:'Synthetic test source'}).getAttribute('href'),'https://example.org/reference');
 await page.unroute('**/api/search/ai');
 await page.getByRole('textbox',{name:'Describe your situation'}).fill('Another cloud query without configuration');
 await page.getByRole('button',{name:'Find proverbs',exact:true}).click();
 await page.getByRole('button',{name:'ಸಾಮಾನ್ಯ ಹುಡುಕಾಟದಲ್ಲಿ ಪ್ರಯತ್ನಿಸಿ (Try local search)',exact:true}).waitFor();
 await page.getByRole('button',{name:'ಸಾಮಾನ್ಯ ಹುಡುಕಾಟದಲ್ಲಿ ಪ್ರಯತ್ನಿಸಿ (Try local search)',exact:true}).click();
 await page.getByText('No reliable match yet.',{exact:true}).last().waitFor();
 console.log('PASS: opt-in cloud mode, separately labeled web sources, missing-key error and local fallback (mock cloud response)');
 await page.route('**/api/health',route=>route.fulfill({json:{backend:'ok',cloud_ai:{provider:'gemini',configured:false,groq_configured:true}}}));
 await page.reload();
 await page.locator('option[value="groq"]').waitFor({state:'attached'});
 let groqRequested=false;
 await page.route('**/api/search/ai',async route=>{assert.equal(route.request().postDataJSON().provider,'groq');groqRequested=true;await route.fulfill({json:{mode:'cloud',provider:'groq',items:[],message:'No reliable match',external_sources:[]}});});
 await page.getByLabel('Search engine',{exact:true}).selectOption('groq');
 await page.getByRole('textbox',{name:'Describe your situation'}).fill('Synthetic Groq provider selection');
 const groqResponse=page.waitForResponse(r=>r.url().endsWith('/api/search/ai')&&r.request().postDataJSON()?.provider==='groq');
 await page.getByRole('button',{name:'Find proverbs',exact:true}).click();
 await groqResponse;
 await page.locator('.chat-user-bubble').filter({hasText:'Synthetic Groq provider selection'}).waitFor();
 await page.getByText('No reliable match yet.',{exact:true}).last().waitFor();
 assert(groqRequested);console.log('PASS: additional Groq selector routes provider-specific search without replacing Gemini (mock request)');
 const pcm=Buffer.alloc(24000*8*2);for(let i=0;i<pcm.length/2;i++)pcm.writeInt16LE(Math.round(Math.sin(i*2*Math.PI*440/24000)*2000),i*2);
 const header=Buffer.alloc(44);header.write('RIFF');header.writeUInt32LE(36+pcm.length,4);header.write('WAVE',8);header.write('fmt ',12);header.writeUInt32LE(16,16);header.writeUInt16LE(1,20);header.writeUInt16LE(1,22);header.writeUInt32LE(24000,24);header.writeUInt32LE(48000,28);header.writeUInt16LE(2,32);header.writeUInt16LE(16,34);header.write('data',36);header.writeUInt32LE(pcm.length,40);
 let narrationCalls=0;
 await page.route('**/api/proverbs/synthetic-voice/narration',route=>{narrationCalls++;return route.fulfill({contentType:'audio/wav',body:Buffer.concat([header,pcm])});});
 await page.route('**/api/search/ai',route=>route.fulfill({json:{mode:'cloud',provider:'groq',items:[{id:'synthetic-voice',proverb_kn:'ಕೃತಕ ಪರೀಕ್ಷಾ ಗಾದೆ',literal_meaning:'Synthetic literal',contextual_meaning:'Synthetic context',rank:1,why:'Synthetic fixture only',category:'Synthetic'}],external_sources:[]}}));
 await page.getByRole('textbox',{name:'Describe your situation'}).fill('Synthetic narrated result');await page.getByRole('button',{name:'Find proverbs',exact:true}).click();
 await page.getByRole('button',{name:'Listen to Kannada explanation',exact:true}).click();
 await page.getByRole('button',{name:'Pause Kannada explanation',exact:true}).waitFor();
 await page.locator('audio[aria-label="Kannada proverb explanation"]').evaluate(a=>window.__narrationAudio=a);
 await page.getByRole('button',{name:'Pause Kannada explanation',exact:true}).click();assert(await page.locator('audio[aria-label="Kannada proverb explanation"]').evaluate(a=>a.paused));
 await page.getByRole('button',{name:'Listen to Kannada explanation',exact:true}).click();await page.getByRole('button',{name:'Pause Kannada explanation',exact:true}).waitFor();
 await page.getByRole('button',{name:'Stop Kannada explanation',exact:true}).click();assert.equal(await page.locator('audio[aria-label="Kannada proverb explanation"]').evaluate(a=>a.currentTime),0);
 await page.getByRole('button',{name:'Listen to Kannada explanation',exact:true}).click();await page.getByRole('button',{name:'Pause Kannada explanation',exact:true}).waitFor();
 await page.evaluate(()=>location.hash='about');await page.waitForFunction(()=>!document.querySelector('.narration-player'));
 assert(await page.evaluate(()=>window.__narrationAudio.paused));assert.equal(narrationCalls,1);
 console.log('PASS: narration click, playback, pause/resume, stop, client replay reuse and cleanup on navigation (synthetic WAV, mocked narration API)');
 assert.deepEqual(errors,[]);console.log('PASS: no JavaScript errors');
}
main().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{
 if(browser)await browser.close();
 if(server&&server.exitCode===null){server.kill('SIGTERM');await new Promise(resolve=>server.once('exit',resolve));}
 fs.rmSync(temp,{recursive:true,force:true});
});
