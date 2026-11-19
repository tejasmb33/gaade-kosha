"""Versioned dictionary translation drafts. Never modifies approved source records."""
import hashlib,json
from pathlib import Path
from .bundled_bilingual import BUNDLE
FIELDS=['proverb_kn','literal_meaning','contextual_meaning','example_usage','category','keywords','region','dialect','source','contributor']
def fingerprint(row):
    return hashlib.sha256(json.dumps({k:getattr(row,k) for k in FIELDS},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def load_translation(data,row):
    path=Path(data)/'translations'/(row.id+'.json')
    candidates=[]
    try:candidates.append(json.loads(path.read_text()))
    except (OSError,ValueError):pass
    candidates.append(BUNDLE.get(row.id,{}).get('translation'))
    for result in candidates:
        if isinstance(result,dict) and result.get('input_hash')==fingerprint(row) and result.get('status')=='MACHINE_TRANSLATION_DRAFT' and isinstance(result.get('fields'),dict):return result
    return None
