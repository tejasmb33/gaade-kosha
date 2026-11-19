"""Fingerprint-checked bilingual presentation drafts; originals stay unchanged."""
import hashlib,json
from pathlib import Path
from .bundled_bilingual import BUNDLE
from .dictionary_translations import fingerprint
from .dictionary_situations import situations_for

def display_hash(row):
    return hashlib.sha256((fingerprint(row)+json.dumps(situations_for(row),ensure_ascii=False,sort_keys=True)).encode()).hexdigest()
def load_display(data,row):
    candidates=[]
    try:candidates.append(json.loads((Path(data)/'bilingual-display'/(row.id+'.json')).read_text()))
    except (OSError,ValueError):pass
    candidates.append(BUNDLE.get(row.id,{}).get('display'))
    for result in candidates:
        if isinstance(result,dict) and result.get('input_hash')==display_hash(row) and result.get('status')=='MACHINE_TRANSLATION_DRAFT' and isinstance(result.get('fields'),dict):return result['fields']
    return None
