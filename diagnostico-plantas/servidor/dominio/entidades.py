"""Objetos que representan una medicion y el resultado de evaluarla."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from dominio.especie import RangoOptimo
from dominio.excepciones import ParametroInvalidoError
from dominio.validacion import validar_valores


class EstadoParametro(str, Enum):
    BAJO = "BAJO"
    OPTIMO = "OPTIMO"
    ALTO = "ALTO"


class EstadoPlanta(str, Enum):
    SALUDABLE = "SALUDABLE"
    EN_RIESGO = "EN_RIESGO"
    CRITICO = "CRITICO"


@dataclass(frozen=True)
class Medicion:
    """Una lectura de humedad, luz y temperatura para una especie."""
    especie: str
    humedad: float
    luz: float
    temperatura: float

    def __post_init__(self):
        if not isinstance(self.especie, str) or not self.especie.strip():
            raise ParametroInvalidoError("especie", "ausente")
        validar_valores(self.humedad, self.luz, self.temperatura)


@dataclass(frozen=True)
class ParametroEvaluado:
    nombre: str
    valor: float
    unidad: str
    rango_optimo: RangoOptimo
    estado: EstadoParametro


@dataclass(frozen=True)
class Diagnostico:
    especie: str
    estado: EstadoPlanta
    parametros: List[ParametroEvaluado] = field(default_factory=list)
    recomendaciones: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class Lectura:
    """Lo que reporta un dispositivo: tres valores y el momento en que se tomaron."""
    momento: datetime
    humedad: float
    luz: float
    temperatura: float

    def __post_init__(self):
        if not isinstance(self.momento, datetime):
            raise ParametroInvalidoError("marcaTiempo", "no es una fecha")
        validar_valores(self.humedad, self.luz, self.temperatura)

    def a_medicion(self, especie: str) -> Medicion:
        return Medicion(especie, self.humedad, self.luz, self.temperatura)


@dataclass(frozen=True)
class RegistroLectura:
    """Una lectura ya guardada en el historial, con el estado que tuvo."""
    planta_id: str
    lectura: Lectura
    estado: EstadoPlanta


@dataclass(frozen=True)
class Usuario:
    id: str
    correo: str
    clave_hash: str


@dataclass(frozen=True)
class Planta:
    id: str
    nombre: str
    especie: str
    usuario_id: str
    dispositivo_id: str


@dataclass(frozen=True)
class Dispositivo:
    """El aparato que reporta lecturas. Pertenece a una sola planta."""
    id: str
    planta_id: str


@dataclass(frozen=True)
class EstadoActual:
    """Lo ultimo que se sabe de una planta. Si todavia no ha llegado
    ninguna lectura, registro y diagnostico son None."""
    planta: Planta
    registro: Optional[RegistroLectura]
    diagnostico: Optional[Diagnostico]
