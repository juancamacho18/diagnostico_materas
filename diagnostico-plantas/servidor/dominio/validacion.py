"""Reglas de validez de una lectura: que sea un numero y que sea
fisicamente posible. No tiene que ver con la especie, eso lo compara
el evaluador."""

import math

from dominio.excepciones import ParametroInvalidoError

LIMITES_FISICOS = {
    "humedad": (0.0, 100.0),
    "luz": (0.0, 100000.0),
    "temperatura": (-40.0, 80.0),
}


def validar_valor(campo: str, valor) -> None:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ParametroInvalidoError(campo, "no numerico")
    if not math.isfinite(valor):
        raise ParametroInvalidoError(campo, "no es un numero finito")
    minimo, maximo = LIMITES_FISICOS[campo]
    if valor < minimo or valor > maximo:
        raise ParametroInvalidoError(campo, "fuera del rango fisicamente posible")


def validar_valores(humedad, luz, temperatura) -> None:
    validar_valor("humedad", humedad)
    validar_valor("luz", luz)
    validar_valor("temperatura", temperatura)
