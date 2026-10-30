"""Dispositivos en SQLite: cada uno pertenece a una sola planta."""

from typing import Optional

from adaptadores.salida.bd import conectar
from dominio.entidades import Dispositivo
from dominio.puertos.salida import DispositivoRepositorioPort


class DispositivosBD(DispositivoRepositorioPort):
    def __init__(self, ruta_bd: str):
        self._ruta_bd = ruta_bd

    def registrar(self, dispositivo: Dispositivo) -> None:
        with conectar(self._ruta_bd) as conexion:
            conexion.execute(
                "INSERT INTO dispositivos (id, planta_id) VALUES (?,?)",
                (dispositivo.id, dispositivo.planta_id),
            )

    def obtener(self, dispositivo_id: str) -> Optional[Dispositivo]:
        with conectar(self._ruta_bd) as conexion:
            fila = conexion.execute(
                "SELECT * FROM dispositivos WHERE id = ?", (dispositivo_id,)
            ).fetchone()
        return Dispositivo(fila["id"], fila["planta_id"]) if fila else None
