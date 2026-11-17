#!/usr/bin/env python3
"""Evaluate real JSONL search cases against a running local API."""
import argparse,json,sys,urllib.request
from pathlib import Path

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('cases',type=Path); p.add_argument('--url',default='http://localhost:8000'); args=p.parse_args()
    cases=[json.loads(x) for x in args.cases.read_text().splitlines() if x.strip()]
    if not cases: print('No cases: real evaluation has NOT passed.'); return 1
    passed=0
    for i,c in enumerate(cases,1):
        if not isinstance(c.get('expected_ids'),list) or not isinstance(c.get('query'),str): raise ValueError(f'Invalid case {i}')
        req=urllib.request.Request(args.url+'/api/search',data=json.dumps({'query':c['query']}).encode(),headers={'Content-Type':'application/json'})
        result=json.load(urllib.request.urlopen(req)); actual={r['id'] for r in result['items']}; expected=set(c['expected_ids'])
        ok=bool(actual & expected) if expected else not actual; passed+=ok
        print(f'{i}: {"PASS" if ok else "FAIL"} {c["query"]}')
    print(f'{passed} passed, {len(cases)-passed} failed'); return int(passed!=len(cases))
if __name__=='__main__': sys.exit(main())
