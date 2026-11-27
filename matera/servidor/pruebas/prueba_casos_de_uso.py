import unittest
from datetime import timedelta

from dominio.casos_de_uso.cuentas import (
    IniciarSesion, ListarPlantas, RegistrarPlanta, RegistrarUsuario, VENTANA_EMPAREJAMIENTO,
)
from dominio.casos_de_uso.diagnostico import Diagnosticar, ListarEspecies
from dominio.casos_de_uso.dispositivos import (
    EmparejarDispositivo, ReemparejarDispositivo, ValidarCredencialDispositivo,
)
from dominio.casos_de_uso.lecturas import (
    AcumularPuntaje, ConsultarEstado, ConsultarHistorial, RegistrarLectura,
)
from dominio.errores import (
    CorreoYaRegistrado, CredencialesInvalidas, DatoInvalido, DispositivoAjeno,
    DispositivoNoRegistrado, DispositivoYaRegistrado, EmparejamientoNoDisponible,
    EspecieDesconocida, PlantaNoEncontrada, ValorFueraDeRangoFisico,
)
from dominio.modelos import Estado, Lectura, Medicion
from pruebas import dobles as d

BUENA = Medicion(60, 3000, 22)
MALA = Medicion(10, 3000, 22)


class Base(unittest.TestCase):
    def setUp(self):
        self.reloj = d.RelojFalso()
        self.especies = d.EspeciesFalsas()
        self.usuarios = d.UsuariosFalsos()
        self.plantas = d.PlantasFalsas()
        self.dispositivos = d.DispositivosFalsos()
        self.historial = d.HistorialFalso()
        self.puntajes = d.PuntajesFalsos()
        self.emisor = d.EmisorFalso()
        self.hash = d.HasheadorFalso()
        self.registrar_usuario = RegistrarUsuario(self.usuarios, self.hash)
        self.registrar_planta = RegistrarPlanta(self.plantas, self.dispositivos, self.especies, self.reloj)
        self.emparejar = EmparejarDispositivo(self.dispositivos, self.emisor, self.reloj)
        self.reemparejar = ReemparejarDispositivo(self.plantas, self.dispositivos, self.reloj)
        puntos = AcumularPuntaje(self.puntajes, self.reloj, timedelta(seconds=300))
        self.lectura = RegistrarLectura(
            self.dispositivos, self.plantas, self.especies, self.historial, puntos, self.reloj)

    def planta(self, usuario=1, dispositivo="ESP32-A"):
        return self.registrar_planta.ejecutar(usuario, "Mi mata", "monstera", dispositivo)


class PruebaDiagnosticar(Base):
    def test_diagnostica(self):
        self.assertEqual(Diagnosticar(self.especies).ejecutar("monstera", BUENA).estado, Estado.SALUDABLE)

    def test_especie_desconocida(self):
        with self.assertRaises(EspecieDesconocida):
            Diagnosticar(self.especies).ejecutar("x", BUENA)

    def test_valida_antes_de_buscar(self):
        with self.assertRaises(ValorFueraDeRangoFisico):
            Diagnosticar(self.especies).ejecutar("x", Medicion(500, 1, 1))

    def test_lista(self):
        self.assertEqual(len(ListarEspecies(self.especies).ejecutar()), 1)


class PruebaCuentas(Base):
    def test_registro_y_sesion(self):
        uid = self.registrar_usuario.ejecutar(" A@b.co ", "secreto")
        token = IniciarSesion(self.usuarios, self.hash, self.emisor).ejecutar("a@b.co", "secreto")
        self.assertEqual(token, f"usuario-{uid}")

    def test_correo_repetido_y_datos_malos(self):
        self.registrar_usuario.ejecutar("a@b.co", "secreto")
        with self.assertRaises(CorreoYaRegistrado):
            self.registrar_usuario.ejecutar("A@b.co", "secreto")
        with self.assertRaises(DatoInvalido):
            self.registrar_usuario.ejecutar("sin-arroba", "secreto")
        with self.assertRaises(DatoInvalido):
            self.registrar_usuario.ejecutar("c@b.co", "123")

    def test_sesion_con_clave_mala(self):
        self.registrar_usuario.ejecutar("a@b.co", "secreto")
        ini = IniciarSesion(self.usuarios, self.hash, self.emisor)
        for correo, clave in (("a@b.co", "otra"), ("z@b.co", "secreto")):
            with self.assertRaises(CredencialesInvalidas):
                ini.ejecutar(correo, clave)

    def test_planta_queda_pendiente_con_ventana(self):
        p = self.planta()
        disp = self.dispositivos.obtener("ESP32-A")
        self.assertEqual(disp.planta_id, p.id)
        self.assertEqual(disp.ventana_hasta, d.INICIO + VENTANA_EMPAREJAMIENTO)

    def test_planta_rechazos(self):
        self.planta()
        with self.assertRaises(DispositivoYaRegistrado):
            self.planta(2)
        with self.assertRaises(EspecieDesconocida):
            self.registrar_planta.ejecutar(1, "x", "nada", "ESP32-B")
        with self.assertRaises(DatoInvalido):
            self.registrar_planta.ejecutar(1, "  ", "monstera", "ESP32-B")

    def test_listar_solo_las_del_usuario(self):
        self.planta(1, "ESP32-A")
        self.planta(2, "ESP32-B")
        lista = ListarPlantas(self.plantas, self.dispositivos).ejecutar(1)
        self.assertEqual([p.dispositivo_id for p in lista], ["ESP32-A"])


class PruebaEmparejamiento(Base):
    def test_token_una_sola_vez(self):
        self.planta()
        self.assertEqual(self.emparejar.ejecutar("ESP32-A"), "dispositivo-ESP32-A-g1")
        with self.assertRaises(EmparejamientoNoDisponible):
            self.emparejar.ejecutar("ESP32-A")

    def test_ventana_vencida_y_desconocido(self):
        self.planta()
        self.reloj.avanzar(minutes=11)
        with self.assertRaises(EmparejamientoNoDisponible):
            self.emparejar.ejecutar("ESP32-A")
        with self.assertRaises(EmparejamientoNoDisponible):
            self.emparejar.ejecutar("ESP32-X")

    def test_credencial_solo_emparejado_y_misma_generacion(self):
        p = self.planta()
        valida = ValidarCredencialDispositivo(self.dispositivos).ejecutar
        self.assertFalse(valida("ESP32-A", 1))
        self.emparejar.ejecutar("ESP32-A")
        self.assertTrue(valida("ESP32-A", 1))
        self.reemparejar.ejecutar(1, p.id)
        self.assertFalse(valida("ESP32-A", 1))
        self.assertEqual(self.emparejar.ejecutar("ESP32-A"), "dispositivo-ESP32-A-g2")
        self.assertTrue(valida("ESP32-A", 2))

    def test_reemparejar_solo_el_dueno(self):
        p = self.planta()
        with self.assertRaises(PlantaNoEncontrada):
            self.reemparejar.ejecutar(2, p.id)


class PruebaLecturas(Base):
    def test_guarda_y_devuelve_resultado(self):
        p = self.planta()
        r = self.lectura.ejecutar("ESP32-A", Lectura("ESP32-A", BUENA))
        self.assertEqual(r.diagnostico.estado, Estado.SALUDABLE)
        self.assertEqual(self.historial.recientes(p.id, 5)[0].medicion, BUENA)

    def test_puntos_tras_un_periodo(self):
        self.planta()
        self.lectura.ejecutar("ESP32-A", Lectura("ESP32-A", BUENA))
        self.reloj.avanzar(seconds=300)
        r = self.lectura.ejecutar("ESP32-A", Lectura("ESP32-A", BUENA))
        self.assertEqual((r.puntos, r.variacion), (10, 10))

    def test_rechazos(self):
        self.planta()
        with self.assertRaises(DispositivoAjeno):
            self.lectura.ejecutar("ESP32-A", Lectura("ESP32-B", BUENA))
        with self.assertRaises(DispositivoNoRegistrado):
            self.lectura.ejecutar("ESP32-X", Lectura("ESP32-X", BUENA))
        with self.assertRaises(ValorFueraDeRangoFisico):
            self.lectura.ejecutar("ESP32-A", Lectura("ESP32-A", Medicion(500, 1, 1)))

    def test_lectura_invalida_no_se_guarda(self):
        p = self.planta()
        with self.assertRaises(ValorFueraDeRangoFisico):
            self.lectura.ejecutar("ESP32-A", Lectura("ESP32-A", Medicion(500, 1, 1)))
        self.assertEqual(self.historial.recientes(p.id, 5), [])

    def test_estado_e_historial_respetan_dueno(self):
        p = self.planta()
        self.lectura.ejecutar("ESP32-A", Lectura("ESP32-A", MALA))
        estado = ConsultarEstado(self.plantas, self.especies, self.historial, self.puntajes)
        self.assertEqual(estado.ejecutar(1, p.id).diagnostico.estado, Estado.EN_RIESGO)
        hist = ConsultarHistorial(self.plantas, self.historial)
        self.assertEqual(len(hist.ejecutar(1, p.id, 10)), 1)
        with self.assertRaises(PlantaNoEncontrada):
            estado.ejecutar(2, p.id)
        with self.assertRaises(PlantaNoEncontrada):
            hist.ejecutar(2, p.id, 10)

    def test_estado_sin_lecturas(self):
        p = self.planta()
        e = ConsultarEstado(self.plantas, self.especies, self.historial, self.puntajes).ejecutar(1, p.id)
        self.assertIsNone(e.ultima)
        self.assertIsNone(e.diagnostico)


if __name__ == "__main__":
    unittest.main()
