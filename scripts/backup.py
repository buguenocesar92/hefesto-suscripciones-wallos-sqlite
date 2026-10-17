#!/usr/bin/env python3
import datetime,hashlib,json,os,shutil,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];os.chdir(root);os.umask(0o077)
def dc(*a,**kw):return subprocess.run(['docker','compose',*a],check=True,**kw)
p=root/'backups'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');p.mkdir(parents=True,mode=0o700)
running=bool(dc('ps','--status','running','-q','app',capture_output=True,text=True).stdout.strip())
try:
    dc('stop','app')
    for volume in ['db','logos']:
        with (p/(volume+'.tar.gz')).open('wb') as f:dc('run','--rm','--no-deps','-T','--entrypoint','tar','filetools','-czf','-','-C','/'+volume,'.',stdout=f)
    shutil.copytree(root/'ops',p/'ops');shutil.copy2(root/'.env',p/'.env');shutil.copy2(root/'compose.yaml',p/'compose.yaml')
    hashes={}
    for n in ['db.tar.gz','logos.tar.gz','.env','compose.yaml','ops/start.sh','ops/nginx.conf']:
        with (p/n).open('rb') as f:hashes[n]=hashlib.file_digest(f,'sha256').hexdigest()
    (p/'manifest.json').write_text(json.dumps({'product':'hefesto-suscripciones','version':'5.8.3','status':'completed','sha256':hashes},indent=2))
    print('Respaldo completo:',p,'Contiene archivos y claves; cifrar antes de transferir.')
finally:
    if running:dc('start','app')
