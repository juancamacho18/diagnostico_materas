from datetime import timedelta

from dominio import reglas
from dominio.errores import DispositivoAjeno, DispositivoNoRegistrado, EspecieDesconocida, PlantaNoEncontrada
from dominio.modelos import (
    EstadoActual, Lectura, LecturaGuardada, Planta, Puntaje, ResultadoLectura,
)
from dominio.puertos.salida import (
    DispositivoRepositorioPuerto, EspecieRepositorioPuerto, HistorialPuerto,
    PlantaRepositorioPuerto, PuntajeRepositorioPuerto, RelojPuerto,
)
from dominio.puntaje import acumular


def planta_del_usuario(plantas: PlantaRepositorioPuerto, usuario_id: int, planta_id: str) -> Planta:
    planta = plantas.obtener(planta_id)
    if planta is None or planta.usuario_id != usuario_id:
        raise PlantaNoEncontrada("Planta no encontrada", {"planta": planta_id})
    return planta


class AcumularPuntaje:
    def __init__(self, puntajes: PuntajeRepositorioPuerto, reloj: RelojPuerto, periodo: timedelta):
        self._puntajes = puntajes
        self._reloj = reloj
        self._periodo = periodo

    def ejecutar(self, planta_id, estado):
        nuevo, variacion = acumular(self._puntajes.obtener(planta_id), estado, self._reloj.ahora(), self._periodo)
        self._puntajes.guardar(nuevo)
        return nuevo, variacion


class RegistrarLectura:
    def __init__(
        self, dispositivos: DispositivoRepositorioPuerto, plantas: PlantaRepositorioPuerto,
        especies: EspecieRepositorioPuerto, historial: HistorialPuerto,
        puntos: AcumularPuntaje, reloj: RelojPuerto,
    ):
        self._dispositivos = dispositivos
        self._plantas = plantas
        self._especies = especies
        self._historial = historial
        self._puntos = puntos
        self._reloj = reloj

    def ejecutar(self, dispositivo_id: str, lectura: Lectura) -> ResultadoLectura:
        if lectura.dispositivo_id != dispositivo_id:
            raise DispositivoAjeno("La lectura trae otro dispositivo", {"dispositivo": lectura.dispositivo_id})
        reglas.validar_medicion(lectura.medicion)
        dispositivo = self._dispositivos.obtener(dispositivo_id)
        if dispositivo is None:
            raise DispositivoNoRegistrado("Dispositivo no registrado", {"dispositivo": dispositivo_id})
        planta = self._plantas.obtener(dispositivo.planta_id)
        especie = self._especies.obtener(planta.especie)
        if especie is None:
            raise EspecieDesconocida(f"Especie desconocida: {planta.especie}", {"especie": planta.especie})
        diagnostico = reglas.diagnosticar(especie, lectura.medicion)
        momento = lectura.momento or self._reloj.ahora()
        self._historial.agregar(planta.id, LecturaGuardada(momento, lectura.medicion, diagnostico.estado))
        puntaje, variacion = self._puntos.ejecutar(planta.id, diagnostico.estado)
        return ResultadoLectura(diagnostico, puntaje.puntos, variacion)


class ConsultarEstado:
    def __init__(
        self, plantas: PlantaRepositorioPuerto, especies: EspecieRepositorioPuerto,
        historial: HistorialPuerto, puntajes: PuntajeRepositorioPuerto,
    ):
        self._plantas = plantas
        self._especies = especies
        self._historial = historial
        self._puntajes = puntajes

    def ejecutar(self, usuario_id: int, planta_id: str) -> EstadoActual:
        planta = planta_del_usuario(self._plantas, usuario_id, planta_id)
        recientes = self._historial.recientes(planta.id, 1)
        ultima = recientes[0] if recientes else None
        especie = self._especies.obtener(planta.especie)
        diagnostico = reglas.diagnosticar(especie, ultima.medicion) if ultima and especie else None
        return EstadoActual(planta, ultima, diagnostico, self._puntajes.obtener(planta.id).puntos)


class ConsultarHistorial:
    def __init__(self, plantas: PlantaRepositorioPuerto, historial: HistorialPuerto):
        self._plantas = plantas
        self._historial = historial

    def ejecutar(self, usuario_id: int, planta_id: str, limite: int) -> list[LecturaGuardada]:
        planta = planta_del_usuario(self._plantas, usuario_id, planta_id)
        return self._historial.recientes(planta.id, limite)
