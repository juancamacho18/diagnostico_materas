import os
import sqlite3
import tempfile
import time
import unittest
from contextlib import closing
from datetime import datetime, timedelta, timezone

import jwt

from adaptadores.salida import bd
from adaptadores.salida.cuentas_bd import PlantasBD, UsuariosBD
from adaptadores.salida.dispositivos_bd import DispositivosBD
from adaptadores.salida.emisor_jwt import EmisorJWT
from adaptadores.salida.hasheador import HasheadorWerkzeug
from adaptadores.salida.historial_bd import HistorialBD
from adaptadores.salida.tabla_bd import TablaBD
from adaptadores.salida.tabla_csv import TablaCSV
from dominio.entidades import Dispositivo, EstadoPlanta, Lectura, Planta, Usuario

SECRETO = "secreto-de-prueba-con-longitud-suficiente"
RUTA_CSV = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "adaptadores", "salida", "especies.csv",
)


class BaseConBD(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self.carpeta.name, "prueba.db")
        bd.crear_tablas(self.ruta)

    def tearDown(self):
        self.carpeta.cleanup()


class PruebaTablas(BaseConBD):
    def test_csv_y_bd_entregan_las_mismas_especies(self):
        csv = TablaCSV(RUTA_CSV)
        tabla_bd = TablaBD(self.ruta)
        self.assertTrue(tabla_bd.esta_vacia())
        tabla_bd.cargar(csv.listar_todas())
        self.assertFalse(tabla_bd.esta_vacia())
        self.assertEqual(
            sorted(csv.listar_todas(), key=lambda e: e.nombre),
            sorted(tabla_bd.listar_todas(), key=lambda e: e.nombre),
        )

    def test_buscar_ignora_mayusculas_y_espacios_en_las_dos(self):
        csv = TablaCSV(RUTA_CSV)
        tabla_bd = TablaBD(self.ruta)
        tabla_bd.cargar(csv.listar_todas())
        for tabla in (csv, tabla_bd):
            self.assertIsNotNone(tabla.obtener_por_nombre("  Monstera Deliciosa "))
            self.assertIsNone(tabla.obtener_por_nombre("no existe"))


def tablas_de(ruta: str):
    with closing(sqlite3.connect(ruta)) as conexion:
        filas = conexion.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return {f[0] for f in filas}


class PruebaEsquema(BaseConBD):
    def test_existen_las_tablas_fijas(self):
        self.assertTrue({"especies", "usuarios", "plantas", "dispositivos"} <= tablas_de(self.ruta))


class PruebaHistorial(BaseConBD):
    PLANTA_1 = "MAT-000001"
    PLANTA_2 = "MAT-00A2F3"

    def lectura(self, minutos, humedad):
        momento = datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(minutes=minutos)
        return Lectura(momento, humedad, 5000, 22)

    def test_guarda_y_devuelve_lo_mas_nuevo_primero(self):
        historial = HistorialBD(self.ruta)
        for minutos, humedad in ((0, 10), (1, 20), (2, 30)):
            historial.guardar(self.PLANTA_1, self.lectura(minutos, humedad), EstadoPlanta.SALUDABLE)
        self.assertEqual(
            [r.lectura.humedad for r in historial.listar(self.PLANTA_1, 10)], [30, 20, 10]
        )
        self.assertEqual(historial.ultima(self.PLANTA_1).lectura.humedad, 30)
        self.assertEqual(len(historial.listar(self.PLANTA_1, 2)), 2)

    def test_ordena_por_la_marca_de_tiempo_y_no_por_el_orden_de_llegada(self):
        historial = HistorialBD(self.ruta)
        historial.guardar(self.PLANTA_1, self.lectura(10, 99), EstadoPlanta.SALUDABLE)
        historial.guardar(self.PLANTA_1, self.lectura(5, 11), EstadoPlanta.SALUDABLE)
        self.assertEqual(historial.ultima(self.PLANTA_1).lectura.humedad, 99)

    def test_cada_planta_tiene_su_propia_tabla(self):
        historial = HistorialBD(self.ruta)
        historial.iniciar(self.PLANTA_1)
        self.assertIn("lecturas_MAT_000001", tablas_de(self.ruta))
        self.assertNotIn("lecturas_MAT_00A2F3", tablas_de(self.ruta))
        historial.guardar(self.PLANTA_2, self.lectura(0, 10), EstadoPlanta.CRITICO)
        self.assertIn("lecturas_MAT_00A2F3", tablas_de(self.ruta))

    def test_las_lecturas_de_una_planta_no_aparecen_en_otra(self):
        historial = HistorialBD(self.ruta)
        historial.guardar(self.PLANTA_1, self.lectura(0, 10), EstadoPlanta.CRITICO)
        self.assertIsNone(historial.ultima(self.PLANTA_2))
        self.assertEqual(historial.ultima(self.PLANTA_1).estado, EstadoPlanta.CRITICO)

    def test_una_planta_sin_lecturas_devuelve_vacio(self):
        historial = HistorialBD(self.ruta)
        self.assertEqual(historial.listar(self.PLANTA_1, 5), [])
        historial.iniciar(self.PLANTA_1)
        self.assertEqual(historial.listar(self.PLANTA_1, 5), [])

    def test_un_id_con_forma_rara_no_llega_al_sql(self):
        historial = HistorialBD(self.ruta)
        malo = "MAT-000001; DROP TABLE usuarios"
        self.assertEqual(historial.listar(malo, 5), [])
        with self.assertRaises(ValueError):
            historial.guardar(malo, self.lectura(0, 10), EstadoPlanta.SALUDABLE)
        with self.assertRaises(ValueError):
            historial.iniciar(malo)
        self.assertIn("usuarios", tablas_de(self.ruta))

    def test_conserva_el_momento_con_zona_horaria(self):
        historial = HistorialBD(self.ruta)
        original = self.lectura(5, 10)
        historial.guardar(self.PLANTA_1, original, EstadoPlanta.SALUDABLE)
        self.assertEqual(historial.ultima(self.PLANTA_1).lectura.momento, original.momento)


class PruebaCuentas(BaseConBD):
    def test_usuarios(self):
        usuarios = UsuariosBD(self.ruta)
        usuarios.guardar(Usuario("U1", "a@a.com", "hash"))
        self.assertEqual(usuarios.obtener_por_correo("a@a.com").id, "U1")
        self.assertIsNone(usuarios.obtener_por_correo("otro@a.com"))

    def test_correo_repetido_lo_rechaza_la_base(self):
        usuarios = UsuariosBD(self.ruta)
        usuarios.guardar(Usuario("U1", "a@a.com", "hash"))
        with self.assertRaises(sqlite3.IntegrityError):
            usuarios.guardar(Usuario("U2", "a@a.com", "hash"))

    def test_plantas_por_usuario_con_su_dispositivo(self):
        plantas, dispositivos = PlantasBD(self.ruta), DispositivosBD(self.ruta)
        plantas.guardar(Planta("MAT-000001", "Sala", "monstera deliciosa", "U1", "ESP32-A"))
        dispositivos.registrar(Dispositivo("ESP32-A", "MAT-000001"))
        plantas.guardar(Planta("MAT-000002", "Patio", "monstera deliciosa", "U2", "ESP32-B"))
        dispositivos.registrar(Dispositivo("ESP32-B", "MAT-000002"))

        propias = plantas.listar_por_usuario("U1")
        self.assertEqual([(p.id, p.dispositivo_id) for p in propias], [("MAT-000001", "ESP32-A")])
        self.assertEqual(plantas.obtener("MAT-000002").dispositivo_id, "ESP32-B")
        self.assertIsNone(plantas.obtener("MAT-000009"))

    def test_dispositivos(self):
        dispositivos = DispositivosBD(self.ruta)
        dispositivos.registrar(Dispositivo("ESP32-A", "MAT-000001"))
        self.assertEqual(dispositivos.obtener("ESP32-A").planta_id, "MAT-000001")
        self.assertIsNone(dispositivos.obtener("ESP32-X"))

    def test_un_dispositivo_no_puede_estar_en_dos_plantas_ni_al_reves(self):
        dispositivos = DispositivosBD(self.ruta)
        dispositivos.registrar(Dispositivo("ESP32-A", "MAT-000001"))
        with self.assertRaises(sqlite3.IntegrityError):
            dispositivos.registrar(Dispositivo("ESP32-A", "MAT-000002"))
        with self.assertRaises(sqlite3.IntegrityError):
            dispositivos.registrar(Dispositivo("ESP32-B", "MAT-000001"))


class PruebaHasheador(unittest.TestCase):
    def test_no_guarda_la_clave_y_la_verifica(self):
        hasheador = HasheadorWerkzeug()
        clave_hash = hasheador.hashear("clave123")
        self.assertNotIn("clave123", clave_hash)
        self.assertTrue(hasheador.verificar("clave123", clave_hash))
        self.assertFalse(hasheador.verificar("otra", clave_hash))


class PruebaEmisorJWT(unittest.TestCase):
    def test_usuario_y_dispositivo_llevan_su_tipo(self):
        emisor = EmisorJWT(SECRETO)
        self.assertEqual(
            emisor.verificar(emisor.emitir_para_usuario("U1")), {"tipo": "usuario", "sub": "U1"}
        )
        self.assertEqual(
            emisor.verificar(emisor.emitir_para_dispositivo("ESP32-A")),
            {"tipo": "dispositivo", "sub": "ESP32-A"},
        )

    def test_rechaza_firma_ajena_basura_y_vencidos(self):
        emisor = EmisorJWT(SECRETO)
        self.assertIsNone(emisor.verificar(EmisorJWT(SECRETO + "-otro").emitir_para_usuario("U1")))
        self.assertIsNone(emisor.verificar("basura"))
        vencido = jwt.encode(
            {"tipo": "usuario", "sub": "U1", "exp": int(time.time()) - 10}, SECRETO, "HS256"
        )
        self.assertIsNone(emisor.verificar(vencido))

    def test_rechaza_tipo_desconocido_o_sin_sub(self):
        emisor = EmisorJWT(SECRETO)
        for datos in ({"tipo": "admin", "sub": "x"}, {"tipo": "usuario"}):
            token = jwt.encode({**datos, "exp": int(time.time()) + 60}, SECRETO, "HS256")
            self.assertIsNone(emisor.verificar(token))


if __name__ == "__main__":
    unittest.main()
