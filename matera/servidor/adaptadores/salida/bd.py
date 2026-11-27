import sqlite3

TABLAS = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    correo TEXT NOT NULL UNIQUE,
    clave_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS especies (
    nombre TEXT PRIMARY KEY, nombre_comun TEXT NOT NULL,
    humedad_min REAL, humedad_max REAL, luz_min REAL, luz_max REAL,
    temp_min REAL, temp_max REAL
);
CREATE TABLE IF NOT EXISTS plantas (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    especie TEXT NOT NULL,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id)
);
CREATE TABLE IF NOT EXISTS dispositivos (
    id TEXT PRIMARY KEY,
    planta_id TEXT NOT NULL UNIQUE REFERENCES plantas(id),
    estado TEXT NOT NULL,
    ventana_hasta TEXT,
    generacion INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS lecturas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    planta_id TEXT NOT NULL REFERENCES plantas(id),
    momento TEXT NOT NULL,
    humedad REAL NOT NULL, luz REAL NOT NULL, temperatura REAL NOT NULL,
    estado TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_lecturas_planta ON lecturas(planta_id, momento DESC);
CREATE TABLE IF NOT EXISTS puntajes (
    planta_id TEXT PRIMARY KEY REFERENCES plantas(id),
    puntos INTEGER NOT NULL,
    estado TEXT, cobrado_hasta TEXT, ultima TEXT
);
"""


class BaseDatos:
    """Una conexión por operación: segura entre los hilos de HTTP, WebSocket y MQTT."""

    def __init__(self, ruta: str):
        self._ruta = ruta
        con = self._abrir()
        try:
            con.executescript(TABLAS)
        finally:
            con.close()

    def _abrir(self):
        con = sqlite3.connect(self._ruta, timeout=10)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        return con

    def consultar(self, sql: str, *parametros) -> list:
        con = self._abrir()
        try:
            return con.execute(sql, parametros).fetchall()
        finally:
            con.close()

    def escribir(self, sql: str, *parametros) -> int:
        con = self._abrir()
        try:
            with con:
                return con.execute(sql, parametros).lastrowid
        finally:
            con.close()
