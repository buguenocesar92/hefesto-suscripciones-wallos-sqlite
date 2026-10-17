#!/usr/bin/env python3
import os
from pathlib import Path
r=Path(__file__).resolve().parents[1]
fd=os.open(r/'.env',os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
with os.fdopen(fd,'w') as f:f.write((r/'.env.example').read_text())
print('.env creado. Usuario/contraseña se definen en instalación privada.')
