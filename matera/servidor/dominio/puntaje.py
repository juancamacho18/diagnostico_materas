from datetime import datetime, timedelta

from dominio.modelos import Estado, Puntaje

PUNTOS_POR_PERIODO = {Estado.SALUDABLE: 10, Estado.EN_RIESGO: -5, Estado.CRITICO: -10}


def acumular(actual: Puntaje, estado: Estado, ahora: datetime, periodo: timedelta):
    racha_rota = (
        actual.estado != estado
        or actual.cobrado_hasta is None
        or actual.ultima is None
        or ahora - actual.ultima > periodo
    )
    if racha_rota:
        nuevo = Puntaje(actual.planta_id, actual.puntos, estado, ahora, ahora)
        return nuevo, 0
    periodos = (ahora - actual.cobrado_hasta) // periodo
    variacion = periodos * PUNTOS_POR_PERIODO[estado]
    puntos = max(0, actual.puntos + variacion)
    cobrado = actual.cobrado_hasta + periodos * periodo
    return Puntaje(actual.planta_id, puntos, estado, cobrado, ahora), puntos - actual.puntos
