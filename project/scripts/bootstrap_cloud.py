#!/usr/bin/env python3
"""Seed an empty cloud database with approved records; never overwrites live data."""
import json,os,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def seed(application,bundle):
    from sqlalchemy import select,text
    from backend.app import Proverb,APPROVED,index_record
    with application.state.Session.begin() as session:
        if session.bind.dialect.name=='postgresql':session.execute(text("SELECT pg_advisory_xact_lock(74623321)"))
        if session.scalar(select(Proverb.id).limit(1)) is not None:return 0
        for item in bundle:
            record=item['record']
            if record['verification_status']!=APPROVED:raise ValueError('Seed may contain approved records only')
            row=Proverb(**record);session.add(row);session.flush();index_record(session,row)
            translation=item.get('translation')
            if translation and session.bind.dialect.name=='postgresql':
                session.execute(text('INSERT INTO dictionary_translations(id,payload) VALUES (:id,:payload)'),{'id':row.id,'payload':json.dumps(translation,ensure_ascii=False)})
        return len(bundle)


def main():
    if not os.getenv('DATABASE_URL'):raise ValueError('DATABASE_URL must be set before cloud startup')
    from backend.object_store import ObjectStore
    ObjectStore().ensure_bucket()
    if os.getenv('GAADE_SPEECH_PROVIDER')!='groq' or not os.getenv('GROQ_API_KEY'):raise ValueError('Groq speech must be configured')
    from backend.app import app
    bundle=json.loads((Path(__file__).resolve().parents[1]/'deployment/approved-seed.json').read_text())
    count=seed(app,bundle)
    print(f'Cloud seed: {count} approved records added; existing databases are preserved.')


if __name__=='__main__':
    try:main()
    except Exception:print('Cloud initialization failed. Check backend database configuration; existing records were not overwritten.',file=sys.stderr);sys.exit(1)
