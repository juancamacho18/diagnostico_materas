"""API para los dispositivos (el ESP32 fisico o el simulador). Solo
acepta lecturas, y solo de la planta a la que pertenece el token."""

from flask import Blueprint, g, jsonify, request

from adaptadores.entrada import dtos
from adaptadores.entrada.errores import respuesta_error
from adaptadores.entrada.seguridad import Seguridad
from dominio.puertos.entrada import RegistrarLecturaPort


def crear_blueprint(seguridad: Seguridad, registrar_lectura: RegistrarLecturaPort) -> Blueprint:
    bp = Blueprint("api_dispositivos", __name__, url_prefix="/api/dispositivos")

    @bp.route("/<dispositivo_id>/lecturas", methods=["POST"])
    @seguridad.requiere_dispositivo
    def lecturas(dispositivo_id):
        # El token de un dispositivo no sirve para reportar por otro.
        if g.dispositivo_id != dispositivo_id:
            return respuesta_error(
                "DISPOSITIVO_NO_AUTORIZADO", "El token no corresponde a este dispositivo", 403
            )
        lectura = dtos.lectura_desde_request(request.get_json(silent=True) or {}, dispositivo_id)
        diagnostico = registrar_lectura.ejecutar(dispositivo_id, lectura)
        return jsonify({"estado": diagnostico.estado.value}), 201

    return bp
