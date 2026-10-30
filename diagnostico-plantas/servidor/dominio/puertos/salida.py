"""
Puertos de salida: lo que el dominio necesita del mundo exterior.
Los declara el dominio y los implementan los adaptadores de
adaptadores/salida/. El dominio no sabe si detras hay un CSV, una
base de datos o un doble de prueba.

Son interfaces chicas y separadas (en vez de un "Repositorio" que lo
hace todo) para que cada caso de uso dependa solo de lo que usa.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from dominio.entidades import (
    Dispositivo,
    EstadoPlanta,
    Lectura,
    Planta,
    RegistroLectura,
    Usuario,
)
from dominio.especie import Especie


class TablaReferenciaPort(ABC):
    @abstractmethod
    def obtener_por_nombre(self, nombre: str) -> Optional[Especie]:
        """Devuelve la Especie si existe, o None si no esta soportada."""
        raise NotImplementedError


class CatalogoEspeciesPort(ABC):
    @abstractmethod
    def listar_todas(self) -> List[Especie]:
        raise NotImplementedError


class HistorialLecturasPort(ABC):
    @abstractmethod
    def iniciar(self, planta_id: str) -> None:
        """Deja listo el registro de lecturas de una planta nueva."""
        raise NotImplementedError

    @abstractmethod
    def guardar(self, planta_id: str, lectura: Lectura, estado: EstadoPlanta) -> None:
        raise NotImplementedError

    @abstractmethod
    def ultima(self, planta_id: str) -> Optional[RegistroLectura]:
        raise NotImplementedError

    @abstractmethod
    def listar(self, planta_id: str, limite: int) -> List[RegistroLectura]:
        """Las mas recientes primero."""
        raise NotImplementedError


class PlantaRepositorioPort(ABC):
    @abstractmethod
    def guardar(self, planta: Planta) -> None:
        raise NotImplementedError

    @abstractmethod
    def obtener(self, planta_id: str) -> Optional[Planta]:
        raise NotImplementedError

    @abstractmethod
    def listar_por_usuario(self, usuario_id: str) -> List[Planta]:
        raise NotImplementedError


class DispositivoRepositorioPort(ABC):
    @abstractmethod
    def registrar(self, dispositivo: Dispositivo) -> None:
        raise NotImplementedError

    @abstractmethod
    def obtener(self, dispositivo_id: str) -> Optional[Dispositivo]:
        raise NotImplementedError


class UsuarioRepositorioPort(ABC):
    @abstractmethod
    def guardar(self, usuario: Usuario) -> None:
        raise NotImplementedError

    @abstractmethod
    def obtener_por_correo(self, correo: str) -> Optional[Usuario]:
        raise NotImplementedError


class HasheadorClavePort(ABC):
    @abstractmethod
    def hashear(self, clave: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def verificar(self, clave: str, clave_hash: str) -> bool:
        raise NotImplementedError


class EmisorTokenPort(ABC):
    """Crea los tokens. Verificarlos NO es asunto del dominio: lo hace
    el adaptador de entrada y el caso de uso recibe una identidad ya
    verificada."""

    @abstractmethod
    def emitir_para_usuario(self, usuario_id: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def emitir_para_dispositivo(self, dispositivo_id: str) -> str:
        raise NotImplementedError
