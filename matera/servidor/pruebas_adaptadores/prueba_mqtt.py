import json
import queue
import time
import unittest
import warnings

import paho.mqtt.client as paho

from adaptadores.entrada.mqtt_dispositivos import CanalMqtt
from pruebas_adaptadores.ayudas import BUENA, DISPOSITIVO, Entorno
from pruebas_adaptadores.broker_de_prueba import BrokerDePrueba

OTRO = "ESP32-BBBB00000002"


class PruebaMqtt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.simplefilter("ignore", DeprecationWarning)
        cls.broker = BrokerDePrueba()
        cls.broker.iniciar()

    @classmethod
    def tearDownClass(cls):
        cls.broker.detener()

    def setUp(self):
        self.e = Entorno(mqtt=f"127.0.0.1:{self.broker.puerto}")
        self.clientes = []
        self.respuestas = queue.Queue()
        self.dispositivo = self.conectar(f"matera/{DISPOSITIVO}/respuesta", self.respuestas)
        self.otro_cola = queue.Queue()
        self.otro = self.conectar(f"matera/{OTRO}/respuesta", self.otro_cola)
        self.esperar_servidor()

    def tearDown(self):
        self.e.cerrar()
        for c in self.clientes:
            c.loop_stop()
            c.disconnect()

    def conectar(self, tema, cola):
        c = paho.Client(paho.CallbackAPIVersion.VERSION2)
        c.on_message = lambda cl, u, m: cola.put((m.topic, json.loads(m.payload), m.retain))
        c.connect("127.0.0.1", self.broker.puerto)
        c.loop_start()
        c.subscribe(tema, qos=1)
        self.clientes.append(c)
        return c

    def esperar_servidor(self):
        limite = time.time() + 10
        while time.time() < limite:
            self.dispositivo.publish(f"matera/{DISPOSITIVO}/emparejar", "[]", qos=1)
            try:
                self.respuestas.get(timeout=0.5)
                return
            except queue.Empty:
                pass
        self.fail("el servidor no se suscribió")

    def decir(self, accion, carga, cliente=None, cola=None, dispositivo=DISPOSITIVO):
        (cliente or self.dispositivo).publish(f"matera/{dispositivo}/{accion}", json.dumps(carga), qos=1)
        return (cola or self.respuestas).get(timeout=5)

    def emparejado(self, dispositivo=DISPOSITIVO):
        cab, pid = self.e.matera(dispositivo=dispositivo)
        cliente, cola = (self.dispositivo, self.respuestas) if dispositivo == DISPOSITIVO else (self.otro, self.otro_cola)
        tema, cuerpo, _ = self.decir("emparejar", {}, cliente, cola, dispositivo)
        return cab, pid, cuerpo["token"]

    def test_flujo_completo(self):
        cab, pid, token = self.emparejado()
        tema, r, retenido = self.decir("lectura", {"token": token, "dispositivo": DISPOSITIVO, **BUENA})
        self.assertEqual((tema, r["tipo"], r["estado"], retenido), (f"matera/{DISPOSITIVO}/respuesta", "ok", "SALUDABLE", False))
        self.assertEqual(len(self.e.http.get(f"/api/plantas/{pid}/lecturas", headers=cab).get_json()), 1)

    def test_token_viaja_en_la_carga_y_no_en_el_tema(self):
        _, _, token = self.emparejado()
        r = self.decir("lectura", {"dispositivo": DISPOSITIVO, **BUENA})[1]
        self.assertEqual(r["error"], "TOKEN_INVALIDO")
        self.assertEqual(self.decir("lectura", {"token": token, "dispositivo": DISPOSITIVO, **BUENA})[1]["tipo"], "ok")

    def test_token_de_otro_dispositivo_no_sirve(self):
        self.emparejado()
        _, _, token_otro = self.emparejado(OTRO)
        r = self.decir("lectura", {"token": token_otro, "dispositivo": DISPOSITIVO, **BUENA})[1]
        self.assertEqual(r["error"], "TOKEN_INVALIDO")

    def test_token_de_usuario_no_sirve(self):
        cab, _, _ = self.emparejado()
        r = self.decir("lectura", {"token": cab["Authorization"][7:], "dispositivo": DISPOSITIVO, **BUENA})[1]
        self.assertEqual(r["error"], "TOKEN_INVALIDO")

    def test_emparejar_una_vez_y_reemparejar(self):
        cab, pid, viejo = self.emparejado()
        self.assertEqual(self.decir("emparejar", {})[1]["error"], "EMPAREJAMIENTO_NO_DISPONIBLE")
        self.e.http.post(f"/api/plantas/{pid}/reemparejar", headers=cab)
        self.assertEqual(self.decir("lectura", {"token": viejo, "dispositivo": DISPOSITIVO, **BUENA})[1]["error"], "TOKEN_INVALIDO")
        nuevo = self.decir("emparejar", {})[1]["token"]
        self.assertEqual(self.decir("lectura", {"token": nuevo, "dispositivo": DISPOSITIVO, **BUENA})[1]["tipo"], "ok")

    def test_nada_se_publica_con_retain(self):
        self.emparejado()
        tardio = queue.Queue()
        self.conectar(f"matera/{DISPOSITIVO}/respuesta", tardio)
        with self.assertRaises(queue.Empty):
            tardio.get(timeout=1)

    def test_datos_invalidos(self):
        _, _, token = self.emparejado()
        r = self.decir("lectura", {"token": token, "dispositivo": DISPOSITIVO, "humedad": 500, "luz": 1, "temperatura": 1})[1]
        self.assertEqual(r["error"], "VALOR_FUERA_DE_RANGO_FISICO")
        self.dispositivo.publish(f"matera/{DISPOSITIVO}/lectura", "no json", qos=1)
        self.assertEqual(self.respuestas.get(timeout=5)[1]["error"], "MENSAJE_INVALIDO")

    def test_temas_ajenos_se_ignoran(self):
        publicados = []
        canal = CanalMqtt(None, None, None, lambda t, c: publicados.append(t))
        for tema in ("otra/cosa", "matera/x/otra", "matera/x/lectura/y"):
            canal.al_recibir(tema, b"{}")
        self.assertEqual(publicados, [])

    def test_servidor_arranca_sin_broker(self):
        e = Entorno(mqtt="127.0.0.1:1")
        try:
            self.assertEqual(e.http.get("/api/especies").status_code, 200)
        finally:
            e.cerrar()


if __name__ == "__main__":
    unittest.main()
