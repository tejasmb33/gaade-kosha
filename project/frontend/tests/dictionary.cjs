// Synthetic entries in an isolated temporary database; no real collection or AI calls.
const {chromium}=require('playwright');const {spawn,spawnSync}=require('node:child_process');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),temp=fs.mkdtempSync(path.join(os.tmpdir(),'gaade-dictionary-'));
const python=process.env.GAADE_TEST_PYTHON||(fs.existsSync(path.join(root,'.venv/bin/python'))?path.join(root,'.venv/bin/python'):'python3');
const base='http://127.0.0.1:15174',wait=ms=>new Promise(r=>setTimeout(r,ms));let server,browser;
async function main(){
 let log='';server=spawn(python,['scripts/dev.py','--frontend-port','15174','--backend-port','18124','--data-dir',temp,'--config-file',path.join(temp,'absent.env')],{cwd:root,env:{...process.env,ADMIN_TOKEN:'',E5_MODEL_PATH:'',WHISPER_MODEL_PATH:'',GEMINI_API_KEY:'',GROQ_API_KEY:'',OPENAI_API_KEY:'',GAADE_AI_PROVIDER:''},stdio:['ignore','pipe','pipe']});
 server.stdout.on('data',x=>log+=x);server.stderr.on('data',x=>log+=x);
 for(let i=0;i<100&&!log.includes('Ready:');i++){if(server.exitCode!==null)throw Error(log);await wait(200);}assert(log.includes('Ready:'),log);
 browser=await chromium.launch({headless:true,...(process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE?{executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE}:{})});
 const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'/#dictionary');await page.getByRole('heading',{name:'No entries found'}).waitFor();
 const token=fs.readFileSync(path.join(temp,'admin-token'),'utf8').trim();
 const api=async(route,body,method='POST')=>{const response=await fetch(base+'/api'+route,{method,headers:{'Content-Type':'application/json','X-Admin-Token':token},body:JSON.stringify(body)});assert(response.ok,await response.clone().text());return response.json();};
 const entries=[];
 for(let i=0;i<14;i++){
  const body={proverb_kn:'ಪರೀಕ್ಷೆ '+String(i).padStart(2,'0')+' — synthetic fixture',literal_meaning:'Synthetic literal meaning '+i,contextual_meaning:'Synthetic contextual meaning '+i,example_usage:'Synthetic example situation '+i,transliteration:'Synthetic transliteration '+i,category:i<7?'Synthetic A':'Synthetic B',keywords:'synthetic, fixture'+i,source:'https://example.org/synthetic/'+i,contributor:'Synthetic tester'};
  const row=await api('/contributions',body);await api('/admin/contributions/'+row.id+'/approve',body,'PATCH');entries.push({...body,id:row.id});
 }
 const pending=await api('/contributions',{proverb_kn:'ಗೋಪ್ಯ ಪರೀಕ್ಷೆ',literal_meaning:'Synthetic pending fixture',contextual_meaning:'Synthetic private fixture'});
 const cached=spawnSync(python,['-c',`import sys,os,json
from pathlib import Path
sys.path.insert(0,sys.argv[1]);os.environ['GAADE_DATA_DIR']=sys.argv[2]
from backend.app import create_app,Proverb
from backend.dictionary_translations import fingerprint
app=create_app(sys.argv[2])
with app.state.Session() as session:
 row=session.get(Proverb,sys.argv[3]);digest=fingerprint(row)
folder=Path(sys.argv[2])/'translations';folder.mkdir(exist_ok=True)
fields={'proverb_en':'Synthetic English rendering','literal_meaning_kn':'ಪರೀಕ್ಷೆಯ ಪದಶಃ ಅರ್ಥ','contextual_meaning_kn':'ಪರೀಕ್ಷೆಯ ವಿವರಣೆ','example_usage_kn':'ಪರೀಕ್ಷೆಯ ಉದಾಹರಣೆ','category_kn':'ಪರೀಕ್ಷಾ ವರ್ಗ','keywords_kn':'ಪರೀಕ್ಷೆ','keywords_en':'synthetic','region_kn':'','dialect_kn':''}
(folder/(sys.argv[3]+'.json')).write_text(json.dumps({'status':'MACHINE_TRANSLATION_DRAFT','input_hash':digest,'fields':fields}))`,root,temp,entries[3].id],{encoding:'utf8'});assert.equal(cached.status,0,cached.stderr);
 await page.reload();await page.locator('.dictionary-row').first().waitFor();assert.equal(await page.locator('.dictionary-row').count(),12);
 assert((await page.locator('.dictionary-row h2').first().textContent()).includes('ಪರೀಕ್ಷೆ 00'));
 await page.getByRole('button',{name:'Next dictionary page',exact:true}).click();await page.waitForFunction(()=>document.querySelectorAll('.dictionary-row').length===2);
 await page.getByRole('textbox',{name:'Search dictionary'}).fill('fixture3');await page.waitForFunction(()=>document.querySelectorAll('.dictionary-row').length===1);
 await page.locator('.dictionary-row').click();await page.getByRole('heading',{name:'Meaning & relevance'}).waitFor();
 assert(page.url().includes('#dictionary/'+entries[3].id));
 await page.getByText('ಪರೀಕ್ಷೆಯ ಪದಶಃ ಅರ್ಥ',{exact:true}).waitFor();
 await page.getByText('ಅನುವಾದ: ಕರಡು',{exact:true}).waitFor();
 await page.getByText('Synthetic literal meaning 3',{exact:true}).waitFor();await page.getByText('Synthetic example situation 3',{exact:true}).waitFor();
 await page.getByRole('link',{name:'https://example.org/synthetic/3'}).waitFor();
 assert.equal(await page.getByText('Not documented',{exact:true}).count(),2);
 assert.equal(await page.evaluate(()=>document.activeElement.tagName),'H1');
 await page.reload();await page.getByRole('heading',{name:'When does it fit?'}).waitFor();
 assert(await page.locator('.dictionary-related a').count()>0);await page.locator('.dictionary-related a').first().click();await page.getByRole('heading',{name:'Meaning & relevance'}).waitFor();
 await page.getByRole('link',{name:'Back to dictionary'}).click();await page.locator('.dictionary-row').first().waitFor();
 await page.getByLabel('Dictionary category',{exact:true}).selectOption('Synthetic B');await page.waitForFunction(()=>document.querySelectorAll('.dictionary-row').length===7);
 await page.goto(base+'/#dictionary/'+pending.id);await page.getByRole('heading',{name:'Entry unavailable'}).waitFor();
 await page.setViewportSize({width:390,height:844});await page.getByRole('button',{name:'Toggle navigation'}).click();await page.getByRole('button',{name:'Dictionary',exact:true}).click();await page.locator('.dictionary-row').first().waitFor();
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile list overflow');
 await page.locator('.dictionary-row').first().click();await page.getByRole('heading',{name:'When does it fit?'}).waitFor();assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile entry overflow');
 await page.setViewportSize({width:800,height:1000});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Tablet overflow');
 assert.deepEqual(errors,[]);
 console.log('PASS: honest empty state, ordered/paginated dictionary, filters, full details, reference link, missing metadata, focus, deep-link reload, related entries, private-record protection, mobile navigation/layout, no JS errors');
}
main().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();if(server&&server.exitCode===null){server.kill('SIGTERM');await new Promise(r=>server.once('exit',r));}fs.rmSync(temp,{recursive:true,force:true});});
