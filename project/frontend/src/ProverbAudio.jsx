import React,{useEffect,useId,useRef,useState} from 'react';
import {Volume2,Pause} from 'lucide-react';
import api from './api';
export default function ProverbAudio({row}){
 const audio=useRef(null),token=useId(),[active,setActive]=useState(false),[playing,setPlaying]=useState(false),[error,setError]=useState('');
 useEffect(()=>{const element=audio.current;const stopOther=e=>{if(e.detail!==token)element?.pause();};window.addEventListener('gaade:narration',stopOther);return()=>{element?.pause();window.removeEventListener('gaade:narration',stopOther);};},[row.id,token,Boolean(row.reading_audio)]);
 if(!row.reading_audio)return null;
 const src=(api.defaults.baseURL||'/api')+'/proverbs/'+encodeURIComponent(row.id)+'/audio';
 async function toggle(){setError('');setActive(true);if(playing){audio.current?.pause();return;}try{await audio.current?.play();}catch{setError('ಧ್ವನಿ ಪ್ಲೇ ಆಗಲಿಲ್ಲ. ಕೆಳಗಿನ Play ಗುಂಡಿ ಒತ್ತಿ ಅಥವಾ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.');}}
 return <div className="proverb-audio"><button type="button" className="secondary" onClick={toggle} aria-label={playing?'Pause proverb audio':'Play proverb audio'}>{playing?<Pause size={17}/>:<Volume2 size={17}/>} {playing?'ವಿರಾಮ':'ಗಾದೆ ಕೇಳಿ'}</button><audio ref={audio} src={src} controls hidden={!active} preload="none" aria-label="Proverb audio recording" onPlay={()=>{setPlaying(true);window.dispatchEvent(new CustomEvent('gaade:narration',{detail:token}));}} onPause={()=>setPlaying(false)} onEnded={()=>setPlaying(false)} onError={()=>{setPlaying(false);setError('ಈ ಗಾದೆಯ ಧ್ವನಿ ಲಭ್ಯವಾಗಲಿಲ್ಲ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.');}}/>{error&&<p role="alert">{error}</p>}</div>;
}
