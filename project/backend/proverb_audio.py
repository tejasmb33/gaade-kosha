"""Explicitly published proverb audio; private contribution recordings stay separate."""
import json,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
AUDIO_ROOT=ROOT/'datasets/submission/audio'
try:MANIFEST=json.loads((ROOT/'deployment/proverb-audio.json').read_text())
except (OSError,ValueError):MANIFEST={}

def normalize(value):
    return ''.join(ch for ch in unicodedata.normalize('NFC',value).replace('\u200c','').replace('\u200d','') if unicodedata.category(ch)[0] in 'LNM')

def audio_path(row):
    item=MANIFEST.get(row.id)
    if not item or row.verification_status!='APPROVED' or item.get('proverb_kn')!=row.proverb_kn:return None
    filename=item.get('filename','')
    if not filename or Path(filename).name!=filename or Path(filename).suffix.lower()!='.mp3':return None
    path=(AUDIO_ROOT/filename).resolve()
    if not path.is_file() and AUDIO_ROOT.is_dir():
        matches=[p.resolve() for p in AUDIO_ROOT.iterdir() if unicodedata.normalize('NFC',p.name)==unicodedata.normalize('NFC',filename)]
        if len(matches)==1:path=matches[0]
    if path.parent!=AUDIO_ROOT.resolve() or not path.is_file():return None
    return path

def audio_metadata(row):
    if not audio_path(row):return None
    return {'url':'/api/proverbs/'+row.id+'/audio','media_type':'audio/mpeg','duration_seconds':MANIFEST[row.id]['duration_seconds']}
