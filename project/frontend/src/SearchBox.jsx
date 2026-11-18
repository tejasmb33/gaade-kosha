import React,{useState,useEffect,useRef} from 'react';
import api from './api';
import {Search,ArrowRight,Mic,Square,X} from 'lucide-react';
import {useRecorder} from './useRecorder';
import {useBrowserSpeech} from './useBrowserSpeech';

export default function SearchBox({onSearch,initial='',initialCloud=null,initialProvider=null}) {
  const [text,setText]=useState(initial);
  const [selectedProvider,setSelectedProvider]=useState(initialProvider);
  const [hasGroq,setHasGroq]=useState(false);
  const [cloud,setCloud]=useState(initialCloud===true);
  const [hostedSpeech,setHostedSpeech]=useState(false);
  const pickedEngine=useRef(false);
  const language='en';
  const [voiceMethod,setVoiceMethod]=useState(()=>(window.SpeechRecognition||window.webkitSpeechRecognition)?'browser':'local');
  const [task,setTask]=useState('transcribe');
  const [clip,setClip]=useState(null);
  const [url,setUrl]=useState('');
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState('');
  const [message,setMessage]=useState('');
  const [sourceText,setSourceText]=useState('');
  const [warning,setWarning]=useState('');
  const request=useRef(null);
  const input=useRef(null);
  useEffect(()=>setText(initial),[initial]);
  useEffect(()=>{let active=true;api.get('/health').then(({data})=>{if(!active)return;setHostedSpeech(data.speech?.provider==='groq');const ai=data.cloud_ai;setHasGroq(Boolean(ai?.groq_configured));if(initialCloud===null&&!pickedEngine.current)setCloud(Boolean(ai?.configured));}).catch(()=>{});return()=>{active=false;};},[initialCloud]);
  useEffect(()=>()=>request.current?.abort(),[]);
  useEffect(()=>{
    if(!clip){setUrl('');return;}
    const objectUrl=URL.createObjectURL(clip);setUrl(objectUrl);
    return()=>URL.revokeObjectURL(objectUrl);
  },[clip]);
  const capture=useRecorder({
    onStart:()=>{setError('');setMessage('');setClip(null);setSourceText('');setWarning('');},
    onError:setError,
    onReady:(blob,duration)=>{setClip(blob);setMessage(`Recorded ${duration.toFixed(1)} seconds. Convert it to editable text below.`);}
  });
  const speech=useBrowserSpeech({language,onText:setText,onError:setError,onStart:()=>{setError('');setMessage('');setClip(null);setSourceText('');setWarning('');}});
  const recording=capture.phase!=='idle'||speech.listening;
  const browserVoice=voiceMethod==='browser';
  async function convert(){
    setBusy(true);setError('');setMessage('ಧ್ವನಿಯನ್ನು ಪಠ್ಯಕ್ಕೆ ಬದಲಾಯಿಸಲಾಗುತ್ತಿದೆ…');
    const controller=new AbortController();request.current=controller;
    try{
      const form=new FormData();form.append('file',clip,'situation');form.append('language',language);form.append('task',task);
      const {data}=await api.post('/search/voice',form,{signal:controller.signal});
      setText(data.text);setSourceText(data.task==='translate'?data.source_text||'':'');setWarning(data.warning||'');setMessage(data.task==='translate'?'English speech translation ready. Edit it if needed, then find proverbs.':'Transcript ready. Edit it if needed, then find proverbs.');
      input.current?.focus();
    }catch(e){
      if(controller.signal.aborted)return;
      setMessage('');setError(typeof e.response?.data?.detail==='string'?e.response.data.detail:'Voice input is unavailable. You can still type your situation in Kannada or English.');
    }finally{if(!controller.signal.aborted)setBusy(false);}
  }
  function changeSettings(setter,value){setter(value);setMessage('');setError('');}
  return <div className="situation-input">
    <form className="search-box" onSubmit={e=>{e.preventDefault();if(!busy&&!recording&&text.trim())onSearch(text.trim(),{cloud,provider:selectedProvider});}}>
      <Search size={23}/>
      <input ref={input} aria-label="Describe your situation" placeholder="ನಿಮ್ಮ ಸಂದರ್ಭವನ್ನು ಇಲ್ಲಿ ಬರೆಯಿರಿ… / Describe your situation" value={text} maxLength={1000} required disabled={busy||recording} onChange={e=>setText(e.target.value)}/>
      {text&&<button type="button" className="clear-search" aria-label="Clear situation" title="ತೆರವುಗೊಳಿಸಿ · Clear" disabled={busy||recording} onClick={()=>{setText('');setClip(null);setSourceText('');setWarning('');setError('');setMessage('');input.current?.focus();}}><X size={18}/></button>}
      <button type="button" className="voice-trigger" aria-label={recording?'Stop situation recording':'Record situation'} title={recording?'Stop recording':'Speak your situation'} disabled={busy||(!browserVoice&&recording&&capture.phase!=='recording')} onClick={browserVoice?(speech.listening?speech.stop:speech.start):(recording?capture.stop:capture.start)}>{recording?<Square size={18}/>:<Mic size={20}/>}</button>
      <button type="submit" aria-label="Find proverbs" disabled={busy||recording}><ArrowRight/></button>
    </form>
    <div className="voice-options">
      <label><span lang="kn">ಧ್ವನಿ ವಿಧಾನ</span> <select aria-label="Voice input method" value={voiceMethod} disabled={busy||recording} onChange={e=>changeSettings(setVoiceMethod,e.target.value)}><option value="browser" disabled={!speech.supported}>ನೇರವಾಗಿ ಮಾತನಾಡಿ</option><option value="local">ಧ್ವನಿ ದಾಖಲಿಸಿ</option></select></label>
      {!browserVoice&&<label><span lang="kn">ಧ್ವನಿಯ ಫಲಿತಾಂಶ</span> <select aria-label="Voice output" value={task} disabled={busy||recording} onChange={e=>changeSettings(setTask,e.target.value)}><option value="transcribe">ಮೂಲ ಭಾಷೆಯಲ್ಲೇ ಉಳಿಸಿ</option><option value="translate">ಇಂಗ್ಲಿಷ್ ಅನುವಾದ · ಪ್ರಾಯೋಗಿಕ</option></select></label>}
    <label><span lang="kn">ಹುಡುಕಾಟದ ವಿಧಾನ</span> <select aria-label="Search engine" value={cloud?(selectedProvider==='groq'?'groq':'cloud'):'local'} disabled={busy||recording} onChange={e=>{pickedEngine.current=true;setCloud(e.target.value!=='local');setSelectedProvider(e.target.value==='groq'?'groq':null);}}><option value="local">ಸಾಮಾನ್ಯ ಹುಡುಕಾಟ</option><option value="cloud">ಸಂದರ್ಭಕ್ಕೆ ತಕ್ಕ ಹುಡುಕಾಟ</option>{(hasGroq||selectedProvider==='groq')&&<option value="groq">ಪರ್ಯಾಯ ಹುಡುಕಾಟ</option>}</select></label>
    </div>

    
    {speech.listening&&<div className="voice-capture" role="status" lang="kn">ಮಾತನಾಡಿ… ಮುಗಿದ ನಂತರ ಮೈಕ್ ಒತ್ತಿ.</div>}
    {!browserVoice&&recording&&<div className="voice-capture" role="status">{capture.phase==='requesting'?'Allow microphone access in your browser…':capture.phase==='finishing'?'Finishing recording…':<><strong>Recording · {capture.seconds}s / 89s</strong><meter min="0" max="100" value={capture.level} aria-label="Situation microphone input level"/><span>{capture.level>2?'Microphone input detected.':'Speak now; check your microphone if the meter stays empty.'}</span></>}</div>}
    {url&&<div className="voice-preview"><audio controls preload="auto" src={url} aria-label="Situation recording playback" onLoadedMetadata={e=>{const audio=e.currentTarget;if(audio.duration===Infinity){audio.currentTime=1e10;audio.ontimeupdate=()=>{audio.ontimeupdate=null;audio.currentTime=0;};}}}/><div className="actions"><button type="button" className="secondary" disabled={busy||recording} onClick={convert}>{busy?'ಪಠ್ಯಕ್ಕೆ ಬದಲಾಯಿಸಲಾಗುತ್ತಿದೆ…':task==='translate'?'Translate speech to English':'Use voice as text'}</button><button type="button" className="text-button" disabled={busy||recording} onClick={()=>{setClip(null);setMessage('');setError('');setSourceText('');setWarning('');}}><X size={14}/> Discard recording</button></div></div>}
    {sourceText&&<div className="source-transcript"><label>ಮೂಲ ಧ್ವನಿ ಪಠ್ಯ ({language==='kn'?'Kannada':'English'})<textarea aria-label="Original speech transcript" lang={language} maxLength={1000} value={sourceText} disabled={busy||recording} onChange={e=>setSourceText(e.target.value)}/></label><button type="button" className="secondary" disabled={busy||recording} onClick={()=>{setText(sourceText);setMessage('Original transcript copied to search. Edits here are not translated; search this Kannada text directly.');input.current?.focus();}}>Use original transcript for search</button></div>}
    {warning&&<p role="status" className="notice">{warning}</p>}
    {error&&<p role="alert" className="notice error">{error}</p>}
    {browserVoice&&error&&!recording&&<button type="button" className="secondary" aria-label="Retry with local voice input" onClick={()=>{setVoiceMethod('local');setTask('transcribe');capture.start();}}>{hostedSpeech?'ಧ್ವನಿ ಪಠ್ಯದಿಂದ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ':'ಸ್ಥಳೀಯ ಧ್ವನಿಯಿಂದ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ'}</button>}
    {message&&<p role="status" className="voice-message">{message}</p>}
  </div>;
}
