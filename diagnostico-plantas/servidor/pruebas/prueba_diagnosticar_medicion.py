"""Prueba el caso de uso con una tabla falsa, para comprobar que no
depende de CSV ni de base de datos."""

import unittest

from dominio.entidades import Medicion
from dominio.evaluador import (
    EvaluadorDeEstadoGlobal,
    EvaluadorHumedad,
    EvaluadorLuz,
    EvaluadorTemperatura,
    GeneradorDeRecomendaciones,
)
from dominio.excepciones import EspecieNoSoportadaError
from dominio.servicio_diagnostico import ServicioDiagnostico
from dominio.servicios.diagnosticar_medicion import DiagnosticarMedicion
from pruebas.dobles_prueba import TablaFalsa, especie_de_prueba


class PruebaDiagnosticarMedicion(unittest.TestCase):
    def setUp(self):
        self.servicio = ServicioDiagnostico(
            EvaluadorHumedad(), EvaluadorLuz(), EvaluadorTemperatura(),
            EvaluadorDeEstadoGlobal(), GeneradorDeRecomendaciones(),
        )

    def test_diagnostica_una_especie_soportada(self):
        tabla = TablaFalsa({"sansevieria": especie_de_prueba("sansevieria")})
        caso = DiagnosticarMedicion(tabla, self.servicio)

        diagnostico = caso.ejecutar(Medicion("sansevieria", 32.5, 850, 21.0))

        self.assertEqual(diagnostico.especie, "sansevieria")

    def test_especie_no_registrada_lanza_excepcion_de_dominio(self):
        caso = DiagnosticarMedicion(TablaFalsa({}), self.servicio)

        with self.assertRaises(EspecieNoSoportadaError):
            caso.ejecutar(Medicion("inexistente", 10, 10, 10))


if __name__ == "__main__":
    unittest.main()
