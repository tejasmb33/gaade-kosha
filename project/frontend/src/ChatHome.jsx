import React,{useEffect,useRef,useState} from 'react';
import {MessageCircle,Plus,ArrowRight,User,BookOpen} from 'lucide-react';
import api from './api';
import SearchBox from './SearchBox';
import './chat-home.css';

function pause(ms,signal){return new Promise(resolve=>{const done=()=>{clearTimeout(timer);signal.removeEventListener('abort',done);resolve();};const timer=setTimeout(done,ms);signal.addEventListener('abort',done,{once:true});if(signal.aborted)done();});}


export default function ChatHome({renderCard,navigate,errorText}){
 const [turns,setTurns]=useState([]),[pending,setPending]=useState(false),[draft,setDraft]=useState({text:'',revision:0}),[epoch,setEpoch]=useState(0);
 const request=useRef(null),thread=useRef(null),sequence=useRef(0),composer=useRef(null);
 useEffect(()=>()=>request.current?.abort(),[]);
 useEffect(()=>{if(thread.current)thread.current.scrollTop=thread.current.scrollHeight;},[turns,pending]);
 async function send(query,{cloud=false,provider=null}={}){
  if(!query.trim()||pending)return;
  const id=++sequence.current,controller=new AbortController();request.current=controller;const started=performance.now();
  setTurns(old=>[...old,{id,query,cloud,provider}]);setPending(true);
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
    {!turns.length&&<div className="chat-prompts">{['ತಾಳ್ಮೆ ಬೇಕಾದಾಗ','ಒಗ್ಗಟ್ಟಿನ ಬಲ','Hard work helped me overcome a difficult situation.'].map(q=><button key={q} disabled={pending} onClick={()=>{setDraft(old=>({text:q,revision:old.revision+1}));composer.current?.querySelector('input')?.focus();}}>{q}<ArrowRight size={15}/></button>)}</div>}
    {turns.map(turn=><div className="chat-turn" id={'chat-turn-'+turn.id} key={turn.id}>
     <div className="chat-message chat-user"><div className="chat-user-bubble">{turn.query}</div><span className="chat-avatar"><User size={19}/></span></div>
     <div className="chat-message chat-assistant"><span className="chat-avatar"><MessageCircle size={20}/></span><div className="chat-answer">
      {turn.error?<div className="chat-error"><p role="alert">{turn.error}</p>{turn.cloud&&<button className="secondary" disabled={pending} onClick={()=>send(turn.query,{cloud:false})}>ಸಾಮಾನ್ಯ ಹುಡುಕಾಟದಲ್ಲಿ ಪ್ರಯತ್ನಿಸಿ (Try local search)</button>}</div>:turn.result?<>
       {turn.result.interpretation&&<p className="chat-interpretation">{turn.result.interpretation}</p>}
       {turn.result.items?.length?<div className="chat-results">{turn.result.items.map(row=>renderCard(row))}</div>:<p><strong>No reliable match yet.</strong> ಹೊಂದುವ ಗಾದೆ ಸಿಗಲಿಲ್ಲ. ಸಂದರ್ಭವನ್ನು ಸ್ವಲ್ಪ ವಿವರವಾಗಿ ಹೇಳಿ. (Try describing the situation in more detail.)</p>}
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
