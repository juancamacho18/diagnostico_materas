import os
import tempfile
import unittest
from datetime import datetime, timezone

from adaptadores.salida.bd import BaseDatos
from adaptadores.salida.especies import EspeciesBd, EspeciesCsv
from adaptadores.salida.repositorios_bd import (
    DispositivosBd, HistorialBd, PlantasBd, PuntajesBd, UsuariosBd,
)
from adaptadores.salida.seguridad_salida import EmisorJwt, Hasheador
from app import RUTA_ESPECIES
from dominio.errores import CorreoYaRegistrado
from dominio.modelos import Dispositivo, Estado, EstadoDispositivo, LecturaGuardada, Medicion, Puntaje

AHORA = datetime(2026, 1, 1, 12, tzinfo=timezone.utc)


class Base(unittest.TestCase):
    def setUp(self):
        self.carpeta = tempfile.TemporaryDirectory()
        self.bd = BaseDatos(os.path.join(self.carpeta.name, "t.db"))

    def tearDown(self):
        self.carpeta.cleanup()


class PruebaRepositorios(Base):
    def test_usuarios(self):
        r = UsuariosBd(self.bd)
        u = r.crear("a@b.co", "h")
        self.assertEqual(r.por_correo("a@b.co"), u)
        self.assertIsNone(r.por_correo("z@b.co"))
        with self.assertRaises(CorreoYaRegistrado):
            r.crear("a@b.co", "h")

    def test_plantas_y_dispositivos(self):
        u = UsuariosBd(self.bd).crear("a@b.co", "h")
        plantas, disp = PlantasBd(self.bd), DispositivosBd(self.bd)
        p = plantas.crear(u.id, "Mata", "monstera deliciosa")
        self.assertRegex(p.id, r"^MAT-[0-9A-F]{6}$")
        self.assertEqual(plantas.obtener(p.id), p)
        self.assertEqual(plantas.de_usuario(u.id), [p])
        d = Dispositivo("ESP32-1", p.id, EstadoDispositivo.PENDIENTE, AHORA, 1)
        disp.guardar(d)
        self.assertEqual(disp.obtener("ESP32-1"), d)
        d2 = Dispositivo("ESP32-1", p.id, EstadoDispositivo.EMPAREJADO, None, 2)
        disp.guardar(d2)
        self.assertEqual(disp.de_planta(p.id), d2)

    def test_historial_ordenado(self):
        u = UsuariosBd(self.bd).crear("a@b.co", "h")
        p = PlantasBd(self.bd).crear(u.id, "Mata", "x")
        h = HistorialBd(self.bd)
        for i in range(3):
            h.agregar(p.id, LecturaGuardada(AHORA.replace(minute=i), Medicion(i, 1, 1), Estado.SALUDABLE))
        self.assertEqual([l.medicion.humedad for l in h.recientes(p.id, 2)], [2, 1])

    def test_puntajes(self):
        u = UsuariosBd(self.bd).crear("a@b.co", "h")
        p = PlantasBd(self.bd).crear(u.id, "Mata", "x")
        r = PuntajesBd(self.bd)
        self.assertEqual(r.obtener(p.id), Puntaje(p.id))
        s = Puntaje(p.id, 20, Estado.CRITICO, AHORA, AHORA)
        r.guardar(s)
        r.guardar(s)
        self.assertEqual(r.obtener(p.id), s)


class PruebaEspecies(Base):
    def test_csv_y_bd_son_intercambiables(self):
        csv = EspeciesCsv(str(RUTA_ESPECIES))
        bd = EspeciesBd(self.bd, csv)
        self.assertGreaterEqual(len(csv.listar()), 5)
        self.assertEqual(csv.obtener("monstera deliciosa"), bd.obtener("monstera deliciosa"))
        self.assertEqual(sorted(e.nombre for e in csv.listar()), sorted(e.nombre for e in bd.listar()))
        self.assertIsNone(bd.obtener("nada"))
        EspeciesBd(self.bd, csv)
        self.assertEqual(len(bd.listar()), len(csv.listar()))


class PruebaSeguridad(unittest.TestCase):
    def test_emisor(self):
        e = EmisorJwt("x" * 32)
        self.assertEqual(e.verificar(e.para_usuario(7))["sub"], "7")
        d = e.verificar(e.para_dispositivo("ESP32-1", 3))
        self.assertEqual((d["tipo"], d["gen"]), ("dispositivo", 3))
        self.assertIsNone(e.verificar("basura"))
        self.assertIsNone(EmisorJwt("y" * 32).verificar(e.para_usuario(1)))
        with self.assertRaises(ValueError):
            EmisorJwt("corto")

    def test_hasheador(self):
        h = Hasheador()
        hash_ = h.hashear("clave")
        self.assertNotEqual(hash_, "clave")
        self.assertTrue(h.coincide("clave", hash_))
        self.assertFalse(h.coincide("otra", hash_))


if __name__ == "__main__":
    unittest.main()
