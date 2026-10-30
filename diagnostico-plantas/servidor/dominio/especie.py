"""Especie soportada por el sistema, con sus rangos optimos."""

from dataclasses import dataclass


@dataclass(frozen=True)
class RangoOptimo:
    """Rango [minimo, maximo] considerado optimo para un parametro."""
    minimo: float
    maximo: float

    def __post_init__(self):
        if self.minimo > self.maximo:
            raise ValueError("El minimo del rango no puede ser mayor que el maximo")


@dataclass(frozen=True)
class Especie:
    nombre: str
    humedad: RangoOptimo
    luz: RangoOptimo
    temperatura: RangoOptimo
    nombre_comun: str = ""
