"""Synthetic cloud adapter contracts; no external services or actual recordings."""
import io,wave,json
from pathlib import Path
import httpx,pytest
from fastapi.testclient import TestClient
from backend.app import create_app,Proverb,APPROVED
from backend.object_store import ObjectStore
from scripts.bootstrap_cloud import seed


def wav():
    out=io.BytesIO()
    with wave.open(out,'wb') as stream:
        stream.setnchannels(1);stream.setsampwidth(2);stream.setframerate(16000);stream.writeframes(b'\0\0'*16000)
    return out.getvalue()


def test_groq_voice_language_translation_and_retry(tmp_path,monkeypatch):
    monkeypatch.setenv('GAADE_SPEECH_PROVIDER','groq');monkeypatch.setenv('GROQ_API_KEY','synthetic-private-key')
    monkeypatch.setenv('WHISPER_MODEL_PATH','');monkeypatch.setenv('E5_MODEL_PATH','')
    calls=[];original=httpx.Client.post;fail=[True]
    def post(client,url,**kwargs):
        if not str(url).startswith('https://'):return original(client,url,**kwargs)
        assert url.startswith('https://api.groq.com/openai/v1/audio/')
        assert kwargs['headers']['Authorization']=='Bearer synthetic-private-key'
        if fail[0]:
            fail[0]=False
            return httpx.Response(429,json={'error':'synthetic-private-key'},request=httpx.Request('POST',url))
        calls.append((url,kwargs['data']))
        assert kwargs['files']['file'][0]=='speech.wav'
        return httpx.Response(200,json={'text':'I need patience' if url.endswith('translations') else 'ನನಗೆ ತಾಳ್ಮೆ ಬೇಕು'},request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx.Client,'post',post)
    app=create_app(tmp_path,'synthetic-token');client=TestClient(app)
    def recognize():return client.post('/api/search/voice',files={'file':('fixture.wav',wav(),'audio/wav')},data={'language':'kn','task':'translate'})
    failed=recognize();assert failed.status_code==503 and 'synthetic-private-key' not in failed.text
    response=recognize();assert response.status_code==200,response.text
    assert response.json()['source_text']=='ನನಗೆ ತಾಳ್ಮೆ ಬೇಕು'
    assert response.json()['text']=='I need patience'
    assert calls[0][1]['language']=='kn' and calls[0][1]['model']=='whisper-large-v3-turbo'
    assert 'language' not in calls[1][1] and calls[1][1]['model']=='whisper-large-v3'
    assert client.get('/api/health').json()['speech']['provider']=='groq'
    assert list((tmp_path/'audio').iterdir())==[]


def test_private_storage_restore_upload_and_no_public_urls(tmp_path,monkeypatch):
    monkeypatch.setenv('SUPABASE_URL','https://synthetic.supabase.co');monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY','synthetic-private-key')
    store=ObjectStore();calls=[]
    def request(client,method,url,**kwargs):
        calls.append((method,url));assert kwargs['headers']['Authorization']=='Bearer synthetic-private-key'
        return httpx.Response(200,content=wav() if method=='GET' else b'{}',request=httpx.Request(method,url))
    monkeypatch.setattr(httpx.Client,'request',request)
    path=tmp_path/'audio';key='audio/'+'a'*32
    assert store.restore(key,path) and path.read_bytes()==wav()
    store.upload(key,path)
    assert calls[0][1]=='https://synthetic.supabase.co/storage/v1/object/authenticated/gaade-private/'+key
    assert calls[1][0]=='POST' and '/object/gaade-private/' in calls[1][1]
    assert store.restore(key,path) and len(calls)==2
    with pytest.raises(ValueError):store.restore('../private',tmp_path/'other')


def test_approved_seed_never_overwrites_or_imports_pending(tmp_path):
    app=create_app(tmp_path,'synthetic-token')
    record={'id':'a'*32,'proverb_kn':'ಪರೀಕ್ಷಾ ಗಾದೆ','literal_meaning':'Synthetic','contextual_meaning':'Synthetic','source':'https://example.org','verification_status':APPROVED}
    assert seed(app,[{'record':record,'translation':None}])==1
    assert seed(app,[{'record':{**record,'literal_meaning':'Overwritten'},'translation':None}])==0
    assert TestClient(app).get('/api/proverbs/'+record['id']).json()['literal_meaning']=='Synthetic'
    empty=create_app(tmp_path/'other','synthetic-token')
    with pytest.raises(ValueError):seed(empty,[{'record':{**record,'verification_status':'PENDING_VERIFICATION'},'translation':None}])
    assert TestClient(empty).get('/api/proverbs').json()['total']==0


def test_cloud_startup_diagnostics_do_not_leak_database_password(monkeypatch):
    from scripts.bootstrap_cloud import validate_environment,safe_failure
    for key,value in {'DATABASE_URL':'postgresql://postgres.fixture:synthetic%40password@fixture.pooler.supabase.com:5432/postgres','SUPABASE_URL':'https://fixture.supabase.co','SUPABASE_SERVICE_ROLE_KEY':'synthetic-private-key','GROQ_API_KEY':'synthetic-private-key','GAADE_SPEECH_PROVIDER':'groq'}.items():monkeypatch.setenv(key,value)
    validate_environment()
    monkeypatch.setenv('DATABASE_URL','postgresql://postgres.fixture:[synthetic@password]@fixture.pooler.supabase.com:5432/postgres')
    with pytest.raises(ValueError,match='URL-encode') as error:validate_environment()
    assert 'synthetic@password' not in str(error.value)
    message=safe_failure('database connection and schema',RuntimeError('password authentication failed: synthetic-secret'))
    assert 'synthetic-secret' not in message and 'rejected' in message
    monkeypatch.delenv('SUPABASE_SERVICE_ROLE_KEY')
    with pytest.raises(ValueError,match='SUPABASE_SERVICE_ROLE_KEY'):validate_environment()


def test_missing_storage_bucket_400_created_privately(monkeypatch):
    monkeypatch.setenv('SUPABASE_URL','https://synthetic.supabase.co');monkeypatch.setenv('SUPABASE_SERVICE_ROLE_KEY','synthetic-private-key')
    calls=[]
    def request(client,method,url,**kwargs):
        calls.append(method)
        if len(calls)==1:return httpx.Response(400,json={'statusCode':'404','error':'Bucket not found'},request=httpx.Request(method,url))
        if method=='POST':assert kwargs['json']['public'] is False
        return httpx.Response(200,json={'public':False},request=httpx.Request(method,url))
    monkeypatch.setattr(httpx.Client,'request',request)
    ObjectStore().ensure_bucket()
    assert calls==['GET','POST','GET']
