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
