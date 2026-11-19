"""Persistent selections for three owner-selected demonstration situations."""
import json,unicodedata
from pathlib import Path

try:
    EXAMPLES=json.loads((Path(__file__).resolve().parents[1]/'deployment/recommended-situations.json').read_text())
except (OSError,ValueError):EXAMPLES=[]

def normalized(value):
    # Normalize comparisons only; preserve the original Kannada text in the response.
    return ''.join(c for c in unicodedata.normalize('NFC',value).casefold() if unicodedata.category(c)[0] in 'LNM')

def find_example(query):
    key=normalized(query)
    return next((example for example in EXAMPLES if key and key in
        [normalized(example['situation_kn']),normalized(example['situation_en'])]),None)

def matches_record(example,row):
    return row is not None and row.verification_status=='APPROVED' and all(
        example.get(key)==getattr(row,key) for key in ['proverb_kn','contextual_meaning'])
