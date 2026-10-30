"""Devuelve las especies soportadas para que el front arme su selector."""

from typing import List

from dominio.especie import Especie
from dominio.puertos.entrada import ListarEspeciesPort
from dominio.puertos.salida import CatalogoEspeciesPort


class ListarEspecies(ListarEspeciesPort):
    def __init__(self, catalogo: CatalogoEspeciesPort):
        self._catalogo = catalogo

    def ejecutar(self) -> List[Especie]:
        return self._catalogo.listar_todas()
