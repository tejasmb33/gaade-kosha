#!/usr/bin/env python3
"""Inspect/sync approved local records to PostgreSQL without overwriting hosted records."""
import argparse,json,sqlite3,sys,unicodedata
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.dev import load_env
from backend.app import Proverb,APPROVED,dump
from backend.dictionary_translations import FIELDS,load_translation
from sqlalchemy import create_engine,select,text
from sqlalchemy.orm import Session

def normalized(value):return unicodedata.normalize('NFC',value).strip()
def plan_sync(session,records):
    remote={row.id:row for row in session.scalars(select(Proverb).with_for_update())}
    byword={normalized(row.proverb_kn):row.id for row in remote.values()}
    missing=[];existing=[];conflicts=[]
    for record in records:
        if record['verification_status']!=APPROVED:raise ValueError('Source contains non-approved records')
        row=remote.get(record['id'])
        if row:
            changed=[field for field in FIELDS+['verification_status'] if getattr(row,field)!=record[field]]
            if changed:conflicts.append({'id':row.id,'fields':changed})
            else:existing.append(row.id)
        elif normalized(record['proverb_kn']) in byword:
            conflicts.append({'id':record['id'],'fields':['duplicate_wording_with_different_id']})
        else:
            missing.append(record);byword[normalized(record['proverb_kn'])]=record['id']
    return remote,missing,existing,conflicts

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');parser.add_argument('--config-file',type=Path,default=ROOT/'.env.cloud');parser.add_argument('--source',type=Path,default=ROOT/'data');args=parser.parse_args()
    source=args.source.resolve()
    with sqlite3.connect((source/'gaade.db').as_uri()+'?mode=ro',uri=True) as connection:
        connection.row_factory=sqlite3.Row
        records=[dict(r) for r in connection.execute("SELECT * FROM proverbs WHERE verification_status='APPROVED' ORDER BY id")]
    config=load_env(args.config_file);url=config.get('DATABASE_URL','').strip()
    if not url:raise ValueError('DATABASE_URL missing from private configuration')
    if url.startswith('postgres://'):url='postgresql+psycopg://'+url[len('postgres://'):]
    elif url.startswith('postgresql://'):url='postgresql+psycopg://'+url[len('postgresql://'):]
    if not url.startswith('postgresql+psycopg://'):raise ValueError('PostgreSQL URL required')
    engine=create_engine(url,connect_args={'sslmode':'require','options':'-csearch_path=gaade','connect_timeout':15},pool_size=1,max_overflow=0,pool_pre_ping=True)
    try:
        with Session(engine) as session,session.begin():
            session.execute(text('SELECT pg_advisory_xact_lock(74623321)'))
            remote,missing,existing,conflicts=plan_sync(session,records)
            print(f'Local approved: {len(records)}; hosted records: {len(remote)}; missing IDs: {len(missing)}; unchanged: {len(existing)}; conflicts: {len(conflicts)}.',flush=True)
            if conflicts:
                print(json.dumps(conflicts,ensure_ascii=False));raise ValueError('Hosted differences require reconciliation; nothing changed')
            if not args.apply:print('Inspection only; no data changed.');return
            folder=source/'backups';folder.mkdir(exist_ok=True)
            stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            before={'records':[dump(row) for row in remote.values()],'translations':[dict(row._mapping) for row in session.execute(text('SELECT id,payload FROM dictionary_translations'))]}
            backup=folder/('cloud-before-approved-sync-'+stamp+'.json');backup.write_text(json.dumps(before,ensure_ascii=False,indent=2));backup.chmod(0o600)
            for record in missing:session.add(Proverb(**record))
            session.flush();translations_added=0
            for record in records:
                translation=load_translation(source,SimpleNamespace(**record))
                if translation:
                    result=session.execute(text('INSERT INTO dictionary_translations(id,payload) VALUES (:id,:payload) ON CONFLICT(id) DO NOTHING'),{'id':record['id'],'payload':json.dumps(translation,ensure_ascii=False)})
                    translations_added+=result.rowcount
            print(f'Synced {len(missing)} approved records and {translations_added} missing translations; existing records/translations preserved.',flush=True)
        print('Transaction committed. Private backup saved; no audio, pending records, keys or admin tokens uploaded.')
    finally:engine.dispose()
if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('Sync stopped safely:',type(exc).__name__,'— no credentials printed. Check private configuration/connectivity or reported conflicts.',file=sys.stderr);sys.exit(1)
