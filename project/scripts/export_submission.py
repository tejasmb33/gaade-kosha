#!/usr/bin/env python3
"""Export approved local proverbs and linked bilingual situations; source DB is read-only."""
import argparse,csv,hashlib,io,json,re,sqlite3,sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.bilingual_display import load_display
from backend.dictionary_themes import theme_for

PREFIX=re.compile(r'^(?:(?:context(?:ual)?\s+)?draft(?:\s+for\s+human\s+verification)?|(?:for\s+)?human\s+verification|(?:ಮಾನವ|ಮನುಷ್ಯ)\s*ಪರಿಶೀಲನೆಗಾಗಿ(?:\s*(?:ಕರಡು|ಡ್ರಾಫ್ಟ್))?|(?:ಕರಡು|ಡ್ರಾಫ್ಟ್)(?:\s*(?:ಮಾನವ|ಮನುಷ್ಯ)\s*ಪರಿಶೀಲನೆಗಾಗಿ)?)\s*[:：.\-–—]\s*',re.I)
def clean(value):
    value=(value or '').strip()
    while PREFIX.match(value):value=PREFIX.sub('',value,count=1).strip()
    return value

def csv_bytes(rows):
    stream=io.StringIO(newline='');writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    return stream.getvalue().encode('utf-8-sig')

def export(data,output):
    with sqlite3.connect((data/'gaade.db').resolve().as_uri()+'?mode=ro',uri=True) as connection:
        connection.row_factory=sqlite3.Row
        rows=[SimpleNamespace(**dict(row)) for row in connection.execute("SELECT * FROM proverbs WHERE verification_status='APPROVED' ORDER BY proverb_kn,id")]
    if not rows:raise ValueError('No approved records to export')
    proverbs=[];situations=[];metadata=[]
    for row in rows:
        fields=load_display(data,row)
        if not fields or len(fields.get('situations',[]))!=2:raise ValueError('Missing complete bilingual display for '+row.id)
        proverbs.append({'gaade_id':row.id,'gaade':row.proverb_kn,'meaning':clean(fields['contextual_meaning_kn']),'English':clean(fields['proverb_en']),'example':clean(fields['example']['kn']),'region':row.region.strip(),'theme':theme_for(row.category)})
        metadata.append({'gaade_id':row.id,'source':row.source,'original_category':row.category,'region_status':'documented' if row.region.strip() else 'not_documented','record_status':row.verification_status,'meaning_translation_status':'MACHINE_TRANSLATION_DRAFT','english_equivalent_type':'English rendering; traditional idiom equivalence not established','example_type':'authored_illustration','independent_cultural_review':'not_established'})
        for i,pair in enumerate(fields['situations'],1):
            if not pair.get('kn') or not pair.get('en'):raise ValueError('Missing bilingual situation')
            situations.append({'situation_id':row.id+'-'+str(i),'gaade_id':row.id,'situation_kn':clean(pair['kn']),'situation_en':clean(pair['en']),'synthetic':'true','review_status':'MACHINE_TRANSLATION_DRAFT'})
    ids={row['gaade_id'] for row in proverbs}
    assert len(ids)==len(proverbs)
    assert all(row['gaade_id'] in ids for row in situations)
    assert len({row['situation_id'] for row in situations})==len(situations)
    assert Counter(row['gaade_id'] for row in situations)==Counter({id:2 for id in ids})
    assert all(row['theme'] in {'money','work','study','family','friends','character'} for row in proverbs)
    for row in proverbs:
        assert all(row[key] for key in ['gaade','meaning','English','example','theme'])
    files={'gaade.csv':csv_bytes(proverbs),'situations.csv':csv_bytes(situations),'metadata.csv':csv_bytes(metadata)}
    manifest={'exported_at_utc':datetime.now(timezone.utc).isoformat(),'approved_proverbs':len(proverbs),'situations':len(situations),'situations_per_proverb':2,'missing_documented_regions':sum(not row['region'] for row in proverbs),'themes':dict(Counter(row['theme'] for row in proverbs)),'encoding':'UTF-8 with BOM','sha256':{name:hashlib.sha256(content).hexdigest() for name,content in files.items()},'source_database_changed':False}
    files['validation.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode()
    output.mkdir(exist_ok=True,parents=True)
    for name,content in files.items():
        temporary=output/(name+'.tmp');temporary.write_bytes(content);temporary.replace(output/name)
    print(f'Exported {len(proverbs)} approved proverbs and {len(situations)} linked bilingual situations to {output}.')
    print(f"Documented region missing for {manifest['missing_documented_regions']} records; region cells left empty.")
    return manifest

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--data-dir',type=Path,default=ROOT/'data');parser.add_argument('--output',type=Path,default=ROOT/'datasets/submission');args=parser.parse_args()
    export(args.data_dir.resolve(),args.output.resolve())
if __name__=='__main__':main()
