import json

from flask import Flask
from flask_sock import Sock
from simple_websocket import ConnectionClosed

from adaptadores.entrada import esquemas
from adaptadores.entrada.mensajes_dispositivo import error, error_de_dominio
from adaptadores.entrada.seguridad import Seguridad
from dominio.errores import ErrorDeDominio

RUTA = "/ws/dispositivos"


def registrar(app: Flask, seguridad: Seguridad, registrar_lectura, emparejar) -> None:
    sock = Sock(app)

    @sock.route(RUTA)
    def canal(ws):
        token = None

        def responder(cuerpo):
            ws.send(json.dumps(cuerpo))

        def tratar(mensaje):
            nonlocal token
            tipo = mensaje.get("tipo")
            if tipo == "emparejar":
                dispositivo = mensaje.get("dispositivo")
                if not isinstance(dispositivo, str) or not dispositivo.strip():
                    return responder(error("PARAMETRO_INVALIDO", "dispositivo ausente", {"campo": "dispositivo"}))
                responder({"tipo": "token", "token": emparejar.ejecutar(dispositivo.strip())})
            elif tipo == "autenticar":
                candidato = mensaje.get("token")
                dispositivo = seguridad.identidad_de_token(candidato, "dispositivo") if isinstance(candidato, str) else None
                token = candidato if dispositivo else None
                if dispositivo is None:
                    return responder(error("TOKEN_INVALIDO", "Token de dispositivo inválido o vencido"))
                responder({"tipo": "autenticado", "dispositivo": dispositivo})
            elif tipo == "lectura":
                if token is None:
                    return responder(error("NO_AUTENTICADO", "Primero hay que autenticar"))
                dispositivo = seguridad.identidad_de_token(token, "dispositivo")
                if dispositivo is None:
                    token = None
                    return responder(error("TOKEN_INVALIDO", "Token de dispositivo inválido o vencido"))
                lectura = esquemas.lectura_desde_json({k: v for k, v in mensaje.items() if k != "tipo"}, dispositivo)
                resultado = registrar_lectura.ejecutar(dispositivo, lectura)
                responder({"tipo": "ok", **esquemas.resultado_lectura_a_json(resultado)})
            else:
                responder(error("TIPO_DESCONOCIDO", f"Tipo de mensaje no reconocido: {tipo!r}"))

        while True:
            try:
                texto = ws.receive()
            except ConnectionClosed:
                break
            try:
                mensaje = json.loads(texto)
            except (TypeError, ValueError):
                mensaje = None
            if not isinstance(mensaje, dict):
                responder(error("MENSAJE_INVALIDO", "El mensaje debe ser un objeto JSON"))
                continue
            try:
                tratar(mensaje)
            except ErrorDeDominio as e:
                responder(error_de_dominio(e))
