"""Editorial dictionary navigation groups; original record categories are untouched."""
import json
from pathlib import Path
THEMES=json.loads((Path(__file__).resolve().parents[1]/'deployment/dictionary-themes.json').read_text())
def theme_for(category):
    return next((theme['id'] for theme in THEMES if category in theme['categories']), 'character')
