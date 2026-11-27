from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Clasificacion(str, Enum):
    BAJO = "BAJO"
    OPTIMO = "OPTIMO"
    ALTO = "ALTO"


class Estado(str, Enum):
    SALUDABLE = "SALUDABLE"
    EN_RIESGO = "EN_RIESGO"
    CRITICO = "CRITICO"


class EstadoDispositivo(str, Enum):
    PENDIENTE = "PENDIENTE"
    EMPAREJADO = "EMPAREJADO"


@dataclass(frozen=True)
class Rango:
    minimo: float
    maximo: float


@dataclass(frozen=True)
class Especie:
    nombre: str
    nombre_comun: str
    humedad: Rango
    luz: Rango
    temperatura: Rango


@dataclass(frozen=True)
class Medicion:
    humedad: float
    luz: float
    temperatura: float


@dataclass(frozen=True)
class ParametroEvaluado:
    nombre: str
    valor: float
    unidad: str
    rango: Rango
    clasificacion: Clasificacion


@dataclass(frozen=True)
class Diagnostico:
    estado: Estado
    parametros: tuple
    recomendaciones: tuple


@dataclass(frozen=True)
class Usuario:
    id: int
    correo: str
    clave_hash: str


@dataclass(frozen=True)
class Planta:
    id: str
    nombre: str
    especie: str
    usuario_id: int
    dispositivo_id: Optional[str] = None


@dataclass(frozen=True)
class Dispositivo:
    id: str
    planta_id: str
    estado: EstadoDispositivo = EstadoDispositivo.PENDIENTE
    ventana_hasta: Optional[datetime] = None
    generacion: int = 1


@dataclass(frozen=True)
class Lectura:
    dispositivo_id: str
    medicion: Medicion
    momento: Optional[datetime] = None


@dataclass(frozen=True)
class LecturaGuardada:
    momento: datetime
    medicion: Medicion
    estado: Estado


@dataclass(frozen=True)
class Puntaje:
    planta_id: str
    puntos: int = 0
    estado: Optional[Estado] = None
    cobrado_hasta: Optional[datetime] = None
    ultima: Optional[datetime] = None


@dataclass(frozen=True)
class ResultadoLectura:
    diagnostico: Diagnostico
    puntos: int
    variacion: int


@dataclass(frozen=True)
class EstadoActual:
    planta: Planta
    ultima: Optional[LecturaGuardada]
    diagnostico: Optional[Diagnostico]
    puntos: int
