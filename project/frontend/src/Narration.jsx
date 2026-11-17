import React,{useEffect,useRef,useState} from 'react';
import api from './api';
import {Volume2,Square,Pause,Play} from 'lucide-react';
export default function Narration({row}){
 const [url,setUrl]=useState(''),[busy,setBusy]=useState(false),[playing,setPlaying]=useState(false),[error,setError]=useState('');
 const audio=useRef(null),lastAudio=useRef(null),autostart=useRef(false),request=useRef(null),alive=useRef(true);
 useEffect(()=>{alive.current=true;const stopOthers=e=>{if(e.detail!==row.id){request.current?.abort();setBusy(false);autostart.current=false;if(audio.current){audio.current.pause();audio.current.currentTime=0;}}};window.addEventListener('gaade:narration',stopOthers);return()=>{alive.current=false;request.current?.abort();lastAudio.current?.pause();window.removeEventListener('gaade:narration',stopOthers);};},[row.id]);
 useEffect(()=>()=>{if(url)URL.revokeObjectURL(url);},[url]);
 async function listen(){
  setError('');window.dispatchEvent(new CustomEvent('gaade:narration',{detail:row.id}));
  if(url){try{await audio.current.play();}catch{setPlaying(false);}return;}
  setBusy(true);const controller=new AbortController();request.current=controller;
  try{const {data}=await api.post('/proverbs/'+encodeURIComponent(row.id)+'/narration',null,{responseType:'blob',signal:controller.signal});if(!alive.current)return;autostart.current=true;setUrl(URL.createObjectURL(data));}
  catch(e){if(controller.signal.aborted)return;let detail='ಧ್ವನಿ ಈಗ ಲಭ್ಯವಿಲ್ಲ. ವಿವರಣೆಯನ್ನು ಓದಿ ಅಥವಾ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.';try{const body=JSON.parse(await e.response.data.text());detail=body.detail||detail;if(/Gemini|API key/i.test(detail))detail='ಧ್ವನಿ ಈಗ ಲಭ್ಯವಿಲ್ಲ. ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.';}catch{}if(alive.current)setError(detail);}
  finally{if(alive.current&&!controller.signal.aborted)setBusy(false);}
 }
 function stop(){autostart.current=false;audio.current?.pause();if(audio.current)audio.current.currentTime=0;setPlaying(false);}
 return <div className="narration-player"><div className="actions"><button className="secondary" type="button" disabled={busy} onClick={playing?()=>audio.current.pause():listen} aria-label={playing?'Pause Kannada explanation':'Listen to Kannada explanation'}>{playing?<Pause size={17}/>:<Volume2 size={17}/>} {busy?'ಧ್ವನಿ ಸಿದ್ಧವಾಗುತ್ತಿದೆ…':playing?'ವಿರಾಮ':'ವಿವರಣೆ ಕೇಳಿ'}</button>{url&&<button className="text-button" type="button" onClick={stop} aria-label="Stop Kannada explanation"><Square size={15}/> ನಿಲ್ಲಿಸಿ</button>}{busy&&<button className="text-button" onClick={()=>{request.current?.abort();setBusy(false);}}>ರದ್ದುಮಾಡಿ</button>}</div>{url&&<audio ref={element=>{audio.current=element;if(element)lastAudio.current=element;}} src={url} controls preload="auto" aria-label="Kannada proverb explanation" onCanPlay={()=>{if(autostart.current){autostart.current=false;audio.current?.play().catch(()=>setPlaying(false));}}} onPlay={()=>{setPlaying(true);window.dispatchEvent(new CustomEvent('gaade:narration',{detail:row.id}));}} onPause={()=>setPlaying(false)} onEnded={()=>setPlaying(false)} onError={()=>setError('ಧ್ವನಿಯನ್ನು ಪ್ಲೇ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.')}/>}{error&&<p role="alert">{error}</p>}</div>;
}
