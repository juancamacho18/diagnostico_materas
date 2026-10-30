"""Traduccion entre JSON y objetos de dominio. Aqui solo se convierte
lo que llega (numeros, fechas); que una lectura sea valida y que este
en rango lo decide el dominio."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dominio.entidades import (
    Diagnostico,
    EstadoActual,
    Lectura,
    Medicion,
    Planta,
    RegistroLectura,
)
from dominio.especie import Especie
from dominio.excepciones import ParametroInvalidoError

def _numero(payload: Dict[str, Any], campo: str) -> float:
    """Solo convierte a numero. Si el valor es posible fisicamente lo
    decide el dominio."""
    if campo not in payload or payload[campo] in (None, ""):
        raise ParametroInvalidoError(campo, "ausente")
    if isinstance(payload[campo], bool):
        raise ParametroInvalidoError(campo, "no numerico")
    try:
        return float(payload[campo])
    except (TypeError, ValueError):
        raise ParametroInvalidoError(campo, "no numerico")


def _marca_de_tiempo(payload: Dict[str, Any]) -> datetime:
    """Usa la marca que trae el dispositivo (ISO 8601); si no trae
    ninguna, pone la hora del servidor."""
    texto = payload.get("marcaTiempo")
    if texto in (None, ""):
        return datetime.now(timezone.utc)
    if not isinstance(texto, str):
        raise ParametroInvalidoError("marcaTiempo", "debe ser texto ISO 8601")
    try:
        momento = datetime.fromisoformat(texto.strip().replace("Z", "+00:00"))
    except ValueError:
        raise ParametroInvalidoError("marcaTiempo", "formato ISO 8601 invalido")
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    return momento.astimezone(timezone.utc)


def medicion_desde_request(payload: Dict[str, Any]) -> Medicion:
    especie = payload.get("especie")
    if not especie or not isinstance(especie, str):
        raise ParametroInvalidoError("especie", "ausente")
    return Medicion(
        especie,
        _numero(payload, "humedad"),
        _numero(payload, "luz"),
        _numero(payload, "temperatura"),
    )


def lectura_desde_request(payload: Dict[str, Any], dispositivo_id: str) -> Lectura:
    """Cada lectura trae dispositivo, marca de tiempo y los tres valores.
    El dispositivo y la marca pueden venir en el cuerpo; el dispositivo
    de la ruta manda."""
    if payload.get("dispositivo") not in (None, dispositivo_id):
        raise ParametroInvalidoError("dispositivo", "no coincide con la ruta")
    return Lectura(
        momento=_marca_de_tiempo(payload),
        humedad=_numero(payload, "humedad"),
        luz=_numero(payload, "luz"),
        temperatura=_numero(payload, "temperatura"),
    )


def texto_requerido(payload: Dict[str, Any], campo: str) -> str:
    valor = payload.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        raise ParametroInvalidoError(campo, "ausente")
    return valor


def diagnostico_a_json(diagnostico: Diagnostico) -> Dict[str, Any]:
    return {
        "especie": diagnostico.especie,
        "estado": diagnostico.estado.value,
        "parametros": [
            {
                "nombre": p.nombre,
                "valor": p.valor,
                "unidad": p.unidad,
                "rangoOptimo": [p.rango_optimo.minimo, p.rango_optimo.maximo],
                "estado": p.estado.value,
            }
            for p in diagnostico.parametros
        ],
        "recomendaciones": diagnostico.recomendaciones,
    }


def especie_a_json(especie: Especie) -> Dict[str, Any]:
    return {
        "nombre": especie.nombre,
        "nombreComun": especie.nombre_comun,
        "rangos": {
            "humedad": [especie.humedad.minimo, especie.humedad.maximo],
            "luz": [especie.luz.minimo, especie.luz.maximo],
            "temperatura": [especie.temperatura.minimo, especie.temperatura.maximo],
        },
    }


def especies_a_json(especies: List[Especie]) -> List[Dict[str, Any]]:
    return [especie_a_json(e) for e in especies]


def planta_a_json(planta: Planta) -> Dict[str, Any]:
    return {
        "id": planta.id,
        "nombre": planta.nombre,
        "especie": planta.especie,
        "dispositivoId": planta.dispositivo_id,
    }


def registro_a_json(registro: Optional[RegistroLectura]) -> Optional[Dict[str, Any]]:
    if registro is None:
        return None
    lectura = registro.lectura
    return {
        "momento": lectura.momento.isoformat(),
        "humedad": lectura.humedad,
        "luz": lectura.luz,
        "temperatura": lectura.temperatura,
        "estado": registro.estado.value,
    }


def estado_actual_a_json(actual: EstadoActual) -> Dict[str, Any]:
    return {
        "planta": planta_a_json(actual.planta),
        "ultimaLectura": registro_a_json(actual.registro),
        "diagnostico": diagnostico_a_json(actual.diagnostico) if actual.diagnostico else None,
    }
