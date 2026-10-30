"""Diagnostico suelto (el de la Fase 1): resuelve la especie en la
tabla de referencia y delega la evaluacion al servicio de dominio."""

from dominio.entidades import Diagnostico, Medicion
from dominio.excepciones import EspecieNoSoportadaError
from dominio.puertos.entrada import DiagnosticarMedicionPort
from dominio.puertos.salida import TablaReferenciaPort
from dominio.servicio_diagnostico import ServicioDiagnostico


class DiagnosticarMedicion(DiagnosticarMedicionPort):
    def __init__(self, tabla: TablaReferenciaPort, servicio: ServicioDiagnostico):
        self._tabla = tabla
        self._servicio = servicio

    def ejecutar(self, medicion: Medicion) -> Diagnostico:
        especie = self._tabla.obtener_por_nombre(medicion.especie)
        if especie is None:
            raise EspecieNoSoportadaError(medicion.especie)
        return self._servicio.diagnosticar(especie, medicion)
