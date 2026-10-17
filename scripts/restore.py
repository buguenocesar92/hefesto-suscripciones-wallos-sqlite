#!/usr/bin/env python3
import hashlib,json,os,subprocess,sys,tarfile
from pathlib import Path,PurePosixPath
root=Path(__file__).resolve().parents[1];os.chdir(root)
if len(sys.argv)!=2:raise SystemExit('Uso: python3 scripts/restore.py /ruta/respaldo')
p=Path(sys.argv[1]).resolve();m=json.loads((p/'manifest.json').read_text())
if m.get('product')!='hefesto-suscripciones' or m.get('version')!='5.8.3' or m.get('status')!='completed':raise SystemExit('Manifest invalido')
for name in ['db','logos']:
    a=p/(name+'.tar.gz')
    with a.open('rb') as f:
        if hashlib.file_digest(f,'sha256').hexdigest()!=m['sha256'][a.name]:raise SystemExit('Hash incorrecto')
    with tarfile.open(a) as tf:
        seen=set()
        for member in tf:
            path=PurePosixPath(member.name)
            if path.is_absolute() or '..' in path.parts or not(member.isfile() or member.isdir()) or str(path) in seen:raise SystemExit('Ruta/tipo no admitido')
            seen.add(str(path))
def dc(*a,**kw):return subprocess.run(['docker','compose',*a],check=True,**kw)
if dc('ps','--status','running','-q','app',capture_output=True,text=True).stdout.strip():raise SystemExit('Detener app antes de restaurar')
for name in ['db','logos']:
    found=dc('run','--rm','--no-deps','-T','--entrypoint','find','filetools','/'+name,'-mindepth','1','-maxdepth','1',capture_output=True,text=True).stdout.strip()
    if found:raise SystemExit('Volumen no vacio: '+name)
for name in ['db','logos']:
    with (p/(name+'.tar.gz')).open('rb') as f:dc('run','--rm','--no-deps','-T','--entrypoint','tar','filetools','-xzf','-','-C','/'+name,stdin=f)
dc('run','--rm','--no-deps','permissions')
print('Datos y configuracion restaurados. Probar suscripciones por entorno privado antes del corte DNS.')
