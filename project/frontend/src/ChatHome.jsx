import React,{useEffect,useRef,useState} from 'react';
import {MessageCircle,Plus,ArrowRight,User,BookOpen} from 'lucide-react';
import api from './api';
import SearchBox from './SearchBox';
import {displayText} from './displayText';
import recommendations from '../../deployment/recommended-situations.json';
import './chat-home.css';

function pause(ms,signal){return new Promise(resolve=>{const done=()=>{clearTimeout(timer);signal.removeEventListener('abort',done);resolve();};const timer=setTimeout(done,ms);signal.addEventListener('abort',done,{once:true});if(signal.aborted)done();});}


function ProgressiveAnswer({row,renderCard}){
 const [visible,setVisible]=useState(0);
 const paths=[['proverb_kn']];
 if(row.display){paths.push(['display','proverb_en'],['display','contextual_meaning_kn'],['contextual_meaning'],['display','example','kn'],['display','example','en']);for(let i=0;i<2;i++)paths.push(['display','situations',i,'kn'],['display','situations',i,'en']);}
 else{paths.push(['translation','fields','proverb_en'],['translation','fields','contextual_meaning_kn'],['contextual_meaning'],['translation','fields','example_usage_kn'],['example_usage']);for(let i=0;i<(row.situations?.length||0);i++)paths.push(['situations',i,'text']);}
 const entries=paths.map(path=>[path,path.reduce((value,key)=>value?.[key],row)]).filter(([,value])=>typeof value==='string'&&value).map(([path,value])=>[path,displayText(value)]);
 const total=entries.reduce((n,[,value])=>n+value.split(/(\s+)/).length,0);
 useEffect(()=>{
  if(matchMedia('(prefers-reduced-motion: reduce)').matches){setVisible(total);return;}
  const timer=setInterval(()=>setVisible(n=>{if(n+8>=total)clearInterval(timer);return Math.min(total,n+8);}),45);
  return()=>clearInterval(timer);
 },[row,total]);
 let remaining=visible;const partial=structuredClone(row);partial.__writing=visible<total;
 for(const [path,value] of entries){const words=value.split(/(\s+)/);let target=partial;for(const key of path.slice(0,-1))target=target[key];target[path.at(-1)]=words.slice(0,Math.max(0,remaining)).join('');remaining-=words.length;}
 return <div className="chat-progressive" aria-busy={visible<total}>{renderCard(partial)}</div>;
}

export default function ChatHome({renderCard,navigate,errorText}){
 const [turns,setTurns]=useState([]),[pending,setPending]=useState(false),[draft,setDraft]=useState({text:'',revision:0}),[epoch,setEpoch]=useState(0);
 const request=useRef(null),thread=useRef(null),sequence=useRef(0),composer=useRef(null);
 useEffect(()=>()=>request.current?.abort(),[]);
 useEffect(()=>{
  const container=thread.current,last=container?.querySelector('.chat-turn:last-child');
  if(!container||!last)return;
  last.style.minHeight=container.clientHeight+'px';
  container.scrollTop+=last.getBoundingClientRect().top-container.getBoundingClientRect().top-16;
 },[turns.length]);
 async function send(query,{cloud=false,provider=null,turnId=null}={}){
  if(!query.trim()||pending)return;
  const id=turnId??++sequence.current,controller=new AbortController();request.current=controller;const started=performance.now();
  setTurns(old=>turnId?old.map(t=>t.id===id?{id,query,cloud,provider}:t):[...old,{id,query,cloud,provider}]);setPending(true);
  try{const {data}=await api.post(cloud?'/search/ai':'/search',cloud?{query,provider}:{query},{signal:controller.signal});await pause(Math.max(0,1000-(performance.now()-started)),controller.signal);if(!controller.signal.aborted)setTurns(old=>old.map(t=>t.id===id?{...t,result:data}:t));}
  catch(e){if(!controller.signal.aborted)setTurns(old=>old.map(t=>t.id===id?{...t,error:errorText(e)}:t));}
  finally{if(!controller.signal.aborted)setPending(false);}
 }
 function reset(){request.current?.abort();setPending(false);setTurns([]);setEpoch(e=>e+1);setDraft(old=>({text:'',revision:old.revision+1}));requestAnimationFrame(()=>composer.current?.querySelector('input')?.focus());}
 return <section className="chat-home" aria-label="ಗಾದಾಮೃತ ಸಂಭಾಷಣೆ">
  <aside className="chat-sidebar">
   <div className="chat-identity"><img src="/images/gaadamruta-emblem.jpeg" alt="ಗಾದಾಮೃತ"/><h1>ನಿಮ್ಮ ಸಂದರ್ಭಕ್ಕೆ<br/><em>ಸೂಕ್ತ ಗಾದೆ.</em></h1><p>A proverb for every situation.</p></div>
   <button className="chat-new" onClick={reset}><Plus size={18}/>ಹೊಸ ಸಂಭಾಷಣೆ (New chat)</button>
   {turns.length>0&&<div className="chat-history"><span>ಈ ಸಂಭಾಷಣೆಯಲ್ಲಿ (This chat)</span>{turns.map(t=><button key={t.id} onClick={()=>document.getElementById('chat-turn-'+t.id)?.scrollIntoView({block:'nearest',behavior:'smooth'})}><MessageCircle size={14}/><span>{t.query}</span></button>)}</div>}
   <button className="chat-dictionary" onClick={()=>navigate('dictionary')}><BookOpen size={16}/>ಗಾದೆ ನಿಘಂಟು (Dictionary)<ArrowRight size={15}/></button>
   <p className="chat-tagline">ಗಾದೆಗಳ ಸೊಗಡಿನಲ್ಲಿ<br/>ಅನುಭವದ ಅಮೃತ.</p>
  </aside>
  <div className="chat-main">
   <div className="chat-topline"><span><MessageCircle size={17}/>ಗಾದಾಮೃತ · ಸಂಭಾಷಣೆ</span><button onClick={reset} aria-label="New chat"><Plus size={17}/></button></div>
   <div className="chat-thread" ref={thread} role="log" aria-label="Conversation" aria-live="polite" aria-relevant="additions text">
    <div className="chat-message chat-assistant"><span className="chat-avatar"><MessageCircle size={20}/></span><div className="chat-welcome"><h2>ನಮಸ್ಕಾರ!</h2><p>ನಿಮ್ಮ ಸಂದರ್ಭವನ್ನು ವಿವರಿಸಿ, ಅದಕ್ಕೆ ತಕ್ಕ ಕನ್ನಡ ಗಾದೆಯನ್ನು ಹುಡುಕುತ್ತೇನೆ.</p><p lang="en">Describe a situation, and I’ll find a Kannada proverb that resonates with it.</p></div></div>
    {!turns.length&&<div className="chat-prompts">{recommendations.map(example=><button key={example.id} disabled={pending} onClick={()=>{setDraft(old=>({text:example.situation_kn,revision:old.revision+1}));composer.current?.querySelector('input')?.focus();}}><span lang="kn"><strong>{example.label_kn}</strong><span>{example.situation_kn}</span></span><ArrowRight size={15}/></button>)}</div>}
    {turns.map(turn=><div className="chat-turn" id={'chat-turn-'+turn.id} key={turn.id}>
     <div className="chat-message chat-user"><div className="chat-user-bubble">{turn.query}</div><span className="chat-avatar"><User size={19}/></span></div>
     <div className="chat-message chat-assistant"><span className="chat-avatar"><MessageCircle size={20}/></span><div className="chat-answer">
      {turn.error?<div className="chat-error"><p role="alert">{turn.error}</p>{turn.cloud&&<button className="secondary" disabled={pending} onClick={()=>send(turn.query,{cloud:false})}>ಸಾಮಾನ್ಯ ಹುಡುಕಾಟದಲ್ಲಿ ಪ್ರಯತ್ನಿಸಿ (Try local search)</button>}</div>:turn.result?<>
       {turn.result.fallback_notice&&<div className="chat-search-fallback"><p role="status">{turn.result.fallback_notice}</p><button className="secondary" disabled={pending} onClick={()=>send(turn.query,{cloud:true,provider:turn.provider,turnId:turn.id})}>ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ (Retry selected search)</button></div>}
       {turn.result.interpretation&&<p className="chat-interpretation">{turn.result.interpretation}</p>}
       {turn.result.items?.length?<div className="chat-results">{turn.result.items.map(row=><ProgressiveAnswer key={row.id} row={row} renderCard={renderCard}/>)}</div>:<p><strong>No reliable match yet.</strong> ಹೊಂದುವ ಗಾದೆ ಸಿಗಲಿಲ್ಲ. ಸಂದರ್ಭವನ್ನು ಸ್ವಲ್ಪ ವಿವರವಾಗಿ ಹೇಳಿ. (Try describing the situation in more detail.)</p>}
       {!!turn.result.external_sources?.length&&<div className="chat-sources"><h3>ಬಾಹ್ಯ ಉಲ್ಲೇಖಗಳು (Unverified web references)</h3>{turn.result.external_sources.map(s=><a key={s.url} href={s.url} target="_blank" rel="noreferrer">{s.title}<ArrowRight size={14}/></a>)}</div>}
       {turn.result.web_notice&&<p>{turn.result.web_notice}</p>}
      </>:<div className="chat-thinking" role="status"><i/><i/><i/><span>ಗಾದೆ ಹುಡುಕುತ್ತಿದ್ದೇನೆ…</span></div>}
     </div></div>
    </div>)}
   </div>
   <div className="chat-composer" ref={composer}><SearchBox key={epoch} initial={draft.text} initialRevision={draft.revision} onSearch={send} submitting={pending} clearOnSubmit/><p className="chat-composer-note">ಕನ್ನಡ ಅಥವಾ English · ನಿಮ್ಮ ಸಂದರ್ಭವನ್ನು ಬರೆಯಿರಿ ಅಥವಾ ಮೈಕ್ ಒತ್ತಿ.</p></div>
  </div>
 </section>;
}
