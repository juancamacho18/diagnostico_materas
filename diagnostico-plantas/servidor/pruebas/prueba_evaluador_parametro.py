"""Prueba la clasificacion BAJO/OPTIMO/ALTO por parametro."""

import unittest

from dominio.entidades import EstadoParametro
from dominio.evaluador import EvaluadorHumedad, EvaluadorLuz, EvaluadorTemperatura
from pruebas.dobles_prueba import especie_de_prueba


class PruebaEvaluadorHumedad(unittest.TestCase):
    def setUp(self):
        self.especie = especie_de_prueba()  # humedad optima: 20-45
        self.evaluador = EvaluadorHumedad()

    def test_humedad_por_debajo_del_rango_es_baja(self):
        resultado = self.evaluador.evaluar(self.especie, 10)
        self.assertEqual(resultado.estado, EstadoParametro.BAJO)

    def test_humedad_dentro_del_rango_es_optima(self):
        resultado = self.evaluador.evaluar(self.especie, 32.5)
        self.assertEqual(resultado.estado, EstadoParametro.OPTIMO)

    def test_humedad_por_encima_del_rango_es_alta(self):
        resultado = self.evaluador.evaluar(self.especie, 90)
        self.assertEqual(resultado.estado, EstadoParametro.ALTO)


class PruebaEvaluadorLuzYTemperatura(unittest.TestCase):
    def setUp(self):
        self.especie = especie_de_prueba()  # luz 200-1500, temp 15-29

    def test_luz_dentro_del_rango_es_optima(self):
        resultado = EvaluadorLuz().evaluar(self.especie, 850)
        self.assertEqual(resultado.estado, EstadoParametro.OPTIMO)

    def test_temperatura_por_encima_del_rango_es_alta(self):
        resultado = EvaluadorTemperatura().evaluar(self.especie, 35)
        self.assertEqual(resultado.estado, EstadoParametro.ALTO)


if __name__ == "__main__":
    unittest.main()
