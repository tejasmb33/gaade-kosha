"""Voice query tests use synthetic WAVs and mocked ASR, never real collection data."""
import io,sys,types,wave
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.app import create_app,Recording
from fastapi.testclient import TestClient
from sqlalchemy import select

def wav():
    out=io.BytesIO()
    with wave.open(out,'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(16000);f.writeframes(b'\0\0'*16000)
    return out.getvalue()
@pytest.fixture
def setup(tmp_path,monkeypatch):
    model=tmp_path/'speech';model.mkdir()
    for name in ['config.json','weights.npz']:(model/name).touch()
    monkeypatch.setenv('WHISPER_MODEL_PATH',str(model))
    monkeypatch.setenv('E5_MODEL_PATH','')
    monkeypatch.setattr('backend.app.platform.system',lambda:'Darwin')
    monkeypatch.setattr('backend.app.platform.machine',lambda:'arm64')
    app=create_app(tmp_path/'data','synthetic-token')
    return app,TestClient(app)
@pytest.mark.parametrize('language,task,text',[('kn','transcribe','ನನಗೆ ಸಹನೆ ಬೇಕು'),('en','transcribe','I need patience'),('kn','translate','I need patience')])
def test_language_task_and_ephemeral_audio(setup,monkeypatch,language,task,text):
    app,client=setup;paths=[]
    def transcribe(path,**kwargs):
        assert Path(path).exists();paths.append(path)
        assert kwargs['language']==language and kwargs['task'] in (['transcribe','translate'] if task=='translate' else ['transcribe'])
        assert kwargs['temperature']==0.0
        return {'text':text}
    monkeypatch.setitem(sys.modules,'mlx_whisper',types.SimpleNamespace(transcribe=transcribe))
    response=client.post('/api/search/voice',files={'file':('situation.wav',wav(),'audio/wav')},data={'language':language,'task':task})
    assert response.status_code==200,response.text
    assert response.json()['text']==text
    assert response.json()['output_language']==('en' if task=='translate' else language)
    assert not Path(paths[0]).exists()
    assert list((app.state.data/'audio').iterdir())==[]
    with app.state.Session() as s:assert s.scalar(select(Recording)) is None

def test_invalid_options_and_audio(setup):
    _,client=setup
    assert client.post('/api/search/voice',files={'file':('x.wav',wav())},data={'language':'fr'}).status_code==422
    assert client.post('/api/search/voice',files={'file':('x.wav',b'fake audio')}).status_code==422
    assert client.post('/api/search/voice',files={'file':('x.wav',b'x'*(10*1024*1024+1))}).status_code==413

def test_no_recognized_speech_and_missing_model(setup,monkeypatch):
    app,client=setup
    monkeypatch.setitem(sys.modules,'mlx_whisper',types.SimpleNamespace(transcribe=lambda *a,**k:{'text':''}))
    assert client.post('/api/search/voice',files={'file':('x.wav',wav())}).status_code==422
    monkeypatch.setattr('backend.app.platform.system',lambda:'Linux')
    assert client.post('/api/search/voice',files={'file':('x.wav',wav())}).status_code==503
    assert client.post('/api/search',json={'query':'patience'}).status_code==200

def test_inference_failure_not_retried(setup,monkeypatch):
    app,client=setup;calls=[]
    def fail(*a,**k):calls.append(1);raise RuntimeError('synthetic internal error')
    monkeypatch.setitem(sys.modules,'mlx_whisper',types.SimpleNamespace(transcribe=fail))
    for _ in range(2):
        response=client.post('/api/search/voice',files={'file':('x.wav',wav())})
        assert response.status_code==503 and 'synthetic internal error' not in response.text
    assert len(calls)==1

def test_translation_preserves_recognition_for_comparison(setup,monkeypatch):
    _,client=setup;tasks=[]
    def recognize(path,**kwargs):
        tasks.append(kwargs['task']);assert kwargs['temperature']==0.0
        # Explicitly mocked reported regression; not an accuracy measurement.
        return {'text':'ಮನೆಗೆ ಬಾ' if kwargs['task']=='transcribe' else 'Bye'}
    monkeypatch.setitem(sys.modules,'mlx_whisper',types.SimpleNamespace(transcribe=recognize))
    response=client.post('/api/search/voice',files={'file':('synthetic.wav',wav())},data={'language':'kn','task':'translate'})
    assert response.status_code==200
    assert response.json()['source_text']=='ಮನೆಗೆ ಬಾ'
    assert response.json()['text']=='Bye'
    assert 'change meaning' in response.json()['warning']
    assert tasks==['transcribe','translate']
