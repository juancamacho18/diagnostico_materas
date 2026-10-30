"""
Puertos de entrada: lo que el dominio ofrece. Cada uno es un caso de
uso; quien los llame (API del front, API de dispositivos, una prueba)
no cambia lo que hacen. Los implementan las clases de dominio/servicios/.
"""

from abc import ABC, abstractmethod
from typing import List, Tuple

from dominio.entidades import (
    Diagnostico,
    EstadoActual,
    Lectura,
    Medicion,
    Planta,
    RegistroLectura,
)
from dominio.especie import Especie


class DiagnosticarMedicionPort(ABC):
    """El diagnostico suelto de la Fase 1: una medicion y una especie."""

    @abstractmethod
    def ejecutar(self, medicion: Medicion) -> Diagnostico:
        raise NotImplementedError


class ListarEspeciesPort(ABC):
    @abstractmethod
    def ejecutar(self) -> List[Especie]:
        raise NotImplementedError


class RegistrarLecturaPort(ABC):
    @abstractmethod
    def ejecutar(self, dispositivo_id: str, lectura: Lectura) -> Diagnostico:
        raise NotImplementedError


class ConsultarEstadoPort(ABC):
    @abstractmethod
    def ejecutar(self, usuario_id: str, planta_id: str) -> EstadoActual:
        raise NotImplementedError


class ConsultarHistorialPort(ABC):
    @abstractmethod
    def ejecutar(self, usuario_id: str, planta_id: str, limite: int) -> List[RegistroLectura]:
        raise NotImplementedError


class RegistrarUsuarioPort(ABC):
    @abstractmethod
    def ejecutar(self, correo: str, clave: str) -> str:
        """Devuelve el id del usuario creado."""
        raise NotImplementedError


class IniciarSesionPort(ABC):
    @abstractmethod
    def ejecutar(self, correo: str, clave: str) -> str:
        """Devuelve el token de usuario."""
        raise NotImplementedError


class RegistrarPlantaPort(ABC):
    @abstractmethod
    def ejecutar(
        self, usuario_id: str, nombre: str, especie: str, dispositivo_id: str
    ) -> Tuple[Planta, str]:
        """Devuelve la planta creada y el token para su dispositivo."""
        raise NotImplementedError


class ListarPlantasPort(ABC):
    @abstractmethod
    def ejecutar(self, usuario_id: str) -> List[Planta]:
        raise NotImplementedError
