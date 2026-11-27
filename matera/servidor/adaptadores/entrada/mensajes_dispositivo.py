from adaptadores.entrada.errores import cuerpo_de_error, describir


def error(codigo: str, mensaje: str, detalle: dict | None = None) -> dict:
    return {"tipo": "error", **cuerpo_de_error(codigo, mensaje, detalle)}


def error_de_dominio(e: Exception) -> dict:
    return {"tipo": "error", **describir(e)[1]}
