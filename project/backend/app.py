"""Local-only reviewed Kannada proverb archive. No runtime model downloads."""
import hashlib, hmac, json, os, platform, re, subprocess, tempfile, threading, unicodedata, uuid
from datetime import datetime, timezone
from typing import Literal
from pathlib import Path
import numpy as np
from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
from .bilingual_display import load_display
from .dictionary_situations import situations_for
from .dictionary_themes import theme_for
from .dictionary_translations import load_translation
from .narration import generate as generate_narration
from .object_store import ObjectStore
from .speech import provider as speech_provider,transcribe_cloud
from .cloud_search import CloudSearch,CloudUnavailable,status as cloud_status
from sqlalchemy import create_engine, String, Text, ForeignKey, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

# Runtime inference must never fetch from a remote model registry.
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')

PENDING='PENDING_VERIFICATION'; APPROVED='APPROVED'; REJECTED='REJECTED'
def now(): return datetime.now(timezone.utc).isoformat()
def uid(): return uuid.uuid4().hex
def tokens(value):
    value=unicodedata.normalize('NFC', value).casefold().replace('\u200d','').replace('\u200c','')
    result=[]; word=''
    for ch in value:
        if unicodedata.category(ch)[0] in 'LNM': word+=ch
        elif word: result.append(word); word=''
    if word: result.append(word)
    return result
# ASCII encoding prevents SQLite's default tokenizer from discarding Indic marks.
def fts_words(value): return ' '.join('u'+w.encode().hex() for w in tokens(value))
class Base(DeclarativeBase): pass
class Proverb(Base):
    __tablename__='proverbs'
    id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    proverb_kn: Mapped[str]=mapped_column(Text)
    transliteration: Mapped[str]=mapped_column(Text, default='')
    literal_meaning: Mapped[str]=mapped_column(Text)
    contextual_meaning: Mapped[str]=mapped_column(Text)
    example_usage: Mapped[str]=mapped_column(Text, default='')
    category: Mapped[str]=mapped_column(Text, default='')
    keywords: Mapped[str]=mapped_column(Text, default='')
    region: Mapped[str]=mapped_column(Text, default='')
    dialect: Mapped[str]=mapped_column(Text, default='')
    source: Mapped[str]=mapped_column(Text, default='')
    contributor: Mapped[str]=mapped_column(Text, default='')
    verification_status: Mapped[str]=mapped_column(String, default=PENDING)
    created_at: Mapped[str]=mapped_column(String, default=now)
    reviewed_at: Mapped[str|None]=mapped_column(String, nullable=True)
class Recording(Base):
    __tablename__='recordings'
    id: Mapped[str]=mapped_column(String, primary_key=True, default=uid)
    proverb_id: Mapped[str|None]=mapped_column(ForeignKey('proverbs.id'), nullable=True, unique=True)
    filename: Mapped[str]=mapped_column(String)
    original_transcript: Mapped[str]=mapped_column(Text, default='')
    corrected_transcript: Mapped[str]=mapped_column(Text, default='')
    created_at: Mapped[str]=mapped_column(String, default=now)
class Contribution(BaseModel):
    proverb_kn: str=Field(min_length=1,max_length=1000)
    literal_meaning: str=Field(min_length=1,max_length=3000)
    contextual_meaning: str=Field(min_length=1,max_length=3000)
    transliteration: str=Field(default='',max_length=1500)
    example_usage: str=Field(default='',max_length=3000)
    category: str=Field(default='',max_length=100)
    keywords: str=Field(default='',max_length=1000)
    region: str=Field(default='',max_length=200)
    dialect: str=Field(default='',max_length=200)
    source: str=Field(default='',max_length=3000)
    contributor: str=Field(default='',max_length=200)
    audio_id: str|None=None
    @field_validator('*', mode='before')
    @classmethod
    def strip(cls,v): return v.strip() if isinstance(v,str) else v
    @field_validator('proverb_kn')
    @classmethod
    def kannada(cls,v):
        if not any('\u0c85'<=c<='\u0cb9' for c in v): raise ValueError('Original Kannada script is required')
        return v
class Search(BaseModel):
    query: str=Field(min_length=1,max_length=1000)
    @field_validator('query')
    @classmethod
    def meaningful(cls,v):
        if not tokens(v): raise ValueError('Enter words describing a situation')
        return v
class CloudQuery(Search):
    provider: Literal['gemini','openai','groq']|None=None
class AudioRequest(BaseModel): audio_id: str=Field(max_length=64)
def dump(row): return {c.name:getattr(row,c.name) for c in row.__table__.columns}
def searchable(row): return ' '.join(getattr(row,k) for k in ['proverb_kn','transliteration','literal_meaning','contextual_meaning','example_usage','category','keywords'])
def index_record(s,row):
    if s.bind.dialect.name!='sqlite':return
    s.execute(text('DELETE FROM proverb_fts WHERE id=:id'),{'id':row.id})
    if row.verification_status==APPROVED: s.execute(text('INSERT INTO proverb_fts(id,words) VALUES (:id,:words)'),{'id':row.id,'words':fts_words(searchable(row))})
def validate_audio(content,original,decoded):
    original.write_bytes(content)
    probe=subprocess.run(['ffprobe','-v','error','-show_entries','format=format_name:stream=codec_type','-of','json',str(original)],capture_output=True,timeout=10)
    info=json.loads(probe.stdout or '{}'); formats=info.get('format',{}).get('format_name','')
    if probe.returncode or not any(x.get('codec_type')=='audio' for x in info.get('streams',[])) or not any(x in formats for x in ['wav','webm','matroska','mp4','mov']): raise ValueError()
    process=subprocess.run(['ffmpeg','-nostdin','-v','error','-i',str(original),'-map','0:a:0','-t','91','-ac','1','-ar','16000','-f','s16le',str(decoded)],capture_output=True,timeout=20)
    duration=decoded.stat().st_size/32000 if decoded.exists() else 0
    if process.returncode or duration<=0: raise ValueError()
    if duration>90: raise HTTPException(422,'Maximum recording duration is 90 seconds')
    return duration

# Ignore English function words for lexical coverage, but retain negation.
SEARCH_STOPWORDS=set('a an the i me my we our you your he she it they their is am are was were be been being to of for in on at by with and or this that these those someone something person people do does did'.split())
def query_terms(value):
    return set(tokens(value))-SEARCH_STOPWORDS

def semantic_passage(row,include_example=True):
    # Editorial draft labels are not retrieval content. Stored originals remain intact.
    meaning=re.sub(r'^Draft(?: for human verification)?:\s*','',row.contextual_meaning,flags=re.IGNORECASE)
    example=re.sub(r'^Draft:\s*','',row.example_usage or '',flags=re.IGNORECASE)
    return meaning+' '+row.keywords+(' Example: '+example if include_example and example else '')

class Semantic:
    def __init__(self,path,cache): self.path=path; self.cache=cache; self.model=None; self.error=None; self.lock=threading.Lock()
    def load(self):
        if not self.path or self.error or self.model is not None: return
        try:
            from sentence_transformers import SentenceTransformer
            self.model=SentenceTransformer(self.path,local_files_only=True,trust_remote_code=False)
        except Exception: self.error='Local semantic model could not load. Keyword search remains available.'
    def scores(self,query,rows):
        with self.lock:
            self.load()
            if self.model is None or not rows: return {}
            try:
                revision=Path(self.path,'revision.json').read_text()
                q=self.model.encode(['query: '+query],normalize_embeddings=True)[0]
                vectors={}; missing=[]
                for row in rows:
                    passage=semantic_passage(row)
                    key=hashlib.sha256(('context-example-v4'+revision+passage).encode()).hexdigest(); dest=self.cache/(key+'.npy')
                    if dest.exists(): vectors[row.id]=np.load(dest,allow_pickle=False)
                    else: missing.append((row.id,dest,[semantic_passage(row,False),passage]))
                if missing:
                    encoded=self.model.encode(['passage: '+p for _,_,views in missing for p in views],normalize_embeddings=True)
                    for i,(id,dest,_) in enumerate(missing):
                        vec=np.stack(encoded[i*2:i*2+2])
                        np.save(dest,vec,allow_pickle=False);vectors[id]=vec
                out={id:float(np.max(vec @ q)) for id,vec in vectors.items()}
                return out
            except Exception:
                self.error='Semantic inference unavailable; keyword search remains available.'; self.model=None
                return {}

def create_app(data_dir=None,admin_token=None,database_url=None):
    data=Path(data_dir or os.getenv('GAADE_DATA_DIR',Path(__file__).resolve().parents[1]/'data')).resolve()
    data.mkdir(parents=True,exist_ok=True)
    for folder in ['audio','embeddings']: (data/folder).mkdir(exist_ok=True,mode=0o700)
    url=database_url or (os.getenv('DATABASE_URL') if data_dir is None else None)
    if url:
        if url.startswith('postgres://'):url='postgresql+psycopg://'+url[len('postgres://'):]
        elif url.startswith('postgresql://'):url='postgresql+psycopg://'+url[len('postgresql://'):]
        if not url.startswith('postgresql+psycopg://'):raise ValueError('DATABASE_URL must be PostgreSQL')
        engine=create_engine(url,connect_args={'sslmode':os.getenv('GAADE_DATABASE_SSLMODE','require'),'options':'-csearch_path=gaade'},pool_size=2,max_overflow=1,pool_pre_ping=True)
        with engine.begin() as conn:conn.execute(text('CREATE SCHEMA IF NOT EXISTS gaade'))
    else:engine=create_engine('sqlite:///'+str(data/'gaade.db'),connect_args={'check_same_thread':False})
    Base.metadata.create_all(engine); Session=sessionmaker(engine)
    if engine.dialect.name=='sqlite':
        with engine.begin() as conn:conn.execute(text('CREATE VIRTUAL TABLE IF NOT EXISTS proverb_fts USING fts5(id UNINDEXED,words)'))
    else:
        with engine.begin() as conn:
            conn.execute(text('CREATE TABLE IF NOT EXISTS dictionary_translations (id TEXT PRIMARY KEY REFERENCES proverbs(id), payload TEXT NOT NULL)'))
            translations=list(conn.execute(text('SELECT id,payload FROM dictionary_translations')))
        folder=data/'translations';folder.mkdir(exist_ok=True)
        for id,payload in translations:
            if re.fullmatch('[a-f0-9]{32}',id):(folder/(id+'.json')).write_text(payload)
    objects=ObjectStore()
    app=FastAPI(title='GAADE KOSHA',version='1.0')
    app.add_middleware(CORSMiddleware,allow_origins=[os.getenv('FRONTEND_ORIGIN','http://localhost:5173')],allow_methods=['GET','POST','PATCH'],allow_headers=['Content-Type','X-Admin-Token'])
    app.state.Session=Session; app.state.data=data; app.state.engine=engine
    semantic=Semantic(os.getenv('E5_MODEL_PATH',''),data/'embeddings'); app.state.semantic=semantic
    token=admin_token if admin_token is not None else os.getenv('ADMIN_TOKEN','')
    speech_path=os.getenv('WHISPER_MODEL_PATH',''); speech_error=None; audio_lock=threading.Lock(); narration_lock=threading.Lock()
    def auth(value):
        if not token: raise HTTPException(503,'Moderation is not configured')
        if not value or not hmac.compare_digest(value.encode(),token.encode()): raise HTTPException(401,'Invalid moderation token')
    def get_record(s,id,public=True):
        row=s.get(Proverb,id)
        if not row or (public and row.verification_status!=APPROVED): raise HTTPException(404,'Proverb not found')
        return row
    @app.get('/api/health')
    def health(): return {'backend':'ok','cloud_ai':cloud_status(),'semantic':{'configured':bool(semantic.path),'loaded':semantic.model is not None,'error':semantic.error},'speech':{'provider':speech_provider(),'mlx_supported':platform.system()=='Darwin' and platform.machine()=='arm64','configured':bool(os.getenv('GROQ_API_KEY')) if speech_provider()=='groq' else bool(speech_path),'error':speech_error}}
    @app.get('/api/categories')
    def categories(bilingual:bool=False):
        with Session() as s:
            rows=list(s.scalars(select(Proverb).where(Proverb.verification_status==APPROVED,Proverb.category!='')))
            values=sorted({r.category for r in rows})
            if not bilingual:return values
            names={}
            for row in rows:
                translated=load_translation(data,row)
                if translated:names[row.category]=translated['fields'].get('category_kn','')
            return [{'value':value,'label_kn':names.get(value,'')} for value in values]
    @app.get('/api/proverbs')
    def library(theme:Literal['','money','work','study','family','friends','character']=Query(''),q:str=Query('',max_length=1000),category:str=Query('',max_length=100),page:int=Query(1,ge=1),page_size:int=Query(12,ge=1,le=50),sort:Literal['recent','alphabetical']=Query('recent')):
        with Session() as s:
            rows=list(s.scalars(select(Proverb).where(Proverb.verification_status==APPROVED).order_by(Proverb.created_at.desc())))
            if sort=='alphabetical': rows.sort(key=lambda r: (unicodedata.normalize('NFC',r.proverb_kn),r.id))
            if theme: rows=[r for r in rows if theme_for(r.category)==theme]
            if category: rows=[r for r in rows if r.category==category]
            if tokens(q): rows=[r for r in rows if set(tokens(q))<=set(tokens(searchable(r)+' '+json.dumps((load_translation(data,r) or {}).get('fields',{}),ensure_ascii=False)))]
            return {'items':[{**dump(r),'translation':load_translation(data,r)} for r in rows[(page-1)*page_size:page*page_size]],'total':len(rows),'page':page,'page_size':page_size}
    @app.get('/api/proverbs/{id}')
    def detail(id:str):
        with Session() as s:
            row=get_record(s,id); result=dump(row);result['translation']=load_translation(data,row);result['situations']=situations_for(row);result['display']=load_display(data,row)
            result['related']=[{**dump(r),'translation':load_translation(data,r)} for r in s.scalars(select(Proverb).where(Proverb.verification_status==APPROVED,Proverb.id!=id,Proverb.category==row.category).limit(3))]
            return result
    @app.post('/api/proverbs/{id}/narration')
    def narration(id:str):
        with Session() as s:
            row=get_record(s,id)
            with narration_lock:path=generate_narration(data,row)
            return FileResponse(path,media_type='audio/wav',filename='gaade-kannada.wav',headers={'Cache-Control':'no-store'})
    @app.post('/api/search')
    def search(body:Search):
        with Session() as s:
            terms=query_terms(body.query)
            if not terms:
                return {'mode':'keyword','items':[],'message':'Describe what happened using a few specific words.','capability_notice':None}
            match=' OR '.join('"u'+w.encode().hex()+'"' for w in terms)
            rows=list(s.scalars(select(Proverb).where(Proverb.verification_status==APPROVED)))
            ids=list(s.execute(text('SELECT id FROM proverb_fts WHERE words MATCH :q ORDER BY bm25(proverb_fts) LIMIT 100'),{'q':match}).scalars()) if engine.dialect.name=='sqlite' else [r.id for r in rows if terms & set(tokens(searchable(r)))]
            # Match situations against contextual fields; literal images alone can mislead.
            lexical={r.id:len(terms & set(tokens(' '.join([r.contextual_meaning,r.example_usage,r.category,r.keywords]))))/len(terms) for r in rows if r.id in ids}
            lexical={k:v for k,v in lexical.items() if v>=0.25}
            exact={r.id for r in rows if tokens(body.query)==tokens(r.proverb_kn)}
            scores=semantic.scores(body.query,rows)
            sem={}
            if scores:
                ordered=sorted(scores,key=scores.get,reverse=True)
                best=scores[ordered[0]]; margin=best-scores[ordered[1]] if len(ordered)>1 else best
                # Provisional guard: avoid forcing a guess for weak/ambiguous situations.
                if (best>=0.80 and (best>=0.84 or margin>=0.005 or lexical.get(ordered[0],0)>=0.5)) or (best>=0.78 and margin>=0.02 and len(terms)>=3):
                    sem={id:score for id,score in scores.items() if score>=max(0.78,best-0.02) and (id==ordered[0] or score>=0.84)}
                if len(terms)<3 and not lexical and best<0.84: sem={}
                candidates=set(sem)|exact
                ranked=sorted(candidates,key=lambda id:(id in exact,scores.get(id,0)+0.015*lexical.get(id,0)),reverse=True)[:3]
            else:
                candidates=set(lexical)|exact
                ranked=sorted(candidates,key=lambda id:(id in exact,lexical.get(id,0)),reverse=True)[:3]
            byid={r.id:r for r in rows}; result=[]
            for i,id in enumerate(ranked):
                row=byid[id]; matched=sorted(terms & set(tokens(searchable(row))))
                result.append({**dump(row),'translation':load_translation(data,row),'display':load_display(data,row),'situations':situations_for(row),'rank':i+1,'why':('Stored metadata matches: '+', '.join(matched)) if matched else 'Local E5 matched the situation to this stored meaning: '+re.sub(r'^Draft(?: for human verification)?:\s*','',row.contextual_meaning),'ranking_label':f'Rank {i+1} · relative order, not probability'})
            return {'mode':'hybrid' if scores else 'keyword','items':result,'message':None if result else 'No reliable match in the reviewed collection. Try other words or contribute a sourced proverb.','capability_notice':semantic.error}
    @app.post('/api/search/ai')
    def ai_search(body:CloudQuery):
        try:
            cloud=CloudSearch(body.provider)
            with Session() as s:
                rows=list(s.scalars(select(Proverb).where(Proverb.verification_status==APPROVED).order_by(Proverb.id)))
                decision=cloud.select(body.query,rows)
                by_id={r.id:r for r in rows};items=[]
                for i,choice in enumerate(decision.matches,1):
                    items.append({**dump(by_id[choice.id]),'translation':load_translation(data,by_id[choice.id]),'display':load_display(data,by_id[choice.id]),'situations':situations_for(by_id[choice.id]),'rank':i,'why':'AI interpretation (not cultural verification): '+choice.reason,'ranking_label':f'Rank {i} · not a probability'})
            result={'mode':'cloud','provider':cloud.provider,'model':cloud.model,'items':items,'interpretation':decision.interpretation,'external_sources':[],'capability_notice':'Situation and approved metadata were sent to the configured cloud provider.','message':None if items else 'No suitable reviewed database match was selected.'}
            if not items and cloud_status(cloud.provider)['web_enabled']:
                try:result.update(cloud.web(body.query))
                except CloudUnavailable:result['web_notice']='Web fallback is unavailable. No unverified result was added.'
            return result
        except CloudUnavailable as exc:raise HTTPException(503,str(exc))
    @app.post('/api/contributions',status_code=201)
    def contribute(body:Contribution):
        with audio_lock, Session.begin() as s:
            values=body.model_dump(exclude={'audio_id'}); row=Proverb(**values); s.add(row); s.flush()
            if body.audio_id:
                rec=s.get(Recording,body.audio_id)
                if not rec: raise HTTPException(404,'Recording not found')
                if rec.proverb_id: raise HTTPException(409,'Recording already submitted')
                rec.proverb_id=row.id; rec.corrected_transcript=body.proverb_kn
            return {'id':row.id,'verification_status':PENDING}
    @app.get('/api/admin/contributions')
    def pending(x_admin_token:str|None=Header(None)):
        auth(x_admin_token)
        with Session() as s:
            result=[]
            for r in s.scalars(select(Proverb).where(Proverb.verification_status==PENDING).order_by(Proverb.created_at)):
                rec=s.scalar(select(Recording).where(Recording.proverb_id==r.id)); obj=dump(r)
                obj['recording']=None if not rec else {k:v for k,v in dump(rec).items() if k!='filename'}; result.append(obj)
            return result
    @app.patch('/api/admin/contributions/{id}/{decision}')
    def review(id:str,decision:str,body:Contribution,x_admin_token:str|None=Header(None)):
        auth(x_admin_token)
        if decision not in ['approve','reject']: raise HTTPException(404,'Unknown action')
        with Session.begin() as s:
            # Acquire SQLite write lock before reading status, avoiding concurrent reviews.
            s.execute(text('UPDATE proverbs SET id=id WHERE id=:id'),{'id':id})
            row=get_record(s,id,False)
            if row.verification_status!=PENDING: raise HTTPException(409,'Already reviewed')
            if decision=='approve' and not body.source.strip(): raise HTTPException(422,'A verified source/reference is required')
            for k,v in body.model_dump(exclude={'audio_id'}).items(): setattr(row,k,v)
            row.verification_status=APPROVED if decision=='approve' else REJECTED; row.reviewed_at=now(); s.flush(); index_record(s,row)
            return {'id':id,'verification_status':row.verification_status}
    @app.post('/api/audio/upload',status_code=201)
    async def upload(file:UploadFile=File(...)):
        content=await file.read(10*1024*1024+1); await file.close()
        if len(content)>10*1024*1024: raise HTTPException(413,'Maximum upload is 10 MB')
        if not content: raise HTTPException(422,'Empty audio')
        id=uid(); dest=data/'audio'/id
        try:
            with tempfile.TemporaryDirectory() as tmp:
                original=Path(tmp)/'input'; decoded=Path(tmp)/'decoded.raw'
                duration=validate_audio(content,original,decoded)
                dest.write_bytes(content); dest.chmod(0o600)
            objects.upload('audio/'+id,dest)
            with Session.begin() as s: s.add(Recording(id=id,filename=id))
            return {'audio_id':id,'duration_seconds':duration}
        except HTTPException: raise
        except FileNotFoundError: raise HTTPException(503,'FFmpeg and ffprobe are required for audio validation')
        except (ValueError,subprocess.TimeoutExpired): raise HTTPException(422,'Invalid or unsupported audio')
    @app.post('/api/search/voice')
    def voice_search(file:UploadFile=File(...),language:Literal['kn','en']=Form('kn'),task:Literal['transcribe','translate']=Form('transcribe')):
        """Ephemeral situation dictation; no recording or contribution is retained."""
        nonlocal speech_error
        try:
            content=file.file.read(10*1024*1024+1)
        finally:
            file.file.close()
        if len(content)>10*1024*1024: raise HTTPException(413,'Maximum upload is 10 MB')
        if not content: raise HTTPException(422,'Empty audio')
        try:
            with tempfile.TemporaryDirectory(prefix='gaade-situation-') as tmp:
                original=Path(tmp)/'input'; decoded=Path(tmp)/'decoded.raw'
                validate_audio(content,original,decoded)
                if speech_provider()!='groq' and (platform.system()!='Darwin' or platform.machine()!='arm64' or not speech_path or not all((Path(speech_path)/f).is_file() for f in ['config.json','weights.npz']) or speech_error):
                    raise HTTPException(503,speech_error or 'Local speech model unavailable. Type your situation in Kannada or English.')
                with audio_lock:
                    try:
                        if speech_provider()=='groq':
                            source_result=transcribe_cloud(original,language,'transcribe')
                            result=transcribe_cloud(original,language,'translate') if task=='translate' else source_result
                        else:
                            import mlx_whisper
                            options={'path_or_hf_repo':speech_path,'language':language,'condition_on_previous_text':False,'temperature':0.0}
                            source_result=mlx_whisper.transcribe(str(original),task='transcribe',**options)
                            result=mlx_whisper.transcribe(str(original),task='translate',**options) if task=='translate' else source_result
                    except HTTPException:raise
                    except Exception:
                        speech_error='Local speech inference unavailable. Type your situation in Kannada or English.'
                        raise HTTPException(503,speech_error)
                transcript=result.get('text','').strip()
                if not tokens(transcript): raise HTTPException(422,'No speech was recognized. Speak clearly and try again, or type your situation.')
                if len(transcript)>1000: raise HTTPException(422,'The transcript is longer than 1000 characters. Record a shorter situation.')
                source_text=source_result.get('text','').strip()
                if len(source_text)>1000: raise HTTPException(422,'The transcript is longer than 1000 characters. Record a shorter situation.')
                warning='Automatic speech translation can change meaning, especially for short clips. Compare the original transcript or search in Kannada directly.' if task=='translate' else None
                return {'text':transcript,'source_text':source_text,'input_language':language,'output_language':'en' if task=='translate' else language,'task':task,'warning':warning}
        except HTTPException: raise
        except FileNotFoundError: raise HTTPException(503,'FFmpeg and ffprobe are required for voice input')
        except (ValueError,subprocess.TimeoutExpired): raise HTTPException(422,'Invalid or unsupported audio')
    @app.post('/api/audio/transcribe')
    def transcribe(body:AudioRequest):
        nonlocal speech_error
        with audio_lock,Session.begin() as s:
            rec=s.get(Recording,body.audio_id)
            if not rec: raise HTTPException(404,'Recording not found')
            if rec.proverb_id: raise HTTPException(409,'Submitted recordings cannot be retranscribed')
            if rec.original_transcript: return {'text':rec.original_transcript}
            if speech_provider()=='groq':
                path=data/'audio'/rec.filename
                if not objects.restore('audio/'+rec.filename,path):raise HTTPException(404,'Recording not found')
                result=transcribe_cloud(path,'kn')
                transcript=result.get('text','').strip()
                if not tokens(transcript):raise HTTPException(422,'No speech was recognized. Please retry.')
                rec.original_transcript=transcript
                return {'text':transcript}
            if platform.system()!='Darwin' or platform.machine()!='arm64' or not speech_path or not all((Path(speech_path)/f).is_file() for f in ['config.json','weights.npz']) or speech_error: raise HTTPException(503,speech_error or 'Local Kannada speech model unavailable. Enter the text manually.')
            try:
                import mlx_whisper
                result=mlx_whisper.transcribe(str(data/'audio'/rec.filename),path_or_hf_repo=speech_path,language='kn')
                rec.original_transcript=result['text'].strip(); return {'text':rec.original_transcript}
            except Exception:
                speech_error='Local speech model could not transcribe. Enter Kannada manually.'
                raise HTTPException(503,speech_error)
    @app.get('/api/admin/audio/{audio_id}')
    def audio(audio_id:str,x_admin_token:str|None=Header(None)):
        auth(x_admin_token)
        with Session() as s:
            rec=s.get(Recording,audio_id)
            if not rec: raise HTTPException(404,'Recording not found')
            path=data/'audio'/rec.filename
            if not objects.restore('audio/'+rec.filename,path):raise HTTPException(404,'Recording not found')
            return FileResponse(path,media_type='application/octet-stream',filename='recording')
    return app

app=create_app()
