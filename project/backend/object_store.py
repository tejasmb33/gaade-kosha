"""Backend-only private Supabase Storage; local development remains file based."""
import os,re
from urllib.parse import quote
import httpx
from fastapi import HTTPException


class ObjectStore:
    def __init__(self):
        self.url=os.getenv('SUPABASE_URL','').rstrip('/')
        self.key=os.getenv('SUPABASE_SERVICE_ROLE_KEY','')
        self.bucket=os.getenv('SUPABASE_STORAGE_BUCKET','gaade-private')
        self.enabled=bool(self.url and self.key)
        if bool(self.url)!=bool(self.key):raise ValueError('Configure both SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY')
        if self.enabled and (not self.url.startswith('https://') or not re.fullmatch(r'[a-zA-Z0-9_-]+',self.bucket)):
            raise ValueError('Invalid Supabase storage configuration')

    def _request(self,method,key,content=None):
        if not re.fullmatch(r'(audio|narrations)/[a-f0-9]+(?:\.wav)?',key):raise ValueError('Invalid storage object name')
        headers={'apikey':self.key,'Authorization':'Bearer '+self.key}
        if content is not None:headers.update({'Content-Type':'audio/wav' if key.endswith('.wav') else 'application/octet-stream','x-upsert':'true'})
        try:
            with httpx.Client(timeout=60,follow_redirects=False) as client:
                response=client.request(method,self.url+'/storage/v1/'+('object/authenticated/' if method=='GET' else 'object/')+quote(self.bucket)+'/'+key,headers=headers,content=content)
            if method=='GET' and response.status_code in (400,404):
                try:missing=str(response.json().get('statusCode',''))=='404' or response.json().get('code')=='NoSuchKey'
                except ValueError:missing=False
                if response.status_code==404 or missing:return None
            response.raise_for_status()
            if len(response.content)>25*1024*1024:raise ValueError('Oversized audio')
            return response.content
        except (httpx.HTTPError,ValueError):raise HTTPException(503,'Audio storage is unavailable. Please retry.') from None

    def ensure_bucket(self):
        if not self.enabled:raise ValueError('Private Supabase storage must be configured')
        headers={'apikey':self.key,'Authorization':'Bearer '+self.key}
        try:
            with httpx.Client(timeout=30,follow_redirects=False) as client:
                url=self.url+'/storage/v1/bucket/'+quote(self.bucket)
                response=client.get(url,headers=headers)
                missing=response.status_code==404
                if response.status_code==400:
                    try:missing=str(response.json().get('statusCode',''))=='404' or response.json().get('code') in ['NoSuchBucket','NoSuchKey']
                    except ValueError:pass
                if missing:
                    response=client.post(self.url+'/storage/v1/bucket',headers=headers,json={'id':self.bucket,'name':self.bucket,'public':False,'file_size_limit':26214400})
                    response.raise_for_status()
                    response=client.get(url,headers=headers)
                response.raise_for_status()
                if response.json().get('public') is not False:raise ValueError('Audio bucket must be private')
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (401,403):raise ValueError('Supabase Storage rejected the backend key (HTTP '+str(exc.response.status_code)+'). Check SUPABASE_SERVICE_ROLE_KEY; do not use a publishable or anon key.') from None
            raise ValueError('Supabase Storage request failed (HTTP '+str(exc.response.status_code)+'). Check SUPABASE_URL and the gaade-private bucket.') from None
        except httpx.HTTPError:raise ValueError('Cannot reach Supabase Storage. Check SUPABASE_URL and project availability.') from None
        except ValueError:raise ValueError('The gaade-private audio bucket must have Public turned OFF.') from None

    def upload(self,key,path):
        if self.enabled:self._request('POST',key,path.read_bytes())

    def restore(self,key,path):
        if path.exists():return True
        if not self.enabled:return False
        content=self._request('GET',key)
        if content is None:return False
        path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        path.write_bytes(content);path.chmod(0o600)
        return True
