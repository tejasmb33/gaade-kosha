#!/usr/bin/env python3
"""Run the complete built app locally; a separate HTTPS tunnel can publish it."""
import argparse,os,signal,subprocess,sys,time
from pathlib import Path
from dev import ROOT,load_env,private_token,check_port,wait_health,stop


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8080)
    parser.add_argument('--data-dir')
    parser.add_argument('--config-file',default=str(ROOT/'.env'))
    args=parser.parse_args();children=[]
    try:
        if not 1<=args.port<=65535: raise ValueError('Port must be between 1 and 65535')
        check_port('127.0.0.1',args.port)
        if not (ROOT/'frontend/dist/index.html').is_file(): raise ValueError('Build frontend first: npm run build --prefix frontend')
        env=load_env(args.config_file)
        data=Path(args.data_dir or env.get('GAADE_DATA_DIR') or ROOT/'data').resolve()
        env['GAADE_DATA_DIR']=str(data)
        env['ADMIN_TOKEN']=env.get('ADMIN_TOKEN') or private_token(data)
        def terminate(signum,frame):raise KeyboardInterrupt
        signal.signal(signal.SIGTERM,terminate)
        children.append(subprocess.Popen([sys.executable,'-m','uvicorn','backend.production:app','--host','127.0.0.1','--port',str(args.port)],cwd=ROOT,env=env,start_new_session=True))
        wait_health(f'http://127.0.0.1:{args.port}/api/health',children)
        print(f'Built app ready: http://localhost:{args.port}',flush=True)
        print('Database, models and recordings stay on this Mac. Keep it awake while hosting.',flush=True)
        while children[0].poll() is None:time.sleep(.3)
        raise RuntimeError('App server stopped')
    except KeyboardInterrupt:return 0
    except (OSError,ValueError,RuntimeError) as exc:print(str(exc),file=sys.stderr);return 1
    finally:stop(children)


if __name__=='__main__':sys.exit(main())
