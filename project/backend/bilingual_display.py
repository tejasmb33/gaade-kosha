"""Fingerprint-checked bilingual presentation drafts; originals stay unchanged."""
import hashlib,json
from pathlib import Path
from .dictionary_translations import fingerprint
from .dictionary_situations import situations_for

def display_hash(row):
    return hashlib.sha256((fingerprint(row)+json.dumps(situations_for(row),ensure_ascii=False,sort_keys=True)).encode()).hexdigest()
def load_display(data,row):
    try:
        result=json.loads((Path(data)/'bilingual-display'/(row.id+'.json')).read_text())
        if result.get('input_hash')==display_hash(row) and result.get('status')=='MACHINE_TRANSLATION_DRAFT':return result['fields']
    except (OSError,ValueError,KeyError):pass
    return None
