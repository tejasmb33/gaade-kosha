"""Ranking regressions using synthetic fixtures; not traditional proverb quality tests."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.app import create_app,Proverb,index_record,APPROVED,query_terms,semantic_passage
from fastapi.testclient import TestClient

def setup(tmp_path):
    app=create_app(tmp_path,'synthetic-token')
    with app.state.Session.begin() as s:
        for id,meaning,keywords,status in [('target','Keep expenses within your income','money budget',APPROVED),('noise','Someone for a person is a thing','for someone person',APPROVED),('private','Keep expenses within your income','money budget','PENDING_VERIFICATION')]:
            row=Proverb(id=id,proverb_kn='ಪರೀಕ್ಷೆ '+id,literal_meaning='Synthetic fixture only',contextual_meaning=meaning,example_usage='',category='',keywords=keywords,transliteration='',verification_status=status)
            s.add(row);s.flush();index_record(s,row)
    return app,TestClient(app)

def test_common_words_do_not_rank_noise(tmp_path):
    app,client=setup(tmp_path)
    app.state.semantic.scores=lambda q,rows:{r.id:(.815 if r.id=='target' else .77) for r in rows}
    data=client.post('/api/search',json={'query':'I spend more than I earn'}).json()
    assert data['mode']=='hybrid'
    assert [r['id'] for r in data['items']]==['target']

def test_weak_ambiguous_candidates_abstain(tmp_path):
    app,client=setup(tmp_path)
    app.state.semantic.scores=lambda q,rows:{'target':.805,'noise':.804}
    assert client.post('/api/search',json={'query':'random meaningless situation'}).json()['items']==[]

def test_no_pending_records_passed_to_model(tmp_path):
    app,client=setup(tmp_path)
    def scores(q,rows):
        assert {r.id for r in rows}=={'target','noise'}
        return {'target':.9,'noise':.75}
    app.state.semantic.scores=scores
    assert client.post('/api/search',json={'query':'A spending situation'}).json()['items'][0]['id']=='target'

def test_negation_preserved_and_editorial_label_excluded():
    assert 'not' in query_terms('I am not working hard')
    row=Proverb(contextual_meaning='Draft for human verification: Work carefully.',keywords='effort')
    assert semantic_passage(row)=='Work carefully. effort'
