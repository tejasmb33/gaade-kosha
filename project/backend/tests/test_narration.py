"""Narration routing/cache contracts with synthetic records and WAV; no live AI calls."""
import base64,io,json,sys,wave
from pathlib import Path
import httpx,pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.app import create_app,Proverb,APPROVED
from backend.dictionary_translations import fingerprint

def wav_bytes():
 out=io.BytesIO()
 with wave.open(out,'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(b'\x01\0'*24000)
 return out.getvalue()
@pytest.fixture
def setup(tmp_path,monkeypatch):
 monkeypatch.setenv('GAADE_TTS_ENABLED','true');monkeypatch.setenv('GEMINI_API_KEY','synthetic-secret')
 monkeypatch.setenv('GAADE_TTS_MODEL','gemini-3.8-flash-lite-tts')
 app=create_app(tmp_path,'test-token')
 with app.state.Session.begin() as s:
  for id,status in [('approved',APPROVED),('private','PENDING_VERIFICATION')]:
   row=Proverb(id=id,proverb_kn='ಪರೀಕ್ಷೆಯ ಗಾದೆ',literal_meaning='Synthetic literal',contextual_meaning='Synthetic context',example_usage='Synthetic example',category='Synthetic',keywords='',source='https://example.org',contributor='',region='',dialect='',verification_status=status)
   s.add(row);s.flush()
   if id=='approved':digest=fingerprint(row)
 folder=tmp_path/'translations';folder.mkdir()
 (folder/'approved.json').write_text(json.dumps({'status':'MACHINE_TRANSLATION_DRAFT','input_hash':digest,'fields':{'literal_meaning_kn':'ಕರಡು: ಪರೀಕ್ಷೆಯ ಪದಶಃ ಅರ್ಥ','contextual_meaning_kn':'ಕರಡು: ಪರೀಕ್ಷೆಯ ವಿವರಣೆ','example_usage_kn':'ಕರಡು: ಪರೀಕ್ಷೆಯ ಉದಾಹರಣೆ','category_kn':'ಪರೀಕ್ಷೆ'}}))
 from fastapi.testclient import TestClient
 return app,TestClient(app)

def test_generated_audio_cached_and_no_private_data(setup,monkeypatch):
 app,client=setup;original=httpx.Client.post;calls=[]
 def post(self,url,**kwargs):
  if not str(url).startswith('https://'):return original(self,url,**kwargs)
  body=kwargs['json'];text=body['input'][0]['content'][0]['text'];calls.append(text)
  assert 'ಪರೀಕ್ಷೆಯ ವಿವರಣೆ' in text and 'ಪರೀಕ್ಷೆಯ ಉದಾಹರಣೆ' in text
  assert 'https://example.org' not in text and 'synthetic-secret' not in text
  assert 'ಪರಿಶೀಲನೆಗೆ' in text
  return httpx.Response(200,json={'steps':[{'type':'model_output','content':[{'type':'audio','data':base64.b64encode(wav_bytes()).decode()}]}]},request=httpx.Request('POST',url))
 monkeypatch.setattr(httpx.Client,'post',post)
 for _ in range(2):
  r=client.post('/api/proverbs/approved/narration');assert r.status_code==200,r.text
  assert r.headers['content-type']=='audio/wav' and r.content==wav_bytes()
 assert len(calls)==1
 assert client.post('/api/proverbs/private/narration').status_code==404
 assert client.post('/api/proverbs/missing/narration').status_code==404
 with app.state.Session.begin() as s:s.get(Proverb,'approved').contextual_meaning='Edited meaning invalidates translation'
 assert client.post('/api/proverbs/approved/narration').status_code==409
 assert len(calls)==1

def test_disabled_and_missing_key(setup,monkeypatch):
 _,client=setup;monkeypatch.setenv('GAADE_TTS_ENABLED','false')
 assert client.post('/api/proverbs/approved/narration').status_code==503
 monkeypatch.setenv('GAADE_TTS_ENABLED','true');monkeypatch.delenv('GEMINI_API_KEY')
 assert client.post('/api/proverbs/approved/narration').status_code==503

def test_provider_failure_does_not_expose_details(setup,monkeypatch):
 _,client=setup;original=httpx.Client.post
 def post(self,url,**kwargs):
  if not str(url).startswith('https://'):return original(self,url,**kwargs)
  return httpx.Response(429,json={'error':'synthetic-secret'},request=httpx.Request('POST',url))
 monkeypatch.setattr(httpx.Client,'post',post)
 r=client.post('/api/proverbs/approved/narration');assert r.status_code==503 and 'synthetic-secret' not in r.text
