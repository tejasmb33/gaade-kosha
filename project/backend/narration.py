"""Verbatim Kannada narration of approved metadata, generated only on explicit request."""
import base64,hashlib,io,os,re,wave
from pathlib import Path
import httpx
from fastapi import HTTPException
from .dictionary_translations import load_translation
from .object_store import ObjectStore

def clean(value):return re.sub(r'^(Draft(?: for human verification)?|ಮಾನವ ಪರಿಶೀಲನೆಗಾಗಿ (?:ಕರಡು|ಡ್ರಾಫ್ಟ್)|ಕರಡು|ಡ್ರಾಫ್ಟ್)\s*:\s*','',value or '',flags=re.IGNORECASE).strip()
def script_for(data,row):
    translation=load_translation(data,row);fields=(translation or {}).get('fields',{})
    def kannada(key):
        value=clean(fields.get(key+'_kn') or getattr(row,key,''))
        return value if re.search('[\u0c80-\u0cff]',value) else ''
    meaning=kannada('contextual_meaning')
    if not meaning:raise HTTPException(409,'ಈ ಗಾದೆಗೆ ಕನ್ನಡ ವಿವರಣೆ ಇನ್ನೂ ಲಭ್ಯವಿಲ್ಲ. ಪೂರ್ಣ ವಿವರವನ್ನು ಓದಬಹುದು.')
    parts=['ಗಾದೆ: '+row.proverb_kn]
    if translation:parts.append('ಗಮನಿಸಿ. ಈ ವಿವರಣೆಯಲ್ಲಿ ಪರಿಶೀಲನೆಗೆ ಒಳಪಡಬೇಕಾದ ಅನುವಾದ ಕರಡು ಇದೆ.')
    for label,key in [('ಪದಶಃ ಅರ್ಥ','literal_meaning'),('ಭಾವಾರ್ಥ ಮತ್ತು ಸೂಕ್ತ ಸಂದರ್ಭ','contextual_meaning'),('ಬಳಕೆಯ ಉದಾಹರಣೆ','example_usage'),('ವರ್ಗ','category'),('ದಾಖಲಿತ ಪ್ರದೇಶ','region'),('ದಾಖಲಿತ ಉಪಭಾಷೆ','dialect')]:
        value=kannada(key)
        if value:parts.append(label+': '+value)
    parts.append('ಮೂಲದ ಉಲ್ಲೇಖ ಮತ್ತು ಹೆಚ್ಚಿನ ವಿವರಗಳಿಗೆ ಗಾದೆಯ ಪೂರ್ಣ ದಾಖಲೆಯನ್ನು ನೋಡಿ.')
    script='\n'.join(parts)
    if len(script)>6500:raise HTTPException(422,'ವಿವರಣೆ ಧ್ವನಿಗೆ ತುಂಬಾ ಉದ್ದವಾಗಿದೆ. ದಾಖಲೆಯ ವಿವರಗಳನ್ನು ಓದಿ.')
    return script

def valid_wav(content):
    if len(content)>25*1024*1024:raise ValueError('Audio too large')
    with wave.open(io.BytesIO(content),'rb') as audio:
        duration=audio.getnframes()/audio.getframerate()
        if not 0.2<duration<=300 or audio.getnchannels() not in [1,2]:raise ValueError('Invalid audio duration')

def generate(data,row):
    if os.getenv('GAADE_TTS_ENABLED','false').lower()!='true':raise HTTPException(503,'ಕನ್ನಡ ಧ್ವನಿ ಸೇವೆ ಸಕ್ರಿಯವಾಗಿಲ್ಲ. ವಿವರಣೆಯನ್ನು ಓದಬಹುದು.')
    model=os.getenv('GAADE_TTS_MODEL','gemini-3.8-flash-lite-tts')
    if model not in ['gemini-3.8-flash-lite-tts','gemini-3.8-flash-tts']:raise HTTPException(503,'ಕನ್ನಡ ಧ್ವನಿ ಮಾದರಿಯ ಸಂರಚನೆಯನ್ನು ಪರಿಶೀಲಿಸಿ.')
    text=script_for(data,row);key=hashlib.sha256((model+'Kore'+text).encode()).hexdigest()
    folder=Path(data)/'narrations';folder.mkdir(exist_ok=True,mode=0o700);dest=folder/(key+'.wav')
    objects=ObjectStore()
    objects.restore('narrations/'+dest.name,dest)
    if dest.exists():
        try:valid_wav(dest.read_bytes());return dest
        except (ValueError,wave.Error,EOFError):dest.unlink()
    api_key=os.getenv('GEMINI_API_KEY','')
    if not api_key:raise HTTPException(503,'ಕನ್ನಡ ಧ್ವನಿಗಾಗಿ Gemini API key ಸಂರಚಿಸಬೇಕು.')
    body={'model':model,'input':[{'type':'user_input','content':[{'type':'text','text':text,'annotations':[{'type':'speech_metadata','style':'Read this Kannada explanation clearly and naturally in Kannada at a calm, measured pace. Read the supplied words verbatim.'}]}]}],'response_format':{'type':'audio'},'generation_config':{'speech_config':[{'voice':'Kore'}]}}
    try:
        with httpx.Client(timeout=httpx.Timeout(90,connect=10),follow_redirects=False) as client:
            response=client.post('https://generativelanguage.googleapis.com/v1beta/interactions',headers={'x-goog-api-key':api_key},json=body)
            response.raise_for_status();result=response.json()
        blocks=[c for step in result.get('steps',[]) if step.get('type')=='model_output' for c in step.get('content',[]) if c.get('type')=='audio']
        if not blocks or not isinstance(blocks[-1].get('data'),str):raise ValueError('Audio missing')
        content=base64.b64decode(blocks[-1]['data'],validate=True);valid_wav(content)
        temporary=dest.with_suffix('.partial');temporary.write_bytes(content);temporary.chmod(0o600);temporary.replace(dest)
        objects.upload('narrations/'+dest.name,dest)
        return dest
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code==429:raise HTTPException(503,'ಧ್ವನಿ ಸೇವೆಯ ಬಳಕೆಯ ಮಿತಿ ತಲುಪಿದೆ. ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.') from None
        raise HTTPException(503,'Gemini ಧ್ವನಿ ಸೇವೆ ಈಗ ಲಭ್ಯವಿಲ್ಲ. ಸ್ವಲ್ಪ ಸಮಯದ ನಂತರ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.') from None
    except (httpx.HTTPError,ValueError,KeyError,TypeError,wave.Error,EOFError):
        raise HTTPException(503,'ಕನ್ನಡ ಧ್ವನಿಯನ್ನು ಸೃಷ್ಟಿಸಲಾಗಲಿಲ್ಲ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ ಅಥವಾ ವಿವರಣೆಯನ್ನು ಓದಿ.') from None
