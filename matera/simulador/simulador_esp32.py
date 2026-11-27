"""Simula un ESP32: se empareja solo, guarda su token y manda lecturas por WebSocket, HTTP o MQTT."""

import argparse
import json
import queue
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

CARAS = {"SALUDABLE": "(^_^)", "EN_RIESGO": "(o_o)", "CRITICO": "(T_T)"}


class TransporteHttp:
    def __init__(self, servidor, dispositivo):
        self.base, self.dispositivo, self.token = servidor.rstrip("/"), dispositivo, None

    def _pedir(self, ruta, cuerpo=None, token=None):
        cabeceras = {"Content-Type": "application/json"}
        if token:
            cabeceras["Authorization"] = f"Bearer {token}"
        datos = json.dumps(cuerpo).encode() if cuerpo is not None else b"{}"
        peticion = urllib.request.Request(self.base + ruta, data=datos, headers=cabeceras, method="POST")
        try:
            with urllib.request.urlopen(peticion, timeout=10) as r:
                return {"tipo": "ok", **json.loads(r.read())}
        except urllib.error.HTTPError as e:
            return {"tipo": "error", **json.loads(e.read() or b"{}")}

    def emparejar(self):
        r = self._pedir(f"/api/dispositivos/{self.dispositivo}/emparejar")
        return r.get("token") if r["tipo"] == "ok" else r

    def usar_token(self, token):
        self.token = token
        return {"tipo": "ok"}

    def enviar(self, cuerpo):
        return self._pedir(f"/api/dispositivos/{self.dispositivo}/lecturas", cuerpo, self.token)

    def cerrar(self):
        pass


class TransporteWs:
    def __init__(self, servidor, dispositivo):
        self.url = servidor.replace("http", "ws", 1).rstrip("/") + "/ws/dispositivos"
        self.dispositivo = dispositivo
        self.canal = None

    def _decir(self, mensaje):
        from simple_websocket import Client
        if self.canal is None:
            self.canal = Client.connect(self.url)
        self.canal.send(json.dumps(mensaje))
        return json.loads(self.canal.receive(timeout=10))

    def emparejar(self):
        r = self._decir({"tipo": "emparejar", "dispositivo": self.dispositivo})
        return r.get("token") if r["tipo"] == "token" else r

    def usar_token(self, token):
        return self._decir({"tipo": "autenticar", "token": token})

    def enviar(self, cuerpo):
        return self._decir({"tipo": "lectura", **cuerpo})

    def cerrar(self):
        if self.canal is not None:
            self.canal.close()


class TransporteMqtt:
    def __init__(self, destino, dispositivo):
        import paho.mqtt.client as paho
        host, _, puerto = destino.partition(":")
        self.dispositivo, self.token, self.respuestas = dispositivo, None, queue.Queue()
        self.cliente = paho.Client(paho.CallbackAPIVersion.VERSION2, client_id=dispositivo)
        self.cliente.on_message = lambda c, u, m: self.respuestas.put(json.loads(m.payload))
        self.cliente.connect(host, int(puerto or 1883))
        self.cliente.loop_start()
        self.cliente.subscribe(f"matera/{dispositivo}/respuesta", qos=1)
        time.sleep(0.5)

    def _decir(self, accion, cuerpo):
        self.cliente.publish(f"matera/{self.dispositivo}/{accion}", json.dumps(cuerpo), qos=1)
        try:
            return self.respuestas.get(timeout=10)
        except queue.Empty:
            return {"tipo": "error", "error": "SIN_RESPUESTA"}

    def emparejar(self):
        r = self._decir("emparejar", {})
        return r.get("token") if r["tipo"] == "token" else r

    def usar_token(self, token):
        self.token = token
        return {"tipo": "ok"}

    def enviar(self, cuerpo):
        return self._decir("lectura", {"token": self.token, **cuerpo})

    def cerrar(self):
        self.cliente.loop_stop()
        self.cliente.disconnect()


def generar(azar, fuera, invalidas):
    lectura = {"humedad": round(azar.uniform(50, 68), 1), "luz": round(azar.uniform(1600, 4800)),
               "temperatura": round(azar.uniform(19, 28), 1)}
    dado = azar.random()
    if dado < invalidas:
        malo = azar.choice(["falta", "texto", "fisico"])
        if malo == "falta":
            del lectura["luz"]
        elif malo == "texto":
            lectura["humedad"] = "mojado"
        else:
            lectura["temperatura"] = 900
    elif dado < invalidas + fuera:
        lectura["humedad"] = round(azar.uniform(3, 15), 1)
        lectura["luz"] = round(azar.uniform(50, 300))
    return lectura


def mostrar(respuesta):
    if respuesta.get("tipo") == "ok":
        v = respuesta["variacion"]
        cara = CARAS.get(respuesta["estado"], "(?_?)")
        print(f"  {cara} {respuesta['puntos']} puntos ({v:+d})  {respuesta['estado']}")
    else:
        print(f"  error: {respuesta.get('error')} - {respuesta.get('mensaje', '')}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dispositivo", required=True)
    p.add_argument("--servidor", default="http://127.0.0.1:5000")
    p.add_argument("--transporte", choices=["ws", "http", "mqtt"], default="ws")
    p.add_argument("--mqtt", default="127.0.0.1:1883")
    p.add_argument("--intervalo", type=float, default=3)
    p.add_argument("--ciclos", type=int, default=0, help="0 = sin fin")
    p.add_argument("--fuera-de-rango", type=float, default=0.2, dest="fuera")
    p.add_argument("--invalidas", type=float, default=0.1)
    p.add_argument("--semilla", type=int)
    a = p.parse_args()

    azar = random.Random(a.semilla)
    archivo = Path(__file__).with_name(f".token_{a.dispositivo}")
    if a.transporte == "mqtt":
        transporte = TransporteMqtt(a.mqtt, a.dispositivo)
    elif a.transporte == "http":
        transporte = TransporteHttp(a.servidor, a.dispositivo)
    else:
        transporte = TransporteWs(a.servidor, a.dispositivo)

    def conseguir_token():
        token = transporte.emparejar()
        if not isinstance(token, str):
            sys.exit(f"No se pudo emparejar: {token.get('error')} - {token.get('mensaje')}")
        archivo.write_text(token)
        print("Emparejado: token guardado")
        return token

    try:
        ejecutar(a, azar, archivo, transporte, conseguir_token)
    except KeyboardInterrupt:
        pass
    finally:
        transporte.cerrar()


def ejecutar(a, azar, archivo, transporte, conseguir_token):
    token = archivo.read_text().strip() if archivo.exists() else conseguir_token()
    transporte.usar_token(token)
    ciclo = 0
    while a.ciclos == 0 or ciclo < a.ciclos:
        ciclo += 1
        lectura = generar(azar, a.fuera, a.invalidas)
        cuerpo = {"dispositivo": a.dispositivo, "marcaTiempo": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **lectura}
        print(f"[{ciclo}] {lectura}")
        respuesta = transporte.enviar(cuerpo)
        if respuesta.get("error") in ("TOKEN_INVALIDO", "NO_AUTENTICADO"):
            print("  token rechazado: pidiendo uno nuevo")
            archivo.unlink(missing_ok=True)
            transporte.usar_token(conseguir_token())
            respuesta = transporte.enviar(cuerpo)
        mostrar(respuesta)
        if a.ciclos == 0 or ciclo < a.ciclos:
            time.sleep(a.intervalo)


if __name__ == "__main__":
    main()
