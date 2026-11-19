"""Bilingual display contracts use synthetic records; no live providers."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.app import create_app,Proverb,APPROVED
from backend.bilingual_display import display_hash
from fastapi.testclient import TestClient

def test_display_cache_in_detail_and_search_but_not_private_records(tmp_path):
    app=create_app(tmp_path,'synthetic-token')
    with app.state.Session.begin() as session:
        row=Proverb(id='synthetic',proverb_kn='ಕೃತಕ ಪರೀಕ್ಷೆ',literal_meaning='Synthetic literal',contextual_meaning='Draft: Synthetic meaning',example_usage='Synthetic example',verification_status=APPROVED)
        session.add(row);session.flush();digest=display_hash(row)
        session.add(Proverb(id='hidden',proverb_kn='ಗೋಪ್ಯ ಪರೀಕ್ಷೆ',literal_meaning='Synthetic literal',contextual_meaning='Synthetic private',verification_status='PENDING_VERIFICATION'))
    folder=tmp_path/'bilingual-display';folder.mkdir()
    fields={'proverb_en':'Synthetic rendering','contextual_meaning_kn':'ಕರಡು: ಕೃತಕ ಅರ್ಥ','example':{'kn':'ಕೃತಕ ಉದಾಹರಣೆ','en':'Synthetic example'},'situations':[{'kn':'ಕೃತಕ ಸಂದರ್ಭ ಒಂದು','en':'Synthetic situation one'},{'kn':'ಕೃತಕ ಸಂದರ್ಭ ಎರಡು','en':'Synthetic situation two'}]}
    payload={'input_hash':digest,'status':'MACHINE_TRANSLATION_DRAFT','fields':fields}
    (folder/'synthetic.json').write_text(json.dumps(payload));(folder/'hidden.json').write_text(json.dumps(payload))
    client=TestClient(app)
    assert client.get('/api/proverbs/synthetic').json()['display']==fields
    assert client.post('/api/search',json={'query':'ಕೃತಕ ಪರೀಕ್ಷೆ'}).json()['items'][0]['display']==fields
    assert client.get('/api/proverbs/hidden').status_code==404
    with app.state.Session.begin() as session:session.get(Proverb,'synthetic').contextual_meaning='Edited synthetic meaning'
    assert client.get('/api/proverbs/synthetic').json()['display'] is None
