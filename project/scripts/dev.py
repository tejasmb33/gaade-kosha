#!/usr/bin/env python3
"""Standard-library development supervisor. Never installs or downloads anything."""
import argparse, importlib.util, os, secrets, shlex, shutil, signal, socket, subprocess, sys, time, urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load_env(path,environ=None):
    result=dict(os.environ if environ is None else environ)
    if Path(path).exists():
        for number,line in enumerate(Path(path).read_text().splitlines(),1):
            if not line.strip() or line.lstrip().startswith('#'): continue
            if '=' not in line: raise ValueError(f'Invalid configuration line {number}')
            key,value=line.split('=',1); key=key.strip()
            if not key.replace('_','a').isalnum() or key[0].isdigit(): raise ValueError(f'Invalid configuration key on line {number}')
            parts=shlex.split(value,comments=True)
            if len(parts)>1: raise ValueError(f'Quote paths containing spaces on line {number}')
            result.setdefault(key,parts[0] if parts else '')
    return result
def private_token(data):
    path=data/'admin-token'; data.mkdir(parents=True,exist_ok=True)
    try:
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as out: out.write(secrets.token_urlsafe(32))
    except FileExistsError: pass
    path.chmod(0o600)
    token=path.read_text().strip()
    if len(token)<32: raise ValueError('Existing admin-token is invalid; replace it locally')
    return token

def check_port(host,port):
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        try: sock.bind((host,port))
        except OSError: raise ValueError(f'Port {port} is unavailable; existing services were left running')
def wait_health(url,children):
    for _ in range(120):
        if any(c.poll() is not None for c in children): raise RuntimeError('A service exited during startup')
        try:
            import json
            with urllib.request.urlopen(url,timeout=1) as response:
                if json.load(response).get('backend')=='ok': return
        except Exception: pass
        time.sleep(.25)
    raise RuntimeError('Health check timed out: '+url)
def stop(children):
    for child in children:
        try: os.killpg(child.pid,signal.SIGTERM)
        except ProcessLookupError: pass
    for child in children:
        try: child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try: os.killpg(child.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            child.wait()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true'); parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--backend-port',type=int,default=8000); parser.add_argument('--frontend-port',type=int,default=5173)
    parser.add_argument('--data-dir'); parser.add_argument('--config-file',default=str(ROOT/'.env'))
    args=parser.parse_args(); children=[]
    try:
        os.chdir(ROOT); env=load_env(args.config_file)
        if any(not 1<=p<=65535 for p in [args.backend_port,args.frontend_port]) or args.backend_port==args.frontend_port: raise ValueError('Ports must be distinct integers from 1 to 65535')
        missing=[p for p in ['fastapi','uvicorn','sqlalchemy','numpy','multipart'] if importlib.util.find_spec(p) is None]
        missing += [p for p in ['node','npm','ffmpeg','ffprobe'] if not shutil.which(p)]
        if not (ROOT/'frontend/node_modules/vite').is_dir(): missing.append('frontend dependencies (npm ci --prefix frontend)')
        if missing: raise ValueError('Missing prerequisites: '+', '.join(missing))
        check_port(args.host,args.backend_port); check_port(args.host,args.frontend_port)
        data=Path(args.data_dir or env.get('GAADE_DATA_DIR') or ROOT/'data').resolve()
        if args.check:
            print('Prerequisites and ports OK. No services started or token generated.'); return 0
        env['GAADE_DATA_DIR']=str(data)
        env['ADMIN_TOKEN']=env.get('ADMIN_TOKEN') or private_token(data)
        env.setdefault('FRONTEND_ORIGIN',f'http://localhost:{args.frontend_port}')
        front_env={k:v for k,v in env.items() if k not in ['ADMIN_TOKEN','E5_MODEL_PATH','WHISPER_MODEL_PATH','OPENAI_API_KEY','GEMINI_API_KEY','GROQ_API_KEY']}
        front_env['GAADE_BACKEND_TARGET']=f'http://127.0.0.1:{args.backend_port}'
        def terminate(signum,frame): raise KeyboardInterrupt
        signal.signal(signal.SIGTERM,terminate)
        children.append(subprocess.Popen([sys.executable,'-m','uvicorn','backend.app:app','--host',args.host,'--port',str(args.backend_port)],env=env,start_new_session=True))
        children.append(subprocess.Popen(['npm','run','dev','--','--host',args.host,'--port',str(args.frontend_port),'--strictPort'],cwd=ROOT/'frontend',env=front_env,start_new_session=True))
        wait_health(f'http://127.0.0.1:{args.backend_port}/api/health',children)
        wait_health(f'http://127.0.0.1:{args.frontend_port}/api/health',children)
        print(f'Ready: http://localhost:{args.frontend_port} | API docs: http://localhost:{args.backend_port}/docs',flush=True)
        print(f'Review token: copy locally from {data / "admin-token"}' if not os.environ.get('ADMIN_TOKEN') and not load_env(args.config_file,{}).get('ADMIN_TOKEN') else 'Review uses configured ADMIN_TOKEN.',flush=True)
        while all(c.poll() is None for c in children): time.sleep(.3)
        raise RuntimeError('A service stopped; shutting down both services')
    except KeyboardInterrupt: return 0
    except (ValueError,RuntimeError,OSError) as exc: print(str(exc),file=sys.stderr); return 1
    finally: stop(children)
if __name__=='__main__': sys.exit(main())
