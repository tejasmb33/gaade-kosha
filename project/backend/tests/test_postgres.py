"""Run against an isolated PostgreSQL service in CI, never the real Supabase DB."""
import os,uuid,json
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app,Proverb,APPROVED,index_record
from backend.dictionary_translations import fingerprint
from scripts.bootstrap_cloud import seed


@pytest.mark.skipif(not os.getenv('GAADE_TEST_POSTGRES_URL'),reason='Isolated PostgreSQL not configured')
def test_postgres_seed_search_review_and_translation_restart(tmp_path,monkeypatch):
    monkeypatch.setenv('GAADE_DATABASE_SSLMODE','disable')
    url=os.environ['GAADE_TEST_POSTGRES_URL']
    app=create_app(tmp_path/'first','synthetic-token',database_url=url)
    id=uuid.uuid4().hex
    record={'id':id,'proverb_kn':'ಪರೀಕ್ಷಾ ಗಾದೆ','literal_meaning':'Synthetic literal','contextual_meaning':'Synthetic patience context','category':'Synthetic','keywords':'patience','source':'https://example.org','verification_status':APPROVED}
    row=Proverb(**record)
    for field in ['transliteration','example_usage','region','dialect','contributor']:setattr(row,field,'')
    translation={'status':'MACHINE_TRANSLATION_DRAFT','input_hash':fingerprint(row),'fields':{'contextual_meaning_kn':'ಪರೀಕ್ಷಾ ವಿವರಣೆ'}}
    assert seed(app,[{'record':record,'translation':translation}])==1
    restarted=create_app(tmp_path/'restart','synthetic-token',database_url=url);client=TestClient(restarted)
    assert client.get('/api/proverbs/'+id).json()['translation']==translation
    assert client.post('/api/search',json={'query':'patience'}).json()['items'][0]['id']==id
    body={'proverb_kn':'ಹೊಸ ಪರೀಕ್ಷಾ ಗಾದೆ','literal_meaning':'Synthetic','contextual_meaning':'Synthetic','source':'https://example.org'}
    pending=client.post('/api/contributions',json=body).json()['id']
    assert client.get('/api/proverbs/'+pending).status_code==404
    assert client.patch('/api/admin/contributions/'+pending+'/approve',json=body).status_code==401
    assert client.patch('/api/admin/contributions/'+pending+'/approve',json=body,headers={'X-Admin-Token':'synthetic-token'}).status_code==200
    assert client.get('/api/proverbs/'+pending).status_code==200
