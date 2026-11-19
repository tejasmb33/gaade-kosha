"""Portable translation drafts for approved records, containing no private runtime data."""
import json
from pathlib import Path
try:
    BUNDLE=json.loads((Path(__file__).resolve().parents[1]/'deployment/bilingual-drafts.json').read_text())
    if not isinstance(BUNDLE,dict):BUNDLE={}
except (OSError,ValueError):BUNDLE={}
