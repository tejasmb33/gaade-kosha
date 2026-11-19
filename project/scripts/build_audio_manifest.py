#!/usr/bin/env python3
"""Match supplied MP3 filenames to approved proverbs; validate media without changing originals."""
import argparse,hashlib,json,sqlite3,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.proverb_audio import normalize

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--data-dir',type=Path,default=ROOT/'data');args=parser.parse_args()
    with sqlite3.connect((args.data_dir.resolve()/'gaade.db').as_uri()+'?mode=ro',uri=True) as connection:
        rows=list(connection.execute("SELECT id,proverb_kn FROM proverbs WHERE verification_status='APPROVED'"))
    byword={}
    for id,word in rows:byword.setdefault(normalize(word),[]).append((id,word))
    manifest={};unmatched=[]
    for path in sorted((ROOT/'datasets/submission/audio').glob('*.mp3')):
        matches=byword.get(normalize(path.stem),[])
        if len(matches)!=1:unmatched.append(path.name);continue
        id,word=matches[0]
        if id in manifest:raise ValueError('Multiple files match one proverb')
        result=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration:stream=codec_type,sample_rate,channels','-of','json',str(path)],capture_output=True,text=True,check=True)
        info=json.loads(result.stdout);streams=[stream for stream in info['streams'] if stream['codec_type']=='audio'];duration=float(info['format']['duration'])
        if len(streams)!=1 or not 0<duration<=300:raise ValueError('Invalid audio')
        manifest[id]={'proverb_kn':word,'filename':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'duration_seconds':round(duration,3),'sample_rate':int(streams[0]['sample_rate']),'channels':int(streams[0]['channels']),'match_basis':'NFC Kannada filename match ignoring spacing and punctuation','transcript_review':'not_established'}
    if unmatched:raise ValueError('Unmatched/ambiguous filenames: '+', '.join(unmatched))
    if not manifest:raise ValueError('No audio files')
    output=ROOT/'deployment/proverb-audio.json';output.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(f'Validated and linked {len(manifest)} supplied MP3 files to approved proverb IDs. Originals unchanged.')
if __name__=='__main__':main()
