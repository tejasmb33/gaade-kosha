"""Versioned dictionary translation drafts. Never modifies approved source records."""
import hashlib,json
from pathlib import Path
FIELDS=['proverb_kn','literal_meaning','contextual_meaning','example_usage','category','keywords','region','dialect','source','contributor']
def fingerprint(row):
    return hashlib.sha256(json.dumps({k:getattr(row,k) for k in FIELDS},ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def load_translation(data,row):
    path=Path(data)/'translations'/(row.id+'.json')
    try:
        result=json.loads(path.read_text())
        if result.get('input_hash')==fingerprint(row) and result.get('status')=='MACHINE_TRANSLATION_DRAFT':return result
    except (OSError,ValueError):pass
    return None
