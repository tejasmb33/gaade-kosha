#!/usr/bin/env python3
"""Offline model smoke checks. Synthetic text/silence are NOT cultural or speech quality tests."""
import argparse, importlib, json, os, sys, tempfile, wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
os.environ['HF_HUB_OFFLINE']='1'
os.environ['TRANSFORMERS_OFFLINE']='1'
os.environ['TOKENIZERS_PARALLELISM']='false'
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--speech-sample',type=Path);args=p.parse_args()
    from scripts.dev import load_env
    config=load_env(ROOT/'.env')
    for key in ['E5_MODEL_PATH','WHISPER_MODEL_PATH']:
        if not config.get(key): raise ValueError(f'{key} is not configured')
        os.environ[key]=str((ROOT/config[key]).resolve())
    import numpy as np
    from backend.app import Semantic,Proverb,create_app
    from fastapi.testclient import TestClient
    with tempfile.TemporaryDirectory(prefix='gaade-model-check-') as temp:
        cache=Path(temp)/'embeddings';cache.mkdir()
        semantic=Semantic(os.environ['E5_MODEL_PATH'],cache)
        semantic.load()
        if semantic.model is None: raise RuntimeError(semantic.error)
        vec=semantic.model.encode(['query: ಸಹನೆ','query: patience'],normalize_embeddings=True)
        assert vec.shape==(2,384) and np.allclose(np.linalg.norm(vec,axis=1),1,atol=1e-5)
        # Explicitly synthetic metadata, never written into the public collection.
        row=Proverb(id='synthetic-model-fixture',proverb_kn='ಪರೀಕ್ಷೆ',transliteration='',literal_meaning='Synthetic test fixture',contextual_meaning='patience and waiting',example_usage='',category='synthetic',keywords='patience',region='',dialect='',source='',contributor='')
        first=semantic.scores('patience',[row])
        assert row.id in first and len(list(cache.glob('*.npy')))==1
        cached=next(cache.glob('*.npy')); stamp=cached.stat().st_mtime_ns
        second=semantic.scores('patience',[row])
        assert first==second and cached.stat().st_mtime_ns==stamp
        row.contextual_meaning='Changed synthetic fixture content'
        assert row.id in semantic.scores('patience',[row]) and len(list(cache.glob('*.npy')))==2
        print('PASS: E5 local Kannada/English encoding, 384 dimensions, normalization, cache reuse and content invalidation',flush=True)
        app=create_app(Path(temp)/'api',admin_token='synthetic-only-token')
        app.state.semantic.model=semantic.model
        client=TestClient(app)
        result=client.post('/api/search',json={'query':'patience'})
        assert result.status_code==200 and result.json()['items']==[]
        print('PASS: empty reviewed collection stays empty with real E5 loaded',flush=True)
        import mlx.core as mx
        from mlx_whisper.transcribe import ModelHolder
        model=ModelHolder.get_model(os.environ['WHISPER_MODEL_PATH'],mx.float16)
        mx.eval(model.parameters())
        print('PASS: Whisper local MLX weights loaded on '+str(mx.default_device()),flush=True)
        audio=args.speech_sample
        if not audio:
            audio=Path(temp)/'synthetic-silence.wav'
            with wave.open(str(audio),'wb') as out:
                out.setnchannels(1);out.setsampwidth(2);out.setframerate(16000);out.writeframes(b'\0\0'*16000)
        import mlx_whisper
        result=mlx_whisper.transcribe(str(audio),path_or_hf_repo=os.environ['WHISPER_MODEL_PATH'],language='kn',verbose=False,condition_on_previous_text=False)
        assert isinstance(result.get('text'),str)
        uploaded=client.post('/api/audio/upload',files={'file':('sample.wav',audio.read_bytes(),'audio/wav')})
        assert uploaded.status_code==201 or uploaded.status_code==200, uploaded.text
        audio_id=uploaded.json()['audio_id']
        transcript=client.post('/api/audio/transcribe',json={'audio_id':audio_id})
        assert transcript.status_code==200,transcript.text
        body={'proverb_kn':'ಪರೀಕ್ಷೆ','literal_meaning':'Synthetic workflow fixture only','contextual_meaning':'Synthetic workflow fixture only','audio_id':audio_id}
        submitted=client.post('/api/contributions',json=body)
        assert submitted.status_code==201,submitted.text
        assert client.post('/api/audio/transcribe',json={'audio_id':audio_id}).status_code==409
        assert client.get('/api/admin/audio/'+audio_id).status_code==401
        retained=client.get('/api/admin/audio/'+audio_id,headers={'X-Admin-Token':'synthetic-only-token'})
        assert retained.status_code==200 and retained.content==audio.read_bytes()
        queue=client.get('/api/admin/contributions',headers={'X-Admin-Token':'synthetic-only-token'}).json()
        assert queue[0]['recording']['corrected_transcript']=='ಪರೀಕ್ಷೆ'
        assert queue[0]['recording']['original_transcript']==transcript.json()['text']
        assert client.get('/api/proverbs').json()['total']==0
        print('PASS: real local speech API, original retention, private pending submission and retranscription protection',flush=True)
        retained_count=len(list((app.state.data/'audio').iterdir()))
        for language,task in [('kn','transcribe'),('en','transcribe'),('kn','translate')]:
            response=client.post('/api/search/voice',files={'file':('situation.wav',audio.read_bytes(),'audio/wav')},data={'language':language,'task':task})
            assert response.status_code in [200,422],response.text
            assert len(list((app.state.data/'audio').iterdir()))==retained_count
        print('PASS: ephemeral situation speech API executed with real local Whisper for Kannada, English and speech-to-English translation; silence is not an accuracy test',flush=True)


        if args.speech_sample:
            print('Kannada sample transcript (requires human accuracy review): '+result['text'])
        else:
            print('PASS: Kannada-language MLX transcription execution on synthetic silence. Real Kannada speech accuracy remains UNVALIDATED.')
    print('All offline model smoke checks passed. No public records were added.')
if __name__=='__main__': main()
