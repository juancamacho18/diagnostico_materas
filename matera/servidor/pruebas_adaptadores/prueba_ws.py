import json
import logging
import threading
import unittest

from simple_websocket import Client
from werkzeug.serving import make_server

from pruebas_adaptadores.ayudas import BUENA, DISPOSITIVO, Entorno

logging.getLogger("werkzeug").setLevel(logging.ERROR)


class PruebaWebSocket(unittest.TestCase):
    def setUp(self):
        self.e = Entorno()
        self.servidor = make_server("127.0.0.1", 0, self.e.app, threaded=True)
        threading.Thread(target=self.servidor.serve_forever, daemon=True).start()
        self.url = f"ws://127.0.0.1:{self.servidor.server_port}/ws/dispositivos"
        self.canales = []

    def tearDown(self):
        for c in self.canales:
            c.close()
        self.servidor.shutdown()
        self.e.cerrar()

    def abrir(self):
        c = Client.connect(self.url)
        self.canales.append(c)
        return c

    def decir(self, canal, **mensaje):
        canal.send(json.dumps(mensaje))
        return json.loads(canal.receive(timeout=5))

    def emparejado(self):
        cab, pid = self.e.matera()
        c = self.abrir()
        token = self.decir(c, tipo="emparejar", dispositivo=DISPOSITIVO)["token"]
        return cab, pid, c, token

    def test_flujo_completo(self):
        cab, pid, c, token = self.emparejado()
        self.assertEqual(self.decir(c, tipo="autenticar", token=token)["tipo"], "autenticado")
        r = self.decir(c, tipo="lectura", dispositivo=DISPOSITIVO, **BUENA)
        self.assertEqual((r["tipo"], r["estado"], r["puntos"]), ("ok", "SALUDABLE", 0))
        j = self.e.http.get(f"/api/plantas/{pid}/lecturas", headers=cab).get_json()
        self.assertEqual(len(j), 1)

    def test_lectura_sin_autenticar(self):
        c = self.abrir()
        self.assertEqual(self.decir(c, tipo="lectura", dispositivo=DISPOSITIVO, **BUENA)["error"], "NO_AUTENTICADO")

    def test_token_malo(self):
        c = self.abrir()
        self.assertEqual(self.decir(c, tipo="autenticar", token="basura")["error"], "TOKEN_INVALIDO")
        self.assertEqual(self.decir(c, tipo="autenticar")["error"], "TOKEN_INVALIDO")

    def test_token_de_usuario_no_sirve(self):
        cab, *_ = self.emparejado()
        c = self.abrir()
        r = self.decir(c, tipo="autenticar", token=cab["Authorization"][7:])
        self.assertEqual(r["error"], "TOKEN_INVALIDO")

    def test_emparejar_una_sola_vez(self):
        _, _, _, _ = self.emparejado()
        r = self.decir(self.abrir(), tipo="emparejar", dispositivo=DISPOSITIVO)
        self.assertEqual(r["error"], "EMPAREJAMIENTO_NO_DISPONIBLE")

    def test_reemparejar_corta_el_canal_abierto(self):
        cab, pid, c, token = self.emparejado()
        self.decir(c, tipo="autenticar", token=token)
        self.e.http.post(f"/api/plantas/{pid}/reemparejar", headers=cab)
        r = self.decir(c, tipo="lectura", dispositivo=DISPOSITIVO, **BUENA)
        self.assertEqual(r["error"], "TOKEN_INVALIDO")
        self.assertEqual(self.decir(c, tipo="lectura", dispositivo=DISPOSITIVO, **BUENA)["error"], "NO_AUTENTICADO")

    def test_lectura_de_otro_dispositivo(self):
        _, _, c, token = self.emparejado()
        self.decir(c, tipo="autenticar", token=token)
        r = self.decir(c, tipo="lectura", dispositivo="ESP32-OTRO", **BUENA)
        self.assertEqual(r["error"], "DISPOSITIVO_AJENO")

    def test_errores_de_datos_no_cierran_el_canal(self):
        _, _, c, token = self.emparejado()
        self.decir(c, tipo="autenticar", token=token)
        r = self.decir(c, tipo="lectura", dispositivo=DISPOSITIVO, humedad=500, luz=1, temperatura=1)
        self.assertEqual(r["error"], "VALOR_FUERA_DE_RANGO_FISICO")
        self.assertEqual(self.decir(c, tipo="lectura", dispositivo=DISPOSITIVO, **BUENA)["tipo"], "ok")

    def test_mensajes_malformados(self):
        c = self.abrir()
        c.send("no es json")
        self.assertEqual(json.loads(c.receive(timeout=5))["error"], "MENSAJE_INVALIDO")
        self.assertEqual(self.decir(c, tipo="otra")["error"], "TIPO_DESCONOCIDO")
        c.send("[1]")
        self.assertEqual(json.loads(c.receive(timeout=5))["error"], "MENSAJE_INVALIDO")


if __name__ == "__main__":
    unittest.main()
