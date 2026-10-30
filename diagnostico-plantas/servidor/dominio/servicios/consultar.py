"""Consultas del dueno de una planta: estado actual, historial y la
lista de sus plantas. Todas pasan por la regla de acceso."""

from typing import List

from dominio.entidades import EstadoActual, Planta, RegistroLectura
from dominio.excepciones import EspecieNoSoportadaError
from dominio.puertos.entrada import (
    ConsultarEstadoPort,
    ConsultarHistorialPort,
    ListarPlantasPort,
)
from dominio.puertos.salida import (
    HistorialLecturasPort,
    PlantaRepositorioPort,
    TablaReferenciaPort,
)
from dominio.servicio_diagnostico import ServicioDiagnostico
from dominio.servicios.acceso import planta_del_usuario


class ConsultarEstado(ConsultarEstadoPort):
    def __init__(
        self,
        plantas: PlantaRepositorioPort,
        tabla: TablaReferenciaPort,
        historial: HistorialLecturasPort,
        servicio: ServicioDiagnostico,
    ):
        self._plantas = plantas
        self._tabla = tabla
        self._historial = historial
        self._servicio = servicio

    def ejecutar(self, usuario_id: str, planta_id: str) -> EstadoActual:
        planta = planta_del_usuario(self._plantas, usuario_id, planta_id)
        registro = self._historial.ultima(planta.id)
        if registro is None:
            return EstadoActual(planta, None, None)

        especie = self._tabla.obtener_por_nombre(planta.especie)
        if especie is None:
            raise EspecieNoSoportadaError(planta.especie)
        diagnostico = self._servicio.diagnosticar(
            especie, registro.lectura.a_medicion(planta.especie)
        )
        return EstadoActual(planta, registro, diagnostico)


class ConsultarHistorial(ConsultarHistorialPort):
    def __init__(self, plantas: PlantaRepositorioPort, historial: HistorialLecturasPort):
        self._plantas = plantas
        self._historial = historial

    def ejecutar(self, usuario_id: str, planta_id: str, limite: int) -> List[RegistroLectura]:
        planta = planta_del_usuario(self._plantas, usuario_id, planta_id)
        return self._historial.listar(planta.id, limite)


class ListarPlantas(ListarPlantasPort):
    def __init__(self, plantas: PlantaRepositorioPort):
        self._plantas = plantas

    def ejecutar(self, usuario_id: str) -> List[Planta]:
        return self._plantas.listar_por_usuario(usuario_id)
