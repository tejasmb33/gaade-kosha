#!/usr/bin/env python3
"""Export existing bilingual situation drafts; never calls a provider or changes records."""
import csv,json,sys,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.dev import load_env
os.chdir(ROOT)
env=load_env(ROOT/'.env')
if env.get('GAADE_DATA_DIR'):os.environ['GAADE_DATA_DIR']=env['GAADE_DATA_DIR']
from backend.app import create_app,Proverb,APPROVED
from backend.bilingual_display import load_display
from sqlalchemy import select
app=create_app();output=[];missing=[]
with app.state.Session() as session:
    for row in session.scalars(select(Proverb).where(Proverb.verification_status==APPROVED).order_by(Proverb.id)):
        data=load_display(app.state.data,row)
        if not data:missing.append(row.id);continue
        for i,pair in enumerate(data['situations'],1):
            output.append({'situation_id':row.id+'-'+str(i),'gaade_id':row.id,'proverb_kn':row.proverb_kn,'situation_kn':pair['kn'],'situation_en':pair['en'],'synthetic':True,'review_status':'MACHINE_TRANSLATION_DRAFT','proverb_source':row.source})
if missing:print(f'Export stopped: {len(missing)} approved records lack complete displays. Existing exports preserved.');sys.exit(1)
folder=ROOT/'datasets';p=folder/'situations-bilingual.jsonl'
p.write_text(''.join(json.dumps(item,ensure_ascii=False)+'\n' for item in output))
with p.with_suffix('.csv').open('w',encoding='utf-8-sig',newline='') as stream:
    writer=csv.DictWriter(stream,fieldnames=list(output[0]));writer.writeheader();writer.writerows(output)
print(f'Exported {len(output)} bilingual situation drafts for {len(output)//2} approved proverbs.')
