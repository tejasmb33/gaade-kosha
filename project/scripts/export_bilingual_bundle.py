#!/usr/bin/env python3
"""Package validated translation drafts for approved records; no keys, audio or pending data."""
import argparse,json,sqlite3,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.bilingual_display import display_hash
from backend.dictionary_translations import fingerprint

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--data-dir',type=Path,default=ROOT/'data');args=parser.parse_args();data=args.data_dir.resolve()
    with sqlite3.connect((data/'gaade.db').as_uri()+'?mode=ro',uri=True) as connection:
        connection.row_factory=sqlite3.Row
        rows=[SimpleNamespace(**dict(r)) for r in connection.execute("SELECT * FROM proverbs WHERE verification_status='APPROVED' ORDER BY id")]
    bundle={}
    for row in rows:
        display=json.loads((data/'bilingual-display'/(row.id+'.json')).read_text())
        translation=json.loads((data/'translations'/(row.id+'.json')).read_text())
        assert display['input_hash']==display_hash(row) and translation['input_hash']==fingerprint(row)
        assert display['status']==translation['status']=='MACHINE_TRANSLATION_DRAFT'
        assert len(display['fields']['situations'])==2
        # Explicit allowlist: no runtime configuration or contributor data is packaged.
        bundle[row.id]={'display':{k:display[k] for k in ['input_hash','status','fields']},'translation':{k:translation[k] for k in ['input_hash','status','fields']}}
    if not bundle:raise ValueError('No approved translation drafts')
    dest=ROOT/'deployment/bilingual-drafts.json';temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(bundle,ensure_ascii=False,indent=2)+'\n');temp.replace(dest)
    print(f'Packaged {len(bundle)} approved bilingual draft entries; database unchanged.')
if __name__=='__main__':main()
