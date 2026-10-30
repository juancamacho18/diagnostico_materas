"""API REST que consume el front. Cada ruta valida lo que llega, llama
a un puerto de entrada y devuelve JSON."""

from flask import Blueprint, g, jsonify, request

from adaptadores.entrada import dtos
from adaptadores.entrada.seguridad import Seguridad
from dominio.puertos.entrada import (
    ConsultarEstadoPort,
    ConsultarHistorialPort,
    DiagnosticarMedicionPort,
    IniciarSesionPort,
    ListarEspeciesPort,
    ListarPlantasPort,
    RegistrarPlantaPort,
    RegistrarUsuarioPort,
)

_LIMITE_HISTORIAL = 200


def crear_blueprint(
    seguridad: Seguridad,
    diagnosticar: DiagnosticarMedicionPort,
    listar_especies: ListarEspeciesPort,
    registrar_usuario: RegistrarUsuarioPort,
    iniciar_sesion: IniciarSesionPort,
    registrar_planta: RegistrarPlantaPort,
    listar_plantas: ListarPlantasPort,
    consultar_estado: ConsultarEstadoPort,
    consultar_historial: ConsultarHistorialPort,
) -> Blueprint:
    bp = Blueprint("api_front", __name__, url_prefix="/api/v1")

    def _cuerpo():
        return request.get_json(silent=True) or {}

    @bp.route("/diagnosticos", methods=["POST"])
    def diagnosticos():
        medicion = dtos.medicion_desde_request(_cuerpo())
        return jsonify(dtos.diagnostico_a_json(diagnosticar.ejecutar(medicion)))

    @bp.route("/especies", methods=["GET"])
    def especies():
        return jsonify(dtos.especies_a_json(listar_especies.ejecutar()))

    @bp.route("/auth/registro", methods=["POST"])
    def registro():
        cuerpo = _cuerpo()
        usuario_id = registrar_usuario.ejecutar(
            dtos.texto_requerido(cuerpo, "correo"), dtos.texto_requerido(cuerpo, "clave")
        )
        return jsonify({"id": usuario_id}), 201

    @bp.route("/auth/login", methods=["POST"])
    def login():
        cuerpo = _cuerpo()
        token = iniciar_sesion.ejecutar(
            dtos.texto_requerido(cuerpo, "correo"), dtos.texto_requerido(cuerpo, "clave")
        )
        return jsonify({"token": token})

    @bp.route("/plantas", methods=["POST"])
    @seguridad.requiere_usuario
    def crear_planta():
        cuerpo = _cuerpo()
        planta, token_dispositivo = registrar_planta.ejecutar(
            g.usuario_id,
            dtos.texto_requerido(cuerpo, "nombre"),
            dtos.texto_requerido(cuerpo, "especie"),
            dtos.texto_requerido(cuerpo, "dispositivo"),
        )
        return jsonify({"planta": dtos.planta_a_json(planta), "tokenDispositivo": token_dispositivo}), 201

    @bp.route("/plantas", methods=["GET"])
    @seguridad.requiere_usuario
    def plantas():
        return jsonify([dtos.planta_a_json(p) for p in listar_plantas.ejecutar(g.usuario_id)])

    @bp.route("/plantas/<planta_id>/estado", methods=["GET"])
    @seguridad.requiere_usuario
    def estado(planta_id):
        return jsonify(dtos.estado_actual_a_json(consultar_estado.ejecutar(g.usuario_id, planta_id)))

    @bp.route("/plantas/<planta_id>/historial", methods=["GET"])
    @seguridad.requiere_usuario
    def historial(planta_id):
        limite = request.args.get("limite", default=20, type=int)
        limite = max(1, min(limite, _LIMITE_HISTORIAL))
        registros = consultar_historial.ejecutar(g.usuario_id, planta_id, limite)
        return jsonify([dtos.registro_a_json(r) for r in registros])

    return bp
