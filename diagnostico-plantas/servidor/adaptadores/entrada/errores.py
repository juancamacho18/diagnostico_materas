"""Traduce las excepciones de dominio a respuestas HTTP con el mismo
formato de error en toda la API."""

from typing import Any, Dict, Optional

from flask import Flask, jsonify

from dominio.excepciones import (
    AccesoDenegadoError,
    CredencialesInvalidasError,
    DispositivoYaRegistradoError,
    EspecieNoSoportadaError,
    ParametroInvalidoError,
    PlantaNoEncontradaError,
    UsuarioYaExisteError,
)


def respuesta_error(codigo: str, mensaje: str, status: int, detalle: Optional[Dict[str, Any]] = None):
    cuerpo = {"error": codigo, "mensaje": mensaje, "detalle": detalle or {}}
    return jsonify(cuerpo), status


def registrar_manejadores(app: Flask) -> None:
    @app.errorhandler(ParametroInvalidoError)
    def _parametro(error):
        return respuesta_error("PARAMETRO_INVALIDO", str(error), 400, {"campo": error.campo})

    @app.errorhandler(EspecieNoSoportadaError)
    def _especie(error):
        return respuesta_error("ESPECIE_NO_SOPORTADA", str(error), 404, {"especie": error.especie})

    @app.errorhandler(PlantaNoEncontradaError)
    def _planta(error):
        return respuesta_error("PLANTA_NO_ENCONTRADA", str(error), 404)

    @app.errorhandler(AccesoDenegadoError)
    def _acceso(error):
        return respuesta_error("ACCESO_DENEGADO", str(error), 403)

    @app.errorhandler(UsuarioYaExisteError)
    def _usuario(error):
        return respuesta_error("USUARIO_YA_EXISTE", str(error), 409)

    @app.errorhandler(DispositivoYaRegistradoError)
    def _dispositivo(error):
        return respuesta_error("DISPOSITIVO_YA_REGISTRADO", str(error), 409)

    @app.errorhandler(CredencialesInvalidasError)
    def _credenciales(error):
        return respuesta_error("CREDENCIALES_INVALIDAS", str(error), 401)

    @app.errorhandler(404)
    def _ruta(_error):
        return respuesta_error("RUTA_NO_ENCONTRADA", "La ruta no existe", 404)

    @app.errorhandler(405)
    def _metodo(_error):
        return respuesta_error("METODO_NO_PERMITIDO", "Metodo no permitido", 405)
