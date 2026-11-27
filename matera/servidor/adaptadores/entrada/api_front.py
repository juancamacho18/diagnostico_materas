from flask import Blueprint, jsonify, request

from adaptadores.entrada import esquemas
from adaptadores.entrada.errores import ErrorDeEntrada
from adaptadores.entrada.seguridad import Seguridad


def cuerpo_json() -> dict:
    cuerpo = request.get_json(silent=True)
    if not isinstance(cuerpo, dict):
        raise ErrorDeEntrada(400, "JSON_INVALIDO", "El cuerpo debe ser un objeto JSON")
    return cuerpo


def crear_blueprint(seguridad: Seguridad, diagnosticar, listar_especies, registrar_usuario,
                    iniciar_sesion, registrar_planta, listar_plantas, consultar_estado,
                    consultar_historial, reemparejar) -> Blueprint:
    bp = Blueprint("front", __name__, url_prefix="/api")

    def usuario() -> int:
        return seguridad.desde_cabecera(request.headers.get("Authorization"), "usuario")

    @bp.get("/especies")
    def especies():
        return jsonify([esquemas.especie_a_json(e) for e in listar_especies.ejecutar()])

    @bp.post("/diagnostico")
    def diagnostico():
        especie, medicion = esquemas.diagnostico_desde_json(cuerpo_json())
        return jsonify(esquemas.diagnostico_a_json(diagnosticar.ejecutar(especie, medicion)))

    @bp.post("/usuarios")
    def crear_usuario():
        correo, clave = esquemas.credenciales_desde_json(cuerpo_json())
        return jsonify({"id": registrar_usuario.ejecutar(correo, clave)}), 201

    @bp.post("/sesion")
    def sesion():
        correo, clave = esquemas.credenciales_desde_json(cuerpo_json())
        return jsonify({"token": iniciar_sesion.ejecutar(correo, clave)})

    @bp.get("/plantas")
    def plantas():
        return jsonify([esquemas.planta_a_json(p) for p in listar_plantas.ejecutar(usuario())])

    @bp.post("/plantas")
    def crear_planta():
        uid = usuario()
        nombre, especie, dispositivo = esquemas.planta_desde_json(cuerpo_json())
        return jsonify(esquemas.planta_a_json(registrar_planta.ejecutar(uid, nombre, especie, dispositivo))), 201

    @bp.get("/plantas/<planta_id>/estado")
    def estado(planta_id):
        return jsonify(esquemas.estado_actual_a_json(consultar_estado.ejecutar(usuario(), planta_id)))

    @bp.get("/plantas/<planta_id>/lecturas")
    def lecturas(planta_id):
        uid = usuario()
        try:
            limite = min(max(int(request.args.get("limite", 50)), 1), 500)
        except ValueError:
            raise ErrorDeEntrada(400, "DATO_INVALIDO", "limite debe ser entero", {"campo": "limite"})
        return jsonify([esquemas.lectura_guardada_a_json(l)
                        for l in consultar_historial.ejecutar(uid, planta_id, limite)])

    @bp.post("/plantas/<planta_id>/reemparejar")
    def reemparejar_planta(planta_id):
        reemparejar.ejecutar(usuario(), planta_id)
        return "", 202

    return bp
