#!/usr/bin/env python3
"""Check configured cloud AI using one situation. Sends approved metadata to the selected provider."""
import os,sys,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.dev import load_env

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--provider',choices=['gemini','openai','groq']);args=parser.parse_args()
    os.chdir(ROOT)
    config=load_env(ROOT/'.env')
    for key in ['GAADE_AI_PROVIDER','GAADE_AI_MODEL','GAADE_AI_WEB_FALLBACK','GEMINI_API_KEY','OPENAI_API_KEY','GAADE_DATA_DIR','GROQ_API_KEY','GAADE_GROQ_MODEL']:
        if key in config:os.environ[key]=config[key]
    from backend.cloud_search import status
    if not status(args.provider)['configured']:
        print('Not ready: add GEMINI_API_KEY to project/.env. No API request was made.');return 2
    from backend.app import create_app,CloudQuery
    app=create_app()
    # Call the route directly so a running development server is not needed.
    handler=next(r.endpoint for r in app.routes if getattr(r,'path',None)=='/api/search/ai')
    try:
        result=handler(CloudQuery(provider=args.provider,query='Financial difficulties nearly forced her to drop out of school. But she worked part-time, earned a scholarship, and completed her education.'))
    except Exception as exc:
        print(getattr(exc,'detail','Cloud check failed. Review your API configuration.'));return 1
    print('Provider:',status(args.provider)['provider'],'Model:',status(args.provider)['model'])
    print('Interpretation:',result['interpretation'])
    for row in result['items']:print('Matched database proverb:',row['proverb_kn'])
    if not result['items']:print('No reviewed database match. External references:',len(result.get('external_sources',[])))
    print('Live request completed. Review the returned match; this is not a general accuracy evaluation.');return 0
if __name__=='__main__':sys.exit(main())
