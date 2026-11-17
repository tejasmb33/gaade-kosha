#!/usr/bin/env python3
"""Validate a complete UTF-8 JSONL file and import as pending; never publish."""
import argparse, json, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app import Contribution, Proverb, create_app

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('file',type=Path); p.add_argument('--data-dir',type=Path)
    args=p.parse_args(); rows=[]; errors=[]
    for line_number,line in enumerate(args.file.read_text(encoding='utf-8').splitlines(),1):
        if not line.strip(): continue
        try:
            raw=json.loads(line)
            if raw.get('audio_id'): raise ValueError('Imports cannot attach audio')
            rows.append(Contribution.model_validate(raw))
        except Exception as e: errors.append(f'Line {line_number}: {e}')
    if errors: print('\n'.join(errors),file=sys.stderr); return 1
    if not rows: print('No records; nothing imported',file=sys.stderr); return 1
    app=create_app(args.data_dir)
    with app.state.Session.begin() as s:
        for row in rows: s.add(Proverb(**row.model_dump(exclude={'audio_id'})))
    print(f'Imported {len(rows)} pending records. Human source verification and review required.'); return 0
if __name__=='__main__': sys.exit(main())
