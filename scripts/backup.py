#!/usr/bin/env python3
"""Respaldo de hefesto-suscripciones (Wallos + SQLite).

El .env nunca se copia en claro: al respaldo solo van sus nombres (env.vars) y,
si hay receptor age, el .env cifrado (env.age). Ver docs/CONTRATO-RESPALDO.md.
"""
import datetime
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from respaldo_contrato import (artefactos_presentes, escribir_manifiesto, ejecutar,
                               exportar_env, marcar_fallido)

SOFTWARE = "hefesto-suscripciones"
VERSION = "5.8.3"
DATABASE = "sqlite"
RAIZ = Path(__file__).resolve().parents[1]
os.chdir(RAIZ)
os.umask(0o077)


def dc(*a, **kw):
    return subprocess.run(["docker", "compose", *a], check=True, **kw)


def main():
    carpeta = RAIZ / "backups" / datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    carpeta.mkdir(parents=True, mode=0o700)
    running = bool(dc("ps", "--status", "running", "-q", "app", capture_output=True, text=True).stdout.strip())
    try:
        dc("stop", "app")
        for volumen in ["db", "logos"]:
            with (carpeta / (volumen + ".tar.gz")).open("wb") as f:
                dc("run", "--rm", "--no-deps", "-T", "--entrypoint", "tar", "filetools",
                   "-czf", "-", "-C", "/" + volumen, ".", stdout=f)
        shutil.copytree(RAIZ / "ops", carpeta / "ops")
        if (RAIZ / "compose.yaml").is_file():
            shutil.copy2(RAIZ / "compose.yaml", carpeta / "compose.yaml")
        meta = exportar_env(RAIZ, carpeta)
        escribir_manifiesto(carpeta, SOFTWARE, VERSION, DATABASE,
                            artefactos_presentes(carpeta), extra=meta)
    except Exception:
        marcar_fallido(carpeta, SOFTWARE, VERSION, DATABASE)
        raise
    finally:
        if running:
            dc("start", "app")
    print("Respaldo completo:", carpeta)
    print("El .env no viaja en claro: solo env.vars y, si hay receptor age, env.age.")
    return 0


if __name__ == "__main__":
    raise SystemExit(ejecutar(main))
