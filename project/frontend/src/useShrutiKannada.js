import {useEffect,useRef} from 'react';

// A dedicated worker; audio never enters the backend or an external speech API.
export function useShrutiKannada(){
 const worker=useRef(null),ready=useRef(false),pending=useRef(null);
 function reset(error=new DOMException('Cancelled','AbortError')){
  worker.current?.terminate();worker.current=null;ready.current=false;
  const job=pending.current;pending.current=null;job?.finish(error);
 }
 useEffect(()=>()=>reset(),[]);
 function request(message,{signal,onProgress}={}){
  if(signal?.aborted)return Promise.reject(new DOMException('Cancelled','AbortError'));
  return new Promise((resolve,reject)=>{
   const abort=()=>reset(),timer=setTimeout(()=>reset(Error('ಕನ್ನಡ ಧ್ವನಿಪಠ್ಯಕ್ಕೆ ಹೆಚ್ಚು ಸಮಯ ಬೇಕಾಗಿದೆ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.')),message.type==='init'?180000:120000);
   const finish=(error,result)=>{clearTimeout(timer);signal?.removeEventListener('abort',abort);error?reject(error):resolve(result);};
   pending.current={finish,onProgress};signal?.addEventListener('abort',abort,{once:true});
   try{worker.current.postMessage(message,message.pcm?[message.pcm.buffer]:[]);}catch(error){reset(error);}
  });
 }
 async function prepare(options){
  if(ready.current)return;
  if(typeof Worker==='undefined'||typeof WebAssembly!=='object'||!window.isSecureContext)throw Error('ಕನ್ನಡ ಧ್ವನಿಗೆ HTTPS ಅಥವಾ localhost ಹಾಗೂ ಹೊಸ ಬ್ರೌಸರ್ ಬೇಕು.');
  const instance=new Worker('/speech/shruti-kn/worker.js');worker.current=instance;
  instance.onerror=()=>{if(worker.current===instance)reset(Error('ಕನ್ನಡ ಧ್ವನಿ ಸಿದ್ಧವಾಗಲಿಲ್ಲ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.'));};
  instance.onmessage=({data})=>{
   if(worker.current!==instance)return;
   if(data.type==='progress'){pending.current?.onProgress?.(data.loaded,data.total);return;}
   if(data.type==='error'){reset(Error('ಕನ್ನಡ ಧ್ವನಿಪಠ್ಯ ಸಿದ್ಧವಾಗಲಿಲ್ಲ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ ಅಥವಾ ಬೇರೆ ಧ್ವನಿ ವಿಧಾನ ಬಳಸಿ.'));return;}
   if(data.type==='ready')ready.current=true;
   const job=pending.current;pending.current=null;job?.finish(null,data.text);
  };
  await request({type:'init'},options);
 }
 async function transcribe(blob,{signal,onProgress}={}){
  await prepare({signal,onProgress});
  if(signal?.aborted)throw new DOMException('Cancelled','AbortError');
  const Context=window.OfflineAudioContext||window.webkitOfflineAudioContext;
  if(!Context)throw Error('ಈ ಬ್ರೌಸರ್ ಕನ್ನಡ ಧ್ವನಿ ಸಂಸ್ಕರಣೆಯನ್ನು ಬೆಂಬಲಿಸುವುದಿಲ್ಲ.');
  const decoded=await new Context(1,1,16000).decodeAudioData(await blob.arrayBuffer());
  if(!decoded.length||decoded.duration>90)throw Error('90 ಸೆಕೆಂಡ್ ಒಳಗಿನ ಧ್ವನಿ ದಾಖಲಿಸಿ.');
  const pcm=new Float32Array(decoded.length);
  for(let c=0;c<decoded.numberOfChannels;c++){const channel=decoded.getChannelData(c);for(let i=0;i<pcm.length;i++)pcm[i]+=channel[i]/decoded.numberOfChannels;}
  if(signal?.aborted)throw new DOMException('Cancelled','AbortError');
  const text=await request({type:'transcribe',pcm},{signal});
  if(!text)throw Error('ಧ್ವನಿ ಗುರುತಿಸಲಾಗಲಿಲ್ಲ. ಸ್ಪಷ್ಟವಾಗಿ ಮತ್ತೆ ಮಾತನಾಡಿ.');
  if(text.length>1000)throw Error('ಪಠ್ಯವು ಹೆಚ್ಚು ಉದ್ದವಾಗಿದೆ. ಚಿಕ್ಕ ಸಂದರ್ಭವನ್ನು ದಾಖಲಿಸಿ.');
  return text;
 }
 return {transcribe};
}
