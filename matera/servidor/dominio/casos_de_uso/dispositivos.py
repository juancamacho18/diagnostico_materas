from dominio.casos_de_uso.cuentas import VENTANA_EMPAREJAMIENTO
from dominio.errores import (
    DispositivoNoRegistrado, EmparejamientoNoDisponible, PlantaNoEncontrada,
)
from dominio.modelos import Dispositivo, EstadoDispositivo
from dominio.puertos.salida import (
    DispositivoRepositorioPuerto, EmisorTokenPuerto, PlantaRepositorioPuerto, RelojPuerto,
)


class EmparejarDispositivo:
    def __init__(self, dispositivos: DispositivoRepositorioPuerto, emisor: EmisorTokenPuerto, reloj: RelojPuerto):
        self._dispositivos = dispositivos
        self._emisor = emisor
        self._reloj = reloj

    def ejecutar(self, dispositivo_id: str) -> str:
        d = self._dispositivos.obtener(dispositivo_id)
        disponible = (
            d is not None
            and d.estado == EstadoDispositivo.PENDIENTE
            and d.ventana_hasta is not None
            and self._reloj.ahora() <= d.ventana_hasta
        )
        if not disponible:
            raise EmparejamientoNoDisponible("Emparejamiento no disponible para este dispositivo")
        self._dispositivos.guardar(Dispositivo(d.id, d.planta_id, EstadoDispositivo.EMPAREJADO, None, d.generacion))
        return self._emisor.para_dispositivo(d.id, d.generacion)


class ValidarCredencialDispositivo:
    def __init__(self, dispositivos: DispositivoRepositorioPuerto):
        self._dispositivos = dispositivos

    def ejecutar(self, dispositivo_id: str, generacion: int) -> bool:
        d = self._dispositivos.obtener(dispositivo_id)
        return d is not None and d.estado == EstadoDispositivo.EMPAREJADO and d.generacion == generacion


class ReemparejarDispositivo:
    def __init__(self, plantas: PlantaRepositorioPuerto, dispositivos: DispositivoRepositorioPuerto, reloj: RelojPuerto):
        self._plantas = plantas
        self._dispositivos = dispositivos
        self._reloj = reloj

    def ejecutar(self, usuario_id: int, planta_id: str) -> None:
        planta = self._plantas.obtener(planta_id)
        if planta is None or planta.usuario_id != usuario_id:
            raise PlantaNoEncontrada("Planta no encontrada", {"planta": planta_id})
        d = self._dispositivos.de_planta(planta_id)
        if d is None:
            raise DispositivoNoRegistrado("La planta no tiene dispositivo")
        self._dispositivos.guardar(Dispositivo(
            d.id, d.planta_id, EstadoDispositivo.PENDIENTE,
            self._reloj.ahora() + VENTANA_EMPAREJAMIENTO, d.generacion + 1,
        ))
