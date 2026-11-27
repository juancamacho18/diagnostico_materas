from flask import Blueprint, jsonify, request

from adaptadores.entrada import esquemas
from adaptadores.entrada.api_front import cuerpo_json
from adaptadores.entrada.errores import ErrorDeEntrada
from adaptadores.entrada.seguridad import Seguridad


def crear_blueprint(seguridad: Seguridad, registrar_lectura, emparejar) -> Blueprint:
    bp = Blueprint("dispositivos", __name__, url_prefix="/api/dispositivos")

    @bp.post("/<dispositivo_id>/emparejar")
    def emparejar_dispositivo(dispositivo_id):
        return jsonify({"token": emparejar.ejecutar(dispositivo_id)})

    @bp.post("/<dispositivo_id>/lecturas")
    def lecturas(dispositivo_id):
        identidad = seguridad.desde_cabecera(request.headers.get("Authorization"), "dispositivo")
        if identidad != dispositivo_id:
            raise ErrorDeEntrada(403, "DISPOSITIVO_AJENO", "El token es de otro dispositivo")
        lectura = esquemas.lectura_desde_json(cuerpo_json(), dispositivo_id)
        return jsonify(esquemas.resultado_lectura_a_json(registrar_lectura.ejecutar(dispositivo_id, lectura))), 201

    return bp
