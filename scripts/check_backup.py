#!/usr/bin/env python3
"""Read-only integrity check of a paused Wallos backup, without Docker."""
import hashlib,json,sqlite3,sys,tarfile,tempfile
from pathlib import Path,PurePosixPath
if len(sys.argv)!=2:raise SystemExit('Uso: python3 scripts/check_backup.py /ruta/respaldo')
p=Path(sys.argv[1]);m=json.loads((p/'manifest.json').read_text())
if (m.get('product'),m.get('version'),m.get('status'))!=('hefesto-suscripciones','5.8.3','completed'):raise SystemExit('Manifest incorrecto')
for n in ['db.tar.gz','logos.tar.gz']:
 with (p/n).open('rb') as f:
  if hashlib.file_digest(f,'sha256').hexdigest()!=m['sha256'][n]:raise SystemExit('Checksum incorrecto')
with tempfile.TemporaryDirectory() as d:
 with tarfile.open(p/'db.tar.gz') as tf:
  for member in tf:
   name=PurePosixPath(member.name)
   if name.is_absolute() or '..' in name.parts or not(member.isfile() or member.isdir()):raise SystemExit('Archivo no seguro')
   if member.isfile() and str(name) in ['wallos.db','wallos.db-wal','wallos.db-shm']:
    with tf.extractfile(member) as src, (Path(d)/name.name).open('wb') as out:
     import shutil;shutil.copyfileobj(src,out)
 db=Path(d)/'wallos.db'
 if not db.exists():raise SystemExit('Falta wallos.db')
 conn=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)
 result=conn.execute('PRAGMA integrity_check').fetchall();conn.close()
 if result!=[('ok',)]:raise SystemExit('SQLite no supera integrity_check')
print('Hashes y SQLite correctos. No sustituye ensayo de restauración de la app.')
