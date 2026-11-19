"""Saved-example behavior with isolated, explicitly synthetic records only."""
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app,Proverb,APPROVED
from backend import recommended_situations as recommendations
from backend.cloud_search import CloudUnavailable

@pytest.fixture
def examples(tmp_path,monkeypatch):
    items=[{'gaade_id':f'synthetic-{i}','proverb_kn':f'ಕೃತಕ ಪರೀಕ್ಷೆ {i}',
        'contextual_meaning':f'Synthetic meaning {i}','situation_kn':f'ಕೃತಕ ಸಂದರ್ಭ {i}.',
        'situation_en':f'Synthetic example situation {i}.'} for i in range(3)]
    monkeypatch.setattr(recommendations,'EXAMPLES',items)
    for key in ['GEMINI_API_KEY','GROQ_API_KEY','OPENAI_API_KEY','GAADE_AI_PROVIDER','GAADE_AI_MODEL']:monkeypatch.delenv(key,raising=False)
    app=create_app(tmp_path/'data','synthetic-test-token')
    with app.state.Session.begin() as s:
        for item in items:s.add(Proverb(id=item['gaade_id'],proverb_kn=item['proverb_kn'],literal_meaning='Synthetic literal',contextual_meaning=item['contextual_meaning'],verification_status=APPROVED))
    return app,TestClient(app),items


def test_all_three_saved_examples_work_without_keys_or_external_calls(examples,monkeypatch):
    _,client,items=examples
    def forbidden(*args,**kwargs):raise AssertionError('A cached example must not construct a cloud provider')
    monkeypatch.setattr('backend.app.CloudSearch',forbidden)
    for item in items:
        for field in ['situation_kn','situation_en']:
            for provider in ['gemini','groq']:
                result=client.post('/api/search/ai',json={'query':item[field],'provider':provider})
                assert result.status_code==200,result.text
                data=result.json();assert data['mode']=='cached' and data['cache_hit'] is True
                assert [row['id'] for row in data['items']]==[item['gaade_id']]
                assert data['items'][0]['proverb_kn']==item['proverb_kn']
                assert data['items'][0]['contextual_meaning']==item['contextual_meaning']
                assert 'display' in data['items'][0] and 'reading_audio' in data['items'][0]
                assert data['external_sources']==[] and data['interpretation'] is None
            assert client.post('/api/search',json={'query':item[field]}).json()['items'][0]['id']==item['gaade_id']


@pytest.mark.parametrize('change',['pending','rejected','deleted','wording','meaning'])
def test_cache_does_not_bypass_approval_or_attach_stale_details(examples,monkeypatch,change):
    app,client,items=examples;item=items[0]
    with app.state.Session.begin() as s:
        row=s.get(Proverb,item['gaade_id'])
        if change=='pending':row.verification_status='PENDING_VERIFICATION'
        elif change=='rejected':row.verification_status='REJECTED'
        elif change=='deleted':s.delete(row)
        elif change=='wording':row.proverb_kn='ಬದಲಾದ ಕೃತಕ ಪರೀಕ್ಷೆ'
        else:row.contextual_meaning='Changed synthetic meaning'
    def unavailable(*args,**kwargs):raise CloudUnavailable('Synthetic missing config')
    monkeypatch.setattr('backend.app.CloudSearch',unavailable)
    result=client.post('/api/search/ai',json={'query':item['situation_en'],'provider':'gemini'})
    assert result.status_code==503
    result=client.post('/api/search',json={'query':item['situation_en']}).json()
    assert result['mode']!='cached'
    if change in ['pending','rejected','deleted']:assert item['gaade_id'] not in [row['id'] for row in result['items']]


def test_saved_examples_require_the_whole_situation(examples):
    _,_,items=examples
    assert recommendations.find_example('  SYNTHETIC example  situation 0 ! ')==items[0]
    assert recommendations.find_example('Synthetic example situation 0 but the outcome is different') is None
    assert recommendations.find_example('Synthetic example') is None
    assert recommendations.find_example('') is None
