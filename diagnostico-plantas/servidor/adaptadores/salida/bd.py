"""Conexion y esquema de SQLite, compartidos por los adaptadores de BD.
Se abre una conexion por operacion porque Flask atiende cada
peticion en un hilo distinto.

Tablas fijas: especies, usuarios, plantas, dispositivos.
Ademas hay una tabla de lecturas por cada planta: lecturas_MAT_XXXXXX.
"""

import re
import sqlite3
from contextlib import contextmanager
from typing import Iterator

_TABLAS = """
CREATE TABLE IF NOT EXISTS especies (
    nombre TEXT PRIMARY KEY,
    nombre_comun TEXT,
    humedad_min REAL, humedad_max REAL,
    luz_min REAL, luz_max REAL,
    temp_min REAL, temp_max REAL
);
CREATE TABLE IF NOT EXISTS usuarios (
    id TEXT PRIMARY KEY,
    correo TEXT UNIQUE NOT NULL,
    clave_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS plantas (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    especie TEXT NOT NULL,
    usuario_id TEXT NOT NULL REFERENCES usuarios (id)
);
CREATE TABLE IF NOT EXISTS dispositivos (
    id TEXT PRIMARY KEY,
    planta_id TEXT UNIQUE NOT NULL REFERENCES plantas (id)
);
"""

_PATRON_ID_PLANTA = re.compile(r"^MAT-[0-9A-F]{6}$")


@contextmanager
def conectar(ruta_bd: str) -> Iterator[sqlite3.Connection]:
    conexion = sqlite3.connect(ruta_bd)
    conexion.row_factory = sqlite3.Row
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def crear_tablas(ruta_bd: str) -> None:
    with conectar(ruta_bd) as conexion:
        conexion.executescript(_TABLAS)


def id_planta_valido(planta_id: str) -> bool:
    return isinstance(planta_id, str) and _PATRON_ID_PLANTA.match(planta_id) is not None


def nombre_tabla_lecturas(planta_id: str) -> str:
    """El nombre de una tabla no se puede pasar como parametro de SQL,
    asi que solo se acepta un id con la forma exacta MAT-XXXXXX."""
    if not id_planta_valido(planta_id):
        raise ValueError(f"Identificador de planta invalido: {planta_id!r}")
    return "lecturas_" + planta_id.replace("-", "_")


def crear_tabla_lecturas(ruta_bd: str, planta_id: str) -> None:
    tabla = nombre_tabla_lecturas(planta_id)
    with conectar(ruta_bd) as conexion:
        conexion.executescript(
            f"CREATE TABLE IF NOT EXISTS {tabla} ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "momento TEXT NOT NULL, "
            "humedad REAL, luz REAL, temperatura REAL, "
            "estado TEXT NOT NULL);"
            f"CREATE INDEX IF NOT EXISTS idx_{tabla} ON {tabla} (momento);"
        )


def existe_tabla(ruta_bd: str, tabla: str) -> bool:
    with conectar(ruta_bd) as conexion:
        fila = conexion.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", (tabla,)
        ).fetchone()
    return fila is not None
