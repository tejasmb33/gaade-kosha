import {useEffect,useRef,useState} from 'react';

export function useBrowserSpeech({language,onText,onError,onStart}) {
  const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
  const [listening,setListening]=useState(false);
  const active=useRef(null),timer=useRef(null);
  useEffect(()=>()=>{
    clearTimeout(timer.current);
    const recognition=active.current;active.current=null;
    if(recognition){recognition.onresult=null;recognition.onerror=null;recognition.onend=null;recognition.abort();}
  },[]);
  function stop(){active.current?.stop();}
  function start(){
    if(!Recognition||active.current)return;
    const recognition=new Recognition();
    recognition.lang=language==='kn'?'kn-IN':'en-IN';
    recognition.continuous=true;recognition.interimResults=true;
    active.current=recognition;
    let received=false,failed=false;
    recognition.onresult=event=>{
      if(active.current!==recognition)return;
      const text=Array.from(event.results,result=>result[0].transcript).join(' ').trim().slice(0,1000);
      if(text){received=true;onText(text);}
    };
    recognition.onerror=event=>{
      if(active.current!==recognition)return;
      failed=true;
      clearTimeout(timer.current);active.current=null;setListening(false);
      recognition.onresult=null;recognition.onerror=null;recognition.onend=null;
      try{recognition.abort();}catch{}
      const messages={
        'not-allowed':'ಮೈಕ್ರೊಫೋನ್ ಅನುಮತಿ ನೀಡಿ, ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.',
        'audio-capture':'ಮೈಕ್ರೊಫೋನ್ ಲಭ್ಯವಿಲ್ಲ. ಸಾಧನವನ್ನು ಪರಿಶೀಲಿಸಿ.',
        'no-speech':'ಧ್ವನಿ ಕೇಳಿಸಲಿಲ್ಲ. ಮತ್ತೆ ಮಾತನಾಡಿ.',
        'network':'ಧ್ವನಿ ಸಂಪರ್ಕ ವಿಫಲವಾಗಿದೆ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ ಅಥವಾ ಸ್ಥಳೀಯ ಧ್ವನಿ ವಿಧಾನ ಬಳಸಿ.',
        'language-not-supported':'ಈ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಆಯ್ದ ಭಾಷೆ ಲಭ್ಯವಿಲ್ಲ. ಸ್ಥಳೀಯ ಧ್ವನಿ ವಿಧಾನ ಬಳಸಿ.'
      };
      if(event.error!=='aborted')onError(messages[event.error]||'ಧ್ವನಿಯನ್ನು ಪಠ್ಯಕ್ಕೆ ಬದಲಾಯಿಸಲಾಗಲಿಲ್ಲ. ಸ್ಥಳೀಯ ಧ್ವನಿ ವಿಧಾನ ಬಳಸಿ.');
    };
    recognition.onend=()=>{
      if(active.current!==recognition)return;
      clearTimeout(timer.current);active.current=null;setListening(false);
      if(!received&&!failed)onError('ಧ್ವನಿ ಕೇಳಿಸಲಿಲ್ಲ. ಮತ್ತೆ ಮಾತನಾಡಿ.');
    };
    onStart();setListening(true);
    try{recognition.start();timer.current=setTimeout(stop,89000);}
    catch{clearTimeout(timer.current);active.current=null;recognition.onresult=null;recognition.onerror=null;recognition.onend=null;try{recognition.abort();}catch{}setListening(false);onError('ಧ್ವನಿ ಪ್ರಾರಂಭವಾಗಲಿಲ್ಲ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ ಅಥವಾ ಸ್ಥಳೀಯ ಧ್ವನಿ ವಿಧಾನ ಬಳಸಿ.');}
  }
  return {supported:Boolean(Recognition),listening,start,stop};
}
