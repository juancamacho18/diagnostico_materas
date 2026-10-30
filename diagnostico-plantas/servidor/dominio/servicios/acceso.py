"""Regla de negocio: un usuario solo ve sus propias plantas."""

from dominio.entidades import Planta
from dominio.excepciones import AccesoDenegadoError, PlantaNoEncontradaError
from dominio.puertos.salida import PlantaRepositorioPort


def planta_del_usuario(
    plantas: PlantaRepositorioPort, usuario_id: str, planta_id: str
) -> Planta:
    planta = plantas.obtener(planta_id)
    if planta is None:
        raise PlantaNoEncontradaError(planta_id)
    if planta.usuario_id != usuario_id:
        raise AccesoDenegadoError()
    return planta
