"""Prueba los casos de uso de usuarios, plantas y lecturas con dobles
en memoria. Aqui se comprueba la regla "un usuario solo ve sus plantas"."""

import unittest
from datetime import datetime, timezone

from dominio.entidades import EstadoPlanta, Lectura
from dominio.evaluador import (
    EvaluadorDeEstadoGlobal,
    EvaluadorHumedad,
    EvaluadorLuz,
    EvaluadorTemperatura,
    GeneradorDeRecomendaciones,
)
from dominio.excepciones import (
    AccesoDenegadoError,
    CredencialesInvalidasError,
    DispositivoYaRegistradoError,
    EspecieNoSoportadaError,
    ParametroInvalidoError,
    PlantaNoEncontradaError,
    UsuarioYaExisteError,
)
from dominio.servicio_diagnostico import ServicioDiagnostico
from dominio.servicios.consultar import ConsultarEstado, ConsultarHistorial
from dominio.servicios.cuentas import IniciarSesion, RegistrarPlanta, RegistrarUsuario
from dominio.servicios.registrar_lectura import RegistrarLectura
from pruebas.dobles_prueba import (
    DispositivosFalsos,
    EmisorFalso,
    HasheadorFalso,
    HistorialFalso,
    PlantasFalsas,
    TablaFalsa,
    UsuariosFalsos,
    especie_de_prueba,
)


def _lectura(humedad=30.0, luz=800.0, temperatura=22.0) -> Lectura:
    return Lectura(datetime.now(timezone.utc), humedad, luz, temperatura)


class BaseConEscenario(unittest.TestCase):
    def setUp(self):
        self.tabla = TablaFalsa({"sansevieria trifasciata": especie_de_prueba()})
        self.historial = HistorialFalso()
        self.plantas = PlantasFalsas()
        self.dispositivos = DispositivosFalsos()
        self.usuarios = UsuariosFalsos()
        self.servicio = ServicioDiagnostico(
            EvaluadorHumedad(), EvaluadorLuz(), EvaluadorTemperatura(),
            EvaluadorDeEstadoGlobal(), GeneradorDeRecomendaciones(),
        )
        self.registrar_usuario = RegistrarUsuario(self.usuarios, HasheadorFalso())
        self.registrar_planta = RegistrarPlanta(
            self.plantas, self.dispositivos, self.historial, self.tabla, EmisorFalso()
        )
        self.registrar_lectura = RegistrarLectura(
            self.dispositivos, self.plantas, self.tabla, self.historial, self.servicio
        )
        self.consultar_estado = ConsultarEstado(
            self.plantas, self.tabla, self.historial, self.servicio
        )
        self.consultar_historial = ConsultarHistorial(self.plantas, self.historial)

        self.ana = self.registrar_usuario.ejecutar("ana@correo.com", "clave123")
        self.luis = self.registrar_usuario.ejecutar("luis@correo.com", "clave456")
        self.planta, _ = self.registrar_planta.ejecutar(
            self.ana, "Sala", "sansevieria trifasciata", "ESP32-A"
        )


class PruebaCuentas(BaseConEscenario):
    def test_correo_repetido_se_rechaza(self):
        with self.assertRaises(UsuarioYaExisteError):
            self.registrar_usuario.ejecutar("ANA@correo.com", "otraclave")

    def test_clave_corta_se_rechaza(self):
        with self.assertRaises(ParametroInvalidoError):
            self.registrar_usuario.ejecutar("nuevo@correo.com", "123")

    def test_login_correcto_y_clave_equivocada(self):
        inicio = IniciarSesion(self.usuarios, HasheadorFalso(), EmisorFalso())
        self.assertEqual(inicio.ejecutar("ana@correo.com", "clave123"), "token-usuario-" + self.ana)
        with self.assertRaises(CredencialesInvalidasError):
            inicio.ejecutar("ana@correo.com", "mala")

    def test_planta_con_especie_desconocida_se_rechaza(self):
        with self.assertRaises(EspecieNoSoportadaError):
            self.registrar_planta.ejecutar(self.ana, "Otra", "no existe", "ESP32-B")

    def test_un_dispositivo_no_puede_estar_en_dos_plantas(self):
        with self.assertRaises(DispositivoYaRegistradoError):
            self.registrar_planta.ejecutar(self.ana, "Otra", "sansevieria trifasciata", "ESP32-A")

    def test_registrar_planta_asocia_el_dispositivo_y_prepara_el_historial(self):
        self.assertEqual(self.dispositivos.obtener("ESP32-A").planta_id, self.planta.id)
        self.assertEqual(self.historial.iniciadas, [self.planta.id])

    def test_registrar_planta_devuelve_token_de_dispositivo(self):
        _, token = self.registrar_planta.ejecutar(
            self.ana, "Cocina", "sansevieria trifasciata", "ESP32-C"
        )
        self.assertEqual(token, "token-dispositivo-ESP32-C")


class PruebaLecturas(BaseConEscenario):
    def test_lectura_se_diagnostica_y_queda_en_el_historial(self):
        diagnostico = self.registrar_lectura.ejecutar("ESP32-A", _lectura(humedad=5))

        self.assertEqual(diagnostico.estado, EstadoPlanta.EN_RIESGO)
        self.assertEqual(len(self.historial.registros), 1)
        self.assertEqual(self.historial.registros[0].planta_id, self.planta.id)

    def test_lectura_de_dispositivo_desconocido(self):
        with self.assertRaises(PlantaNoEncontradaError):
            self.registrar_lectura.ejecutar("ESP32-X", _lectura())
        self.assertEqual(self.historial.registros, [])

    def test_estado_sin_lecturas_viene_vacio(self):
        actual = self.consultar_estado.ejecutar(self.ana, self.planta.id)
        self.assertIsNone(actual.registro)
        self.assertIsNone(actual.diagnostico)

    def test_estado_refleja_la_ultima_lectura(self):
        self.registrar_lectura.ejecutar("ESP32-A", _lectura())
        self.registrar_lectura.ejecutar("ESP32-A", _lectura(humedad=5, luz=5, temperatura=50))

        actual = self.consultar_estado.ejecutar(self.ana, self.planta.id)

        self.assertEqual(actual.diagnostico.estado, EstadoPlanta.CRITICO)

    def test_historial_trae_las_mas_recientes_primero_y_respeta_el_limite(self):
        for humedad in (30, 31, 32):
            self.registrar_lectura.ejecutar("ESP32-A", _lectura(humedad=humedad))

        registros = self.consultar_historial.ejecutar(self.ana, self.planta.id, 2)

        self.assertEqual([r.lectura.humedad for r in registros], [32, 31])


class PruebaAcceso(BaseConEscenario):
    def test_otro_usuario_no_puede_ver_el_estado(self):
        with self.assertRaises(AccesoDenegadoError):
            self.consultar_estado.ejecutar(self.luis, self.planta.id)

    def test_otro_usuario_no_puede_ver_el_historial(self):
        with self.assertRaises(AccesoDenegadoError):
            self.consultar_historial.ejecutar(self.luis, self.planta.id, 10)

    def test_planta_inexistente(self):
        with self.assertRaises(PlantaNoEncontradaError):
            self.consultar_estado.ejecutar(self.ana, "MAT-NOEXISTE")


if __name__ == "__main__":
    unittest.main()
