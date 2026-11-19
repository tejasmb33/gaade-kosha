"""Authored example pairs, kept separate from approved cultural metadata."""
import json
from pathlib import Path
BUNDLE=json.loads((Path(__file__).resolve().parents[1]/'deployment/dictionary-situations.json').read_text())
def situations_for(row):
    record=BUNDLE.get(row.id,{})
    # Never attach an old example pair to an edited or unrelated proverb.
    if any(record.get(key)!=getattr(row,key) for key in ['proverb_kn','contextual_meaning','example_usage']):return []
    return record.get('items',[])
