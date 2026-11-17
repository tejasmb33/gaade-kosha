"""Local-model fallback/cache regressions. All records are synthetic fixtures."""
import importlib.util
import json
import sys
import types
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.app import Semantic,Proverb,create_app
from fastapi.testclient import TestClient

def fixture():
    return Proverb(id='synthetic',proverb_kn='ಪರೀಕ್ಷೆ',transliteration='',literal_meaning='Synthetic fixture only',contextual_meaning='patience',example_usage='',category='test',keywords='patience')
def test_failed_model_load_is_not_retried(tmp_path,monkeypatch):
    calls=[]
    def fail(*args,**kwargs): calls.append(kwargs);raise RuntimeError('synthetic load failure')
    monkeypatch.setitem(sys.modules,'sentence_transformers',types.SimpleNamespace(SentenceTransformer=fail))
    model=Semantic(str(tmp_path/'missing'),tmp_path)
    assert model.scores('patience',[fixture()])=={}
    assert model.scores('patience',[fixture()])=={}
    assert len(calls)==1
    assert calls[0]['local_files_only'] is True and calls[0]['trust_remote_code'] is False
    assert model.error

def test_prefixes_normalization_and_cache(tmp_path):
    model_path=tmp_path/'model';model_path.mkdir();(model_path/'revision.json').write_text('{"revision":"synthetic-revision"}')
    cache=tmp_path/'cache';cache.mkdir();calls=[]
    class Encoder:
        def encode(self,values,normalize_embeddings):
            assert normalize_embeddings
            calls.extend(values);return np.array([[1.,0.,0.] for _ in values])
    model=Semantic(str(model_path),cache);model.model=Encoder();row=fixture()
    assert model.scores('patience',[row])=={'synthetic':1.0}
    files=list(cache.glob('*.npy'));assert len(files)==1
    model.scores('patience',[row]);assert len([c for c in calls if c.startswith('passage: ')])==2
    assert calls[0]=='query: patience'
    row.contextual_meaning='changed synthetic content';model.scores('patience',[row]);assert len(list(cache.glob('*.npy')))==2
    row.example_usage='A new synthetic situation';model.scores('patience',[row]);assert len(list(cache.glob('*.npy')))==3

def test_missing_e5_keeps_keyword_search(tmp_path,monkeypatch):
    monkeypatch.setenv('E5_MODEL_PATH',str(tmp_path/'missing'))
    app=create_app(tmp_path/'data','test-token')
    app.state.semantic.error='Synthetic known model failure'
    with app.state.Session.begin() as s:
        from backend.app import APPROVED,index_record
        row=fixture();row.verification_status=APPROVED;s.add(row);s.flush();index_record(s,row)
    client=TestClient(app)
    result=client.post('/api/search',json={'query':'patience'}).json()
    assert result['mode']=='keyword' and result['items'][0]['id']=='synthetic'
    assert result['capability_notice']

def test_downloader_verifies_hash(tmp_path):
    spec=importlib.util.spec_from_file_location('models_download',Path(__file__).resolve().parents[2]/'scripts/download_models.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    import hashlib,pytest
    path=tmp_path/'weight';path.write_bytes(b'synthetic test weights')
    record={'size':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'git_oid':None}
    module.verify(path,record)
    path.write_bytes(b"corrupt")
    with pytest.raises(ValueError): module.verify(path,record)
