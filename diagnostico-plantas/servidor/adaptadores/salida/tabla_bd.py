"""Tabla de referencia en SQLite: mismo puerto que tabla_csv.py, otra tecnologia."""

from typing import List, Optional

from adaptadores.salida.bd import conectar
from dominio.especie import Especie, RangoOptimo
from dominio.puertos.salida import CatalogoEspeciesPort, TablaReferenciaPort


def _a_especie(fila) -> Especie:
    return Especie(
        nombre=fila["nombre"],
        humedad=RangoOptimo(fila["humedad_min"], fila["humedad_max"]),
        luz=RangoOptimo(fila["luz_min"], fila["luz_max"]),
        temperatura=RangoOptimo(fila["temp_min"], fila["temp_max"]),
        nombre_comun=fila["nombre_comun"] or "",
    )


class TablaBD(TablaReferenciaPort, CatalogoEspeciesPort):
    def __init__(self, ruta_bd: str):
        self._ruta_bd = ruta_bd

    def esta_vacia(self) -> bool:
        with conectar(self._ruta_bd) as conexion:
            return conexion.execute("SELECT COUNT(*) FROM especies").fetchone()[0] == 0

    def cargar(self, especies: List[Especie]) -> None:
        with conectar(self._ruta_bd) as conexion:
            conexion.executemany(
                "INSERT OR REPLACE INTO especies VALUES (?,?,?,?,?,?,?,?)",
                [
                    (
                        e.nombre, e.nombre_comun,
                        e.humedad.minimo, e.humedad.maximo,
                        e.luz.minimo, e.luz.maximo,
                        e.temperatura.minimo, e.temperatura.maximo,
                    )
                    for e in especies
                ],
            )

    def obtener_por_nombre(self, nombre: str) -> Optional[Especie]:
        with conectar(self._ruta_bd) as conexion:
            fila = conexion.execute(
                "SELECT * FROM especies WHERE nombre = ?", ((nombre or "").strip().lower(),)
            ).fetchone()
        return _a_especie(fila) if fila else None

    def listar_todas(self) -> List[Especie]:
        with conectar(self._ruta_bd) as conexion:
            filas = conexion.execute("SELECT * FROM especies ORDER BY nombre").fetchall()
        return [_a_especie(f) for f in filas]
