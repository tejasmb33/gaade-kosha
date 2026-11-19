"""Public supplied-audio boundary tests; synthetic files only, no user recordings."""
from fastapi.testclient import TestClient
from backend.app import create_app,Proverb,APPROVED
from backend import proverb_audio

def test_audio_matches_approved_record_and_supports_byte_ranges(tmp_path,monkeypatch):
    folder=tmp_path/'published';folder.mkdir();content=b'ID3'+b'synthetic-audio-fixture'*20;(folder/'synthetic.mp3').write_bytes(content)
    manifest={id:{'filename':'synthetic.mp3','proverb_kn':'ಕೃತಕ ಪರೀಕ್ಷೆ','duration_seconds':1} for id in ['synthetic','pending']}
    monkeypatch.setattr(proverb_audio,'AUDIO_ROOT',folder);monkeypatch.setattr(proverb_audio,'MANIFEST',manifest)
    app=create_app(tmp_path/'data','synthetic-token')
    with app.state.Session.begin() as session:
        for id,status in [('synthetic',APPROVED),('pending','PENDING_VERIFICATION'),('no-audio',APPROVED)]:
            session.add(Proverb(id=id,proverb_kn='ಕೃತಕ ಪರೀಕ್ಷೆ',literal_meaning='Synthetic',contextual_meaning='Synthetic',verification_status=status))
    client=TestClient(app)
    detail=client.get('/api/proverbs/synthetic').json();assert detail['reading_audio']['url']=='/api/proverbs/synthetic/audio'
    assert any(row['reading_audio'] for row in client.get('/api/proverbs').json()['items'])
    result=client.get('/api/proverbs/synthetic/audio');assert result.status_code==200 and result.content==content and result.headers['content-type']=='audio/mpeg'
    result=client.get('/api/proverbs/synthetic/audio',headers={'Range':'bytes=0-9'});assert result.status_code==206 and result.content==content[:10]
    assert client.get('/api/proverbs/pending/audio').status_code==404
    assert client.get('/api/proverbs/no-audio/audio').status_code==404
    assert client.get('/api/proverbs/missing/audio').status_code==404
    with app.state.Session.begin() as session:session.get(Proverb,'synthetic').proverb_kn='ಬದಲಾದ ಕೃತಕ ಪರೀಕ್ಷೆ'
    assert client.get('/api/proverbs/synthetic').json()['reading_audio'] is None
    assert client.get('/api/proverbs/synthetic/audio').status_code==404

def test_manifest_cannot_escape_audio_directory(tmp_path,monkeypatch):
    folder=tmp_path/'public';folder.mkdir();private=tmp_path/'private.mp3';private.write_bytes(b'synthetic private fixture')
    row=type('Row',(),{'id':'synthetic','proverb_kn':'ಕೃತಕ ಪರೀಕ್ಷೆ','verification_status':APPROVED})()
    monkeypatch.setattr(proverb_audio,'AUDIO_ROOT',folder)
    monkeypatch.setattr(proverb_audio,'MANIFEST',{'synthetic':{'filename':'../private.mp3','proverb_kn':row.proverb_kn,'duration_seconds':1}})
    assert proverb_audio.audio_path(row) is None
    (folder/'link.mp3').symlink_to(private)
    proverb_audio.MANIFEST['synthetic']['filename']='link.mp3'
    assert proverb_audio.audio_path(row) is None


def test_audio_first_order_applies_before_pagination_and_with_filters(tmp_path,monkeypatch):
    folder=tmp_path/'published';folder.mkdir();(folder/'synthetic.mp3').write_bytes(b'ID3 synthetic fixture')
    # Synthetic corpus: 50 audio entries alphabetically after 150 entries without audio.
    manifest={f'audio-{i}':{'filename':'synthetic.mp3','proverb_kn':f'ಕೃತಕ ಧ್ವನಿ {i:03}','duration_seconds':1} for i in range(50)}
    monkeypatch.setattr(proverb_audio,'AUDIO_ROOT',folder);monkeypatch.setattr(proverb_audio,'MANIFEST',manifest)
    app=create_app(tmp_path/'data','synthetic-token')
    with app.state.Session.begin() as session:
        for i in range(200):
            id=f'audio-{i}' if i<50 else f'text-{i}'
            word=manifest[id]['proverb_kn'] if i<50 else f'ಅ ಕೃತಕ ಪಠ್ಯ {i:03}'
            session.add(Proverb(id=id,proverb_kn=word,literal_meaning='Synthetic',contextual_meaning='Synthetic',category='Synthetic audio' if i<50 else 'Synthetic text',verification_status=APPROVED))
    client=TestClient(app)
    rows=[]
    for page in range(1,18):
        result=client.get('/api/proverbs',params={'sort':'audio_first','page':page,'page_size':12}).json()
        assert result['total']==200
        rows.extend(result['items'])
    assert len(rows)==len({row['id'] for row in rows})==200
    assert {row['id'] for row in rows[:50]}==set(manifest)
    assert all(row['reading_audio'] for row in rows[:50])
    assert all(row['reading_audio'] is None for row in rows[50:])
    assert [row['proverb_kn'] for row in rows[:50]]==sorted(row['proverb_kn'] for row in rows[:50])
    filtered=client.get('/api/proverbs',params={'sort':'audio_first','category':'Synthetic text','page_size':50}).json()
    assert filtered['total']==150 and all(row['reading_audio'] is None for row in filtered['items'])
    assert client.get('/api/proverbs',params={'sort':'alphabetical'}).json()['items'][0]['reading_audio'] is None
