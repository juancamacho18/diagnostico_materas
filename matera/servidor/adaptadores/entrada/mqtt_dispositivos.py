import json

import paho.mqtt.client as paho

from adaptadores.entrada import esquemas
from adaptadores.entrada.mensajes_dispositivo import error, error_de_dominio
from adaptadores.entrada.seguridad import Seguridad
from dominio.errores import ErrorDeDominio

RAIZ = "matera"
SUSCRIPCIONES = (f"{RAIZ}/+/emparejar", f"{RAIZ}/+/lectura")


def tema_de_respuesta(dispositivo: str) -> str:
    return f"{RAIZ}/{dispositivo}/respuesta"


class CanalMqtt:
    """Lógica del canal sin red: recibe (tema, carga) y publica por la función inyectada."""

    def __init__(self, seguridad: Seguridad, registrar_lectura, emparejar, publicar):
        self._seguridad = seguridad
        self._registrar_lectura = registrar_lectura
        self._emparejar = emparejar
        self._publicar = publicar

    def al_recibir(self, tema: str, carga: bytes) -> None:
        partes = tema.split("/")
        if len(partes) != 3 or partes[0] != RAIZ or partes[2] not in ("emparejar", "lectura"):
            return
        dispositivo, accion = partes[1], partes[2]

        def responder(cuerpo):
            self._publicar(tema_de_respuesta(dispositivo), json.dumps(cuerpo))

        try:
            mensaje = json.loads(carga) if carga else {}
        except (TypeError, ValueError):
            mensaje = None
        if not isinstance(mensaje, dict):
            return responder(error("MENSAJE_INVALIDO", "La carga debe ser un objeto JSON"))
        try:
            if accion == "emparejar":
                responder({"tipo": "token", "token": self._emparejar.ejecutar(dispositivo)})
            else:
                self._lectura(dispositivo, mensaje, responder)
        except ErrorDeDominio as e:
            responder(error_de_dominio(e))

    def _lectura(self, dispositivo, mensaje, responder):
        token = mensaje.get("token")
        identidad = self._seguridad.identidad_de_token(token, "dispositivo") if isinstance(token, str) else None
        if identidad is None or identidad != dispositivo:
            return responder(error("TOKEN_INVALIDO", "Token de dispositivo inválido o vencido"))
        lectura = esquemas.lectura_desde_json({k: v for k, v in mensaje.items() if k != "token"}, dispositivo)
        resultado = self._registrar_lectura.ejecutar(dispositivo, lectura)
        responder({"tipo": "ok", **esquemas.resultado_lectura_a_json(resultado)})


class ClienteMqtt:
    def __init__(self, host: str, puerto: int, seguridad: Seguridad, registrar_lectura, emparejar,
                 usuario: str | None = None, clave: str | None = None):
        self._host, self._puerto = host, puerto
        self._cliente = paho.Client(paho.CallbackAPIVersion.VERSION2, client_id="matera-servidor")
        if usuario:
            self._cliente.username_pw_set(usuario, clave)
        self._canal = CanalMqtt(seguridad, registrar_lectura, emparejar, self._publicar)
        self._cliente.reconnect_delay_set(1, 30)
        self._cliente.on_connect = self._al_conectar
        self._cliente.on_message = lambda c, u, m: self._canal.al_recibir(m.topic, m.payload)

    def _al_conectar(self, cliente, userdata, flags, codigo, propiedades):
        for tema in SUSCRIPCIONES:
            cliente.subscribe(tema, qos=1)

    def _publicar(self, tema: str, carga: str) -> None:
        self._cliente.publish(tema, carga, qos=1, retain=False)

    def iniciar(self) -> None:
        self._cliente.connect_async(self._host, self._puerto)
        self._cliente.loop_start()

    def detener(self) -> None:
        self._cliente.loop_stop()
        self._cliente.disconnect()
