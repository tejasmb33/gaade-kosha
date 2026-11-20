import React,{useState,useEffect,useRef} from 'react';
import api from './api';
import {Search,ArrowRight,Mic,Square,X} from 'lucide-react';
import {useRecorder} from './useRecorder';
import {useBrowserSpeech} from './useBrowserSpeech';
import {useShrutiKannada} from './useShrutiKannada';

export default function SearchBox({onSearch,initial='',initialCloud=null,initialProvider=null,submitting=false,clearOnSubmit=false,initialRevision=0}) {
  const [text,setText]=useState(initial);
  const [selectedProvider,setSelectedProvider]=useState(initialProvider);
  const [hasGroq,setHasGroq]=useState(false);
  const [cloud,setCloud]=useState(initialCloud===true);
  const [hostedSpeech,setHostedSpeech]=useState(false);
  const pickedEngine=useRef(false);
  const [voiceMethod,setVoiceMethod]=useState('kannada');
  const kannadaVoice=voiceMethod==='kannada';
  const language=kannadaVoice?'kn':'en';
  const shruti=useShrutiKannada();
  const [task,setTask]=useState('transcribe');
  const [clip,setClip]=useState(null);
  const [url,setUrl]=useState('');
  const [processing,setBusy]=useState(false);
  const busy=processing||submitting;
  const [error,setError]=useState('');
  const [message,setMessage]=useState('');
  const [sourceText,setSourceText]=useState('');
  const [warning,setWarning]=useState('');
  const request=useRef(null);
  const input=useRef(null);
  useEffect(()=>setText(initial),[initial,initialRevision]);
  useEffect(()=>{let active=true;api.get('/health').then(({data})=>{if(!active)return;const hosted=data.speech?.provider==='groq'&&Boolean(data.speech?.configured);setHostedSpeech(hosted);const ai=data.cloud_ai;setHasGroq(Boolean(ai?.groq_configured));if(initialCloud===null&&!pickedEngine.current)setCloud(Boolean(ai?.configured));}).catch(()=>{});return()=>{active=false;};},[initialCloud]);
  useEffect(()=>()=>request.current?.abort(),[]);
  useEffect(()=>{
    if(!clip){setUrl('');return;}
    const objectUrl=URL.createObjectURL(clip);setUrl(objectUrl);
    return()=>URL.revokeObjectURL(objectUrl);
  },[clip]);
  const capture=useRecorder({
    onStart:()=>{setError('');setMessage('');setClip(null);setSourceText('');setWarning('');},
    onError:setError,
    onReady:(blob,duration)=>{setClip(blob);if(hostedSpeech||kannadaVoice)convert(blob);else setMessage(`Recorded ${duration.toFixed(1)} seconds. Convert it to editable text below.`);}
  });
  const speech=useBrowserSpeech({language,onText:setText,onError:setError,onUnavailable:()=>{setVoiceMethod('local');setTask('transcribe');setError('');setMessage('ಧ್ವನಿ ದಾಖಲಿಸುವ ವಿಧಾನಕ್ಕೆ ಬದಲಾಯಿಸಲಾಗಿದೆ. ಮೈಕ್ ಒತ್ತಿ ಮತ್ತೆ ಮಾತನಾಡಿ. (Press the microphone and speak again.)');},onStart:()=>{setError('');setMessage('');setClip(null);setSourceText('');setWarning('');}});
  const recording=capture.phase!=='idle'||speech.listening;
  const browserVoice=voiceMethod==='browser';
  async function convert(audioBlob=clip){
    if(!audioBlob)return;
    setBusy(true);setError('');setMessage('ಧ್ವನಿಯನ್ನು ಪಠ್ಯಕ್ಕೆ ಬದಲಾಯಿಸಲಾಗುತ್ತಿದೆ…');
    const controller=new AbortController();request.current=controller;
    try{
      if(kannadaVoice){
        const transcript=await shruti.transcribe(audioBlob,{signal:controller.signal,onProgress:(loaded,total)=>{if(!controller.signal.aborted)setMessage('ಕನ್ನಡ ಧ್ವನಿ ಸಿದ್ಧವಾಗುತ್ತಿದೆ… '+Math.round(loaded/total*100)+'%');}});
        if(controller.signal.aborted)return;
        setText(transcript);setSourceText('');setWarning('');setMessage('ಕನ್ನಡ ಪಠ್ಯ ಸಿದ್ಧವಾಗಿದೆ. ಪರಿಶೀಲಿಸಿ, ಬೇಕಿದ್ದರೆ ತಿದ್ದಿ ಹುಡುಕಿ.');input.current?.focus();return;
      }
      const form=new FormData();form.append('file',audioBlob,'situation');form.append('language',language);form.append('task',task);
      const {data}=await api.post('/search/voice',form,{signal:controller.signal});
      if(controller.signal.aborted)return;
      setText(data.text);setSourceText(data.task==='translate'?data.source_text||'':'');setWarning(data.warning||'');setMessage(data.task==='translate'?'English speech translation ready. Edit it if needed, then find proverbs.':'Transcript ready. Edit it if needed, then find proverbs.');
      input.current?.focus();
    }catch(e){
      if(controller.signal.aborted)return;
      setMessage('');setError(kannadaVoice?(e.message||'ಕನ್ನಡ ಧ್ವನಿಪಠ್ಯ ಸಿದ್ಧವಾಗಲಿಲ್ಲ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.'):typeof e.response?.data?.detail==='string'?e.response.data.detail:'Voice input is unavailable. You can still type your situation in Kannada or English.');
    }finally{if(!controller.signal.aborted)setBusy(false);}
  }
  function changeSettings(setter,value){setter(value);setMessage('');setError('');}
  function toggleVoice(){if(browserVoice){speech.listening?speech.stop():speech.start();}else{recording?capture.stop():capture.start();}}
  return <div className="situation-input">
    <form className="search-box" onSubmit={e=>{e.preventDefault();if(!busy&&!recording&&text.trim()){onSearch(text.trim(),{cloud,provider:selectedProvider});if(clearOnSubmit){setText('');setClip(null);setSourceText('');setMessage('');}}}}>
      <Search size={23}/>
      <input ref={input} aria-label="Describe your situation" placeholder="ನಿಮ್ಮ ಸಂದರ್ಭವನ್ನು ಇಲ್ಲಿ ಬರೆಯಿರಿ… / Describe your situation" value={text} maxLength={1000} required disabled={busy||recording} onChange={e=>setText(e.target.value)}/>
      {text&&<button type="button" className="clear-search" aria-label="Clear situation" title="ತೆರವುಗೊಳಿಸಿ · Clear" disabled={busy||recording} onClick={()=>{setText('');setClip(null);setSourceText('');setWarning('');setError('');setMessage('');input.current?.focus();}}><X size={18}/></button>}
      <button type="button" className="voice-trigger" aria-label={recording?'Stop situation recording':'Record situation'} title={recording?'Stop recording':'Speak your situation'} disabled={busy||(!browserVoice&&recording&&capture.phase!=='recording')} onClick={toggleVoice}>{recording?<Square size={18}/>:<Mic size={20}/>}</button>
      <button type="submit" aria-label="Find proverbs" disabled={busy||recording}><ArrowRight/></button>
    </form>
    <div className="voice-options">
      <label><span lang="kn">ಧ್ವನಿ ವಿಧಾನ (Voice input)</span> <select aria-label="Voice input method" value={voiceMethod} disabled={busy||recording} onChange={e=>{changeSettings(setVoiceMethod,e.target.value);setTask('transcribe');setClip(null);setSourceText('');setWarning('');}}><option value="kannada">ಕನ್ನಡ (Kannada)</option><option value="local">English (Record audio)</option><option value="browser" disabled={!speech.supported}>English (Browser)</option></select></label>
      {!browserVoice&&!kannadaVoice&&<label><span lang="kn">ಧ್ವನಿಯ ಫಲಿತಾಂಶ (Voice output)</span> <select aria-label="Voice output" value={task} disabled={busy||recording} onChange={e=>changeSettings(setTask,e.target.value)}><option value="transcribe">ಮೂಲ ಭಾಷೆಯಲ್ಲೇ ಉಳಿಸಿ (Original language)</option><option value="translate">ಇಂಗ್ಲಿಷ್ ಅನುವಾದ (Translate to English)</option></select></label>}
    <label><span lang="kn">ಹುಡುಕಾಟದ ವಿಧಾನ (Search method)</span> <select aria-label="Search engine" value={cloud?(selectedProvider==='groq'?'groq':'cloud'):'local'} disabled={busy||recording} onChange={e=>{pickedEngine.current=true;setCloud(e.target.value!=='local');setSelectedProvider(e.target.value==='groq'?'groq':null);}}><option value="local">ಸಾಮಾನ್ಯ ಹುಡುಕಾಟ (Standard)</option><option value="cloud">ಜೆಮಿನಿ (Gemini)</option>{(hasGroq||selectedProvider==='groq')&&<option value="groq">ಗ್ರೋಕ್ (Groq)</option>}</select></label>
    </div>
    {kannadaVoice&&<p className="voice-message" lang="kn">ಕನ್ನಡದಲ್ಲಿ ಮಾತನಾಡಿ, ಮುಗಿದ ನಂತರ ಮೈಕ್ ಒತ್ತಿ. ಮೊದಲ ಬಳಕೆಗೆ ಸುಮಾರು 30 MB ಲೋಡ್ ಆಗುತ್ತದೆ; ಧ್ವನಿ ನಿಮ್ಮ ಸಾಧನದಲ್ಲೇ ಪಠ್ಯವಾಗುತ್ತದೆ.</p>}
    {processing&&<button type="button" className="text-button" onClick={()=>{request.current?.abort();setBusy(false);setMessage('ಧ್ವನಿ ಸಂಸ್ಕರಣೆ ರದ್ದುಮಾಡಲಾಗಿದೆ.');}} aria-label="Cancel voice transcription">ರದ್ದುಮಾಡಿ (Cancel)</button>}


    {speech.listening&&<div className="voice-capture" role="status" lang="kn">ಮಾತನಾಡಿ… ಮುಗಿದ ನಂತರ ಮೈಕ್ ಒತ್ತಿ.</div>}
    {!browserVoice&&recording&&<div className="voice-capture" role="status">{capture.phase==='requesting'?'Allow microphone access in your browser…':capture.phase==='finishing'?'Finishing recording…':<><strong>Recording · {capture.seconds}s / 89s</strong><meter min="0" max="100" value={capture.level} aria-label="Situation microphone input level"/><span>{capture.level>2?'Microphone input detected.':'Speak now; check your microphone if the meter stays empty.'}</span></>}</div>}
    {url&&<div className="voice-preview"><audio controls preload="auto" src={url} aria-label="Situation recording playback" onLoadedMetadata={e=>{const audio=e.currentTarget;if(audio.duration===Infinity){audio.currentTime=1e10;audio.ontimeupdate=()=>{audio.ontimeupdate=null;audio.currentTime=0;};}}}/><div className="actions"><button type="button" className="secondary" disabled={busy||recording} onClick={()=>convert()}>{busy?'ಪಠ್ಯಕ್ಕೆ ಬದಲಾಯಿಸಲಾಗುತ್ತಿದೆ…':task==='translate'?'Translate speech to English':'Use voice as text'}</button><button type="button" className="text-button" disabled={busy||recording} onClick={()=>{setClip(null);setMessage('');setError('');setSourceText('');setWarning('');}}><X size={14}/> Discard recording</button></div></div>}
    {sourceText&&<div className="source-transcript"><label>ಮೂಲ ಧ್ವನಿ ಪಠ್ಯ ({language==='kn'?'Kannada':'English'})<textarea aria-label="Original speech transcript" lang={language} maxLength={1000} value={sourceText} disabled={busy||recording} onChange={e=>setSourceText(e.target.value)}/></label><button type="button" className="secondary" disabled={busy||recording} onClick={()=>{setText(sourceText);setMessage('Original transcript copied to search. Edits here are not translated; search this Kannada text directly.');input.current?.focus();}}>Use original transcript for search</button></div>}
    {warning&&<p role="status" className="notice">{warning}</p>}
    {error&&<p role="alert" className="notice error">{error}</p>}
    {browserVoice&&error&&!recording&&<button type="button" className="secondary" aria-label="Retry with local voice input" onClick={()=>{setVoiceMethod('local');setTask('transcribe');capture.start();}}>{hostedSpeech?'ಧ್ವನಿ ಪಠ್ಯದಿಂದ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ':'ಸ್ಥಳೀಯ ಧ್ವನಿಯಿಂದ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ'}</button>}
    {message&&<p role="status" className="voice-message">{message}</p>}
  </div>;
}
