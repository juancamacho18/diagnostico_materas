"""Una lectura llega desde un dispositivo: se busca a que planta
pertenece, se diagnostica y se guarda en el historial."""

from dominio.entidades import Diagnostico, Lectura
from dominio.excepciones import EspecieNoSoportadaError, PlantaNoEncontradaError
from dominio.puertos.entrada import RegistrarLecturaPort
from dominio.puertos.salida import (
    DispositivoRepositorioPort,
    HistorialLecturasPort,
    PlantaRepositorioPort,
    TablaReferenciaPort,
)
from dominio.servicio_diagnostico import ServicioDiagnostico


class RegistrarLectura(RegistrarLecturaPort):
    def __init__(
        self,
        dispositivos: DispositivoRepositorioPort,
        plantas: PlantaRepositorioPort,
        tabla: TablaReferenciaPort,
        historial: HistorialLecturasPort,
        servicio: ServicioDiagnostico,
    ):
        self._dispositivos = dispositivos
        self._plantas = plantas
        self._tabla = tabla
        self._historial = historial
        self._servicio = servicio

    def ejecutar(self, dispositivo_id: str, lectura: Lectura) -> Diagnostico:
        dispositivo = self._dispositivos.obtener(dispositivo_id)
        planta = self._plantas.obtener(dispositivo.planta_id) if dispositivo else None
        if planta is None:
            raise PlantaNoEncontradaError(dispositivo_id)

        especie = self._tabla.obtener_por_nombre(planta.especie)
        if especie is None:
            raise EspecieNoSoportadaError(planta.especie)

        diagnostico = self._servicio.diagnosticar(especie, lectura.a_medicion(planta.especie))
        self._historial.guardar(planta.id, lectura, diagnostico.estado)
        return diagnostico
