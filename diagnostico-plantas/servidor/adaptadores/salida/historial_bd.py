"""Historial de lecturas en SQLite: una tabla por planta."""

from datetime import datetime
from typing import List, Optional

from adaptadores.salida.bd import (
    conectar,
    crear_tabla_lecturas,
    existe_tabla,
    id_planta_valido,
    nombre_tabla_lecturas,
)
from dominio.entidades import EstadoPlanta, Lectura, RegistroLectura
from dominio.puertos.salida import HistorialLecturasPort


def _a_registro(planta_id: str, fila) -> RegistroLectura:
    lectura = Lectura(
        momento=datetime.fromisoformat(fila["momento"]),
        humedad=fila["humedad"],
        luz=fila["luz"],
        temperatura=fila["temperatura"],
    )
    return RegistroLectura(planta_id, lectura, EstadoPlanta(fila["estado"]))


class HistorialBD(HistorialLecturasPort):
    def __init__(self, ruta_bd: str):
        self._ruta_bd = ruta_bd

    def iniciar(self, planta_id: str) -> None:
        crear_tabla_lecturas(self._ruta_bd, planta_id)

    def guardar(self, planta_id: str, lectura: Lectura, estado: EstadoPlanta) -> None:
        crear_tabla_lecturas(self._ruta_bd, planta_id)
        tabla = nombre_tabla_lecturas(planta_id)
        with conectar(self._ruta_bd) as conexion:
            conexion.execute(
                f"INSERT INTO {tabla} (momento, humedad, luz, temperatura, estado) VALUES (?,?,?,?,?)",
                (
                    lectura.momento.isoformat(),
                    lectura.humedad, lectura.luz, lectura.temperatura, estado.value,
                ),
            )

    def ultima(self, planta_id: str) -> Optional[RegistroLectura]:
        registros = self.listar(planta_id, 1)
        return registros[0] if registros else None

    def listar(self, planta_id: str, limite: int) -> List[RegistroLectura]:
        if not id_planta_valido(planta_id):
            return []
        tabla = nombre_tabla_lecturas(planta_id)
        if not existe_tabla(self._ruta_bd, tabla):
            return []
        with conectar(self._ruta_bd) as conexion:
            filas = conexion.execute(
                f"SELECT * FROM {tabla} ORDER BY momento DESC, id DESC LIMIT ?", (limite,)
            ).fetchall()
        return [_a_registro(planta_id, f) for f in filas]
