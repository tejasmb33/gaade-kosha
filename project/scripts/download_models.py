#!/usr/bin/env python3
"""Inspect approved upstream snapshots; download only with --download. TLS remains verified."""
import argparse, hashlib, json, os, sys, urllib.request
from pathlib import Path
MODELS={
 'e5':{'repo':'intfloat/multilingual-e5-small','license':'mit','weight':'model.safetensors','required':['config.json','tokenizer.json','tokenizer_config.json','special_tokens_map.json','sentencepiece.bpe.model','modules.json','1_Pooling/config.json','sentence_bert_config.json']},
 'whisper':{'repo':'mlx-community/whisper-small-mlx','license':'mit','weight':'weights.npz','required':['config.json']}}
BUDGET=2_000_000_000

def inspect(name,spec):
    url='https://huggingface.co/api/models/'+spec['repo']+'?blobs=true'
    with urllib.request.urlopen(url,timeout=60) as r: meta=json.load(r)
    rev=meta['sha']; license=meta.get('cardData',{}).get('license')
    license_evidence=None
    if name=='whisper' and license is None:
        # This conversion card omits license metadata; verify the original publisher's
        # explicit code-and-model-weights statement at an immutable revision.
        license_evidence='https://raw.githubusercontent.com/openai/whisper/86098128c0b4f24f0e2aa2994de830614b474227/README.md'
        with urllib.request.urlopen(license_evidence,timeout=60) as r: documentation=r.read().decode()
        if "Whisper's code and model weights are released under the MIT License." not in documentation:
            raise ValueError('Official Whisper weight licence evidence changed')
        license='mit'
    if license!=spec['license']: raise ValueError(f'{name}: expected documented MIT license, got {license!r}')
    files={x['rfilename']:x for x in meta['siblings']}
    selected=[spec['weight']]+spec['required']
    for optional in ['README.md','LICENSE','LICENSE.txt']:
        if optional in files: selected.append(optional)
    for f in selected:
        if f not in files or not isinstance(files[f].get('size'),int): raise ValueError(f'Upstream layout changed: missing size or file {name}/{f}')
    if len(rev)!=40: raise ValueError('Expected immutable commit SHA')
    return {'repo':spec['repo'],'revision':rev,'license':license,'license_evidence':license_evidence or f'https://huggingface.co/{spec["repo"]}/blob/{rev}/README.md','documentation':f'https://huggingface.co/{spec["repo"]}/blob/{rev}/README.md','files':[{ 'name':f,'size':files[f]['size'],'sha256':files[f].get('lfs',{}).get('sha256'),'git_oid':files[f].get('blobId')} for f in selected],'all_upstream_artifacts':[{ 'name':f,'size':v.get('size')} for f,v in files.items()]}

def verify(path,item):
    if path.stat().st_size!=item['size']: raise ValueError('File size mismatch: '+str(path))
    data=path.read_bytes()
    if item['sha256']:
        digest=hashlib.sha256(data).hexdigest(); expected=item['sha256']
    else:
        digest=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(); expected=item['git_oid']
    if not expected or digest!=expected: raise ValueError('Authoritative checksum mismatch: '+str(path))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--download',action='store_true');p.add_argument('--inspect',action='store_true');p.add_argument('--destination',type=Path,default=Path(__file__).resolve().parents[1]/'models');args=p.parse_args()
    reports={name:inspect(name,spec) for name,spec in MODELS.items()}
    root=args.destination.resolve(); existing=sum(f.stat().st_size for f in root.rglob('*') if f.is_file()) if root.exists() else 0
    extra=0
    for name,report in reports.items():
        for f in report['files']:
            path=root/name/f['name']
            if path.exists(): verify(path,f)
            else: extra+=f['size']
    summary={'budget_bytes':BUDGET,'existing_bytes_including_stale_variants':existing,'additional_bytes':extra,'projected_total_bytes':existing+extra,'models':reports}
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if existing+extra>BUDGET: raise ValueError('Combined model budget exceeded, including stale artifacts. Remove unwanted variants manually.')
    if not args.download: return 0
    root.mkdir(parents=True,exist_ok=True)
    for name,report in reports.items():
        target=root/name;target.mkdir(exist_ok=True)
        for item in report['files']:
            dest=target/item['name'];dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists(): continue
            temp=dest.with_name(dest.name+'.partial')
            url=f'https://huggingface.co/{report["repo"]}/resolve/{report["revision"]}/{item["name"]}'
            try:
                with urllib.request.urlopen(url,timeout=120) as src,temp.open('wb') as out:
                    remaining=item['size']
                    while chunk:=src.read(min(1024*1024,remaining+1)):
                        remaining-=len(chunk)
                        if remaining<0: raise ValueError('Upstream file exceeded declared size')
                        out.write(chunk)
                verify(temp,item);temp.replace(dest)
            finally:
                if temp.exists(): temp.unlink()
        (target/'revision.json').write_text(json.dumps(report,indent=2))
    (root/'model-evidence.json').write_text(json.dumps(summary,indent=2));print('Verified model snapshots downloaded. Configure E5_MODEL_PATH and WHISPER_MODEL_PATH explicitly.')
    return 0
if __name__=='__main__':
    try: sys.exit(main())
    except Exception as exc: print(f'Model operation failed: {exc}',file=sys.stderr);sys.exit(1)
