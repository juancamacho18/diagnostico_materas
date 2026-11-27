from datetime import datetime, timezone

from dominio.errores import DatoInvalido, ParametroAusente, ValorNoNumerico
from dominio.modelos import Lectura, Medicion

CAMPOS = ("humedad", "luz", "temperatura")


def _numero(cuerpo: dict, campo: str) -> float:
    if campo not in cuerpo or cuerpo[campo] is None:
        raise ParametroAusente(f"Falta {campo}", {"campo": campo})
    valor = cuerpo[campo]
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValorNoNumerico(f"{campo} no es numérico", {"campo": campo})
    return float(valor)


def _texto(cuerpo: dict, campo: str) -> str:
    valor = cuerpo.get(campo)
    if valor is None:
        raise ParametroAusente(f"Falta {campo}", {"campo": campo})
    if not isinstance(valor, str) or not valor.strip():
        raise DatoInvalido(f"{campo} inválido", {"campo": campo})
    return valor.strip()


def medicion_desde_json(cuerpo: dict) -> Medicion:
    return Medicion(*(_numero(cuerpo, c) for c in CAMPOS))


def diagnostico_desde_json(cuerpo: dict) -> tuple[str, Medicion]:
    return _texto(cuerpo, "especie"), medicion_desde_json(cuerpo)


def credenciales_desde_json(cuerpo: dict) -> tuple[str, str]:
    return _texto(cuerpo, "correo"), _texto(cuerpo, "clave")


def planta_desde_json(cuerpo: dict) -> tuple[str, str, str]:
    return _texto(cuerpo, "nombre"), _texto(cuerpo, "especie"), _texto(cuerpo, "dispositivo")


def lectura_desde_json(cuerpo: dict, dispositivo_id: str) -> Lectura:
    momento = None
    if cuerpo.get("marcaTiempo") is not None:
        try:
            momento = datetime.fromisoformat(str(cuerpo["marcaTiempo"]).replace("Z", "+00:00"))
        except ValueError:
            raise DatoInvalido("marcaTiempo inválida", {"campo": "marcaTiempo"})
        if momento.tzinfo is None:
            momento = momento.replace(tzinfo=timezone.utc)
    return Lectura(_texto(cuerpo, "dispositivo"), medicion_desde_json(cuerpo), momento)


def rango_a_json(r) -> dict:
    return {"minimo": r.minimo, "maximo": r.maximo}


def especie_a_json(e) -> dict:
    return {
        "especie": e.nombre, "nombreComun": e.nombre_comun,
        "humedad": rango_a_json(e.humedad), "luz": rango_a_json(e.luz),
        "temperatura": rango_a_json(e.temperatura),
    }


def diagnostico_a_json(d) -> dict:
    return {
        "estado": d.estado.value,
        "parametros": [
            {"nombre": p.nombre, "valor": p.valor, "unidad": p.unidad,
             "rango": rango_a_json(p.rango), "clasificacion": p.clasificacion.value}
            for p in d.parametros
        ],
        "recomendaciones": list(d.recomendaciones),
    }


def resultado_lectura_a_json(r) -> dict:
    return {"estado": r.diagnostico.estado.value, "puntos": r.puntos, "variacion": r.variacion}


def planta_a_json(p) -> dict:
    return {"id": p.id, "nombre": p.nombre, "especie": p.especie, "dispositivo": p.dispositivo_id}


def lectura_guardada_a_json(l) -> dict:
    return {
        "momento": l.momento.isoformat(), "humedad": l.medicion.humedad, "luz": l.medicion.luz,
        "temperatura": l.medicion.temperatura, "estado": l.estado.value,
    }


def estado_actual_a_json(e) -> dict:
    return {
        "planta": planta_a_json(e.planta),
        "puntos": e.puntos,
        "ultimaLectura": lectura_guardada_a_json(e.ultima) if e.ultima else None,
        "diagnostico": diagnostico_a_json(e.diagnostico) if e.diagnostico else None,
    }
