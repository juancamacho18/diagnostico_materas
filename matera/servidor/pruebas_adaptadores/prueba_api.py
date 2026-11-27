import unittest

import jwt

from pruebas_adaptadores.ayudas import BUENA, DISPOSITIVO, MALA, SECRETO, Entorno


class Base(unittest.TestCase):
    tipo_tabla = "csv"

    def setUp(self):
        self.e = Entorno(self.tipo_tabla)
        self.http = self.e.http

    def tearDown(self):
        self.e.cerrar()

    def lectura(self, token, cuerpo=BUENA, dispositivo=DISPOSITIVO, ruta=None):
        return self.http.post(
            f"/api/dispositivos/{ruta or dispositivo}/lecturas",
            headers={"Authorization": f"Bearer {token}"},
            json={"dispositivo": dispositivo, **cuerpo})


class PruebaDiagnostico(Base):
    def diag(self, **cambios):
        cuerpo = {"especie": "monstera deliciosa", **BUENA, **cambios}
        return self.http.post("/api/diagnostico", json=cuerpo)

    def test_saludable(self):
        r = self.diag()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["estado"], "SALUDABLE")

    def test_critico_con_recomendaciones(self):
        j = self.diag(humedad=5, luz=100).get_json()
        self.assertEqual(j["estado"], "CRITICO")
        self.assertEqual(len(j["recomendaciones"]), 2)

    def test_errores_con_cuerpo_uniforme(self):
        casos = [
            (self.diag(especie="nada"), 404, "ESPECIE_DESCONOCIDA"),
            (self.diag(humedad=None), 400, "PARAMETRO_AUSENTE"),
            (self.diag(luz="mucha"), 400, "VALOR_NO_NUMERICO"),
            (self.diag(humedad=101), 422, "VALOR_FUERA_DE_RANGO_FISICO"),
            (self.http.post("/api/diagnostico", data="no json", content_type="application/json"), 400, "JSON_INVALIDO"),
        ]
        for r, estado, codigo in casos:
            self.assertEqual((r.status_code, r.get_json()["error"]), (estado, codigo))
            self.assertEqual(set(r.get_json()), {"error", "mensaje", "detalle"})

    def test_especies(self):
        j = self.http.get("/api/especies").get_json()
        self.assertGreaterEqual(len(j), 5)
        self.assertIn("humedad", j[0])

    def test_cors(self):
        r = self.http.get("/api/especies", headers={"Origin": "http://localhost:8080"})
        self.assertIn(r.headers["Access-Control-Allow-Origin"], ("*", "http://localhost:8080"))

    def test_ruta_inexistente_devuelve_json(self):
        r = self.http.get("/nada")
        self.assertEqual(r.status_code, 404)
        self.assertIn("error", r.get_json())

    def test_con_tabla_en_bd(self):
        e = Entorno("bd")
        try:
            nombres = lambda h: sorted(x["especie"] for x in h.get("/api/especies").get_json())
            self.assertEqual(nombres(e.http), nombres(self.http))
        finally:
            e.cerrar()


class PruebaUsuariosYPlantas(Base):
    def test_registro_y_sesion(self):
        self.assertEqual(self.http.post("/api/usuarios", json={"correo": "a@b.co", "clave": "123456"}).status_code, 201)
        self.assertEqual(self.http.post("/api/usuarios", json={"correo": "a@b.co", "clave": "123456"}).status_code, 409)
        self.assertEqual(self.http.post("/api/sesion", json={"correo": "a@b.co", "clave": "mala"}).status_code, 401)
        self.assertEqual(self.http.post("/api/usuarios", json={"correo": "x", "clave": "123456"}).status_code, 400)

    def test_rutas_protegidas(self):
        self.assertEqual(self.http.get("/api/plantas").status_code, 401)
        r = self.http.get("/api/plantas", headers={"Authorization": "Bearer basura"})
        self.assertEqual(r.get_json()["error"], "TOKEN_INVALIDO")

    def test_token_de_dispositivo_no_sirve_como_usuario(self):
        self.e.matera()
        t = self.e.token_dispositivo()
        r = self.http.get("/api/plantas", headers={"Authorization": f"Bearer {t}"})
        self.assertEqual(r.status_code, 401)

    def test_crear_y_listar(self):
        cab, pid = self.e.matera()
        self.assertTrue(pid.startswith("MAT-"))
        j = self.http.get("/api/plantas", headers=cab).get_json()
        self.assertEqual([(p["id"], p["dispositivo"]) for p in j], [(pid, DISPOSITIVO)])

    def test_cada_usuario_ve_solo_lo_suyo(self):
        a, pid = self.e.matera()
        b = self.e.usuario("beto@correo.com")
        self.assertEqual(self.http.get("/api/plantas", headers=b).get_json(), [])
        self.assertEqual(self.http.get(f"/api/plantas/{pid}/estado", headers=b).status_code, 404)
        self.assertEqual(self.http.get(f"/api/plantas/{pid}/lecturas", headers=b).status_code, 404)
        self.assertEqual(self.http.post(f"/api/plantas/{pid}/reemparejar", headers=b).status_code, 404)

    def test_dispositivo_repetido_y_especie_mala(self):
        cab, _ = self.e.matera()
        r = self.http.post("/api/plantas", headers=cab, json={"nombre": "x", "especie": "monstera deliciosa", "dispositivo": DISPOSITIVO})
        self.assertEqual(r.status_code, 409)
        r = self.http.post("/api/plantas", headers=cab, json={"nombre": "x", "especie": "nada", "dispositivo": "ESP32-OTRO"})
        self.assertEqual(r.status_code, 404)


class PruebaLecturas(Base):
    def setUp(self):
        super().setUp()
        self.cab, self.pid = self.e.matera()
        self.token = self.e.token_dispositivo()

    def test_lectura_se_guarda_y_responde(self):
        r = self.lectura(self.token)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json(), {"estado": "SALUDABLE", "puntos": 0, "variacion": 0})
        estado = self.http.get(f"/api/plantas/{self.pid}/estado", headers=self.cab).get_json()
        self.assertEqual(estado["diagnostico"]["estado"], "SALUDABLE")
        self.assertEqual(estado["ultimaLectura"]["humedad"], 60)

    def test_historial_mas_reciente_primero(self):
        self.lectura(self.token, BUENA)
        self.e.reloj.avanzar(seconds=5)
        self.lectura(self.token, MALA)
        j = self.http.get(f"/api/plantas/{self.pid}/lecturas?limite=1", headers=self.cab).get_json()
        self.assertEqual([x["estado"] for x in j], ["EN_RIESGO"])
        self.assertEqual(self.http.get(f"/api/plantas/{self.pid}/lecturas?limite=x", headers=self.cab).status_code, 400)

    def test_marca_de_tiempo(self):
        self.lectura(self.token, {**BUENA, "marcaTiempo": "2026-05-01T10:00:00Z"})
        j = self.http.get(f"/api/plantas/{self.pid}/lecturas", headers=self.cab).get_json()
        self.assertTrue(j[0]["momento"].startswith("2026-05-01T10:00:00"))
        self.assertEqual(self.lectura(self.token, {**BUENA, "marcaTiempo": "ayer"}).status_code, 400)

    def test_lecturas_invalidas(self):
        for cuerpo, estado in (({**BUENA, "humedad": 500}, 422), ({**BUENA, "luz": "x"}, 400),
                               ({"humedad": 1, "luz": 1}, 400)):
            self.assertEqual(self.lectura(self.token, cuerpo).status_code, estado)
        self.assertEqual(self.http.get(f"/api/plantas/{self.pid}/lecturas", headers=self.cab).get_json(), [])

    def test_sin_token_o_con_token_ajeno(self):
        self.assertEqual(self.http.post(f"/api/dispositivos/{DISPOSITIVO}/lecturas", json=BUENA).status_code, 401)
        self.assertEqual(self.lectura(self.token, ruta="ESP32-OTRO").status_code, 403)
        self.assertEqual(self.lectura(self.token, dispositivo="ESP32-OTRO", ruta=DISPOSITIVO).status_code, 403)

    def test_token_de_usuario_no_sirve_como_dispositivo(self):
        token_usuario = self.cab["Authorization"][7:]
        self.assertEqual(self.lectura(token_usuario).status_code, 401)

    def test_token_falsificado_o_sin_generacion(self):
        falso = jwt.encode({"tipo": "dispositivo", "sub": DISPOSITIVO, "gen": 1, "exp": 9999999999}, "otro" * 10, algorithm="HS256")
        sin_gen = jwt.encode({"tipo": "dispositivo", "sub": DISPOSITIVO, "exp": 9999999999}, SECRETO, algorithm="HS256")
        for t in (falso, sin_gen):
            self.assertEqual(self.lectura(t).status_code, 401)

    def test_token_vencido(self):
        vencido = jwt.encode({"tipo": "dispositivo", "sub": DISPOSITIVO, "gen": 1, "exp": 1}, SECRETO, algorithm="HS256")
        self.assertEqual(self.lectura(vencido).status_code, 401)


class PruebaEmparejamiento(Base):
    def test_token_se_entrega_una_vez(self):
        self.e.matera()
        self.assertEqual(self.http.post(f"/api/dispositivos/{DISPOSITIVO}/emparejar").status_code, 200)
        r = self.http.post(f"/api/dispositivos/{DISPOSITIVO}/emparejar")
        self.assertEqual((r.status_code, r.get_json()["error"]), (403, "EMPAREJAMIENTO_NO_DISPONIBLE"))

    def test_desconocido_y_vencido_se_ven_igual(self):
        self.e.matera()
        self.e.reloj.avanzar(minutes=11)
        a = self.http.post(f"/api/dispositivos/{DISPOSITIVO}/emparejar")
        b = self.http.post("/api/dispositivos/ESP32-NADA/emparejar")
        self.assertEqual((a.status_code, a.get_json()), (b.status_code, b.get_json()))

    def test_token_no_se_entrega_al_crear_la_planta(self):
        self.e.usuario()
        r = self.http.post("/api/plantas", headers=self.e.usuario(),
                           json={"nombre": "x", "especie": "monstera deliciosa", "dispositivo": "ESP32-Z"})
        self.assertNotIn("token", r.get_json())

    def test_reemparejar_revoca_el_token_viejo(self):
        cab, pid = self.e.matera()
        viejo = self.e.token_dispositivo()
        self.assertEqual(self.lectura(viejo).status_code, 201)
        self.assertEqual(self.http.post(f"/api/plantas/{pid}/reemparejar", headers=cab).status_code, 202)
        self.assertEqual(self.lectura(viejo).status_code, 401)
        nuevo = self.e.token_dispositivo()
        self.assertEqual(self.lectura(nuevo).status_code, 201)
        self.assertEqual(self.lectura(viejo).status_code, 401)


class PruebaPuntos(Base):
    def test_puntos_suben_con_periodos_completos_en_verde(self):
        cab, pid = self.e.matera()
        t = self.e.token_dispositivo()
        self.lectura(t)
        self.e.reloj.avanzar(seconds=300)
        self.assertEqual(self.lectura(t).get_json()["puntos"], 10)
        self.e.reloj.avanzar(seconds=300)
        self.lectura(t)
        self.assertEqual(self.http.get(f"/api/plantas/{pid}/estado", headers=cab).get_json()["puntos"], 20)

    def test_puntos_bajan_en_rojo(self):
        _, _ = self.e.matera()
        t = self.e.token_dispositivo()
        self.lectura(t, BUENA)
        self.e.reloj.avanzar(seconds=300)
        self.lectura(t, BUENA)
        self.lectura(t, {"humedad": 5, "luz": 100, "temperatura": 22})
        self.e.reloj.avanzar(seconds=300)
        j = self.lectura(t, {"humedad": 5, "luz": 100, "temperatura": 22}).get_json()
        self.assertEqual((j["estado"], j["variacion"], j["puntos"]), ("CRITICO", -10, 0))


if __name__ == "__main__":
    unittest.main()
