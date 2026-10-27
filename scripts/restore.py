#!/usr/bin/env python3
"""Restauracion de hefesto-suscripciones en un destino nuevo y vacio.

Sin --confirmar CONFIRMAR_RESTAURACION no se escribe nada; con --dry-run se
simula. Valida manifiesto, sha256 y rutas tar antes de tocar el destino, exige
los volumenes destino vacios y deja restore-report.json y auditoria.
"""
import os
import subprocess
import sys
import tarfile
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
from respaldo_contrato import (RespaldoError, auditar, ejecutar, ejecutar_check,
                               escribir_informe, opciones_restore)

SOFTWARE = "hefesto-suscripciones"
VERSION = "5.8.3"
DATABASE = "sqlite"
RAIZ = Path(__file__).resolve().parents[1]
os.chdir(RAIZ)
os.umask(0o077)


def dc(*a, **kw):
    return subprocess.run(["docker", "compose", *a], check=True, **kw)


def main():
    modo, origen = opciones_restore(sys.argv[1:])
    origen = Path(origen).resolve()
    ejecutar_check(str(origen), SOFTWARE, VERSION, DATABASE)
    for volumen in ["db", "logos"]:
        with tarfile.open(origen / (volumen + ".tar.gz"), "r:gz") as archivo:
            vistos = set()
            for miembro in archivo:
                ruta = PurePosixPath(miembro.name)
                if ruta.is_absolute() or ".." in ruta.parts or not (miembro.isfile() or miembro.isdir()) or str(ruta) in vistos:
                    raise RespaldoError("Ruta o tipo no admitido en " + volumen, 2)
                vistos.add(str(ruta))
    if modo == "dry-run":
        print("Simulacion: el respaldo es integro y no se escribio nada.")
        print("Para restaurar de verdad: --confirmar CONFIRMAR_RESTAURACION")
        return 0
    if dc("ps", "--status", "running", "-q", "app", capture_output=True, text=True).stdout.strip():
        raise RespaldoError("Detener app antes de restaurar", 5)
    for volumen in ["db", "logos"]:
        ocupado = dc("run", "--rm", "--no-deps", "-T", "--entrypoint", "find", "filetools",
                     "/" + volumen, "-mindepth", "1", "-maxdepth", "1",
                     capture_output=True, text=True).stdout.strip()
        if ocupado:
            raise RespaldoError("Volumen no vacio: " + volumen, 5)
    for volumen in ["db", "logos"]:
        with (origen / (volumen + ".tar.gz")).open("rb") as f:
            dc("run", "--rm", "--no-deps", "-T", "--entrypoint", "tar", "filetools",
               "-xzf", "-", "-C", "/" + volumen, stdin=f)
    dc("run", "--rm", "--no-deps", "permissions")
    escribir_informe(origen, software=SOFTWARE, version=VERSION, database=DATABASE,
                     modo="confirmado", resultado="restaurado", destino=str(RAIZ))
    auditar(RAIZ, operacion="restore", kit=SOFTWARE, origen=str(origen), destino=str(RAIZ),
            resultado="restaurado")
    print("Datos y configuracion restaurados. Probar suscripciones por entorno privado "
          "antes del corte DNS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(ejecutar(main))
