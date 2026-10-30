import os
import sqlite3
import tempfile
import unittest
from contextlib import closing

from adaptadores.salida.emisor_jwt import EmisorJWT
from app import crear_app

SECRETO = "secreto-de-prueba-con-longitud-suficiente"


class PruebaApi(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.app = crear_app(
            tipo_tabla="csv",
            ruta_bd=os.path.join(self.carpeta.name, "prueba.db"),
            secreto=SECRETO,
        )
        self.cliente = self.app.test_client()

    def tearDown(self):
        self.carpeta.cleanup()

    def registrar_y_entrar(self, correo="ana@correo.com", clave="clave123"):
        self.cliente.post("/api/v1/auth/registro", json={"correo": correo, "clave": clave})
        token = self.cliente.post(
            "/api/v1/auth/login", json={"correo": correo, "clave": clave}
        ).get_json()["token"]
        return {"Authorization": f"Bearer {token}"}

    def crear_planta(self, cabecera, dispositivo="ESP32-A", especie="monstera deliciosa"):
        respuesta = self.cliente.post(
            "/api/v1/plantas",
            json={"nombre": "Sala", "especie": especie, "dispositivo": dispositivo},
            headers=cabecera,
        )
        cuerpo = respuesta.get_json()
        return cuerpo["planta"]["id"], {"Authorization": f"Bearer {cuerpo['tokenDispositivo']}"}

    def enviar(self, dispositivo, cabecera, humedad=60, luz=8000, temperatura=22):
        return self.cliente.post(
            f"/api/dispositivos/{dispositivo}/lecturas",
            json={"humedad": humedad, "luz": luz, "temperatura": temperatura},
            headers=cabecera,
        )

    def test_registro_duplicado_da_409(self):
        datos = {"correo": "a@a.com", "clave": "clave123"}
        self.assertEqual(self.cliente.post("/api/v1/auth/registro", json=datos).status_code, 201)
        respuesta = self.cliente.post("/api/v1/auth/registro", json=datos)
        self.assertEqual(respuesta.status_code, 409)
        self.assertEqual(respuesta.get_json()["error"], "USUARIO_YA_EXISTE")

    def test_login_con_clave_incorrecta_da_401(self):
        self.cliente.post("/api/v1/auth/registro", json={"correo": "a@a.com", "clave": "clave123"})
        respuesta = self.cliente.post("/api/v1/auth/login", json={"correo": "a@a.com", "clave": "otra"})
        self.assertEqual(respuesta.status_code, 401)

    def test_rutas_de_usuario_sin_token_dan_401(self):
        self.assertEqual(self.cliente.get("/api/v1/plantas").status_code, 401)

    def test_token_manipulado_da_401(self):
        respuesta = self.cliente.get("/api/v1/plantas", headers={"Authorization": "Bearer basura"})
        self.assertEqual(respuesta.status_code, 401)

    def test_lectura_del_dispositivo_se_guarda_y_se_consulta(self):
        usuario = self.registrar_y_entrar()
        planta_id, dispositivo = self.crear_planta(usuario)
        self.assertEqual(self.enviar("ESP32-A", dispositivo).status_code, 201)

        estado = self.cliente.get(f"/api/v1/plantas/{planta_id}/estado", headers=usuario).get_json()
        self.assertEqual(estado["ultimaLectura"]["humedad"], 60)
        self.assertIsNotNone(estado["diagnostico"])

    def test_lectura_fuera_de_rango_de_la_especie_no_es_saludable(self):
        usuario = self.registrar_y_entrar()
        planta_id, dispositivo = self.crear_planta(usuario)
        respuesta = self.enviar("ESP32-A", dispositivo, humedad=2, luz=100, temperatura=40)
        self.assertEqual(respuesta.status_code, 201)
        self.assertNotEqual(respuesta.get_json()["estado"], "SALUDABLE")

    def test_lecturas_invalidas_dan_400(self):
        usuario = self.registrar_y_entrar()
        _, dispositivo = self.crear_planta(usuario)
        casos = [
            {"humedad": "abc", "luz": 100, "temperatura": 20},
            {"humedad": 150, "luz": 100, "temperatura": 20},
            {"humedad": 50, "luz": -5, "temperatura": 20},
            {"humedad": 50, "luz": 100},
            {},
        ]
        for caso in casos:
            respuesta = self.cliente.post(
                "/api/dispositivos/ESP32-A/lecturas", json=caso, headers=dispositivo
            )
            self.assertEqual(respuesta.status_code, 400, caso)
            self.assertEqual(respuesta.get_json()["error"], "PARAMETRO_INVALIDO")

    def test_la_lectura_trae_dispositivo_marca_de_tiempo_y_valores(self):
        usuario = self.registrar_y_entrar()
        planta_id, dispositivo = self.crear_planta(usuario)
        respuesta = self.cliente.post(
            "/api/dispositivos/ESP32-A/lecturas",
            json={
                "dispositivo": "ESP32-A", "marcaTiempo": "2026-03-01T12:00:00Z",
                "humedad": 55, "luz": 3000, "temperatura": 22,
            },
            headers=dispositivo,
        )
        self.assertEqual(respuesta.status_code, 201)
        ultima = self.cliente.get(f"/api/v1/plantas/{planta_id}/estado", headers=usuario).get_json()
        self.assertTrue(ultima["ultimaLectura"]["momento"].startswith("2026-03-01T12:00:00"))

    def test_sin_marca_de_tiempo_la_pone_el_servidor(self):
        usuario = self.registrar_y_entrar()
        planta_id, dispositivo = self.crear_planta(usuario)
        self.enviar("ESP32-A", dispositivo)
        ultima = self.cliente.get(f"/api/v1/plantas/{planta_id}/estado", headers=usuario).get_json()
        self.assertTrue(ultima["ultimaLectura"]["momento"].startswith("20"))

    def test_marca_de_tiempo_mal_escrita_da_400(self):
        usuario = self.registrar_y_entrar()
        _, dispositivo = self.crear_planta(usuario)
        respuesta = self.cliente.post(
            "/api/dispositivos/ESP32-A/lecturas",
            json={"marcaTiempo": "ayer", "humedad": 50, "luz": 500, "temperatura": 20},
            headers=dispositivo,
        )
        self.assertEqual(respuesta.status_code, 400)
        self.assertEqual(respuesta.get_json()["detalle"]["campo"], "marcaTiempo")

    def test_el_dispositivo_del_cuerpo_debe_coincidir_con_la_ruta(self):
        usuario = self.registrar_y_entrar()
        _, dispositivo = self.crear_planta(usuario)
        respuesta = self.cliente.post(
            "/api/dispositivos/ESP32-A/lecturas",
            json={"dispositivo": "ESP32-OTRO", "humedad": 50, "luz": 500, "temperatura": 20},
            headers=dispositivo,
        )
        self.assertEqual(respuesta.status_code, 400)

    def test_registrar_una_planta_crea_su_tabla_de_lecturas(self):
        usuario = self.registrar_y_entrar()
        planta_id, _ = self.crear_planta(usuario)
        with closing(sqlite3.connect(os.path.join(self.carpeta.name, "prueba.db"))) as conexion:
            tablas = {f[0] for f in conexion.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertIn("lecturas_" + planta_id.replace("-", "_"), tablas)

    def test_token_valido_de_un_dispositivo_no_registrado_da_404(self):
        token = EmisorJWT(SECRETO).emitir_para_dispositivo("ESP32-FANTASMA")
        respuesta = self.cliente.post(
            "/api/dispositivos/ESP32-FANTASMA/lecturas",
            json={"humedad": 50, "luz": 500, "temperatura": 20},
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_dispositivo_sin_token_da_401(self):
        self.assertEqual(self.enviar("ESP32-A", {}).status_code, 401)

    def test_token_de_usuario_no_sirve_en_el_endpoint_del_dispositivo(self):
        usuario = self.registrar_y_entrar()
        self.crear_planta(usuario)
        self.assertEqual(self.enviar("ESP32-A", usuario).status_code, 401)

    def test_token_de_dispositivo_no_sirve_en_rutas_de_usuario(self):
        usuario = self.registrar_y_entrar()
        planta_id, dispositivo = self.crear_planta(usuario)
        self.assertEqual(self.cliente.get("/api/v1/plantas", headers=dispositivo).status_code, 401)
        self.assertEqual(
            self.cliente.get(f"/api/v1/plantas/{planta_id}/estado", headers=dispositivo).status_code, 401
        )

    def test_token_de_un_dispositivo_no_sirve_para_otro(self):
        usuario = self.registrar_y_entrar()
        _, dispositivo_a = self.crear_planta(usuario, "ESP32-A")
        self.crear_planta(usuario, "ESP32-B")
        self.assertEqual(self.enviar("ESP32-B", dispositivo_a).status_code, 403)

    def test_dispositivo_ya_registrado_da_409(self):
        usuario = self.registrar_y_entrar()
        self.crear_planta(usuario, "ESP32-A")
        respuesta = self.cliente.post(
            "/api/v1/plantas",
            json={"nombre": "Otra", "especie": "monstera deliciosa", "dispositivo": "ESP32-A"},
            headers=usuario,
        )
        self.assertEqual(respuesta.status_code, 409)

    def test_especie_inexistente_al_registrar_da_404(self):
        usuario = self.registrar_y_entrar()
        respuesta = self.cliente.post(
            "/api/v1/plantas",
            json={"nombre": "X", "especie": "planta inventada", "dispositivo": "ESP32-Z"},
            headers=usuario,
        )
        self.assertEqual(respuesta.status_code, 404)

    def test_un_usuario_no_ve_la_planta_de_otro(self):
        ana = self.registrar_y_entrar("ana@correo.com")
        luis = self.registrar_y_entrar("luis@correo.com")
        planta_id, _ = self.crear_planta(ana)
        for ruta in ("estado", "historial"):
            respuesta = self.cliente.get(f"/api/v1/plantas/{planta_id}/{ruta}", headers=luis)
            self.assertEqual(respuesta.status_code, 403, ruta)
        self.assertEqual(self.cliente.get("/api/v1/plantas", headers=luis).get_json(), [])

    def test_planta_inexistente_da_404(self):
        usuario = self.registrar_y_entrar()
        respuesta = self.cliente.get("/api/v1/plantas/MAT-NOEXISTE/estado", headers=usuario)
        self.assertEqual(respuesta.status_code, 404)

    def test_historial_viene_del_mas_nuevo_al_mas_viejo_y_respeta_el_limite(self):
        usuario = self.registrar_y_entrar()
        planta_id, dispositivo = self.crear_planta(usuario)
        for humedad in (40, 50, 60, 70):
            self.enviar("ESP32-A", dispositivo, humedad=humedad)
        historial = self.cliente.get(
            f"/api/v1/plantas/{planta_id}/historial?limite=3", headers=usuario
        ).get_json()
        self.assertEqual([r["humedad"] for r in historial], [70, 60, 50])

    def test_estado_sin_lecturas_no_falla(self):
        usuario = self.registrar_y_entrar()
        planta_id, _ = self.crear_planta(usuario)
        estado = self.cliente.get(f"/api/v1/plantas/{planta_id}/estado", headers=usuario).get_json()
        self.assertIsNone(estado["ultimaLectura"])
        self.assertIsNone(estado["diagnostico"])

    def test_diagnostico_suelto_de_la_fase_1_sigue_funcionando(self):
        respuesta = self.cliente.post(
            "/api/v1/diagnosticos",
            json={"especie": "monstera deliciosa", "humedad": 60, "luz": 8000, "temperatura": 22},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn(respuesta.get_json()["estado"], ("SALUDABLE", "EN_RIESGO", "CRITICO"))

    def test_errores_tienen_siempre_el_mismo_formato(self):
        for respuesta in (
            self.cliente.get("/api/no-existe"),
            self.cliente.get("/api/v1/plantas"),
            self.cliente.put("/api/v1/especies"),
            self.cliente.post("/api/v1/diagnosticos", json={}),
        ):
            self.assertEqual(set(respuesta.get_json()), {"error", "mensaje", "detalle"})


class PruebaTablaIntercambiable(unittest.TestCase):
    def test_csv_y_bd_responden_igual(self):
        peticion = {"especie": "monstera deliciosa", "humedad": 30, "luz": 1000, "temperatura": 35}
        respuestas = []
        for tipo in ("csv", "bd"):
            with tempfile.TemporaryDirectory() as carpeta:
                app = crear_app(tipo_tabla=tipo, ruta_bd=os.path.join(carpeta, "t.db"), secreto="secreto-de-prueba-con-longitud-suficiente")
                cliente = app.test_client()
                diagnostico = cliente.post("/api/v1/diagnosticos", json=peticion).get_json()
                especies = cliente.get("/api/v1/especies").get_json()
                respuestas.append((diagnostico, especies))
        self.assertEqual(respuestas[0], respuestas[1])

    def test_tipo_de_tabla_desconocido_falla_al_arrancar(self):
        with tempfile.TemporaryDirectory() as carpeta:
            with self.assertRaises(ValueError):
                crear_app(tipo_tabla="excel", ruta_bd=os.path.join(carpeta, "t.db"), secreto="secreto-de-prueba-con-longitud-suficiente")


if __name__ == "__main__":
    unittest.main()
