#!/usr/bin/env python3
"""Copy local records/private audio to cloud without deleting or overwriting data.

Inspection is the default. --apply uses project/.env.cloud (ignored by Git).
The source SQLite database is opened read-only. No secrets are printed.
"""
import argparse,json,os,sqlite3,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.dev import load_env


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--source',default=str(ROOT/'data'))
    parser.add_argument('--config-file',default=str(ROOT/'.env.cloud'))
    args=parser.parse_args();source=Path(args.source).resolve()
    connection=sqlite3.connect('file:'+str(source/'gaade.db')+'?mode=ro',uri=True);connection.row_factory=sqlite3.Row
    records=[dict(row) for row in connection.execute('SELECT * FROM proverbs')]
    recordings=[dict(row) for row in connection.execute('SELECT * FROM recordings')];connection.close()
    print(f'Inspected {len(records)} records and {len(recordings)} private recordings. Originals remain unchanged.')
    if not args.apply:print('No upload performed. Configure .env.cloud, then use --apply.');return
    env=load_env(args.config_file)
    if not env.get('DATABASE_URL'):raise ValueError('Cloud database not configured')
    os.environ.update(env);os.environ['GAADE_DATA_DIR']=str(source/'migration-cache')
    from backend.app import app,Proverb,Recording,dump
    from backend.object_store import ObjectStore
    from backend.dictionary_translations import load_translation
    from sqlalchemy import text
    objects=ObjectStore();objects.ensure_bucket()
    # Check for conflicting IDs first; never silently replace remote edits.
    with app.state.Session.begin() as session:
        for model,rows in [(Proverb,records),(Recording,recordings)]:
            for values in rows:
                existing=session.get(model,values['id'])
                if existing and dump(existing)!=values:raise ValueError('Remote record differs; migration stopped for manual reconciliation')
        for values in recordings:
            filename=values['filename'];path=source/'audio'/filename
            if path.parent!=source/'audio' or not path.is_file():raise ValueError('Source recording missing')
            objects.upload('audio/'+filename,path)
        for values in records:
            row=session.get(Proverb,values['id'])
            if not row:row=Proverb(**values);session.add(row);session.flush()
            translation=load_translation(source,row)
            if translation:
                payload=json.dumps(translation,ensure_ascii=False)
                current=session.execute(text('SELECT payload FROM dictionary_translations WHERE id=:id'),{'id':row.id}).scalar()
                if current is None:session.execute(text('INSERT INTO dictionary_translations(id,payload) VALUES (:id,:payload)'),{'id':row.id,'payload':payload})
                elif json.loads(current)!=translation:raise ValueError('Remote translation differs; migration stopped')
        for values in recordings:
            if not session.get(Recording,values['id']):session.add(Recording(**values))
    for path in (source/'narrations').glob('*.wav'):
        objects.upload('narrations/'+path.name,path)
    print('Migration complete. IDs, approval states, private audio and narration caches preserved. Local originals remain unchanged.')


if __name__=='__main__':
    try:main()
    except Exception:print('Migration failed; source was not changed. Check cloud configuration, missing files, or conflicting remote records.',file=sys.stderr);sys.exit(1)
