#!/usr/bin/env python3
"""Build/reuse local E5 embeddings for approved database records. Never downloads models."""
import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.dev import load_env

def main():
    os.chdir(ROOT)
    config=load_env(ROOT/'.env')
    for key in ['E5_MODEL_PATH','GAADE_DATA_DIR']:
        if config.get(key):os.environ[key]=str(Path(config[key]).resolve())
    from backend.app import create_app,Proverb,APPROVED
    from sqlalchemy import select
    app=create_app()
    with app.state.Session() as s:
        rows=list(s.scalars(select(Proverb).where(Proverb.verification_status==APPROVED)))
        model=app.state.semantic
        if not model.path:raise RuntimeError('Configure E5_MODEL_PATH in .env before building the index')
        scores=model.scores('Prepare local search index',rows)
        if model.error:raise RuntimeError(model.error)
        if len(scores)!=len(rows):raise RuntimeError('Embedding count mismatch')
        print(f'Local E5 index ready: {len(rows)} approved proverbs. Existing vectors reused; no database records or statuses changed.')
if __name__=='__main__':main()
