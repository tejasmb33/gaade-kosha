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

def test_dictionary_theme_filter_preserves_categories(tmp_path):
    app=create_app(tmp_path,'synthetic-token')
    with app.state.Session.begin() as session:
        for id,category in [('money-a','Money and moderation'),('money-b','Greed'),('work-a','Work and agriculture'),('other','Synthetic')]:
            session.add(Proverb(id=id,proverb_kn='ಪರೀಕ್ಷೆ '+id,category=category,literal_meaning='Synthetic literal',contextual_meaning='Synthetic context',verification_status=APPROVED))
        session.add(Proverb(id='pending-money',proverb_kn='ಗೋಪ್ಯ ಪರೀಕ್ಷೆ',category='Greed',literal_meaning='Synthetic literal',contextual_meaning='Synthetic context',verification_status='PENDING_VERIFICATION'))
    client=TestClient(app)
    result=client.get('/api/proverbs',params={'theme':'money','page_size':1}).json()
    assert result['total']==2 and len(result['items'])==1
    narrowed=client.get('/api/proverbs',params={'theme':'money','category':'Greed'}).json()
    assert [row['id'] for row in narrowed['items']]==['money-b']
    assert narrowed['items'][0]['category']=='Greed'
    assert client.get('/api/proverbs',params={'theme':'work','category':'Greed'}).json()['total']==0
    assert client.get('/api/proverbs',params={'theme':'invalid'}).status_code==422
    assert 'Greed' in client.get('/api/categories').json()

def test_situation_pairs_only_for_unchanged_approved_records(tmp_path,monkeypatch):
    from backend import dictionary_situations
    app=create_app(tmp_path,'synthetic-token')
    examples=[{'id':'synthetic-1','text':'Synthetic situation one','language':'en','status':'DRAFT_REQUIRES_NATIVE_SPEAKER_REVIEW'},{'id':'synthetic-2','text':'Synthetic situation two','language':'en','status':'DRAFT_REQUIRES_NATIVE_SPEAKER_REVIEW'}]
    with app.state.Session.begin() as session:
        for id,status in [('synthetic',APPROVED),('hidden','PENDING_VERIFICATION')]:
            session.add(Proverb(id=id,proverb_kn='ಪರೀಕ್ಷೆ',literal_meaning='Synthetic literal',contextual_meaning='Synthetic context',example_usage='Synthetic example',verification_status=status))
    record={'proverb_kn':'ಪರೀಕ್ಷೆ','contextual_meaning':'Synthetic context','example_usage':'Synthetic example','items':examples}
    monkeypatch.setattr(dictionary_situations,'BUNDLE',{'synthetic':record,'hidden':record})
    client=TestClient(app)
    assert client.get('/api/proverbs/synthetic').json()['situations']==examples
    assert client.get('/api/proverbs/hidden').status_code==404
    with app.state.Session.begin() as session:session.get(Proverb,'synthetic').contextual_meaning='Changed synthetic meaning'
    assert client.get('/api/proverbs/synthetic').json()['situations']==[]
