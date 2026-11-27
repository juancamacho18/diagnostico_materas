from dominio.errores import ParametroAusente, ValorFueraDeRangoFisico, ValorNoNumerico
from dominio.modelos import (
    Clasificacion, Diagnostico, Especie, Estado, Medicion, ParametroEvaluado, Rango,
)

LIMITES_FISICOS = {
    "humedad": Rango(0, 100),
    "luz": Rango(0, 100000),
    "temperatura": Rango(-20, 60),
}
UNIDADES = {"humedad": "%", "luz": "lux", "temperatura": "C"}

RECOMENDACIONES = {
    ("humedad", Clasificacion.BAJO): "Humedad baja: riega la planta.",
    ("humedad", Clasificacion.ALTO): "Humedad alta: reduce el riego y mejora el drenaje.",
    ("luz", Clasificacion.BAJO): "Poca luz: acércala a una ventana.",
    ("luz", Clasificacion.ALTO): "Demasiada luz: aléjala del sol directo.",
    ("temperatura", Clasificacion.BAJO): "Temperatura baja: llévala a un lugar más cálido.",
    ("temperatura", Clasificacion.ALTO): "Temperatura alta: llévala a un lugar más fresco.",
}


def validar_medicion(medicion: Medicion) -> None:
    for nombre, limite in LIMITES_FISICOS.items():
        valor = getattr(medicion, nombre)
        if valor is None:
            raise ParametroAusente(f"Falta {nombre}", {"campo": nombre})
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ValorNoNumerico(f"{nombre} no es numérico", {"campo": nombre})
        if not limite.minimo <= valor <= limite.maximo:
            raise ValorFueraDeRangoFisico(
                f"{nombre} fuera del rango físico ({limite.minimo} a {limite.maximo})",
                {"campo": nombre, "minimo": limite.minimo, "maximo": limite.maximo},
            )


def clasificar(valor: float, rango: Rango) -> Clasificacion:
    if valor < rango.minimo:
        return Clasificacion.BAJO
    if valor > rango.maximo:
        return Clasificacion.ALTO
    return Clasificacion.OPTIMO


def estado_global(parametros) -> Estado:
    fuera = sum(1 for p in parametros if p.clasificacion != Clasificacion.OPTIMO)
    if fuera == 0:
        return Estado.SALUDABLE
    return Estado.EN_RIESGO if fuera == 1 else Estado.CRITICO


def diagnosticar(especie: Especie, medicion: Medicion) -> Diagnostico:
    parametros = tuple(
        ParametroEvaluado(
            nombre, getattr(medicion, nombre), UNIDADES[nombre],
            getattr(especie, nombre), clasificar(getattr(medicion, nombre), getattr(especie, nombre)),
        )
        for nombre in LIMITES_FISICOS
    )
    recomendaciones = tuple(
        RECOMENDACIONES[(p.nombre, p.clasificacion)]
        for p in parametros if p.clasificacion != Clasificacion.OPTIMO
    )
    return Diagnostico(estado_global(parametros), parametros, recomendaciones)
