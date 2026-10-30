"""Prueba el estado global y las recomendaciones a traves del
ServicioDiagnostico completo, siempre en memoria."""

import unittest

from dominio.entidades import EstadoPlanta, Medicion
from dominio.evaluador import (
    EvaluadorDeEstadoGlobal,
    EvaluadorHumedad,
    EvaluadorLuz,
    EvaluadorTemperatura,
    GeneradorDeRecomendaciones,
)
from dominio.servicio_diagnostico import ServicioDiagnostico
from pruebas.dobles_prueba import especie_de_prueba


def _crear_servicio() -> ServicioDiagnostico:
    return ServicioDiagnostico(
        evaluador_humedad=EvaluadorHumedad(),
        evaluador_luz=EvaluadorLuz(),
        evaluador_temperatura=EvaluadorTemperatura(),
        evaluador_estado_global=EvaluadorDeEstadoGlobal(),
        generador_recomendaciones=GeneradorDeRecomendaciones(),
    )


class PruebaEstadoGlobal(unittest.TestCase):
    def setUp(self):
        self.especie = especie_de_prueba()  # humedad 20-45, luz 200-1500, temp 15-29
        self.servicio = _crear_servicio()

    def test_todo_dentro_de_rango_es_saludable(self):
        medicion = Medicion(self.especie.nombre, humedad=32.5, luz=850, temperatura=21.0)
        diagnostico = self.servicio.diagnosticar(self.especie, medicion)
        self.assertEqual(diagnostico.estado, EstadoPlanta.SALUDABLE)
        self.assertEqual(diagnostico.recomendaciones, [])

    def test_un_parametro_fuera_de_rango_es_en_riesgo(self):
        medicion = Medicion(self.especie.nombre, humedad=10, luz=850, temperatura=21.0)
        diagnostico = self.servicio.diagnosticar(self.especie, medicion)
        self.assertEqual(diagnostico.estado, EstadoPlanta.EN_RIESGO)
        self.assertEqual(len(diagnostico.recomendaciones), 1)

    def test_dos_parametros_fuera_de_rango_es_critico(self):
        medicion = Medicion(self.especie.nombre, humedad=10, luz=50, temperatura=21.0)
        diagnostico = self.servicio.diagnosticar(self.especie, medicion)
        self.assertEqual(diagnostico.estado, EstadoPlanta.CRITICO)
        self.assertEqual(len(diagnostico.recomendaciones), 2)


if __name__ == "__main__":
    unittest.main()
