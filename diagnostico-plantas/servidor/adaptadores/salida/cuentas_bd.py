"""Usuarios y plantas en SQLite. Los dispositivos van en dispositivos_bd.py."""

from typing import List, Optional

from adaptadores.salida.bd import conectar
from dominio.entidades import Planta, Usuario
from dominio.puertos.salida import PlantaRepositorioPort, UsuarioRepositorioPort


class UsuariosBD(UsuarioRepositorioPort):
    def __init__(self, ruta_bd: str):
        self._ruta_bd = ruta_bd

    def guardar(self, usuario: Usuario) -> None:
        with conectar(self._ruta_bd) as conexion:
            conexion.execute(
                "INSERT INTO usuarios (id, correo, clave_hash) VALUES (?,?,?)",
                (usuario.id, usuario.correo, usuario.clave_hash),
            )

    def obtener_por_correo(self, correo: str) -> Optional[Usuario]:
        with conectar(self._ruta_bd) as conexion:
            fila = conexion.execute(
                "SELECT * FROM usuarios WHERE correo = ?", (correo,)
            ).fetchone()
        return Usuario(fila["id"], fila["correo"], fila["clave_hash"]) if fila else None


_SELECT_PLANTA = (
    "SELECT p.id, p.nombre, p.especie, p.usuario_id, COALESCE(d.id, '') AS dispositivo_id "
    "FROM plantas p LEFT JOIN dispositivos d ON d.planta_id = p.id"
)


def _a_planta(fila) -> Planta:
    return Planta(
        fila["id"], fila["nombre"], fila["especie"], fila["usuario_id"], fila["dispositivo_id"]
    )


class PlantasBD(PlantaRepositorioPort):
    def __init__(self, ruta_bd: str):
        self._ruta_bd = ruta_bd

    def guardar(self, planta: Planta) -> None:
        with conectar(self._ruta_bd) as conexion:
            conexion.execute(
                "INSERT OR REPLACE INTO plantas (id, nombre, especie, usuario_id) VALUES (?,?,?,?)",
                (planta.id, planta.nombre, planta.especie, planta.usuario_id),
            )

    def obtener(self, planta_id: str) -> Optional[Planta]:
        with conectar(self._ruta_bd) as conexion:
            fila = conexion.execute(_SELECT_PLANTA + " WHERE p.id = ?", (planta_id,)).fetchone()
        return _a_planta(fila) if fila else None

    def listar_por_usuario(self, usuario_id: str) -> List[Planta]:
        with conectar(self._ruta_bd) as conexion:
            filas = conexion.execute(
                _SELECT_PLANTA + " WHERE p.usuario_id = ? ORDER BY p.nombre", (usuario_id,)
            ).fetchall()
        return [_a_planta(f) for f in filas]
