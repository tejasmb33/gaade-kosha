"""Explicitly configured cloud speech; no runtime model downloads."""
import os
import httpx
from fastapi import HTTPException


def provider():return os.getenv('GAADE_SPEECH_PROVIDER','local').lower()


def transcribe_cloud(path,language='kn',task='transcribe'):
    if provider()!='groq':raise HTTPException(503,'Cloud speech is not configured')
    key=os.getenv('GROQ_API_KEY','')
    if not key:raise HTTPException(503,'Voice input is unavailable. Please type your situation.')
    endpoint='translations' if task=='translate' else 'transcriptions'
    fields={'model':'whisper-large-v3' if task=='translate' else 'whisper-large-v3-turbo','response_format':'json','temperature':'0'}
    if task!='translate':fields['language']=language
    try:
        prefix=path.read_bytes()[:12]
        extension='wav' if prefix.startswith(b'RIFF') else 'webm' if prefix.startswith(b'\x1aE\xdf\xa3') else 'mp4'
        with httpx.Client(timeout=httpx.Timeout(90,connect=10),follow_redirects=False) as client,path.open('rb') as audio:
            response=client.post('https://api.groq.com/openai/v1/audio/'+endpoint,headers={'Authorization':'Bearer '+key},data=fields,files={'file':('speech.'+extension,audio,'application/octet-stream')})
        response.raise_for_status();result=response.json()
        if not isinstance(result,dict) or not isinstance(result.get('text'),str):raise ValueError('Missing text')
        return result
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code==429:raise HTTPException(503,'Voice input limit reached. Please retry later or type your situation.') from None
        raise HTTPException(503,'Voice input is unavailable. Please retry or type your situation.') from None
    except (httpx.HTTPError,ValueError):raise HTTPException(503,'Voice input is unavailable. Please retry or type your situation.') from None
