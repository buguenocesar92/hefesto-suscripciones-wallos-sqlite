#!/usr/bin/env python3
"""Verificacion de integridad de un respaldo de hefesto-suscripciones.

Codigos de salida: 0 integro, 1 uso, 2 integridad o manifiesto invalido,
4 material sensible en claro dentro del respaldo.
"""
import shutil
import sqlite3
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath

sys.path.insert(0, str(Path(__file__).resolve().parent))
from respaldo_contrato import RespaldoError, ejecutar, ejecutar_check

SOFTWARE = "hefesto-suscripciones"
VERSION = "5.8.3"
DATABASE = "sqlite"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python3 scripts/check_backup.py /ruta/respaldo")
    p = Path(sys.argv[1])
    ejecutar_check(str(p), SOFTWARE, VERSION, DATABASE)
    with tempfile.TemporaryDirectory() as d:
        with tarfile.open(p / "db.tar.gz") as tf:
            for member in tf:
                nombre = PurePosixPath(member.name)
                if nombre.is_absolute() or ".." in nombre.parts or not (member.isfile() or member.isdir()):
                    raise RespaldoError("Archivo no seguro en el respaldo", 2)
                if member.isfile() and str(nombre) in ["wallos.db", "wallos.db-wal", "wallos.db-shm"]:
                    with tf.extractfile(member) as origen, (Path(d) / nombre.name).open("wb") as salida:
                        shutil.copyfileobj(origen, salida)
        base = Path(d) / "wallos.db"
        if not base.exists():
            raise RespaldoError("Falta wallos.db en el respaldo", 2)
        con = sqlite3.connect(base.as_uri() + "?mode=ro", uri=True)
        resultado = con.execute("PRAGMA integrity_check").fetchall()
        con.close()
        if resultado != [("ok",)]:
            raise RespaldoError("SQLite no supera integrity_check", 2)
    print("Manifiesto, checksums, SQLite y ausencia de secretos en claro verificados.")
    print("No sustituye el ensayo de restauracion de la app.")
    return 0


if __name__ == "__main__":
    raise SystemExit(ejecutar(main))
