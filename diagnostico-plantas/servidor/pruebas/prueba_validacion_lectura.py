"""Lecturas validas, fuera de rango de la especie e invalidas, probadas
solo con el dominio y dobles en memoria."""

import unittest
from datetime import datetime, timezone

from dominio.entidades import EstadoPlanta, Lectura, Medicion
from dominio.evaluador import (
    EvaluadorDeEstadoGlobal,
    EvaluadorHumedad,
    EvaluadorLuz,
    EvaluadorTemperatura,
    GeneradorDeRecomendaciones,
)
from dominio.excepciones import ParametroInvalidoError
from dominio.servicio_diagnostico import ServicioDiagnostico
from dominio.servicios.cuentas import RegistrarPlanta, RegistrarUsuario
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

AHORA = datetime.now(timezone.utc)


class PruebaValidezDeLaLectura(unittest.TestCase):
    def test_una_lectura_fisicamente_posible_se_acepta(self):
        lectura = Lectura(AHORA, 0, 0, -40)
        self.assertEqual(lectura.humedad, 0)
        Lectura(AHORA, 100, 100000, 80)

    def test_valores_imposibles_se_rechazan(self):
        casos = [
            (-1, 500, 20), (101, 500, 20),
            (50, -1, 20), (50, 100001, 20),
            (50, 500, -41), (50, 500, 81),
        ]
        for humedad, luz, temperatura in casos:
            with self.assertRaises(ParametroInvalidoError, msg=str((humedad, luz, temperatura))):
                Lectura(AHORA, humedad, luz, temperatura)

    def test_no_numericos_nan_e_infinitos_se_rechazan(self):
        for malo in ("abc", None, True, float("nan"), float("inf")):
            with self.assertRaises(ParametroInvalidoError, msg=repr(malo)):
                Lectura(AHORA, malo, 500, 20)

    def test_la_marca_de_tiempo_debe_ser_una_fecha(self):
        with self.assertRaises(ParametroInvalidoError):
            Lectura("ayer", 50, 500, 20)

    def test_la_medicion_exige_especie_y_valores_validos(self):
        with self.assertRaises(ParametroInvalidoError):
            Medicion("", 50, 500, 20)
        with self.assertRaises(ParametroInvalidoError):
            Medicion("monstera", 500, 500, 20)


class PruebaEstadoSegunLaLectura(unittest.TestCase):
    def setUp(self):
        tabla = TablaFalsa({"sansevieria trifasciata": especie_de_prueba()})
        self.historial = HistorialFalso()
        plantas, dispositivos = PlantasFalsas(), DispositivosFalsos()
        usuario = RegistrarUsuario(UsuariosFalsos(), HasheadorFalso()).ejecutar("a@a.com", "clave123")
        RegistrarPlanta(plantas, dispositivos, self.historial, tabla, EmisorFalso()).ejecutar(
            usuario, "Sala", "sansevieria trifasciata", "ESP32-A"
        )
        servicio = ServicioDiagnostico(
            EvaluadorHumedad(), EvaluadorLuz(), EvaluadorTemperatura(),
            EvaluadorDeEstadoGlobal(), GeneradorDeRecomendaciones(),
        )
        self.registrar = RegistrarLectura(dispositivos, plantas, tabla, self.historial, servicio)

    def test_en_rango_es_saludable(self):
        diagnostico = self.registrar.ejecutar("ESP32-A", Lectura(AHORA, 30, 800, 22))
        self.assertEqual(diagnostico.estado, EstadoPlanta.SALUDABLE)
        self.assertEqual(diagnostico.recomendaciones, [])

    def test_un_parametro_fuera_de_rango_es_en_riesgo(self):
        diagnostico = self.registrar.ejecutar("ESP32-A", Lectura(AHORA, 5, 800, 22))
        self.assertEqual(diagnostico.estado, EstadoPlanta.EN_RIESGO)
        self.assertEqual(len(diagnostico.recomendaciones), 1)

    def test_dos_o_mas_fuera_de_rango_es_critico(self):
        diagnostico = self.registrar.ejecutar("ESP32-A", Lectura(AHORA, 5, 5, 22))
        self.assertEqual(diagnostico.estado, EstadoPlanta.CRITICO)

    def test_los_limites_del_rango_cuentan_como_optimos(self):
        diagnostico = self.registrar.ejecutar("ESP32-A", Lectura(AHORA, 20, 1500, 29))
        self.assertEqual(diagnostico.estado, EstadoPlanta.SALUDABLE)

    def test_una_lectura_invalida_ni_siquiera_llega_al_historial(self):
        with self.assertRaises(ParametroInvalidoError):
            self.registrar.ejecutar("ESP32-A", Lectura(AHORA, 999, 800, 22))
        self.assertEqual(self.historial.registros, [])


if __name__ == "__main__":
    unittest.main()
