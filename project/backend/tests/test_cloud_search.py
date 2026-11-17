"""External AI contract tests use mocked HTTP only; no keys or live calls."""
import json,sys,types
from pathlib import Path
import pytest,httpx
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.cloud_search import CloudSearch,CloudUnavailable,safe_sources
from backend.app import create_app,Proverb,index_record,APPROVED
from fastapi.testclient import TestClient

@pytest.fixture
def cloud(tmp_path,monkeypatch):
    monkeypatch.setenv('GAADE_AI_PROVIDER','openai');monkeypatch.setenv('GAADE_AI_MODEL','test-model')
    monkeypatch.setenv('OPENAI_API_KEY','synthetic-secret');monkeypatch.setenv('GAADE_AI_WEB_FALLBACK','true')
    app=create_app(tmp_path,'test-admin')
    with app.state.Session.begin() as s:
        for id,status in [('approved',APPROVED),('pending','PENDING_VERIFICATION')]:
            r=Proverb(id=id,proverb_kn='ಪರೀಕ್ಷೆ',literal_meaning='Synthetic fixture',contextual_meaning='Determination overcomes obstacles',example_usage='',category='Test',keywords='effort',transliteration='',verification_status=status)
            s.add(r);s.flush();index_record(s,r)
    return app,TestClient(app)

def response(text):return {'output':[{'content':[{'type':'output_text','text':text}]}]}
def mock_post(monkeypatch,callback):
    original=httpx.Client.post
    def post(self,url,**kwargs):
        if not str(url).startswith('https://'):return original(self,url,**kwargs)
        return httpx.Response(200,json=callback(url,kwargs),request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx.Client,'post',post)

def test_cloud_selects_only_existing_approved_record(cloud,monkeypatch):
    app,client=cloud
    def call(url,args):
        assert args['headers']['Authorization']=='Bearer synthetic-secret'
        assert args['json']['store'] is False
        prompt=args['json']['input'];assert 'approved' in prompt and '"id": "pending"' not in prompt
        return response(json.dumps({'interpretation':'Persistence despite financial obstacles','matches':[{'id':'approved','reason':'Her effort made education possible.'}]}))
    mock_post(monkeypatch,call)
    result=client.post('/api/search/ai',json={'query':'Financial difficulties nearly forced her to drop out. She worked and completed school.'})
    assert result.status_code==200,result.text
    assert result.json()['items'][0]['id']=='approved'
    assert 'synthetic-secret' not in result.text
    assert result.json()['external_sources']==[]

@pytest.mark.parametrize('id',['invented','pending'])
def test_unknown_and_private_ids_rejected(cloud,monkeypatch,id):
    _,client=cloud
    mock_post(monkeypatch,lambda *a:response(json.dumps({'interpretation':'Test','matches':[{'id':id,'reason':'Test'}]})))
    assert client.post('/api/search/ai',json={'query':'A test situation'}).status_code==503

def test_web_sources_are_grounded_metadata_not_generated_links(cloud,monkeypatch):
    app,client=cloud;calls=[]
    def call(url,args):
        calls.append(args['json'])
        if len(calls)==1:return response(json.dumps({'interpretation':'No matching record','matches':[]}))
        assert args['json']['tools']==[{'type':'web_search'}]
        return {'output':[{'content':[{'type':'output_text','text':'Made up proverb with https://invented.invalid','annotations':[{'type':'url_citation','url':'https://example.org/source','title':'Published reference'},{'type':'url_citation','url':'javascript:alert(1)','title':'Invalid'}]}]}]}
    mock_post(monkeypatch,call)
    result=client.post('/api/search/ai',json={'query':'A situation not covered'})
    assert result.status_code==200,result.text
    assert result.json()['external_sources']==[{'url':'https://example.org/source','title':'Published reference'}]
    assert 'Made up proverb' not in result.text and 'invented.invalid' not in result.text
    with app.state.Session() as s:assert len(s.query(Proverb).all())==2

def test_missing_config_keeps_local_available(cloud,monkeypatch):
    _,client=cloud;monkeypatch.delenv('OPENAI_API_KEY')
    assert client.post('/api/search/ai',json={'query':'A situation'}).status_code==503
    assert client.post('/api/search',json={'query':'effort'}).status_code==200

@pytest.mark.parametrize('failure',['malformed','http'])
def test_provider_errors_are_safe(cloud,monkeypatch,failure):
    _,client=cloud
    original=httpx.Client.post
    def fail(self,url,**kwargs):
        if not str(url).startswith('https://'):return original(self,url,**kwargs)
        if failure=='malformed':return httpx.Response(200,json=response('not json'),request=httpx.Request('POST',url))
        raise httpx.ConnectError('synthetic-secret provider failure')
    monkeypatch.setattr(httpx.Client,'post',fail)
    result=client.post('/api/search/ai',json={'query':'A situation'})
    assert result.status_code==503 and 'synthetic-secret' not in result.text

def test_gemini_request_contract(cloud,monkeypatch):
    _,client=cloud;monkeypatch.setenv('GAADE_AI_PROVIDER','gemini');monkeypatch.setenv('GEMINI_API_KEY','gemini-synthetic-secret')
    def call(url,args):
        assert url.startswith('https://generativelanguage.googleapis.com/')
        assert args['headers']['x-goog-api-key']=='gemini-synthetic-secret'
        assert args['json']['generationConfig']['responseMimeType']=='application/json'
        return {'candidates':[{'content':{'parts':[{'text':json.dumps({'interpretation':'Persistence','matches':[{'id':'approved','reason':'Effort despite obstacles'}]})}]}}]}
    mock_post(monkeypatch,call)
    assert client.post('/api/search/ai',json={'query':'Kept studying despite obstacles'}).json()['items'][0]['id']=='approved'

@pytest.mark.parametrize('code,expected',[(429,'quota'),(403,'authentication'),(404,'model'),(503,'temporarily busy')])
def test_free_tier_errors_are_actionable(cloud,monkeypatch,code,expected):
    _,client=cloud;original=httpx.Client.post
    def post(self,url,**kwargs):
        if not str(url).startswith('https://'):return original(self,url,**kwargs)
        return httpx.Response(code,json={'error':'synthetic-secret'},request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx.Client,'post',post)
    result=client.post('/api/search/ai',json={'query':'A difficult situation'})
    assert result.status_code==503 and expected in result.text.lower()
    assert 'synthetic-secret' not in result.text

def test_groq_additional_provider_keeps_gemini_default(cloud,monkeypatch):
    _,client=cloud
    monkeypatch.setenv('GAADE_AI_PROVIDER','gemini');monkeypatch.setenv('GEMINI_API_KEY','synthetic-gemini')
    monkeypatch.setenv('GROQ_API_KEY','synthetic-groq');monkeypatch.setenv('GAADE_GROQ_MODEL','openai/gpt-oss-20b')
    def call(url,args):
        assert url=='https://api.groq.com/openai/v1/chat/completions'
        assert args['headers']['Authorization']=='Bearer synthetic-groq'
        assert args['json']['model']=='openai/gpt-oss-20b'
        assert args['json']['max_completion_tokens']==1500 and args['json']['reasoning_effort']=='low'
        assert args['json']['response_format']['json_schema']['strict'] is True
        return {'choices':[{'message':{'content':json.dumps({'interpretation':'Persistence','matches':[{'id':'approved','reason':'Effort overcame obstacles'}]})}}]}
    mock_post(monkeypatch,call)
    result=client.post('/api/search/ai',json={'query':'A synthetic effort situation','provider':'groq'})
    assert result.status_code==200,result.text
    assert result.json()['provider']=='groq' and result.json()['items'][0]['id']=='approved'
    health=client.get('/api/health').json()['cloud_ai']
    assert health['provider']=='gemini' and health['groq_configured'] is True
    assert 'synthetic-groq' not in result.text

def test_groq_rejects_private_ids_and_no_web_calls(cloud,monkeypatch):
    _,client=cloud;monkeypatch.setenv('GROQ_API_KEY','synthetic-groq');calls=[]
    def call(url,args):
        calls.append(url)
        return {'choices':[{'message':{'content':json.dumps({'interpretation':'No match','matches':[]})}}]}
    mock_post(monkeypatch,call)
    result=client.post('/api/search/ai',json={'query':'An unknown situation','provider':'groq'})
    assert result.status_code==200 and result.json()['items']==[]
    assert len(calls)==1 and result.json()['external_sources']==[]
    mock_post(monkeypatch,lambda *a:{'choices':[{'message':{'content':json.dumps({'interpretation':'Bad ID','matches':[{'id':'pending','reason':'No'}]})}}]})
    assert client.post('/api/search/ai',json={'query':'An unknown situation','provider':'groq'}).status_code==503
