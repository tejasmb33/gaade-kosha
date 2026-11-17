#!/usr/bin/env python3
"""Seed an empty cloud database with approved records; never overwrites live data."""
import json,os,sys
from urllib.parse import urlsplit
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


def validate_environment():
    required=['DATABASE_URL','SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY','GROQ_API_KEY']
    missing=[key for key in required if not os.getenv(key,'').strip()]
    if missing:raise ValueError('Missing Render environment variables: '+', '.join(missing))
    value=os.environ['DATABASE_URL'].strip()
    if value!=os.environ['DATABASE_URL']:raise ValueError('DATABASE_URL contains leading or trailing whitespace')
    try:
        parsed=urlsplit(value)
        valid=parsed.scheme in ['postgres','postgresql','postgresql+psycopg'] and parsed.hostname and parsed.username and parsed.password
        if not valid:raise ValueError()
        if any(char in parsed.password for char in ['[',']']) or value.count('@')!=1:
            raise ValueError()
        parsed.port
    except ValueError:
        raise ValueError('DATABASE_URL is malformed. Use the Supabase Session pooler URI; remove password placeholder brackets and URL-encode special characters in the password.') from None
    if os.getenv('GAADE_SPEECH_PROVIDER')!='groq':raise ValueError('Set GAADE_SPEECH_PROVIDER=groq on Render')
    if os.getenv('SUPABASE_SERVICE_ROLE_KEY','').startswith('sb_publishable_'):
        raise ValueError('SUPABASE_SERVICE_ROLE_KEY contains a publishable key. Use the backend service_role key instead.')


def safe_failure(stage,exc):
    # Do not print raw exceptions: driver/provider errors can contain credentials.
    if stage=='configuration':return str(exc) if isinstance(exc,ValueError) else 'Check required environment variables.'
    if stage=='private audio storage':return str(exc) if isinstance(exc,ValueError) else 'Check SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, and the private gaade-private bucket.'
    message=str(exc).lower()
    if 'password authentication failed' in message or 'invalid password' in message:return 'PostgreSQL rejected the database password. Check DATABASE_URL and URL-encode its password.'
    if 'tenant or user not found' in message:return 'Supabase rejected the pooler user. Copy the complete Session pooler URI, including postgres.PROJECT_REF.'
    if any(word in message for word in ['name or service not known','nodename nor servname','could not translate host','name resolution']):return 'Database hostname could not be resolved. Copy the Session pooler hostname from Supabase Connect.'
    if any(word in message for word in ['network is unreachable','connection refused','timeout expired','connection timeout']):return 'Database connection failed. Use the IPv4-compatible Session pooler URI and confirm the Supabase project is active.'
    if 'permission denied' in message:return 'Database user lacks permission to create/use the gaade schema. Check the Session pooler credentials.'
    return 'Database initialization failed ('+type(exc).__name__+'). Check the Session pooler URI, password, project availability and database permissions.'


def main():
    stage='configuration'
    try:
        validate_environment()
        stage='private audio storage'
        print('Cloud startup: checking private audio storage...',flush=True)
        from backend.object_store import ObjectStore
        ObjectStore().ensure_bucket()
        stage='database connection and schema'
        print('Cloud startup: connecting to PostgreSQL and checking schema...',flush=True)
        from backend.app import app
        stage='approved seed import'
        bundle=json.loads((Path(__file__).resolve().parents[1]/'deployment/approved-seed.json').read_text())
        count=seed(app,bundle)
        print(f'Cloud seed: {count} approved records added; existing databases are preserved.',flush=True)
        return 0
    except Exception as exc:
        print('Cloud initialization failed at '+stage+': '+safe_failure(stage,exc),file=sys.stderr,flush=True)
        return 1


if __name__=='__main__':sys.exit(main())
