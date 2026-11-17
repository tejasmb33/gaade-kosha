"""Bilingual dictionary cache tests; synthetic fixtures only, no provider calls."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.app import create_app,Proverb,APPROVED
from backend.dictionary_translations import fingerprint
from fastapi.testclient import TestClient

def test_bilingual_cache_search_and_invalidation(tmp_path):
    app=create_app(tmp_path,'synthetic-token')
    with app.state.Session.begin() as s:
        row=Proverb(id='synthetic',proverb_kn='ಪರೀಕ್ಷೆ',literal_meaning='Synthetic literal',contextual_meaning='Synthetic context',example_usage='Synthetic example',keywords='fixture',category='Synthetic')
        row.verification_status=APPROVED;s.add(row);s.flush();hash=fingerprint(row)
        private=Proverb(id='private',proverb_kn='ಗೋಪ್ಯ ಪರೀಕ್ಷೆ',literal_meaning='Private synthetic',contextual_meaning='Private synthetic',verification_status='PENDING_VERIFICATION');s.add(private)
    folder=tmp_path/'translations';folder.mkdir()
    fields={'proverb_en':'Synthetic test','literal_meaning_kn':'ಪರೀಕ್ಷೆಯ ಪದಶಃ ಅರ್ಥ','contextual_meaning_kn':'ಪರೀಕ್ಷೆಯ ವಿವರಣೆ','category_kn':'ಪರೀಕ್ಷೆ'}
    (folder/'synthetic.json').write_text(json.dumps({'status':'MACHINE_TRANSLATION_DRAFT','input_hash':hash,'fields':fields}))
    client=TestClient(app)
    assert client.get('/api/proverbs/synthetic').json()['translation']['fields']==fields
    assert client.get('/api/proverbs',params={'q':'ವಿವರಣೆ'}).json()['total']==1
    assert client.get('/api/categories').json()==['Synthetic']
    assert client.get('/api/categories?bilingual=true').json()==[{'value':'Synthetic','label_kn':'ಪರೀಕ್ಷೆ'}]
    assert client.get('/api/proverbs/private').status_code==404
    with app.state.Session.begin() as s:s.get(Proverb,'synthetic').contextual_meaning='Edited synthetic meaning'
    assert client.get('/api/proverbs/synthetic').json()['translation'] is None
    assert client.get('/api/proverbs',params={'q':'ವಿವರಣೆ'}).json()['total']==0
    assert client.get('/api/proverbs/synthetic').json()['literal_meaning']=='Synthetic literal'
