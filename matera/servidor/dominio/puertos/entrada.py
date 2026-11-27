from typing import Optional, Protocol

from dominio.modelos import (
    Diagnostico, EstadoActual, Lectura, LecturaGuardada, Medicion, Planta, ResultadoLectura,
)


class DiagnosticarPuerto(Protocol):
    def ejecutar(self, especie: str, medicion: Medicion) -> Diagnostico: ...


class ListarEspeciesPuerto(Protocol):
    def ejecutar(self) -> list: ...


class RegistrarUsuarioPuerto(Protocol):
    def ejecutar(self, correo: str, clave: str) -> int: ...


class IniciarSesionPuerto(Protocol):
    def ejecutar(self, correo: str, clave: str) -> str: ...


class RegistrarPlantaPuerto(Protocol):
    def ejecutar(self, usuario_id: int, nombre: str, especie: str, dispositivo_id: str) -> Planta: ...


class ListarPlantasPuerto(Protocol):
    def ejecutar(self, usuario_id: int) -> list[Planta]: ...


class ConsultarEstadoPuerto(Protocol):
    def ejecutar(self, usuario_id: int, planta_id: str) -> EstadoActual: ...


class ConsultarHistorialPuerto(Protocol):
    def ejecutar(self, usuario_id: int, planta_id: str, limite: int) -> list[LecturaGuardada]: ...


class RegistrarLecturaPuerto(Protocol):
    def ejecutar(self, dispositivo_id: str, lectura: Lectura) -> ResultadoLectura: ...


class EmparejarDispositivoPuerto(Protocol):
    def ejecutar(self, dispositivo_id: str) -> str: ...


class ReemparejarDispositivoPuerto(Protocol):
    def ejecutar(self, usuario_id: int, planta_id: str) -> None: ...


class ValidarCredencialDispositivoPuerto(Protocol):
    def ejecutar(self, dispositivo_id: str, generacion: int) -> bool: ...
